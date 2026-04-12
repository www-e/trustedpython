"""
Tests for Chat REST API endpoints.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from httpx import AsyncClient

from app.models.user import User
from app.models.chat import ChatRoom, ChatParticipant, Message
from app.core.security import create_access_token


@pytest.fixture
async def test_chat_room(db_session):
    """Create a test chat room with participants."""
    # Create test users
    user1 = User(
        id=uuid4(),
        username="testuser1",
        email="test1@example.com",
        phone="1234567890",
        password_hash="hash",
        is_active=True
    )
    user2 = User(
        id=uuid4(),
        username="testuser2",
        email="test2@example.com",
        phone="1234567891",
        password_hash="hash",
        is_active=True
    )

    db_session.add(user1)
    db_session.add(user2)
    await db_session.commit()

    # Create chat room
    room = ChatRoom(
        id=uuid4(),
        name="Test Room",
        type="group",
        is_active=True
    )
    db_session.add(room)
    await db_session.commit()

    # Add participants
    participant1 = ChatParticipant(
        id=uuid4(),
        room_id=room.id,
        user_id=user1.id,
        role="admin"
    )
    participant2 = ChatParticipant(
        id=uuid4(),
        room_id=room.id,
        user_id=user2.id,
        role="member"
    )
    db_session.add(participant1)
    db_session.add(participant2)
    await db_session.commit()

    return room, user1, user2


@pytest.mark.asyncio
async def test_get_chat_rooms(client: AsyncClient, test_chat_room):
    """Test getting user's chat rooms."""
    room, user1, _ = test_chat_room

    # Create access token for user1
    token = create_access_token(data={"sub": str(user1.id)})

    # Get chat rooms
    response = await client.get(
        "/api/v1/chat/rooms",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "rooms" in data["data"]


@pytest.mark.asyncio
async def test_get_chat_room_details(client: AsyncClient, test_chat_room):
    """Test getting chat room details."""
    room, user1, _ = test_chat_room

    # Create access token for user1
    token = create_access_token(data={"sub": str(user1.id)})

    # Get room details
    response = await client.get(
        f"/api/v1/chat/rooms/{room.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == str(room.id)
    assert data["data"]["name"] == "Test Room"
    assert len(data["data"]["participants"]) == 2


@pytest.mark.asyncio
async def test_send_message(client: AsyncClient, test_chat_room):
    """Test sending a message."""
    room, user1, _ = test_chat_room

    # Create access token for user1
    token = create_access_token(data={"sub": str(user1.id)})

    # Send message
    response = await client.post(
        f"/api/v1/chat/rooms/{room.id}/messages",
        json={
            "content": "Hello, world!",
            "type": "text"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["content"] == "Hello, world!"
    assert data["data"]["type"] == "text"


@pytest.mark.asyncio
async def test_mark_chat_as_read(client: AsyncClient, test_chat_room):
    """Test marking chat as read."""
    room, user1, _ = test_chat_room

    # Create access token for user1
    token = create_access_token(data={"sub": str(user1.id)})

    # Mark as read
    response = await client.post(
        f"/api/v1/chat/rooms/{room.id}/read",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "messages_marked_read" in data["data"]


@pytest.mark.asyncio
async def test_get_unread_count(client: AsyncClient, test_chat_room):
    """Test getting unread count."""
    room, user1, _ = test_chat_room

    # Create access token for user1
    token = create_access_token(data={"sub": str(user1.id)})

    # Get unread count
    response = await client.get(
        "/api/v1/chat/unread-count",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "unread_count" in data["data"]


@pytest.mark.asyncio
async def test_leave_chat(client: AsyncClient, test_chat_room):
    """Test leaving a chat room."""
    room, user1, _ = test_chat_room

    # Create access token for user1
    token = create_access_token(data={"sub": str(user1.id)})

    # Leave chat
    response = await client.delete(
        f"/api/v1/chat/rooms/{room.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Left chat room successfully"


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient, test_chat_room):
    """Test that unauthorized users cannot access chat rooms."""
    room, _, _ = test_chat_room
    other_user_id = uuid4()

    # Create access token for non-participant user
    token = create_access_token(data={"sub": str(other_user_id)})

    # Try to get room details
    response = await client.get(
        f"/api/v1/chat/rooms/{room.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_send_message_empty_content(client: AsyncClient, test_chat_room):
    """Test that empty messages are rejected."""
    room, user1, _ = test_chat_room

    # Create access token for user1
    token = create_access_token(data={"sub": str(user1.id)})

    # Try to send empty message
    response = await client.post(
        f"/api/v1/chat/rooms/{room.id}/messages",
        json={
            "content": "",
            "type": "text"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_message_xss_prevention(client: AsyncClient, test_chat_room):
    """Test that message content is sanitized to prevent XSS."""
    room, user1, _ = test_chat_room

    # Create access token for user1
    token = create_access_token(data={"sub": str(user1.id)})

    # Send message with XSS attempt
    xss_payload = "<script>alert('xss')</script>"
    response = await client.post(
        f"/api/v1/chat/rooms/{room.id}/messages",
        json={
            "content": xss_payload,
            "type": "text"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    # Content should be escaped
    assert "<script>" not in data["data"]["content"]
    assert "&lt;script&gt;" in data["data"]["content"]
