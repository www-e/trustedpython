"""Helper functions to trigger notifications from various events."""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.schemas.notification import NotificationType
from app.services.notifications import NotificationService

logger = logging.getLogger(__name__)


async def notify_new_message(
    db: AsyncSession,
    recipient_id: UUID,
    sender_name: str,
    message_preview: str,
    conversation_id: UUID,
) -> None:
    """
    Send notification when user receives a new message.

    Args:
        db: Database session
        recipient_id: User receiving the message
        sender_name: Name of sender (masked if needed)
        message_preview: Preview of message content
        conversation_id: ID of conversation
    """
    try:
        await NotificationService.create_notification(
            db=db,
            user_id=recipient_id,
            title=f"New message from {sender_name}",
            description=message_preview[:100],
            notification_type=NotificationType.MESSAGE,
            icon="message",
            action_url=f"/chat/{conversation_id}",
            metadata={
                "sender_name": sender_name,
                "conversation_id": str(conversation_id),
                "type": "new_message",
            },
        )
        logger.info(f"New message notification sent to user {recipient_id}")
    except Exception as e:
        logger.error(f"Failed to send new message notification: {e}")


async def notify_deal_initiated(
    db: AsyncSession,
    buyer_id: UUID,
    seller_id: UUID,
    deal_id: UUID,
    listing_title: str,
    counterparty_name: str,
) -> None:
    """
    Send notification when a deal is initiated.

    Args:
        db: Database session
        buyer_id: Buyer user ID
        seller_id: Seller user ID
        deal_id: Deal ID
        listing_title: Title of listing
        counterparty_name: Name of other party
    """
    try:
        # Notify seller
        await NotificationService.create_notification(
            db=db,
            user_id=seller_id,
            title="New purchase request",
            description=f"{counterparty_name} wants to buy '{listing_title}'",
            notification_type=NotificationType.PURCHASE,
            icon="shopping_cart",
            action_url=f"/deals/{deal_id}",
            metadata={
                "deal_id": str(deal_id),
                "listing_title": listing_title,
                "buyer_name": counterparty_name,
                "type": "deal_initiated",
            },
        )

        # Notify buyer
        await NotificationService.create_notification(
            db=db,
            user_id=buyer_id,
            title="Purchase request sent",
            description=f"You've sent a purchase request for '{listing_title}'",
            notification_type=NotificationType.PURCHASE,
            icon="shopping_cart",
            action_url=f"/deals/{deal_id}",
            metadata={
                "deal_id": str(deal_id),
                "listing_title": listing_title,
                "type": "deal_initiated_buyer",
            },
        )

        logger.info(f"Deal initiated notifications sent for deal {deal_id}")
    except Exception as e:
        logger.error(f"Failed to send deal initiated notifications: {e}")


async def notify_payment_confirmed(
    db: AsyncSession,
    seller_id: UUID,
    deal_id: UUID,
    listing_title: str,
    amount: float,
    currency: str = "USD",
) -> None:
    """
    Send notification when payment is confirmed.

    Args:
        db: Database session
        seller_id: Seller user ID
        deal_id: Deal ID
        listing_title: Title of listing
        amount: Payment amount
        currency: Currency code
    """
    try:
        await NotificationService.create_notification(
            db=db,
            user_id=seller_id,
            title="Payment received",
            description=f"You've received {amount:.2f} {currency} for '{listing_title}'",
            notification_type=NotificationType.PURCHASE,
            icon="payment",
            action_url=f"/deals/{deal_id}",
            metadata={
                "deal_id": str(deal_id),
                "listing_title": listing_title,
                "amount": amount,
                "currency": currency,
                "type": "payment_confirmed",
            },
        )
        logger.info(f"Payment confirmation notification sent to seller {seller_id}")
    except Exception as e:
        logger.error(f"Failed to send payment confirmation notification: {e}")


async def notify_account_verified(db: AsyncSession, user_id: UUID) -> None:
    """
    Send notification when user account is verified.

    Args:
        db: Database session
        user_id: User ID
    """
    try:
        await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title="Account verified",
            description="Your account has been verified. You can now start selling!",
            notification_type=NotificationType.ACCOUNT_UPDATE,
            icon="verified",
            action_url="/profile",
            metadata={"type": "account_verified"},
        )
        logger.info(f"Account verification notification sent to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send account verification notification: {e}")


async def notify_password_changed(db: AsyncSession, user_id: UUID) -> None:
    """
    Send notification when password is changed.

    Args:
        db: Database session
        user_id: User ID
    """
    try:
        await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title="Password updated",
            description="Your password was successfully changed",
            notification_type=NotificationType.SECURITY_ALERT,
            icon="security",
            action_url="/security",
            metadata={"type": "password_changed"},
        )
        logger.info(f"Password change notification sent to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send password change notification: {e}")


async def notify_new_login(
    db: AsyncSession,
    user_id: UUID,
    device_info: Optional[str] = None,
    location: Optional[str] = None,
) -> None:
    """
    Send notification when new login is detected from unusual device/location.

    Args:
        db: Database session
        user_id: User ID
        device_info: Device information
        location: Location information
    """
    try:
        description = "New login detected"
        if device_info:
            description += f" from {device_info}"
        if location:
            description += f" in {location}"

        await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title="New login detected",
            description=description,
            notification_type=NotificationType.SECURITY_ALERT,
            icon="security",
            action_url="/security",
            metadata={"device_info": device_info, "location": location, "type": "new_login"},
        )
        logger.info(f"New login notification sent to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send new login notification: {e}")


async def notify_system_maintenance(
    db: AsyncSession, scheduled_time: str, affected_users: Optional[list[UUID]] = None
) -> None:
    """
    Send notification about scheduled system maintenance.

    Args:
        db: Database session
        scheduled_time: Maintenance time description
        affected_users: List of affected user IDs (None = all users)
    """
    try:
        # If no specific users, this would need to be handled differently
        # For now, we'll skip if no specific users provided
        if not affected_users:
            logger.warning("System maintenance notification with no specific users - skipping")
            return

        for user_id in affected_users:
            await NotificationService.create_notification(
                db=db,
                user_id=user_id,
                title="Scheduled maintenance",
                description=f"System maintenance scheduled for {scheduled_time}",
                notification_type=NotificationType.SYSTEM,
                icon="notifications",
                metadata={"scheduled_time": scheduled_time, "type": "maintenance"},
            )

        logger.info(f"System maintenance notifications sent to {len(affected_users)} users")
    except Exception as e:
        logger.error(f"Failed to send system maintenance notifications: {e}")


async def notify_mediator_assigned(
    db: AsyncSession, user_id: UUID, deal_id: UUID, mediator_name: str
) -> None:
    """
    Send notification when a mediator is assigned to a deal.

    Args:
        db: Database session
        user_id: User ID (deal participant)
        deal_id: Deal ID
        mediator_name: Name of assigned mediator
    """
    try:
        await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title="Mediator assigned",
            description=f"{mediator_name} has been assigned to help with your deal",
            notification_type=NotificationType.MESSAGE,
            icon="support_agent",
            action_url=f"/deals/{deal_id}",
            metadata={
                "deal_id": str(deal_id),
                "mediator_name": mediator_name,
                "type": "mediator_assigned",
            },
        )
        logger.info(f"Mediator assignment notification sent to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send mediator assignment notification: {e}")


async def notify_dispute_created(
    db: AsyncSession, participant_id: UUID, deal_id: UUID, creator_name: str
) -> None:
    """
    Send notification when a dispute is created.

    Args:
        db: Database session
        participant_id: User ID (deal participant)
        deal_id: Deal ID
        creator_name: Name of user who created dispute
    """
    try:
        await NotificationService.create_notification(
            db=db,
            user_id=participant_id,
            title="Dispute created",
            description=f"{creator_name} has created a dispute for this deal",
            notification_type=NotificationType.MESSAGE,
            icon="gavel",
            action_url=f"/deals/{deal_id}",
            metadata={
                "deal_id": str(deal_id),
                "creator_name": creator_name,
                "type": "dispute_created",
            },
        )
        logger.info(f"Dispute created notification sent to user {participant_id}")
    except Exception as e:
        logger.error(f"Failed to send dispute created notification: {e}")


async def notify_review_received(
    db: AsyncSession, recipient_id: UUID, reviewer_name: str, rating: int, deal_id: UUID
) -> None:
    """
    Send notification when user receives a review.

    Args:
        db: Database session
        recipient_id: User receiving review
        reviewer_name: Name of reviewer
        rating: Rating given (1-5)
        deal_id: Deal ID
    """
    try:
        stars = "⭐" * rating
        await NotificationService.create_notification(
            db=db,
            user_id=recipient_id,
            title=f"New review: {stars}",
            description=f"{reviewer_name} left you a {rating}-star review",
            notification_type=NotificationType.ACCOUNT_UPDATE,
            icon="star",
            action_url=f"/deals/{deal_id}",
            metadata={
                "deal_id": str(deal_id),
                "reviewer_name": reviewer_name,
                "rating": rating,
                "type": "review_received",
            },
        )
        logger.info(f"Review received notification sent to user {recipient_id}")
    except Exception as e:
        logger.error(f"Failed to send review received notification: {e}")


async def notify_listing_approved(
    db: AsyncSession, seller_id: UUID, listing_id: UUID, listing_title: str
) -> None:
    """
    Send notification when listing is approved.

    Args:
        db: Database session
        seller_id: Seller user ID
        listing_id: Listing ID
        listing_title: Title of listing
    """
    try:
        await NotificationService.create_notification(
            db=db,
            user_id=seller_id,
            title="Listing approved",
            description=f"Your listing '{listing_title}' has been approved",
            notification_type=NotificationType.ACCOUNT_UPDATE,
            icon="check_circle",
            action_url=f"/listings/{listing_id}",
            metadata={
                "listing_id": str(listing_id),
                "listing_title": listing_title,
                "type": "listing_approved",
            },
        )
        logger.info(f"Listing approval notification sent to user {seller_id}")
    except Exception as e:
        logger.error(f"Failed to send listing approval notification: {e}")


async def notify_listing_rejected(
    db: AsyncSession, seller_id: UUID, listing_id: UUID, listing_title: str, reason: str
) -> None:
    """
    Send notification when listing is rejected.

    Args:
        db: Database session
        seller_id: Seller user ID
        listing_id: Listing ID
        listing_title: Title of listing
        reason: Rejection reason
    """
    try:
        await NotificationService.create_notification(
            db=db,
            user_id=seller_id,
            title="Listing rejected",
            description=f"Your listing '{listing_title}' was rejected: {reason}",
            notification_type=NotificationType.ACCOUNT_UPDATE,
            icon="error",
            action_url=f"/listings/{listing_id}/edit",
            metadata={
                "listing_id": str(listing_id),
                "listing_title": listing_title,
                "reason": reason,
                "type": "listing_rejected",
            },
        )
        logger.info(f"Listing rejection notification sent to user {seller_id}")
    except Exception as e:
        logger.error(f"Failed to send listing rejection notification: {e}")
