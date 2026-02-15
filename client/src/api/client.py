"""API 客户端封装"""

import httpx
from typing import TypeVar, Type, Optional, Any
from pydantic import BaseModel

from app.config import settings

T = TypeVar("T", bound=BaseModel)


class APIError(Exception):
    """API 错误"""
    def __init__(self, message: str, status_code: int = None, detail: Any = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class APIClient:
    """HTTP API 客户端"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.API_BASE_URL
        self._token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """获取 HTTP 客户端 (懒加载)"""
        if self._client is None:
            headers = {}
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"

            self._client = httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    def set_token(self, access_token: str, refresh_token: str = None):
        """设置认证令牌"""
        self._token = access_token
        self._refresh_token = refresh_token

        # 更新客户端头部
        if self._client:
            self._client.headers["Authorization"] = f"Bearer {access_token}"
        else:
            # 触发客户端创建
            _ = self.client

    def clear_token(self):
        """清除认证令牌"""
        self._token = None
        self._refresh_token = None
        if self._client:
            self._client.headers.pop("Authorization", None)

    def get_token(self) -> Optional[str]:
        """获取当前令牌"""
        return self._token

    def get_refresh_token(self) -> Optional[str]:
        """获取刷新令牌"""
        return self._refresh_token

    def _handle_response(self, response: httpx.Response) -> dict:
        """处理响应"""
        if response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("detail", f"请求失败: {response.status_code}")
            except:
                message = f"请求失败: {response.status_code}"
            raise APIError(message, response.status_code, error_data if 'error_data' in dir() else None)

        return response.json()

    def get(self, path: str, params: dict = None) -> dict:
        """GET 请求"""
        response = self.client.get(path, params=params)
        return self._handle_response(response)

    def post(self, path: str, body: BaseModel = None, data: dict = None) -> dict:
        """POST 请求"""
        json_data = body.model_dump() if body else data
        response = self.client.post(path, json=json_data)
        return self._handle_response(response)

    def put(self, path: str, body: BaseModel = None, data: dict = None) -> dict:
        """PUT 请求"""
        json_data = body.model_dump() if body else data
        response = self.client.put(path, json=json_data)
        return self._handle_response(response)

    def delete(self, path: str) -> dict:
        """DELETE 请求"""
        response = self.client.delete(path)
        return self._handle_response(response)

    def close(self):
        """关闭客户端"""
        if self._client:
            self._client.close()
            self._client = None


# 全局 API 客户端实例
api_client = APIClient()
