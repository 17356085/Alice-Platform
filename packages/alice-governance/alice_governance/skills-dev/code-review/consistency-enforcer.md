# Skill: code-review/consistency-enforcer

### 目标
机械化检查（不调 LLM）：验证前后端接口一致性——前端调用的 API 是否在后端存在、请求/响应类型是否匹配。

### 输入
- 前端 API 调用代码（`api/*.ts`）
- 后端 Router 代码（`routers/*.py`）
- API_CONTRACTS.md

### 输出
- `CONSISTENCY_REPORT.md`：不一致项清单

### 规则
- **Mechanical** — grep 前端 fetch/axios 调用，对照后端路由
- 检查：路径匹配、HTTP 方法匹配、请求体字段匹配
- 不匹标注为 ⚠️

---

## Prompt 模板（无 LLM — 纯脚本）

```python
import re, sys
from pathlib import Path

# Extract frontend API calls
frontend_calls = set()
for f in Path("frontend/src/api").rglob("*.ts"):
    for match in re.finditer(r'(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', f.read_text()):
        frontend_calls.add(match.group(1))

# Extract backend routes  
backend_routes = set()
for f in Path("backend/app/routers").rglob("*.py"):
    for match in re.finditer(r'@router\.(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', f.read_text()):
        backend_routes.add(match.group(1))

missing = frontend_calls - backend_routes
print(f"Frontend calls: {len(frontend_calls)}, Backend routes: {len(backend_routes)}")
print(f"Mismatches: {len(missing)}")
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | code-review | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->