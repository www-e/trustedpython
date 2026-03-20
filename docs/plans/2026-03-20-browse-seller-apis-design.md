# Phase 4 API Design: Browse & Discovery + Seller Flows

**Date:** 2026-03-20
**Status:** Design Approved
**Approach:** User Flow-Based Development

---

## 📋 Overview

This phase implements two complete user flows:
1. **Browse & Discovery Flow** - Buyers can browse listings, filter by game/category, view featured accounts
2. **Seller Management Flow** - Sellers can create listings, manage their inventory, view trade history

---

## 🗄️ Database Schema Changes

### A. User Model Updates

**File:** `app/models/user.py`

**New Fields:**
```python
username: Mapped[str | None] = mapped_column(String(50), unique=True)
avatar_url: Mapped[str | None] = mapped_column(String(500))
rating: Mapped[float] = mapped_column(Numeric(3, 2), default=0.0)  # 0.00-5.00
total_deals_as_buyer: Mapped[int] = mapped_column(Integer, default=0)
total_deals_as_seller: Mapped[int] = mapped_column(Integer, default=0)
completed_deals: Mapped[int] = mapped_column(Integer, default=0)
bio: Mapped[str | None] = mapped_column(Text)
```

### B. ListingStatus Enum Updates

**File:** `app/models/enums.py`

**Add PENDING status:**
```python
class ListingStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"      # ⭐ NEW - Awaiting admin approval
    ACTIVE = "active"
    PAUSED = "paused"
    SOLD = "sold"
    ARCHIVED = "archived"
```

### C. ListingMediator Model (New)

**File:** `app/models/listing_mediator.py`

```python
"""Listing-Mediator relationship model."""

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# Type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.listing import Listing
    from app.models.user import User


class ListingMediator(BaseModel):
    """Which mediators are allowed to mediate a listing."""

    __tablename__ = "listing_mediators"

    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False
    )
    mediator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relationships
    listing: Mapped["Listing"] = relationship("Listing", back_populates="allowed_mediators")
    mediator: Mapped["User"] = relationship("User", back_populates="listings_to_mediate")

    __table_args__ = (
        UniqueConstraint('listing_id', 'mediator_id', name='unique_listing_mediator'),
    )

    def __repr__(self) -> str:
        return f"<ListingMediator(listing_id={self.listing_id}, mediator_id={self.mediator_id})>"
```

### D. Deal Model (New)

**File:** `app/models/deal.py`

```python
"""Deal model for transactions."""

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from enum import Enum

from app.models.base import BaseModel

# Type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.listing import Listing
    from app.models.user import User


class DealStatus(str, Enum):
    """Deal status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_PAYMENT = "awaiting_payment"
    PAYMENT_VERIFIED = "payment_verified"
    CREDENTIALS_EXCHANGED = "credentials_exchanged"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class Deal(BaseModel):
    """Deal/transaction between buyer and seller."""

    __tablename__ = "deals"

    # Foreign Keys
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    buyer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    seller_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    mediator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Deal Details
    status: Mapped[DealStatus] = mapped_column(
        PgEnum(DealStatus, name="deal_status", create_type=False),
        default=DealStatus.PENDING,
        nullable=False,
        index=True
    )
    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    # Relationships
    listing: Mapped["Listing"] = relationship("Listing")
    buyer: Mapped["User"] = relationship("User", foreign_keys=[buyer_id], back_populates="deals_as_buyer")
    seller: Mapped["User"] = relationship("User", foreign_keys=[seller_id], back_populates="deals_as_seller")
    mediator: Mapped["User"] = relationship("User", foreign_keys=[mediator_id])

    def __repr__(self) -> str:
        return f"<Deal(id={self.id}, status={self.status}, price={self.price})>"
```

### E. Update Listing Model

**File:** `app/models/listing.py`

**Add relationship to ListingMediator:**
```python
from app.models.listing_mediator import ListingMediator

# In Listing class, add:
allowed_mediators: Mapped[list["ListingMediator"]] = relationship(
    "ListingMediator",
    back_populates="listing",
    cascade="all, delete-orphan"
)
```

### F. Update User Model Relationships

**File:** `app/models/user.py`

**Add deal relationships:**
```python
# Add imports and type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.deal import Deal
    from app.models.listing_mediator import ListingMediator

# In User class, add:
deals_as_buyer: Mapped[list["Deal"]] = relationship(
    "Deal",
    foreign_keys="Deal.buyer_id",
    back_populates="buyer"
)
deals_as_seller: Mapped[list["Deal"]] = relationship(
    "Deal",
    foreign_keys="Deal.seller_id",
    back_populates="seller"
)
listings_to_mediate: Mapped[list["ListingMediator"]] = relationship(
    "ListingMediator",
    back_populates="mediator"
)
```

---

## 🌐 API Endpoints

### Flow 1: Browse & Discovery APIs

#### 1. Categories (Games) with Icons

```
GET /api/v1/categories
Description: Get all active games with icons for home page
Response: List of categories with icon_url
Access: Public
```

#### 2. Featured Listings

```
GET /api/v1/listings/featured
Query Params: limit=6
Description: Get featured listings for home page
Response: 6 featured listings (status=active, is_featured=true)
Access: Public
```

#### 3. Enhanced Search/Filter

```
GET /api/v1/listings/search
Query Params:
  - category_id: int (filter by game)
  - min_price: decimal
  - max_price: decimal
  - game_type: enum
  - rank: string
  - server: string
  - search: string (full-text)
  - sort: enum (newest, cheapest, expensive, popular)
  - limit: int (default 20)
  - cursor: string (pagination)
Description: Advanced search for listings
Response: Paginated listings
Access: Public
```

#### 4. Category Listings Page

```
GET /api/v1/categories/{id}/listings
Query Params:
  - status: active (default)
  - limit: 20
  - cursor: string
Description: Get all listings for a specific game
Response: Paginated listings for that game
Access: Public
```

#### 5. Listing Details

```
GET /api/v1/listings/{id}
Description: Get full listing details with images
Response: Complete listing with seller info, images, category
Access: Public
```

### Flow 2: Seller Management APIs

#### 6. Get Available Mediators

```
GET /api/v1/mediators/available
Query Params:
  - tier: enum (bronze, silver, gold, platinum)
  - min_rating: decimal
Description: Get list of mediators available for selection
Response: List of mediators with id, username, rating, tier
Access: Sellers only
```

#### 7. Create Listing with Mediators

```
POST /api/v1/listings
Request Body:
{
  "category_id": int,
  "title": string,
  "short_description": string,
  "full_description": string,
  "game_type": enum,
  "level": int,
  "rank": string,
  "server": string,
  "skins_count": int,
  "characters_count": int,
  "price": decimal,
  "mediator_ids": [int, int, int],  // Min 3 required
  "images": [
    {"url": string, "caption": string, "is_primary": true},
    {"url": string},
    {"url": string}
  ]
}
Description: Create new listing (goes to PENDING status)
Response: Created listing with status=pending
Access: Sellers only
Business Rules:
  - Minimum 3 mediators required
  - Maximum 3 images
  - Status automatically set to PENDING
  - One image must be primary
```

#### 8. My Listings (Tabs)

```
GET /api/v1/listings/my
Query Params:
  - status: enum (active, pending, sold, paused)
  - limit: 20
  - cursor: string
Description: Get seller's listings with status filter for tabs
Response: Paginated listings filtered by status
Access: Sellers only
```

#### 9. Get My Profile

```
GET /api/v1/users/me
Description: Get current user profile with stats
Response: User profile with ratings, deals counts, listings preview (3)
Access: Authenticated
```

#### 10. Update Profile

```
PUT /api/v1/users/me
Request Body:
{
  "username": string,
  "bio": string,
  "avatar_url": string
}
Description: Update user profile
Response: Updated user
Access: Authenticated (own profile only)
```

#### 11. Change Password

```
PUT /api/v1/users/me/password
Request Body:
{
  "current_password": string,
  "new_password": string,
  "confirm_password": string
}
Description: Change user password (no OTP)
Response: Success message
Access: Authenticated
Business Rules:
  - Current password must match
  - New password must match confirm
  - Password strength validation
```

#### 12. Trade History

```
GET /api/v1/deals/my
Query Params:
  - as: enum (buyer, seller, all)
  - status: enum (pending, in_progress, completed, cancelled)
  - limit: 20
  - cursor: string
Description: Get user's trade history
Response: Paginated deals with listing info, price, status, date
Access: Authenticated
```

---

## 📁 File Structure

### New Files to Create

```
app/
├── models/
│   ├── deal.py                    # Deal model
│   └── listing_mediator.py        # Listing-Mediator join table
├── schemas/
│   ├── deal.py                    # Deal schemas
│   ├── user_profile.py            # User profile schemas
│   └── mediator.py                # Mediator schemas
├── repositories/
│   ├── deal.py                    # Deal repository
│   └── listing_mediator.py        # ListingMediator repository
├── services/
│   ├── deal_service.py            # Deal business logic
│   ├── user_service.py            # User profile management
│   └── mediator_service.py        # Mediator availability
└── api/v1/
    ├── users.py                   # User profile endpoints
    ├── deals.py                   # Deal endpoints
    └── mediators.py               # Mediator endpoints

tests/
├── test_deals.py                  # Deal tests
├── test_user_profile.py           # User profile tests
├── test_mediators.py              # Mediator tests
└── test_trade_history.py          # Trade history tests

database/
└── migrations/versions/
    └── 20260320_phase4_user_deal_mediators.py  # Migration
```

### Files to Modify

```
app/
├── models/
│   ├── user.py                    # Add profile fields, relationships
│   ├── listing.py                 # Add allowed_mediators relationship
│   └── enums.py                   # Add DealStatus, PENDING status
├── schemas/
│   ├── user.py                    # Update user schemas
│   ├── listing.py                 # Update listing schemas
│   └── __init__.py                # Export new schemas
├── repositories/
│   ├── user.py                    # Add profile methods
│   ├── listing.py                 # Add mediator filtering
│   └── __init__.py                # Export new repositories
├── services/
│   ├── user_service.py            # Update or create
│   ├── listing_service.py         # Add mediator validation
│   └── __init__.py                # Export new services
└── api/v1/
    ├── listings.py                # Add mediator selection to create
    ├── router.py                  # Include new routers
    └── dependencies.py            # Add mediator dependencies if needed
```

---

## 🔄 Data Flow Examples

### Example 1: Seller Creates Listing

```
1. Seller submits listing with 3 mediators
   POST /api/v1/listings
   {
     "title": "PUBG Ace Account",
     "category_id": 1,
     "price": 50.00,
     "mediator_ids": [5, 8, 12],
     "images": [...]
   }

2. Service layer validates:
   - Minimum 3 mediators ✓
   - All mediators exist and have role=MEDIATOR ✓
   - Max 3 images ✓

3. Listing created with status=PENDING

4. ListingMediator rows created for each mediator

5. Response: Listing with status=pending
```

### Example 2: Buyer Browses Home Page

```
1. GET /api/v1/categories
   Response: [
     {id: 1, name: "PUBG", icon_url: "...", is_active: true},
     {id: 2, name: "Free Fire", icon_url: "...", is_active: true}
   ]

2. GET /api/v1/listings/featured?limit=6
   Response: 6 featured listings with images

3. User clicks "PUBG" game

4. GET /api/v1/categories/1/listings
   Response: All active PUBG listings (paginated)
```

### Example 3: Seller Views Their Listings

```
1. GET /api/v1/listings/my?status=pending
   Response: Pending listings awaiting approval

2. GET /api/v1/listings/my?status=active
   Response: Active listings

3. GET /api/v1/listings/my?status=sold
   Response: Sold listings
```

---

## 🧪 Testing Strategy

### Unit Tests (Per File)

- **test_deal_repository.py**: Deal CRUD, filtering by status/user
- **test_deal_service.py**: Deal creation logic, status transitions
- **test_user_service.py**: Profile updates, password changes, stats
- **test_mediator_service.py**: Mediator availability, filtering

### Integration Tests (Per Flow)

- **test_browse_flow.py**: Home page API integration
  - Get categories
  - Get featured listings
  - Search/filter listings

- **test_seller_flow.py**: Seller management integration
  - Create listing with mediators
  - View my listings (all tabs)
  - Update profile
  - Change password
  - View trade history

### Test Coverage Goals

- Target: 90%+ coverage for new code
- All business logic tested
- All endpoints tested
- Error cases tested

---

## 🎯 Success Criteria

### Browse & Discovery Flow
- ✅ Home page displays featured listings
- ✅ Home page displays games with icons
- ✅ Search/filter works by game, price, rank
- ✅ Category pages show all listings for that game
- ✅ Listing details page shows complete info

### Seller Management Flow
- ✅ Sellers can create listings with mediator selection
- ✅ Listings go to PENDING status automatically
- ✅ Minimum 3 mediator validation works
- ✅ Max 3 images validation works
- ✅ Sellers can view listings by status (tabs)
- ✅ Profile management works (avatar, bio, username)
- ✅ Password change works without OTP
- ✅ Trade history shows all deals with status

### Data Integrity
- ✅ All migrations run successfully
- ✅ Foreign key constraints enforced
- ✅ Unique constraints enforced
- ✅ Status transitions validated

---

## 📊 API Response Formats

### Category Response
```json
{
  "id": 1,
  "name": "PUBG",
  "description": "PlayerUnknown's Battlegrounds",
  "icon_url": "https://cdn.../pubg.png",
  "is_active": true,
  "sort_order": 1,
  "listings_count": 150
}
```

### Featured Listing Response
```json
{
  "id": 123,
  "title": "PUBG Ace Account",
  "short_description": "High-level account...",
  "price": 50.00,
  "game_type": "pubg",
  "level": 85,
  "rank": "Ace",
  "primary_image": "https://...",
  "seller": {
    "id": 5,
    "username": "proseller",
    "rating": 4.8,
    "completed_deals": 42
  },
  "is_featured": true
}
```

### My Listings Response
```json
{
  "items": [
    {
      "id": 123,
      "title": "PUBG Ace Account",
      "price": 50.00,
      "status": "pending",
      "created_at": "2026-03-20T10:00:00Z",
      "views_count": 0
    }
  ],
  "pagination": {
    "next_cursor": "abc123",
    "has_more": true,
    "limit": 20
  }
}
```

### Trade History Response
```json
{
  "items": [
    {
      "id": 456,
      "listing": {
        "id": 123,
        "title": "PUBG Ace Account"
      },
      "role": "seller",
      "price": 50.00,
      "status": "completed",
      "created_at": "2026-03-15T14:30:00Z",
      "completed_at": "2026-03-16T10:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "limit": 20
  }
}
```

---

## 🚀 Implementation Order

1. **Database Layer (Day 1 Morning)**
   - Create new models (Deal, ListingMediator)
   - Update existing models (User, Listing, Enums)
   - Create migration
   - Run migration

2. **Schemas & Repositories (Day 1 Afternoon)**
   - Create all Pydantic schemas
   - Create all repositories
   - Test repositories

3. **Services & APIs (Day 2)**
   - Create all services
   - Create all API endpoints
   - Test each endpoint

4. **Integration & Testing (Day 2-3)**
   - Write comprehensive tests
   - Test complete flows
   - Fix bugs
   - Document APIs

---

**Next Step:** Implementation phase - create all files, run migrations, write tests.
