"""用户服务"""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.core.exceptions import BadRequestException, NotFoundException
from voidview_shared import UserRole
from voidview_shared.constants import DEFAULT_ROOT_USERNAME, DEFAULT_ROOT_PASSWORD, DEFAULT_ROOT_DISPLAY_NAME


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return await self.db.get(User, user_id)

    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = await self.get_by_username(username)
        if not user:
            return None
        if not user.is_active:
            return None
        if not user.verify_password(password):
            return None

        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        await self.db.commit()

        return user

    async def create_user(
        self,
        username: str,
        password: str,
        display_name: str,
        created_by: int,
        role: UserRole = UserRole.TESTER
    ) -> User:
        """创建用户"""
        # 检查用户名是否已存在
        existing = await self.get_by_username(username)
        if existing:
            raise BadRequestException("用户名已存在")

        user = User(
            username=username,
            display_name=display_name,
            role=role,
            created_by=created_by,
            must_change_password=True,
        )
        user.set_password(password)

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def update_user(self, user_id: int, display_name: Optional[str] = None, is_active: Optional[bool] = None) -> User:
        """更新用户"""
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundException("用户不存在")

        if display_name is not None:
            user.display_name = display_name
        if is_active is not None:
            user.is_active = is_active

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(self, user: User, old_password: str, new_password: str) -> None:
        """修改密码"""
        if not user.verify_password(old_password):
            raise BadRequestException("当前密码错误")

        user.set_password(new_password)
        user.must_change_password = False
        await self.db.commit()

    async def reset_password(self, user_id: int, new_password: str) -> None:
        """重置密码 (管理员操作)"""
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundException("用户不存在")

        user.set_password(new_password)
        user.must_change_password = True
        await self.db.commit()

    async def init_root_user(self) -> Optional[User]:
        """初始化 root 账号"""
        existing = await self.get_by_username(DEFAULT_ROOT_USERNAME)
        if existing:
            return None

        root = User(
            username=DEFAULT_ROOT_USERNAME,
            display_name=DEFAULT_ROOT_DISPLAY_NAME,
            role=UserRole.ROOT,
            must_change_password=True,
        )
        root.set_password(DEFAULT_ROOT_PASSWORD)

        self.db.add(root)
        await self.db.commit()
        await self.db.refresh(root)

        return root

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """获取用户列表"""
        stmt = select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_users(self) -> int:
        """统计用户数量"""
        from sqlalchemy import func
        stmt = select(func.count(User.id))
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    def create_tokens(self, user: User) -> dict:
        """创建访问令牌"""
        access_token = create_access_token(user.id, user.role)
        refresh_token = create_refresh_token(user.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
