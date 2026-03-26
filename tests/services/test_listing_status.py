"""Tests for ListingStatusService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.listing_status import ListingStatusService
from app.models.enums import ListingStatus
from app.exceptions import ValidationError, ForbiddenError


@pytest.mark.asyncio
async def test_publish_listing_success(db_session: AsyncSession, setup_listing):
    """Test successful listing publication."""
    listing, seller = setup_listing

    service = ListingStatusService(db_session)
    result = await service.publish_listing(listing.id, seller.id)

    assert result.status == ListingStatus.ACTIVE


@pytest.mark.asyncio
async def test_publish_listing_wrong_user(db_session: AsyncSession, setup_listing, setup_user):
    """Test publishing listing by non-owner."""
    listing, seller = setup_listing
    other_user = setup_user

    service = ListingStatusService(db_session)

    with pytest.raises(ForbiddenError):
        await service.publish_listing(listing.id, other_user.id)


@pytest.mark.asyncio
async def test_publish_listing_already_active(db_session: AsyncSession, setup_active_listing):
    """Test publishing already active listing."""
    listing, seller = setup_active_listing

    service = ListingStatusService(db_session)

    with pytest.raises(ValidationError, match="Only draft"):
        await service.publish_listing(listing.id, seller.id)


@pytest.mark.asyncio
async def test_pause_listing_success(db_session: AsyncSession, setup_active_listing):
    """Test successful listing pause."""
    listing, seller = setup_active_listing

    service = ListingStatusService(db_session)
    result = await service.pause_listing(listing.id, seller.id)

    assert result.status == ListingStatus.PAUSED


@pytest.mark.asyncio
async def test_pause_listing_not_active(db_session: AsyncSession, setup_listing):
    """Test pausing non-active listing."""
    listing, seller = setup_listing

    service = ListingStatusService(db_session)

    with pytest.raises(ValidationError, match="Only active"):
        await service.pause_listing(listing.id, seller.id)
