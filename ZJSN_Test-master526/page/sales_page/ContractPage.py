"""合同管理页面 Page Object — 企业级

==== 页面概述 ====
  路径：销售管理 → 合同管理
  功能：管理与客户签订的购销合同，控制产品销售总量及有效期

==== 页面实际 HTML 结构（基于页面分析）====

  【搜索区】
    - ElementInput:  placeholder="合同编号"
    - ElementInput:  placeholder="客户名称"
    - ElementSelect: placeholder="产品类型"
    - ElementDatePicker (Range): placeholder="有效期起" ~ "有效期止"
    - ElementSelect: placeholder="合同状态"
    - ElementButton: "查询"
    - ElementButton: "重置"
    - ElementButton: "新增合同"

  【表格区】
    列: 合同编号 | 客户名称 | 产品 | 合同总量(吨) | 已执行量 | 有效期至 | 状态 | 操作
    - 已执行量列包含 ElementProgress（带 3s CSS 动画）
    - 状态列包含 ElementTag（el-tag--danger=已终止, el-tag--success=已完成）
    - 操作列: "详情"、"销售订单" 按钮

  【分页区】
    - 总条数、每页条数 Select、翻页按钮

==== 定位策略 ====
  1. CSS_SELECTOR：语义属性 > Element Plus 标准类
  2. XPath：仅用于文本匹配保底
  3. 禁止：绝对 XPath、动态 ID、scoped data-v 属性
  4. 弹窗过滤：始终使用 :not([style*="display: none"]) 排除隐藏弹窗

==== Vue/Element Plus 风险点 ====
  1. Select/DatePicker 面板通过 Teleport 挂载到 body，需等待面板可见
  2. 查询后表格异步加载，需等待 loading 遮罩消失
  3. 进度条有 3s CSS 动画，断言百分比需等待动画完成
  4. 翻页后 DOM 复用，需等待新数据渲染
"""
import json
import logging
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

from base.base_page import BasePage
from base.element_plus_helper import ElementPlusHelper
from config import BASE_URL, TIMEOUT_CONFIG

logger = logging.getLogger(__name__)


class ContractPage(BasePage):
    """合同管理页面"""

    # ==================================================================
    #  路由
    # ==================================================================
    PAGE_ROUTE = "#/sales/contract"

    # ==================================================================
    #  状态常量
    # ==================================================================
    STATE_TERMINATED = "已终止"
    STATE_COMPLETED = "已完成"

    # 状态 → ElementTag 类型映射
    STATUS_TAG_MAP = {
        STATE_TERMINATED: "danger",
        STATE_COMPLETED: "success",
    }

    # ==================================================================
    #  搜索区 — 定位器（CSS_SELECTOR 优先）
    # ==================================================================

    # -- 输入框：通过 placeholder 定位，最稳定 --
    SEARCH_CONTRACT_NO_INPUT = (
        By.CSS_SELECTOR, 'input[placeholder="合同编号"]'
    )
    SEARCH_CONTRACT_NO_XPATH = (
        By.XPATH, '//input[@placeholder="合同编号"]'
    )
    SEARCH_CUSTOMER_INPUT = (
        By.CSS_SELECTOR, 'input[placeholder="客户名称"]'
    )
    SEARCH_CUSTOMER_XPATH = (
        By.XPATH, '//input[@placeholder="客户名称"]'
    )

    # -- Select 选择器：通过 placeholder 文本定位 --
    # Element Plus 实际DOM结构: div.el-select__selected-item.el-select__placeholder > span
    SEARCH_PRODUCT_TYPE_SELECT = (
        By.XPATH,
        '//div[contains(@class,"el-select")]'
        '[.//div[contains(@class,"el-select__placeholder")]'
        '/span[contains(normalize-space(.),"产品类型")]]',
    )
    SEARCH_STATUS_SELECT = (
        By.XPATH,
        '//div[contains(@class,"el-select")]'
        '[.//div[contains(@class,"el-select__placeholder")]'
        '/span[contains(normalize-space(.),"合同状态")]]',
    )

    # -- 日期范围选择器 --
    SEARCH_START_DATE_INPUT = (
        By.CSS_SELECTOR, 'input[placeholder="有效期起"]'
    )
    SEARCH_START_DATE_XPATH = (
        By.XPATH, '//input[@placeholder="有效期起"]'
    )
    SEARCH_END_DATE_INPUT = (
        By.CSS_SELECTOR, 'input[placeholder="有效期止"]'
    )
    SEARCH_END_DATE_XPATH = (
        By.XPATH, '//input[@placeholder="有效期止"]'
    )

    # -- 按钮：XPath 文本匹配（最可靠）--
    BTN_SEARCH_XPATH = (
        By.XPATH,
        '//button[contains(@class,"el-button--primary")]'
        '//span[contains(normalize-space(.),"查询")]/parent::button',
    )
    BTN_RESET_XPATH = (
        By.XPATH,
        '//button[not(contains(@class,"el-button--primary"))]'
        '//span[contains(normalize-space(.),"重置")]/parent::button',
    )
    BTN_ADD_XPATH = (
        By.XPATH,
        '//button[contains(@class,"el-button")]'
        '//span[contains(normalize-space(.),"新增合同")]/parent::button',
    )
    # 保底：部分文本匹配（不含 primary class 限制，因为可能是 success 等变体）
    BTN_SEARCH_XPATH_FALLBACK = (
        By.XPATH,
        '//button[contains(@class,"el-button--primary") and contains(.,"查询")]',
    )
    BTN_RESET_XPATH_FALLBACK = (
        By.XPATH,
        '//button[not(contains(@class,"el-button--primary")) and contains(.,"重置")]',
    )
    BTN_ADD_XPATH_FALLBACK = (
        By.XPATH,
        '//button[contains(@class,"el-button") and contains(.,"新增")]',
    )

    # ==================================================================
    #  表格区 — 定位器
    # ==================================================================

    # -- 列索引常量（1-based，基于实际页面 HTML 分析）--
    COL_CONTRACT_NO = 1       # 合同编号
    COL_CUSTOMER_NAME = 2     # 客户名称
    COL_PRODUCT = 3           # 产品
    COL_TOTAL_QTY = 4         # 合同总量(吨)
    COL_EXECUTED_QTY = 5      # 已执行量（含 Progress 组件）
    COL_EXPIRE_DATE = 6       # 有效期至
    COL_STATUS = 7            # 状态（含 Tag 组件）
    COL_OPERATIONS = 8        # 操作（详情/销售订单 按钮）

    # -- 通用表格定位器（继承自 BasePage）--
    # TABLE_ROWS, TABLE_EMPTY, TOTAL_COUNT 已在 BasePage 定义

    # -- 进度条相关定位器 --
    PROGRESS_BAR_INNER = (
        By.CSS_SELECTOR, '.el-progress-bar__inner'
    )
    PROGRESS_TEXT = (
        By.CSS_SELECTOR,
        'tr.el-table__row td:nth-child(5) .cell span.text-xs'
    )

    # -- 状态标签定位器 --
    TAG_IN_ROW = (
        By.CSS_SELECTOR, 'span.el-tag'
    )
    TAG_DANGER = (By.CSS_SELECTOR, 'span.el-tag--danger')
    TAG_SUCCESS = (By.CSS_SELECTOR, 'span.el-tag--success')

    # -- 行内操作按钮 --
    BTN_DETAIL_XPATH = (
        By.XPATH, '//button[contains(.,"详情")]'
    )
    BTN_SALES_ORDER_XPATH = (
        By.XPATH, '//button[contains(.,"销售订单")]'
    )

    # ==================================================================
    #  构造
    # ==================================================================
    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)
        self._el_helper = ElementPlusHelper(driver, timeout)

    # ==================================================================
    #  导航
    # ==================================================================
    def navigate(self):
        """通过侧边栏导航至合同管理页面"""
        logger.info("导航到 → 合同管理 (%s)", self.PAGE_ROUTE)
        self.navigate_to("销售管理", "合同管理")
        self._wait_page_ready()

    def _wait_page_ready(self, timeout=15):
        """等待页面渲染完成"""
        self._wait_loading_gone(timeout)
        self.wait_vue_stable()
        self._el_helper.wait_table_ready(timeout)

    # ==================================================================
    #  搜索区操作
    # ==================================================================

    # ── 输入框 ──

    def input_contract_no(self, contract_no):
        """输入合同编号搜索条件（Vue安全：使用JS设置值+触发input事件）"""
        logger.info("搜索合同编号: %s", contract_no)
        if not contract_no:
            return
        self._fill_vue_input(['合同编号', '合同'], contract_no)

    def input_customer_name(self, customer_name):
        """输入客户名称搜索条件（Vue安全：使用JS设置值+触发input事件）"""
        logger.info("搜索客户名称: %s", customer_name)
        if not customer_name:
            return
        self._fill_vue_input(['客户名称', '客户'], customer_name)

    def _fill_vue_input(self, placeholder_keywords, value):
        """Vue安全输入：通过JS直接设置value并触发input事件以更新v-model

        Element Plus 的 el-input__wrapper 包裹层会拦截Selenium的click/send_keys，
        因此使用JS直接操作DOM并派发事件来触发Vue的响应式绑定。

        Args:
            placeholder_keywords: placeholder 匹配关键词列表（按优先级）
            value: 要输入的值
        """
        escaped_value = value.replace('\\', '\\\\').replace("'", "\\'")
        keywords_json = json.dumps(placeholder_keywords, ensure_ascii=False)  # 正确编码为JS数组

        js_code = f'''
            (function() {{
                try {{
                    var keywords = {keywords_json};
                    // 策略1: 标准 el-input__inner
                    var inputs = document.querySelectorAll('input.el-input__inner');
                    // 策略2: el-range-input (日期选择器)
                    if (!inputs.length) inputs = document.querySelectorAll('input.el-range-input');
                    // 策略3: 任意input
                    if (!inputs.length) inputs = document.querySelectorAll('input[type="text"]');
                    // 策略4: 所有input
                    if (!inputs.length) inputs = document.querySelectorAll('input');

                    for (var i = 0; i < inputs.length; i++) {{
                        var inp = inputs[i];
                        var ph = inp.placeholder || '';
                        var found = false;
                        for (var k = 0; k < keywords.length; k++) {{
                            if (ph.indexOf(keywords[k]) !== -1) {{ found = true; break; }}
                        }}
                        if (found) {{
                            // 尝试聚焦
                            try {{ inp.focus(); }} catch(e) {{}}
                            inp.value = '{escaped_value}';
                            inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            inp.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                            return 'filled:' + ph;
                        }}
                    }}
                    return 'not_found';
                }} catch(err) {{
                    return 'error:' + err.message;
                }}
            }})();
        '''
        try:
            result = self.driver.execute_script(js_code)
            logger.info("Vue输入填充结果: %s → %s", value, result or 'None/null')
            self.wait_vue_stable()  # 等 v-model 绑定响应

            # 验证输入值是否实际设置成功（execute_script可能返回None但值已设置）
            actual_value = self.driver.execute_script('''
                var inputs = document.querySelectorAll('input.el-input__inner');
                for (var i = 0; i < inputs.length; i++) {
                    var ph = inputs[i].placeholder || '';
                    var kw = ''' + json.dumps(placeholder_keywords, ensure_ascii=False) + ''';
                    for (var k = 0; k < kw.length; k++) {
                        if (ph.indexOf(kw[k]) !== -1) return inputs[i].value;
                    }
                }
                return null;
            ''')
            logger.info("Vue输入实际值验证: %s", actual_value)

            if actual_value and actual_value == value:
                # 值已正确设置，无需fallback
                logger.info("Vue输入填充成功（值已验证）")
                return

            # 值未设置或为空，尝试Selenium原生方式
            logger.warning("Vue输入值未生效(result=%s, actual=%s)，尝试Selenium原生方式", result, actual_value)
            for kw in placeholder_keywords:
                for loc in [
                    (By.CSS_SELECTOR, f'input[placeholder*="{kw}"]'),
                    (By.XPATH, f'//input[contains(@placeholder,"{kw}")]'),
                ]:
                    try:
                        self.input_text(loc, value)
                        logger.info("Selenium原生输入成功: %s", kw)
                        return
                    except Exception:
                        continue
            raise TimeoutException(f"无法定位输入框: keywords={placeholder_keywords}")
        except TimeoutException:
            raise
        except Exception as e:
            logger.error("Vue输入填充异常: %s", e)
            raise

    # ── 下拉选择器 ──

    def select_product_type(self, product_type):
        """选择产品类型筛选条件"""
        logger.info("筛选产品类型: %s", product_type)
        self._click_vue_select(self.SEARCH_PRODUCT_TYPE_SELECT, "产品类型", product_type)

    def select_status(self, status_text):
        """选择合同状态筛选条件"""
        logger.info("筛选合同状态: %s", status_text)
        self._click_vue_select(self.SEARCH_STATUS_SELECT, "合同状态", status_text)

    def _click_vue_select(self, select_locator, placeholder_text, option_text):
        """Vue安全的Select操作：先通过JS点击触发器，再选择选项

        解决Element Plus Select的焦点冲突问题：当输入框刚操作完，
        Select可能因焦点问题无法正常打开。使用JS直接click绕过。
        """
        # 策略1: JS点击Select触发器（绕过焦点冲突）
        try:
            js_result = self.driver.execute_script(f'''
                var selects = document.querySelectorAll('div.el-select');
                for (var i = 0; i < selects.length; i++) {{
                    // 兼容两种Element Plus Select placeholder结构
            var placeholderSpan = selects[i].querySelector('.el-select__placeholder span');
            if (!placeholderSpan) placeholderSpan = selects[i].querySelector('.el-select__selected-item span');
            if (!placeholderSpan) placeholderSpan = selects[i].querySelector('.el-select__placeholder');
                    var text = placeholder ? placeholder.textContent.trim() : '';
                    if (text.indexOf('{placeholder_text}') !== -1) {{
                        var input = selects[i].querySelector('input');
                        if (input) {{ input.focus(); input.click(); }}
                        selects[i].click();
                        return 'clicked';
                    }}
                }}
                return 'not_found';
            ''')
            if js_result == 'clicked':
                self.wait_vue_stable()  # 等下拉展开动画
                try:
                    self._select_option(option_text)
                    return
                except Exception:
                    pass  # JS click opened dropdown but option not found, try helper
            else:
                # JS没找到Select（页面异常），等1秒再试
                logger.debug("JS未找到Select '%s'，等待Vue稳定后重试", placeholder_text)
                self.wait_vue_stable()
        except Exception as e:
            logger.debug("JS点击Select失败: %s", e)

        # 策略2: Selenium点击
        try:
            self.click(select_locator, timeout=5)
            self.wait_vue_stable()  # 等下拉展开动画
            self._select_option(option_text)
            return
        except TimeoutException:
            pass
        except Exception:
            pass

        # 策略3: ElementPlusHelper保底
        logger.debug("使用ElementPlusHelper保底选择: %s → %s", placeholder_text, option_text)
        self._el_helper.select_option_by_placeholder(placeholder_text, option_text)

    # ── 日期范围 ──

    def input_date_range(self, start_date, end_date):
        """输入有效期日期范围

        Args:
            start_date: 开始日期（如 "2026-01-01"）
            end_date: 结束日期（如 "2026-12-31"）
        """
        logger.info("输入日期范围: %s ~ %s", start_date, end_date)
        self._el_helper.input_date_range(
            "有效期起", "有效期止", start_date, end_date
        )

    def clear_date_range(self):
        """清空日期范围搜索条件"""
        logger.info("清空日期范围")
        try:
            start_input = self.find_clickable(self.SEARCH_START_DATE_INPUT, timeout=3)
            start_input.clear()
        except TimeoutException:
            pass
        try:
            end_input = self.find_clickable(self.SEARCH_END_DATE_INPUT, timeout=3)
            end_input.clear()
        except TimeoutException:
            pass

    # ── 按钮操作 ──

    def click_search(self):
        """点击查询按钮，等待表格加载完成"""
        logger.info("点击查询按钮")
        # 多策略点击搜索按钮
        clicked = False
        search_strategies = [
            # 策略1: JS点击（绕过Element Plus遮挡）
            lambda: self.driver.execute_script("""
                var btns = document.querySelectorAll('button.el-button--primary');
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.indexOf('查询') !== -1 ||
                        btns[i].textContent.indexOf('搜索') !== -1) {
                        btns[i].click();
                        return true;
                    }
                }
                return false;
            """),
            # 策略2: XPath
            lambda: self.click(self.BTN_SEARCH_XPATH),
            # 策略3: 保底文本匹配
            lambda: self._el_helper.click_button_by_text("查询"),
        ]
        for i, strategy in enumerate(search_strategies):
            try:
                result = strategy()
                if result or result is None:
                    clicked = True
                    break
            except Exception:
                continue
        if not clicked:
            logger.warning("所有搜索按钮点击策略均失败")
        self._el_helper.wait_table_ready()

        # 验证搜索是否实际触发（如果没有loading效果，尝试Enter键触发）
        try:
            loading_check = self.driver.execute_script("""
                var loading = document.querySelector('.el-loading-mask');
                return loading && loading.offsetParent !== null;
            """)
            if not loading_check:
                # 无loading，尝试在合同编号输入框按Enter触发搜索
                logger.debug("未检测到loading状态，尝试Enter键触发搜索")
                self.driver.execute_script("""
                    var inputs = document.querySelectorAll('input.el-input__inner');
                    for (var i = 0; i < inputs.length; i++) {
                        if (inputs[i].value && inputs[i].offsetParent !== null) {
                            inputs[i].dispatchEvent(new KeyboardEvent('keydown', {key:'Enter', keyCode:13, bubbles:true}));
                            inputs[i].dispatchEvent(new KeyboardEvent('keyup', {key:'Enter', keyCode:13, bubbles:true}));
                            return 'enter_sent';
                        }
                    }
                    return 'no_input';
                """)
                self._el_helper.wait_table_ready()
        except Exception:
            pass

    def click_reset(self):
        """点击重置按钮，等待表格刷新"""
        logger.info("点击重置按钮")
        try:
            self.click(self.BTN_RESET_XPATH)
        except TimeoutException:
            logger.debug("精确 XPath 定位失败，使用保底定位")
            try:
                self.click(self.BTN_RESET_XPATH_FALLBACK)
            except TimeoutException:
                self._el_helper.click_button_by_text("重置")
        self._el_helper.wait_table_ready()

    def click_add(self):
        """点击新增合同按钮（JS优先，绕过Element Plus class变体问题）"""
        logger.info("点击新增合同按钮")
        # 策略1: JS点击（最可靠，不受class变体影响）
        result = self.driver.execute_script("""
            var btns = document.querySelectorAll('button.el-button');
            for (var i = 0; i < btns.length; i++) {
                var text = btns[i].textContent || '';
                if (text.indexOf('新增合同') !== -1 || text.indexOf('新增') !== -1) {
                    btns[i].click();
                    return 'clicked:' + text.trim();
                }
            }
            return 'not_found';
        """)
        if result and result.startswith('clicked'):
            logger.info("JS点击新增成功: %s", result)
        else:
            # 策略2: XPath保底
            logger.debug("JS未找到新增按钮，尝试XPath")
            try:
                self.click(self.BTN_ADD_XPATH)
            except TimeoutException:
                try:
                    self.click(self.BTN_ADD_XPATH_FALLBACK)
                except TimeoutException:
                    self._el_helper.click_button_by_text("新增合同")
        self.wait_vue_stable()
        # 确保弹窗已打开
        try:
            self.wait_dialog_open(timeout=8)
        except TimeoutException:
            logger.warning("弹窗未在 8s 内打开，尝试继续")

    # ── 组合搜索 ──
    @staticmethod
    def _has_text(value):
        """判断值是否为非空字符串"""
        return bool(value)

    # ── 批量设置搜索条件 ──

    def clear_all_search(self):
        """清空所有搜索条件（通过点击重置按钮）"""
        logger.info("清空所有搜索条件")
        self.click_reset()

    def set_search_conditions(self, *,
                               contract_no=None,
                               customer_name=None,
                               product_type=None,
                               start_date=None,
                               end_date=None,
                               status=None):
        """批量设置搜索条件（不点击查询）

        Args:
            contract_no: 合同编号
            customer_name: 客户名称
            product_type: 产品类型
            start_date: 有效期起
            end_date: 有效期止
            status: 合同状态
        """
        if contract_no is not None:
            self.input_contract_no(contract_no)
        if customer_name is not None:
            self.input_customer_name(customer_name)
        if product_type is not None:
            self.select_product_type(product_type)
        if start_date is not None and end_date is not None:
            self.input_date_range(start_date, end_date)
        elif start_date is not None:
            self.input_date_range(start_date, "")
        elif end_date is not None:
            self.input_date_range("", end_date)
        if status is not None:
            self.select_status(status)

    def search(self, **kwargs):
        """组合搜索：设置条件 → 点击查询

        用法:
            page.search(contract_no="HT20260527")
            page.search(customer_name="贵州", status="已完成")
            page.search(product_type="LNG", start_date="2026-01-01", end_date="2026-12-31")
        """
        self.set_search_conditions(**kwargs)
        self.wait_vue_stable()  # 等 v-model 更新 + input 事件处理
        self.click_search()

    # ==================================================================
    #  表格数据获取
    # ==================================================================

    def get_table_row_count(self):
        """获取当前页可见数据行数（StaleElement 安全）"""
        self._el_helper.wait_table_ready()
        try:
            rows = self.find_all(self.TABLE_ROWS)
            count = 0
            for r in rows:
                try:
                    if r.is_displayed():
                        count += 1
                except StaleElementReferenceException:
                    # DOM 被 Vue 重新渲染，重新获取
                    pass
            return count
        except Exception:
            # 完全重新获取
            self._el_helper.wait_table_ready()
            rows = self.find_all(self.TABLE_ROWS)
            count = 0
            for r in rows:
                try:
                    if r.is_displayed():
                        count += 1
                except StaleElementReferenceException:
                    pass
            return count

    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）"""
        for attempt in range(6):
            try:
                self._wait_table_ready() if hasattr(self, '_wait_table_ready') else self._wait_loading_gone(timeout=2)
            except:
                self._wait_loading_gone(timeout=2)
            self.wait_vue_stable()
            headers = self.driver.execute_script("""
                return Array.from(
                    document.querySelectorAll('.el-table__header-wrapper th .cell')
                ).map(function(el) { return el.textContent.trim(); }).filter(Boolean);
            """)
            if headers and len(headers) >= 3:
                return headers
            self._wait_loading_gone(timeout=2)
        return []
    def get_row_by_contract_no(self, contract_no, timeout=5):
        """根据合同编号获取表格行元素

        Args:
            contract_no: 合同编号
            timeout: 超时时间

        Returns:
            WebElement 或 None
        """
        self._el_helper.wait_table_ready()
        return self._el_helper.get_table_row_by_cell_text(contract_no, timeout)

    def is_contract_present(self, contract_no, timeout=3):
        """检查指定合同编号是否存在于当前表格

        Args:
            contract_no: 合同编号
            timeout: 超时时间

        Returns:
            bool: 是否存在
        """
        return self.get_row_by_contract_no(contract_no, timeout) is not None

    # ── 列数据获取 ──

    def get_contract_no_list(self):
        """获取当前页所有合同编号"""
        self._el_helper.wait_table_ready()
        return self.get_column_data(self.COL_CONTRACT_NO)

    def get_customer_name_list(self):
        """获取当前页所有客户名称"""
        self._el_helper.wait_table_ready()
        return self.get_column_data(self.COL_CUSTOMER_NAME)

    def get_status_list(self):
        """获取当前页所有合同状态文本"""
        self._el_helper.wait_table_ready()
        return self.get_column_data(self.COL_STATUS)

    def get_cell_text_by_contract_no(self, contract_no, col_index):
        """根据合同编号获取指定列单元格文本

        Args:
            contract_no: 合同编号
            col_index: 列索引（1-based）

        Returns:
            str: 单元格文本，未找到返回空字符串
        """
        row = self.get_row_by_contract_no(contract_no)
        if row:
            return self._el_helper.get_cell_value(row, col_index)
        return ""

    def get_status_by_contract_no(self, contract_no):
        """获取指定合同的状态文本"""
        return self.get_cell_text_by_contract_no(contract_no, self.COL_STATUS)

    def get_product_by_contract_no(self, contract_no):
        """获取指定合同的产品类型"""
        return self.get_cell_text_by_contract_no(contract_no, self.COL_PRODUCT)

    # ── 进度条相关 ──

    def get_progress_percentage_by_contract_no(self, contract_no, timeout=8):
        """获取指定合同的进度条百分比

        处理 Element Plus Progress 3s 动画：轮询等待宽度值稳定后返回。

        Args:
            contract_no: 合同编号
            timeout: 超时时间（应大于 3s 动画时长）

        Returns:
            float: 进度百分比（0-100），未找到返回 -1
        """
        row = self.get_row_by_contract_no(contract_no)
        if not row:
            logger.warning("未找到合同行: %s", contract_no)
            return -1.0

        try:
            # 在行的已执行量列中查找进度条
            progress_bar = row.find_element(
                By.CSS_SELECTOR,
                f'td:nth-child({self.COL_EXECUTED_QTY}) .el-progress-bar__inner'
            )
            return self._el_helper.get_progress_percentage(progress_bar, timeout)
        except Exception:
            logger.warning("合同 %s 的进度条元素未找到", contract_no)
            return -1.0

    def get_progress_text_by_contract_no(self, contract_no):
        """获取指定合同的进度文本（如 "100%"、"0%"）

        Args:
            contract_no: 合同编号

        Returns:
            str: 进度文本，未找到返回空字符串
        """
        row = self.get_row_by_contract_no(contract_no)
        if not row:
            return ""
        try:
            progress_text_el = row.find_element(
                By.CSS_SELECTOR,
                f'td:nth-child({self.COL_EXECUTED_QTY}) .cell span.text-xs'
            )
            return (progress_text_el.text or '').strip()
        except Exception:
            # 尝试从进度条 style 中提取
            pct = self.get_progress_percentage_by_contract_no(contract_no)
            if pct >= 0:
                return f"{pct:.0f}%"
            return ""

    def verify_progress_consistency(self, contract_no):
        """验证进度条宽度与文本百分比一致

        Element Plus Progress 的进度条宽度（style="width: X%"）应与
        显示文本一致。此方法同时获取两者并比较。

        Args:
            contract_no: 合同编号

        Returns:
            tuple: (pct_from_bar, pct_from_text, is_consistent)
        """
        bar_pct = self.get_progress_percentage_by_contract_no(contract_no)
        text = self.get_progress_text_by_contract_no(contract_no)

        # 从文本中提取百分比数值（优先匹配括号内的百分比，如 "15 / 15 吨 (100%)" → 100）
        text_pct = -1.0
        if text:
            # 策略1: 提取括号内的百分比
            pct_match = re.search(r'\((\d+(?:\.\d+)?)\s*%\)', text)
            if pct_match:
                text_pct = float(pct_match.group(1))
            else:
                # 策略2: 提取纯数字百分比 "100%"
                pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
                if pct_match:
                    text_pct = float(pct_match.group(1))
                else:
                    # 策略3: 提取第一个数字
                    nums = re.findall(r'[\d.]+', text)
                    if nums:
                        text_pct = float(nums[0])

        is_consistent = abs(bar_pct - text_pct) < 1.0 if bar_pct >= 0 and text_pct >= 0 else False
        logger.info("合同 %s 进度一致性: bar=%.1f%%, text='%s' (%.1f%%), 一致=%s",
                     contract_no, bar_pct, text, text_pct, is_consistent)
        return bar_pct, text_pct, is_consistent

    # ── 状态标签相关 ──

    def get_status_tag_type_by_contract_no(self, contract_no):
        """获取指定合同的状态标签类型

        Args:
            contract_no: 合同编号

        Returns:
            str: 'danger', 'success', 'info', 'warning', 'primary' 或 'unknown'
        """
        row = self.get_row_by_contract_no(contract_no)
        if not row:
            return 'unknown'
        try:
            tag = row.find_element(
                By.CSS_SELECTOR,
                f'td:nth-child({self.COL_STATUS}) span.el-tag'
            )
            return self._el_helper.get_tag_type(tag)
        except Exception:
            return 'unknown'

    def verify_status_tag(self, contract_no, expected_status):
        """验证合同的状态标签类型与状态文本匹配

        Args:
            contract_no: 合同编号
            expected_status: 预期状态文本（如 "已完成"、"已终止"）

        Returns:
            tuple: (actual_status, tag_type, is_correct)
        """
        actual_status = self.get_status_by_contract_no(contract_no)
        tag_type = self.get_status_tag_type_by_contract_no(contract_no)
        expected_tag_type = self.STATUS_TAG_MAP.get(actual_status, 'unknown')
        is_correct = (tag_type == expected_tag_type)
        logger.info("合同 %s 状态标签: status='%s', tag='%s', expected='%s', 正确=%s",
                     contract_no, actual_status, tag_type, expected_tag_type, is_correct)
        return actual_status, tag_type, is_correct

    # ==================================================================
    #  表格行内操作
    # ==================================================================

    def click_detail_by_contract_no(self, contract_no):
        """点击指定合同的详情按钮

        Args:
            contract_no: 合同编号
        """
        logger.info("查看合同详情: %s", contract_no)
        self._el_helper.click_row_button(contract_no, "详情")

    def click_sales_order_by_contract_no(self, contract_no):
        """点击指定合同的销售订单按钮

        Args:
            contract_no: 合同编号
        """
        logger.info("查看销售订单: %s", contract_no)
        self._el_helper.click_row_button(contract_no, "销售订单")

    def is_detail_button_present(self, contract_no, timeout=3):
        """检查详情按钮是否存在"""
        return self._is_row_button_present(contract_no, "详情", timeout)

    def is_sales_order_button_present(self, contract_no, timeout=3):
        """检查销售订单按钮是否存在"""
        return self._is_row_button_present(contract_no, "销售订单", timeout)

    # ==================================================================
    #  分页操作
    # ==================================================================

    def get_total_count_text(self):
        """获取分页总条数文本（如 "共 4 条"）"""
        return self._el_helper.get_pagination_total()

    def get_total_count(self):
        """获取分页总条数（纯数字）

        Returns:
            int: 总条数，解析失败返回 0
        """
        return self._el_helper.get_pagination_total_number()

    def select_page_size(self, size_text="10条/页"):
        """切换每页条数

        Args:
            size_text: 如 "10条/页"、"20条/页"、"50条/页"
        """
        self._el_helper.select_page_size(size_text)
        self._el_helper.wait_table_ready()

    def click_next_page(self):
        """点击下一页并等待渲染"""
        logger.info("点击下一页")
        self._el_helper.click_next_page()
        self._el_helper.wait_table_ready()

    def click_prev_page(self):
        """点击上一页并等待渲染"""
        logger.info("点击上一页")
        self._el_helper.click_prev_page()
        self._el_helper.wait_table_ready()

    def is_next_page_enabled(self):
        """检查下一页按钮是否可用"""
        return self._el_helper.is_next_page_enabled()

    def is_prev_page_enabled(self):
        """检查上一页按钮是否可用"""
        return self._el_helper.is_prev_page_enabled()

    # ==================================================================
    #  验证方法
    # ==================================================================

    def verify_search_result_count(self, expected_min=0, expected_max=None):
        """验证搜索结果数量

        Args:
            expected_min: 最小期望条数
            expected_max: 最大期望条数（None 表示不限制）

        Returns:
            tuple: (row_count, total_count, is_valid)
        """
        row_count = self.get_table_row_count()
        total_count = self.get_total_count()
        is_valid = row_count >= expected_min
        if expected_max is not None:
            is_valid = is_valid and row_count <= expected_max
        logger.info("搜索结果验证: 当前页=%d, 总数文本='%s', 有效=%s",
                     row_count, self.get_total_count_text(), is_valid)
        return row_count, total_count, is_valid

    def verify_all_status_equal(self, expected_status):
        """验证当前页所有合同状态都等于预期状态

        Args:
            expected_status: 预期状态文本

        Returns:
            tuple: (all_statuses, is_all_match)
        """
        statuses = self.get_status_list()
        is_all_match = all(s == expected_status for s in statuses)
        logger.info("状态一致性验证: 总数=%d, 预期='%s', 全部匹配=%s",
                     len(statuses), expected_status, is_all_match)
        return statuses, is_all_match

    # ==================================================================
    #  内部工具方法
    # ==================================================================

    def _is_row_button_present(self, contract_no, button_text, timeout=3):
        """检查指定行中是否存在某按钮"""
        try:
            xpath = (
                f'//tr[contains(@class,"el-table__row")]'
                f'[.//td[contains(normalize-space(.),"{contract_no}")]]'
                f'//button[contains(.,"{button_text}")]'
            )
            self.find((By.XPATH, xpath), timeout=timeout)
            return True
        except TimeoutException:
            return False

    def _wait_table_ready(self, timeout=10):
        """等待表格数据渲染完成（兼容旧接口）"""
        return self._el_helper.wait_table_ready(timeout)

    def fill_contract_form(self, *, name=None, customer=None, product_type=None,
                           total_quantity=None, unit_price=None,
                           start_date=None, end_date=None):
        """填充合同新增/编辑弹窗表单。
        基于 placeholder 定位（弹窗使用 input placeholder 而非 label）。
        """
        if name is not None:
            self.js_fill_input(
                (By.XPATH, '//div[contains(@class,"el-dialog")]//input[@placeholder="合同名称"]'),
                name, fallback_send_keys=True)
        if customer is not None:
            self._click_vue_select(None, "请选择客户", customer)
        if product_type is not None:
            self._click_vue_select(None, "产品类型", product_type)
        if total_quantity is not None:
            self.js_fill_input(
                (By.XPATH, '//div[contains(@class,"el-dialog")]//input[@placeholder="合同总量(吨)"]'),
                str(total_quantity), fallback_send_keys=True)
        if unit_price is not None:
            self.js_fill_input(
                (By.XPATH, '//div[contains(@class,"el-dialog")]//input[@placeholder="合同金额(万元)"]'),
                str(unit_price), fallback_send_keys=True)
        if start_date is not None:
            self.js_fill_input(
                (By.XPATH, '//div[contains(@class,"el-dialog")]//input[@placeholder="生效日期"]'),
                start_date, fallback_send_keys=True)
        if end_date is not None:
            self.js_fill_input(
                (By.XPATH, '//div[contains(@class,"el-dialog")]//input[@placeholder="有效期至"]'),
                end_date, fallback_send_keys=True)

    def click_save(self):
        """点击弹窗确定按钮，返回 toast 消息文本"""
        logger.info("点击确定按钮")
        self._el_helper.click_button_by_text("确定")
        self.wait_vue_stable()
        return self.get_toast()

    def get_form_error_text(self, timeout=3):
        """获取所有表单验证错误文本

        Returns:
            list[str]: 错误信息列表
        """
        errors = self.find_all((By.CSS_SELECTOR, '.el-form-item__error'))
        return [e.text.strip() for e in errors if e.is_displayed() and e.text.strip()]
