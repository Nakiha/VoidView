"""用户服务 - Excel 存储版本"""

from datetime import datetime
from typing import Optional, List, Dict

from app.storage import excel_store
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.core.exceptions import BadRequestException, NotFoundException
from voidview_shared import UserRole
from voidview_shared.constants import DEFAULT_ROOT_USERNAME, DEFAULT_ROOT_PASSWORD, DEFAULT_ROOT_DISPLAY_NAME


class UserService:
    def __init__(self, db=None):  # db 参数保留兼容性，但不再使用
        pass

    async def get_by_id(self, user_id: int) -> Optional[Dict]:
        """根据ID获取用户"""
        return excel_store.get_user_by_id(user_id)

    async def get_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取用户"""
        return excel_store.get_user_by_username(username)

    async def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """用户认证"""
        user = await self.get_by_username(username)
        if not user:
            return None
        if not user.get("is_active", True):
            return None

        # 验证密码
        password_hash = user.get("password_hash", "")
        if not verify_password(password, password_hash):
            return None

        # 更新最后登录时间
        excel_store.update_user(user["id"], last_login_at=datetime.now().isoformat())

        return user

    async def create_user(
        self,
        username: str,
        password: str,
        display_name: str,
        created_by: int,
        role: UserRole = UserRole.TESTER
    ) -> Dict:
        """创建用户"""
        # 检查用户名是否已存在
        existing = await self.get_by_username(username)
        if existing:
            raise BadRequestException("用户名已存在")

        password_hash = get_password_hash(password)
        user = excel_store.create_user(
            username=username,
            password_hash=password_hash,
            display_name=display_name,
            role=role.value,
            created_by=created_by
        )
        return user

    async def update_user(self, user_id: int, display_name: Optional[str] = None, is_active: Optional[bool] = None) -> Dict:
        """更新用户"""
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundException("用户不存在")

        update_data = {}
        if display_name is not None:
            update_data["display_name"] = display_name
        if is_active is not None:
            update_data["is_active"] = is_active

        if update_data:
            result = excel_store.update_user(user_id, **update_data)
            if not result:
                raise NotFoundException("用户不存在")
            return result
        return user

    async def change_password(self, user: Dict, old_password: str, new_password: str) -> None:
        """修改密码"""
        password_hash = user.get("password_hash", "")
        if not verify_password(old_password, password_hash):
            raise BadRequestException("当前密码错误")

        new_hash = get_password_hash(new_password)
        excel_store.update_user(user["id"], password_hash=new_hash, must_change_password=False)

    async def reset_password(self, user_id: int, new_password: str) -> None:
        """重置密码 (管理员操作)"""
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundException("用户不存在")

        new_hash = get_password_hash(new_password)
        excel_store.update_user(user_id, password_hash=new_hash, must_change_password=True)

    async def init_root_user(self) -> Optional[Dict]:
        """初始化 root 账号 - Excel 存储会自动创建"""
        existing = await self.get_by_username(DEFAULT_ROOT_USERNAME)
        if existing:
            return None
        # Excel 存储初始化时已创建 root 用户
        return await self.get_by_username(DEFAULT_ROOT_USERNAME)

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """获取用户列表"""
        users = excel_store.list_users()
        return users[skip:skip + limit]

    async def count_users(self) -> int:
        """统计用户数量"""
        users = excel_store.list_users()
        return len(users)

    def create_tokens(self, user: Dict) -> dict:
        """创建访问令牌"""
        user_id = user["id"]
        role = UserRole(user.get("role", "tester"))
        access_token = create_access_token(user_id, role)
        refresh_token = create_refresh_token(user_id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
