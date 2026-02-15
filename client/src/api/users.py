"""用户管理 API"""

from typing import Optional

from voidview_shared import UserRole
from .client import api_client, APIError
from models.user import UserResponse, UserCreateRequest


class UsersAPI:
    """用户管理 API (仅 root 可用)"""

    @staticmethod
    def list_users(page: int = 1, page_size: int = 20) -> dict:
        """获取用户列表"""
        response = api_client.get("/users", params={"page": page, "page_size": page_size})
        # 将 items 中的 dict 转换为 UserResponse 对象
        if "items" in response:
            response["items"] = [UserResponse(**item) for item in response["items"]]
        return response

    @staticmethod
    def create_user(
        username: str,
        password: str,
        display_name: str,
        role: UserRole = UserRole.TESTER
    ) -> UserResponse:
        """创建用户"""
        response = api_client.post("/users", UserCreateRequest(
            username=username,
            password=password,
            display_name=display_name,
            role=role
        ))
        return UserResponse(**response)

    @staticmethod
    def get_user(user_id: int) -> UserResponse:
        """获取用户详情"""
        response = api_client.get(f"/users/{user_id}")
        return UserResponse(**response)

    @staticmethod
    def update_user(user_id: int, display_name: Optional[str] = None, is_active: Optional[bool] = None) -> UserResponse:
        """更新用户"""
        data = {}
        if display_name is not None:
            data["display_name"] = display_name
        if is_active is not None:
            data["is_active"] = is_active

        response = api_client.put(f"/users/{user_id}", data=data)
        return UserResponse(**response)

    @staticmethod
    def reset_password(user_id: int, new_password: str) -> dict:
        """重置用户密码"""
        return api_client.post(f"/users/{user_id}/reset-password", data={"new_password": new_password})

    @staticmethod
    def toggle_active(user_id: int) -> dict:
        """切换用户启用状态"""
        return api_client.post(f"/users/{user_id}/toggle-active")


# 便捷访问
users_api = UsersAPI()
