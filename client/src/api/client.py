"""API 客户端封装"""

import logging
import httpx
from typing import TypeVar, Type, Optional, Any
from pydantic import BaseModel

from app.config import user_config

T = TypeVar("T", bound=BaseModel)

# API 客户端日志
logger = logging.getLogger("api_client")


class APIError(Exception):
    """API 错误"""
    def __init__(self, message: str, status_code: int = None, detail: Any = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        # 记录错误日志
        logger.error(f"API Error [{status_code}]: {message}, detail={detail}")
        super().__init__(self.message)


class ServerUnreachableError(Exception):
    """服务端不可达错误"""
    def __init__(self, message: str = "无法连接到服务器，请检查网络连接或服务器状态"):
        self.message = message
        # 记录错误日志
        logger.error(f"Server Unreachable: {message}")
        super().__init__(self.message)


class APIClient:
    """HTTP API 客户端"""

    def __init__(self, base_url: str = None):
        self._base_url = base_url
        self._token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._client: Optional[httpx.Client] = None

    @property
    def base_url(self) -> str:
        """获取当前服务器地址"""
        return self._base_url or user_config.server_url

    def update_base_url(self, url: str):
        """更新服务器地址"""
        self._base_url = url.rstrip("/")
        # 关闭旧客户端，下次使用时会创建新客户端
        if self._client:
            self._client.close()
            self._client = None

    @property
    def client(self) -> httpx.Client:
        """获取 HTTP 客户端 (懒加载)"""
        if self._client is None:
            headers = {}
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"

            # 设置更合理的超时：连接超时 5 秒，读取超时 30 秒
            timeout = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=timeout,
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
                # 尝试获取更详细的错误信息
                if isinstance(error_data.get("detail"), dict):
                    # Pydantic 验证错误格式
                    detail_info = error_data["detail"]
                    if "msg" in detail_info:
                        message = detail_info["msg"]
                    else:
                        message = str(detail_info)
                else:
                    message = error_data.get("detail", f"请求失败: {response.status_code}")
            except Exception:
                message = f"请求失败: {response.status_code}"
                error_data = None
            raise APIError(message, response.status_code, error_data)

        return response.json()

    def _handle_request_error(self, e: Exception) -> None:
        """处理请求异常"""
        if isinstance(e, httpx.ConnectError):
            raise ServerUnreachableError("无法连接到服务器，请检查服务器是否已启动")
        elif isinstance(e, httpx.ConnectTimeout):
            raise ServerUnreachableError("连接服务器超时，请检查网络连接")
        elif isinstance(e, httpx.ReadTimeout):
            raise ServerUnreachableError("服务器响应超时，请稍后重试")
        elif isinstance(e, httpx.NetworkError):
            raise ServerUnreachableError(f"网络错误: {str(e)}")
        else:
            raise ServerUnreachableError(f"请求失败: {str(e)}")

    def ping(self) -> bool:
        """检测服务端是否可用"""
        try:
            # 使用一个简单的健康检查端点
            response = self.client.get("/health", timeout=3.0)
            return response.status_code == 200
        except:
            return False

    def get(self, path: str, params: dict = None) -> dict:
        """GET 请求"""
        try:
            response = self.client.get(path, params=params)
            return self._handle_response(response)
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            self._handle_request_error(e)

    def post(self, path: str, body: BaseModel = None, data: dict = None) -> dict:
        """POST 请求"""
        try:
            json_data = body.model_dump() if body else data
            response = self.client.post(path, json=json_data)
            return self._handle_response(response)
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            self._handle_request_error(e)

    def put(self, path: str, body: BaseModel = None, data: dict = None) -> dict:
        """PUT 请求"""
        try:
            json_data = body.model_dump() if body else data
            response = self.client.put(path, json=json_data)
            return self._handle_response(response)
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            self._handle_request_error(e)

    def delete(self, path: str) -> dict:
        """DELETE 请求"""
        try:
            response = self.client.delete(path)
            return self._handle_response(response)
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            self._handle_request_error(e)

    def close(self):
        """关闭客户端"""
        if self._client:
            self._client.close()
            self._client = None


# 全局 API 客户端实例
api_client = APIClient()
