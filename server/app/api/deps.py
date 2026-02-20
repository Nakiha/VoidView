"""API 依赖注入 - Excel 存储版本"""

from typing import Optional, Dict

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.user_service import UserService
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from voidview_shared import UserRole

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict:
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

    user_service = UserService()
    user = await user_service.get_by_id(int(user_id))

    if not user:
        raise UnauthorizedException("用户不存在")

    if not user.get("is_active", True):
        raise UnauthorizedException("账号已被禁用")

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict]:
    """获取当前用户 (可选)"""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except UnauthorizedException:
        return None


def require_root(current_user: Dict = Depends(get_current_user)) -> Dict:
    """要求 root 权限"""
    role = current_user.get("role", "tester")
    if role != "root":
        raise ForbiddenException("需要管理员权限")
    return current_user
