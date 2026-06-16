# Skill: test-data-generation

## 目标
为测试场景生成可用于执行的测试数据。

## 输入
- TEST_CASES.md（测试数据列）
- 数据约束规则（长度、格式、唯一性、依赖关系）
- 已有测试数据种子（如有）

## 输出
- 格式化测试数据表（场景 → 输入数据 → 预期结果）

## 规则
- 数据必须满足所有约束规则
- 覆盖：合法数据、边界数据、异常数据
- 不同场景间数据不冲突（如名称唯一性）
- 标注数据间的依赖关系（如先创建再编辑）

## 依赖
- skills/testcase-design.md

## 边界
- 本 Skill 不生成测试用例，只生成测试数据
- 不生成自动化脚本

---

## Prompt 模板

```text
请为以下测试场景生成测试数据。

## 数据需求
- 模块：{{设备管理}}
- 场景：
  1. {{新增报警配置}} — 需要合法数据 3 组
  2. {{搜索报警}} — 需要覆盖：精确匹配、模糊匹配、无结果
  3. {{边界值测试}} — 需要：最小值、最大值、超限值、特殊字符

## 数据约束
- 名称：{{不超过50字符，不能重复}}
- 阈值：{{0-1000 之间的数字}}
- 类型：{{温度/压力/流量}}

## 输出格式
| 场景 | 输入数据 | 预期结果 |
|------|---------|---------|
| 合法新增1 | name=温度报警 type=温度 threshold=80 | 新增成功，表格可见 |
| 边界-最小值 | name=边界测试 type=温度 threshold=0 | 新增成功 |
| 边界-超限 | name=超限测试 type=温度 threshold=9999 | 表单校验提示"阈值范围0-1000" |
| 特殊字符 | name=<script>alert(1)</script> type=温度 threshold=50 | 新增成功，XSS被转义 |
| 模糊搜索 | keyword=温 | 返回含"温"的所有记录 |
| ... | | |

## 约束
- 数据必须满足所有数据约束规则
- 不同场景间数据不冲突（名称唯一）
- 覆盖：合法数据、边界数据、异常数据
```

### 生成 Python 测试数据文件

```text
基于以下测试用例，生成可导入的 Python 测试数据模块。

## 输入
- TEST_CASES：{{粘贴 TEST_CASES 中标注了测试数据的行}}
- 数据约束：{{粘贴 字段约束规则}}

## 任务
生成 `data/{{module}}_test_data.py`：

```python
"""{{设备管理}} 模块测试数据 — 自动生成"""

# 合法数据（新增用）
VALID_ALARM_CONFIGS = [
    {"name": "温度报警-测试01", "type": "温度", "threshold": 80, "expect": "success"},
    {"name": "压力报警-测试01", "type": "压力", "threshold": 100, "expect": "success"},
    {"name": "流量报警-测试01", "type": "流量", "threshold": 200, "expect": "success"},
]

# 边界值数据
BOUNDARY_ALARM_CONFIGS = [
    {"name": "边界-最小值", "type": "温度", "threshold": 0, "expect": "success"},
    {"name": "边界-最大值", "type": "温度", "threshold": 1000, "expect": "success"},
    {"name": "边界-超限值", "type": "温度", "threshold": 9999, "expect": "error", "error_msg": "阈值范围0-1000"},
]

# 异常数据（安全测试用）
ABNORMAL_ALARM_CONFIGS = [
    {"name": "", "type": "温度", "threshold": 50, "expect": "error", "error_msg": "请输入名称"},
    {"name": "A" * 51, "type": "温度", "threshold": 50, "expect": "error", "error_msg": "名称不超过50字符"},
    {"name": "<script>alert(1)</script>", "type": "温度", "threshold": 50, "expect": "success"},
    {"name": "测试'; DROP TABLE alarm;--", "type": "温度", "threshold": 50, "expect": "success"},
]

# 搜索数据
SEARCH_KEYWORDS = [
    {"keyword": "温度", "expect_min_results": 1, "desc": "精确匹配"},
    {"keyword": "温", "expect_min_results": 1, "desc": "模糊匹配"},
    {"keyword": "xyz_not_exist", "expect_min_results": 0, "desc": "无匹配结果"},
    {"keyword": "", "expect_min_results": 0, "desc": "空搜索"},
]
```

## 约束
- 数据间无冲突（名称唯一、不依赖特定数据库状态）
- 每组数据标注期望结果（success/error + error_msg）
- 异常数据覆盖 OWASP Top 10 注入向量
- 使用数据清理前缀（如 "测试-"）便于 teardown 识别
```

## 检查清单
- [ ] 覆盖合法数据 ≥ 3 组
- [ ] 覆盖边界数据（最小值/最大值/超限值）
- [ ] 覆盖异常数据（空值/超长/特殊字符/SQL注入/XSS）
- [ ] 数据间无冲突（唯一性约束满足）
- [ ] 标注了数据间的依赖关系（先创建再编辑等）
- [ ] Python 数据文件可直接 import 使用
