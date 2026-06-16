# UserManagePage 重构任务

> 创建日期：2026-06-11 | 优先级：P0 | 预估工时：4-6h

## 背景

在 2026-06-11 的架构审计中发现，`ZJSN_Test-master526/page/system_page/UserManagePage.py` 与同项目的 `AlarmConfigPage` 使用了**两种完全不同的代码风格**。UserManagePage 未遵循项目编码规范，存在大量禁止模式。

## 问题清单

### P0 — 阻塞性问题

| 编号 | 问题 | 严重度 | 当前代码示例 |
|------|------|--------|-------------|
| UMP-01 | **未继承 BasePage** | Blocker | `class UserManagePage:` → 应为 `class UserManagePage(BasePage):` |
| UMP-02 | **大量 time.sleep() 硬等待** | Blocker | 全文出现 35+ 处 `time.sleep(n)`，均为硬等待 |
| UMP-03 | **使用 print() 替代 logger** | Blocker | `print("[OK] ...")` → 应使用 `self.logger.info(...)` |
| UMP-04 | **绝对 XPath 定位器** | Blocker | `//*[@id="app"]/div/div[2]/div[2]/div[1]/div/ul/li[1]/div/span` — 任何 DOM 层级变化都会导致定位失效 |
| UMP-05 | **直接使用 self.driver.find_element** | Blocker | 全文使用 `self.driver.find_elements(...)` → 应通过 BasePage 方法 |
| UMP-06 | **导航逻辑重复/混乱** | Critical | `navigate_to_user_management()` 和 `click_system_management()` + `click_user_management()` 两套逻辑并存 |
| UMP-07 | **470 行 JS 内联脚本** | Critical | `select_dialog_first_valid_option()` 方法内嵌了 ~190 行 `driver.execute_script()` JS 代码 |

### P1 — 架构问题

| 编号 | 问题 | 建议 |
|------|------|------|
| UMP-08 | **弹窗操作方法过于复杂** | `open_dialog_select()` / `select_dialog_first_valid_option()` / `_click_dialog_option_and_verify()` 等方法的兜底逻辑已超出 Page Object 职责 |
| UMP-09 | **定位器缺少稳定性评级** | 无 A/B/C 分级 |
| UMP-10 | **方法无 return self** | 不支持链式调用 |

## 重构方案

### 第一步：继承 BasePage + 清理定位器（~1.5h）

```python
from base.base_page import BasePage
from selenium.webdriver.common.by import By

class UserManagePage(BasePage):
    """用户管理页面"""
    
    # ── 复用 BasePage 通用定位器 ──
    # DIALOG, DIALOG_SAVE, TOAST, TABLE_ROWS, TOTAL_COUNT, NEXT_PAGE 等已继承
    
    # ── 页面专属定位器 ──
    SEARCH_USERNAME_INPUT = (
        By.CSS_SELECTOR,
        'input[placeholder*="用户名"], input[placeholder*="姓名"], input[placeholder*="手机号"]'
    )
    ADD_USER_BTN = (
        By.XPATH,
        '//button[contains(@class,"el-button")][.//span[contains(text(),"新增") or contains(text(),"新建")]]'
    )
    # ... 其余定位器全部替换为 CSS 优先 + 相对 XPath
```

### 第二步：替换 time.sleep → BasePage 等待方法（~1h）

| 原代码 | 替换为 |
|--------|--------|
| `time.sleep(1)` | `self.wait_vue_stable()` |
| `time.sleep(2)` 等搜索结果 | `self._wait_loading_gone(timeout=5)` |
| `time.sleep(0.5)` 等弹窗 | `self.wait_dialog_open()` |
| `time.sleep(0.3)` 等 Toast | `self.wait_for_toast_text()` |
| `WebDriverWait(self.driver, 5).until(...)` | `self.find_visible(locator, timeout=5)` |

### 第三步：提取弹窗操作为独立类（~1h）

```python
class UserFormDialog(BasePage):
    """用户新增/编辑弹窗"""
    def fill_name(self, name): ...
    def fill_username(self, username): ...
    def select_department(self, dept_name): ...
    def select_role(self, role_name): ...
    def confirm(self): ...
    def cancel(self): ...
```

### 第四步：JS 内联脚本 → ElementPlusHelper 扩展（~1h）

`select_dialog_first_valid_option()` 中的 ~190 行 JS 应提取为 `ElementPlusHelper` 的通用方法 `select_first_valid_option(label_text)`，供所有模块复用。

### 第五步：验证（~0.5h）

- 运行 `pytest script/system/test_user_management.py -v` 确认行为一致
- 用 code-consistency-checker（待建设）逐项检查

## 影响范围

- **直接修改**：`page/system_page/UserManagePage.py`
- **可能影响**：所有引用 UserManagePage 的测试脚本（需确认 fixture 兼容性）
- **依赖方**：`script/system/` 目录下的测试脚本

## 关联任务

- [ ] 建立 `code-consistency-checker` Skill 进行自动化合规检查
- [ ] 在 PROJECT_CONTEXT.md 的"已知坑位"中补充本次重构发现的通用问题
- [ ] 评估其他 Page Object 是否存在同类问题（`SystemLogPage`, `MenuManagePage` 等 system_page 下的文件）

## 完成标准

- [ ] UserManagePage 继承 BasePage
- [ ] 0 处 `time.sleep()` 硬等待
- [ ] 0 处 `print()` 替代 logger
- [ ] 0 处绝对 XPath
- [ ] 所有定位器有 CSS 优先策略
- [ ] 弹窗操作提取为独立 Page Object
- [ ] 现有测试用例全部通过（行为等价）
- [ ] 通过 code-consistency-checker 合规检查
