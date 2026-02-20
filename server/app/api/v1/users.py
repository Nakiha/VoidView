"""用户管理 API (仅 root 可用) - Excel 存储版本"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_root
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate, UserResponse, ResetPasswordRequest

router = APIRouter(prefix="/users", tags=["用户管理"])


def _convert_datetime(data: dict) -> dict:
    """转换 datetime 字段"""
    result = dict(data)
    for key in ['created_at', 'updated_at', 'last_login_at']:
        if key in result and result[key] is not None:
            if isinstance(result[key], str):
                result[key] = datetime.fromisoformat(result[key])
    return result


@router.get("", response_model=dict)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_root)
):
    """获取用户列表 (仅 root)"""
    user_service = UserService()

    skip = (page - 1) * page_size
    users = await user_service.list_users(skip=skip, limit=page_size)
    total = await user_service.count_users()

    return {
        "items": [UserResponse.model_validate(_convert_datetime(u)) for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=UserResponse)
async def create_user(
    data: UserCreate,
    current_user: dict = Depends(require_root)
):
    """创建用户 (仅 root)"""
    user_service = UserService()
    user = await user_service.create_user(
        username=data.username,
        password=data.password,
        display_name=data.display_name,
        created_by=current_user["id"],
        role=data.role
    )
    return UserResponse.model_validate(_convert_datetime(user))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: dict = Depends(require_root)
):
    """获取用户详情 (仅 root)"""
    user_service = UserService()
    user = await user_service.get_by_id(user_id)

    if not user:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("用户不存在")

    return UserResponse.model_validate(_convert_datetime(user))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: dict = Depends(require_root)
):
    """更新用户 (仅 root)"""
    user_service = UserService()
    user = await user_service.update_user(
        user_id,
        display_name=data.display_name,
        is_active=data.is_active
    )
    return UserResponse.model_validate(_convert_datetime(user))


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    data: ResetPasswordRequest,
    current_user: dict = Depends(require_root)
):
    """重置用户密码 (仅 root)"""
    user_service = UserService()
    await user_service.reset_password(user_id, data.new_password)
    return {"message": "密码已重置"}


@router.post("/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    current_user: dict = Depends(require_root)
):
    """切换用户启用状态 (仅 root)"""
    if user_id == current_user["id"]:
        from app.core.exceptions import BadRequestException
        raise BadRequestException("不能禁用自己的账号")

    user_service = UserService()
    user = await user_service.get_by_id(user_id)

    if not user:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("用户不存在")

    is_active = not user.get("is_active", True)
    user = await user_service.update_user(user_id, is_active=is_active)
    status_text = "启用" if is_active else "禁用"
    return {"message": f"已{status_text}账号", "is_active": is_active}
