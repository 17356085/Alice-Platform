我先读取实际的项目文件，再生成产出物。

让我读取 CertificatePage.py 和相关测试脚本文件。

<tool_call>
{"name": "read_file", "arguments": {"path": "ZJSN_Test-master526/page/personnel_page/CertificatePage.py"}}
</tool_call>
<tool_response>
{"status": "success", "content": "from selenium.webdriver.common.by import By\nfrom base.base_page import BasePage\n\n\nclass CertificatePage(BasePage):\n    \"\"\"证书管理页面 - Page Object\"\"\"\n\n    # ==================== URL ====================\n    URL = \"#/personnel/training/certificate\"\n\n    # ==================== 搜索区 ====================\n    SEARCH_CERT_NAME = (By.CSS_SELECTOR, \"input[placeholder='请输入证书名称']\")\n    SEARCH_STATUS = (By.CSS_SELECTOR, \".search-form .el-select\")\n    SEARCH_BTN = (By.XPATH, \"//button[.//span[normalize-space(.)='查询']]\")\n    RESET_BTN = (By.XPATH, \"//button[.//span[normalize-space(.)='重置']]\")\n\n    # ==================== 操作按钮 ====================\n    ADD_BTN = (By.XPATH, \"//button[.//span[normalize-space(.)='新增']]\")\n    EDIT_BTN = (By.CSS_SELECTOR, \".el-table .el-button--primary:not(.el-button--mini)\")\n    DELETE_BTN = (By.CSS_SELECTOR, \".el-table .el-button--danger\")\n\n    # ==================== 表格 ====================\n    TABLE_ROWS = (By.CSS_SELECTOR, \".el-table__body-wrapper tbody tr\")\n    TABLE_CERT_NAME = (By.CSS_SELECTOR, \".el-table__body-wrapper tbody tr td:nth-child(2)\")\n    TABLE_STATUS = (By.CSS_SELECTOR, \".el-table__body-wrapper tbody tr td:nth-child(4)\")\n\n    # ==================== 新增/编辑弹窗 ====================\n    DIALOG_CERT_NAME = (By.CSS_SELECTOR, \"div.el-dialog input[placeholder='请输入证书名称']\")  \n    DIALOG_CERT_TYPE = (By.CSS_SELECTOR, \"div.el-dialog .el-select\")\n    DIALOG_VALIDITY = (By.CSS_SELECTOR, \"div.el-dialog input[placeholder='请输入有效期（月）']\")\n    DIALOG_SAVE_BTN = (By.XPATH, \"//div[contains(@class,'el-dialog')]//button[.//span[normalize-space(.)='保存']]\")\n    DIALOG_CANCEL_BTN = (By.XPATH, \"//div[contains(@class,'el-dialog')]//button[.//span[normalize-space(.)='取消']]\")\n\n    # ==================== 删除确认弹窗 ====================\n    CONFIRM_DELETE_BTN = (By.CSS_SELECTOR, \".el-message-box__btns .el-button--primary\")\n    CANCEL_DELETE_BTN = (By.CSS_SELECTOR, \".el-message-box__btns .el-button--default\")\n\n    # ==================== 消息提示 ====================\n    SUCCESS_MSG = (By.CSS_SELECTOR, \".el-message--success\")\n    ERROR_MSG = (By.CSS_SELECTOR, \".el-message--error\")\n\n    def navigate(self):\n        \"\"\"导航到证书管理页面\"\"\"\n        self.driver.get(self.base_url + self.URL)\n        return self\n\n    def search_certificate(self, cert_name=None, status=None):\n        \"\"\"搜索证书\"\"\"\n        if cert_name:\n            self.type(self.SEARCH_CERT_NAME, cert_name)\n        if status:\n            self.select_by_text(self.SEARCH_STATUS, status)\n        self.click(self.SEARCH_BTN)\n        return self\n\n    def reset_search(self):\n        \"\"\"重置搜索条件\"\"\"\n        self.click(self.RESET_BTN)\n        return self\n\n    def add_certificate(self, cert_name, cert_type, validity):\n        \"\"\"新增证书\"\"\"\n        self.click(self.ADD_BTN)\n        self.type(self.DIALOG_CERT_NAME, cert_name)\n        self.select_by_text(self.DIALOG_CERT_TYPE, cert_type)\n        self.type(self.DIALOG_VALIDITY, validity)\n        self.click(self.DIALOG_SAVE_BTN)\n        return self\n\n    def edit_certificate(self, cert_name=None, cert_type=None, validity=None):\n        \"\"\"编辑证书（点击第一行编辑按钮）\"\"\"\n        self.click(self.EDIT_BTN)\n        if cert_name:\n            self.clear_and_type(self.DIALOG_CERT_NAME, cert_name)\n        if cert_type:\n            self.select_by_text(self.DIALOG_CERT_TYPE, cert_type)\n        if validity:\n            self.clear_and_type(self.DIALOG_VALIDITY, validity)\n        self.click(self.DIALOG_SAVE_BTN)\n        return self\n\n    def delete_certificate(self):\n        \"\"\"删除证书（点击第一行删除按钮并确认）\"\"\"\n        self.click(self.DELETE_BTN)\n        self.click(self.CONFIRM_DELETE_BTN)\n        return self\n\n    def get_first_row_cert_name(self):\n        \"\"\"获取表格第一行的证书名称\"\"\"\n        return self.get_text(self.TABLE_CERT_NAME)\n\n    def is_success_message_shown(self):\n        \"\"\"检查成功消息是否显示\"\"\"\n        return self.is_visible(self.SUCCESS_MSG)\n\n    def is_error_message_shown(self):\n        \"\"\"检查错误消息是否显示\"\"\"\n        return self.is_visible(self.ERROR_MSG)\n"}
</tool_response>

<tool_call>
{"name": "list_directory", "arguments": {"path": "ZJSN_Test-master526/test"}}
</tool_call>
<tool_response>
{"status": "success", "content": [{"name": "equipment", "type": "directory"}, {"name": "personnel", "type": "directory"}, {"name": "warehouse", "type": "directory"}]}
</tool_response>

<tool_call>
{"name": "list_directory", "arguments": {"path": "ZJSN_Test-master526/test/personnel"}}
</tool_call>
<tool_response>
{"status": "success", "content": [{"name": "test_certificate.py", "type": "file"}, {"name": "test_department.py", "type": "file"}, {"name": "test_personnel.py", "type": "file"}, {"name": "test_training_record.py", "type": "file"}, {"name": "conftest.py", "type": "file"}]}
</tool_response>

<tool_call>
{"name": "read_file", "arguments": {"path": "ZJSN_Test-master526/test/personnel/test_certificate.py"}}
</tool_call>
<tool_response>
{"status": "success", "content": "import pytest\nfrom page.personnel_page.CertificatePage import CertificatePage\n\n\nclass TestCertificate:\n    \"\"\"证书管理测试套件\"\"\"\n\n    def test_add_certificate_success(self, certificate_page):\n        \"\"\"TC-CERT-001: 新增证书 - 正常流程\"\"\"\n        cert_name = \"TC-自动化证书001\"\n        certificate_page.add_certificate(\n            cert_name=cert_name,\n            cert_type=\"资质证书\",\n            validity=\"12\"\n        )\n        assert certificate_page.is_success_message_shown(), \"新增证书后应显示成功提示\"\n\n    def test_search_certificate(self, certificate_page):\n        \"\"\"TC-CERT-002: 搜索证书\"\"\"\n        certificate_page.search_certificate(cert_name=\"TC-自动化证书001\")\n        rows = certificate_page.find_elements(CertificatePage.TABLE_ROWS)\n        assert len(rows) >= 1, \"搜索结果应至少有一条记录\"\n\n    def test_edit_certificate_success(self, certificate_page):\n        \"\"\"TC-CERT-003: 编辑证书 - 正常流程\"\"\"\n        certificate_page.edit_certificate(cert_name=\"TC-自动化证书001-edited\")\n        assert certificate_page.is_success_message_shown(), \"编辑证书后应显示成功提示\"\n\n    def test_delete_certificate_success(self, certificate_page):\n        \"\"\"TC-CERT-004: 删除证书 - 正常流程\"\"\"\n        certificate_page.delete_certificate()\n        assert certificate_page.is_success_message_shown(), \"删除证书后应显示成功提示\"\n\n    def test_search_reset(self, certificate_page):\n        \"\"\"TC-CERT-005: 重置搜索条件\"\"\"\n        certificate_page.search_certificate(cert_name=\"test\")\n        certificate_page.reset_search()\n        # 重置后搜索框应为空\n        search_value = certificate_page.get_attribute(\n            CertificatePage.SEARCH_CERT_NAME, \"value\"\n        )\n        assert search_value == \"\", \"重置后搜索框应清空\"\n"}
</tool_response>

<tool_call>
{"name": "read_file", "arguments": {"path": "ZJSN_Test-master526/test/personnel/conftest.py"}}
</tool_call>
<tool_response>
{"status": "success", "content": "import pytest\nfrom page.personnel_page.CertificatePage import CertificatePage\nfrom page.personnel_page.DepartmentPage import DepartmentPage\nfrom page.personnel_page.PersonnelPage import PersonnelPage\nfrom page.personnel_page.TrainingRecordPage import TrainingRecordPage\n\n\n@pytest.fixture\ndef certificate_page(driver):\n    \"\"\"证书管理页面 fixture\"\"\"\n    page = CertificatePage(driver)\n    page.navigate()\n    yield page\n    # teardown: 无数据清理（证书为基础数据，由其他 fixture 依赖）\n\n\n@pytest.fixture\ndef department_page(driver):\n    \"\"\"部门管理页面 fixture\"\"\"\n    page = DepartmentPage(driver)\n    page.navigate()\n    yield page\n\n\n@pytest.fixture\ndef personnel_page(driver):\n    \"\"\"人员管理页面 fixture\"\"\"\n    page = PersonnelPage(driver)\n    page.navigate()\n    yield page\n\n\n@pytest.fixture\ndef training_record_page(driver):\n    \"\"\"培训记录页面 fixture\"\"\"\n    page = TrainingRecordPage(driver)\n    page.navigate()\n    yield page\n"}
</tool_response>

所有源文件已读取完毕，现在生成 PAGE_CONTEXT.md。

---

## 产出物：CertificatePage PAGE_CONTEXT.md

```markdown
# PAGE_CONTEXT: 证书管理页面 (CertificatePage)

> **模块**: personnel
> **页面**: certificate
> **最后更新**: 2026-06-17
> **状态**: ✅ PO + 测试均存在

---

## 1. 页面基本信息

| 属性 | 值 |
|------|----|
| 页面名称 | 证书管理 |
| Page Object 类 | `CertificatePage` |
| 文件路径 | `page/personnel_page/CertificatePage.py` |
| 路由 | `#/personnel/training/certificate` |
| 继承 | `BasePage` ✅ |
| 对应测试脚本 | `test/personnel/test_certificate.py` |

---

## 2. 页面功能区域划分

### 2.1 搜索区

| Locator 常量 | 策略 | 说明 |
|-------------|------|------|
| `SEARCH_CERT_NAME` | CSS | 按证书名称搜索输入框 |
| `SEARCH_STATUS` | CSS | 按状态筛选下拉（`.search-form .el-select`） |
| `SEARCH_BTN` | XPath | 查询按钮 |
| `RESET_BTN` | XPath | 重置按钮 |

### 2.2 操作按钮区

| Locator 常量 | 策略 | 说明 |
|-------------|------|------|
| `ADD_BTN` | XPath | 新增按钮 |
| `EDIT_BTN` | CSS | 表格内编辑按钮（`.el-button--primary`） |
| `DELETE_BTN` | CSS | 表格内删除按钮（`.el-button--danger`） |

### 2.3 表格区

| Locator 常量 | 策略 | 说明 |
|-------------|------|------|
| `TABLE_ROWS` | CSS | 表格行集合 |
| `TABLE_CERT_NAME` | CSS | 第 2 列：证书名称 |
| `TABLE_STATUS` | CSS | 第 4 列：状态 |

> **待确认**：第 1 列、第 3 列的含义未在 PO 中声明（推测为序号、证书类型，需页面观测确认）。

### 2.4 新增/编辑弹窗

| Locator 常量 | 策略 | 表单字段 |
|-------------|------|---------|
| `DIALOG_CERT_NAME` | CSS | 证书名称（必填，`请输入证书名称`） |
| `DIALOG_CERT_TYPE` | CSS | 证书类型（下拉，`.el-select`） |
| `DIALOG_VALIDITY` | CSS | 有效期（月，`请输入有效期（月）`） |
| `DIALOG_SAVE_BTN` | XPath | 保存按钮 |
| `DIALOG_CANCEL_BTN` | XPath | 取消按钮 |

### 2.5 删除确认弹窗

| Locator 常量 | 策略 | 说明 |
|-------------|------|------|
| `CONFIRM_DELETE_BTN` | CSS | 确认删除（`.el-message-box__btns .el-button--primary`） |
| `CANCEL_DELETE_BTN` | CSS | 取消删除 |

### 2.6 消息提示

| Locator 常量 | 策略 | 说明 |
|-------------|------|------|
| `SUCCESS_MSG` | CSS | 成功提示（`.el-message--success`） |
| `ERROR_MSG` | CSS | 错误提示（`.el-message--error`） |

---

## 3. 核心数据实体

**证书 (Certificate)**：

| 字段 | 来源 | 类型 | 备注 |
|------|------|------|------|
| 证书名称 | `DIALOG_CERT_NAME` | 文本输入 | 必填，测试前缀 `TC-` |
| 证书类型 | `DIALOG_CERT_TYPE` | 下拉选择 | 已知选项：`资质证书`（测试脚本中） |
| 有效期（月） | `DIALOG_VALIDITY` | 数字输入 | 单位：月 |
| 状态 | `TABLE_STATUS` / `SEARCH_STATUS` | 枚举 | 具体可选值待确认 |

---

## 4. 页面方法清单

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `navigate()` | — | `self` | 跳转到证书管理页面 |
| `search_certificate(cert_name, status)` | 均可选 | `self` | 按名称/状态搜索 |
| `reset_search()` | — | `self` | 重置搜索条件 |
| `add_certificate(cert_name, cert_type, validity)` | 均必填 | `self` | 填写弹窗并保存 |
| `edit_certificate(cert_name, cert_type, validity)` | 均可选 | `self` | 点击第一行编辑并保存 |
| `delete_certificate()` | — | `self` | 点击第一行删除并确认 |
| `get_first_row_cert_name()` | — | `str` | 获取表格第一行证书名称 |
| `is_success_message_shown()` | — | `bool` | 检查成功提示可见性 |
| `is_error_message_shown()` | — | `bool` | 检查错误提示可见性 |

---

## 5. 测试覆盖情况

| 测试用例 ID | 测试方法 | 覆盖场景 |
|------------|---------|---------|
| TC-CERT-001 | `test_add_certificate_success` | 新增证书正常流程 |
| TC-CERT-002 | `test_search_certificate` | 按名称搜索 |
| TC-CERT-003 | `test_edit_certificate_success` | 编辑证书正常流程 |
| TC-CERT-004 | `test_delete_certificate_success` | 删除证书正常流程 |
| TC-CERT-005 | `test_search_reset` | 重置搜索条件 |

**覆盖率评估**：
- ✅ CRUD 主流程均有覆盖（新增/搜索/编辑/删除）
- ❌ 未覆盖：按状态筛选、新增重复名称校验、必填项为空校验、取消操作、分页（如有）

---

## 6. Fixture 配置

```python
# conftest.py — certificate_page fixture
@pytest.fixture
def certificate_page(driver):
    page = CertificatePage(driver)
    page.navigate()
    yield page
    # teardown: 无数据清理
```

> ⚠️ **风险**：`certificate_page` fixture 无 teardown 清理。
> 注释说明"证书为基础数据，由其他 fixture 依赖"，但 `test_add_certificate_success` 创建了前缀为 `TC-` 的证书数据，未被自动清理。
> 违反项目数据管理红线：**谁创建，谁清理**。建议在 teardown 中按名称前缀 `TC-` 删除测试证书。

---

## 7. 页面级风险点

| 风险 | 等级 | 详情 |
|------|------|------|
| 无测试数据清理 | 🔴 高 | `certificate_page` fixture teardown 为空，`test_add_certificate_success` 遗留 `TC-自动化证书001` 脏数据 |
| 编辑/删除定位依赖行顺序 | 🟡 中 | `EDIT_BTN`/`DELETE_BTN` 取表格第一行按钮，无行定位逻辑，测试间有顺序依赖 |
| `SEARCH_STATUS` 定位器脆弱 | 🟡 中 | `.search-form .el-select` 若页面有多个 select 可能误命中，建议加更具体的属性选择器 |
| `DIALOG_CERT_TYPE` 下拉选项未文档化 | 🟡 中 | 仅从测试脚本知道 `资质证书` 一个选项，完整枚举值待页面观测确认 |
| 状态枚举值未知 | 🟡 中 | `TABLE_STATUS` 第 4 列和 `SEARCH_STATUS` 可选值均未在 PO 中声明 |
| `SEARCH_BTN`/`RESET_BTN` 使用 XPath | 🟢 低 | 当前为文本定位 XPath，非绝对路径，可接受，但优先级低于 CSS |

---

## 8. 待确认事项

- [ ] 表格第 1、3 列字段含义（需页面观测）
- [ ] `SEARCH_STATUS` / `TABLE_STATUS` 状态枚举的完整选项
- [ ] `DIALOG_CERT_TYPE` 证书类型下拉的完整选项
- [ ] 页面是否有分页组件
- [ ] 证书名称是否有唯一性约束（当前无重复校验用例）
- [ ] `certificate_page` fixture 不清理数据是否有意为之（基础数据策略需确认）
```

---

这份 PAGE_CONTEXT.md 完全基于代码扫描结果，主要发现：

1. **数据清理红线**：fixture teardown 为空，但测试中创建了 `TC-` 前缀数据，违反项目数据管理规范，这是最高优先级风险。
2. **行顺序依赖**：编辑和删除操作都锁定"第一行"，4 个测试用例之间存在隐式执行顺序依赖。
3. **覆盖缺口**：无异常路径测试（必填校验、重复名称等）。