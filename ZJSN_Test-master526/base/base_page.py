"""BasePage - 企业级 Page Object 基类

封装通用操作，优先使用 CSS_SELECTOR，内置 Vue/Element Plus 异步渲染处理。
"""
import os
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)

from config import TIMEOUT_CONFIG

logger = logging.getLogger(__name__)


class BasePage:
    """Page Object 基类

    提供：
    - 智能等待（处理 Vue 异步渲染）
    - CSS_SELECTOR 优先的元素定位
    - Element Plus 弹窗/Toast/下拉框操作
    - 表格/分页通用操作
    - 统一日志输出
    """

    # ── 通用 Element Plus 定位器（子类无需重复定义）──────────────────
    DIALOG = (
        By.CSS_SELECTOR,
        '.el-dialog:not([style*="display: none"])',
    )
    DIALOG_TITLE = (
        By.CSS_SELECTOR,
        '.el-dialog:not([style*="display: none"]) .el-dialog__title',
    )
    DIALOG_SAVE = (
        By.CSS_SELECTOR,
        '.el-dialog:not([style*="display: none"]) .el-button--primary',
    )
    DIALOG_CANCEL = (
        By.CSS_SELECTOR,
        '.el-dialog:not([style*="display: none"]) .el-button:not(.el-button--primary), '
        '.el-dialog:not([style*="display: none"]) button:not(.el-button--primary)',
    )
    # 文本匹配保底（CSS 不支持文本筛选）
    DIALOG_SAVE_XPATH = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
        '//button[contains(@class,"el-button--primary")]',
    )
    DIALOG_CANCEL_XPATH = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
        '//button[not(contains(@class,"el-button--primary"))]//span[contains(normalize-space(.),"取消")]',
    )
    TOAST = (By.CSS_SELECTOR, '.el-message__content, .el-notification__content, .ep-message__content')
    TOAST_ERROR = (By.CSS_SELECTOR, '.el-message--error .el-message__content, .el-notification--error .el-notification__content')
    TOAST_SUCCESS = (By.CSS_SELECTOR, '.el-message--success .el-message__content')
    FORM_ERROR = (By.CSS_SELECTOR, '.el-form-item__error')
    LOADING_MASK = (By.CSS_SELECTOR, '.el-loading-mask')
    MESSAGE_BOX = (
        By.CSS_SELECTOR,
        '.el-message-box:not([style*="display: none"])',
    )
    MESSAGE_BOX_CONFIRM = (
        By.CSS_SELECTOR,
        '.el-message-box:not([style*="display: none"]) .el-button--primary',
    )
    DROPDOWN_OPTIONS = (
        By.CSS_SELECTOR,
        'body > .el-popper:not([style*="display: none"]) .el-select-dropdown__item:not(.is-disabled)',
    )
    TABLE_ROWS = (By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')
    TABLE_EMPTY = (By.CSS_SELECTOR, '.el-table__empty-text')
    TOTAL_COUNT = (By.CSS_SELECTOR, '.el-pagination__total')
    NEXT_PAGE = (By.CSS_SELECTOR, '.el-pagination .btn-next:not([disabled])')
    PREV_PAGE = (By.CSS_SELECTOR, '.el-pagination .btn-prev:not([disabled])')

    def __init__(self, driver, timeout=None):
        self.driver = driver
        self.timeout = timeout or TIMEOUT_CONFIG.get('explicit_wait', 10)
        self.wait = WebDriverWait(driver, self.timeout, poll_frequency=0.5)

    # ==================================================================
    #  侧边栏导航（委托给 SidebarNavigator）
    # ==================================================================

    def navigate_to(self, *menu_path):
        """通过侧边栏菜单导航到指定页面

        用法:
            self.navigate_to("系统管理", "字典管理")
            self.navigate_to("人员管理", "培训管理", "课程管理")
            self.navigate_to("控制台")
        """
        from base.sidebar_navigator import SidebarNavigator
        nav = SidebarNavigator(self.driver, self.timeout)
        return nav.navigate_to(*menu_path)

    def navigate_to_by_hash(self, href: str, label: str = ""):
        """直接通过 window.location.hash 导航（绕过侧边栏菜单文本匹配）

        适用场景：菜单文本有歧义（如"关键参数监控"同时存在于设备管理和DCS数据）

        实现：_ensure_on_welcome → set hash → wait page ready
        与 SidebarNavigator._navigate_by_js_hash 同逻辑
        """
        import time
        from selenium.webdriver.support.ui import WebDriverWait

        logger.info("Hash 导航: %s → %s", label, href)

        # Ensure on app base (not login page)
        for _ in range(3):
            h = self.driver.execute_script("return window.location.hash;")
            if h in ("", "#/", "#/welcome", "#/index"):
                break
            self.driver.execute_script("window.location.hash = '#/welcome';")
            time.sleep(0.5)

        # Set target hash
        self.driver.execute_script(f"window.location.hash = '{href}';")

        # Wait for hash to take effect (Vue Router)
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: href in d.execute_script("return window.location.hash;")
            )
        except Exception:
            logger.warning("hash 未在 10s 内生效，当前: %s",
                           self.driver.execute_script("return window.location.hash;"))

        self._wait_page_content_ready()
        return True

    def _wait_page_content_ready(self):
        """等待页面主要内容渲染完成"""
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.el-table, .el-card, .el-pagination, .stat-card'))
            )
        except Exception:
            pass
        time.sleep(0.5)

    # ==================================================================
    #  核心定位方法
    # ==================================================================

    def find(self, locator, timeout=None):
        """等待元素存在后返回单个元素"""
        t = timeout or self.timeout
        return WebDriverWait(self.driver, t).until(
            EC.presence_of_element_located(locator)
        )

    def find_visible(self, locator, timeout=None):
        """等待元素可见后返回"""
        t = timeout or self.timeout
        return WebDriverWait(self.driver, t).until(
            EC.visibility_of_element_located(locator)
        )

    def find_clickable(self, locator, timeout=None):
        """等待元素可点击后返回"""
        t = timeout or self.timeout
        return WebDriverWait(self.driver, t).until(
            EC.element_to_be_clickable(locator)
        )

    def find_all(self, locator):
        """返回所有匹配元素（不等待）"""
        return self.driver.find_elements(*locator)

    def find_in_parent(self, parent, locator, timeout=5):
        """在父元素内查找子元素

        每次重试都调用 parent.find_element 重新查找。
        若 parent 引用因 Vue 异步渲染变得 stale，
        WebDriverWait 机制会捕获 StaleElementReferenceException 并重试，
        但重试使用同一 stale 引用会持续失败，故增加显式重查询逻辑。
        """
        from selenium.common.exceptions import StaleElementReferenceException

        def _find(d):
            try:
                el = parent.find_element(*locator)
            except StaleElementReferenceException:
                # 父引用已 stale — 向上抛出让外层调用者处理
                # (调用者应使用 _get_dialog_form_item 已修复的版本)
                raise Exception("parent element is stale — caller should re-query")
            if not el.is_displayed():
                raise Exception("not visible")
            return el

        return WebDriverWait(self.driver, timeout).until(_find)

    # ==================================================================
    #  表格操作
    # ==================================================================

    def get_table_headers(self, min_columns=0, timeout=15):
        """JS提取表格表头（含重试，比XPath text更可靠应对Element Plus异步渲染）"""
        deadline = __import__('time').time() + timeout
        last = []
        for _ in range(20):
            try:
                headers = self.driver.execute_script("""
                    return Array.from(
                        document.querySelectorAll('.el-table__header-wrapper th .cell')
                    ).map(function(el) { return el.textContent.trim(); }).filter(Boolean);
                """)
                if headers and len(headers) >= min_columns:
                    if headers == last:
                        return headers  # 稳定了
                    last = headers
            except Exception:
                pass
            if __import__('time').time() > deadline:
                break
            __import__('time').sleep(0.8)
        return last  # 返回最后一次结果（即使不完整）

    # ==================================================================
    #  Vue 异步渲染处理
    # ==================================================================

    def wait_vue_stable(self, timeout=5):
        """等待 Vue 反应式更新和 Element Plus 动画完成（best-effort，永不抛异常）"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script(
                    "return document.querySelectorAll("
                    "'.el-fade-in-linear-enter-active,.el-fade-in-enter-active,"
                    ".el-zoom-in-center-enter-active,.el-collapse-transition'"
                    ").length === 0;"
                )
            )
        except Exception:
            pass  # JS 错误/超时均不阻塞流程

    def wait_overlay_gone(self, timeout=10):
        """等待 Element Plus 遮罩层（loading overlay）消失"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, '.el-overlay:not([style*="display: none"])')
                )
            )
        except TimeoutException:
            pass

    # ==================================================================
    #  智能交互操作（企业级：Vue 场景全覆盖）
    # ==================================================================

    def click(self, locator, timeout=None):
        """智能点击 — 逐级降级，覆盖 Vue 渲染/遮罩/拦截场景。

        执行顺序:
          1. 等待 loading 遮罩消失
          2. 等待元素可点击 (element_to_be_clickable)
          3. Selenium 原生 click()
          4. 被拦截 → 等待拦截元素消失后重试
          5. 仍失败 → JS click（绕过遮罩层）
          6. JS 也失败 → 派发 MouseEvent 模拟真实点击
        """
        t = timeout or self.timeout
        self._wait_loading_gone(t)

        el = self._wait_until_clickable_safe(locator, t)
        if el is None:
            raise TimeoutException(
                f"元素在 {t}s 内未变为可点击状态。"
                f"\n  定位器: {locator}"
                f"\n  {self._diagnose_element(locator)}"
            )

        self._scroll_into_view(el)
        self.wait_vue_stable()

        # 策略 1：Selenium 原生点击
        try:
            el.click()
            logger.debug("元素点击成功（原生 click）")
            return el
        except ElementClickInterceptedException as e:
            logger.warning("点击被拦截: %s", str(e)[:120])

        # 策略 2：等待拦截元素消失后重试原生点击
        try:
            self._wait_interceptor_gone()
            el = self.find_clickable(locator, timeout=3)
            el.click()
            logger.debug("元素点击成功（等待遮罩消失后重试）")
            return el
        except Exception:
            pass

        # 策略 3：JS 点击（绕过所有遮罩）
        try:
            self._js_click_el(el)
            logger.debug("元素点击成功（JS click）")
            return el
        except Exception:
            pass

        # 策略 4：派发完整鼠标事件链（终极手段）
        self._dispatch_click_events(el)
        logger.debug("元素点击成功（MouseEvent 派发）")
        return el

    def js_click(self, locator, timeout=None):
        """JavaScript 直接点击（绕过 Element Plus 弹层遮挡）"""
        el = self.find(locator, timeout)
        self._js_click_el(el)
        return el

    def input_text(self, locator, value, clear=True, timeout=None):
        """输入文本：自动清空 + 输入 + Vue 绑定触发"""
        el = self.find_clickable(locator, timeout)
        self._scroll_into_view(el)
        try:
            el.click()
        except Exception:
            self._js_click_el(el)
        if clear:
            el.send_keys(Keys.CONTROL + "a")
            el.send_keys(Keys.DELETE)
        if value:
            el.send_keys(value)
        time.sleep(TIMEOUT_CONFIG["micro_wait"])  # v-model 绑定同步
        return el

    def js_fill_input(self, locator, text, clear_first=True, timeout=None, fallback_send_keys=False):
        """JS 原生 setter 填充 — 解决 StaleElement + Vue 3 响应式兼容。

        使用 Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set
        而非 .value= 直接赋值，确保 Vue 3 的 Proxy/defineProperty 拦截生效。
        同时派发 input/change/compositionend 事件链，兼容 Element Plus 2.x。

        fallback_send_keys=True: JS 赋值后追加 send_keys 完整按键保底（创建对话框等必须触发 v-model 的场景）

        适用场景：弹窗输入框（避免 send_keys 导致的 StaleElement）、
                  大量文本输入（比 send_keys 快 10x+）

        Args:
            locator: 定位器元组
            text: 要输入的文本
            clear_first: 是否先清空
            timeout: 超时（秒）
            fallback_send_keys: 是否追加完整 send_keys 保底
        """
        el = self.find(locator, timeout)
        self.driver.execute_script("""
            var el = arguments[0];
            var text = arguments[1];
            var clear = arguments[2];

            // Vue 3 兼容：使用原生 value setter（Vue 3 Proxy 会拦截）
            var nativeSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            if (nativeSetter) {
                if (clear) { nativeSetter.call(el, ''); }
                nativeSetter.call(el, text);
            } else {
                // 降级：直接赋值（覆盖 el-input 内部 <input>）
                if (clear) { el.value = ''; }
                el.value = text;
            }

            // 完整事件链：确保 Vue 3 v-model + Element Plus 校验 都触发
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            // compositionend — Element Plus 中文输入法兼容
            el.dispatchEvent(new CompositionEvent('compositionend', { data: text, bubbles: true }));
            // focus+blur — 触发 el-form-item 校验
            el.focus(); el.blur();
        """, el, text, clear_first)
        # 保底：确保 Vue v-model 键盘事件链被触发
        from selenium.webdriver.common.keys import Keys
        try:
            el.click()
            if fallback_send_keys:
                # 完整 send_keys：先清空再逐字输入（触发完整 keyboard 事件链）
                el.send_keys(Keys.CONTROL + "a")
                el.send_keys(Keys.DELETE)
                el.send_keys(text)
            else:
                # 轻量保底：空格+退格触发 v-model 刷新
                el.send_keys(Keys.SPACE)
                el.send_keys(Keys.BACKSPACE)
        except Exception:
            pass
        self.wait_vue_stable()
        return el

    def js_fill_input_multi(self, locators, text, clear_first=True, timeout=None, fallback_send_keys=False):
        """多定位器 fallback 版 js_fill_input。返回成功的定位器。"""
        for loc in locators:
            try:
                return self.js_fill_input(loc, text, clear_first, timeout, fallback_send_keys)
            except Exception:
                self.wait_vue_stable()
                continue
        raise RuntimeError(f"js_fill_input_multi: 所有 {len(locators)} 个定位器均未找到元素")

    def get_text(self, locator, timeout=None):
        """获取元素文本（兼容 textContent）"""
        el = self.find_visible(locator, timeout)
        return el.text.strip() or el.get_attribute("textContent").strip()

    def get_attribute(self, locator, name, timeout=None):
        """获取元素属性值"""
        el = self.find(locator, timeout)
        return el.get_attribute(name)

    # ==================================================================
    #  状态判断
    # ==================================================================

    def is_visible(self, locator, timeout=3):
        """判断元素是否可见"""
        try:
            self.find_visible(locator, timeout)
            return True
        except (TimeoutException, Exception):
            return False

    def is_present(self, locator, timeout=3):
        """判断元素是否存在于 DOM"""
        try:
            self.find(locator, timeout)
            return True
        except (TimeoutException, Exception):
            return False

    def wait_until_gone(self, locator, timeout=None):
        """等待元素从 DOM 消失"""
        t = timeout or self.timeout
        WebDriverWait(self.driver, t).until(
            EC.invisibility_of_element_located(locator)
        )

    def wait_until_visible(self, locator, timeout=None):
        """等待元素可见（Vue 渲染后常用）"""
        return self.find_visible(locator, timeout)

    def wait_page_ready(self, timeout=30):
        """等待页面 DOM 加载完成"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            logger.warning("页面 DOM 未在 %ds 内加载完成", timeout)

    # ==================================================================
    #  Element Plus 弹窗操作
    # ==================================================================

    def _get_visible_dialog(self, timeout=None):
        """获取当前可见弹窗"""
        return self.find_visible(self.DIALOG, timeout)

    def wait_dialog_open(self, timeout=None):
        """等待弹窗出现"""
        self.wait_vue_stable()
        return self._get_visible_dialog(timeout)

    def is_dialog_visible(self):
        """判断当前弹窗是否可见"""
        try:
            return self.driver.find_element(*self.DIALOG).is_displayed()
        except Exception:
            return False

    def wait_dialog_close(self, timeout=None):
        """等待弹窗关闭"""
        t = timeout or self.timeout
        self.wait_until_gone(
            (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"])'),
            timeout=t,
        )
        self.wait_overlay_gone(timeout=3)

    def get_dialog_title(self, timeout=None):
        """获取弹窗标题文本"""
        return self.get_text(self.DIALOG_TITLE, timeout)

    def _get_dialog_form_item(self, label_text, timeout=10):
        """通过 label 文本定位弹窗表单项容器

        兼容三种表单布局：
        1. Element Plus 标准：div.el-form-item > label.el-form-item__label
        2. Element Plus 简化：div.el-form-item > * (任意子元素含文本)
        3. 自定义布局：div.info-item / div.form-item > label(纯文本)

        注意：每次重试都重新查询 dialog 元素，避免 Vue 异步重渲染导致
        WebElement 引用 stale 后 WebDriverWait 持续重试耗尽 timeout。
        """
        xpaths = [
            # 策略1：Element Plus 标准布局
            f'.//div[contains(@class,"el-form-item")]'
            f'[.//label[contains(@class,"el-form-item__label") and contains(normalize-space(.),"{label_text}")]]',
            # 策略2：Element Plus 简化（label 无特定 class）
            f'.//div[contains(@class,"el-form-item")]'
            f'[.//*[contains(normalize-space(.),"{label_text}")]]',
            # 策略3：自定义表单布局（如 info-item, form-item, form-group）
            f'.//*[contains(@class,"form-item") or contains(@class,"info-item") or contains(@class,"form-group")]'
            f'[.//label[contains(normalize-space(.),"{label_text}")]]',
            # 策略4：任意 label 的父容器
            f'.//label[contains(normalize-space(.),"{label_text}")]/..',
            # 策略5（新增）：包含文本的 span / div（可能无 label 标签）
            f'.//*[contains(normalize-space(.),"{label_text}")]//ancestor::div[contains(@class,"el-form-item")]',
        ]
        for idx, xp in enumerate(xpaths):
            try:
                item = WebDriverWait(self.driver, timeout).until(
                    lambda d: self._get_visible_dialog().find_element(By.XPATH, xp)
                )
                if item.is_displayed():
                    self._scroll_into_view(item)
                    logger.debug(f"✓ 表单项「{label_text}」定位成功 (策略 {idx+1})")
                    return item
            except Exception as e:
                logger.debug(f"✗ 策略 {idx+1} 失败: {e}")
                continue
        raise Exception(f"未找到弹窗表单项: {label_text}")

    def fill_dialog_input(self, label_text, value, clear=True):
        """在弹窗中通过 label 定位并填充输入框"""
        item = self._get_dialog_form_item(label_text)
        input_el = self.find_in_parent(
            item,
            (By.CSS_SELECTOR, 'input:not([disabled]), textarea:not([disabled])'),
        )
        self._scroll_into_view(input_el)
        try:
            input_el.click()
        except Exception:
            self._js_click_el(input_el)
        if clear:
            input_el.send_keys(Keys.CONTROL + "a")
            input_el.send_keys(Keys.DELETE)
        if value:
            input_el.send_keys(value)
        time.sleep(TIMEOUT_CONFIG["micro_wait"])
        logger.info("弹窗输入 [%s] = %s", label_text, value)

    def clear_dialog_input(self, label_text):
        """清空弹窗输入框"""
        self.fill_dialog_input(label_text, '', clear=True)

    def fill_dialog_field(self, label_text, value):
        """在弹窗中通过 label 定位并填充任意类型表单项

        自动识别: input/textarea → 文本填充
                  el-select     → 下拉选择
                  el-radio      → 单选选择
                  el-checkbox   → 勾选/取消
        """
        item = self._get_dialog_form_item(label_text)

        # 策略1: input / textarea (与 fill_dialog_input 相同选择器)
        try:
            input_el = self.find_in_parent(
                item,
                (By.CSS_SELECTOR, 'input:not([disabled]), textarea:not([disabled])'),
            )
            self._scroll_into_view(input_el)
            input_el.click()
            input_el.send_keys(Keys.CONTROL + "a")
            input_el.send_keys(Keys.DELETE)
            if value:
                input_el.send_keys(value)
            time.sleep(TIMEOUT_CONFIG["micro_wait"])
            logger.info("弹窗输入 [%s] = %s", label_text, value)
            return
        except Exception:
            pass

        # 策略2: el-select 下拉
        try:
            select = item.find_element(By.CSS_SELECTOR, '.el-select, .el-select__wrapper')
            if select.is_displayed():
                self._scroll_into_view(select)
                select.click()
                time.sleep(TIMEOUT_CONFIG["animate_wait"])
                self._select_option(value)
                logger.info("弹窗下拉 [%s] = %s", label_text, value)
                return
        except Exception:
            pass

        # 策略3: el-radio 单选组
        try:
            radios = item.find_elements(By.CSS_SELECTOR, '.el-radio, .el-radio__original, input[type="radio"]')
            for radio in radios:
                label = radio.find_element(By.XPATH, './/span[@class="el-radio__label"]') if radio.tag_name != 'label' else radio
                try:
                    label_text_of_radio = label.text.strip()
                except Exception:
                    continue
                if value in label_text_of_radio or label_text_of_radio in value:
                    self._js_click_el(radio)
                    time.sleep(TIMEOUT_CONFIG["micro_wait"])
                    logger.info("弹窗单选 [%s] = %s", label_text, value)
                    return
            # fallback: click by index if value is numeric
            if value.isdigit() and 0 <= int(value) - 1 < len(radios):
                self._js_click_el(radios[int(value) - 1])
                time.sleep(TIMEOUT_CONFIG["micro_wait"])
                logger.info("弹窗单选(索引) [%s] = #%s", label_text, value)
                return
        except Exception:
            pass

        raise Exception(f"未找到可填充的表单项: {label_text} (value={value})")

    def select_dialog_dropdown(self, label_text, option_text):
        """在弹窗中点击下拉框并选择指定选项"""
        item = self._get_dialog_form_item(label_text)
        # 找到下拉触发器
        select_xpaths = [
            './/div[contains(@class,"el-select__wrapper")]',
            './/div[contains(@class,"el-select")]',
            './/input',
        ]
        trigger = None
        for xp in select_xpaths:
            try:
                trigger = item.find_element(By.XPATH, xp)
                if trigger.is_displayed():
                    break
            except Exception:
                continue
        if not trigger:
            raise Exception(f"无法定位下拉触发器: {label_text}")

        self._scroll_into_view(trigger)
        time.sleep(TIMEOUT_CONFIG["micro_wait"])
        try:
            trigger.click()
        except Exception:
            self._js_click_el(trigger)
        time.sleep(TIMEOUT_CONFIG["animate_wait"])
        return self._select_option(option_text)

    def click_dialog_save(self, timeout=15):
        """点击弹窗保存/确定按钮（CSS → XPath → JS 文本搜索 三级降级）"""
        try:
            self.click(self.DIALOG_SAVE, timeout)
        except TimeoutException:
            try:
                logger.debug("CSS 定位弹窗保存按钮失败，使用 XPath 保底")
                self.js_click(self.DIALOG_SAVE_XPATH, timeout)
            except TimeoutException:
                logger.debug("XPath 定位失败，使用 JS 文本搜索兜底")
                result = self.driver.execute_script("""
                    var dialogs = document.querySelectorAll('.el-dialog:not([style*=\"display: none\"])');
                    for (var i = dialogs.length - 1; i >= 0; i--) {
                        var btns = dialogs[i].querySelectorAll('button');
                        for (var j = 0; j < btns.length; j++) {
                            var t = btns[j].textContent.trim();
                            if (t === '确定' || t === '保存' || t === '提交' || t === '确 定' || t === '保 存') {
                                btns[j].click();
                                return 'clicked:' + t;
                            }
                        }
                    }
                    // 最后的兜底：找最后一个弹窗的 primary 按钮
                    var allPrimary = document.querySelectorAll('.el-dialog:not([style*=\"display: none\"]) .el-button--primary');
                    if (allPrimary.length > 0) {
                        allPrimary[allPrimary.length - 1].click();
                        return 'clicked:primary-fallback';
                    }
                    return 'not_found';
                """)
                if result and result.startswith('clicked'):
                    logger.debug("JS兜底点击成功: %s", result)
                else:
                    raise TimeoutException("弹窗保存按钮未找到 (CSS/XPath/JS均失败)")
        self.wait_overlay_gone(timeout=5)
        self.wait_vue_stable()

    def click_dialog_cancel(self):
        """点击弹窗取消按钮（CSS_SELECTOR 优先 → XPath 保底）"""
        try:
            self.click(self.DIALOG_CANCEL)
        except TimeoutException:
            logger.debug("CSS 定位弹窗取消按钮失败，使用 XPath 保底")
            self.js_click(self.DIALOG_CANCEL_XPATH)
        self.wait_overlay_gone(timeout=TIMEOUT_CONFIG["dialog_close"])

    # ==================================================================
    #  Element Plus Toast / MessageBox
    # ==================================================================

    def get_toast(self, timeout=5):
        """获取 Toast 消息文本"""
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(self.TOAST)
            )
            return (el.text or '').strip()
        except TimeoutException:
            return ''

    def wait_for_toast_text(self, timeout=10, max_attempts=3):
        """轮询等待 Toast 消息出现并返回文本

        改进: 多轮重试 + 自适应等待

        Args:
            timeout: 单轮超时时间（秒）
            max_attempts: 最多尝试轮数

        Returns:
            str: Toast 消息文本，超时返回空字符串
        """
        for attempt in range(max_attempts):
            deadline = time.time() + timeout
            while time.time() < deadline:
                text = self.get_toast()
                if text:
                    logger.info(f"✓ 第 {attempt+1} 轮获取 Toast: {text}")
                    return text
                time.sleep(TIMEOUT_CONFIG["animate_wait"])  # 0.5s 轮询
            logger.warning(f"✗ 第 {attempt+1} 轮超时（{timeout}s），准备重试...")
            time.sleep(0.3)
        logger.warning(f"✗ 所有 {max_attempts} 轮重试均无 Toast，返回空字符串")
        return ''

    def get_form_error(self, timeout=3):
        """获取表单校验错误文本"""
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.FORM_ERROR)
            )
            return (el.text or '').strip()
        except TimeoutException:
            return ''

    def confirm_message_box(self, timeout=8):
        """确认 Element Plus MessageBox"""
        btn = self.find_clickable(self.MESSAGE_BOX_CONFIRM, timeout)
        self._js_click_el(btn)
        self.wait_overlay_gone(timeout=TIMEOUT_CONFIG["dialog_close"])

    def get_message_box_text(self, timeout=5):
        """获取 MessageBox 提示文本"""
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        '.el-message-box:not([style*="display: none"]) .el-message-box__message p',
                    )
                )
            )
            return (el.text or '').strip()
        except TimeoutException:
            return ''

    # ==================================================================
    #  下拉选择（已展开的）
    # ==================================================================

    def _select_option(self, option_text, timeout=5):
        """从已展开的下拉列表中选择选项"""
        time.sleep(TIMEOUT_CONFIG["animate_wait"])  # 等 Teleport 渲染完成
        option_xpaths = [
            # 匹配 Element Plus 2.x el-select__popper + el-select-dropdown 两种容器
            f'(//div[contains(@class,"el-select__popper") or contains(@class,"el-select-dropdown")]'
            f'[not(contains(@style,"display: none"))])[last()]'
            f'//li[not(contains(@class,"is-disabled")) and normalize-space(.)="{option_text}"]',
            f'//div[contains(@class,"el-select__popper") and not(contains(@style,"display: none"))]'
            f'//li[not(contains(@class,"is-disabled")) and normalize-space(.)="{option_text}"]',
            f'//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
            f'//li[not(contains(@class,"is-disabled")) and contains(normalize-space(.),"{option_text}")]',
            f'//body//li[@role="option" and contains(normalize-space(.),"{option_text}")]',
        ]
        for xp in option_xpaths:
            try:
                opt = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                self._js_click_el(opt)
                self.wait_vue_stable()
                logger.info("已选择下拉选项: %s", option_text)
                return
            except Exception:
                continue
        raise Exception(f"无法选择下拉选项: {option_text}")

    # ==================================================================
    #  表格操作
    # ==================================================================

    def get_table_row_count(self):
        """获取当前页表格行数"""
        try:
            return len(self.find_all(self.TABLE_ROWS))
        except Exception:
            return 0

    def get_column_data(self, col_index):
        """获取指定列（1-based）所有行数据"""
        try:
            cells = self.find_all(
                (
                    By.CSS_SELECTOR,
                    f'.el-table__body-wrapper tbody tr td:nth-child({col_index}) .cell',
                )
            )
            return [c.text.strip() for c in cells if c.text.strip()]
        except Exception:
            return []

    def get_first_row_data(self):
        """获取第一行所有列数据"""
        try:
            row = self.find_visible(self.TABLE_ROWS, timeout=5)
            cells = row.find_elements(By.TAG_NAME, 'td')
            return [c.text.strip() for c in cells]
        except Exception:
            return []

    def get_cell(self, row_index, col_index):
        """获取指定单元格文本"""
        try:
            rows = self.find_all(self.TABLE_ROWS)
            if row_index <= len(rows):
                cells = rows[row_index - 1].find_elements(By.TAG_NAME, 'td')
                if col_index <= len(cells):
                    return cells[col_index - 1].text.strip()
            return ''
        except Exception:
            return ''

    def click_row_button(self, row_identifier, button_text, max_retries=3):
        """在表格中查找包含指定文本的行，点击行内按钮

        改进: 增重试、更强的 XPath、强制滚动
        """
        for attempt in range(max_retries):
            try:
                xpath = (
                    f'//tr[contains(@class,"el-table__row")]'
                    f'[.//td[contains(translate(normalize-space(.), " ", ""), translate("{row_identifier}", " ", ""))]]'
                    f'//button[contains(.,"{button_text}")]'
                )
                btn = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                self._scroll_into_view(btn)
                time.sleep(TIMEOUT_CONFIG["micro_wait"])
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_vue_stable()
                logger.info(f"已点击行「{row_identifier}」的【{button_text}】按钮 (尝试 {attempt+1})")
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"第 {attempt+1} 次尝试失败，row_id={row_identifier}, btn={button_text}: {e}")
                    raise Exception(f"未找到表格行「{row_identifier}」中的按钮【{button_text}】: {e}")
                logger.warning(f"第 {attempt+1} 次尝试失败，准备重试... ({e})")
                time.sleep(0.5)

    def is_row_present(self, text):
        """判断表格中是否存在包含指定文本的行"""
        try:
            self.driver.find_element(
                By.XPATH,
                f'//tr[contains(@class,"el-table__row")]//td[contains(normalize-space(.),"{text}")]',
            )
            return True
        except Exception:
            return False

    # ==================================================================
    #  搜索 & 分页
    # ==================================================================

    # ── 搜索 & 分页按钮定位器 ──
    SEARCH_BUTTON_CSS = (
        By.CSS_SELECTOR,
        '.search-form .el-button--primary, '
        '.el-form .el-button--primary, '
        'button.el-button--primary .el-icon-search',
    )
    SEARCH_BUTTON_XPATH = (
        By.XPATH,
        '//button[contains(@class,"el-button--primary")]'
        '//span[contains(normalize-space(.),"搜索") or contains(normalize-space(.),"查询")]'
        '/parent::button',
    )
    RESET_BUTTON_CSS = (
        By.CSS_SELECTOR,
        '.search-form .el-button--default, '
        '.el-form .el-button:not(.el-button--primary)',
    )
    RESET_BUTTON_XPATH = (
        By.XPATH,
        '//button[not(contains(@class,"el-button--primary"))]'
        '//span[contains(normalize-space(.),"重置")]/parent::button',
    )

    def click_search_button(self, timeout=None):
        """点击搜索/查询按钮（CSS → XPath → JS文本搜索 三级降级）"""
        try:
            self.click(self.SEARCH_BUTTON_CSS, timeout)
        except TimeoutException:
            try:
                self.click(self.SEARCH_BUTTON_XPATH, timeout)
            except TimeoutException:
                self._js_click_by_text(["搜索", "查询", "Search"])
        self.wait_vue_stable()

    def click_reset_button(self):
        """点击重置按钮（CSS → XPath → JS文本搜索 三级降级）"""
        try:
            self.click(self.RESET_BUTTON_CSS)
        except TimeoutException:
            try:
                self.click(self.RESET_BUTTON_XPATH)
            except TimeoutException:
                self._js_click_by_text(["重置", "Reset"])
        self.wait_vue_stable()

    def _js_click_by_text(self, texts):
        """JS文本匹配点击按钮（兜底方案）"""
        texts_js = str(texts).replace("'", '"')
        self.driver.execute_script(f"""
            var btns = document.querySelectorAll('button');
            var targets = {texts_js};
            for (var i = 0; i < btns.length; i++) {{
                var t = btns[i].textContent.trim();
                for (var j = 0; j < targets.length; j++) {{
                    if (t.indexOf(targets[j]) !== -1) {{
                        btns[i].click();
                        return;
                    }}
                }}
            }}
        """)

    def get_total_count(self):
        """获取分页总数 (CSS 优先, JS 兜底 Element Plus 2.x)"""
        try:
            text = self.get_text(self.TOTAL_COUNT, timeout=3)
            if text:
                return int(''.join(filter(str.isdigit, text)))
        except (ValueError, TypeError, TimeoutException):
            pass
        # JS 兜底: 从 .el-pagination textContent 提取第一个数字
        try:
            result = self.driver.execute_script("""
                var pag = document.querySelector('.el-pagination');
                if (!pag) return '0';
                var nums = pag.textContent.match(/\\d+/g);
                return nums ? nums[nums.length - 1] : '0';
            """)
            return int(result)
        except (ValueError, TypeError):
            return 0

    def click_next_page(self):
        """点击下一页"""
        self.click(self.NEXT_PAGE, timeout=5)
        self.wait_vue_stable()

    def click_prev_page(self):
        """点击上一页"""
        self.click(self.PREV_PAGE, timeout=5)
        self.wait_vue_stable()

    # ==================================================================
    #  内部工具方法
    # ==================================================================

    def _scroll_into_view(self, element):
        """将元素滚动到可视区域中心"""
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                element,
            )
        except Exception:
            pass

    def _js_click_el(self, element):
        """JavaScript 点击（绕过元素遮挡和不可交互问题）"""
        self._scroll_into_view(element)
        time.sleep(TIMEOUT_CONFIG["animate_wait"])  # 等 scroll 动画完成
        self.driver.execute_script("arguments[0].click();", element)

    def _dispatch_click_events(self, element):
        """派发完整鼠标事件链，模拟真实点击并触发 Vue 事件绑定"""
        self._scroll_into_view(element)
        try:
            self.driver.execute_script("""
                var el = arguments[0];
                var opts = {bubbles: true, cancelable: true, view: window};
                el.dispatchEvent(new MouseEvent('mousedown', opts));
                el.dispatchEvent(new MouseEvent('mouseup', opts));
                el.dispatchEvent(new MouseEvent('click', opts));
                if (el.tagName === 'BUTTON' || el.type === 'submit') {
                    var form = el.closest('form');
                    if (form) form.dispatchEvent(new Event('submit', opts));
                }
            """, element)
        except Exception:
            self._js_click_el(element)

    @staticmethod
    def build_locator(by, value):
        """便捷构造定位器元组"""
        return (by, value)

    # ==================================================================
    #  诊断工具（排查定位/点击失败时使用）
    # ==================================================================

    def _wait_loading_gone(self, timeout=10):
        """等待所有 loading 遮罩层消失（Vue/Element Plus 初始化阶段常见）"""
        end = time.time() + timeout
        while time.time() < end:
            try:
                masks = self.driver.find_elements(
                    By.CSS_SELECTOR, '.el-loading-mask, .el-loading-parent--relative .el-loading-mask'
                )
                visible = []
                for m in masks:
                    try:
                        if m.is_displayed():
                            visible.append(m)
                    except Exception:
                        continue
                if not visible:
                    return True
            except Exception:
                pass
            time.sleep(0.3)
        return False

    def _wait_until_clickable_safe(self, locator, timeout):
        """安全等待元素可点击，超时返回 None 而非抛异常"""
        try:
            return WebDriverWait(self.driver, timeout, poll_frequency=0.3).until(
                EC.element_to_be_clickable(locator)
            )
        except TimeoutException:
            return None

    def _wait_interceptor_gone(self, timeout=5):
        """等待遮挡元素消失（loading / overlay / transition）"""
        end = time.time() + timeout
        while time.time() < end:
            interceptors = self.driver.find_elements(
                By.CSS_SELECTOR,
                '.el-loading-mask, '
                '.el-loading-spinner, '
                '.el-overlay:not([style*="display: none"]), '
                '.v-modal',
            )
            visible = False
            for el in interceptors:
                try:
                    if el.is_displayed():
                        visible = True
                        break
                except Exception:
                    continue
            if not visible:
                return True
            time.sleep(0.3)
        return False

    def _diagnose_element(self, locator):
        """诊断元素当前状态 — 排查为何无法点击/定位"""
        lines = []
        try:
            els = self.driver.find_elements(*locator)
            lines.append(f"匹配元素数量: {len(els)}")
            if not els:
                lines.append("→ 定位器匹配不到任何元素！请检查:")
                lines.append("  1. CSS class 是否由 Vue 动态生成（如 scoped data-v-xxx）")
                lines.append("  2. 元素是否在 iframe 或 Shadow DOM 内")
                lines.append("  3. 是否存在 v-if 条件未满足")
                return "\n  ".join(lines)
            for i, el in enumerate(els[:3]):  # 最多检查前 3 个
                tag = el.tag_name
                classes = el.get_attribute("class") or ""
                displayed = el.is_displayed()
                enabled = el.is_enabled()
                rect = el.rect if displayed else {}
                lines.append(
                    f"[{i}] <{tag}> class=\"{classes[:80]}\" "
                    f"displayed={displayed} enabled={enabled} "
                    f"size={rect.get('width', 0):.0f}x{rect.get('height', 0):.0f}"
                )
                if not displayed:
                    lines.append(f"  → 元素存在于 DOM 但不可见！检查 CSS display/visibility/opacity")
                if not enabled:
                    lines.append(f"  → 元素被禁用（disabled）！检查是否有 disabled 属性")
                if displayed and rect.get('width', 0) == 0:
                    lines.append(f"  → 元素尺寸为 0！可能被 CSS 隐藏或未渲染")
        except Exception as e:
            lines.append(f"诊断异常: {e}")
        return "\n  ".join(lines)

    def save_debug_snapshot(self, prefix="debug"):
        """保存诊断截图 + HTML 源码（兜底写入 artifacts/failures/，避免根目录污染）"""
        # 确保至少写入 artifacts/failures/，不污染项目根目录
        if not os.path.dirname(prefix):
            _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            _artifacts_dir = os.path.join(_project_root, "artifacts", "failures")
            os.makedirs(_artifacts_dir, exist_ok=True)
            prefix = os.path.join(_artifacts_dir, prefix)
        try:
            self.driver.save_screenshot(f"{prefix}.png")
            logger.info("诊断截图已保存: %s.png", prefix)
        except Exception:
            pass
        try:
            with open(f"{prefix}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            logger.info("诊断 HTML 已保存: %s.html", prefix)
        except Exception:
            pass

    def _check_overlay_covering(self, locator):
        """JS 检测是否有遮罩层遮挡目标元素（调试用）"""
        try:
            return self.driver.execute_script("""
                var target = document.querySelector(arguments[0]);
                if (!target) return 'element_not_found';
                var rect = target.getBoundingClientRect();
                var cx = rect.left + rect.width / 2;
                var cy = rect.top + rect.height / 2;
                var top = document.elementFromPoint(cx, cy);
                if (!top) return 'no_element_at_point';
                if (top === target) return 'element_on_top';
                return {
                    covering_element: top.tagName + '.' + (top.className || '').split(' ').slice(0,3).join('.'),
                    covering_zIndex: window.getComputedStyle(top).zIndex,
                    target_zIndex: window.getComputedStyle(target).zIndex
                };
            """, locator[1])
        except Exception as e:
            return f'js_error: {e}'

    # ==================================================================
    #  JS 表单交互助手 — 解决 Element Plus teleport + xpath 编码问题
    # ==================================================================

    def js_fill_by_placeholder(self, placeholder_contains: str, value: str) -> bool:
        """按 placeholder 填输入框 — JS 直接注入，绕过 xpath 中文编码 + teleport。

        遍历所有未隐藏的 input，匹配 placeholder 包含指定文本的字段，
        清空后填入 value，派发 input + change 事件（触发 Vue 数据绑定）。

        Args:
            placeholder_contains: placeholder 部分文本（如 "物品名称" 匹配 "请输入物品名称"）
            value: 要填入的值

        Returns:
            True 如果找到并填写成功，False 如果未找到匹配输入框
        """
        script = """
            var ph = arguments[0], val = arguments[1];
            var inputs = document.querySelectorAll('input:not([type="hidden"])');
            var dialogs = document.querySelectorAll('.el-dialog');
            // 优先搜索弹窗内的输入框
            var candidates = [];
            for (var d = 0; d < dialogs.length; d++) {
                if (dialogs[d].offsetParent === null) continue;
                var dInputs = dialogs[d].querySelectorAll('input:not([type="hidden"])');
                for (var i = 0; i < dInputs.length; i++) { candidates.push(dInputs[i]); }
            }
            // 弹窗内没找到则搜索全局
            if (candidates.length === 0) {
                for (var i = 0; i < inputs.length; i++) {
                    if (inputs[i].offsetParent !== null) candidates.push(inputs[i]);
                }
            }
            for (var j = 0; j < candidates.length; j++) {
                var p = candidates[j].getAttribute('placeholder') || '';
                if (p.indexOf(ph) >= 0) {
                    candidates[j].focus();
                    candidates[j].value = '';
                    candidates[j].value = val;
                    candidates[j].dispatchEvent(new Event('input', {bubbles: true}));
                    candidates[j].dispatchEvent(new Event('change', {bubbles: true}));
                    return p;
                }
            }
            return '';
        """
        result = self.driver.execute_script(script, placeholder_contains, value)
        self.wait_vue_stable()
        if not result:
            logger.warning("js_fill_by_placeholder: 未找到 placeholder 包含 '%s' 的输入框", placeholder_contains)
            return False
        logger.debug("js_fill_by_placeholder: '%s' → '%s'", placeholder_contains, value)
        return True

    def js_select_teleport_option(self, label: str, option_text: str) -> bool:
        """Element Plus teleport el-select 下拉选择 — JS 绕过 Selenium is_displayed() 缺陷。

        Element Plus 2.x 将 el-select 下拉列表 teleport 到 <body> 下，
        Selenium is_displayed() 对 teleport 元素返回 False。
        此方法用 JS 直接操作：找到弹窗内 label → 点击展开 → 在 body 下找选项并点击。

        Args:
            label: 表单项 label 文本（如 "报警类型"、"物品类型"）
            option_text: 下拉选项文本（如 "设备报警"、"一般"）

        Returns:
            True 如果成功选择，False 如果失败
        """
        script = """
            var label = arguments[0], option = arguments[1];
            // Step 1: 找到弹窗内对应 label 的 el-select 容器并点击展开
            var dlgs = document.querySelectorAll('.el-dialog');
            var clicked = false;
            for (var i = 0; i < dlgs.length; i++) {
                if (dlgs[i].offsetParent === null) continue;
                var labels = dlgs[i].querySelectorAll('label');
                for (var j = 0; j < labels.length; j++) {
                    if (labels[j].textContent.indexOf(label) >= 0) {
                        // 找到 label 的父级 el-form-item，在其中找 el-select
                        var formItem = labels[j].closest('.el-form-item');
                        if (!formItem) formItem = labels[j].parentElement;
                        var select = formItem.querySelector('.el-select');
                        if (select) {
                            select.click();
                            clicked = true;
                            break;
                        }
                    }
                }
                if (clicked) break;
            }
            if (!clicked) return 'no_select_found';
            // Step 2: 等下拉列表渲染后，在 body 下找到匹配选项并点击
            return new Promise(function(resolve) {
                setTimeout(function() {
                    var items = document.querySelectorAll(
                        '.el-select-dropdown:not([style*="display: none"]) .el-select-dropdown__item'
                    );
                    for (var k = 0; k < items.length; k++) {
                        if (items[k].textContent.indexOf(option) >= 0) {
                            items[k].click();
                            resolve('selected:' + items[k].textContent.trim());
                            return;
                        }
                    }
                    resolve('option_not_found');
                }, 300);
            });
        """
        try:
            result = self.driver.execute_script(script, label, option_text)
            self.wait_vue_stable()
            if result and 'selected' in str(result):
                logger.debug("js_select_teleport_option: '%s' → '%s'", label, option_text)
                return True
            logger.warning("js_select_teleport_option: '%s' → '%s' 失败: %s",
                           label, option_text, result)
            return False
        except Exception as e:
            logger.warning("js_select_teleport_option: 异常: %s", e)
            return False

    def js_click_button_in_dialog(self, button_text: str) -> bool:
        """在可见弹窗内查找并点击指定文本的按钮（JS 方式）。

        用于替代 DIALOG_SAVE/DIALOG_CANCEL 在特殊场景下失效的情况。

        Args:
            button_text: 按钮文本（如 "确定"、"取消"、"保存"）

        Returns:
            True 如果成功点击
        """
        script = """
            var text = arguments[0];
            var dlgs = document.querySelectorAll('.el-dialog');
            for (var i = 0; i < dlgs.length; i++) {
                if (dlgs[i].offsetParent === null) continue;
                var btns = dlgs[i].querySelectorAll('button');
                for (var j = 0; j < btns.length; j++) {
                    if (btns[j].textContent.indexOf(text) >= 0 &&
                        btns[j].offsetParent !== null) {
                        btns[j].click();
                        return 'clicked:' + btns[j].textContent.trim();
                    }
                }
            }
            return 'not_found';
        """
        result = self.driver.execute_script(script, button_text)
        self.wait_vue_stable()
        return 'clicked' in str(result)
