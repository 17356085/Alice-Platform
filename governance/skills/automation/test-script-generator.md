# Skill: test-script-generator

## 目标
基于 Page Object 和测试用例（TEST_CASES），生成符合项目规范的 pytest 测试脚本。

## 输入
- Page Object 类定义（由 page-object-generator 产出）
- TEST_CASES.md（自动化覆盖范围内的用例）
- 模块 conftest.py（如已有）
- PROJECT_CONTEXT.md（§ 编码强制规范）

## 输出
- `test_<module>.py` 测试脚本（单文件）

## 规则
- `@allure.epic/feature/story/severity` 注解必须完整
- `with allure.step("描述")` 标记所有关键步骤
- `@pytest.mark.smoke` 标记冒烟用例
- 断言包含失败时的描述信息：`assert x == y, "失败原因"`
- 测试方法独立，不依赖执行顺序
- 数据清理在 fixture teardown 中完成
- 禁止在测试用例中直接使用 `driver.find_element`
- 禁止使用 `time.sleep`
- 禁止硬编码敏感信息（URL/密码）

## 依赖
- skills/automation/page-object-generator.md
- skills/testcase-design.md
- governance/context/projects/web-automation/PROJECT_CONTEXT.md（§ 编码强制规范）

## 边界
- 本 Skill 只生成测试脚本，不生成 Page Object（那是 page-object-generator 的职责）
- 附带生成 conftest.py（P1-2 合并自 conftest-generator）
- 不涉及已有测试脚本审查

---

## Prompt 模板

```text
基于以下 Page Object 和测试用例，生成 pytest 测试脚本。

## 输入
- PageObject：{{粘贴 PageObject 类定义}}
- TEST_CASES：{{粘贴自动化覆盖范围内的用例}}
- 现有 conftest.py：{{粘贴模块级 conftest.py}}

## 任务
生成 `test_{{模块}}.py`，要求：

### 测试类结构
```python
import pytest
import allure

@allure.epic("{{设备管理}}")
@allure.feature("{{设备报警配置}}")
class TestAlarmConfig:
    
    @allure.story("{{页面加载}}")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, {{alarm_config_page}}):
        """TC-ALARM-001: 页面正常加载"""
        with allure.step("导航到报警配置页"):
            {{alarm_config_page}}.navigate()
        with allure.step("验证页面核心元素"):
            assert {{alarm_config_page}}.is_table_visible(), "表格未加载"
    
    @allure.story("{{搜索功能}}")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_002_search_by_name(self, {{alarm_config_page}}):
        """TC-ALARM-002: 按报警名称搜索"""
        with allure.step("输入搜索关键词"):
            {{alarm_config_page}}.search("{{温度报警}}")
        with allure.step("验证搜索结果"):
            data = {{alarm_config_page}}.get_table_data()
            assert len(data) > 0, "搜索结果为空"
```

### 必须遵循的规范
- `@allure.epic/feature/story/severity` 注解完整
- `with allure.step()` 标记关键步骤
- `@pytest.mark.smoke` 标记冒烟用例
- `@pytest.mark.destructive` 标记破坏性用例（增删改）
- 断言包含失败时的描述信息
- 测试方法独立，不依赖执行顺序
- 数据清理在 fixture teardown 中完成

### 禁止事项
- 不要在测试用例中直接写 Selenium 代码（如 driver.find_element）
- 不要使用 time.sleep
- 不要硬编码敏感信息

### ⛔ 生成后自检（不可跳过）

代码生成后，**必须执行以下检查**：

```
═══ 代码自检报告 ═══
[PASS] 无 driver.find_element 直接调用
[PASS] 无 time.sleep
[PASS] 无 print()（仅在 Page Object 中为阻塞，测试脚本中为警告）
[PASS] @allure.epic/feature/story/severity 注解完整
[PASS] 断言含失败描述
════════════════════
结果: 通过 / 不通过
```

如果任何一项不通过，先修复再继续。```
```

---

## 检查清单

> 对照 coding-standards.md §测试脚本规范 + §禁止模式 逐项自检。所有项必须通过。
> 自检命令：`grep "time.sleep\|print(\|driver.find_element" <file>` → 必须为空（禁止模式）。

## 产出物
→ `script/<module>/test_<page>.py`
→ 编码规范参见 `PROJECT_CONTEXT.md` § 自动化编码强制规范。

---

## 附: conftest.py 生成 (P1-2 合并自 conftest-generator)

> P1-2 (2026-06-13): `conftest-generator` Skill 已合并到本 Skill。
> conftest.py 与测试脚本属于同一模块基础设施，单独拆分 Skill 粒度过细。

### 目标
为模块生成符合项目规范的 pytest conftest.py，包含 module 级 driver fixture 和 function 级 Page Object fixture。

### 规则
- Module scope driver 确保同一模块内共享浏览器实例
- fixture 中的 navigate() 保证页面就绪
- 数据清理在 teardown 中，清理失败只发 warning
- 复用 `BaseDriver.ensure_logged_in()` 保障登录状态
- fixture 命名规则：`<page_name>_page`

### Prompt 模板

```text
为 {{模块}} 生成 conftest.py。参考 script/equipment/conftest.py。

必须包含:
- @pytest.fixture(scope="module") driver_setup → BaseDriver().open_browser() → ensure_logged_in() → 导航逻辑
- 每个 Page Object 对应一个 @pytest.fixture(scope="module") fixture
- fixture 中执行 navigate() 确保页面就绪
- 数据清理在 finally/yield 后，清理失败只发 warning

参考路径:
- BaseDriver: base/browser_driver.py
- 参考实现: ZJSN_Test-master526/script/equipment/conftest.py
```

### 检查清单
- [ ] Module scope driver_setup fixture 存在
- [ ] ensure_logged_in() 在 driver_setup 中调用
- [ ] 每个 Page Object 对应一个 fixture
- [ ] fixture scope 正确（module 级）
- [ ] 数据清理逻辑在 finally 或 yield 后
- [ ] 清理失败只发 warning，不抛异常

### 产出物
→ `script/<module>/conftest.py`
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | automation | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->