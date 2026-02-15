"""认证相关 API"""

from typing import Optional

from .client import api_client, APIError
from models.user import LoginRequest, TokenResponse, UserResponse, ChangePasswordRequest


class AuthAPI:
    """认证 API"""

    @staticmethod
    def login(username: str, password: str) -> TokenResponse:
        """用户登录"""
        response = api_client.post("/auth/login", LoginRequest(
            username=username,
            password=password
        ))
        token_data = TokenResponse(**response)
        # 保存 token 到客户端
        api_client.set_token(token_data.access_token, token_data.refresh_token)
        return token_data

    @staticmethod
    def logout():
        """用户登出"""
        api_client.clear_token()

    @staticmethod
    def get_current_user() -> UserResponse:
        """获取当前用户信息"""
        response = api_client.get("/auth/me")
        return UserResponse(**response)

    @staticmethod
    def change_password(old_password: str, new_password: str) -> dict:
        """修改密码"""
        return api_client.post("/auth/change-password", ChangePasswordRequest(
            old_password=old_password,
            new_password=new_password
        ))

    @staticmethod
    def refresh_token(refresh_token: str) -> TokenResponse:
        """刷新令牌"""
        response = api_client.post("/auth/refresh", data={"refresh_token": refresh_token})
        token_data = TokenResponse(**response)
        api_client.set_token(token_data.access_token, token_data.refresh_token)
        return token_data


# 便捷访问
auth_api = AuthAPI()
