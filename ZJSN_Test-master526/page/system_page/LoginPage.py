"""登录页面操作类 — CSS_SELECTOR 优先，Vue 异步渲染兼容

  登录页: http://8.136.215.171:8081/
  登录后: http://8.136.215.171:8081/#/welcome

==== 元素定位稳定性分析 ====

| 元素        | HTML class                        | 稳定性 | 判定依据                          |
|------------|-----------------------------------|--------|----------------------------------|
| 用户名输入框  | el-input__inner                   | ⚠️中等  | Element Plus 标准类，版本升级可能变 |
| 密码输入框   | el-input__inner                   | ⚠️中等  | 同上，且与用户名共用同一类，不唯一    |
| 登录按钮    | el-button el-button--primary      | ✅高   | Element Plus 标准类，框架保证      |
| 登录按钮    | login-btn                         | ❌不稳定 | 自定义类，前端重构可能改名/删除      |
| 表单容器    | login-form                        | ❌不稳定 | 自定义类，定位仅作辅助               |

==== 推荐 CSS_SELECTOR（优先使用语义属性）====

  用户名:   input[type="text"][placeholder*="账号"]
  密码:     input[type="password"]
  登录按钮:  .el-button--primary       （CSS 定位）
            + //button[contains(@class,"el-button--primary")][contains(.,"登")]  （XPath 保底）

==== 登录按钮点击失败原因分析 ====

  1. Element Plus 初始化 loading 遮罩 (.el-loading-mask) 在页面加载时覆盖全屏
  2. Vue reaction system 尚未完成 mounted 钩子，按钮事件绑定未就绪
  3. 按钮 type="button"（非 submit），依赖 Vue @click 事件，普通 click() 可能不触发
  4. Element Plus 按钮有 ripple 动画，动画期间 element_to_be_clickable 可能判定为不可点击
  5. 若前端在表单验证失败时 disabled 了按钮，Selenium 永久等待

  → 解决方案：BasePage.click() 已内置 4 级降级 + loading 遮罩等待
  → 第 4 级 MouseEvent dispatch 确保能触发 Vue @click 绑定

==== data-testid 建议 ====

  建议前端在以下元素添加 data-testid 属性：
    <input data-testid="login-username" placeholder="请输入账号" />
    <input data-testid="login-password" type="password" placeholder="请输入密码" />
    <button data-testid="login-submit" class="el-button--primary">登录</button>

  如果团队接受，定位器可简化为 [data-testid="login-submit"]，稳定且不受样式变更影响。
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage
from config import BASE_URL

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """登录页面 Page Object"""

    # ── 定位器（CSS_SELECTOR 优先，语义属性优先）──────────────────
    # 原则：
    #   1. CSS_SELECTOR > 相对 XPath
    #   2. 语义属性 (placeholder/type) > Element Plus class > 自定义 class
    #   3. 表单作用域限定避免歧义
    #   4. 不使用动态 ID（如 el-id-*）
    #   5. 不使用绝对路径（如 /html/body/...）

    # 用户名输入框 — 多个选择器取并集，提高命中率
    USERNAME_INPUT = (
        By.CSS_SELECTOR,
        'input[type="text"][placeholder*="账号"], '
        'input[type="text"][placeholder*="用户"], '
        'input:not([type="password"])[placeholder*="账号"], '
        'input[placeholder*="请输入账号"]',
    )

    # 密码输入框 — type="password" 是 HTML 标准属性，最稳定
    PASSWORD_INPUT = (By.CSS_SELECTOR, 'input[type="password"]')

    # 登录按钮 — CSS 优先（不依赖自定义类 login-btn）
    # 保底 XPath：按文本 + Element Plus 标准类，按钮文字含空格（"登 录"）用 contains
    LOGIN_BUTTON_CSS = (
        By.CSS_SELECTOR,
        'form .el-button--primary, '
        'button.el-button--primary, '
        '.el-button.el-button--primary',
    )
    LOGIN_BUTTON = (
        By.XPATH,
        '//button[contains(@class,"el-button--primary") and contains(.,"登")]',
    )

    # 已登录检测 — 侧边栏或首页特征
    APP_READY = (
        By.CSS_SELECTOR,
        '.el-menu, .sidebar-container, .app-main, '
        '.el-container .el-aside',
    )

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)
        self.wait = WebDriverWait(driver, self.timeout)

    # ==================================================================
    #  页面就绪
    # ==================================================================

    def wait_login_form_ready(self, timeout=30):
        """等待登录表单就绪 — 输入框可见且 loading 遮罩消失"""
        logger.info("等待登录表单就绪...")
        self._wait_loading_gone(timeout)
        self.find_visible(self.USERNAME_INPUT, timeout)
        self.find_visible(self.PASSWORD_INPUT, timeout=5)
        self.wait_vue_stable()
        logger.info("登录表单就绪")

    def is_login_page(self):
        """当前是否在登录页面"""
        return self.is_visible(self.USERNAME_INPUT, timeout=2)

    # ==================================================================
    #  原子操作
    # ==================================================================

    def input_username(self, username):
        """输入用户名"""
        self.input_text(self.USERNAME_INPUT, username)
        logger.info("已输入用户名")

    def input_password(self, password):
        """输入密码"""
        self.input_text(self.PASSWORD_INPUT, password)
        logger.info("已输入密码")

    def click_login_button(self):
        """点击登录按钮

        智能降级策略（BasePage.click 已内置）：
          1. 等待 loading 遮罩消失
          2. element_to_be_clickable 等待按钮可点击
          3. 原生 click() → 被拦截则等遮罩消失后重试
          4. JS click() → 绕过遮罩层
          5. MouseEvent dispatch → 确保触发 Vue @click 绑定
        """
        # 先尝试 CSS_SELECTOR，失败则用 XPath 保底
        try:
            self.click(self.LOGIN_BUTTON_CSS, timeout=10)
        except TimeoutException:
            logger.warning("CSS 定位登录按钮失败，尝试 XPath 保底")
            self.click(self.LOGIN_BUTTON, timeout=5)
        logger.info("已点击登录按钮")

    # ==================================================================
    #  完整登录流程
    # ==================================================================

    def login(self, username, password):
        """完整登录流程：检测状态 → 等待表单 → 输入 → 点击"""
        logger.info("========== 开始登录流程 ==========")

        if self._is_already_logged_in():
            logger.info("检测到已登录状态，跳过登录")
            return True

        self.wait_login_form_ready()

        self.input_username(username)
        self.input_password(password)
        self.click_login_button()

        # 等待登录完成
        self.wait_vue_stable()
        self.wait_overlay_gone(timeout=10)

        logger.info("========== 登录流程结束 ==========")
        return True

    # ==================================================================
    #  登录结果检测
    # ==================================================================

    def is_login_success(self, timeout=15):
        """判断登录是否成功（URL 跳转到 #/welcome 或首页元素出现）"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: "#/welcome" in (d.current_url or "")
                or self.is_visible(self.APP_READY, timeout=2)
            )
            return True
        except TimeoutException:
            return False

    def get_login_error_toast(self, timeout=5):
        """获取登录失败时的错误提示"""
        return self.get_toast(timeout) or self.get_form_error(timeout)

    # ==================================================================
    #  内部方法
    # ==================================================================

    def _is_already_logged_in(self):
        """检测是否已处于登录后状态"""
        try:
            url = self.driver.current_url or ""
            if "#/welcome" in url or "#/index" in url or "#/home" in url:
                return True
            if not url or url.rstrip("/") == BASE_URL.rstrip("/"):
                return False
            return self.is_visible(self.APP_READY, timeout=2)
        except Exception:
            return False

    def get_current_url(self):
        """获取当前 URL"""
        try:
            return self.driver.current_url or ""
        except Exception:
            return ""

    def wait_for_url_change(self, timeout=15):
        """等待 URL 跳转到 #/welcome（登录成功标志）"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: "#/welcome" in (d.current_url or "")
            )
            return True
        except TimeoutException:
            return False

    def is_app_loaded(self, timeout=10):
        """系统首页是否加载完成"""
        return self.is_visible(self.APP_READY, timeout)
