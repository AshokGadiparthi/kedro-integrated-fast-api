"""
Pydantic Schemas - PHASE 0
============================
Request/Response validation and data modeling

WHY PYDANTIC?
- Validates incoming data from frontend
- Converts JSON to Python objects
- Type checking and error messages
- Automatic OpenAPI documentation
- Easy serialization to JSON
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserRegister(BaseModel):
    """User registration request"""
    
    email: EmailStr = Field(
        ...,
        description="Email address (must be valid email)"
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Username (3-100 characters)"
    )
    password: str = Field(
        ...,
        min_length=6,
        description="Password (minimum 6 characters)"
    )
    full_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Full name (optional)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "john_doe",
                "password": "securepass123",
                "full_name": "John Doe"
            }
        }


class UserLogin(BaseModel):
    """User login request"""
    
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepass123"
            }
        }


class UserResponse(BaseModel):
    """User response (sent to frontend)"""
    
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    is_active: bool = Field(..., description="Is account active")
    created_at: datetime = Field(..., description="Registration date")
    
    class Config:
        from_attributes = True  # Convert SQLAlchemy objects to Pydantic
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "username": "john_doe",
                "full_name": "John Doe",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00"
            }
        }


class TokenResponse(BaseModel):
    """Token response after successful login"""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "token_type": "bearer",
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "user@example.com",
                    "username": "john_doe",
                    "full_name": "John Doe",
                    "is_active": True,
                    "created_at": "2024-01-15T10:30:00"
                }
            }
        }


# ============================================================================
# WORKSPACE SCHEMAS
# ============================================================================

class WorkspaceCreate(BaseModel):
    """Create workspace request"""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Workspace name"
    )
    description: Optional[str] = Field(
        default=None,
        description="Workspace description"
    )
    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern="^[a-z0-9-]+$",
        description="URL-friendly slug (lowercase, hyphens only)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "My ML Workspace",
                "description": "For development and testing",
                "slug": "my-ml-workspace"
            }
        }


class WorkspaceUpdate(BaseModel):
    """Update workspace request"""
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New workspace name"
    )
    description: Optional[str] = Field(
        default=None,
        description="New description"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Workspace Name",
                "description": "Updated description"
            }
        }


class WorkspaceResponse(BaseModel):
    """Workspace response (sent to frontend)"""
    
    id: str = Field(..., description="Workspace ID")
    name: str = Field(..., description="Workspace name")
    slug: str = Field(..., description="URL-friendly slug")
    description: Optional[str] = Field(None, description="Description")
    owner_id: str = Field(..., description="Owner user ID")
    is_active: bool = Field(..., description="Is workspace active")
    created_at: datetime = Field(..., description="Creation date")
    updated_at: datetime = Field(..., description="Last update date")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "My ML Workspace",
                "slug": "my-ml-workspace",
                "description": "For development and testing",
                "owner_id": "550e8400-e29b-41d4-a716-446655440001",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }


class WorkspaceListResponse(BaseModel):
    """Response for listing workspaces"""
    
    count: int = Field(..., description="Number of workspaces")
    workspaces: List[WorkspaceResponse] = Field(..., description="List of workspaces")


# ============================================================================
# ERROR SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    
    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    
    detail: List[dict] = Field(..., description="List of validation errors")


# ============================================================================
# UTILITY SCHEMAS
# ============================================================================

class MessageResponse(BaseModel):
    """Simple message response"""
    
    message: str = Field(..., description="Response message")


class SuccessResponse(BaseModel):
    """Success response"""
    
    success: bool = Field(default=True)
    message: str = Field(..., description="Success message")
