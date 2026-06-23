# 测试数据管理规范

> **加载者**: automation-agent（代码生成时参考）, execution-agent（执行前确认）
> ⚠️ **公司要求不留脏数据。** 所有测试脚本必须确保创建的测试数据在 teardown 阶段被清理。

## 核心原则

1. **谁创建，谁清理** — 测试用例创建的数据必须由该用例或 fixture 负责删除
2. **注册胜于遗忘** — 使用 `CleanupTracker` 注册所有待清理实体，而非手动调用删除
3. **teardown 兜底** — fixture teardown 中执行清理，即使用例失败也必须执行
4. **清理失败不阻塞** — 清理抛出异常只发 warning，不导致用例失败
5. **可识别前缀** — 所有测试数据名称统一前缀（如 `TC-`、`TEST-`），便于人工巡查

## 已有基础设施

项目已有 `base/cleanup_tracker.py`（`CleanupTracker`），基于注册模式管理脏数据。
全局 autouse fixture `_data_cleanup`（`script/conftest.py`）在每条用例 teardown 时自动触发清理。

### 标准注册（推荐）

```python
from base.cleanup_tracker import get_cleanup_tracker

def test_add_dict(dict_page):
    tracker = get_cleanup_tracker()
    # 注册待清理实体 — teardown 时自动通过 API 删除
    tracker.register(
        entity_type="dict",
        entity_id=42,
        entity_name="TC-字典类型",
        api_delete_url="/api/system/dict/type/{id}",
    )
    # 测试逻辑...
    # teardown 时 autouse fixture 自动调用 cleanup_all()
```

### 回调式注册（无 API 时的兜底）

```python
def test_delete_monitor(monitor_page):
    tracker = get_cleanup_tracker()
    # register_entity 是 register() 的别名，支持 delete_callback
    tracker.register_entity(
        "monitor",
        "TC-监控项",
        delete_callback=lambda name: monitor_page.delete_monitor_by_name(name),
    )
    # 清理时调用 delete_callback("TC-监控项")
```

### 手动清理（不依赖 autouse）

```python
def test_batch_ops(all_data_page):
    tracker = get_cleanup_tracker()
    # ... 创建数据、注册 ...
    # 立即清理（不等到 teardown）
    tracker.cleanup_all(warn_only=True)
```

## 各级清理策略

| 级别 | 时机 | 策略 | 适用场景 |
|------|------|------|----------|
| **API 清理**（推荐） | fixture teardown | 调用 DELETE API 删除 | 新增/编辑操作（有后端接口的模块） |
| **UI 清理** | fixture teardown | 通过 Page Object 在页面中点删除 | 无独立删除 API 的场景 |
| **DB 清理** | module teardown | 直连数据库执行 DELETE | 测试环境有数据库访问权限 |
| **手工巡查** | 定期 | 按前缀搜索并人工确认 | 兜底：自动化清理遗漏的数据 |

## 测试数据命名规范

| 数据用途 | 命名前缀 | 示例 | 备注 |
|----------|----------|------|------|
| 自动化测试通用数据 | `TC-` | 用户: TC-张三, 角色: TC-admin | 所有模块通用 |
| 模块专属数据 | `TC-{模块}-` | TC-equip-报警001 | 配合 teardown 按前缀筛选 |
| 储罐模块 | `TEST-` | TEST-罐001 | tank 模块约定 |
| 一次性调试数据 | `DBG-` | DBG-临时数据 | 执行后立即清理，不留过夜 |

## TEST_DESIGN 中的数据策略声明

每份 `TEST_DESIGN.md` 必须明确以下内容（见 `templates/test-design.template.md`）：

```
## 数据策略
- 测试数据来源：data/alarm_config_data.py（种子数据）
- 数据清理方式：fixture teardown 中按名称前缀"TC-"删除测试数据
- 清理失败处理：只发 warning，不阻塞其他用例
```

## 红线检查

在 `code-consistency-checker` 中，以下两项为必查：
- ❌ **无清理逻辑** — 测试脚本创建了数据但没有 teardown 删除，视为**红线违规**
- ⚠️ **清理失败抛异常** — 清理代码抛出异常导致用例 FAIL，应改为 warning
