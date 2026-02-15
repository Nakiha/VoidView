"""用户相关模型"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from voidview_shared import UserRole


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    display_name: str
    role: UserRole
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
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


class UserCreateRequest(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6)
    display_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.TESTER
