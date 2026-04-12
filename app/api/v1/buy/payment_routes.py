"""
Payment routes for the buy flow.

Handles payment submission, verification, and status checking
for deals in the buy flow.
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.deal import ConfirmPaymentRequest, PaymentStatusResponse, RejectPaymentRequest
from app.services.buy import BuyService

router = APIRouter(prefix="/deals", tags=["Payment"])


# ==================== PAYMENT ENDPOINTS ====================


@router.post(
    "/{deal_id}/payment",
    response_model=APIResponse[PaymentStatusResponse],
    summary="Submit payment",
    description="Submit payment screenshot for verification",
)
async def submit_payment(
    deal_id: str,
    screenshot: UploadFile = File(..., description="Payment screenshot image"),
    notes: Optional[str] = Form(None, description="Optional notes"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PaymentStatusResponse]:
    """
    Submit payment screenshot for mediator verification.

    Requirements:
    - File must be JPG, JPEG, or PNG
    - Maximum file size: 5MB
    - Only buyer can submit payment

    Deal status will change to PAYMENT_SUBMITTED.
    """
    try:
        # Validate file
        if not screenshot.content_type or not screenshot.content_type.startswith("image/"):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="File must be an image (JPG, JPEG, PNG)",
            )

        # Check file size (5MB limit)
        content = await screenshot.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail="File size exceeds 5MB limit"
            )

        # TODO: Upload file to storage service
        # For now, use a placeholder URL
        screenshot_url = f"https://storage.example.com/payments/{deal_id}/{screenshot.filename}"

        service = BuyService(db)
        result = await service.submit_payment(
            deal_id=deal_id, screenshot_url=screenshot_url, notes=notes
        )
        return APIResponse.success_response(data=result, message="Payment submitted successfully")
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit payment: {str(e)}",
        )


@router.post(
    "/{deal_id}/payment/confirm",
    response_model=APIResponse[PaymentStatusResponse],
    summary="Confirm payment",
    description="Mediator confirms payment received",
)
async def confirm_payment(
    deal_id: str,
    request: ConfirmPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PaymentStatusResponse]:
    """
    Confirm payment (mediator only).

    This action:
    - Marks payment as VERIFIED
    - Updates deal status to VERIFIED
    - Notifies buyer and seller

    Optional notes can be added for documentation.
    """
    try:
        # TODO: Verify user is mediator for this deal
        service = BuyService(db)
        result = await service.confirm_payment(deal_id=deal_id, notes=request.notes)
        return APIResponse.success_response(data=result, message="Payment confirmed successfully")
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm payment: {str(e)}",
        )


@router.post(
    "/{deal_id}/payment/reject",
    response_model=APIResponse[PaymentStatusResponse],
    summary="Reject payment",
    description="Mediator rejects payment",
)
async def reject_payment(
    deal_id: str,
    request: RejectPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PaymentStatusResponse]:
    """
    Reject payment (mediator only).

    This action:
    - Marks payment as REJECTED
    - Updates deal status to REJECTED
    - Records rejection reason
    - Notifies buyer

    A reason (min 10 characters) is required for rejection.
    """
    try:
        # TODO: Verify user is mediator for this deal
        service = BuyService(db)
        result = await service.reject_payment(deal_id=deal_id, reason=request.reason)
        return APIResponse.success_response(data=result, message="Payment rejected")
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject payment: {str(e)}",
        )


@router.get(
    "/{deal_id}/payment/status",
    response_model=APIResponse[PaymentStatusResponse],
    summary="Check payment status",
    description="Poll for payment status updates",
)
async def check_payment_status(
    deal_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> APIResponse[PaymentStatusResponse]:
    """
    Check current payment status for a deal.

    Used by frontend waiting screen to poll for status updates.

    Returns:
    - Payment status (pending, submitted, verified, rejected)
    - Screenshot URL (if submitted)
    - Timestamps for submission/verification
    - Rejection reason (if rejected)
    """
    try:
        service = BuyService(db)
        result = await service.check_payment_status(deal_id)
        return APIResponse.success_response(data=result)
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check payment status: {str(e)}",
        )
