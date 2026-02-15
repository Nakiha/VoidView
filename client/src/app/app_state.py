"""全局应用状态"""

from typing import Optional

from models import UserResponse


class AppState:
    """全局应用状态 (单例)"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._current_user = None
        return cls._instance

    @property
    def current_user(self) -> Optional[UserResponse]:
        return self._current_user

    def set_user(self, user: UserResponse):
        self._current_user = user

    def logout(self):
        self._current_user = None

    def is_root(self) -> bool:
        return self._current_user and self._current_user.role.value == "root"


# 全局实例
app_state = AppState()
