# 自动化编码强制规范

> **加载者**: automation-agent（必需）, project-agent（审计用）
> ⚠️ 以下为强制规范，code-consistency-checker Skill 将逐项检查。

## Page Object 规范

| 规则 | 说明 |
|------|------|
| **继承 BasePage** | 所有 Page Object 类必须继承 `base.base_page.BasePage` |
| **Locator 声明** | 定位器定义为类属性元组：`ELEMENT = (By.CSS_SELECTOR, ".selector")` |
| **CSS 优先** | 定位器选择顺序：CSS Selector > XPath（文字匹配）> 绝对 XPath（禁止） |
| **navigate() 唯一入口** | 每个 Page 类有唯一的导航入口方法 |
| **操作方法 return self** | 支持链式调用：`page.search("x").get_table_data()` |
| **操作方法无 assert** | Page Object 只操作页面，不包含测试断言 |
| **操作方法无 time.sleep ≥ 0.5s** | 使用 WebDriverWait 或 BasePage 内置等待方法 |
| **使用 self.logger** | 禁止使用 `print()`，使用 `logging.getLogger(__name__)` |

## 测试脚本规范

| 规则 | 说明 |
|------|------|
| **@allure 注解** | `@allure.epic/feature/story/severity` 注解必须完整 |
| **allure.step()** | 用 `with allure.step("描述")` 标记关键步骤 |
| **断言含描述** | `assert x == y, "失败时输出此描述"` |
| **测试方法独立** | 不依赖执行顺序 |
| **数据清理在 teardown** | fixture yield 后执行清理，清理失败只发 warning |
| **@pytest.mark.smoke** | 冒烟用例必须有标记 |
| **⚑ CRUD 必须注册清理** | 任何创建/修改数据的操作必须调用 `get_cleanup_tracker().register()` |

## 禁止模式

| 禁止 | 说明 | 替代方案 |
|------|------|----------|
| `driver.find_element()` 直接调用 | 测试用例中禁止直接使用 Selenium API | 通过 Page Object 方法操作 |
| `time.sleep()` | 禁止硬等待（≥0.5s） | WebDriverWait / BasePage 等待方法 |
| 绝对 XPath | 禁止 `/html/body/div[3]/...` 路径 | CSS Selector 或相对 XPath |
| 硬编码 URL/密码 | 禁止代码中写死 URL 或敏感信息 | `config.py` / `.env` |
| 无清理逻辑 | 测试数据必须清理 | fixture teardown |
| 直接继承 Object | Page Object 不继承 BasePage 直接使用 driver | 继承 BasePage |
| 无清理逻辑 | CRUD 测试创建数据但未注册 tracker | `get_cleanup_tracker().register(entity_type=..., entity_id=..., api_delete_url=...)` |

## 代码红线速查（9 条）

| # | ❌ 禁止 | ✅ 必须 |
|---|---------|--------|
| 1 | 不继承 BasePage | `class XxxPage(BasePage):` |
| 2 | 绝对 XPath | CSS Selector 或相对 XPath |
| 3 | `time.sleep(N)` 硬等待 | `self.wait_vue_stable()` / `WebDriverWait` |
| 4 | `print()` 调试输出 | `logger.info()` / `logger.warning()` |
| 5 | 不用 `navigate_to()` 导航 | `self.navigate_to("一级", "二级", ...)` |
| 6 | 重复/副本文件 | 确认后删除 Git 冲突恢复副本 |
| 7 | Page Object 含 assert | assert 只在测试脚本中 |
| 8 | 硬编码 URL/账号/密码 | `config.py` / `.env` |
| 9 | CRUD 测试无清理注册 | `get_cleanup_tracker().register(entity_type=..., entity_id=..., api_delete_url=...)` |

### 自检命令

```
grep -n "class \w\+:" <新文件>          # 确认继承 BasePage
grep -n "//\*\[@id=.app.\]" <新文件>     # 确认无绝对XPath (输出为空=通过)
grep -n "time.sleep" <新文件>            # 确认无硬等待
grep -n "print(" <新文件>                # 确认无print (输出为空=通过)
grep -L "cleanup_tracker\|get_cleanup_tracker" <测试文件>  # 确认有清理注册 (CRUD文件必须命中)
```

