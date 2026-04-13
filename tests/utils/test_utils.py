"""
Tests for utility modules: storage, rate_limit, redis_pubsub.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO

from app.utils.storage import upload_file_to_storage
from app.utils.redis_pubsub import RedisPubSubManager, publish_to_channel


class TestStorage:
    """Test storage utilities."""

    @pytest.mark.asyncio
    async def test_upload_file_returns_url(self):
        """Test upload file returns URL."""
        import asyncio
        
        # Create a proper async mock for file.read()
        async def mock_read():
            return b"test content"
        
        # Mock the Minio client
        with patch("app.utils.storage.Minio") as mock_minio:
            mock_client = MagicMock()
            mock_minio.return_value = mock_client
            mock_client.bucket_exists.return_value = True
            mock_client.put_object = MagicMock()

            # Create a proper mock UploadFile
            file = MagicMock()
            file.filename = "test.jpg"
            file.content_type = "image/jpeg"
            file.read = mock_read  # Async function

            result = await upload_file_to_storage(file, folder="test")
            assert isinstance(result, str)
            assert "http" in result.lower()


class TestRedisPubSub:
    """Test Redis pub/sub utilities."""

    @pytest.mark.asyncio
    async def test_publish_to_channel_returns_bool(self):
        """Test publish to channel returns boolean."""
        with patch("app.utils.redis_pubsub.pubsub_manager") as mock_manager:
            mock_manager.publish_to_channel = AsyncMock(return_value=True)
            
            result = await publish_to_channel("test:channel", {"key": "value"})
            assert result is True

    @pytest.mark.asyncio
    async def test_redis_pubsub_manager_init(self):
        """Test RedisPubSubManager initialization."""
        manager = RedisPubSubManager()
        assert manager.pubsub is None
        assert manager._running is False

    @pytest.mark.asyncio
    async def test_redis_pubsub_manager_stop_listening(self):
        """Test stop listening sets running to False."""
        manager = RedisPubSubManager()
        manager._running = True
        manager.stop_listening()
        assert manager._running is False


class TestRateLimit:
    """Test rate limiting utilities."""

    def test_rate_limit_import(self):
        """Test rate limit module imports."""
        from app.utils import rate_limit
        assert rate_limit is not None
