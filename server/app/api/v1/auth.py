"""认证 API"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_root
from app.models.user import User
from app.services.user_service import UserService
from app.schemas.user import (
    UserCreate, UserResponse, UserLogin, TokenResponse,
    ChangePasswordRequest, ResetPasswordRequest
)
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    user_service = UserService(db)
    user = await user_service.authenticate(data.username, data.password)

    if not user:
        raise BadRequestException("用户名或密码错误")

    tokens = user_service.create_tokens(user)

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    user_service = UserService(db)
    await user_service.change_password(
        current_user,
        data.old_password,
        data.new_password
    )
    return {"message": "密码修改成功"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse.model_validate(current_user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """刷新令牌"""
    from app.core.security import decode_token

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise BadRequestException("无效的刷新令牌")

    user_id = payload.get("sub")
    if not user_id:
        raise BadRequestException("令牌格式错误")

    user_service = UserService(db)
    user = await user_service.get_by_id(int(user_id))

    if not user or not user.is_active:
        raise BadRequestException("用户不存在或已禁用")

    tokens = user_service.create_tokens(user)

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )
