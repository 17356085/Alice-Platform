# Excel 报告格式统一计划

> 创建: 2026-06-22 | 状态: 待执行 | 优先级: P0

## 问题陈述

`governance/kpi/reports/` 下 4 个有报告的模块存在 **3 种不同的 Excel 格式**，无一与参考格式（equipment per-page）完全一致。根因是 Agent 每次调用"当场写生成脚本"而非调用固定函数。

## 根因分析

### 责任比例

| 因素 | 占比 | 说明 |
|------|------|------|
| **Agent/架构问题** | 70% | excel-exporter Skill 让 Agent 写代码生成 Excel，非调用标准函数。每次 Agent 跑的脚本不同 → 格式必然不同 |
| **Skill 规范缺陷** | 20% | Scene C 模板缺失分组行(N条)、P0/P1/P2、emoji标注的规范；输出路径写的是按模块非按页面 |
| **历史残留** | 10% | 10 个 standalone 脚本、KPI README 命名规范与实际产出矛盾 |

### 证据

```
ZJSN_Test-master526/tools/report/
├── generate_customer_testcase_excel.py  ← 11列, 有(N条)
├── generate_final_two.py                ← 有(N条), P0/P1/P2
├── generate_dcs_excel.py                ← 11列, 无(N条), 无P0/P1/P2
├── generate_production_excel.py         ← 7列, 无分组
├── ...共10个脚本
```

- **0 行共享代码** — 全部 standalone，无 `import common_excel`
- 同一天（2026-06-18）3 次 Agent 调用产出 3 种格式

### Skill 规范与实际的 4 处关键偏差

| # | Skill Scene C 模板 | equipment 实际 | 缺失 |
|---|-------------------|---------------|------|
| 1 | `测试报告-{module}.xlsx`（按模块） | `测试报告-equipment-{page}.xlsx`（按页面） | 输出粒度 |
| 2 | `总用例: N` | `总: N (P0:X P1:Y P2:Z) \| 通过率: R%` | 优先级分布+通过率 |
| 3 | 无分组行定义 | `功能测试 (4条)` + 🆕/⚠️ | 分组格式 |
| 4 | 无用例ID格式 | `AC-01`, `CAM-01` | ID命名前缀 |

---

## 当前状态

### 各模块格式偏离

| 模块 | 文件数 | 列数 | 分组(N条) | P0/P1/P2 | 通过率 | 用例ID | 数据行 | 一致性 |
|------|--------|------|-----------|----------|--------|--------|--------|--------|
| equipment | 4 | 11 | ✅ | ✅ | ✅ | ✅ 真实 | ✅ 明细 | **参考** |
| dcs | 5 | 11 | ❌ 无计数 | ❌ | ❌ | ❌ `---` | ✅ 明细 | 部分 |
| production | 4 | 7 | ❌ 无分组 | ❌ | ✅ | ✅ 真实 | ✅ 明细 | 部分 |
| sales | 4 | 6 | ❌ | ❌ | ❌ | ❌ | ❌ 仅摘要 | 完全不一致 |
| 其余8模块 | 0 | — | — | — | — | — | — | 缺失 |

### 参考格式规范（equipment per-page）

```
Row1: 标题合并   "模块名 — 页面名 测试报告"
Row2: 统计合并   "生成时间: YYYY-MM-DD HH:MM | 页面: 页面名(slug) | 总: N (P0:X P1:Y P2:Z) | 通过: P | 失败: F | 跳过: S | 通过率: R%"
Row3: 空
Row4: 列标题    用例编号 | 用例标题 | 优先级 | 前置条件 | 测试步骤 | 输入数据 | 预期结果 | 实际状态 | 耗时(s) | 错误信息 | 自动化
Row5+: 分组标题  "功能测试 (N条)"、"搜索筛选测试 (N条)"... 含(N条)计数 + 🆕/⚠️标注
       数据行    真实case ID (AC-01, MT-01...)
```

- 11 列 (A-K)，sheet 名 = page slug
- 优先级配色: P0=红(#FFC7CE) / P1=黄(#FFEB9C) / P2=绿(#C6EFCE)
- 状态配色: PASS=绿 / FAIL=红 / SKIP=黄 / 未执行=灰
- 字体: 微软雅黑，表头蓝底(#4472C4)白字，冻结 A5

---

## 优化方案

### Phase 1: 统一生成引擎（消除 Agent 不确定性）⏱ 1-2h

新建共享库 `ZJSN_Test-master526/tools/report/excel_renderer.py`：

```python
"""Excel 报告统一渲染引擎 — 唯一的格式真相来源"""
from tools.report.excel_renderer import render_page_report

render_page_report(
    module="equipment",          # 模块英文名
    module_cn="设备管理",         # 模块中文名
    page_key="alarm-config",     # 页面 slug
    page_cn="设备报警配置",       # 页面中文名
    test_cases=parsed_cases,     # list[dict] from TEST_CASES.md
    allure_results=allure_map,   # dict[name→{status,duration,message}]
    output_dir="governance/kpi/reports/equipment/",
)
```

**固定输出（不可变）**:
- 文件名: `测试报告-{module}-{page}.xlsx`
- 1 sheet，名 = page slug
- 11 列固定表头（用例编号/用例标题/优先级/前置条件/测试步骤/输入数据/预期结果/实际状态/耗时(s)/错误信息/自动化）
- Row1 标题 + Row2 统计行（含 P0/P1/P2 + 通过率%）
- 按 `category` 字段自动分组 → `"{category}测试 ({N}条)"` 格式
- 新增用例自动 `🆕` 标注，已知问题自动 `⚠️` 标注
- 用例ID格式: `{module_abbr}-{page_abbr}-{seq:02d}`
- openpyxl 样式全部在函数内完成，调用方不可覆写

**辅助函数**:
```python
parse_test_cases_md(md_path: str) -> list[dict]
    # 解析 TEST_CASES.md Markdown 表格 → [{id, title, priority, category, precondition, steps, data, expected, auto}]

parse_allure_results(allure_dir: str) -> dict[str, dict]
    # 解析 *-result.json → {name: {status, duration, message}}

match_cases_to_results(cases, allure_map) -> list[dict]
    # 模糊匹配（去括号后缀 + 子串匹配）→ 合并后的完整数据行
```

**Agent 不再写代码，只调用函数。**

### Phase 2: 修正 Skill 规范 ⏱ 0.5h

更新 `governance/skills/execution/excel-exporter.md`:

1. **Scene C Prompt 模板**: 删除"生成 Python 脚本"段落，改为:
   ```
   调用 excel_renderer.render_page_report() 生成 Excel。
   你只需准备数据（解析 TEST_CASES.md + Allure JSON），不写代码。
   ```

2. **输出路径修正**: `测试报告-{module}.xlsx` → `测试报告-{module}-{page}.xlsx`

3. **补充分组行规范**:
   - 每个 category 生成一个合并的分组标题行 `"{category} ({N}条)"`
   - 新增分类（不在预定义列表中的）追加 `🆕`
   - 已知 Teleport/环境问题分类追加 `⚠️`

4. **补充统计行规范**: Row2 必须包含 `P0:N P1:N P2:N` 和 `通过率: R%`

5. **标记 Scene A/B 为废弃**（保留供手动参考）

更新 `governance/kpi/README.md`:
- 命名规范: `测试报告-{模块}.xlsx` → `测试报告-{模块}-{页面}.xlsx`
- 补充 per-page 粒度说明

### Phase 3: 清理与重新生成 ⏱ 0.5h

**3a. 归档旧脚本**:
```bash
mkdir -p ZJSN_Test-master526/tools/report/_archived/
mv ZJSN_Test-master526/tools/report/generate_*.py \
   ZJSN_Test-master526/tools/report/_archived/
# 仅保留 excel_renderer.py
```

**3b. 重新生成已有报告**（对齐 equipment 格式）:
| 模块 | 文件 | 操作 |
|------|------|------|
| dcs | 5 | 重新生成（原文件归档） |
| production | 4 | 重新生成（原文件归档） |
| sales | 4 | 重新生成（原文件归档） |

**3c. 生成缺失报告**:
| 模块 | 预计页面数 |
|------|-----------|
| lab | ~5 |
| personnel | ~10 |
| system | ~6 |
| system-management | ~6 |
| system-role | ~4 |
| tank | ~4 |
| warehouse | ~3 |
| workflow | ~4 |

### Phase 4: Agent 调用模式变更 ⏱ 0.5h

更新 `governance/agents/report-agent.md`:

```
旧流程: Agent 读 excel-exporter Skill → 写 Python 脚本 → 执行脚本 → 输出 xlsx
新流程: Agent 收集 TEST_CASES.md + Allure JSON → 调用 render_page_report() → 输出 xlsx
```

Agent 职责从"代码生成器"变为"数据准备器"。格式 100% 由共享库决定。

---

## 工作量汇总

| Phase | 内容 | 估时 | 产出物 |
|-------|------|------|--------|
| 1 | `excel_renderer.py` 共享库 | 1-2h | 1 个 .py 文件 |
| 2 | Skill + README 规范更新 | 0.5h | 2 个 .md 更新 |
| 3 | 归档旧脚本 + 重新生成 15+8 报告 | 0.5h | 目录清理 + 23 个 .xlsx |
| 4 | Agent 调用模式调整 | 0.5h | 1 个 .md 更新 |
| **合计** | | **3-4h** | |

---

## 验收标准

- [ ] `excel_renderer.py` 生成的 Excel 与 equipment per-page 参考格式逐行一致
- [ ] 所有 4 个已有模块（equipment/dcs/production/sales）重新生成后格式统一
- [ ] 8 个缺失模块全部生成初始报告
- [ ] 无 Agent 生成的 standalone 脚本残留在 `tools/report/` 下
- [ ] `excel-exporter.md` Skill 不再包含"写 Python 脚本"指令
- [ ] `KPI README.md` 命名规范与生成器一致
