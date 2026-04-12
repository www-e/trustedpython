"""Common schemas used across the API."""

from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationSchema(BaseModel):
    """Pagination information schema."""

    page: int = Field(..., description="Current page number (1-indexed)")
    limit: int = Field(..., description="Number of items per page")
    total: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

    @classmethod
    def create(cls, page: int, limit: int, total: int) -> "PaginationSchema":
        """
        Create pagination schema.

        Args:
            page: Current page number
            limit: Items per page
            total: Total number of items

        Returns:
            PaginationSchema: Pagination information
        """
        total_pages = (total + limit - 1) // limit if limit > 0 else 0
        return cls(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


class APIResponse(BaseModel, Generic[T]):
    """
    Standard API response wrapper.

    Generic type T should be the response data type.
    """

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[T] = Field(None, description="Response payload")
    message: Optional[str] = Field(None, description="Optional success/info message")
    error: Optional[str] = Field(None, description="Error message if unsuccessful")
    pagination: Optional[PaginationSchema] = Field(
        None, description="Pagination info for list endpoints"
    )

    @classmethod
    def success_response(
        cls, data: T, message: Optional[str] = None, pagination: Optional[PaginationSchema] = None
    ) -> "APIResponse[T]":
        """
        Create a successful API response.

        Args:
            data: Response data
            message: Optional success message
            pagination: Optional pagination info

        Returns:
            APIResponse: Success response
        """
        return cls(success=True, data=data, message=message, error=None, pagination=pagination)

    @classmethod
    def error_response(cls, error: str, data: Optional[T] = None, message: Optional[str] = None) -> "APIResponse[T]":
        """
        Create an error API response.

        Args:
            error: Error message
            data: Optional data (partial results)
            message: Optional additional message

        Returns:
            APIResponse: Error response
        """
        return cls(success=False, error=error, data=data, message=message, pagination=None)


class ErrorDetail(BaseModel):
    """Error detail for validation errors."""

    field: str = Field(..., description="Field name that has the error")
    messages: list[str] = Field(..., description="List of error messages for this field")


class ErrorResponse(BaseModel):
    """
    Standard error response schema.
    Used for validation errors and other client errors.
    """

    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, list[str]]] = Field(
        None, description="Field-specific validation errors (field -> list of errors)"
    )

    @classmethod
    def create(
        cls, error_code: str, message: str, details: Optional[Dict[str, list[str]]] = None
    ) -> "ErrorResponse":
        """
        Create an error response.

        Args:
            error_code: Machine-readable error code
            message: Human-readable error message
            details: Optional field-specific errors

        Returns:
            ErrorResponse: Error response
        """
        return cls(error_code=error_code, message=message, details=details)


class SuccessResponse(BaseModel):
    """
    Simple success response without data payload.
    Used for operations that only need confirmation.
    """

    success: bool = Field(True, description="Always true for this response")
    message: str = Field(..., description="Success message")

    @classmethod
    def create(cls, message: str) -> "SuccessResponse":
        """
        Create a success response.

        Args:
            message: Success message

        Returns:
            SuccessResponse: Success response
        """
        return cls(success=True, message=message)
