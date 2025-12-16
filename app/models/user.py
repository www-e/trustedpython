from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Enum as SQLEnum, String
from typing import Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, field_validator
from passlib.context import CryptContext
import re

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Enums for user roles and states
class UserRole(str, Enum):
    ADMIN = "admin"
    MEDIATOR = "mediator"
    REGULAR_USER = "regular_user"

class UserState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class UserBase(BaseModel):
    username: str
    phone_number: str
    second_phone_number: Optional[str] = None
    account_info: str
    role: UserRole = UserRole.REGULAR_USER

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Username must be between 3 and 50 characters')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v

    @field_validator('phone_number', 'second_phone_number')
    @classmethod
    def validate_phone_number(cls, v):
        if v is None:
            return v
        # Basic phone number validation - adjust as needed
        if len(v) < 10 or len(v) > 15:
            raise ValueError('Phone number must be between 10 and 15 digits')
        if not re.match(r'^[\d\-\+\(\)\s]+$', v):
            raise ValueError('Invalid phone number format')
        return v

class UserRegistration(UserBase):
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    state: UserState
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: UserRole
    state: UserState

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None
    state: Optional[UserState] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserUpdateRequest(BaseModel):
    phone_number: Optional[str] = None
    second_phone_number: Optional[str] = None
    account_info: Optional[str] = None

    @field_validator('phone_number', 'second_phone_number')
    @classmethod
    def validate_optional_phone_number(cls, v):
        if v is None:
            return v
        if len(v) < 10 or len(v) > 15:
            raise ValueError('Phone number must be between 10 and 15 digits')
        if not re.match(r'^[\d\-\+\(\)\s]+$', v):
            raise ValueError('Invalid phone number format')
        return v

class UserApprovalRequest(BaseModel):
    user_id: int
    approve: bool

# SQLModel table definition
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(sa_column=Column(String, unique=True, nullable=False))
    hashed_password: str = Field(sa_column=Column(String, nullable=False))
    phone_number: str = Field(sa_column=Column(String, nullable=False))
    second_phone_number: Optional[str] = Field(sa_column=Column(String, nullable=True))
    account_info: str = Field(sa_column=Column(String, nullable=False))
    role: UserRole = Field(sa_column=Column(SQLEnum(UserRole), nullable=False), default=UserRole.REGULAR_USER)
    state: UserState = Field(sa_column=Column(SQLEnum(UserState), nullable=False), default=UserState.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def set_password(self, password: str):
        self.hashed_password = pwd_context.hash(password)

    def verify_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, self.hashed_password)

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Function to create database tables
async def create_db_and_tables():
    from app.database.core import engine
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)