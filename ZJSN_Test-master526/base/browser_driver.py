"""浏览器驱动管理 - BaseDriver + 登录状态保障 + Pytest Fixtures"""
import logging
import os
import shutil
import time

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from config import BASE_URL, BROWSER_CONFIG, DEFAULT_USERNAME, DEFAULT_PASSWORD

logger = logging.getLogger(__name__)


class BaseDriver:
    """浏览器驱动基类"""

    def __init__(self):
        self.driver = None
        self.base_url = BASE_URL
        self.download_dir = None

    def setup_driver(self, headless=False):
        """初始化 Chrome 浏览器驱动"""
        chrome_options = Options()
        chrome_options.page_load_strategy = BROWSER_CONFIG.get(
            "page_load_strategy", "eager"
        )

        # 下载目录配置
        self.download_dir = os.path.abspath(
            os.path.join(os.getcwd(), "downloads")
        )
        os.makedirs(self.download_dir, exist_ok=True)
        chrome_options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": self.download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            },
        )

        # 通用浏览器选项
        if BROWSER_CONFIG.get("maximize", True):
            chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        if BROWSER_CONFIG.get("headless", False):
            chrome_options.add_argument("--headless=new")

        # ChromeDriver 路径
        chromedriver_path = os.path.join(os.getcwd(), "chromedriver.exe")
        if os.path.exists(chromedriver_path):
            service = Service(executable_path=chromedriver_path)
        elif shutil.which("chromedriver"):
            service = Service()
        else:
            logger.info("chromedriver 由 Selenium 自动管理")
            service = Service()

        try:
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("ChromeDriver 启动成功")
        except Exception as e:
            logger.error("ChromeDriver 启动失败: %s", e)
            raise

        # 超时配置
        self.driver.set_page_load_timeout(
            BROWSER_CONFIG.get("page_load_timeout", 60)
        )
        self.driver.implicitly_wait(
            BROWSER_CONFIG.get("implicit_wait", 0)
        )

        # 下载行为配置
        try:
            self.driver.execute_cdp_cmd(
                "Page.setDownloadBehavior",
                {"behavior": "allow", "downloadPath": self.download_dir},
            )
        except Exception:
            pass
        try:
            setattr(self.driver, "download_dir", self.download_dir)
        except Exception:
            pass

        return self.driver

    def open_browser(self):
        """打开浏览器并访问基础 URL（带重试）"""
        if self.driver is None:
            self.setup_driver()

        logger.info("正在访问: %s", self.base_url)
        try:
            self.driver.set_page_load_timeout(
                BROWSER_CONFIG.get("page_load_timeout", 60)
            )
        except Exception:
            pass

        for attempt in range(1, 4):
            try:
                self.driver.get(self.base_url)
                logger.info("第 %d 次访问页面成功", attempt)
                break
            except TimeoutException:
                logger.warning("第 %d 次页面加载超时", attempt)
                self._stop_loading()
            except Exception as exc:
                logger.warning("第 %d 次页面访问异常: %s", attempt, exc)
                self._stop_loading()

            if attempt < 3:
                time.sleep(2)

        # 恢复页面加载超时
        try:
            self.driver.set_page_load_timeout(
                BROWSER_CONFIG.get("page_load_timeout", 60)
            )
        except Exception:
            pass

        # 等待 DOM 就绪
        self._wait_dom_ready()
        return self.driver

    def _stop_loading(self):
        """强制停止当前页面加载"""
        try:
            self.driver.execute_script("window.stop();")
        except Exception:
            pass

    def _wait_dom_ready(self, timeout=30):
        """等待页面 DOM 加载完成"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                state = self.driver.execute_script("return document.readyState;")
                if state == "complete":
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def get_wait(self, timeout=None):
        """获取显式等待对象"""
        if self.driver is None:
            raise RuntimeError("浏览器驱动未初始化，请先调用 open_browser()")
        from config import TIMEOUT_CONFIG

        t = timeout or TIMEOUT_CONFIG.get("explicit_wait", 10)
        return WebDriverWait(self.driver, t)

    def close_browser(self):
        """关闭浏览器"""
        if self.driver:
            logger.info("正在关闭浏览器...")
            try:
                self.driver.quit()
            except Exception:
                pass
            try:
                service = getattr(self.driver, "service", None)
                if service and hasattr(service, "stop"):
                    service.stop()
            except Exception:
                pass
            self.driver = None

    def get_current_url(self):
        if self.driver:
            return self.driver.current_url
        return None

    def get_title(self):
        if self.driver:
            return self.driver.title
        return None


# ==================================================================
#  登录状态保障函数
# ==================================================================

def ensure_logged_in(driver, username=None, password=None, timeout=60):
    """确保浏览器已登录到系统

    检测登录页 / 已登录状态，自动执行登录。
    可从 session-scoped fixture 或测试用例中调用。
    """
    username = username or DEFAULT_USERNAME
    password = password or DEFAULT_PASSWORD

    from page.system_page.LoginPage import LoginPage

    login_page = LoginPage(driver)

    def _load_base():
        try:
            driver.get(BASE_URL)
        except TimeoutException:
            logger.warning("登录页加载超时，继续等待前端渲染")
        except Exception:
            try:
                driver.refresh()
            except Exception:
                pass

    for attempt in range(1, 4):
        _load_base()
        try:
            # 等待页面稳定
            login_page.wait_page_ready(timeout=30)
        except Exception:
            pass

        # 已登录直接返回
        if login_page._is_already_logged_in():
            logger.info("检测到已登录状态")
            return True

        # 在登录页则执行登录
        if login_page.is_login_page():
            logger.info("检测到登录页，执行登录...")
            login_page.login(username, password)
            # 等待登录后导航完成——关键：必须等到 URL 离开 #/login
            try:
                WebDriverWait(driver, 30).until(
                    lambda d: "#/login" not in (d.current_url or "")
                )
                logger.info("登录后已跳转: %s", driver.current_url)
            except TimeoutException:
                logger.warning("登录后 30s 内未跳转，当前 URL: %s", driver.current_url)
            try:
                login_page.wait_page_ready(timeout=30)
                login_page.wait_vue_stable(timeout=10)
            except Exception:
                pass
            time.sleep(1)
            return True

        logger.warning("第 %d 次未检测到登录页或已登录页面，重试...", attempt)

    raise TimeoutException("无法确认登录状态：未检测到登录页或应用首页")


def login_as(driver, username, password=DEFAULT_PASSWORD, timeout=30):
    """以指定用户登录（支持多账号切换，供权限测试复用）

    已登录状态下直接返回 True。在登录页时输入凭据并等待跳转。
    3 次重试 + 已登录检测，兼容连续切换用户的场景。

    Args:
        driver: Selenium WebDriver 实例
        username: 目标用户名
        password: 密码（默认 DEFAULT_PASSWORD）
        timeout: 最大等待时间（秒）

    Returns:
        bool: 登录成功返回 True，否则返回 False
    """
    from page.system_page.LoginPage import LoginPage

    page = LoginPage(driver)

    # 导航到首页
    driver.get(BASE_URL)
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState;") == "complete"
        )
    except Exception:
        pass

    # 已登录则直接返回
    try:
        if page._is_already_logged_in():
            cur_hash = driver.execute_script("return window.location.hash;")
            if "#/login" not in cur_hash and "#" in cur_hash:
                logger.info("login_as: 已在登录状态 (%s)", username)
                return True
    except Exception:
        pass

    # 登录流程（3 次重试）
    for attempt in range(3):
        try:
            driver.get(BASE_URL)
            page.wait_login_form_ready(timeout=10)
            if page.is_login_page():
                page.input_username(username)
                page.input_password(password)
                # 点击登录按钮
                btns = driver.find_elements(
                    "xpath", "//button[.//span[contains(.,'登')]]"
                )
                if btns:
                    btns[0].click()
                else:
                    driver.execute_script(
                        "document.querySelector('.el-button--primary').click();"
                    )
                # 等待跳转
                try:
                    WebDriverWait(driver, 15).until(
                        lambda d: "#/login" not in (d.current_url or "")
                    )
                except Exception:
                    pass
                page.wait_vue_stable()
                logger.info("login_as: %s 登录成功", username)
                return True
            if page._is_already_logged_in():
                return True
        except Exception as e:
            logger.debug("login_as 第 %d 次重试: %s", attempt + 1, e)
            try:
                page.wait_vue_stable()
            except Exception:
                pass

    logger.warning("login_as: %s 登录失败（3次重试用尽）", username)
    return False
