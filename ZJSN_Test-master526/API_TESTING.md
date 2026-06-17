# API 测试模块

## 结构

```
aitest/testing/
  └─ api_client.py          # HTTP 通用驱动

ZJSN_Test-master526/
  base/
    └─ api_base.py          # 被测系统 API 基类（Page Object 风格）
  script/
    ├─ equipment/
    │   └─ test_api_equipment.py    # 设备管理 API 用例
    ├─ personnel/
    │   └─ test_api_personnel.py    # 人员管理 API 用例（可选）
    └─ conftest.py          # 共享 fixture
```

## 用法

### 第 1 步：环境配置

```bash
# .env 或环境变量
export TEST_API_BASE_URL="https://aiwechatminidemo.cimc-digital.com/api"
export TEST_USER="admin"
export TEST_PASSWORD="password"
```

### 第 2 步：运行用例

```bash
cd ZJSN_Test-master526

# 单个模块
pytest script/equipment/test_api_equipment.py -v

# 全部 API 用例
pytest script/*/test_api_*.py -v

# 带 allure 报告
pytest script/equipment/test_api_equipment.py -v --alluredir=allure-results
allure serve allure-results
```

## 架构

### 层 1：HTTP 驱动 (`api_client.py`)

- 封装 `requests` — 重试 + 超时 + 认证
- 统一 `APIResponse` 容器

```python
from aitest.testing.api_client import APIClient

client = APIClient(base_url="https://api.example.com")
resp = client.get("/users", params={"page": 1})
assert resp.is_ok()
```

### 层 2：业务基类 (`api_base.py`)

- Page Object 风格 — API 端点映射为方法
- 自动认证 + Token 注入
- Schema 化请求/响应

```python
from base.api_base import AJSystemAPI

api = AJSystemAPI(base_url="https://api.example.com")
api.login(username="admin", password="password")
users = api.get_users(page=1)
```

### 层 3：用例 (`test_api_*.py`)

- Pytest + Allure
- 与 UI 用例并行
- 按模块组织

```python
def test_get_equipment_list(api_client):
    resp = api_client.get_equipment_list(page=1, page_size=20)
    assert resp.code == 200
```

## 扩展指南

### 1. 新增模块 API 用例

1. 在 `api_base.py` 中添加端点方法
2. 在 `script/<module>/test_api_<module>.py` 中编写用例
3. 使用 fixture 自动登录 + 清理

示例：

```python
# api_base.py
def get_personnel_list(self, page=1, page_size=20):
    resp = self.client.get("/api/personnel", params={...})
    return ListResponse.from_json(resp.json())

# test_api_personnel.py
def test_get_personnel_list(api_client):
    resp = api_client.get_personnel_list()
    assert resp.code == 200
```

### 2. 自定义认证

```python
# Bearer Token
api.client.set_auth_token("token_value")

# Basic Auth
api.client.set_auth_basic(username="user", password="pass")

# 自定义 Header
api.client.default_headers["X-API-Key"] = "key_value"
```

### 3. 响应校验

```python
resp = api.get_equipment(equipment_id)
assert resp.is_ok()
assert resp.json()["data"]["name"] == "expected_name"
```

## 与 UI 用例对比

| 维度 | UI 用例 | API 用例 |
|------|--------|---------|
| 执行速度 | 慢（Selenium） | 快（HTTP） |
| 覆盖层 | UI 交互 + 逻辑 | 后端逻辑 + 数据库 |
| 维护成本 | 高（定位器脆弱） | 低（Schema 稳定） |
| SOP 位置 | Page Object 定位 | API 端点调用 |

## 故障排查

### 401 Unauthorized

```
症状: 所有请求返回 401
原因: Token 过期或 login() 未执行
解决: 确保 fixture 中执行了 api.login()
```

### 429 Too Many Requests

```
症状: 随机请求失败
原因: 频率限制
解决: 增加 backoff_factor，或在 conftest.py 添加延迟
```

### SSL 证书错误

```
症状: requests.exceptions.SSLError
原因: 测试环境自签名证书
解决: 使用 verify_ssl=False（仅测试环境）
```

## 下一步

- [ ] 集成到 SOP 图（governance/graphs_dev/）
- [ ] 添加性能基准（response time 追踪）
- [ ] Schema 验证（Pydantic + JsonSchema）
- [ ] 多租户支持（API key 管理）
