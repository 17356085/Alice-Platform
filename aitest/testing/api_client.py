"""
HTTP API 客户端 — 统一 REST 请求驱动

功能:
  1. 封装 requests 核心：认证、重试、超时、响应校验
  2. 参数化 URL + Headers + Body 构造
  3. JSON Schema 响应验证（可选）
  4. 自动日志 + 性能指标
"""
import logging
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("aitest.api_client")


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


@dataclass
class APIResponse:
    """统一响应容器。"""
    status_code: int
    headers: Dict[str, str]
    body: Any  # JSON 或 bytes
    elapsed_ms: float
    raw_response: requests.Response

    def json(self) -> Dict:
        """返回 JSON 体。"""
        if isinstance(self.body, dict):
            return self.body
        return {}

    def text(self) -> str:
        """返回文本体。"""
        return self.raw_response.text

    def is_ok(self) -> bool:
        """状态码是否 2xx。"""
        return 200 <= self.status_code < 300


class APIClient:
    """
    RESTful API 客户端。

    示例:
        client = APIClient(base_url="https://api.example.com", timeout=10)
        resp = client.get("/users", params={"id": 1})
        assert resp.is_ok()
        print(resp.json())
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.3,
        verify_ssl: bool = True,
    ):
        """
        参数:
            base_url: API 基地址（含 http:// 或 https://）
            timeout: 单个请求超时秒数
            max_retries: 重试次数（5xx 状态码）
            backoff_factor: 退避倍数
            verify_ssl: 是否校验 SSL 证书
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.verify = verify_ssl

        # 重试策略：仅 5xx + 连接错误
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 默认 headers
        self.default_headers = {
            "User-Agent": "AITest-APIClient/1.0",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: HTTPMethod,
        path: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> APIResponse:
        """
        发送 HTTP 请求（内部）。

        参数:
            method: HTTP 方法
            path: URI 路径（相对 base_url）
            params: 查询参数
            data: form-data 体
            headers: 自定义 headers
            json: JSON 体（互斥 data）
        """
        url = f"{self.base_url}{path}"
        req_headers = {**self.default_headers}
        if headers:
            req_headers.update(headers)

        start = time.time()
        try:
            resp = self.session.request(
                method.value,
                url,
                params=params,
                data=data,
                json=json,
                headers=req_headers,
                timeout=self.timeout,
            )
            elapsed_ms = (time.time() - start) * 1000

            # 日志
            logger.debug(
                f"{method.value} {path} | {resp.status_code} | {elapsed_ms:.1f}ms"
            )

            # 解析响应体
            try:
                body = resp.json()
            except ValueError:
                body = resp.text

            return APIResponse(
                status_code=resp.status_code,
                headers=dict(resp.headers),
                body=body,
                elapsed_ms=elapsed_ms,
                raw_response=resp,
            )
        except requests.RequestException as e:
            elapsed_ms = (time.time() - start) * 1000
            logger.error(f"{method.value} {path} | ERROR | {str(e)}")
            raise

    def get(
        self,
        path: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> APIResponse:
        """GET 请求。"""
        return self._request(HTTPMethod.GET, path, params=params, headers=headers)

    def post(
        self,
        path: str,
        json: Optional[Dict] = None,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> APIResponse:
        """POST 请求。"""
        return self._request(
            HTTPMethod.POST,
            path,
            params=params,
            data=data,
            json=json,
            headers=headers,
        )

    def put(
        self,
        path: str,
        json: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> APIResponse:
        """PUT 请求。"""
        return self._request(
            HTTPMethod.PUT,
            path,
            params=params,
            json=json,
            headers=headers,
        )

    def patch(
        self,
        path: str,
        json: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> APIResponse:
        """PATCH 请求。"""
        return self._request(
            HTTPMethod.PATCH,
            path,
            params=params,
            json=json,
            headers=headers,
        )

    def delete(
        self,
        path: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> APIResponse:
        """DELETE 请求。"""
        return self._request(
            HTTPMethod.DELETE,
            path,
            params=params,
            headers=headers,
        )

    def set_auth_token(self, token: str, scheme: str = "Bearer"):
        """设置 Bearer Token 认证。"""
        self.default_headers["Authorization"] = f"{scheme} {token}"

    def set_auth_basic(self, username: str, password: str):
        """设置 HTTP Basic 认证。"""
        import base64
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.default_headers["Authorization"] = f"Basic {credentials}"

    def close(self):
        """关闭会话。"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
