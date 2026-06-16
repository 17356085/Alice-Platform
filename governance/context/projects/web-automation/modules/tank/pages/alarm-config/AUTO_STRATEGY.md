# AUTO_STRATEGY — tank/alarm-config

## 自动化策略

### 整体策略

| 策略项 | 决策 | 理由 |
|--------|------|------|
| 页面对象模式 | ✅ 采用 | 标准化复用，便于维护 |
| 定位器优先级 | XPath > CSS | Element Plus 表单用 label-following-sibling 最稳定 |
| 等待策略 | 显式等待 + Vue稳定 | Element Plus 异步渲染需要 |
| 测试数据管理 | 参数化 + Fixture | 灵活组合不同场景 |
| 断言层级 | 多层级降级 | UI → 响应码 → 接口响应 |

### 定位器策略

#### 1. 主要定位器设计

| 元素 | 定位策略 | 定位器 | 优先级 |
|------|---------|--------|--------|
| 弹窗容器 | CSS | `.el-dialog` | B |
| 弹窗标题 | XPath | `//span[contains(text(), '报警配置')]` | C |
| 报警类型下拉 | XPath | `//label[text()='报警类型']/following-sibling::div//input` | B |
| 报警邮箱输入 | XPath | `//label[text()='报警邮箱']/following-sibling::div//input` | B |
| 备注文本域 | XPath | `//label[text()='备注']/following-sibling::div//textarea` | B |
| 确定按钮 | XPath | `//button[.//span[text()='确 定']]` | B |
| 取消按钮 | XPath | `//button[.//span[text()='取消']]` | B |
| 下拉选项 | XPath | `//div[contains(@class, 'el-select-dropdown')]//span[text()='{option}']` | B |
| 错误提示 | XPath | `//div[contains(@class, 'el-form-item__error')]` | B |
| Toast 消息 | CSS | `.el-message` | B |

#### 2. 辅助定位器

| 场景 | 定位器 | 用途 |
|------|--------|------|
| 加载中 | `.el-loading-mask` | 等待加载完成 |
| 下拉展开 | `.el-select-dropdown` | 判断下拉是否展开 |
| 必填标记 | `//label[contains(@class, 'is-required')]` | 识别必填字段 |

### 等待策略

#### 1. 页面级等待

```python
# 弹窗出现等待
wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-dialog")))

# 弹窗关闭等待
wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-dialog")))

# Vue 渲染稳定（自定义方法）
def wait_vue_stable(self, timeout=10):
    """等待 Vue 渲染完成"""
    time.sleep(0.5)  # Vue 响应式更新延迟
```

#### 2. 元素级等待

| 操作 | 等待条件 | 超时 |
|------|---------|------|
| 点击下拉框 | `element_to_be_clickable` | 5s |
| 选择下拉选项 | `visibility_of_element_located` | 5s |
| 提交表单 | `invisibility_of_element_located(.el-loading-mask)` | 10s |
| Toast 消息 | `visibility_of_element_located(.el-message)` | 3s |

#### 3. 条件等待

```python
# 等待弹窗标题包含特定文本
wait.until(lambda d: '报警配置' in d.find_element(By.CSS_SELECTOR, ".el-dialog__title").text)

# 等待表单验证错误出现
try:
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-form-item__error")))
    has_error = True
except TimeoutException:
    has_error = False
```

### 操作策略

#### 1. 下拉框操作

Element Plus 的 el-select 需要特殊处理：

```python
def select_option(self, dropdown_locator, option_text):
    """选择下拉选项"""
    # 1. 展开下拉
    self.click(dropdown_locator)
    
    # 2. 等待下拉菜单出现
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-select-dropdown")))
    
    # 3. 点击选项（使用 JS 避免 overlay 遮挡）
    option_xpath = f"//div[contains(@class, 'el-select-dropdown')]//span[text()='{option_text}']"
    option = self.driver.find_element(By.XPATH, option_xpath)
    self.driver.execute_script("arguments[0].click();", option)
    
    # 4. 等待下拉收起
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-select-dropdown")))
```

#### 2. 表单提交

```python
def submit_form(self):
    """提交表单"""
    # 1. 点击确定按钮
    self.click(self.SAVE_BUTTON)
    
    # 2. 等待加载完成
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-loading-mask")))
    
    # 3. 捕获 Toast 消息
    try:
        toast = self.driver.find_element(By.CSS_SELECTOR, ".el-message")
        return toast.text
    except NoSuchElementException:
        return ""
```

#### 3. 弹窗关闭

```python
def close_dialog(self):
    """关闭弹窗"""
    # 优先点击取消按钮
    try:
        self.click(self.CANCEL_BUTTON)
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-dialog")))
    except:
        # 备选：点击遮罩层或 ESC 键
        self.driver.execute_script("document.querySelector('.el-overlay').click();")
```

### 测试数据策略

#### 1. 测试数据分层

| 层级 | 数据类型 | 用途 |
|------|---------|------|
| Fixture 数据 | 登录账号、基础配置 | 测试前置准备 |
| 参数化数据 | 不同输入组合 | 覆盖各种场景 |
| 临时数据 | 随机邮箱、备注 | 避免数据冲突 |
| 清理数据 | 测试后删除 | 保持环境清洁 |

#### 2. 测试数据示例

```python
# conftest.py fixture
@pytest.fixture
def alarm_config_data():
    """报警配置测试数据"""
    return {
        "valid": {
            "alarm_type": "液位报警",
            "alarm_email": "test@example.com",
            "remark": "自动化测试创建"
        },
        "invalid_email": {
            "alarm_type": "液位报警",
            "alarm_email": "invalid-email",
            "remark": "测试邮箱验证"
        },
        "missing_required": {
            "alarm_type": "",  # 必填为空
            "alarm_email": "test@example.com",
            "remark": "测试必填验证"
        }
    }
```

### 断言策略

#### 1. 多层级断言

```python
def assert_submit_success(self):
    """断言提交成功（多层级降级）"""
    # 层级1: Toast 消息
    try:
        toast = self.get_text((By.CSS_SELECTOR, ".el-message--success"))
        assert "成功" in toast or "保存" in toast
        return True
    except:
        pass
    
    # 层级2: 弹窗关闭
    try:
        is_closed = not self.is_visible((By.CSS_SELECTOR, ".el-dialog"))
        assert is_closed
        return True
    except:
        pass
    
    # 层级3: 表单列表更新（需要回到父页面）
    return False
```

#### 2. 表单验证断言

```python
def assert_validation_error(self, field_label, expected_error=None):
    """断言表单验证错误"""
    # 找到对应字段的错误提示
    error_xpath = f"//label[text()='{field_label}']/following-sibling::div//div[contains(@class, 'el-form-item__error')]"
    error_elem = self.driver.find_element(By.XPATH, error_xpath)
    actual_error = error_elem.text
    
    if expected_error:
        assert actual_error == expected_error
    else:
        assert actual_error != ""  # 只要有错误即可
```

### 异常处理策略

#### 1. 常见异常处理

| 异常场景 | 处理方式 |
|---------|---------|
| 元素未找到 | 重试 3 次 + 详细日志 |
| 弹窗未打开 | 检查父页面按钮是否可点击 |
| 下拉菜单未展开 | 使用 JS 强制展开 |
| Toast 未出现 | 检查是否在 iframe 中 |
| 网络超时 | 截图 + 记录当前状态 |

#### 2. 重试机制

```python
from selenium.common.exceptions import (NoSuchElementException, 
                                        TimeoutException, 
                                        StaleElementReferenceException)

def click_with_retry(self, locator, max_retries=3):
    """带重试的点击操作"""
    for attempt in range(max_retries):
        try:
            elem = self.driver.find_element(*locator)
            self.driver.execute_script("arguments[0].scrollIntoView();", elem)
            elem.click()
            return True
        except (StaleElementReferenceException, ElementClickInterceptedException) as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(1)
    return False
```

### 性能优化策略

| 优化项 | 策略 | 效果 |
|--------|------|------|
| 元素查找 | 缓存常用元素 | 减少 DOM 查询 |
| 等待时间 | 动态等待而非固定 sleep | 提升执行速度 |
| 数据清理 | 测试后立即清理 | 避免数据积累 |
| 并行执行 | 按页面分组 | 缩短总执行时间 |

### 代码规范

#### 1. 命名规范
- 类名: `TankAlarmConfigPage` (大驼峰)
- 方法名: `fill_form`, `submit_form` (小写下划线)
- 定位器: 大写下划线 `ALARM_TYPE_SELECT`

#### 2. 注释规范
- 类级注释: 页面用途和注意事项
- 方法级注释: 功能说明和参数描述
- 复杂逻辑: 行内注释说明

#### 3. 错误处理
- 所有外部操作都要 try-except
- 异常信息包含上下文（模块/页面/操作）
- 失败时截图保存

---

**生成时间**: 2026-06-14
**策略版本**: 1.0