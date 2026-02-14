"""Standardized response schemas for all API endpoints."""

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar("T")


class AppError(BaseModel):
    """Error details in response."""
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class AppResponse(BaseModel, Generic[T]):
    """Standardized API response wrapper."""
    success: bool
    data: Optional[T] = None
    error: Optional[AppError] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {},
                "error": None,
                "timestamp": "2024-02-08T10:00:00",
                "request_id": "req_123456"
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated response."""
    success: bool
    data: List[T]
    pagination: dict[str, int] = Field(default_factory=lambda: {
        "total": 0,
        "limit": 10,
        "offset": 0
    })
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
