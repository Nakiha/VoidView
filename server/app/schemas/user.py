"""用户相关的 Pydantic 模型"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from voidview_shared import UserRole


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """创建用户请求"""
    password: str = Field(..., min_length=6, max_length=100)
    role: UserRole = UserRole.TESTER


class UserUpdate(BaseModel):
    """更新用户请求"""
    display_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """用户响应"""
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    created_by: Optional[int] = None
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """登录请求"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str = Field(..., min_length=6)


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    new_password: str = Field(..., min_length=6)
