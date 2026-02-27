"""Standardized response schemas for all API endpoints matching professional frontend design."""

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar("T")


class AppError(BaseModel):
    """Professional error details in response."""
    code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(None, description="Additional error context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "INVALID_INPUT",
                "message": "The provided input failed validation",
                "details": {"field": "email", "reason": "Invalid email format"}
            }
        }


class AppResponse(BaseModel, Generic[T]):
    """Professional standardized API response wrapper."""
    success: bool = Field(..., description="Operation success status")
    status_code: int = Field(default=200, description="HTTP status code")
    title: Optional[str] = Field(None, description="Response title or operation name")
    message: Optional[str] = Field(None, description="Brief status message")
    data: Optional[T] = Field(None, description="Response data payload")
    error: Optional[AppError] = Field(None, description="Error details if operation failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracking")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "status_code": 200,
                "title": "Wallet Created",
                "message": "Wallet created successfully",
                "data": {"wallet_id": "uuid", "blockchain": "ethereum"},
                "error": None,
                "timestamp": "2024-02-08T10:00:00",
                "request_id": "req_123456"
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Professional standardized paginated response."""
    success: bool = Field(..., description="Operation success status")
    status_code: int = Field(default=200, description="HTTP status code")
    title: Optional[str] = Field(None, description="Response title")
    message: Optional[str] = Field(None, description="Brief status message")
    data: List[T] = Field(..., description="Array of response items")
    pagination: dict[str, int] = Field(
        default_factory=lambda: {
            "total": 0,
            "limit": 10,
            "offset": 0,
            "page": 1,
            "total_pages": 0
        },
        description="Pagination metadata"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracking")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "status_code": 200,
                "title": "Wallets Retrieved",
                "message": "Successfully retrieved user wallets",
                "data": [
                    {"id": "uuid1", "name": "Primary Ethereum"},
                    {"id": "uuid2", "name": "Backup Solana"}
                ],
                "pagination": {
                    "total": 2,
                    "limit": 10,
                    "offset": 0,
                    "page": 1,
                    "total_pages": 1
                },
                "timestamp": "2024-02-08T10:00:00",
                "request_id": "req_123456"
            }
        }


class SuccessResponse(BaseModel, Generic[T]):
    """Minimal success response for simple operations."""
    success: bool = True
    data: T = Field(..., description="Response data")
    message: Optional[str] = Field(None, description="Success message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": "123"},
                "message": "Operation completed successfully"
            }
        }


class ErrorResponse(BaseModel):
    """Error response with professional formatting."""
    success: bool = False
    error: AppError
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request parameters"
                },
                "timestamp": "2024-02-08T10:00:00"
            }
        }
