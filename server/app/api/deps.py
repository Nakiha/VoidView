"""API 依赖注入"""

from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.user import User
from app.services.user_service import UserService
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from voidview_shared import UserRole

security = HTTPBearer(auto_error=False)


async def get_db():
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户"""
    if not credentials:
        raise UnauthorizedException("未提供认证凭证")

    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise UnauthorizedException("无效的认证凭证")

    if payload.get("type") != "access":
        raise UnauthorizedException("无效的令牌类型")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("令牌格式错误")

    user_service = UserService(db)
    user = await user_service.get_by_id(int(user_id))

    if not user:
        raise UnauthorizedException("用户不存在")

    if not user.is_active:
        raise UnauthorizedException("账号已被禁用")

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """获取当前用户 (可选)"""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except UnauthorizedException:
        return None


def require_root(current_user: User = Depends(get_current_user)) -> User:
    """要求 root 权限"""
    if not current_user.is_root():
        raise ForbiddenException("需要管理员权限")
    return current_user
