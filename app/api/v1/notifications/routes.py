"""Notification API routes."""

from typing import Optional, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_current_user, get_db, paginate
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    MarkAllReadResponse,
    MarkReadResponse,
    NotificationListResponse,
    NotificationResponse,
    NotificationSettingsResponse,
    NotificationType,
    UnreadCountResponse,
    UpdateNotificationSettingsRequest,
)
from app.services.notifications import NotificationService
from app.utils.rate_limit import check_rate_limit

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    pagination: PaginationParams = Depends(paginate),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationListResponse:
    """
    Get notifications for the authenticated user.

    Query Parameters:
        type: Filter by notification type (account_update, message, security_alert, purchase, system)
        is_read: Filter by read status (true/false)
        page: Page number (default: 1)
        limit: Items per page (default: 20, max: 50)

    Returns:
        NotificationListResponse: Paginated list of notifications with unread count

    Raises:
        HTTPException 400: Invalid pagination parameters
        HTTPException 401: Not authenticated
    """
    try:
        result = await NotificationService.get_user_notifications(
            db=db,
            user_id=current_user.id,
            notification_type=notification_type,
            is_read=is_read,
            page=pagination.page,
            limit=pagination.limit,
        )
        return cast(NotificationListResponse, result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    """
    Get a single notification by ID.

    Path Parameters:
        notification_id: Notification UUID

    Returns:
        NotificationResponse: Notification details

    Raises:
        HTTPException 401: Not authenticated
        HTTPException 403: Notification belongs to different user
        HTTPException 404: Notification not found
    """
    try:
        result = await NotificationService.get_notification(
            db=db, notification_id=notification_id, user_id=current_user.id
        )
        return cast(NotificationResponse, result)
    except NotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    except ForbiddenException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this notification"
        )


@router.post("/{notification_id}/read", response_model=MarkReadResponse)
async def mark_notification_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MarkReadResponse:
    """
    Mark a notification as read.

    Path Parameters:
        notification_id: Notification UUID

    Returns:
        MarkReadResponse: Success confirmation

    Raises:
        HTTPException 401: Not authenticated
        HTTPException 403: Notification belongs to different user
        HTTPException 404: Notification not found
    """
    try:
        result = await NotificationService.mark_as_read(
            db=db, notification_id=notification_id, user_id=current_user.id
        )
        return MarkReadResponse(**result)
    except NotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    except ForbiddenException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this notification"
        )


@router.post("/read-all", response_model=MarkAllReadResponse)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> MarkAllReadResponse:
    """
    Mark all notifications as read for the authenticated user.

    Returns:
        MarkAllReadResponse: Success confirmation with count of marked notifications

    Raises:
        HTTPException 401: Not authenticated
    """
    result = await NotificationService.mark_all_as_read(db=db, user_id=current_user.id)
    return MarkAllReadResponse(**result)


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_notification_count(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> UnreadCountResponse:
    """
    Get the count of unread notifications.

    Returns:
        UnreadCountResponse: Unread notification count

    Raises:
        HTTPException 401: Not authenticated
    """
    count = await NotificationService.get_unread_count(db=db, user_id=current_user.id)

    # Cache in Redis for WebSocket badge updates
    from app.core.redis import get_redis

    redis_client = await get_redis()
    if redis_client:
        cache_key = f"unread_count:{current_user.id}"
        await redis_client.setex(cache_key, 300, str(count))  # Cache for 5 minutes

    return UnreadCountResponse(success=True, data={"count": count})


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Delete a notification.

    Path Parameters:
        notification_id: Notification UUID

    Returns:
        Success confirmation message

    Raises:
        HTTPException 401: Not authenticated
        HTTPException 403: Notification belongs to different user
        HTTPException 404: Notification not found
    """
    try:
        result = await NotificationService.delete_notification(
            db=db, notification_id=notification_id, user_id=current_user.id
        )
        return result
    except NotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    except ForbiddenException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this notification"
        )


@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> NotificationSettingsResponse:
    """
    Get notification preferences for the authenticated user.

    Returns:
        NotificationSettingsResponse: User's notification settings

    Raises:
        HTTPException 401: Not authenticated
    """
    result = await NotificationService.get_notification_settings(db=db, user_id=current_user.id)
    return cast(NotificationSettingsResponse, result)


@router.put("/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    settings_update: UpdateNotificationSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationSettingsResponse:
    """
    Update notification preferences for the authenticated user.

    Request Body:
        push_notifications: Enable/disable push notifications (optional)
        email_notifications: Enable/disable email notifications (optional)
        types: Per-type settings (optional, all fields optional)

    Returns:
        NotificationSettingsResponse: Updated settings

    Raises:
        HTTPException 401: Not authenticated
        HTTPException 400: Invalid settings data
    """
    try:
        result = await NotificationService.update_notification_settings(
            db=db,
            user_id=current_user.id,
            push_notifications=settings_update.push_notifications,
            email_notifications=settings_update.email_notifications,
            types=settings_update.types,
        )
        return cast(NotificationSettingsResponse, result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to update settings: {str(e)}"
        )


# Internal helper endpoint for creating notifications
# This would typically be called by other services
@router.post("/internal/create", response_model=NotificationResponse, include_in_schema=False)
async def create_notification_internal(
    user_id: UUID,
    title: str,
    description: str,
    notification_type: NotificationType,
    icon: Optional[str] = None,
    action_url: Optional[str] = None,
    metadata: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    """
    Internal endpoint to create notifications.

    This endpoint is not documented in OpenAPI schema (include_in_schema=False)
    and should only be called internally by other services.

    Args:
        user_id: Target user ID
        title: Notification title
        description: Notification description
        notification_type: Type of notification
        icon: Optional icon identifier
        action_url: Optional deep link URL
        metadata: Optional additional data

    Returns:
        NotificationResponse: Created notification

    Raises:
        HTTPException 400: Invalid data or user doesn't exist
        HTTPException 429: Rate limit exceeded
    """
    # Apply rate limiting
    is_allowed = await check_rate_limit(
        f"create_notification:{user_id}", max_requests=10, window_seconds=60
    )
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Notification creation rate limit exceeded",
        )

    try:
        result = await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            description=description,
            notification_type=notification_type,
            icon=icon,
            action_url=action_url,
            metadata=metadata,
        )
        return cast(NotificationResponse, result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
