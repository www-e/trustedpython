# Database Schema

## 🗄️ Database Overview

**PostgreSQL 16** with **SQLAlchemy 2.0 async** ORM

**Design Principles:**
- ACID transactions for deal consistency
- Foreign keys with CASCADE rules
- Indexes for query performance
- Timestamps for audit trails
- Soft deletes for data recovery

---

## 📊 Entity Relationships

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│    User     │         │   Listing   │         │    Deal     │
│  (Buyer/    │─┐       │             │─┐       │             │
│   Seller)   │ │       │             │ │       │             │
└─────────────┘ │       └─────────────┘ │       └─────────────┘
               │         │               │         │
               │         │               │         │
               ▼         ▼               ▼         ▼
┌──────────────────────────────────────────────────────────┐
│                      Chat                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐      │
│  │Private:  │  │Private:  │  │     Group        │      │
│  │Buyer-    │  │Seller-   │  │Buyer+Seller+     │      │
│  │Mediator  │  │Mediator  │  │Mediator          │      │
│  └──────────┘  └──────────┘  └──────────────────┘      │
└──────────────────────────────────────────────────────────┘
               │
               ▼
        ┌─────────────┐
        │  Message    │
        └─────────────┘

┌─────────────┐         ┌─────────────┐
│  Mediator   │         │    Tier     │
│             │─┐   ┌───│             │
└─────────────┘ │   │   └─────────────┘
                │   │
                ▼   ▼
         ┌─────────────┐
         │  Assistant  │
         │ (Sub-account)│
         └─────────────┘
```

---

## 👥 Users Table

```python
# models/user.py

class User(Base, TimestampMixin):
    """Unified Buyer/Seller account"""
    __tablename__ = "users"

    # Primary Key
    id: int = Column(Integer, primary_key=True)

    # Authentication
    phone: str = Column(String(20), unique=True, nullable=False, index=True)
    hashed_password: str = Column(String(255), nullable=False)

    # Profile
    username: str = Column(String(50), unique=True, nullable=False)
    full_name: str = Column(String(100))
    avatar_url: str = Column(String(500), nullable=True)
    bio: str = Column(Text, nullable=True)

    # Status
    is_active: bool = Column(Boolean, default=True)
    is_verified: bool = Column(Boolean, default=False)  # Verified seller
    is_banned: bool = Column(Boolean, default=False)

    # Role (one of: user, mediator, admin)
    role: UserRole = Column(Enum(UserRole), default=UserRole.USER, nullable=False)

    # Statistics
    total_listings: int = Column(Integer, default=0)
    sold_count: int = Column(Integer, default=0)
    bought_count: int = Column(Integer, default=0)

    # Timestamps (from TimestampMixin)
    created_at: datetime = Column(DateTime, default=func.now())
    updated_at: datetime = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    listings: List["Listing"] = relationship("Listing", back_populates="seller")
    deals_buyer: List["Deal"] = relationship("Deal", foreign_keys="Deal.buyer_id", back_populates="buyer")
    deals_seller: List["Deal"] = relationship("Deal", foreign_keys="Deal.seller_id", back_populates="seller")
    chat_participations: List["ChatParticipant"] = relationship("ChatParticipant", back_populates="user")
    sent_messages: List["Message"] = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")

    # Indexes
    __table_args__ = (
        Index('ix_users_role', 'role'),
        Index('ix_users_is_active', 'is_active'),
        Index('ix_users_created_at', 'created_at'),
    )
```

---

## 📦 Listings Table

```python
# models/listing.py

class Listing(Base, TimestampMixin):
    """Gaming account for sale"""
    __tablename__ = "listings"

    # Primary Key
    id: int = Column(Integer, primary_key=True)

    # Foreign Keys
    seller_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id: int = Column(Integer, ForeignKey("categories.id"), nullable=False)

    # Listing Details
    title: str = Column(String(200), nullable=False)
    description: str = Column(Text, nullable=False)
    price: Decimal = Column(Numeric(10, 2), nullable=False)

    # Game/Account Specifics
    game: str = Column(String(50), nullable=False)  # pubg, freefire, etc
    rank: str = Column(String(50), nullable=True)  # ace, conqueror, etc
    level: int = Column(Integer, nullable=True)
    server: str = Column(String(50), nullable=True)

    # Images (comma-separated URLs or JSON array)
    images: List[str] = Column(ARRAY(String), nullable=False, default=[])

    # Status
    status: ListingStatus = Column(
        Enum(ListingStatus),
        default=ListingStatus.ACTIVE,
        nullable=False
    )

    # Deal reference (when sold)
    deal_id: int = Column(Integer, ForeignKey("deals.id", ondelete="SET NULL"), nullable=True)

    # Statistics
    views: int = Column(Integer, default=0)
    favorites: int = Column(Integer, default=0)

    # Timestamps
    created_at: datetime = Column(DateTime, default=func.now(), index=True)
    updated_at: datetime = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    seller: User = relationship("User", foreign_keys=[seller_id], back_populates="listings")
    category: Category = relationship("Category", back_populates="listings")
    deal: Deal = relationship("Deal", foreign_keys=[deal_id], back_populates="listing")

    # Indexes
    __table_args__ = (
        Index('ix_listings_seller_id', 'seller_id'),
        Index('ix_listings_category_id', 'category_id'),
        Index('ix_listings_status', 'status'),
        Index('ix_listings_price', 'price'),
        Index('ix_listings_game', 'game'),
        Index('ix_listings_created_at', 'created_at'),
        # Composite index for filtering
        Index('ix_listings_status_game', 'status', 'game'),
    )
```

---

## 💰 Deals Table

```python
# models/deal.py

class Deal(Base, TimestampMixin):
    """Transaction between buyer and seller mediated by third party"""
    __tablename__ = "deals"

    # Primary Key
    id: int = Column(Integer, primary_key=True)

    # Foreign Keys
    listing_id: int = Column(Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    buyer_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    seller_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mediator_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Deal Status
    status: DealStatus = Column(
        Enum(DealStatus),
        default=DealStatus.PENDING,
        nullable=False
    )

    # Timestamps for workflow
    requested_at: datetime = Column(DateTime, default=func.now())
    accepted_at: datetime = Column(DateTime, nullable=True)
    payment_verified_at: datetime = Column(DateTime, nullable=True)
    credentials_verified_at: datetime = Column(DateTime, nullable=True)
    closed_at: datetime = Column(DateTime, nullable=True)

    # Final price (may differ from listing if negotiated)
    final_price: Decimal = Column(Numeric(10, 2), nullable=True)

    # Payment method (for tracking)
    payment_method: str = Column(String(50), nullable=True)  # vodafone, crypto, bank_transfer

    # Cancellation reason (if applicable)
    cancellation_reason: str = Column(Text, nullable=True)
    cancelled_by: int = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    listing: Listing = relationship("Listing", foreign_keys=[listing_id], back_populates="deal")
    buyer: User = relationship("User", foreign_keys=[buyer_id], back_populates="deals_buyer")
    seller: User = relationship("User", foreign_keys=[seller_id], back_populates="deals_seller")
    mediator: User = relationship("User", foreign_keys=[mediator_id])
    chats: List["Chat"] = relationship("Chat", back_populates="deal")

    # Indexes
    __table_args__ = (
        Index('ix_deals_listing_id', 'listing_id'),
        Index('ix_deals_buyer_id', 'buyer_id'),
        Index('ix_deals_seller_id', 'seller_id'),
        Index('ix_deals_mediator_id', 'mediator_id'),
        Index('ix_deals_status', 'status'),
        Index('ix_deals_created_at', 'created_at'),
    )
```

---

## 💬 Chats Table

```python
# models/chat.py

class Chat(Base, TimestampMixin):
    """Chat room for deal communication"""
    __tablename__ = "chats"

    # Primary Key
    id: int = Column(Integer, primary_key=True)

    # Foreign Keys
    deal_id: int = Column(Integer, ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    # Chat Type
    chat_type: ChatType = Column(
        Enum(ChatType),
        nullable=False
    )  # GROUP, BUYER_MEDIATOR_PRIVATE, SELLER_MEDIATOR_PRIVATE

    # Chat metadata
    name: str = Column(String(100), nullable=False)  # e.g., "Deal #123 - Group Chat"
    is_read_only: bool = Column(Boolean, default=False)  # True when deal closed

    # Timestamps
    created_at: datetime = Column(DateTime, default=func.now())

    # Relationships
    deal: Deal = relationship("Deal", back_populates="chats")
    participants: List["ChatParticipant"] = relationship("ChatParticipant", back_populates="chat")
    messages: List["Message"] = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_chats_deal_id', 'deal_id'),
        Index('ix_chats_type', 'chat_type'),
    )
```

### Chat Participants Table

```python
class ChatParticipant(Base):
    """Many-to-many relationship between users and chats"""
    __tablename__ = "chat_participants"

    id: int = Column(Integer, primary_key=True)
    chat_id: int = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    user_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Read tracking
    last_read_at: datetime = Column(DateTime, nullable=True)
    unread_count: int = Column(Integer, default=0)

    # Timestamp
    joined_at: datetime = Column(DateTime, default=func.now())

    # Relationships
    chat: Chat = relationship("Chat", back_populates="participants")
    user: User = relationship("User", back_populates="chat_participations")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('chat_id', 'user_id', name='uq_chat_user'),
        Index('ix_chat_participants_chat_id', 'chat_id'),
        Index('ix_chat_participants_user_id', 'user_id'),
    )
```

### Messages Table

```python
class Message(Base, TimestampMixin):
    """Chat message"""
    __tablename__ = "messages"

    # Primary Key
    id: int = Column(Integer, primary_key=True)

    # Foreign Keys
    chat_id: int = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    sender_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Message content
    content: str = Column(Text, nullable=False)
    message_type: MessageType = Column(
        Enum(MessageType),
        default=MessageType.TEXT,
        nullable=False
    )  # TEXT, IMAGE, SYSTEM, PROOF

    # Attachments (for image/proof messages)
    attachment_url: str = Column(String(500), nullable=True)

    # Timestamp
    created_at: datetime = Column(DateTime, default=func.now(), index=True)

    # Relationships
    chat: Chat = relationship("Chat", back_populates="messages")
    sender: User = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")

    # Indexes
    __table_args__ = (
        Index('ix_messages_chat_id_created_at', 'chat_id', 'created_at'),
        Index('ix_messages_sender_id', 'sender_id'),
    )
```

---

## 🎯 Mediators & Tiers

### Mediator Profile Table

```python
# models/mediator.py

class Mediator(Base, TimestampMixin):
    """Mediator-specific profile"""
    __tablename__ = "mediators"

    # Primary Key
    id: int = Column(Integer, primary_key=True)

    # Foreign Key
    user_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Tier assignment
    tier_id: int = Column(Integer, ForeignKey("tiers.id"), nullable=False)

    # Mediator stats
    total_deals: int = Column(Integer, default=0)
    successful_deals: int = Column(Integer, default=0)
    cancelled_deals: int = Column(Integer, default=0)
    average_rating: Decimal = Column(Numeric(3, 2), nullable=True)
    response_time_minutes: int = Column(Integer, default=0)  # Average

    # Current usage (for tier limits)
    active_deals: int = Column(Integer, default=0)  # Current concurrent deals
    assistant_count: int = Column(Integer, default=0)  # Current assistants

    # Status
    is_online: bool = Column(Boolean, default=False)
    is_available: bool = Column(Boolean, default=True)  # Manually toggle availability

    # Timestamps
    created_at: datetime = Column(DateTime, default=func.now())
    updated_at: datetime = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user: User = relationship("User")
    tier: Tier = relationship("Tier", back_populates="mediators")
    assistants: List["MediatorAssistant"] = relationship("MediatorAssistant", back_populates="mediator", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_mediators_user_id', 'user_id'),
        Index('ix_mediators_tier_id', 'tier_id'),
        Index('ix_mediators_is_online', 'is_online'),
        Index('ix_mediators_is_available', 'is_available'),
    )
```

### Tier Table

```python
# models/tier.py

class Tier(Base):
    """Mediator subscription tier"""
    __tablename__ = "tiers"

    # Primary Key
    id: int = Column(Integer, primary_key=True)

    # Tier details
    name: str = Column(String(50), unique=True, nullable=False)  # bronze, silver, gold, platinum
    display_name: str = Column(String(100), nullable=False)
    badge_url: str = Column(String(500), nullable=True)

    # Limits
    max_concurrent_deals: int = Column(Integer, nullable=False)
    max_assistants: int = Column(Integer, default=0)
    can_reopen_closed_chats: bool = Column(Boolean, default=False)

    # Display priority (for sorting)
    display_order: int = Column(Integer, default=0)

    # Timestamp
    created_at: datetime = Column(DateTime, default=func.now())

    # Relationships
    mediators: List["Mediator"] = relationship("Mediator", back_populates="tier")

    # Indexes
    __table_args__ = (
        Index('ix_tiers_name', 'name'),
        Index('ix_tiers_display_order', 'display_order'),
    )
```

### Mediator Assistant Table

```python
class MediatorAssistant(Base):
    """Sub-account for mediator assistants"""
    __tablename__ = "mediator_assistants"

    # Primary Key
    id: int = Column(Integer, primary_key=True)

    # Foreign Key
    mediator_id: int = Column(Integer, ForeignKey("mediators.id", ondelete="CASCADE"), nullable=False)

    # Assistant credentials
    username: str = Column(String(50), unique=True, nullable=False)
    hashed_password: str = Column(String(255), nullable=False)

    # Status
    is_active: bool = Column(Boolean, default=True)

    # Timestamps
    created_at: datetime = Column(DateTime, default=func.now())
    last_login_at: datetime = Column(DateTime, nullable=True)

    # Relationships
    mediator: Mediator = relationship("Mediator", back_populates="assistants")

    # Indexes
    __table_args__ = (
        Index('ix_mediator_assistants_mediator_id', 'mediator_id'),
        Index('ix_mediator_assistants_username', 'username'),
    )
```

---

## 📁 Categories Table

```python
# models/category.py

class Category(Base):
    """Game categories"""
    __tablename__ = "categories"

    # Primary Key
    id: int = Column(Integer, primary_key=True)

    # Category details
    name: str = Column(String(100), unique=True, nullable=False)  # PUBG, Free Fire
    slug: str = Column(String(100), unique=True, nullable=False)  # pubg, free-fire
    icon_url: str = Column(String(500), nullable=True)

    # Display
    display_order: int = Column(Integer, default=0)
    is_active: bool = Column(Boolean, default=True)

    # Timestamps
    created_at: datetime = Column(DateTime, default=func.now())

    # Relationships
    listings: List["Listing"] = relationship("Listing", back_populates="category")

    # Indexes
    __table_args__ = (
        Index('ix_categories_slug', 'slug'),
        Index('ix_categories_display_order', 'display_order'),
    )
```

---

## 🔔 Notifications Table

```python
# models/notification.py

class Notification(Base):
    """User notifications"""
    __tablename__ = "notifications"

    # Primary Key
    id: int = Column(Integer, primary_key=True)

    # Foreign Key
    user_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Notification details
    type: NotificationType = Column(Enum(NotificationType), nullable=False)
    title: str = Column(String(200), nullable=False)
    body: str = Column(Text, nullable=False)

    # Related entity (optional)
    deal_id: int = Column(Integer, ForeignKey("deals.id", ondelete="SET NULL"), nullable=True)
    chat_id: int = Column(Integer, ForeignKey("chats.id", ondelete="SET NULL"), nullable=True)

    # Status
    is_read: bool = Column(Boolean, default=False)
    read_at: datetime = Column(DateTime, nullable=True)

    # Push notification status
    push_sent: bool = Column(Boolean, default=False)
    push_sent_at: datetime = Column(DateTime, nullable=True)

    # Timestamp
    created_at: datetime = Column(DateTime, default=func.now(), index=True)

    # Indexes
    __table_args__ = (
        Index('ix_notifications_user_id', 'user_id'),
        Index('ix_notifications_is_read', 'is_read'),
        Index('ix_notifications_created_at', 'created_at'),
    )
```

---

## 🔒 Enums

```python
# models/enums.py

from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    MEDIATOR = "mediator"
    ADMIN = "admin"

class ListingStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"  # Deal in progress
    SOLD = "sold"
    ARCHIVED = "archived"

class DealStatus(str, Enum):
    PENDING = "pending"           # Awaiting mediator acceptance
    ACCEPTED = "accepted"         # Mediator accepted, deal active
    PAYMENT_VERIFIED = "payment_verified"
    CREDENTIALS_VERIFIED = "credentials_verified"
    COMPLETED = "completed"       # Deal closed successfully
    CANCELLED = "cancelled"

class ChatType(str, Enum):
    GROUP = "group"  # Buyer + Seller + Mediator
    BUYER_MEDIATOR_PRIVATE = "buyer_mediator_private"
    SELLER_MEDIATOR_PRIVATE = "seller_mediator_private"

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    SYSTEM = "system"  # Auto-generated messages
    PROOF = "proof"    # Payment proof, credential proof

class NotificationType(str, Enum):
    DEAL_REQUEST = "deal_request"
    DEAL_ACCEPTED = "deal_accepted"
    DEAL_CLOSED = "deal_closed"
    NEW_MESSAGE = "new_message"
    PROOF_UPLOADED = "proof_uploaded"
    LISTING_SOLD = "listing_sold"
}
```

---

## 🔄 Database Migrations

### Migration Workflow

```bash
# Generate migration
alembic revision --autogenerate -m "Add listings table"

# Apply migration
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# View migration history
alembic history
```

### Migration File Structure

```python
# migrations/versions/001_initial.py

"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-14
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        # ... more columns
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_phone', 'users', ['phone'], unique=True)

def downgrade():
    op.drop_index('ix_users_phone', table_name='users')
    op.drop_table('users')
```

---

## 📊 Performance Indexes

### Critical Indexes

```sql
-- User authentication
CREATE INDEX ix_users_phone ON users(phone);

-- Listing browsing
CREATE INDEX ix_listings_status_game ON listings(status, game);
CREATE INDEX ix_listings_seller_id ON listings(seller_id);
CREATE INDEX ix_listings_created_at ON listings(created_at DESC);

-- Deal queries
CREATE INDEX ix_deals_buyer_id_status ON deals(buyer_id, status);
CREATE INDEX ix_deals_seller_id_status ON deals(seller_id, status);
CREATE INDEX ix_deals_mediator_id_status ON deals(mediator_id, status);

-- Chat messages
CREATE INDEX ix_messages_chat_id_created_at ON messages(chat_id, created_at DESC);

-- Full-text search
CREATE INDEX ix_listings_fts ON listings USING gin(to_tsvector('english', title || ' ' || description));
```

---

## 📚 Related Documentation

- [Architecture Design](../02-Architecture-Design.md) - How database fits into architecture
- [API Structure](./API-Structure.md) - How models map to API responses
- [Realtime Architecture](../architecture/Realtime-Architecture.md) - Real-time data updates

---

**Last Updated**: 2026-03-14
**Version**: 0.1.0
