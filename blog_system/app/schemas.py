from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: str
    login: str

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def password_length(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v
    
    @validator('email')
    def email_valid(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v

class UserResponse(UserBase):
    id: int
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True

class PostBase(BaseModel):
    title: str
    content: str

class PostCreate(PostBase):
    authorId: int

class PostResponse(PostBase):
    id: int
    authorId: int
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True