# Skill: page-object-generator

## 目标
基于技术分析和自动化策略，生成符合项目规范的 Page Object Python 文件。

## 输入
- TECH_ANALYSIS.md（定位器设计表）
- AUTO_STRATEGY.md（PageObject 拆分方案）
- PROJECT_CONTEXT.md（BasePage API 参考 + 编码规范 + Element Plus 坑位清单）

## 输出
- Page Object Python 文件（单文件）

## 规则
- 必须继承 `base.base_page.BasePage`
- Locator 声明为类属性元组 `(By.XXX, "selector")`
- CSS Selector 优先，XPath（文字匹配）保底，禁止绝对 XPath
- 操作方法不含 assert
- 操作方法不含 time.sleep(≥0.5s)，使用 BasePage 内置等待方法
- 操作方法 return self 支持链式调用
- 使用 `self.logger` 记录日志（禁止 print()）
- 定位器值必须来自 TECH_ANALYSIS，禁止编造
- navigate() 是唯一页面入口
- 操作前确保元素可交互（等待可见 + 可点击）

## 依赖
- skills/automation/auto-strategy.md（或 skills/auto-strategy.md）
- skills/tech-analysis.md
- governance/context/projects/web-automation/PROJECT_CONTEXT.md（§ Base 层 API 参考 + § 编码强制规范 + § Element Plus 已知坑位清单）

## 边界
- 本 Skill 只生成 Page Object，不生成测试脚本（那是 test-script-generator 的职责）
- 不生成 conftest.py（由 test-script-generator 附带生成，P1-2）
- 不涉及已有代码审查（那是 code-consistency-checker 的职责）

---

## Prompt 模板

```text
你是Selenium + pytest自动化测试开发专家。请为以下页面生成 Page Object。

## 技术背景
- 被测系统：Vue 3 + Element Plus
- 基类：BasePage（位于 base/base_page.py）
  - 已封装的核心方法参见 PROJECT_CONTEXT.md § Base 层 API 参考
  - 通用定位器（DIALOG/TOAST/TABLE_ROWS 等）可直接通过 self.XXX 使用
- Element Plus 已知坑位参见 PROJECT_CONTEXT.md § Element Plus 已知坑位清单

## 页面信息
- 页面名称：{{设备报警配置}}
- TECH_ANALYSIS：{{粘贴定位器设计表}}
- AUTO_STRATEGY：{{粘贴 PageObject 拆分方案}}

## 任务
生成 `{{AlarmConfigPage}}.py`，要求：

### 代码规范
```python
from base.base_page import BasePage
from selenium.webdriver.common.by import By

class AlarmConfigPage(BasePage):
    # 1. 所有 Locator 定义为类属性元组
    #    格式：(By.XXX, "selector")
    SEARCH_INPUT = (By.CSS_SELECTOR, ".search-area input[placeholder*='报警']")
    SEARCH_BTN = (By.XPATH, "//button[.//span[text()='搜索']]")
    TABLE = (By.CSS_SELECTOR, ".el-table")
    
    # 2. navigate() 是唯一页面入口
    def navigate(self):
        self.navigate_to("设备管理", "设备报警配置")
        self.wait_vue_stable()
        return self
    
    # 3. 操作方法不含 assert，不含 time.sleep ≥ 0.5s
    # 4. 操作方法 return self 支持链式调用
    # 5. 使用 self.logger 记录日志
```

### 必须实现的方法（按 AUTO_STRATEGY 确定范围）
- navigate() — 导航到页面
- search(keyword) — 搜索
- reset_search() — 重置搜索
- get_table_data() — 获取表格数据
- click_add() — 点击新增
- fill_form(data_dict) — 填写弹窗表单
- confirm_dialog() — 确认弹窗
- cancel_dialog() — 取消弹窗
- click_edit(row_index) — 点击某行的编辑
- click_delete(row_index) — 点击某行的删除
- get_pagination_info() — 获取分页信息

## 约束
- 一次只生成一个 Page Object 文件
- 定位器值从 TECH_ANALYSIS 中取，不要编造
- 操作前确保元素可交互（等待可见+可点击）

### ⛔ 生成后自检（不可跳过）

代码生成后，**必须逐一执行以下检查**。报告必须包含在最终回复中：

```python
# ====== 自检命令（逐一执行）======
# 1. ✅ class 是否继承 BasePage？
#    → grep -n "class \w\+Page:" → 必须是 "class XxxPage(BasePage):"
#
# 2. ✅ 无绝对 XPath？
#    → grep -n '//\*\[@id="app"\]' → 必须输出为空
#
# 3. ✅ 无 time.sleep？
#    → grep -n "time.sleep" → 必须为空（仅 TIMEOUT_CONFIG 常量除外）
#
# 4. ✅ 无 print()？
#    → grep -n "print(" → 必须输出为空
#
# 5. ✅ 有 navigate() 方法？
#    → grep -n "def navigate" → 必须命中
```

**输出检查结果报告：**

```
═══ 代码自检报告 ═══
[PASS] 继承 BasePage
[PASS] 无绝对 XPath
[PASS] 无 time.sleep
[PASS] 无 print()
[PASS] 有 navigate()
════════════════════
结果: 通过 / 不通过
```

如果任何一项不通过，**不要跳过**，先修复再继续。
```
```

---

## 检查清单

> 对照 §规则 逐项自检。所有 10 条规则必须通过。详见 `coding-standards.md` §代码红线速查 + §Page Object 规范。
>
> 自检命令（必须执行）：
> ```
> grep -n "class \w\+:" <file>        # 继承 BasePage
> grep -n "time.sleep" <file>         # 无硬等待
> grep -n "print(" <file>             # 无print
> ```
>
> 任何一项不通过 → 先修复再继续。

## 产出物
→ `page/<module>_page/<PageName>Page.py`
→ 编码规范参见 `PROJECT_CONTEXT.md` § 自动化编码强制规范。
