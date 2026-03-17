from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum
from app.schemas.user import UserRole


class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole
    full_name: Optional[str] = None


class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class LinkHRManagerRequest(BaseModel):
    hr_id: str
    manager_id: str


class AccountRequestCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    requested_role: str = "hr"  # "hr" or "manager"
    message: Optional[str] = None


class AccountRequestStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class AccountRequestStatusUpdate(BaseModel):
    status: AccountRequestStatus
