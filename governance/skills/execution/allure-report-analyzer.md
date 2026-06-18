# Skill: allure-report-analyzer

## 目标
解析 Allure 原始 JSON 结果文件，自动生成结构化测试摘要报告。不依赖图片分析，仅从 JSON 文本数据提取通过率、失败分布、耗时趋势。

## 输入
- Allure JSON 结果文件（`allure-results/*-result.json`）
- 历史对比基线（上次执行的 Allure JSON 或上次的 TEST_SUMMARY.md）

## 输出
- TEST_SUMMARY.md（含通过率、失败分布、趋势对比、不稳定用例清单）
- 失败用例分组（按错误类型：TimeoutException / AssertionError / NoSuchElementException / 其他）

## 规则
- 纯文本解析：只从 JSON 的 `status`、`statusDetails.message`、`statusDetails.trace`、`labels`、`steps` 字段提取信息
- 不读取截图附件（`attachments` 中的 base64 或文件路径只做引用）
- 与上次构建对比：通过率变化、新增失败、修复用例
- 自动标注不稳定用例（最近 N 次执行中状态不一致的用例）

## JSON 数据字段说明

```
*-result.json 关键字段:
├── name:               用例名称
├── fullName:           全限定名 (含模块和类名)
├── status:             "passed" | "failed" | "broken" | "skipped" | "unknown"
├── statusDetails:
│   ├── message:        错误消息（一行摘要）
│   ├── trace:          完整堆栈（可从中提取异常类型）
│   └── flaky:          (可选) 是否标记为不稳定
├── stage:              "scheduled" | "running" | "finished"
├── steps[]:            每个 allure.step() 的执行记录
│   ├── name:           步骤名称
│   ├── status:         步骤状态
│   └── start / stop:   时间戳
├── labels[]:
│   ├── name:"epic" / "feature" / "story" / "severity" / "tag"
│   └── value:          对应值
├── attachments[]:      附件（截图/日志等，本Skill不解析）
└── start / stop:       执行时间戳（可用于计算耗时）
```

## 依赖
- `governance/skills/test-summary.md`
- Allure JSON 格式（2.13.2）

## 边界
- 本 Skill 只解析 Allure JSON，不解析 HTML 报告或截图
- 不分析单个失败根因（那是 bug-analysis 的职责）
- 不修改 Allure 源文件

---

## Prompt 模板

### 单次执行摘要

```text
解析以下 Allure 测试结果，生成 TEST_SUMMARY.md。

## 执行信息
- 执行时间：{{2026-06-11 14:30}}
- 环境：{{test}}
- Allure JSON：{{粘贴 3-5 个典型 *-result.json 的内容}}

## 任务
1. **总体统计**：
   | 指标 | 数值 |
   |------|------|
   | 总用例数 | {{N}} |
   | 通过 | {{N}} (%) |
   | 失败 | {{N}} (%) |
   | 跳过 | {{N}} (%) |
   | 总耗时 | {{X}} min |

2. **失败用例分组**（按异常类型）：
   | 异常类型 | 数量 | 占比 | 代表用例 |
   |----------|------|------|----------|
   | TimeoutException | 3 | 60% | test_search_by_name |
   | AssertionError | 1 | 20% | test_add_role_validation |
   | NoSuchElementException | 1 | 20% | test_delete_role |

3. **按模块分布**：
   | 模块 | 总数 | 通过 | 失败 | 通过率 |
   |------|------|------|------|--------|
   | equipment | 20 | 18 | 2 | 90% |
   | system | 15 | 14 | 1 | 93% |

4. **按 epic/feature 分布**：从 labels[] 提取分组统计

5. **不稳定用例检测**（需要历史数据时）：
   标注状态不一致的用例（如：最近3次执行中2次通过1次失败）

6. **关键步骤耗时 Top 5**：从 steps[].stop - steps[].start 计算
```

### 与上次构建对比

```text
对比本次和上次 Allure 测试结果。

## 本次 JSON
{{粘贴本次 3-5 个 result JSON}}

## 上次摘要
{{粘贴上次 TEST_SUMMARY.md 或上次的 JSON}}

## 任务
1. **通过率变化**：本次 XX% vs 上次 XX%（↑/↓ XX%）
2. **新增失败**：上次通过、本次失败的用例（含错误信息）
3. **修复用例**：上次失败、本次通过的用例
4. **不稳定用例**：状态频繁变化的用例清单
5. **耗时变化**：总耗时 ↑/↓ XX%
```

---

## 检查清单

- [ ] 总体统计完整（总数/通过/失败/跳过/耗时）
- [ ] 失败用例按异常类型分组
- [ ] 按模块分布统计
- [ ] 对比模式下：新增失败 + 修复用例 + 不稳定用例全部标注
- [ ] 不依赖截图/附件解析
- [ ] 输出可直接作为 TEST_SUMMARY.md 使用

## 产出物
→ `TEST_SUMMARY.md`，存放至 `governance/context/projects/web-automation/summaries/`。
→ 格式参见 `templates/test-summary.template.md`。
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | execution | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->