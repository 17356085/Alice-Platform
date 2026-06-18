# Skill: report-generator

## 目标
统一报告生成引擎。支持三种模式：
- **模式 A (test-summary)**：测试周期总结报告（TEST_SUMMARY.md）
- **模式 B (progress)**：周度/阶段进度报告 + 进度追踪更新
- **模式 C (excel)**：测试用例/执行结果导出为 .xlsx

## 输入

| 模式 | 输入 | 触发时机 |
|------|------|----------|
| A: test-summary | 测试执行报告 + Bug统计 + 自动化结果 + 遗留问题清单 | 测试周期结束 |
| B: progress | 日报/周报 + 进度追踪 + 用例统计 + Bug统计 | 定期汇报 |
| C: excel | TEST_CASES.md 或 Allure JSON | 按需导出 |

## 输出

| 模式 | 输出 |
|------|------|
| A | TEST_SUMMARY.md（含结论：✅建议上线 / ⚠️有条件 / ❌不建议） |
| B | 进度报告 + 更新后的进度追踪 |
| C | .xlsx 文件（governance/kpi/reports/{模块}/ 目录，覆盖式无日期后缀） |

## 规则（通用）

1. **数据驱动**：所有统计数据必须有来源，不得编造
2. **环比对比**：模式 A/B 均需对比上周期/上周数据
3. **结论明确**：模式 A 必须三选一（建议上线/有条件/不建议）；模式 B 必须标注进度偏差
4. **格式参考模板**：
   - 模式 A → `templates/test-summary.template.md`
   - 模式 B → 标准周报格式（表格式）
   - 模式 C → Excel 样式参考 `ZJSN_Test-master526/tools/report/generate_*.py`

## 依赖

- `governance/templates/test-summary.template.md`
- `governance/workflows/test-cycle-closure.md`
- `ZJSN_Test-master526/tools/report/`（Excel 样式参考）

## 边界

- ❌ 不分析 Bug 根因（那是 bug-analysis 的职责）
- ❌ 不设计新测试用例（那是 test-design 的职责）
- ❌ 不执行测试（那是 execution 的职责）
- ✅ 本 Skill 是 report-agent 的核心 Skill（★Primary Owner）

---

## Prompt 模板

### 模式 A：测试周期总结（test-summary）

```text
基于以下测试执行数据，生成测试周期总结报告。

## 输入数据
- 测试周期：{{2026-06-01 ~ 2026-06-09}}
- 测试范围：{{设备管理模块}}
- 执行报告汇总：
  - 总用例数：{{N}} / 通过：{{N}} / 失败：{{N}} / 阻塞：{{N}}
  - 通过率：{{%}}
- Bug统计：Blocker={{N}} / Critical={{N}} / Major={{N}} / Minor={{N}}
- 自动化覆盖：{{%}}

## 任务
输出 TEST_SUMMARY.md，包含：

1. **测试概况**：周期、范围、执行结论
2. **用例执行统计**：总表 + 按模块拆分表
3. **Bug统计**：按严重程度 + 按模块交叉分析
4. **遗留Bug清单与风险评估**：逐Bug评估上线风险
5. **自动化覆盖情况**：覆盖率 + 未覆盖高危场景
6. **测试结论**：✅ 建议上线 / ⚠️ 有条件上线 / ❌ 不建议上线
7. **后续建议**：下周期重点

## 格式
参考 templates/test-summary.template.md
```

### 模式 B：进度报告（progress）

```text
基于我本周的日报和当前测试进度，生成一份进度报告。

## 输入
- 本周日报：{{粘贴 工作日志/日报/ 内容}}
- 当前进度追踪：{{粘贴 测试进度追踪.md}}

## 任务
1. 统计本周完成的工作量：
   - 新增用例数：{{N}}
   - 自动化用例数：{{N}}
   - 发现Bug数：{{N}}（按严重程度分）
   - 覆盖模块数/页面数
2. 与上周环比对比（趋势 ↑/↓）
3. 更新「测试进度追踪.md」中的状态
4. 识别进度偏差（哪些模块落后计划）
5. 生成周报草稿（可直接用于汇报）

## 输出格式
| 维度 | 本周 | 上周 | 趋势 |
|------|------|------|------|
| 新增用例 | | | |
| 自动化用例 | | | |
| 发现Bug(Blocker/Critical/Major) | | | |
| 覆盖模块 | | | |
```

### 模式 C：Excel 导出（excel）

```text
将测试用例/执行结果导出为格式化的 Excel 文件。

## 场景 C-1：TEST_CASES.md → 测试用例 Excel

> ⚠️ **已废弃**：Phase 3 不生成 Excel，仅产出 .md 文件。此场景保留供手动使用，不走 SOP 流程。

参数：
- 模块名称：{{设备管理}}
- 页面名称：{{设备报警配置}}
- TEST_CASES.md：{{粘贴用例表格}}

输出：`governance/kpi/reports/{模块}/测试用例-{模块}-{页面}.xlsx`（手动触发，非 SOP）
样式：蓝色表头(#4472C4)、P0=红/P1=黄/P2=绿、冻结首行、自动列宽

## 场景 C-2：Allure JSON → 执行结果 Excel ★ Phase 9 主场景

参数：
- 模块名称：{{模块}}
- allure-results/ 目录下的 *-result.json 文件

输出：`governance/kpi/reports/{模块}/测试报告-{模块}.xlsx`（覆盖式，无日期后缀）
样式：PASS=绿/FAIL=红/SKIP=黄/BROKEN=灰、按模块分Sheet、含通过率统计行
```

---

## 检查清单

### 模式 A
- [ ] 用例统计总表 + 按模块拆分表完整
- [ ] Bug按严重程度和模块交叉分析
- [ ] 每个遗留Bug评估了上线风险
- [ ] 测试结论三选一明确（建议上线/有条件/不建议）
- [ ] 下周期建议具体可执行

### 模式 B
- [ ] 统计维度完整：用例/自动化/Bug/覆盖
- [ ] 环比上周有对比数据
- [ ] 进度偏差已识别（落后/超前模块）
- [ ] 下阶段建议具体可执行

### 模式 C
- [ ] 优先级/状态配色正确
- [ ] 冻结首行 + 列宽自适应
- [ ] 文件名：`测试报告-{模块}.xlsx`（无日期后缀，覆盖式）
- [ ] 通过率计算正确（场景 C-2）

## 产出物

| 模式 | 产出 |
|------|------|
| A | `context/projects/*/summaries/TEST_SUMMARY.md` |
| B | 周报草稿 + 进度追踪更新 |
| C | `governance/kpi/reports/{模块}/测试报告-{模块}.xlsx`（覆盖式） |
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | reporting | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->