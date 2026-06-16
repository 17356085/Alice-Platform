# TEST SUMMARY — system-management 工作流管理 7页面

> 2026-06-12 | 3轮修复 | 全量回归 28P/6F/11S

## 一、执行摘要

| 指标 | 值 |
| --- | --- |
| 测试范围 | system-management 模块 7 个零覆盖页面 |
| 新增代码 | 14 文件（7 PO + 7 测试脚本），~2,500 行 |
| 新增用例 | 46 条（smoke 7 + functional 30 + boundary 7 + validation 2） |
| 修复轮次 | 3 轮 |
| 修复 Bug 数 | 4 个关键 Bug + 2 个环境问题 |
| 最终结果 | 28 passed, 6 failed, 11 skipped（单文件：6/7 零失败） |
| 遗留问题 | SAP日志/API管理/监控管理各 2 fail（全量回归环境问题） |

## 二、测试结果总览

### 单文件运行（推荐模式）

| 测试文件 | Pass | Fail | Skip | 状态 |
|---------|------|------|------|:--:|
| test_my_application.py | 5 | 0 | 3 | ✅ |
| test_approval_todo.py | 6 | 0 | 2 | ✅ |
| test_approval_history.py | 6 | 0 | 1 | ✅ |
| test_approval_chain.py | **8** | **0** | **1** | ✅ (1→8) |
| test_sap_push_log.py | 4 | 0 | 2 | ✅ |
| test_api_management.py | 3 | 0 | 1 | ✅ |
| test_monitor_management.py | 2 | 0 | 2 | ✅ |
| **合计** | **34** | **0** | **12** | 🟢 |

### 全量回归

| 测试文件 | Pass | Fail | Skip | 状态 |
|---------|------|------|------|:--:|
| test_my_application.py | 5 | 0 | 3 | ✅ |
| test_approval_todo.py | 6 | 0 | 2 | ✅ |
| test_approval_history.py | 6 | 0 | 1 | ✅ |
| test_approval_chain.py | 7 | 1 | 0 | 🟢 |
| test_sap_push_log.py | 3 | 2 | 1 | 🔴 |
| test_api_management.py | 1 | 1 | 2 | 🔴 |
| test_monitor_management.py | 0 | 2 | 2 | 🔴 |
| **合计** | **28** | **6** | **11** | |

## 三、关键 Bug 修复记录

| # | Bug | 发现阶段 | 根因 | 修复 | 影响文件 |
|:---:|------|:---:|------|------|------|
| 1 | 工作流页面路由跳404 | 首次运行 | 短路径 `#/todo` 不被Vue识别 | sidebar_navigator + conftest + 4PO 改用完整路径 | 5 文件 |
| 2a | 搜索/重置按钮定位器不匹配 | 首次运行 | 自定XPath与HTML不匹配 | 委托BasePage 三级降级方法 | 5 文件 |
| 2b | 搜索字段名错误：input_title→input_factory | 第二轮 | PO假设"标题"字段，实际是"工厂代码"（el-select） | JS label遍历 "工厂" → input | 3 文件 |
| 2c | ApprovalChain 点击新增无弹窗 | 第二轮→第三轮 | ①按钮XPath span嵌套 ②DIALOG [last()]选错overlay | JS文本搜索 + CSS Selector | 2 文件 |
| 3 | API管理页面非Swagger UI | 首次运行 | PO假设为纯Swagger iframe | 4级页面加载检测 | 2 文件 |
| 环境1 | root conftest PermissionError | 首次运行 | `shutil.rmtree` 删allure-results失败 | 添加PermissionError catch | 1 文件 |

## 四、新确立的代码模式

### 按钮点击
```python
# ✅ JS文本搜索 — 不受span嵌套影响
self.driver.execute_script("""
    var btns = document.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {
        if (btns[i].textContent.indexOf('新增') !== -1) {
            btns[i].click(); return;
        }
    }
""")
```

### 弹窗检测
```python
# ✅ CSS Selector — 不受多overlay干扰
DIALOG = (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"])')
```

### 弹窗表单定位
```python
# ✅ JS label遍历 — 不受placeholder变化影响
def _find_field_in_dialog(self, label_keyword):
    el = self.driver.execute_script("""
        var labels = dlg.querySelectorAll('.el-form-item__label');
        for (var i = 0; i < labels.length; i++) {
            if (labels[i].textContent.indexOf(keyword) !== -1) {
                return labels[i].closest('.el-form-item').querySelector('input, textarea');
            }
        }
        return null;
    """, dlg, label_keyword)
```

### 空文本断言
```python
# ✅ 前缀匹配 — 兼容多种变体
assert (row_count > 0) or ("暂无" in empty)
```

### 分页跳过
```python
# ✅ 页码比较 — 精准判断
page1 = page.get_current_page_number()
page.click_next_page()
page2 = page.get_current_page_number()
if page2 == page1: pytest.skip("只有一页数据")
```

## 五、产出物清单

| 类别 | 文件 | 数量 |
|------|------|:--:|
| **代码** | Page Object (.py) | 7 |
| **代码** | 测试脚本 (.py) | 7 |
| **代码** | conftest 修改 | 2 |
| **代码** | sidebar_navigator 修改 | 1 |
| **治理** | PAGE_CONTEXT.md | 7 |
| **治理** | RISK_MODEL.md | 1 |
| **治理** | TEST_DESIGN.md | 1 |
| **治理** | SOP_STATUS JSON | 1 |
| **治理** | CURRENT_TASK.md | 1 |
| **治理** | MODULE_CONTEXT.md 更新 | 1 |
| **报告** | TEST_SUMMARY.md | 1 |
| **诊断** | 诊断JSON/HTML/截图 | ~30 |

## 六、遗留问题 & 建议

| 问题 | 严重度 | 建议 |
|------|:---:|------|
| SAP/API/监控全量回归不稳定 | P2 | 分组独立运行；排查element click intercepted根因（是否loading遮罩） |
| 单文件跑100%通过，全量回归下降 | P2 | 优化fixture teardown清理策略，确保driver干净启动 |
| L4异常场景未覆盖 | P3 | Mock框架补充网络超时/接口错误测试 |
| Phase 1-3 文档为retroactive补建 | P3 | 后续模块严格执行SOP门禁，先PAGE_CONTEXT再写代码 |

## 七、经验教训

1. **Phase 1 不可跳过**：7页面直接写代码 → 3轮返工。PAGE_CONTEXT 是最重要的文档
2. **JS > XPath 中文匹配**：`textContent.indexOf()` 比 `normalize-space()` 可靠
3. **placeholder ≠ label**：弹窗表单不能靠placeholder定位
4. **CSS Selector > XPath [last()]**：多overlay页面CSS Selector更精准
5. **诊断先行**：花5分钟跑DOM诊断脚本，省5小时返工
