# Skill: backend/backend-consistency-checker

### 目标
机械化检查（不调 LLM）：对生成的后端代码执行 import 完整性检查 + endpoint 覆盖率检查 + 类型一致性检查。

### 输入
- 所有生成的后端 `.py` 文件路径列表
- `API_CONTRACTS.md` — 期望的 API 端点清单

### 输出
- 一致性检查报告：import 缺失、未覆盖的端点、类型不匹配

### 规则
- 此 Skill 是 **mechanical**（不调 LLM）——直接 grep + import 检查
- 不修改代码（只报告问题）

### 代码红线（后端 8 条）

| # | ❌ 禁止 | ✅ 必须 | 检查方式 |
|---|---------|--------|-----------|
| 1 | sync def | `async def` | `grep "def "` 检查无 "async" 前缀 |
| 2 | Pydantic v1 | `model_config` | `grep "class Config:"` (禁止) |
| 3 | print() | logger | `grep "print\("` (禁止) |
| 4 | SQLAlchemy 1.x | `select()` + `mapped_column` | `grep "Column("` (禁止) |
| 5 | 无 docstring | 每个端点有 docstring | AST 检查 |
| 6 | 不明确的类型 | 完整类型注解 | `grep ": Any\|: any"` (禁止) |
| 7 | 吞异常 | HTTPException | `grep "except.*:"` (检查无 `raise`) |
| 8 | 硬编码配置 | settings/环境变量 | `grep "http://\|https://"` (禁止) |

### 依赖
- 无前置 LLM Skill

### 边界
- 不修改代码
- 不运行测试（那是 build-agent 的 test-runner 职责）

---

## Prompt 模板（无 LLM — 纯脚本）

> 此 Skill 不需要 LLM。直接执行以下检查脚本：

```bash
echo "=== Backend 一致性检查 ==="
ERROR_COUNT=0

for f in {{TARGET_FILES}}; do
  echo "--- $f ---"

  # 红线1: async def（非测试文件）
  if [[ "$f" == *"routers/"* ]]; then
    sync_endpoints=$(grep -n "^def " "$f" || true)
    if [ -n "$sync_endpoints" ]; then
      echo "  ❌ 同步端点（应为 async def）: $sync_endpoints"
      ((ERROR_COUNT++))
    fi
  fi

  # 红线2: 遗留 Pydantic v1 配置
  if grep -q "class Config:" "$f"; then
    echo "  ❌ 使用 Pydantic v1 class Config（应为 model_config = ConfigDict(...)）"
    ((ERROR_COUNT++))
  fi

  # 红线3: print() 调试
  print_lines=$(grep -n "print(" "$f" | grep -v "#" || true)
  if [ -n "$print_lines" ]; then
    echo "  ❌ print() 调试残留: $print_lines"
    ((ERROR_COUNT++))
  fi

  # 红线4: SQLAlchemy 1.x Column() 语法
  if grep -qP "^\s+\w+\s*=\s*Column\(" "$f"; then
    echo "  ❌ SQLAlchemy 1.x Column() — 应使用 mapped_column()"
    ((ERROR_COUNT++))
  fi

  # 红线6: Any 类型
  if grep -qP ": Any|: any" "$f"; then
    echo "  ❌ Any 类型 — 应使用具体类型"
    ((ERROR_COUNT++))
  fi

  # 红线8: 硬编码 URL
  urls=$(grep -nP "(http://|https://)" "$f" | grep -v "localhost" | grep -v "test" || true)
  if [ -n "$urls" ]; then
    echo "  ❌ 硬编码外部 URL: $urls"
    ((ERROR_COUNT++))
  fi
done

echo "=== 检查完成: $ERROR_COUNT 个错误 ==="
```

### Python fallback (if bash unavailable)

```python
import re, sys
from pathlib import Path

CHECKS = [
    ("async def (routers)", r"^def \w+.*:", True, lambda f: "routers" in str(f)),
    ("Pydantic v2 model_config", r"class Config:", False, None),
    ("no print()", r"^\s*print\(", False, None),
    ("SQLAlchemy 2.0 mapped_column", r"^\s+\w+\s*=\s*Column\(", False, None),
    ("no Any type", r":\s*Any\b", False, None),
]

for fpath in Path("{{TARGET_DIR}}").rglob("*.py"):
    content = fpath.read_text()
    for label, pattern, should_find, condition in CHECKS:
        if condition and not condition(fpath):
            continue
        found = bool(re.search(pattern, content, re.MULTILINE))
        if found != should_find:
            print(f"  ❌ {fpath.name}: {label}")
```
```
