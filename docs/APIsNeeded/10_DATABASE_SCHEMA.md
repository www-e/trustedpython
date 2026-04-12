# 10 - Database Schema

> **Database:** PostgreSQL 15+  
> **ORM:** SQLAlchemy + Alembic  
> **Cache:** Redis  
> **Status:** Ready for implementation

---

## Schema Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       ENTITIES                              │
├─────────────────────────────────────────────────────────────┤
│  1. users               - User accounts                     │
│  2. user_profiles       - Extended user info                │
│  3. sessions            - Auth sessions/tokens              │
│  4. accounts            - Game accounts for sale            │
│  5. account_images      - Account images                    │
│  6. account_features  - Account features/badges             │
│  7. listings            - User listings                     │
│  8. deals               - Transactions                      │
│  9. payments            - Payment records                   │
│  10. mediators          - Mediator profiles                 │
│  11. mediator_badges    - Mediator achievements             │
│  12. chat_rooms         - Chat conversations                │
│  13. chat_participants  - Room memberships                  │
│  14. messages           - Chat messages                     │
│  15. message_attachments- Message files                     │
│  16. notifications      - User notifications                │
│  17. notification_prefs - User notif settings               │
│  18. games              - Supported games                   │
│  19. categories         - Listing categories                │
│  20. reviews            - User reviews                      │
│  21. promo_banners      - Marketing banners                 │
│  22. faq_items          - FAQ content                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. users

Core user authentication and identity.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_email_verified BOOLEAN DEFAULT FALSE,
    email_verified_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_suspended BOOLEAN DEFAULT FALSE,
    suspension_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
```

---

## 2. user_profiles

Extended user profile information.

```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    display_name VARCHAR(100),
    avatar_url VARCHAR(500),
    bio TEXT,
    user_role VARCHAR(50) DEFAULT 'Trader',
    is_verified BOOLEAN DEFAULT FALSE,
    member_since DATE,
    completed_deals INTEGER DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0.00,
    accounts_sold INTEGER DEFAULT 0,
    bought_count INTEGER DEFAULT 0,
    total_revenue DECIMAL(12,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
```

---

## 3. sessions

Authentication sessions and tokens.

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    access_token_hash VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255),
    device_info JSONB,
    ip_address INET,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_access_token ON sessions(access_token_hash);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
```

---

## 4. accounts (listings)

Game accounts available for sale.

```sql
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    game VARCHAR(100) NOT NULL,
    rank VARCHAR(100),
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'EGP',
    description TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    is_featured BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'active', -- active, sold, expired
    views_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    sold_at TIMESTAMP
);

CREATE INDEX idx_accounts_seller_id ON accounts(seller_id);
CREATE INDEX idx_accounts_game ON accounts(game);
CREATE INDEX idx_accounts_status ON accounts(status);
CREATE INDEX idx_accounts_price ON accounts(price);
CREATE INDEX idx_accounts_created_at ON accounts(created_at DESC);
```

---

## 5. account_images

Images for game accounts.

```sql
CREATE TABLE account_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    filename VARCHAR(255),
    size_bytes INTEGER,
    width INTEGER,
    height INTEGER,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_account_images_account_id ON account_images(account_id);
```

---

## 6. account_features

Features/badges for accounts.

```sql
CREATE TABLE account_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    icon VARCHAR(100) NOT NULL,
    label VARCHAR(200) NOT NULL
);

CREATE INDEX idx_account_features_account_id ON account_features(account_id);
```

---

## 7. listings

User-created listings (alternative to accounts).

```sql
CREATE TABLE listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    game VARCHAR(100),
    category_id UUID,
    description TEXT,
    thumbnail_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'draft', -- draft, active, sold, expired
    is_premium BOOLEAN DEFAULT FALSE,
    tier VARCHAR(20) DEFAULT 'Regular', -- Regular, Gold, Elite
    views_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP,
    expired_at TIMESTAMP
);

CREATE INDEX idx_listings_seller_id ON listings(seller_id);
CREATE INDEX idx_listings_status ON listings(status);
CREATE INDEX idx_listings_game ON listings(game);
CREATE INDEX idx_listings_created_at ON listings(created_at DESC);
```

---

## 8. deals

Transactions between buyers, sellers, and mediators.

```sql
CREATE TABLE deals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    listing_id UUID REFERENCES listings(id),
    buyer_id UUID REFERENCES users(id),
    seller_id UUID REFERENCES users(id),
    mediator_id UUID,
    status VARCHAR(30) DEFAULT 'pending',
    -- pending, awaiting_payment, payment_submitted, verified, completed, cancelled, disputed
    total_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'EGP',
    notes TEXT,
    chat_room_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    cancellation_reason TEXT
);

CREATE INDEX idx_deals_buyer_id ON deals(buyer_id);
CREATE INDEX idx_deals_seller_id ON deals(seller_id);
CREATE INDEX idx_deals_mediator_id ON deals(mediator_id);
CREATE INDEX idx_deals_status ON deals(status);
CREATE INDEX idx_deals_created_at ON deals(created_at DESC);
```

---

## 9. payments

Payment records for deals.

```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id UUID UNIQUE REFERENCES deals(id) ON DELETE CASCADE,
    screenshot_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending',
    -- pending, submitted, verified, rejected
    submitted_at TIMESTAMP,
    verified_at TIMESTAMP,
    verified_by UUID REFERENCES users(id),
    rejection_reason TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_payments_deal_id ON payments(deal_id);
CREATE INDEX idx_payments_status ON payments(status);
```

---

## 10. mediators

Mediator profiles.

```sql
CREATE TABLE mediators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    rating DECIMAL(3,2) DEFAULT 0.00,
    program_rating DECIMAL(3,2) DEFAULT 0.00,
    transactions_count INTEGER DEFAULT 0,
    specialization VARCHAR(100),
    response_time VARCHAR(100),
    is_online BOOLEAN DEFAULT TRUE,
    tier VARCHAR(20) DEFAULT 'bronze', -- bronze, silver, gold, elite
    is_verified BOOLEAN DEFAULT FALSE,
    bio TEXT,
    avg_response_time_minutes INTEGER,
    success_rate DECIMAL(5,2),
    member_since DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mediators_user_id ON mediators(user_id);
CREATE INDEX idx_mediators_tier ON mediators(tier);
CREATE INDEX idx_mediators_rating ON mediators(rating DESC);
```

---

## 11. mediator_badges

Mediator achievements.

```sql
CREATE TABLE mediator_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mediator_id UUID REFERENCES mediators(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(100) NOT NULL,
    description TEXT,
    earned_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mediator_badges_mediator_id ON mediator_badges(mediator_id);
```

---

## 12. chat_rooms

Chat conversations.

```sql
CREATE TABLE chat_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200),
    avatar VARCHAR(500),
    type VARCHAR(20) NOT NULL, -- group, private
    is_active BOOLEAN DEFAULT TRUE,
    deal_id UUID REFERENCES deals(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chat_rooms_type ON chat_rooms(type);
CREATE INDEX idx_chat_rooms_deal_id ON chat_rooms(deal_id);
```

---

## 13. chat_participants

Room memberships.

```sql
CREATE TABLE chat_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID REFERENCES chat_rooms(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member', -- admin, member
    joined_at TIMESTAMP DEFAULT NOW(),
    left_at TIMESTAMP,
    UNIQUE(room_id, user_id)
);

CREATE INDEX idx_chat_participants_room_id ON chat_participants(room_id);
CREATE INDEX idx_chat_participants_user_id ON chat_participants(user_id);
```

---

## 14. messages

Chat messages.

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID REFERENCES chat_rooms(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES users(id),
    content TEXT NOT NULL,
    type VARCHAR(20) DEFAULT 'text', -- text, image, system
    reply_to_message_id UUID REFERENCES messages(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_room_id ON messages(room_id);
CREATE INDEX idx_messages_sender_id ON messages(sender_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
```

---

## 15. message_attachments

File attachments for messages.

```sql
CREATE TABLE message_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    filename VARCHAR(255),
    size_bytes INTEGER,
    mime_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_message_attachments_message_id ON message_attachments(message_id);
```

---

## 16. notifications

User notifications.

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    type VARCHAR(30) NOT NULL,
    -- account_update, message, security_alert, purchase, system
    is_read BOOLEAN DEFAULT FALSE,
    icon VARCHAR(100),
    action_url VARCHAR(500),
    metadata JSONB,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
```

---

## 17. notification_prefs

User notification preferences.

```sql
CREATE TABLE notification_prefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    push_notifications BOOLEAN DEFAULT TRUE,
    email_notifications BOOLEAN DEFAULT TRUE,
    types JSONB DEFAULT '{
        "account_update": {"enabled": true, "push": true, "email": true},
        "message": {"enabled": true, "push": true, "email": true},
        "security_alert": {"enabled": true, "push": true, "email": true},
        "purchase": {"enabled": true, "push": true, "email": true},
        "system": {"enabled": true, "push": true, "email": true}
    }',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 18. games

Supported games.

```sql
CREATE TABLE games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    icon_url VARCHAR(500),
    banner_url VARCHAR(500),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_popular BOOLEAN DEFAULT FALSE,
    is_trending BOOLEAN DEFAULT FALSE,
    active_listings INTEGER DEFAULT 0,
    avg_price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_games_slug ON games(slug);
CREATE INDEX idx_games_is_popular ON games(is_popular);
```

---

## 19. categories

Listing categories.

```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    icon VARCHAR(100),
    description TEXT,
    game_id UUID REFERENCES games(id),
    is_active BOOLEAN DEFAULT TRUE,
    listing_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 20. reviews

User reviews for mediators/sellers.

```sql
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reviewer_id UUID REFERENCES users(id),
    reviewee_id UUID REFERENCES users(id),
    deal_id UUID REFERENCES deals(id),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_reviews_reviewee_id ON reviews(reviewee_id);
CREATE INDEX idx_reviews_deal_id ON reviews(deal_id);
CREATE INDEX idx_reviews_created_at ON reviews(created_at DESC);
```

---

## 21. promo_banners

Marketing banners.

```sql
CREATE TABLE promo_banners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    subtitle VARCHAR(300),
    image_url VARCHAR(500) NOT NULL,
    action_url VARCHAR(500),
    action_text VARCHAR(100),
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_promo_banners_is_active ON promo_banners(is_active);
CREATE INDEX idx_promo_banners_priority ON promo_banners(priority);
```

---

## 22. faq_items

FAQ content.

```sql
CREATE TABLE faq_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question VARCHAR(300) NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100),
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_faq_items_category ON faq_items(category);
CREATE INDEX idx_faq_items_display_order ON faq_items(display_order);
```

---

## Redis Cache Strategy

### What to Cache

| Key Pattern | TTL | Purpose |
|-------------|-----|---------|
| `user:{id}` | 1h | User profile data |
| `user:stats:{id}` | 30m | User statistics |
| `account:{id}` | 1h | Account details |
| `accounts:featured` | 6h | Featured accounts |
| `games:all` | 24h | All games list |
| `categories:all` | 24h | All categories |
| `home:feed:{page}` | 30m | Home feed pages |
| `mediator:{id}` | 1h | Mediator profile |
| `notifications:unread:{id}` | 5m | Unread count |
| `session:{token}` | 1h | Session validation |
| `rate_limit:{endpoint}:{ip}` | 1m | Rate limiting |

### Pub/Sub Channels

| Channel | Purpose |
|---------|---------|
| `chat:new_message:{room_id}` | Real-time message delivery |
| `notifications:{user_id}` | Push notifications |
| `deal:status:{deal_id}` | Deal status updates |
| `user:online:{user_id}` | User presence tracking |

---

## Indexes for Performance

### Composite Indexes

```sql
-- Fast account browsing by game and price
CREATE INDEX idx_accounts_game_price ON accounts(game, price);

-- Fast deal lookup by user and status
CREATE INDEX idx_deals_user_status ON deals(buyer_id, status);
CREATE INDEX idx_deals_seller_status ON deals(seller_id, status);

-- Fast message retrieval by room and time
CREATE INDEX idx_messages_room_time ON messages(room_id, created_at DESC);

-- Fast notifications by user and read status
CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read, created_at DESC);
```

---

## Migration Strategy

Use Alembic for schema migrations:

```bash
# Create new migration
alembic revision --autogenerate -m "create users table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Data Integrity

### Foreign Key Constraints
All relationships use `ON DELETE CASCADE` or `ON DELETE SET NULL` to prevent orphaned records.

### Check Constraints
```sql
ALTER TABLE accounts ADD CONSTRAINT chk_price_positive CHECK (price > 0);
ALTER TABLE reviews ADD CONSTRAINT chk_rating_range CHECK (rating >= 1 AND rating <= 5);
```

### Triggers
```sql
-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```
