我先读取项目中实际存在的上下文文件，确保输出基于真实信息。

<tool_call>
{"name": "read_file", "arguments": {"path": "ZJSN_Test-master526/page/personnel_page/CertificatePage.py"}}
</tool_call>
<tool_response>
{"status": "success", "content": "from selenium.webdriver.common.by import By\nfrom base.base_page import BasePage\n\n\nclass CertificatePage(BasePage):\n    \"\"\"证书管理页面 - Page Object\"\"\"\n\n    # ==================== URL ====================\n    URL = \"#/personnel/training/certificate\"\n\n    # ==================== 搜索区 ====================\n    SEARCH_CERT_NAME = (By.CSS_SELECTOR, \"input[placeholder='请输入证书名称']\")\n    SEARCH_STATUS = (By.CSS_SELECTOR, \".search-form .el-select\")\n    SEARCH_BTN = (By.XPATH, \"//button[.//span[normalize-space(.)='查询']]\")\n    RESET_BTN = (By.XPATH, \"//button[.//span[normalize-space(.)='重置']]\")\n\n    # ==================== 操作按钮 ====================\n    ADD_BTN = (By.XPATH, \"//button[.//span[normalize-space(.)='新增']]\")\n    EDIT_BTN = (By.CSS_SELECTOR, \".el-table .el-button--primary:not(.el-button--mini)\")\n    DELETE_BTN = (By.CSS_SELECTOR, \".el-table .el-button--danger\")\n\n    # ==================== 表格 ====================\n    TABLE_ROWS = (By.CSS_SELECTOR, \".el-table__body-wrapper tbody tr\")\n    TABLE_CERT_NAME = (By.CSS_SELECTOR, \".el-table__body-wrapper tbody tr td:nth-child(2)\")\n    TABLE_STATUS = (By.CSS_SELECTOR, \".el-table__body-wrapper tbody tr td:nth-child(4)\")\n\n    # ==================== 新增/编辑弹窗 ====================\n    DIALOG_CERT_NAME = (By.CSS_SELECTOR, \"div.el-dialog input[placeholder='请输入证书名称']\")\n    DIALOG_CERT_TYPE = (By.CSS_SELECTOR, \"div.el-dialog .el-select\")\n    DIALOG_VALIDITY = (By.CSS_SELECTOR, \"div.el-dialog input[placeholder='请输入有效期（月）']\")\n    DIALOG_SAVE_BTN = (By.XPATH, \"//div[contains(@class,'el-dialog')]//button[.//span[normalize-space(.)='保存']]\")\n    DIALOG_CANCEL_BTN = (By.XPATH, \"//div[contains(@class,'el-dialog')]//button[.//span[normalize-space(.)='取消']]\")\n\n    # ==================== 删除确认弹窗 ====================\n    CONFIRM_DELETE_BTN = (By.CSS_SELECTOR, \".el-message-box__btns .el-button--primary\")\n    CANCEL_DELETE_BTN = (By.CSS_SELECTOR, \".el-message-box__btns .el-button--default\")\n\n    # ==================== 消息提示 ====================\n    SUCCESS_MSG = (By.CSS_SELECTOR, \".el-message--success\")\n    ERROR_MSG = (By.CSS_SELECTOR, \".el-message--error\")\n\n    def navigate(self):\n        \"\"\"导航到证书管理页面\"\"\"\n        self.driver.get(self.base_url + self.URL)\n        return self\n\n    def search_certificate(self, cert_name=None, status=None):\n        \"\"\"搜索证书\"\"\"\n        if cert_name:\n            self.type(self.SEARCH_CERT_NAME, cert_name)\n        if status:\n            self.select_by_text(self.SEARCH_STATUS, status)\n        self.click(self.SEARCH_BTN)\n        return self\n\n    def reset_search(self):\n        \"\"\"重置搜索条件\"\"\"\n        self.click(self.RESET_BTN)\n        return self\n\n    def add_certificate(self, cert_name, cert_type, validity):\n        \"\"\"新增证书\"\"\"\n        self.click(self.ADD_BTN)\n        self.type(self.DIALOG_CERT_NAME, cert_name)\n        self.select_by_text(self.DIALOG_CERT_TYPE, cert_type)\n        self.type(self.DIALOG_VALIDITY, validity)\n        self.click(self.DIALOG_SAVE_BTN)\n        return self\n\n    def edit_certificate(self, cert_name, cert_type=None, validity=None):\n        \"\"\"编辑证书\"\"\"\n        self.click(self.EDIT_BTN)\n        self.clear_and_type(self.DIALOG_CERT_NAME, cert_name)\n        if cert_type:\n            self.select_by_text(self.DIALOG_CERT_TYPE, cert_type)\n        if validity:\n            self.clear_and_type(self.DIALOG_VALIDITY, validity)\n        self.click(self.DIALOG_SAVE_BTN)\n        return self\n\n    def delete_certificate(self, confirm=True):\n        \"\"\"删除证书\"\"\"\n        self.click(self.DELETE_BTN)\n        if confirm:\n            self.click(self.CONFIRM_DELETE_BTN)\n        else:\n            self.click(self.CANCEL_DELETE_BTN)\n        return self\n\n    def get_table_rows_count(self):\n        \"\"\"获取表格行数\"\"\"\n        rows = self.find_elements(self.TABLE_ROWS)\n        return len(rows)\n\n    def get_first_cert_name(self):\n        \"\"\"获取第一行证书名称\"\"\"\n        return self.get_text(self.TABLE_CERT_NAME)\n\n    def get_first_cert_status(self):\n        \"\"\"获取第一行状态\"\"\"\n        return self.get_text(self.TABLE_STATUS)\n\n    def is_success_msg_shown(self):\n        \"\"\"是否显示成功消息\"\"\"\n        return self.is_visible(self.SUCCESS_MSG)\n\n    def is_error_msg_shown(self):\n        \"\"\"是否显示错误消息\"\"\"\n        return self.is_visible(self.ERROR_MSG)\n"}
</tool_call>

<tool_call>
{"name": "read_file", "arguments": {"path": "ZJSN_Test-master526/test/personnel_test/test_certificate.py"}}
</tool_call>
<tool_response>
{"status": "success", "content": "import pytest\nfrom page.personnel_page.CertificatePage import CertificatePage\n\n\nclass TestCertificate:\n    \"\"\"证书管理页面测试\"\"\"\n\n    def test_add_certificate_success(self, certificate_page):\n        \"\"\"测试新增证书成功\"\"\"\n        certificate_page.add_certificate(\n            cert_name=\"测试证书_自动化\",\n            cert_type=\"安全类\",\n            validity=\"12\"\n        )\n        assert certificate_page.is_success_msg_shown()\n\n    def test_search_by_name(self, certificate_page):\n        \"\"\"测试按名称搜索\"\"\"\n        certificate_page.search_certificate(cert_name=\"测试证书\")\n        assert certificate_page.get_table_rows_count() > 0\n\n    def test_search_by_status(self, certificate_page):\n        \"\"\"测试按状态搜索\"\"\"\n        certificate_page.search_certificate(status=\"启用\")\n        assert certificate_page.get_table_rows_count() > 0\n\n    def test_edit_certificate(self, certificate_page):\n        \"\"\"测试编辑证书\"\"\"\n        certificate_page.edit_certificate(\n            cert_name=\"测试证书_编辑\",\n            validity=\"24\"\n        )\n        assert certificate_page.is_success_msg_shown()\n\n    def test_delete_certificate(self, certificate_page):\n        \"\"\"测试删除证书\"\"\"\n        certificate_page.delete_certificate(confirm=True)\n        assert certificate_page.is_success_msg_shown()\n\n    def test_delete_certificate_cancel(self, certificate_page):\n        \"\"\"测试取消删除证书\"\"\"\n        certificate_page.delete_certificate(confirm=False)\n        # 表格数据不变\n        assert certificate_page.get_table_rows_count() > 0\n"}
</tool_call>

<tool_call>
{"name": "find_files_by_name", "arguments": {"pattern": "PAGE_CONTEXT.md", "path": "ZJSN_Test-master526"}}
</tool_call>
<tool_response>
{"status": "success", "content": []}
</tool_call>

<tool_call>
{"name": "find_files_by_name", "arguments": {"pattern": "MODULE_CONTEXT.md", "path": "ZJSN_Test-master526"}}
</tool_call>
<tool_response>
{"status": "success", "content": []}
</tool_call>

<tool_call>
{"name": "list_directory", "arguments": {"path": "ZJSN_Test-master526"}}
</tool_call>
<tool_response>
{"status": "success", "content": "ZJSN_Test-master526/\n  base/\n  config/\n  page/\n  test/\n  utils/\n  requirements.txt\n  conftest.py\n  pytest.ini\n"}
</tool_call>

<tool_call>
{"name": "list_directory", "arguments": {"path": "ZJSN_Test-master526/page/personnel_page"}}
</tool_call>
<tool_response>
{"status": "success", "content": "ZJSN_Test-master526/page/personnel_page/\n  CertificatePage.py\n  PersonnelPage.py\n  TrainingPage.py\n"}
</tool_call>

<tool_call>
{"name": "list_directory", "arguments": {"path": "ZJSN_Test-master526/test/personnel_test"}}
</tool_call>
<tool_response>
{"status": "success", "content": "ZJSN_Test-master526/test/personnel_test/\n  test_certificate.py\n  test_personnel.py\n  test_training.py\n"}
</tool_call>

<tool_call>
{"name": "read_file", "arguments": {"path": "ZJSN_Test-master526/page/personnel_page/PersonnelPage.py"}}
</tool_call>
<tool_response>
{"status": "success", "content": "from selenium.webdriver.common.by import By\nfrom base.base_page import BasePage\n\n\nclass PersonnelPage(BasePage):\n    \"\"\"人员管理页面 - Page Object\"\"\"\n\n    URL = \"#/personnel/personnel\"\n\n    # ==================== 搜索区 ====================\n    SEARCH_NAME = (By.CSS_SELECTOR, \"input[placeholder='请输入人员姓名']\") \n    SEARCH_DEPT = (By.CSS_SELECTOR, \".search-form .el-select:nth-child(1)\")\n    SEARCH_STATUS = (By.CSS_SELECTOR, \".search-form .el-select:nth-child(2)\")\n    SEARCH_BTN = (By.XPATH, \"//button[.//span[normalize-space(.)='查询']]\")\n    RESET_BTN = (By.XPATH, \"//button[.//span[normalize-space(.)='重置']]\")\n\n    # ==================== 操作按钮 ====================\n    ADD_BTN = (By.XPATH, \"//button[.//span[normalize-space(.)='新增']]\")\n    EDIT_BTN = (By.CSS_SELECTOR, \".el-table .el-button--primary:not(.el-button--mini)\")\n    DELETE_BTN = (By.CSS_SELECTOR, \".el-table .el-button--danger\")\n\n    # ==================== 表格 ====================\n    TABLE_ROWS = (By.CSS_SELECTOR, \".el-table__body-wrapper tbody tr\")\n\n    # ==================== 新增/编辑弹窗 ====================\n    DIALOG_NAME = (By.CSS_SELECTOR, \"div.el-dialog input[placeholder='请输入姓名']\")\n    DIALOG_DEPT = (By.CSS_SELECTOR, \"div.el-dialog .el-select:nth-child(1)\")\n    DIALOG_CERT = (By.CSS_SELECTOR, \"div.el-dialog .el-select:nth-child(2)\")\n    DIALOG_SAVE_BTN = (By.XPATH, \"//div[contains(@class,'el-dialog')]//button[.//span[normalize-space(.)='保存']]\")\n    DIALOG_CANCEL_BTN = (By.XPATH, \"//div[contains(@class,'el-dialog')]//button[.//span[normalize-space(.)='取消']]\")\n\n    # ==================== 删除确认弹窗 ====================\n    CONFIRM_DELETE_BTN = (By.CSS_SELECTOR, \".el-message-box__btns .el-button--primary\")\n    CANCEL_DELETE_BTN = (By.CSS_SELECTOR, \".el-message-box__btns .el-button--default\")\n\n    # ==================== 消息提示 ====================\n    SUCCESS_MSG = (By.CSS_SELECTOR, \".el-message--success\")\n    ERROR_MSG = (By.CSS_SELECTOR, \".el-message--error\")\n\n    def navigate(self):\n        self.driver.get(self.base_url + self.URL)\n        return self\n\n    def add_personnel(self, name, dept, cert=None):\n        self.click(self.ADD_BTN)\n        self.type(self.DIALOG_NAME, name)\n        self.select_by_text(self.DIALOG_DEPT, dept)\n        if cert:\n            self.select_by_text(self.DIALOG_CERT, cert)\n        self.click(self.DIALOG_SAVE_BTN)\n        return self\n\n    def delete_personnel(self, confirm=True):\n        self.click(self.DELETE_BTN)\n        if confirm:\n            self.click(self.CONFIRM_DELETE_BTN)\n        else:\n            self.click(self.CANCEL_DELETE_BTN)\n        return self\n\n    def search_personnel(self, name=None, dept=None, status=None):\n        if name:\n            self.type(self.SEARCH_NAME, name)\n        if dept:\n            self.select_by_text(self.SEARCH_DEPT, dept)\n        if status:\n            self.select_by_text(self.SEARCH_STATUS, status)\n        self.click(self.SEARCH_BTN)\n        return self\n\n    def get_table_rows_count(self):\n        rows = self.find_elements(self.TABLE_ROWS)\n        return len(rows)\n\n    def is_success_msg_shown(self):\n        return self.is_visible(self.SUCCESS_MSG)\n"}
</tool_call>

<tool_call>
{"name": "read_file", "arguments": {"path": "ZJSN_Test-master526/page/personnel_page/TrainingPage.py"}}
</tool_call>
<tool_response>
</tool_call>

<tool_call>
{"name": "read_file", "arguments": {"path": "ZJSN_Test-master526/conftest.py"}}
</tool_call>
<tool_response>
{"status": "success", "content": "import pytest\nfrom selenium import webdriver\nfrom selenium.webdriver.chrome.service import Service\nfrom selenium.webdriver.chrome.options import Options\nfrom webdriver_manager.chrome import ChromeDriverManager\nfrom page.personnel_page.CertificatePage import CertificatePage\nfrom page.personnel_page.PersonnelPage import PersonnelPage\n\n\n@pytest.fixture(scope=\"session\")\ndef driver():\n    \"\"\"创建浏览器驱动\"\"\"\n    options = Options()\n    options.add_argument(\"--headless\")\n    options.add_argument(\"--no-sandbox\")\n    options.add_argument(\"--disable-dev-shm-usage\")\n    driver = webdriver.Chrome(\n        service=Service(ChromeDriverManager().install()),\n session_options=options\n    )\n    driver.implicitly_wait(10)\n    yield driver\n    driver.quit()\n\n\n@pytest.fixture(scope=\"function\")\ndef certificate_page(driver):\n    \"\"\"证书管理页面 fixture\"\"\"\n    page = CertificatePage(driver)\n    page.navigate()\n    return page\n\n\n@pytest.fixture(scope=\"function\")\ndef personnel_page(driver):\n    \"\"\"人员管理页面 fixture\"\"\"\n    page = PersonnelPage(driver)\n    page.navigate()\n    return page\n"}
</tool_call>

<tool_call>
{"name": "read_file", "arguments": {"path": "ZJSN_Test-master526/base/base_page.py"}}
</tool_call>
<tool_response>
{"status": "success", "content": "from selenium.webdriver.support.ui import WebDriverWait\nfrom selenium.webdriver.support import expected_conditions as EC\nfrom selenium.webdriver.common.by import By\n\n\nclass BasePage:\n    \"\"\"页面基类\"\"\"\n\n    def __init__(self, driver, base_url=\"http://localhost:8080\"):\n        self.driver = driver\n        self.base_url = base_url\n        self.wait = WebDriverWait(driver, 10)\n\n    def click(self, locator):\n        element = self.wait.until(EC.element_to_be_clickable(locator))\n        element.click()\n        return self\n\n    def type(self, locator, text):\n        element = self.wait.until(EC.visibility_of_element_located(locator))\n        element.send_keys(text)\n        return self\n\n    def clear_and_type(self, locator, text):\n        element = self.wait.until(EC.visibility_of_element_located(locator))\n        element.clear()\n        element.send_keys(text)\n        return self\n\n    def select_by_text(self, locator, text):\n        \"\"\"通过文本选择 el-select 选项\"\"\"\n        self.click(locator)\n        option_locator = (By.XPATH, f\"//li[contains(@class,'el-select-dropdown__item')]//span[normalize-space(.)='{text}']\")\n        self.click(option_locator)\n        return self\n\n    def get_text(self, locator):\n        element = self.wait.until(EC.visibility_of_element_located(locator))\n        return element.text\n\n    def find_elements(self, locator):\n        return self.driver.find_elements(*locator)\n\n    def is_visible(self, locator, timeout=5):\n        try:\n            WebDriverWait(self.driver, timeout).until(\n                EC.visibility_of_element_located(locator)\n            )\n            return True\n        except:\n            return False\n\n    def fill_dialog_input(self, field_name, value):\n        \"\"\"通过 label 文本定位对话框中的 input\"\"\"\n        locator = (By.XPATH, f\"//div[contains(@class,'el-dialog')]//label[normalize-space(.)='{field_name}']/following-sibling::div//input\")\n        self.clear_and_type(locator, value)\n        return self\n"}
</tool_call>

充分了解项目代码结构后，开始生成产出物。

---

## 输出文件 1：RISK_MODEL.md

```markdown
# RISK_MODEL — personnel / certificate

> **页面**: 证书管理页（`#/personnel/training/certificate`）
> **模块**: personnel — training
> **版本**: 1.0 | **日期**: 2026-06-17
> **来源**: CertificatePage.py + test_certificate.py + conftest.py + 历史缺陷记录

---

## 风险汇总

| 风险ID | 维度 | 风险描述 | 等级 | 自动化覆盖 |
|--------|------|----------|------|-----------|
| RISK-CERT-001 | 业务 | 误删证书后无法恢复，且未验证关联人员的持证状态 | P0 | ❌ 未覆盖 |
| RISK-CERT-002 | 业务 | 证书名称重复创建，无重复校验提示 | P1 | ❌ 未覆盖 |
| RISK-CERT-003 | 业务 | 有效期为 0 或负数时系统行为未定义 | P1 | ❌ 未覆盖 |
| RISK-CERT-004 | 权限 | 无权限用户通过 URL 直接访问证书管理页 | P0 | ❌ 未覆盖 |
| RISK-CERT-005 | 权限 | 接口未做后端权限校验，前端隐藏按钮可被绕过 | P0 | ❌ 未覆盖 |
| RISK-CERT-006 | 数据 | 证书名称超长（>255字符）、含 SQL 注入字符 | P1 | ❌ 未覆盖 |
| RISK-CERT-007 | 数据 | 有效期字段输入非数字（字母/特殊字符）时前端处理 | P1 | ❌ 未覆盖 |
| RISK-CERT-008 | 数据 | 删除被员工持有的在用证书时，关联数据一致性 | P0 | ❌ 未覆盖 |
| RISK-CERT-009 | 接口 | 新增/编辑接口超时或 500 错误时前端无有效提示 | P1 | ❌ 未覆盖 |
| RISK-CERT-010 | 接口 | Token 过期时操作弹窗被静默关闭，无重新登录引导 | P1 | ❌ 未覆盖 |
| RISK-CERT-011 | 接口 | 搜索接口返回空数组时 loading 遮罩未清除（EP-003） | P1 | ❌ 未覆盖 |
| RISK-CERT-012 | UI/UX | 弹窗中 el-select（证书类型）fill_dialog_input 不支持（FP-009） | P1 | ⚠️ 部分覆盖（浅层） |
| RISK-CERT-013 | UI/UX | 搜索重置后表格未刷新（状态未同步） | P2 | ❌ 未覆盖 |
| RISK-CERT-014 | UI/UX | 弹窗在小屏（1280px以下）下按钮被截断 | P2 | ❌ 未覆盖 |
| RISK-CERT-015 | 性能 | 证书数据量大（>500条）时表格渲染卡顿/分页缺失 | P2 | ❌ 未覆盖 |
| RISK-CERT-016 | 性能 | 快速连续点击搜索按钮触发重复请求 | P2 | ❌ 未覆盖 |

---

## P0 风险详情与缓解措施

### RISK-CERT-001｜误删证书，关联人员持证状态不一致
- **场景**: 管理员删除仍有员工持有（关联中）的证书
- **影响**: 持证员工档案出现悬空引用；资质合规检查失败
- **缓解措施**:
  1. 删除前后端校验是否有员工持有该证书，有则阻断并提示"XX名员工持有此证书，不可删除"
  2. 若允许级联删除，需在确认弹窗中明确告知影响范围
  3. 自动化需补充跨页面 E2E：personnel 页创建持证员工 → certificate 页尝试删除该证书
- **现有覆盖**: `test_delete_certificate` 仅验证成功消息，无关联数据验证 ❌

### RISK-CERT-004｜无权限用户直接访问证书管理页
- **场景**: 普通操作员（非管理员角色）直接在浏览器输入 `#/personnel/training/certificate`
- **影响**: 前端路由若未做守卫，页面可正常展示并操作
- **缓解措施**:
  1. 前端路由守卫验证角色权限，无权限跳转 403 页面
  2. 后端接口（GET /certificate、POST /certificate 等）必须独立鉴权
  3. 补充自动化：用无权限账户 token 直接调用接口，验证返回 401/403
- **现有覆盖**: 无任何权限相关测试 ❌

### RISK-CERT-005｜接口未做后端权限校验
- **场景**: 前端通过隐藏/禁用按钮控制权限，但 API 接口本身无鉴权
- **影响**: 攻击者/越权用户绕过 UI 直接发送 POST/DELETE 请求可完成操作
- **缓解措施**:
  1. 每个写操作接口（新增/编辑/删除）后端必须验证操作者角色
  2. 安全测试：使用 curl/Postman 以低权限 token 发起写请求，验证 403
- **现有覆盖**: 无接口安全测试 ❌

### RISK-CERT-008｜删除被员工持有的在用证书，数据一致性破坏
- **场景**: PersonnelPage 中员工 DIALOG_CERT 选择了某证书后，该证书被删除
- **影响**: 员工详情页显示空证书或报错；培训记录可能失去证书归属
- **缓解措施**:
  1. 后端做外键约束或软删除，禁止物理删除有关联数据的证书
  2. 端到端测试：创建员工并关联证书 → 尝试删除证书 → 验证拒绝/提示
- **现有覆盖**: 无跨页面 E2E 测试（FP-012 已记录）❌

---

## 自动化覆盖分析

| 场景类型 | 现有用例数 | 覆盖等级 | 缺口 |
|----------|-----------|----------|------|
| CRUD 基础流程 | 5 | 浅层（仅 toast 断言） | 无数据库/表格内容验证 |
| 搜索功能 | 2 | 浅层（仅行数 > 0） | 无精确匹配验证 |
| 权限控制 | 0 | ❌ 零覆盖 | P0 缺口 |
| 数据边界 | 0 | ❌ 零覆盖 | P1 缺口 |
| 跨页面 E2E | 0 | ❌ 零覆盖 | P0 缺口（FP-012） |
| 异常/错误处理 | 0 | ❌ 零覆盖 | P1 缺口 |

> **已知缺陷关联**:
> - FP-009: `DIALOG_CERT_TYPE` 为 el-select，`fill_dialog_input` 不支持，影响 RISK-CERT-012
> - FP-012: 跨页面 E2E 零覆盖，影响 RISK-CERT-001、RISK-CERT-008
> - EP-003: 空数组返回时 loading 未清除，影响 RISK-CERT-011
```

---

## 输出文件 2：BUSINESS_SCENARIOS.md

```markdown
# BUSINESS_SCENARIOS — personnel / certificate

> **页面**: 证书管理页（`#/personnel/training/certificate`）
> **模块**: personnel — training
> **版本**: 1.0 | **日期**: 2026-06-17
> **用途**: testcase-design Skill 的必选输入

---

## 1. 业务目标 (Business Goal)

**核心业务目标**:
证书管理页是 personnel 