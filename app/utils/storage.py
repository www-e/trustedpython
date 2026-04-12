"""
Storage utility for file uploads to MinIO/S3.
"""

import io
from typing import Optional

from fastapi import UploadFile
from minio import Minio
from minio.error import S3Error

from app.core.config import settings


async def upload_file_to_storage(file: UploadFile, folder: str = "uploads") -> str:
    """
    Upload a file to MinIO/S3 storage.

    Args:
        file: File to upload
        folder: Folder path in bucket

    Returns:
        Public URL of uploaded file

    Raises:
        Exception: If upload fails
    """
    try:
        # Initialize MinIO client
        client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )

        # Ensure bucket exists
        bucket_name = settings.MINIO_BUCKET
        try:
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
        except S3Error as e:
            if e.code != "BucketAlreadyOwnedByYou":
                raise

        # Generate unique filename
        import uuid
        from datetime import datetime

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{folder}/{timestamp}_{unique_id}_{file.filename}"

        # Read file content
        content = await file.read()
        file_stream = io.BytesIO(content)
        file_stream.seek(0)

        # Determine content type
        content_type = file.content_type or "application/octet-stream"

        # Upload file
        client.put_object(
            bucket_name=bucket_name,
            object_name=filename,
            data=file_stream,
            length=len(content),
            content_type=content_type,
        )

        # Generate public URL
        protocol = "https" if settings.MINIO_SECURE else "http"
        url = f"{protocol}://{settings.MINIO_ENDPOINT}/{bucket_name}/{filename}"

        return url

    except S3Error as e:
        raise Exception(f"Storage error: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to upload file: {str(e)}")


async def delete_file_from_storage(file_url: str) -> bool:
    """
    Delete a file from MinIO/S3 storage.

    Args:
        file_url: Full URL of the file

    Returns:
        True if deleted successfully

    Raises:
        Exception: If deletion fails
    """
    try:
        # Initialize MinIO client
        client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )

        # Extract object name from URL
        # URL format: http://localhost:9000/bucket/folder/file.ext
        parts = file_url.split("/", 3)  # Split into [http:, '', endpoint, rest]
        if len(parts) < 4:
            raise ValueError("Invalid file URL format")

        rest = parts[3]
        object_name = rest.split("/", 1)[1] if "/" in rest else rest

        # Remove bucket name from path if present
        bucket_name = settings.MINIO_BUCKET
        if object_name.startswith(bucket_name + "/"):
            object_name = object_name[len(bucket_name + "/") :]

        # Delete object
        client.remove_object(bucket_name, object_name)

        return True

    except S3Error as e:
        raise Exception(f"Storage error: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to delete file: {str(e)}")
