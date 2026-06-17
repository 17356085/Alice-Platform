"""
鞍集涂源管理系统 API 基类 — Page Object 风格 API 模型

功能:
  1. 认证 + 会话管理（登录/登出）
  2. API 端点封装为 Python 方法
  3. 请求/响应模式化（Pydantic Schema）
  4. 错误处理 + 重试机制

使用模式:
    api = AJSystemAPI(base_url="https://api.example.com")
    api.login(username="admin", password="123")
    users = api.get_users(limit=10)
    api.logout()
"""
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

from aitest.testing.api_client import APIClient, APIResponse

logger = logging.getLogger("aitest.api_base")


class APIStatus(str, Enum):
    """API 响应状态码（被测系统自定义）。"""
    SUCCESS = "success"
    ERROR = "error"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"


@dataclass
class LoginRequest:
    """登录请求体。"""
    username: str
    password: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LoginResponse:
    """登录响应体。"""
    code: int
    message: str
    data: Dict[str, Any]  # 包含 token / user_info

    @classmethod
    def from_json(cls, json_data: Dict) -> "LoginResponse":
        return cls(
            code=json_data.get("code"),
            message=json_data.get("message", ""),
            data=json_data.get("data", {}),
        )


@dataclass
class ListResponse:
    """通用列表响应。"""
    code: int
    message: str
    data: Dict[str, Any]  # 包含 total / items 等

    @classmethod
    def from_json(cls, json_data: Dict) -> "ListResponse":
        return cls(
            code=json_data.get("code"),
            message=json_data.get("message", ""),
            data=json_data.get("data", {}),
        )


class AJSystemAPI:
    """
    鞍集系统 API 客户端。

    示例:
        api = AJSystemAPI(base_url="https://api.example.com")
        api.login(username="admin", password="password")
        resp = api.get_users(page=1, page_size=20)
        assert resp.code == 200
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        verify_ssl: bool = False,
    ):
        """
        参数:
            base_url: API 基地址
            timeout: 请求超时秒数
            verify_ssl: 是否校验 SSL（测试环境通常关闭）
        """
        self.client = APIClient(
            base_url=base_url,
            timeout=timeout,
            verify_ssl=verify_ssl,
        )
        self.token: Optional[str] = None
        self.user_info: Dict[str, Any] = {}

    # ────────────────────────────────────────────────────────────────────
    # 认证端点
    # ────────────────────────────────────────────────────────────────────

    def login(self, username: str, password: str) -> LoginResponse:
        """
        用户登录。

        参数:
            username: 用户名
            password: 密码

        返回: LoginResponse
        """
        req = LoginRequest(username=username, password=password)
        resp = self.client.post(
            "/api/auth/login",
            json=req.to_dict(),
        )

        if not resp.is_ok():
            logger.error(f"Login failed: {resp.status_code} | {resp.body}")
            raise Exception(f"Login API error: {resp.status_code}")

        login_resp = LoginResponse.from_json(resp.json())

        # 从响应中提取 token（假设结构：data.token）
        if login_resp.data and "token" in login_resp.data:
            self.token = login_resp.data["token"]
            self.client.set_auth_token(self.token)
            logger.info(f"User {username} logged in")

        self.user_info = login_resp.data.get("user", {})
        return login_resp

    def logout(self) -> APIResponse:
        """用户登出。"""
        resp = self.client.post("/api/auth/logout")
        self.token = None
        self.user_info = {}
        logger.info("User logged out")
        return resp

    # ────────────────────────────────────────────────────────────────────
    # 用户管理端点
    # ────────────────────────────────────────────────────────────────────

    def get_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> ListResponse:
        """
        获取用户列表。

        参数:
            page: 页号（从 1 开始）
            page_size: 每页记录数
            search: 搜索关键词（可选）

        返回: ListResponse
        """
        params = {
            "page": page,
            "pageSize": page_size,
        }
        if search:
            params["search"] = search

        resp = self.client.get("/api/users", params=params)

        if not resp.is_ok():
            logger.error(f"Get users failed: {resp.status_code}")
            raise Exception(f"Get users API error: {resp.status_code}")

        return ListResponse.from_json(resp.json())

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        获取单个用户详情。

        参数:
            user_id: 用户 ID

        返回: 用户对象
        """
        resp = self.client.get(f"/api/users/{user_id}")

        if not resp.is_ok():
            logger.error(f"Get user {user_id} failed: {resp.status_code}")
            raise Exception(f"Get user API error: {resp.status_code}")

        return resp.json().get("data", {})

    def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        创建用户。

        参数:
            username: 用户名
            password: 密码
            email: 邮箱（可选）
            **kwargs: 其他字段

        返回: 创建的用户对象
        """
        payload = {
            "username": username,
            "password": password,
            "email": email,
            **kwargs,
        }
        resp = self.client.post("/api/users", json=payload)

        if not resp.is_ok():
            logger.error(f"Create user failed: {resp.status_code} | {resp.body}")
            raise Exception(f"Create user API error: {resp.status_code}")

        return resp.json().get("data", {})

    def update_user(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        更新用户。

        参数:
            user_id: 用户 ID
            **kwargs: 要更新的字段

        返回: 更新后的用户对象
        """
        resp = self.client.put(f"/api/users/{user_id}", json=kwargs)

        if not resp.is_ok():
            logger.error(f"Update user {user_id} failed: {resp.status_code}")
            raise Exception(f"Update user API error: {resp.status_code}")

        return resp.json().get("data", {})

    def delete_user(self, user_id: str) -> APIResponse:
        """
        删除用户。

        参数:
            user_id: 用户 ID
        """
        resp = self.client.delete(f"/api/users/{user_id}")

        if not resp.is_ok():
            logger.error(f"Delete user {user_id} failed: {resp.status_code}")
            raise Exception(f"Delete user API error: {resp.status_code}")

        return resp

    # ────────────────────────────────────────────────────────────────────
    # 设备管理端点
    # ────────────────────────────────────────────────────────────────────

    def get_equipment_list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> ListResponse:
        """
        获取设备列表。

        参数:
            page: 页号（从 1 开始）
            page_size: 每页记录数
            search: 搜索关键词（可选）

        返回: ListResponse
        """
        params = {
            "page": page,
            "pageSize": page_size,
        }
        if search:
            params["search"] = search

        resp = self.client.get("/api/equipment", params=params)

        if not resp.is_ok():
            logger.error(f"Get equipment list failed: {resp.status_code}")
            raise Exception(f"Get equipment list API error: {resp.status_code}")

        return ListResponse.from_json(resp.json())

    def get_equipment(self, equipment_id: str) -> Dict[str, Any]:
        """
        获取单个设备详情。

        参数:
            equipment_id: 设备 ID

        返回: 设备对象
        """
        resp = self.client.get(f"/api/equipment/{equipment_id}")

        if not resp.is_ok():
            logger.error(f"Get equipment {equipment_id} failed: {resp.status_code}")
            raise Exception(f"Get equipment API error: {resp.status_code}")

        return resp.json().get("data", {})

    def create_equipment(
        self,
        name: str,
        code: str,
        type: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        创建设备。

        参数:
            name: 设备名称
            code: 设备代码
            type: 设备类型
            **kwargs: 其他字段

        返回: 创建的设备对象
        """
        payload = {
            "name": name,
            "code": code,
            "type": type,
            **kwargs,
        }
        resp = self.client.post("/api/equipment", json=payload)

        if not resp.is_ok():
            logger.error(f"Create equipment failed: {resp.status_code} | {resp.body}")
            raise Exception(f"Create equipment API error: {resp.status_code}")

        return resp.json().get("data", {})

    def update_equipment(self, equipment_id: str, **kwargs) -> Dict[str, Any]:
        """
        更新设备。

        参数:
            equipment_id: 设备 ID
            **kwargs: 要更新的字段

        返回: 更新后的设备对象
        """
        resp = self.client.put(f"/api/equipment/{equipment_id}", json=kwargs)

        if not resp.is_ok():
            logger.error(f"Update equipment {equipment_id} failed: {resp.status_code}")
            raise Exception(f"Update equipment API error: {resp.status_code}")

        return resp.json().get("data", {})

    def delete_equipment(self, equipment_id: str) -> APIResponse:
        """
        删除设备。

        参数:
            equipment_id: 设备 ID
        """
        resp = self.client.delete(f"/api/equipment/{equipment_id}")

        if not resp.is_ok():
            logger.error(f"Delete equipment {equipment_id} failed: {resp.status_code}")
            raise Exception(f"Delete equipment API error: {resp.status_code}")

        return resp

    # ────────────────────────────────────────────────────────────────────
    # 其他端点占位（按需扩展）
    # ────────────────────────────────────────────────────────────────────

    def close(self):
        """关闭连接。"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
