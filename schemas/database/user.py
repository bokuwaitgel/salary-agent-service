from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

UserRole = Literal["user", "viewer", "admin"]


# class UserCreate(BaseModel):
#     username: str = Field(..., min_length=3, max_length=50)
#     email: EmailStr
#     password: str = Field(..., min_length=6)
#     role: UserRole = "candidate"


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="ignore")

    name: str = Field(..., description="User's name")
    email: str = Field(..., description="User's email address")
    password_hash: str = Field(..., description="Password hash")
    role: UserRole = Field(default="user", description="User role")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), description="Record creation timestamp")


class UserRegisterInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=255)
    role: UserRole = Field(default="user")


class UserLoginInput(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=255)


class UserPublic(BaseModel):
    id: str
    name: str
    email: str
    role: UserRole
    created_at: datetime


class UserTable(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
