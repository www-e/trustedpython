# Notifications Integration Guide

## Quick Start for Developers

This guide shows how to integrate notifications into your modules.

## Basic Usage

### 1. Import Helper Functions

```python
from app.services.notification_helpers import (
    notify_new_message,
    notify_deal_initiated,
    notify_payment_confirmed,
    notify_account_verified,
    notify_password_changed,
    notify_new_login
)
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationType
```

### 2. Create Simple Notification

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def send_custom_notification(
    db: AsyncSession,
    user_id: UUID
):
    """Send a simple notification."""
    notification = await NotificationService.create_notification(
        db=db,
        user_id=user_id,
        title="Custom Event",
        description="Something happened!",
        notification_type=NotificationType.SYSTEM,
        icon="event",
        action_url="/custom/path",
        metadata={"custom_field": "value"}
    )

    return notification
```

## Integration Examples

### Chat Module Integration

```python
# In app/services/chat_service.py

from app.services.notification_helpers import notify_new_message

async def send_message(
    db: AsyncSession,
    conversation_id: UUID,
    sender_id: UUID,
    content: str
):
    """Send a message and notify recipients."""

    # 1. Create message in database
    message = await create_message_in_db(
        db=db,
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content
    )

    # 2. Get conversation participants
    participants = await get_conversation_participants(
        db=db,
        conversation_id=conversation_id
    )

    # 3. Get sender info
    sender = await get_user_by_id(db=db, user_id=sender_id)

    # 4. Send notification to all participants except sender
    for participant in participants:
        if participant.id != sender_id:
            await notify_new_message(
                db=db,
                recipient_id=participant.id,
                sender_name=mask_username(sender.username),
                message_preview=content,
                conversation_id=conversation_id
            )

    return message
```

### Deals/Orders Module Integration

```python
# In app/services/deal_service.py

from app.services.notification_helpers import (
    notify_deal_initiated,
    notify_payment_confirmed
)

async def create_deal(
    db: AsyncSession,
    listing_id: UUID,
    buyer_id: UUID
):
    """Create a new deal and notify parties."""

    # 1. Get listing and seller info
    listing = await get_listing(db=db, listing_id=listing_id)
    seller_id = listing.seller_id

    # 2. Create deal in database
    deal = await create_deal_in_db(
        db=db,
        listing_id=listing_id,
        buyer_id=buyer_id,
        seller_id=seller_id
    )

    # 3. Get user info
    buyer = await get_user_by_id(db=db, user_id=buyer_id)

    # 4. Send notifications
    await notify_deal_initiated(
        db=db,
        buyer_id=buyer_id,
        seller_id=seller_id,
        deal_id=deal.id,
        listing_title=listing.title,
        counterparty_name=mask_username(buyer.username)
    )

    return deal

async def confirm_payment(
    db: AsyncSession,
    deal_id: UUID
):
    """Confirm payment and notify seller."""

    # 1. Get deal info
    deal = await get_deal(db=db, deal_id=deal_id)

    # 2. Update deal status
    deal.status = "payment_confirmed"
    await db.commit()

    # 3. Get listing info
    listing = await get_listing(db=db, listing_id=deal.listing_id)

    # 4. Notify seller
    await notify_payment_confirmed(
        db=db,
        seller_id=deal.seller_id,
        deal_id=deal.id,
        listing_title=listing.title,
        amount=float(deal.price),
        currency=deal.currency
    )

    return deal
```

### Auth Module Integration

```python
# In app/services/auth_service.py

from app.services.notification_helpers import (
    notify_password_changed,
    notify_new_login,
    notify_account_verified
)

async def change_password(
    db: AsyncSession,
    user_id: UUID,
    new_password: str
):
    """Change password and notify user."""

    # 1. Update password in database
    await update_user_password(
        db=db,
        user_id=user_id,
        new_password=new_password
    )

    # 2. Send notification
    await notify_password_changed(db=db, user_id=user_id)

async def handle_login(
    db: AsyncSession,
    user_id: UUID,
    ip_address: str,
    user_agent: str
):
    """Handle login and detect unusual activity."""

    # 1. Create login record
    await create_login_history(
        db=db,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent
    )

    # 2. Check for unusual login (new device, new location)
    is_unusual = await check_unusual_login(
        db=db,
        user_id=user_id,
        ip_address=ip_address
    )

    # 3. Notify if unusual
    if is_unusual:
        device_info = parse_user_agent(user_agent)
        location = await get_location_from_ip(ip_address)

        await notify_new_login(
            db=db,
            user_id=user_id,
            device_info=device_info,
            location=location
        )

async def verify_account(
    db: AsyncSession,
    user_id: UUID
):
    """Verify user account and notify them."""

    # 1. Update user verification status
    await update_user_verification(
        db=db,
        user_id=user_id,
        is_verified=True
    )

    # 2. Send notification
    await notify_account_verified(db=db, user_id=user_id)
```

### Admin Module Integration

```python
# In app/services/admin_service.py

from app.services.notification_helpers import (
    notify_listing_approved,
    notify_listing_rejected,
    notify_system_maintenance
)

async def approve_listing(
    db: AsyncSession,
    listing_id: UUID,
    admin_id: UUID
):
    """Approve a listing and notify seller."""

    # 1. Get listing
    listing = await get_listing(db=db, listing_id=listing_id)

    # 2. Update status
    listing.status = "approved"
    listing.reviewed_by = admin_id
    await db.commit()

    # 3. Notify seller
    await notify_listing_approved(
        db=db,
        seller_id=listing.seller_id,
        listing_id=listing.id,
        listing_title=listing.title
    )

async def reject_listing(
    db: AsyncSession,
    listing_id: UUID,
    reason: str
):
    """Reject a listing and notify seller."""

    # 1. Get listing
    listing = await get_listing(db=db, listing_id=listing_id)

    # 2. Update status
    listing.status = "rejected"
    listing.rejection_reason = reason
    await db.commit()

    # 3. Notify seller
    await notify_listing_rejected(
        db=db,
        seller_id=listing.seller_id,
        listing_id=listing.id,
        listing_title=listing.title,
        reason=reason
    )

async def schedule_maintenance(
    db: AsyncSession,
    scheduled_time: str
):
    """Schedule maintenance and notify users."""

    # 1. Create maintenance record
    await create_maintenance_event(
        db=db,
        scheduled_time=scheduled_time
    )

    # 2. Get active users
    active_users = await get_active_users(db=db)

    # 3. Send notifications
    await notify_system_maintenance(
        db=db,
        scheduled_time=scheduled_time,
        affected_users=[u.id for u in active_users]
    )
```

## Custom Notification Creation

### Create Custom Notification Type

```python
async def notify_custom_event(
    db: AsyncSession,
    user_id: UUID,
    event_data: dict
):
    """Create a custom notification."""

    notification = await NotificationService.create_notification(
        db=db,
        user_id=user_id,
        title=event_data["title"],
        description=event_data["description"],
        notification_type=NotificationType.SYSTEM,
        icon=event_data.get("icon", "info"),
        action_url=event_data.get("action_url"),
        metadata={
            "event_type": "custom_event",
            "data": event_data
        }
    )

    return notification
```

### Bulk Notifications

```python
async def notify_bulk_users(
    db: AsyncSession,
    user_ids: list[UUID],
    title: str,
    description: str
):
    """Send notification to multiple users."""

    notifications = []
    for user_id in user_ids:
        try:
            notification = await NotificationService.create_notification(
                db=db,
                user_id=user_id,
                title=title,
                description=description,
                notification_type=NotificationType.SYSTEM,
                metadata={"bulk": True}
            )
            notifications.append(notification)
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")

    return notifications
```

## Testing Notification Integration

### Unit Test Example

```python
import pytest
from app.services.notification_helpers import notify_new_message
from app.services.notification_service import NotificationService

@pytest.mark.asyncio
async def test_new_message_notification(db_session):
    """Test that new message creates notification."""

    # Arrange
    sender = create_test_user(username="sender")
    recipient = create_test_user(username="recipient")
    conversation = create_test_conversation()
    await db_session.add_all([sender, recipient, conversation])
    await db_session.commit()

    # Act
    await notify_new_message(
        db=db_session,
        recipient_id=recipient.id,
        sender_name="sender",
        message_preview="Hello!",
        conversation_id=conversation.id
    )

    # Assert
    notifications = await NotificationService.get_user_notifications(
        db=db_session,
        user_id=recipient.id
    )

    assert len(notifications.notifications) == 1
    assert notifications.notifications[0].type == NotificationType.MESSAGE
    assert notifications.notifications[0].title == "New message from sender"
```

### Integration Test Example

```python
@pytest.mark.asyncio
async def test_deal_flow_notifications(db_session):
    """Test notifications throughout deal lifecycle."""

    # Create deal
    deal = await create_deal(
        db_session,
        listing_id=listing.id,
        buyer_id=buyer.id
    )

    # Check seller notification
    seller_notifications = await NotificationService.get_user_notifications(
        db=db_session,
        user_id=seller.id
    )
    assert any(
        "purchase request" in n.description.lower()
        for n in seller_notifications.notifications
    )

    # Confirm payment
    await confirm_payment(db_session, deal_id=deal.id)

    # Check payment confirmation notification
    updated_notifications = await NotificationService.get_user_notifications(
        db=db_session,
        user_id=seller.id
    )
    assert any(
        "payment received" in n.description.lower()
        for n in updated_notifications.notifications
    )
```

## WebSocket Client Integration

### JavaScript/TypeScript Example

```typescript
class NotificationManager {
  private ws: WebSocket | null = null;
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  connect() {
    const wsUrl = `wss://api.example.com/api/v1/notifications/ws?token=${this.token}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleEvent(data);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private handleEvent(event: any) {
    switch (event.event) {
      case 'notification':
        this.onNotification(event.data);
        break;
      case 'badge_update':
        this.onBadgeUpdate(event.data);
        break;
      case 'notification_read':
        this.onNotificationRead(event.data);
        break;
      case 'notifications_cleared':
        this.onNotificationsCleared();
        break;
    }
  }

  private onNotification(notification: any) {
    // Show notification to user
    showToast({
      title: notification.title,
      body: notification.description,
      icon: notification.icon,
      onClick: () => {
        navigate(notification.action_url);
      }
    });

    // Update badge
    this.fetchUnreadCount();
  }

  private onBadgeUpdate(data: any) {
    // Update badge count
    updateBadgeCount(data.count);
  }

  private onNotificationRead(data: any) {
    // Remove notification from list
    removeNotification(data.notification_id);
  }

  private onNotificationsCleared() {
    // Clear all notifications
    clearAllNotifications();
  }

  private async fetchUnreadCount() {
    const response = await fetch('/api/v1/notifications/unread-count', {
      headers: {
        'Authorization': `Bearer ${this.token}`
      }
    });
    const data = await response.json();
    this.onBadgeUpdate(data.data);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

## Monitoring & Debugging

### Check Notification Creation

```python
# Log all notification creations
logger.info(f"Notification created: type={notification.type}, user_id={user_id}")

# Check notification count per user
notifications_count = await NotificationService.get_unread_count(db, user_id)
logger.info(f"User {user_id} has {notifications_count} unread notifications")
```

### Monitor Redis Messages

```bash
# Subscribe to notification channel
redis-cli
> SUBSCRIBE notifications:user_123

# Monitor all notification channels
redis-cli
> PSUBSCRIBE notifications:*
```

### Check Rate Limits

```python
# Check rate limit status
is_allowed = await rate_limit(
    key=f"create_notification:{user_id}",
    max_requests=10,
    window_seconds=60
)

if not is_allowed:
    logger.warning(f"Rate limit exceeded for user {user_id}")
```

## Best Practices

### 1. Use Descriptive Titles
```python
# Good
title="New message from seller_123"
title="Payment received: $50.00 USD"

# Bad
title="Update"
title="Notification"
```

### 2. Include Action URLs
```python
# Good
action_url="/chat/conversation_abc"
action_url="/deals/deal_123"

# Bad
action_url=None
action_url="/"
```

### 3. Use Appropriate Metadata
```python
# Good
metadata={
    "deal_id": str(deal.id),
    "listing_title": listing.title,
    "amount": float(deal.price),
    "type": "payment_confirmed"
}

# Bad
metadata={}
metadata={"data": "everything"}  # Too generic
```

### 4. Handle Errors Gracefully
```python
try:
    await notify_new_message(...)
except Exception as e:
    logger.error(f"Failed to send notification: {e}")
    # Continue with main operation
```

### 5. Don't Spam Notifications
```python
# Bad: Sending notification for every tiny update
for progress in range(100):
    await notify_progress(db, user_id, progress)

# Good: Batch important updates
if progress % 10 == 0 or progress == 100:
    await notify_progress(db, user_id, progress)
```

## Troubleshooting

### Notifications Not Appearing

1. **Check database:**
```python
result = await db.execute(
    select(Notification).where(Notification.user_id == user_id)
)
notifications = result.scalars().all()
print(f"Found {len(notifications)} notifications")
```

2. **Check Redis connection:**
```python
redis_client = await get_redis()
if redis_client:
    await redis_client.ping()
else:
    print("Redis not connected")
```

3. **Check WebSocket connection:**
```javascript
if (ws.readyState === WebSocket.OPEN) {
  console.log('WebSocket connected');
} else {
  console.log('WebSocket not connected');
}
```

### High Memory Usage

1. **Limit pagination size:**
```python
# Don't do this
notifications = await get_all_notifications(user_id)  # Thousands of records

# Do this instead
notifications = await get_user_notifications(
    user_id=user_id,
    page=1,
    limit=20  # Reasonable limit
)
```

2. **Use database indexes:**
```sql
-- Check query performance
EXPLAIN ANALYZE
SELECT * FROM notifications
WHERE user_id = '...' AND is_read = false
ORDER BY created_at DESC;
```

### Rate Limit Issues

1. **Check rate limit status:**
```python
# Current rate limit: 10 notifications per minute per user
# Adjust if needed in routes.py
is_allowed = await rate_limit(
    f"create_notification:{user_id}",
    max_requests=10,  # Adjust this
    window_seconds=60  # And this
)
```

## Conclusion

This guide provides everything you need to integrate notifications into your modules. For more details, see:
- `docs/APIsNeeded/03_NOTIFICATIONS.md` - API specification
- `docs/notifications_implementation_summary.md` - Implementation details
- `app/services/notification_helpers.py` - Helper functions
- `app/services/notification_service.py` - Core service
