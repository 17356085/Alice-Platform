# AUTOMATION ARCHITECTURE — ZJSN 自动化测试框架

> 版本：1.0 | 日期：2026-06-04 | 评审人：架构评审

---

## 一、项目定位

本项目是一个面向 **鞍集涂源管理系统**（Vue3 + Element Plus）的 UI 自动化测试框架，
覆盖系统管理、人员管理、销售管理、实验室等核心业务模块。

当前定位：**Level 2 — 团队内部项目**（具备 Level 3 部分特征，但尚未完成企业化改造）。

---

## 二、技术架构

```
Python 3.x
├── pytest 7.4.4           # 测试运行与插件体系
├── Selenium 4.15.2        # WebDriver 驱动层
├── allure-pytest 2.13.2   # 报告体系
├── pytest-xdist 3.5.0     # 并行执行（尚未启用）
└── openpyxl / pandas      # 数据驱动（部分使用）
```

被测系统：Vue 3 + Element Plus（前端）| 未知后端 API

---

## 三、分层设计（当前实现）

```
┌─────────────────────────────────────────────────────────┐
│                  测试脚本层 (script/)                     │
│  test_*.py  — 业务场景编排，不含 Selenium 直接调用        │
├─────────────────────────────────────────────────────────┤
│                  Fixture 编排层 (conftest.py)             │
│  module / function / session 三级 scope                  │
│  自动导航 + 数据清理 + 登录保障                          │
├─────────────────────────────────────────────────────────┤
│                  页面对象层 (page/)                        │
│  XxxPage.py  — 业务操作封装，locator 与操作共存           │
├─────────────────────────────────────────────────────────┤
│          基础封装层 (base/)                               │
│  BasePage            — 通用操作 + Vue 等待策略            │
│  ElementPlusHelper   — Element Plus 组件专用              │
│  SidebarNavigator    — 侧边栏导航封装                     │
│  BaseDriver          — WebDriver 生命周期管理             │
├─────────────────────────────────────────────────────────┤
│                  配置层 (config.py / pytest.ini)          │
│  URL、超时、浏览器、日志 集中管理                        │
└─────────────────────────────────────────────────────────┘
```

---

## 四、目录规范

### 4.1 当前目录（已验证合理）

```
ZJSN_Test-master526/
├── config.py              # 环境变量、超时、浏览器、日志 — 单一配置入口
├── conftest.py            # 根级：路径注入、日志初始化、失败截图钩子
├── pytest.ini             # 执行配置、markers 定义
├── requirements.txt       # 依赖锁定
│
├── base/                  # 基础封装 — 框架级代码，业务无关
│   ├── base_page.py       # Page Object 基类
│   ├── browser_driver.py  # 驱动生命周期 + ensure_logged_in
│   ├── element_plus_helper.py  # Element Plus 组件专用
│   └── sidebar_navigator.py   # 导航封装
│
├── page/                  # Page Object 层 — 业务操作封装
│   ├── system_page/
│   ├── person_page/
│   ├── sales_page/
│   └── lab_page/
│
├── script/                # 测试用例层 — 断言 + 场景编排
│   ├── conftest.py        # 根测试配置（可选）
│   ├── system/conftest.py # 模块 fixture
│   ├── sales/conftest.py
│   ├── person/conftest.py
│   └── lab/conftest.py
│
├── data/                  # 测试数据文件
├── artifacts/             # 失败截图 + HTML（自动生成，应加入 .gitignore）
└── allure-results/        # Allure 原始结果（自动生成，应加入 .gitignore）
```

### 4.2 建议补充目录

```
├── .env                   # 环境变量（不提交）
├── .env.example           # 示例环境变量（提交）
├── .gitignore             # 排除 artifacts/ allure-results/ __pycache__/
├── Makefile               # 标准化执行命令入口
└── data/
    ├── fixtures/          # 静态测试数据 (JSON/YAML)
    └── factories/         # 动态数据工厂
```

---

## 五、PageObject 规范

### 5.1 已遵循的规范（正向）

- 继承 `BasePage`，不直接操作 `webdriver`
- Locator 以类属性常量形式声明在 Page 类顶部
- 每个 Page 类聚焦单一页面，有 `navigate()` 入口
- 使用 CSS Selector 优先，XPath 保底（符合最佳实践）
- 操作方法命名语义化（`click_search`, `input_contract_no`）

### 5.2 规范定义（补充约束）

```python
class XxxPage(BasePage):
    # 1. 所有 Locator 在类顶部声明为 (By.XXX, "selector") 元组
    SEARCH_INPUT = (By.CSS_SELECTOR, ".search-input input")
    
    # 2. navigate() 是唯一的页面跳转入口
    def navigate(self):
        self.navigate_to("一级菜单", "二级菜单")
        self._wait_page_ready()
    
    # 3. 操作方法不含 assert，不含 time.sleep > 0.5s
    # 4. 操作方法返回 self 以支持链式调用（可选）
    # 5. 不在 Page 内导入 pytest、logging（使用 BasePage 的 logger）
```

### 5.3 Locator 分离（建议演进方向）

```python
# page/locators/sales_locators.py
class ContractLocators:
    SEARCH_INPUT    = (By.CSS_SELECTOR, ".contract-no input")
    SEARCH_BUTTON   = (By.XPATH, "//button[.//span[text()='搜索']]")
    TABLE_ROWS      = (By.CSS_SELECTOR, ".el-table__row")
```

---

## 六、Fixture 规范

### 6.1 Scope 使用原则

| Scope | 适用场景 | 当前实现 |
|-------|---------|---------|
| `session` | 整个测试会话共享浏览器（只读/查询场景） | 已实现（sales） |
| `module` | 每个 test_*.py 独立浏览器（增删改场景） | 主要模式 |
| `function` | 每用例独立 Page Object（高隔离，慢） | 部分使用 |
| `class` | 测试类内共享 | 未使用 |

### 6.2 Fixture 命名约定

```
driver_setup          — module 级驱动（历史命名，保持兼容）
{module}_logged_in_driver   — 已登录驱动（建议统一前缀）
{page_name}_page      — 已初始化 Page Object (function 级)
{module}_test_data    — 模块级测试数据准备
```

### 6.3 数据清理原则

- 后置清理（`finally` 块）优于前置清理
- 清理失败只记录警告，不阻断测试
- 使用模块级变量（`module.CREATED_XXX`）传递待清理数据标识

### 6.4 登录状态管理（当前实现要点）

```
ensure_logged_in() → 检测已登录 → 跳过 / 检测登录页 → 执行登录
所有 module fixture 通过 ensure_logged_in() 保障，不依赖 session cookie
```

---

## 七、测试执行流程

```
1. pytest 收集 script/ 下所有 test_*.py
2. 按 module scope 初始化 driver_setup
   └── BaseDriver.open_browser() → 启动 Chrome
   └── ensure_logged_in() → 登录验证
   └── _navigate_for_module() → 自动导航
3. 执行测试用例
   └── conftest.pytest_runtest_makereport → 失败截图
4. module teardown → _teardown_for_module() → 数据清理
5. allure-results/ 生成原始结果 → allure generate → HTML 报告
```

### 7.1 标准执行命令

```bash
# 冒烟测试
pytest -m smoke --alluredir=allure-results

# 全量回归
pytest --alluredir=allure-results

# 指定模块
pytest script/sales/ --alluredir=allure-results

# 并行（需要独立浏览器实例支持）
pytest -n 4 --alluredir=allure-results

# 查看报告
allure serve allure-results
```

---

## 八、报告体系

### 8.1 当前状态

| 报告类型 | 工具 | 状态 |
|---------|------|------|
| Allure HTML | allure-pytest | 已接入，缺少 `@allure.story` 等注解 |
| 失败截图 | 自实现 hook | 完整实现 |
| Excel 报告 | tools/generate_*.py | 手动生成，非标 |
| pytest-html | pytest-html | 已安装，未使用 |

### 8.2 Allure 注解规范（待补充）

```python
@allure.epic("销售管理")
@allure.feature("合同管理")
@allure.story("合同列表搜索")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.smoke
def test_search_by_contract_no(contract_page):
    with allure.step("输入合同编号搜索"):
        ...
    with allure.step("断言搜索结果"):
        ...
```

---

## 九、演进路线

### Phase 1 — 稳定化（当前 → 1个月）

- [ ] 敏感信息（URL/密码）迁移到 `.env`，config.py 读取环境变量
- [ ] 统一 Allure 注解（epic/feature/story/severity）
- [ ] 补充 `__init__.py` 确保 page/ 下所有模块可导入
- [ ] 添加 `.gitignore` 排除 artifacts/、allure-results/、__pycache__/
- [ ] tools/ 调试脚本迁移出核心目录

### Phase 2 — 工程化（1个月 → 3个月）

- [ ] Locator 与操作逻辑分离（`page/locators/`）
- [ ] 测试数据外置（YAML/JSON）+ 数据工厂
- [ ] pytest-xdist 并行化（需解决 module 级 driver 共享问题）
- [ ] Jenkins Pipeline 接入（headless 模式 + 报告发布）
- [ ] 接口 Mock 层（减少 E2E 依赖，提升稳定性）

### Phase 3 — 平台化（3个月+）

- [ ] 测试平台化（Web UI 管理用例/执行/报告）
- [ ] 测试环境动态管理（多环境切换）
- [ ] AI 辅助用例生成（基于页面 DOM 分析）
- [ ] 质量门禁与覆盖率度量

---

*文档维护：每次架构变更后同步更新本文件*
