# system_page 合规扫描报告

> 扫描日期：2026-06-11 | 扫描工具：code-consistency-checker（手动执行）
> 规范来源：`PROJECT_CONTEXT.md` § 编码强制规范 + § 禁止模式

## 扫描结果总览

| 文件 | 行数 | 继承BasePage | time.sleep | 绝对XPath | print() | logger | 合规度 |
|------|------|-------------|------------|-----------|---------|--------|--------|
| SystemLogPage.py | 516 | ❌ | 16 | 9 | 0 | 0 | **0%** |
| MenuManagePage.py | 878 | ❌ | 38 | 10 | 0 | 0 | **0%** |
| OperationLogPage.py | 589 | ❌ | 18 | 8 | 0 | 0 | **0%** |
| RoleManagePage.py | 979 | ❌ | 51 | 8 | 2 | 0 | **0%** |
| **合计** | **2962** | **0/4** | **123** | **35** | **2** | **0** | |

> **对比**: UserManagePage 重构前同样 0% 合规，重构后达到 100%。这 4 个文件需同流程重构。

## 逐文件问题详情

### SystemLogPage.py（516行）
- [ ] **P0-01** 未继承 BasePage — `class SystemLogPage:` 无基类
- [ ] **P0-02** 16处 `time.sleep()` — 硬等待
- [ ] **P0-03** 9处绝对 XPath — 含 `//*[@id="app"]/div/...`
- [ ] **P0-04** 无 logger — 使用 print() 或静默

### MenuManagePage.py（878行）
- [ ] **P0-01** 未继承 BasePage
- [ ] **P0-02** 38处 `time.sleep()` — 最严重
- [ ] **P0-03** 10处绝对 XPath
- [ ] **P0-04** 无 logger

### OperationLogPage.py（589行）
- [ ] **P0-01** 未继承 BasePage
- [ ] **P0-02** 18处 `time.sleep()`
- [ ] **P0-03** 8处绝对 XPath
- [ ] **P0-04** 无 logger

### RoleManagePage.py（979行）
- [ ] **P0-01** 未继承 BasePage
- [ ] **P0-02** 51处 `time.sleep()` — 最严重
- [ ] **P0-03** 8处绝对 XPath
- [ ] **P0-04** 2处 `print()` 调用
- [ ] **P0-05** 无 logger

## 建议

1. **优先重构 RoleManagePage**（最多 sleep + 有 print，影响面最大）
2. **然后 MenuManagePage**（第二多 sleep）
3. 重构流程参照 `artifacts/user-manage-page-refactor-plan.md` 的 5 步方案
4. 每次重构后运行对应 test_*.py 确认行为等价

## 关联

- [[user-manage-page-refactor-plan]] — 已执行的重构模板
- PROJECT_CONTEXT.md § 编码强制规范 — 检查依据
- code-consistency-checker — 自动化检查 Skill
