# AI 辅助测试开发治理规范 — ZJSN 自动化测试项目

> **版本**: 2.1 | **生效日期**: 2026-06-10 | **适用范围**: ZJSN 测试团队全体 AI 模型协作 | **维护人**: AI 开发成员

---

## 一、文档说明

### 1.1 目的

本文档为 ZJSN 自动化测试项目定义 AI 辅助开发的治理规范。在多 AI 模型（Claude 4.x、GPT-4o / Codex、DeepSeek、Cursor 等）协作环境下，确保：

- 项目架构稳定，不会被 AI 误解后无序修改
- 所有生成的 Page Object、测试脚本、Fixture 风格一致
- 修改前有完整的 Change Plan，可审计、可回溯
- 敏感信息（凭证、环境 URL）永不进入 AI 上下文或生成产物

### 1.2 适用范围

本文档适用于以下所有开发行为：

| 行为 | 适用模型 | 要求 |
|------|---------|------|
| 新增 Page Object 文件 |  | 遵循第四章 PageObject 规范 |
| 新增测试用例脚本 |          | 遵循第五章测试脚本规范 |
| 修改 base/ 层代码 |  | 必须先出 Change Plan |
| 修改 conftest.py / pytest.ini |  | 必须先出 Change Plan |
| 生成测试数据文件 | 任意模型 | 遵循 6.3 节 Change Plan 要求 |
| 调试失败用例 |  | 遵循第七章排查流程 |

### 1.3 核心原则

```
原则 1：架构稳定优先 — 不因 AI 建议而随意改变 base/ page/ script/ config/ 层级
原则 2：Change Plan 前置 — 任何 >2 文件或 >50 行的修改必须先输出计划
原则 3：风格继承 — 新代码必须读同级已有文件，模仿其命名、注释密度、异常处理方式
原则 4：凭证零泄露 — 密码/Token/URL 永不出现在 AI 生成的代码或文档中
原则 5：可审计 — 每次 AI 协作的 Prompt 摘要 + 产出摘要写入 Git 提交信息
原则 6：数据即用即清 — 每条用例产生的脏数据必须在用例执行完毕后立即清除，不遗留测试痕迹到生产或测试环境
```

---

## 二、测试项目架构规范

### 2.1 分层架构（不可变更）

```
ZJSN_Test-master526/
├── config/                  # 配置层 — 环境感知，凭证外置
│   ├── __init__.py          #   入口：按 ENV 加载对应环境
│   ├── base.py              #   公共：BROWSER_CONFIG / TIMEOUT_CONFIG / LOGGING_CONFIG
│   ├── dev.py               #   开发环境
│   ├── test.py              #   测试环境
│   └── staging.py           #   预发环境
│
├── base/                    # 基础封装层 — 框架级代码，禁止业务逻辑
│   ├── base_page.py         #   Page Object 基类（Vue/Element Plus 等待策略）
│   ├── browser_driver.py    #   驱动生命周期 + ensure_logged_in()
│   ├── element_plus_helper.py # Element Plus 组件专用操作
│   └── sidebar_navigator.py   # 侧边栏菜单导航
│
├── page/                    # 页面对象层 — 按业务模块分包
│   ├── system_page/         #   系统管理 (15 个 Page)
│   ├── person_page/         #   人员管理 (7 个 Page)
│   ├── sales_page/          #   销售管理 (4 个 Page)
│   └── lab_page/            #   实验室 (1 个 Page)
│
├── script/                  # 测试脚本层 — 按业务模块分包
│   ├── conftest.py          #   script 级共享 fixture
│   ├── system/              #   系统管理测试 (15 个 test_*.py)
│   ├── person/              #   人员管理测试 (7 个 test_*.py)
│   ├── sales/               #   销售管理测试 (19 个 test_*.py)
│   └── lab/                 #   实验室测试 (1 个 test_*.py)
│
├── data/                    # 测试数据层
│   ├── fixtures/            #   静态数据：YAML / JSON
│   └── test_files/          #   上传测试用的文件
│
├── tools/                   # 辅助工具（非测试代码）
│   ├── debug/               #   调试脚本
│   ├── fix/                 #   修复脚本
│   ├── inspect/             #   页面探查脚本
│   ├── report/              #   Excel 报告生成
│   └── seed/                #   测试数据造数
│
├── conftest.py              # 根级：路径注入 + 日志 + 失败截图 hook
├── pytest.ini               # pytest 执行配置 + markers
├── requirements.txt         # 依赖清单
├── Jenkinsfile              # CI 流水线
├── .env                     # 本地凭证（不提交 Git）
└── .env.example             # 凭证模板（提交 Git）
```

### 2.2 层级依赖规则

```
┌──────────┐
│  script/ │  → 依赖 page/ + base/ + conftest.py + config/
├──────────┤
│  page/   │  → 依赖 base/ + config/（仅超时配置）
├──────────┤
│  base/   │  → 依赖 config/（仅配置读取）
├──────────┤
│  config/ │  → 无内部依赖
├──────────┤
│  data/   │  → 无内部依赖（纯数据文件）
└──────────┘
```

**严格禁止的依赖方向**：
- `base/` 不能引入 `page/` 的任何符号
- `config/` 不能引入任何业务代码
- `page/` 不能引入 `script/` 的 fixture 或 mark
- `data/` 不能包含 Python 业务逻辑（仅数据文件 + `__init__.py`）

### 2.3 Page Object 模式规范

#### 2.3.1 继承关系

```
BasePage（base/base_page.py）          ← 所有 Page Object 的基类
  ├── 通用操作方法（click/input_text/get_text）
  ├── Element Plus 弹窗/Toast/表格操作
  ├── Vue 异步等待策略
  └── 诊断工具（save_debug_snapshot / _diagnose_element）
```

#### 2.3.2 Page Object 文件结构模板

每个 `XxxPage.py` 必须按以下格式组织：

```python
"""模块 — 页面描述（一行）"""
# （可选）详细的 Vue/Element Plus 注意事项
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class XxxPage(BasePage):
    """页面操作类"""
    
    # ==================================================================
    #  Locators（类属性，按功能分组）
    # ==================================================================
    # ── 搜索区 ──
    SEARCH_INPUT = (By.CSS_SELECTOR, ".search-input input")
    SEARCH_BUTTON = (By.XPATH, "//button[.//span[text()='搜索']]")
    
    # ── 表格区 ──
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")
    
    # ── 弹窗区 ──
    DIALOG_INPUT = (By.CSS_SELECTOR, ".el-dialog input[placeholder*='名称']")
    
    # ==================================================================
    #  导航
    # ==================================================================
    def navigate(self):
        """导航到本页面（唯一入口）"""
        self.navigate_to("一级菜单名", "二级菜单名")
        self.wait_page_ready()
        return self
    
    # ==================================================================
    #  业务操作（方法名 = 动词_对象，不含 assert）
    # ==================================================================
    def input_keyword(self, text):
        """输入搜索关键词"""
        self.input_text(self.SEARCH_INPUT, text)
        return self
    
    def click_search(self):
        """点击搜索按钮"""
        self.click_search_button()   # 继承自 BasePage
        return self
```

#### 2.3.3 Locator 编写优先级（强制）

```
1️⃣  文本组合 XPath                ← 最稳，按钮/链接首选
    //button[.//span[normalize-space(.)="搜索"]]
    //tr[contains(@class,"el-table__row")]//td[contains(.,"关键词")]

2️⃣  placeholder / label 属性      ← input/select 首选
    (By.CSS_SELECTOR, 'input[placeholder*="合同编号"]')

3️⃣  稳定 CSS class               ← 全局样式或组件固定 class
    (By.CSS_SELECTOR, '.el-dialog__title')

4️⃣  绝对 XPath（精确路径）         ← 兜底，避免动态 index
    //*[@id="app"]/div/...（仅当其他方式均失败时使用）

❌ 禁止使用：
    - data-v-xxxx 动态属性
    - nth-child(n) 硬编码索引（除非表格列位置永远固定）
    - //div[3]/div[2]/... 未经验证的路径
```

#### 2.3.4 Page Object 禁止清单

- [ ] **禁止在 Page 内写 `assert`** — 断言在 `test_*.py` 中完成
- [ ] **禁止在 Page 内直接 `time.sleep(n)`** — 使用 `wait_vue_stable()` / `wait_overlay_gone()`
- [ ] **禁止将 `driver` 暴露给测试用例** — 所有操作通过 Page 方法封装
- [ ] **禁止在 Page 内处理测试数据生成逻辑** — 应在 `conftest.py` fixture 或 `data/` 中处理
- [ ] **禁止从 Page 导入 `pytest` / `allure`** — Page 是纯业务操作层

---

## 三、目录与文件命名规范

### 3.1 已有目录（不可变更）

| 目录 | 用途 | 不可变更 |
|------|------|---------|
| `base/` | 框架基类 | ✅ 仅允许修改已有文件，不新增目录 |
| `page/{module}_page/` | 页面对象 | 遵循已有命名模式 |
| `script/{module}/` | 测试脚本 | 遵循已有命名模式 |
| `config/` | 环境配置 | 仅允许新增环境文件 |
| `data/fixtures/` | 测试数据 | 自由新增 YAML/JSON |
| `tools/` | 辅助工具 | 自由新增，按子目录归类 |

### 3.2 文件命名规则

| 文件类型 | 命名规则 | 正确示例 | 错误示例 |
|---------|---------|---------|---------|
| Page Object | `{业务英文}PagetName.py`（大驼峰） | `ContractPage.py`、`UserManagePage.py` | `contract_page.py`、`Contract.py` |
| 测试脚本 | `test_{业务英文小写}.py` | `test_contract_search.py` | `ContractSearchTest.py` |
| 测试数据 | `{模块}_{实体}_snake.yaml` | `sales_contract.yaml` | `SalesContract.yaml` |
| conftest | `conftest.py`（固定名称） | `conftest.py` | `conftest_sales.py` |
| 工具脚本 | `{动词}_{对象}_snake.py` | `generate_excel.py`、`debug_sidebar.py` | `Excel.py` |
| bug 分析 | `{模块}_禅道Bug分析.xlsx` | `合同管理_禅道Bug分析.xlsx` | — |

### 3.3 模块缩写前缀（用于用例 ID）

用例编号格式：`{模块缩写}-{类型缩写}-{序号}`

| 模块 | 缩写 | 示例 |
|------|------|------|
| 字典管理 | DICT | `DICT-FUNC-001` |
| 用户管理 | USER | `USER-FUNC-001` |
| 角色管理 | ROLE | `ROLE-FUNC-001` |
| 组织管理 | ORG | `ORG-FUNC-001` |
| 菜单管理 | MENU | `MENU-FUNC-001` |
| 合同管理 | CT | `CT-FUNC-001` |
| 客户管理 | CUST | `CUST-FUNC-001` |
| 销售订单 | SO | `SO-FUNC-001` |
| 日报表 | DR | `DR-FUNC-001` |
| 课程管理 | COURSE | `COURSE-FUNC-001` |
| 考试管理 | EXAM | `EXAM-FUNC-001` |

用例类型缩写：

| 类型 | 缩写 |
|------|------|
| 功能测试 | FUNC |
| UI 测试 | UI |
| 边界值测试 | BDY |
| 异常测试 | EXC |
| 权限测试 | PERM |
| 数据校验 | DAT |
| 接口联动 | INT |
| 重复提交 | DUP |

---

## 四、Selenium + Pytest 测试脚本开发规范

### 4.1 测试文件结构模板

```python
"""模块名 — 测试范围描述

测试点：
  - {用例ID}: 场景简述
  - {用例ID}: 场景简述

Vue/Element Plus 注意：
  - {组件} 通过 Teleport 挂载到 body
  - {操作} 后表格异步加载，需等待遮罩消失
"""
import logging
import pytest
import allure

from page.{module}_page.{PageName} import {PageName}Page

logger = logging.getLogger(__name__)


class Test{业务名}:
    """{模块} — {测试范围}"""

    # ── Allure 元数据自动注入 ──
    @pytest.fixture(autouse=True)
    def _allure_meta(self, request):
        doc = (__import__("inspect").getdoc(request.function) or "").strip()
        title = doc.replace(":", " ").strip() if doc else request.function.__name__
        try:
            allure.dynamic.title(title)
            if doc:
                allure.dynamic.description(doc)
        except Exception:
            pass
        yield

    # ==================================================================
    #  {用例ID}: {标题}
    # ==================================================================
    @pytest.mark.smoke
    @allure.epic("{史诗}")
    @allure.feature("{特性}")
    @allure.story("{用户故事}")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_{动词}_{对象}_{条件}(self, {page}_page, {module}_test_data):
        """{用例ID}: {一行描述} — {预期结果简述}"""
        page = {page}_page
        data = {module}_test_data["{key}"]

        with allure.step("步骤1: {描述}"):
            page.{操作}()
        
        with allure.step("步骤2: {描述}"):
            actual = page.{获取结果}()
        
        with allure.step("步骤3: 断言"):
            assert actual == data["expected"], f"预期: {data['expected']}, 实际: {actual}"
```

### 4.2 Fixture 使用规范

#### 4.2.1 Fixture 选择决策树

```
需要独立浏览器？
├── 是（增删改类用例） → 使用 module 级 driver_setup
│   └── 参数: driver_setup（来自模块 conftest.py）
└── 否（只读/查询用例）→ 可使用 session 级
    └── 参数: session_logged_in_browser

每个测试函数需要干净的页面状态？
├── 是 → 使用 function 级 Page Object fixture
│   └── 参数: {page}_page
└── 否 → 直接使用 driver_setup + 手动构造 Page
```

#### 4.2.2 已有 Fixture 速查表

| Fixture 名 | Scope | 来源 | 用途 |
|-----------|-------|------|------|
| `driver_setup` | module | `script/{module}/conftest.py` | 自动登录 + 导航的驱动 |
| `{page}_page` | function | `script/{module}/conftest.py` | 已复位的 Page Object |
| `{module}_test_data` | session | `script/{module}/conftest.py` | 从 YAML 加载的测试数据 |
| `sales_test_data` | module | `script/sales/conftest.py` | 销售订单预取数据 |

#### 4.2.3 新增 Fixture 规则

```python
# ✅ 正确：在模块 conftest.py 中新增
@pytest.fixture(scope="module")
def new_fixture(driver_setup):
    """描述用途"""
    ...

# ❌ 错误：在 test_*.py 中定义 module 级 driver fixture
# 会导致重复启动浏览器，增加执行时间
```

### 4.3 Allure 注解规范（强制）

每个测试函数必须包含：

```python
@allure.epic("{四大史诗之一}")         # 销售管理 | 人员管理 | 系统管理 | 实验室
@allure.feature("{模块名}")          # 合同管理 | 用户管理 | 角色管理 ...
@allure.story("{用户故事}")          # 合同搜索 | 用户新增 | 角色分配 ...
@allure.severity(allure.severity_level.{等级})  # BLOCKER / CRITICAL / NORMAL / MINOR / TRIVIAL
```

### 4.4 pytest.mark 使用规范

| mark | 使用条件 | 示例 |
|------|---------|------|
| `smoke` | 核心正向流程，<15min | 登录、基础 CRUD、核心搜索 |
| `regression` | 全量回归 | 所有用例默认带上 |
| `destructive` | 会创建/修改/删除数据的用例 | 新增、编辑、删除 |
| `slow` | 预计 >60s 的用例 | 文件上传、大数据分页遍历 |
| `flaky` | 已知因环境/网络不稳定的用例 | 依赖第三方 API 的场景 |
| `validation` | 表单校验类 | 必填为空、格式校验 |
| `boundary` | 边界值 | 最大长度、0 值、负值 |
| `permission` | 权限相关 | 无权限用户访问页面 |

### 4.5 断言规范

```python
# ✅ 正确：包含清晰的错误消息
assert actual_count >= expected_min, \
    f"搜索结果数量不足：预期≥{expected_min}，实际={actual_count}"

# ✅ 正确：toast 消息校验
toast = page.get_toast()
assert "成功" in toast, f"期望包含"成功"，实际toast: {toast}"

# ❌ 错误：裸断言，失败时无法定位
assert result

# ❌ 错误：在 Page Object 方法内写 assert
def click_save_and_check(self):
    self.click_save()
    toast = self.get_toast()
    assert "成功" in toast  # ← 不应在 Page 内断言
```

### 4.7 数据清理规范（强制）

每条增删改测试用例产生的数据必须在用例执行完毕后立即清除。

#### 4.7.1 清理时机

```
用例执行前 → 记录初始状态（计数/快照）
用例执行中 → 创建/修改数据
用例执行后 → 清理脏数据（teardown 阶段）
                 │
                 ├── 用例成功 → 清理
                 └── 用例失败 → 清理（必须！finalizer 确保即使断言失败也执行）
```

#### 4.7.2 清理方式优先级

```
1️⃣ API 删除               ← 最优先，直接调用后端接口批量删除
   page.delete_by_api(id)

2️⃣ UI 逐条删除            ← API 不可用时，通过页面操作删除
   page.click_delete(id)
   page.confirm_delete()

3️⃣ 数据库直删              ← 兜底，仅用于自动化测试专用数据库
   sql: DELETE FROM xxx WHERE name LIKE 'test_%'

❌ 禁止：
   - 依赖后续用例覆盖脏数据（如：修改操作复用前一条创建的数据）
   - 不清除，留给手工清理
   - 在 teardown 中 time.sleep 等待删除生效（应使用显式等待）
```

#### 4.7.3 代码模板

```python
class TestXxx:
    """模块测试 — 所有增删改用例必须清理数据"""

    # 存放本模块测试中创建的待清理 ID 列表
    _cleanup_ids: list = []

    @pytest.fixture(autouse=True)
    def _data_cleanup(self, request):
        """每条用例执行后的自动清理"""
        yield
        if self._cleanup_ids:
            logger.info(f"清理脏数据: {self._cleanup_ids}")
            try:
                for tid in self._cleanup_ids:
                    page.delete_by_api(tid)
                logger.info(f"已清理 {len(self._cleanup_ids)} 条脏数据")
            except Exception as e:
                logger.warning(f"清理脏数据失败: {e}")
            finally:
                self._cleanup_ids.clear()
```

#### 4.7.4 测试数据命名规范（辅助清理）

所有自动化测试创建的**名称/编码**必须包含可识别前缀，便于批量检索和清理：

| 字段 | 前缀规则 | 示例 | 清理查询 |
|------|---------|------|---------|
| 名称 | `test_` 开头 | `test_字典名称_001` | `WHERE name LIKE 'test_%'` |
| 编码 | 含 `TEST` | `TEST_DICT_001` | `WHERE code LIKE '%TEST%'` |
| 备注 | 含 `[AUTO]` | `自动化测试创建[AUTO]` | `WHERE remark LIKE '%[AUTO]%'` |

#### 4.7.5 例外规则

| 场景 | 允许不清除 | 原因 |
|------|-----------|------|
| 只读查询用例 | ✅ | 未产生任何脏数据 |
| 测试环境专用账号的初始化数据 | ✅ | 一次性创建，后续测试依赖 |
| 报表/统计分析类数据（仅追加） | ⚠️ 需标注 | 清理成本 > 残留影响时 |

> **违反后果**：CI 流水线中检测到残留 `test_` 前缀数据超过阈值（当前：50 条）将标记为构建警告。

### 4.6 等待规范

```python
# ✅ 正确：使用显式等待
page.wait_vue_stable()          # Vue 异步渲染完成
page.wait_overlay_gone()        # 遮罩层消失
page.find_visible(locator, 10)  # 等待特定元素可见

# ❌ 错误：无条件 time.sleep
time.sleep(3)                   # 不可靠！环境差异会导致随机失败
time.sleep(1)                   # 同上

# ✅ 唯一允许的 time.sleep 用法：微等待（使用配置常量）
from config import TIMEOUT_CONFIG
time.sleep(TIMEOUT_CONFIG["micro_wait"])   # 0.2s，v-model 绑定同步
```

---

## 五、AI 模型使用规范

### 5.1 模型任务分工

| 任务 | 推荐模型 | 原因 |
|------|---------|------|
| 新增 Page Object（新模块） | Claude Opus 4.x | 需要理解 Vue 组件结构 + 复用基类能力 |
| 新增测试用例脚本 | Claude Sonnet 4.x | 需要模仿已有用例风格 |
| 修改 base/ 层代码 | Claude Opus 4.x | 框架级修改不可出错 |
| 修改 conftest.py | Claude Opus 4.x | 影响面大 |
| 生成测试数据 YAML | 任意模型 | 数据结构简单 |
| 生成 Excel 测试报告 | Claude Haiku 4.x | 格式化工单 |
| 修复定位器失效 | Claude Sonnet 4.x | 需诊断 DOM 变化 |
| 调试失败用例 | Claude Sonnet 4.x | 需分析截图+日志+HTML |
| 代码格式化 / import 整理 | Cursor | 机械操作 |
| 新增 tools/ 脚本 | 任意模型 | 不影响核心框架 |

### 5.2 系统提示模板

#### 5.2.1 Claude Code（命令行模式）

在项目根目录 `.claude/settings.json` 中已配置自动加载本规范，每次会话开始时 AI 会读取 `docs/AI辅助测试开发治理规范.md`。如需手动注入系统提示：

```markdown
你是 ZJSN 自动化测试项目的 AI 开发成员。

技术栈：Python 3.x + Selenium 4.x + pytest 7.x + Allure 2.x
被测系统：Vue 3 + Element Plus + SSM 后端

项目规范参见: docs/AI辅助测试开发治理规范.md

核心约束：
1. 修改 >2 个文件或 >50 行代码时，必须先输出 Change Plan
2. base/ 层代码仅在明确授权时修改
3. Page Object 不写 assert，test_*.py 不写 locator
4. 新代码必须模仿同目录已有文件的风格
5. 生成的代码中不得包含任何密码/Token/真实 URL
```

#### 5.2.2 Cursor（IDE 内嵌模式）

在 `.cursorrules` 中补充：

```
你是 ZJSN 测试项目的开发助手。
- 修改前读 README.md 和 docs/AI辅助测试开发治理规范.md
- 不能在 Page Object 中写 assert
- 不能用 time.sleep 代替显式等待
- 新测试用例必须包含 @allure 注解
- 不能修改 base/ base_page.py browser_driver.py conftest.py pytest.ini
```

#### 5.2.3 DeepSeek / GPT-4o（Web 界面模式）

每次新会话开始时，粘贴以下上下文块：

```
【ZJSN 项目上下文 — 请在回复前阅读】

项目: 鞍集涂源管理系统 自动化测试
架构: config/ → base/ → page/ → script/
      配置层  → 框架层→ 页面层→ 测试层

核心文件:
- base/base_page.py: Page Object 基类，提供 click/input_text/get_text + Vue 等待
- base/browser_driver.py: 驱动管理 + ensure_logged_in()
- config/__init__.py: 按 ENV 加载多环境配置，优先级 .env > env file > default

关键规则:
1. Page Object 继承 BasePage，不写 assert
2. 测试脚本在 script/{module}/test_*.py，如需修改 >2 文件先告诉我计划
3. Locator 优先级: 文本XPath > placeholder > CSS class > 绝对路径
4. 不要建议改变 base/ config/ conftest.py 的架构
5. 不要输出任何包含密码的代码

我的问题:
[在此输入任务描述]
```

### 5.3 模型切换时的上下文传递

当从 Claude 切换到 Cursor 或其他模型时，必须传递以下最小上下文：

```markdown
## 上次会话摘要（由 Claude 生成）

### 已完成
- 文件: {列表}
- 改动量: {行数概览}

### 当前阻塞
- {问题描述}

### 未完成
- {待办列表}

### 关键决策
- {为什么这样做，而非那样做}
```

此摘要由 AI 在每次会话结束时自动生成，提交到 Git 的 Extended Commit Message 中。

---

## 六、Change Plan 规范

### 6.1 何时必须出具 Change Plan

以下任一条件触发：

| 条件 | 说明 |
|------|------|
| 修改文件数 > 2 | 不包括纯格式调整 |
| 新增/删除行数 > 50 | 单文件或累计 |
| 涉及 base/ 目录 | 无论改动大小 |
| 涉及 conftest.py / pytest.ini | 无论改动大小 |
| 新增 Page Object 文件 | 需说明类结构 |
| 修改 fixture scope 或签名 | 影响面大 |

### 6.2 Change Plan 模板

```markdown
## Change Plan: {简短标题}

### 背景
{为什么需要这个改动}

### 影响范围

| 文件 | 操作 | 行数概算 |
|------|------|---------|
| page/sales_page/ContractPage.py | 修改 | +30 / -5 |
| script/sales/test_contract_search.py | 修改 | +15 / -3 |

### 风险评估

| 风险 | 概率 | 缓解措施 |
|------|------|---------|
| 现有用例因 locator 变更失败 | 中 | 先在本地跑一次 smoke |

### 预期结果
{改动后的行为}

### 回滚方案
{如何恢复到改动前}
```

### 6.3 生成新测试用例的 Change Plan 模板

```markdown
## Change Plan: 新增 {模块} 测试用例

### 要测试的页面
- page/{module}_page/{PageName}.py

### 要覆盖的用例

| 用例ID | 标题 | 优先级 | 类型 |
|--------|------|--------|------|
| XXX-FUNC-001 | {描述} | P0 | 功能测试 |
| XXX-BDY-001 | {描述} | P1 | 边界值 |

### 会用到的已有 fixture
- driver_setup（module 级，conftest 已定义）
- {page}_page（需在 conftest 中新增）

### 测试数据
- 来源: data/fixtures/{module}_{entity}.yaml
- 是否需要新增: {是/否}

### 新增文件
- script/{module}/test_{entity}.py
- data/fixtures/{module}_{entity}.yaml（如需要）
```

### 6.4 Change Plan 输出时机

```
用户提出需求
    │
    ├── 改动 ≤ 2 文件 且 ≤ 50 行 → 直接写代码
    │
    └── 超出范围 → 输出 Change Plan → 等待用户确认 → 开始写代码
```

---

## 七、项目护栏（Guardrails）

### 7.1 不可修改的文件（需架构评审批准）

| 文件 | 原因 |
|------|------|
| `base/base_page.py` | 所有 Page Object 的基类，改动影响全局 |
| `base/browser_driver.py` | 驱动生命周期，改动影响所有模块 |
| `conftest.py`（根级） | 失败截图 hook 影响全部用例 |
| `pytest.ini` | 执行参数、markers 影响 CI |
| `config/__init__.py` | 环境加载逻辑影响全部配置读取 |
| `AUTOMATION_ARCHITECTURE.md` | 架构定义文档，仅架构评审后更新 |

### 7.2 不可修改的目录结构

```
ZJSN_Test-master526/
├── base/        ← 框架层，不新增子目录
├── page/        ← 可按 {module}_page/ 模式新增
├── script/      ← 可按 {module}/ 模式新增
├── config/      ← 仅可新增环境文件 (xxx.py)
├── data/        ← 可新增子目录
└── tools/       ← 可新增子目录
```

### 7.3 代码级护栏

| 禁区 | 说明 |
|------|------|
| 不在 Page Object 中写 `assert` | 断言在 test_*.py |
| 不在 test_*.py 中定义 locator | locator 在 Page Object |
| 不直接实例化 `webdriver.Chrome()` | 通过 `BaseDriver` |
| 不硬编码 URL / 密码 | 从 `config` 读取 |
| 不使用 `implicitly_wait` | 项目规范：implicit_wait=0，统一显式等待 |
| 不修改 fixture scope 为 `session`（增删改模块） | session 共享导致数据污染 |
| 不在 `page/` 中使用 `@pytest.fixture` | fixture 在 `conftest.py` |
| 不在 `base/` 中使用 `allure` | 框架层与报告层解耦 |

### 7.4 AI 生成产物的自动检查清单

AI 每次生成代码后，必须自查：

```
□ 有没有包含密码/Token？
□ Page Object 有没有 assert？
□ 有没有裸 time.sleep(N>0.5)？
□ 有没有 import config（不该 import 的模块）？
□ 有没有直接 webdriver.Chrome()？
□ 新增的 fixture 名字是否与已有 fixture 冲突？
□ 用例有没有 @allure.epic / @allure.feature / @allure.story / @allure.severity？
□ 有没有从 test_*.py import Page Object 到其他 test_*.py？
```

---

## 八、审计与追踪

### 8.1 Git 提交信息规范

```
{类型}({模块}): {简短描述}

{AI 模型} | Prompt 摘要: {一句话}
{变更详情的要点列表}

Co-Authored-By: {模型名} <noreply@anthropic.com>
```

示例：

```
feat(sales): 新增合同搜索组合条件测试

Claude Sonnet 4.6 | Prompt: "基于 ContractPage 已有方法，生成多条件组合查询
的测试用例，覆盖合同编号+客户名称+状态下拉的三条件 AND 搜索"

- 新增 test_contract_combined_search.py（TC_S09-TC_S12）
- 新增 data/fixtures/sales_contract.yaml 中 combined_search 数据节点

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

### 8.2 会话日志

在 `.workbuddy/` 或项目约定的日志目录中，记录每次 AI 协作会话：

```yaml
# session_log.yaml（可选，推荐每个模块一个文件）
- date: 2026-06-05
  model: claude-sonnet-4-6
  task: 新增合同搜索测试
  files_changed:
    - script/sales/test_contract_search.py
  change_plan: docs/change_plans/2026-06-05_contract_search.md
  outcome: PASS（本地 smoke 全绿）
```

### 8.3 文档同步要求

当以下变更发生时，必须同步更新本规范文档中的对应章节：

| 变更 | 更新章节 |
|------|---------|
| 新增模块缩写 | 第三章 3.3 缩写前缀表 |
| 新增 fixture | 第四章 4.2.2 fixture 速查表 |
| 新增 pytest marker | 第四章 4.4 mark 使用表 |
| 架构层级变化 | 第二章 2.1 + 架构文档 |

---

## 九、文档维护

### 9.1 维护责任人

| 文档 | 维护人 | 更新频率 |
|------|--------|---------|
| `AI辅助测试开发治理规范.md`（本文档） | AI 开发成员 | 每次架构变更时 |
| `AUTOMATION_ARCHITECTURE.md` | 架构评审人 | 每次架构变更后 |
| `REFACTOR_PLAN.md` | AI 开发成员 | 每个 P0/P1 完成后 |
| `Prompt/TestEngineer.md` | 测试开发实习生 | 发现新高频场景时 |
| `Prompt/workflow.md` | 测试开发实习生 | 流程优化时 |

### 9.2 版本管理

本文档版本号规则：

- 大版本（1.0 → 2.0）：架构层级变更、新增强制规范
- 小版本（1.0 → 1.1）：补充示例、修正错误、小节增补

每次更新需在文档顶部 `版本` 字段递增，并在 Git 提交信息中注明 `docs: 治理规范 v1.0 → v1.1`。

### 9.3 反馈渠道

AI 在使用本文档过程中，如果发现规范不合理（如某条规则在实际任务中反复导致问题），需在会话结束时输出：

```markdown
## 规范反馈

### 规范条款
{章节号} {条款内容}

### 遇到的问题
{具体场景}

### 修订建议
{建议的新表述}
```

此反馈由人类维护人评估后决定是否修订。

---

## 十、示例模板

### 10.1 测试用例表模板

> 源自 `TestIntern_library/testcases/TEMPLATE--测试用例表.md`

```markdown
# [模块名称]--测试用例表

> **生成日期:** [YYYY-MM-DD] | **用例总数:** [N] | **P0:** [n] | **P1:** [n] | **P2:** [n]

| 用例ID | 用例标题 | 所属模块 | 优先级 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 | 实际结果 |
|--------|---------|---------|--------|---------|---------|---------|---------|---------|
| **功能测试(X条)** | | | | | | | | |
| XXX-FUNC-001 | [模块名称]-功能测试-[操作] | [模块名称] | P0/P1/P2 | [前置条件] | 1. [步骤1]<br>2. [步骤2]<br>3. [步骤3] | [数据项: 值] | [执行状态] [预期校验点] | 待验证 |
| **UI测试(X条)** | | | | | | | | |
| XXX-UI-001 | [模块名称]-UI测试-[操作] | [模块名称] | P0/P1/P2 | [前置条件] | 1. [步骤1]<br>2. [步骤2] | — | [执行状态] [预期校验点] | 待验证 |
| **边界值测试(X条)** | | | | | | | | |
| XXX-BDY-001 | [模块名称]-边界值测试-[操作] | [模块名称] | P0/P1/P2 | [前置条件] | 1. [步骤1]<br>2. [步骤2] | [数据项: 值] | [执行状态] [预期校验点] | 待验证 |
| **异常测试(X条)** | | | | | | | | |
| XXX-EXC-001 | [模块名称]-异常测试-[操作] | [模块名称] | P0/P1/P2 | [前置条件] | 1. [步骤1]<br>2. [步骤2] | [数据项: 值] | [执行状态] [预期校验点] | 待验证 |
| **权限测试(X条)** | | | | | | | | |
| XXX-PERM-001 | [模块名称]-权限测试-[操作] | [模块名称] | P0/P1/P2 | [前置条件] | 1. [步骤1]<br>2. [步骤2] | — | [执行状态] [预期校验点] | 待验证 |
| **数据校验测试(X条)** | | | | | | | | |
| XXX-DAT-001 | [模块名称]-数据校验测试-[操作] | [模块名称] | P0/P1/P2 | [前置条件] | 1. [步骤1]<br>2. [步骤2] | [数据项: 值] | [执行状态] [预期校验点] | 待验证 |
| **接口联动测试(X条)** | | | | | | | | |
| XXX-INT-001 | [模块名称]-接口联动测试-[操作] | [模块名称] | P0/P1/P2 | [前置条件] | 1. [步骤1]<br>2. [步骤2] | [数据项: 值] | [执行状态] [预期校验点] | 待验证 |
| **重复提交测试(X条)** | | | | | | | | |
| XXX-DUP-001 | [模块名称]-重复提交测试-[操作] | [模块名称] | P0/P1/P2 | [前置条件] | 1. [步骤1]<br>2. [步骤2] | [数据项: 值] | [执行状态] [预期校验点] | 待验证 |

---

> **统计:** 合计[N]条 | P0:[n] | P1:[n] | P2:[n] | PASS:[n] | 手工PASS[n] | FAIL:[n] | BLOCKED:[n] | SKIP/NOT RUN[n]

**测试状态包含**：

- PASS
- 手工PASS[n]
- FAIL
- BLOCKED
- SKIP/NOT RUN
```

### 10.2 测试用例填写示例（字典管理 — 新增字典）

```markdown
# 字典管理--测试用例表

> **生成日期:** 2026-06-05 | **用例总数:** 42 | **P0:** 8 | **P1:** 18 | **P2:** 16

| 用例ID | 用例标题 | 所属模块 | 优先级 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 | 实际结果 |
|--------|---------|---------|--------|---------|---------|---------|---------|---------|
| **功能测试(8条)** | | | | | | | | |
| DICT-FUNC-001 | 字典管理-功能测试-新增字典-必填项完整 | 字典管理 | P0 | 1. 已登录系统<br>2. 拥有字典管理权限<br>3. 进入字典管理页面 | 1. 点击新增按钮<br>2. 填写字典名称<br>3. 填写字典编码<br>4. 选择状态为启用<br>5. 点击确定 | 字典名称: test_dict_001<br>字典编码: DICT001 | 弹出"新增成功"提示<br>列表刷新后包含新增的字典 | 待验证 |
| DICT-FUNC-002 | 字典管理-功能测试-新增字典-字典名称为空 | 字典管理 | P0 | 1. 已登录系统<br>2. 拥有字典管理权限<br>3. 进入字典管理页面 | 1. 点击新增按钮<br>2. 字典名称留空<br>3. 填写字典编码<br>4. 点击确定 | 字典编码: DICT002 | 字典名称输入框标红<br>提示"请输入字典名称"<br>弹窗不关闭 | 待验证 |
| **边界值测试(6条)** | | | | | | | | |
| DICT-BDY-001 | 字典管理-边界值测试-字典名称最大长度 | 字典管理 | P1 | 1. 已登录系统<br>2. 拥有字典管理权限<br>3. 进入字典管理页面 | 1. 点击新增按钮<br>2. 输入最大长度字典名称<br>3. 填写字典编码<br>4. 点击确定 | 字典名称: 50字符中英文混合<br>字典编码: BDY001 | 系统接受输入<br>新增成功 | 待验证 |
```

### 10.3 Page Object 模板（继承 BasePage）

```python
"""合同管理页面操作类

继承 BasePage，使用 CSS_SELECTOR 优先的定位策略。
Vue/Element Plus 注意：
  - 合同状态下拉通过 Teleport 挂载到 body
  - 搜索后表格异步加载，需等待遮罩消失
"""
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class ContractPage(BasePage):
    """合同管理 — 列表页操作"""

    # ==================================================================
    #  Locators: 搜索区
    # ==================================================================
    SEARCH_INPUT_CONTRACT_NO = (
        By.CSS_SELECTOR,
        '.search-form input[placeholder*="合同编号"]',
    )
    SEARCH_INPUT_CUSTOMER = (
        By.CSS_SELECTOR,
        '.search-form input[placeholder*="客户"]',
    )
    SEARCH_BUTTON = (
        By.XPATH,
        '//button[contains(@class,"el-button--primary")]'
        '//span[contains(normalize-space(.),"搜索")]/parent::button',
    )
    RESET_BUTTON = (
        By.XPATH,
        '//button[not(contains(@class,"el-button--primary"))]'
        '//span[contains(normalize-space(.),"重置")]/parent::button',
    )

    # ==================================================================
    #  Locators: 表格区
    # ==================================================================
    COL_CONTRACT_NO = 2   # 合同编号列（1-based）
    COL_CUSTOMER = 3      # 客户名称列
    COL_STATUS = 5        # 合同状态列

    # ==================================================================
    #  Locators: 弹窗区（使用 BasePage 继承的通用 DIALOG_*）
    # ==================================================================
    # 合同详情弹窗内的特定元素
    DIALOG_CONTRACT_TITLE = (
        By.CSS_SELECTOR,
        '.el-dialog:not([style*="display: none"]) .contract-title',
    )

    # ==================================================================
    #  导航
    # ==================================================================
    def navigate(self):
        """导航到合同管理页面（继承自 BasePage 的侧边栏导航）"""
        self.navigate_to("销售管理", "合同管理")
        self._wait_page_ready(timeout=15)
        self.wait_vue_stable()
        return self

    # ==================================================================
    #  业务操作: 搜索
    # ==================================================================
    def input_contract_no(self, text):
        """输入合同编号搜索条件"""
        self.input_text(self.SEARCH_INPUT_CONTRACT_NO, text)
        return self

    def input_customer_name(self, text):
        """输入客户名称搜索条件"""
        self.input_text(self.SEARCH_INPUT_CUSTOMER, text)
        return self

    def click_search(self):
        """点击搜索按钮并等待结果加载"""
        self.click_search_button()   # 继承自 BasePage
        self.wait_overlay_gone()
        self.wait_vue_stable()
        return self

    def click_reset(self):
        """点击重置按钮"""
        self.click_reset_button()    # 继承自 BasePage
        self.wait_vue_stable()
        return self

    # ==================================================================
    #  业务操作: 获取数据
    # ==================================================================
    def get_contract_count(self):
        """获取当前页合同数量"""
        return self.get_table_row_count()

    def get_first_contract_no(self):
        """获取第一行合同编号"""
        return self.get_cell(1, self.COL_CONTRACT_NO)

    def is_contract_present(self, contract_no):
        """判断合同是否存在于当前列表"""
        return self.is_row_present(contract_no)

    # ==================================================================
    #  内部方法
    # ==================================================================
    def _wait_page_ready(self, timeout=15):
        """等待合同列表页完全加载"""
        self._wait_loading_gone(timeout)
        self.wait_vue_stable()
        try:
            self.find_visible(
                (By.CSS_SELECTOR, '.el-table__body-wrapper'),
                timeout,
            )
        except Exception:
            logger.warning("表格未在 %ds 内出现", timeout)
```

### 10.4 测试脚本模板（完整示例）

```python
"""合同管理 — 搜索功能测试

测试点：
  - TC_S01: 按合同编号精确查询
  - TC_S02: 按客户名称模糊查询
  - TC_S03: 空条件查询（全量数据）

Vue/Element Plus 注意：
  - Select 下拉面板通过 Teleport 挂载到 body
  - 查询后表格异步加载，需等待遮罩消失
"""
import logging
import inspect

import pytest
import allure

from page.sales_page.ContractPage import ContractPage

logger = logging.getLogger(__name__)


class TestContractSearch:
    """合同管理 — 搜索功能"""

    @pytest.fixture(autouse=True)
    def _allure_meta(self, request):
        """自动将函数 docstring 注入 Allure 报告"""
        doc = (inspect.getdoc(request.function) or "").strip()
        title = doc.replace(":", " ").strip() if doc else request.function.__name__
        try:
            allure.dynamic.title(title)
            if doc:
                allure.dynamic.description(doc)
        except Exception:
            pass
        yield

    # ==================================================================
    #  TC_S01: 按合同编号精确查询
    # ==================================================================
    @pytest.mark.smoke
    @allure.epic("销售管理")
    @allure.feature("合同管理")
    @allure.story("合同搜索")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_search_by_contract_no_exact(self, contract_page, contract_test_data):
        """TC_S01: 按合同编号精确查询 — 输入完整编号，返回唯一匹配记录"""
        page = contract_page
        data = contract_test_data["existing"]

        with allure.step("步骤1: 输入完整合同编号"):
            page.input_contract_no(data["contract_no"])

        with allure.step("步骤2: 点击搜索"):
            page.click_search()

        with allure.step("步骤3: 断言 — 至少返回 1 条记录"):
            count = page.get_contract_count()
            assert count >= 1, \
                f"预期 ≥1 条记录，实际 {count} 条"

        with allure.step("步骤4: 断言 — 返回记录的合同编号匹配"):
            first_no = page.get_first_contract_no()
            assert data["contract_no"] in first_no, \
                f"预期合同编号含 {data['contract_no']}，实际 {first_no}"

    # ==================================================================
    #  TC_S02: 按客户名称模糊查询
    # ==================================================================
    @pytest.mark.smoke
    @allure.epic("销售管理")
    @allure.feature("合同管理")
    @allure.story("合同搜索")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_search_by_customer_fuzzy(self, contract_page):
        """TC_S02: 按客户名称模糊查询 — 输入部分名称，返回匹配记录"""
        page = contract_page

        with allure.step("步骤1: 输入部分客户名称"):
            page.click_reset()
            page.input_customer_name("科技")

        with allure.step("步骤2: 点击搜索"):
            page.click_search()

        with allure.step("步骤3: 断言 — 返回至少 1 条记录"):
            count = page.get_contract_count()
            assert count >= 1, \
                f"预期 ≥1 条记录，实际 {count} 条"
```

### 10.5 测试数据文件模板（YAML）

```yaml
# sales_contract.yaml — 合同管理静态测试数据
# 用途：为 test_contract_search.py 和 test_contract_display.py 提供固定数据
# 维护：当测试环境数据被清空重建时，更新此文件中的 known 条目

existing:
  contract_no: "HT20260527001"
  customer_name: "测试客户"

search_cases:
  - id: TC_S01
    name: "精确搜索合同编号"
    contract_no: "HT20260527001"
    expect_min_rows: 1
  - id: TC_S02
    name: "模糊搜索客户"
    customer: "科技"
    expect_min_rows: 1
  - id: TC_S03
    name: "空条件搜索"
    expect_min_rows: 0
    expect_max_rows: null

filters:
  statuses:
    - "待审核"
    - "已签订"
    - "已终止"
  product_types:
    - "液化天然气"
    - "压缩天然气"
```

### 10.6 conftest.py 模板（模块级）

```python
"""{模块名}模块共享 fixtures

Fixture 层级：
  - {page}_page (function 级)：每个测试函数独立 Page Object
  - driver_setup (module 级)：每个 test_*.py 文件独立浏览器实例
  - {module}_test_data (session 级)：从 YAML 加载的测试数据

使用方式：
    def test_xxx(self, {page}_page, {module}_test_data):
        page = {page}_page
        data = {module}_test_data["key"]
"""
import logging
import os

import pytest
import yaml

from base.browser_driver import BaseDriver, ensure_logged_in
from page.{module}_page.{PageName} import {PageName}Page

logger = logging.getLogger(__name__)

_FIXTURES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "fixtures"
)


# ==================================================================
#  Module 级 Fixture: 独立浏览器 + 自动导航
# ==================================================================
@pytest.fixture(scope="module")
def driver_setup(request):
    """Module 级：每个测试文件一个浏览器实例，自动导航到目标页面"""
    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        {PageName}Page(driver).navigate()
        yield driver
    finally:
        base.close_browser()


# ==================================================================
#  Function 级 Fixture: Page Object
# ==================================================================
@pytest.fixture(scope="function")
def {page}_page(driver_setup):
    """每个测试函数获取已初始化的 Page Object"""
    page = {PageName}Page(driver_setup)
    page._wait_loading_gone(timeout=10)
    page.wait_vue_stable()
    try:
        page.click_reset()
    except Exception:
        logger.info("重置按钮不可用（可能已在初始状态），继续执行")
    return page


# ==================================================================
#  Session 级 Fixture: 测试数据
# ==================================================================
@pytest.fixture(scope="session")
def {module}_test_data():
    """Session 级：从 YAML 文件加载测试数据"""
    yaml_path = os.path.join(_FIXTURES_DIR, "{module}_entity.yaml")
    with open(yaml_path, encoding="utf-8") as f:
        return yaml.safe_load(f)
```

---

> **文档结束** | 版本 2.0 | 2026-06-05
>
> 本规范适用于 ZJSN 自动化测试项目的所有 AI 模型协作。
> AI 开发成员须在每次会话开始时确保模型已加载本文档的全部或相应章节。
