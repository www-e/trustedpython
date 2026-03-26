"""Tests for ListingAuthService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.listing_auth import ListingAuthService
from app.exceptions import ForbiddenError, NotFoundError


@pytest.mark.asyncio
async def test_verify_ownership_success(db_session: AsyncSession, setup_listing):
    """Test successful ownership verification."""
    listing, seller = setup_listing

    service = ListingAuthService(db_session)
    result = await service.verify_ownership(listing.id, seller.id)

    assert result.id == listing.id
    assert result.seller_id == seller.id


@pytest.mark.asyncio
async def test_verify_ownership_wrong_user(db_session: AsyncSession, setup_listing, setup_user):
    """Test ownership verification with wrong user."""
    listing, seller = setup_listing
    other_user = setup_user

    service = ListingAuthService(db_session)

    with pytest.raises(ForbiddenError, match="don't own"):
        await service.verify_ownership(listing.id, other_user.id)


@pytest.mark.asyncio
async def test_verify_ownership_not_found(db_session: AsyncSession):
    """Test ownership verification with non-existent listing."""
    service = ListingAuthService(db_session)

    with pytest.raises(NotFoundError, match="not found"):
        await service.verify_ownership(99999, 1)


@pytest.mark.asyncio
async def test_verify_ownership_or_admin_as_owner(db_session: AsyncSession, setup_listing):
    """Test ownership verification as owner."""
    listing, seller = setup_listing

    service = ListingAuthService(db_session)
    result = await service.verify_ownership_or_admin(listing.id, seller.id, is_admin=False)

    assert result.id == listing.id


@pytest.mark.asyncio
async def test_verify_ownership_or_admin_as_admin(db_session: AsyncSession, setup_listing, setup_admin):
    """Test ownership verification as admin."""
    listing, seller = setup_listing
    admin = setup_admin

    service = ListingAuthService(db_session)
    result = await service.verify_ownership_or_admin(listing.id, admin.id, is_admin=True)

    assert result.id == listing.id
