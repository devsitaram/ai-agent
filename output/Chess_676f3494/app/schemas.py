# Pydantic schemas for request/response validation
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


# ---- Auth Schemas ----

class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


# ---- Item Schemas ----

class ItemCreate(BaseModel):
    """Schema for creating an item."""
    title: str
    description: Optional[str] = None


class ItemUpdate(BaseModel):
    """Schema for updating an item."""
    title: Optional[str] = None
    description: Optional[str] = None


class ItemResponse(BaseModel):
    """Schema for item response."""
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemListResponse(BaseModel):
    """Schema for paginated item list."""
    items: List[ItemResponse]
    total: int
    page: int
    page_size: int
