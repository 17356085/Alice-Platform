"""用户列表页 Page Object — system-user 模块

基于 PAGE_INTERFACE.yaml v1.0 + PAGE_ELEMENT_POSITION.md (Selenium 实测 DOM)
页面路径: /system-user/user-list (即 系统管理 > 用户管理)
核心功能: 搜索筛选、表格浏览、行操作、批量操作、分页

变更记录:
  2026-06-13: 初始生成，PAGE_INTERFACE.yaml 驱动，CSS优先 + XPath保底
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class UserListPage(BasePage):
    """用户列表页操作 — 继承 BasePage

    对应系统管理 > 用户管理 列表视图。
    提供搜索筛选、表格数据获取、行操作、批量操作、分页等能力。
    弹窗/表单操作由 UserFormPage (user-form) 负责。
    """

    # ══════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════════
    #  搜索/筛选区定位器 (CSS优先 → XPath保底)
    #  来源: PAGE_INTERFACE.yaml + PAGE_ELEMENT_POSITION.md
    # ══════════════════════════════════════════════════════════════════

    # 搜索输入框 — placeholder='搜索用户名/姓名/手机号'
    SEARCH_INPUT = (
        By.CSS_SELECTOR,
        "input.el-input__inner[placeholder*='搜索']",
    )
    SEARCH_INPUT_XPATH = (
        By.XPATH,
        "//input[@placeholder='搜索用户名/姓名/手机号']",
    )

    # 角色下拉选择 — 默认显示'全部角色'
    ROLE_SELECT_TRIGGER = (
        By.XPATH,
        "//div[contains(@class,'el-form-item')][.//label[contains(.,'角色')]]"
        "//div[contains(@class,'el-select')]",
    )

    # 状态下拉选择 — 默认显示'全部'，⚠️ 实测为 el-select 非 radio-group
    STATUS_SELECT_TRIGGER = (
        By.XPATH,
        "//div[contains(@class,'el-form-item')]"
        "[.//label[contains(.,'状态') and not(contains(.,'角色'))]]"
        "//div[contains(@class,'el-select')]",
    )
    STATUS_SELECT_TRIGGER_CSS = (
        By.CSS_SELECTOR,
        ".el-select:has(.el-select__placeholder:contains('全部'))",
    )

    # 查询按钮 — 包含search图标的 el-button--primary
    # ⚠️ normalize-space: EP 按钮文本含前后空白 (" 查询 " → normalize-space → "查询")
    SEARCH_BUTTON = (
        By.XPATH,
        "//button[.//span[normalize-space()='查询']]",
    )
    SEARCH_BUTTON_CSS = (
        By.CSS_SELECTOR,
        "button.el-button--primary .el-icon-search",
    )

    # 重置按钮 — 纯文字'重置'
    RESET_BUTTON = (
        By.XPATH,
        "//button[.//span[normalize-space()='重置']]",
    )

    # 下拉选项通用定位 (Teleport 到 body 下)
    SELECT_DROPDOWN_OPTION = (
        By.XPATH,
        "//div[contains(@class,'el-select-dropdown') and not(contains(@style,'display: none'))]"
        "//li[contains(@class,'el-select-dropdown__item')]//span",
    )

    # ══════════════════════════════════════════════════════════════════
    #  工具栏定位器
    # ══════════════════════════════════════════════════════════════════

    # 新增按钮 — 工具栏第一个 el-button--primary
    ADD_BUTTON = (
        By.XPATH,
        "//button[contains(@class,'el-button--primary')][.//span[normalize-space()='新增']]",
    )

    # 导出按钮 — 绿色 el-button--success
    EXPORT_BUTTON = (
        By.CSS_SELECTOR,
        "button.el-button--success",
    )

    # 批量删除按钮 — 红色 el-button--danger
    BATCH_DELETE_BUTTON = (
        By.XPATH,
        "//button[contains(@class,'el-button--danger')][.//span[normalize-space()='删除']]",
    )
    BATCH_DELETE_DISABLED = (
        By.CSS_SELECTOR,
        "button.el-button--danger.is-disabled",
    )

    # ══════════════════════════════════════════════════════════════════
    #  表格定位器
    # ══════════════════════════════════════════════════════════════════

    TABLE_BODY = (
        By.CSS_SELECTOR,
        ".el-table__body-wrapper tbody",
    )

    # 表格行
    TABLE_ROW = (
        By.CSS_SELECTOR,
        ".el-table__body-wrapper .el-table__row",
    )

    # 表头全选复选框
    HEADER_CHECKBOX = (
        By.CSS_SELECTOR,
        ".el-table__header-wrapper .el-checkbox",
    )

    # 行复选框
    ROW_CHECKBOX = (
        By.CSS_SELECTOR,
        ".el-table__body-wrapper .el-checkbox",
    )

    # 状态标签
    STATUS_TAG = (
        By.CSS_SELECTOR,
        ".el-table__body .cell .el-tag",
    )

    # 角色标签 (排除 success 类型避免与状态混淆)
    ROLE_TAG = (
        By.CSS_SELECTOR,
        ".el-table__body .cell .el-tag:not(.el-tag--success)",
    )

    # 操作列文字按钮 (查看/编辑/分配角色/更多)
    ROW_ACTION_LINK = (
        By.CSS_SELECTOR,
        ".el-table__body .cell .el-button--text",
    )

    # ══════════════════════════════════════════════════════════════════
    #  分页定位器
    # ══════════════════════════════════════════════════════════════════

    PAGINATION_TOTAL = (
        By.CSS_SELECTOR,
        ".el-pagination__total",
    )

    # ══════════════════════════════════════════════════════════════════
    #  行操作按钮 (per-row, 来源: PAGE_ELEMENT_POSITION.md)
    # ══════════════════════════════════════════════════════════════════

    ROW_VIEW_BUTTON = (
        By.XPATH,
        ".//button[contains(@class,'el-button--primary')][normalize-space()='查看']",
    )
    ROW_EDIT_BUTTON = (
        By.XPATH,
        ".//button[contains(@class,'el-button--primary')][normalize-space()='编辑']",
    )
    ROW_ASSIGN_ROLE_BUTTON = (
        By.XPATH,
        ".//button[.//span[normalize-space()='分配角色']]",
    )
    ROW_MORE_BUTTON = (
        By.CSS_SELECTOR,
        "td .el-dropdown button",
    )
    # 更多下拉菜单项 (在 body 下独立容器中)
    MORE_DROPDOWN_RESET_PWD = (
        By.XPATH,
        "//li[contains(@class,'el-dropdown-menu__item') and contains(.,'重置密码')]",
    )
    MORE_DROPDOWN_DELETE = (
        By.XPATH,
        "//li[contains(@class,'el-dropdown-menu__item') and contains(.,'删除')]",
    )

    # ══════════════════════════════════════════════════════════════════
    #  通用
    # ══════════════════════════════════════════════════════════════════

    LOADING_MASK_CSS = (
        By.CSS_SELECTOR,
        ".el-loading-mask",
    )

    def __init__(self, driver, timeout=None):
        """初始化用户列表页 — 继承 BasePage"""
        super().__init__(driver, timeout)

    # ══════════════════════════════════════════════════════════════════
    #  导航 (唯一入口)
    # ══════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到用户列表页 — 唯一入口"""
        logger.info("导航到 → 系统管理 → 用户管理 (用户列表)")
        self.navigate_to("系统管理", "用户管理")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self

    def wait_table_loaded(self, timeout=15):
        """等待表格数据加载完成"""
        try:
            self.wait.until(
                EC.visibility_of_element_located(self.TABLE_BODY)
            )
            self._wait_loading_gone(timeout=timeout)
            self.wait_vue_stable()
            logger.info("表格加载完成")
        except TimeoutException:
            logger.warning("表格加载超时（可能无数据）")
        return self

    # ══════════════════════════════════════════════════════════════════
    #  搜索/筛选操作
    # ══════════════════════════════════════════════════════════════════

    def input_search(self, keyword):
        """输入搜索关键词（搜索框 placeholder='搜索用户名/姓名/手机号'）"""
        try:
            element = self.find_visible(self.SEARCH_INPUT, timeout=5)
            element.clear()
            element.send_keys(keyword)
            logger.info("搜索输入: %s", keyword)
        except Exception as e:
            logger.error("搜索输入失败: %s", e)
            raise
        return self

    def clear_search(self):
        """清空搜索框"""
        try:
            element = self.find_visible(self.SEARCH_INPUT, timeout=5)
            element.clear()
            logger.info("已清空搜索框")
        except Exception as e:
            logger.error("清空搜索框失败: %s", e)
            raise
        return self

    def click_search(self):
        """点击查询按钮"""
        try:
            self.click_search_button()
            logger.info("已点击查询按钮")
            self._wait_loading_gone(timeout=5)
            self.wait_vue_stable()
        except Exception as e:
            logger.error("点击查询按钮失败: %s", e)
            raise
        return self

    def click_reset(self):
        """点击重置按钮"""
        try:
            self.click_reset_button()
            logger.info("已点击重置按钮")
            self._wait_loading_gone(timeout=5)
            self.wait_vue_stable()
        except Exception as e:
            logger.error("点击重置按钮失败: %s", e)
            raise
        return self

    def select_role_filter(self, role_name):
        """选择角色筛选（搜索区角色下拉）

        注意: EP-001 — 下拉选项通过 Teleport 渲染到 body，需在 body 下查找选项
        """
        try:
            trigger = self.find_clickable(self.ROLE_SELECT_TRIGGER, timeout=5)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", trigger
            )
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", trigger)
            logger.info("已打开角色下拉框")
            self.wait_vue_stable()

            # 等待下拉列表出现 (Teleport 到 body)
            option_xpath = (
                f"//div[contains(@class,'el-select-dropdown')"
                f" and not(contains(@style,'display: none'))]"
                f"//li[contains(@class,'el-select-dropdown__item')]"
                f"//span[normalize-space()='{role_name}']"
            )
            option = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, option_xpath))
            )
            self.driver.execute_script("arguments[0].click();", option)
            logger.info("已选择角色筛选: %s", role_name)
            self._wait_loading_gone(timeout=3)
            self.wait_vue_stable()
        except Exception as e:
            logger.error("选择角色筛选失败: %s", e)
            raise
        return self

    def select_status_filter(self, status_name):
        """选择状态筛选（搜索区状态下拉）

        ⚠️ 实测为 el-select 而非 radio-group (PAGE_ELEMENT_POSITION 已确认)
        ⚠️ 状态 select 和角色 select 并排，需精确定位避免匹配到角色下拉
        注意: EP-001 — Teleport 渲染
        """
        try:
            # 多重触发定位：优先用 label 精确文本匹配
            trigger_locators = [
                # 最精确：label 文本精确为"状态"的 form-item 内 el-select
                (By.XPATH, "//label[normalize-space()='状态']/..//div[contains(@class,'el-select__wrapper')]"),
                # 通过表单 label 匹配
                self.STATUS_SELECT_TRIGGER,
                # 回退：通过 placeholder 文本 "全部" (状态默认值，不是"全部角色")
                (By.XPATH, "//div[contains(@class,'el-select')][.//span[contains(@class,'el-select__placeholder') and normalize-space()='全部']]"),
            ]

            trigger = None
            last_err = None
            for loc in trigger_locators:
                try:
                    trigger = self.find_clickable(loc, timeout=3)
                    if trigger:
                        break
                except Exception as err:
                    last_err = err
                    continue

            if not trigger:
                raise Exception(f"无法定位状态下拉触发器: {last_err}")

            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", trigger
            )
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", trigger)
            logger.info("已打开状态下拉框")
            self.wait_vue_stable()

            # 查找可见下拉中的选项
            option_locators = [
                (By.XPATH, f"//div[contains(@class,'el-select-dropdown') and not(contains(@style,'display: none'))]//li[contains(@class,'el-select-dropdown__item')]//span[normalize-space()='{status_name}']"),
                (By.XPATH, f"//div[contains(@class,'el-popper') and not(contains(@style,'display: none'))]//li[contains(@class,'el-select-dropdown__item')]//span[normalize-space()='{status_name}']"),
                (By.XPATH, f"//li[contains(@class,'el-select-dropdown__item') and not(contains(@class,'is-disabled'))]//span[normalize-space()='{status_name}']"),
            ]

            option = None
            for loc in option_locators:
                try:
                    option = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable(loc)
                    )
                    if option:
                        break
                except Exception:
                    continue

            if not option:
                raise Exception(f"未找到状态下拉选项: {status_name}")

            self.driver.execute_script("arguments[0].click();", option)
            logger.info("已选择状态筛选: %s", status_name)
            self._wait_loading_gone(timeout=3)
            self.wait_vue_stable()
        except Exception as e:
            logger.error("选择状态筛选失败: %s", e)
            raise
        return self

    # ══════════════════════════════════════════════════════════════════
    #  表格数据获取
    # ══════════════════════════════════════════════════════════════════

    def get_row_count(self):
        """获取当前页表格行数"""
        try:
            self.wait.until(
                EC.presence_of_element_located(self.TABLE_ROW)
            )
            rows = self.driver.find_elements(*self.TABLE_ROW)
            count = len(rows)
            logger.info("当前页行数: %d", count)
            return count
        except TimeoutException:
            logger.info("表格无数据或未加载")
            return 0
        except Exception as e:
            logger.error("获取行数失败: %s", e)
            return 0

    def get_column_data(self, col_index):
        """获取指定列的所有数据 (col_index 从 1 开始)"""
        return super().get_column_data(col_index)

    def get_cell_text(self, row_index, col_index):
        """获取指定单元格文本"""
        return super().get_cell(row_index, col_index)

    def get_table_headers(self):
        """获取表格列头"""
        try:
            headers = super().get_table_headers(min_columns=1)
            logger.info("获取到表头: %s", headers)
            return headers
        except Exception as e:
            logger.error("获取表头失败: %s", e)
            return []

    def get_all_usernames(self):
        """获取当前页所有用户名 (第2列)"""
        try:
            col_data = self.get_column_data(2)
            logger.info("当前页用户名: %s", col_data)
            return col_data
        except Exception as e:
            logger.error("获取用户名列表失败: %s", e)
            return []

    def is_username_present(self, username):
        """判断列表中是否存在指定用户名（精确匹配）"""
        try:
            usernames = self.get_all_usernames()
            return any(u == username for u in usernames)
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════
    #  行选择 (复选框)
    # ══════════════════════════════════════════════════════════════════

    def select_all_rows(self):
        """点击表头全选复选框"""
        try:
            label_el = self.driver.find_element(
                By.CSS_SELECTOR, ".el-table__header-wrapper .el-checkbox"
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", label_el
            )
            self.wait_vue_stable()
            self.driver.execute_script("""
                var label = arguments[0];
                label.click();
                var input = label.querySelector('input[type=\"checkbox\"]');
                if (input) {
                    input.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                }
            """, label_el)
            logger.info("已点击全选复选框")
            self.wait_vue_stable()
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("全选操作失败: %s", e)
            raise
        return self

    def select_row_by_index(self, index):
        """勾选第 index 行 (1-based, 对应表格行号)"""
        try:
            rows = self.driver.find_elements(*self.TABLE_ROW)
            if index < 1 or index > len(rows):
                raise IndexError(f"行号 {index} 超出范围 (1-{len(rows)})")
            row = rows[index - 1]
            # 找到 label 和 input，两者都点击确保 Vue 响应
            label_el = row.find_element(By.CSS_SELECTOR, ".el-checkbox")
            try:
                input_el = row.find_element(By.CSS_SELECTOR, "input.el-checkbox__original")
            except Exception:
                input_el = None

            is_already_checked = (
                "is-checked" in (label_el.get_attribute("class") or "") or
                (input_el and input_el.get_attribute("checked") == "true")
            )

            if not is_already_checked:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", label_el
                )
                self.wait_vue_stable()
                # 原生 click on label（Element Plus 的 .el-checkbox 是 label 元素，包裹 input）
                self.driver.execute_script("""
                    var label = arguments[0];
                    label.click();
                    // 同时触发原生 input 的 change 供 Vue v-model 消费
                    var input = label.querySelector('input[type=\"checkbox\"]');
                    if (input) {
                        input.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                        input.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                """, label_el)
                logger.info("已勾选第 %d 行", index)
            else:
                logger.info("第 %d 行已处于勾选状态", index)
            self.wait_vue_stable()
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("勾选第 %d 行失败: %s", index, e)
            raise
        return self

    def select_row_by_username(self, username):
        """根据用户名勾选对应行"""
        try:
            checkbox_xpath = (
                f"//tr[.//td[2]//div[normalize-space()='{username}']]"
                f"//td[1]//label[contains(@class,'el-checkbox')]"
            )
            checkbox = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, checkbox_xpath))
            )
            if "is-checked" not in (checkbox.get_attribute("class") or ""):
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", checkbox
                )
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].click();", checkbox)
                logger.info("已勾选用户: %s", username)
            self.wait_vue_stable()
        except Exception as e:
            logger.error("勾选用户 %s 失败: %s", username, e)
            raise
        return self

    # ══════════════════════════════════════════════════════════════════
    #  行操作按钮 (per-row)
    # ══════════════════════════════════════════════════════════════════

    def _get_row_by_text(self, text, col_index=2):
        """根据文本定位表格行"""
        xpath = (
            f"//tr[contains(@class,'el-table__row')]"
            f"[.//td[{col_index}]//div[normalize-space()='{text}']]"
        )
        try:
            row = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return row
        except TimeoutException:
            logger.warning("未找到包含 '%s' 的行 (列%d)", text, col_index)
            return None

    def click_row_view(self, username):
        """点击指定行的查看按钮"""
        try:
            row = self._get_row_by_text(username)
            if not row:
                raise Exception(f"未找到用户 '{username}' 的行")
            btn = row.find_element(*self.ROW_VIEW_BUTTON)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", btn
            )
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", btn)
            logger.info("已点击用户 %s 的查看按钮", username)
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击查看按钮失败: %s", e)
            raise
        return self

    def click_row_edit(self, username):
        """点击指定行的编辑按钮"""
        try:
            row = self._get_row_by_text(username)
            if not row:
                raise Exception(f"未找到用户 '{username}' 的行")
            btn = row.find_element(*self.ROW_EDIT_BUTTON)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", btn
            )
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", btn)
            logger.info("已点击用户 %s 的编辑按钮", username)
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击编辑按钮失败: %s", e)
            raise
        return self

    def click_row_assign_role(self, username):
        """点击指定行的分配角色按钮"""
        try:
            row = self._get_row_by_text(username)
            if not row:
                raise Exception(f"未找到用户 '{username}' 的行")
            btn = row.find_element(*self.ROW_ASSIGN_ROLE_BUTTON)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", btn
            )
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", btn)
            logger.info("已点击用户 %s 的分配角色按钮", username)
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击分配角色按钮失败: %s", e)
            raise
        return self

    def click_row_more(self, username):
        """点击指定行的更多下拉按钮"""
        try:
            row = self._get_row_by_text(username)
            if not row:
                raise Exception(f"未找到用户 '{username}' 的行")
            btn = row.find_element(*self.ROW_MORE_BUTTON)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", btn
            )
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", btn)
            logger.info("已点击用户 %s 的更多按钮", username)
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击更多按钮失败: %s", e)
            raise
        return self

    def click_more_reset_password(self):
        """点击更多下拉菜单中的重置密码"""
        try:
            option = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(self.MORE_DROPDOWN_RESET_PWD)
            )
            self.driver.execute_script("arguments[0].click();", option)
            logger.info("已点击更多→重置密码")
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击重置密码选项失败: %s", e)
            raise
        return self

    def click_more_delete(self):
        """点击更多下拉菜单中的删除"""
        try:
            option = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(self.MORE_DROPDOWN_DELETE)
            )
            self.driver.execute_script("arguments[0].click();", option)
            logger.info("已点击更多→删除")
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击删除选项失败: %s", e)
            raise
        return self

    # ══════════════════════════════════════════════════════════════════
    #  工具栏操作
    # ══════════════════════════════════════════════════════════════════

    def click_add(self):
        """点击新增按钮"""
        try:
            self._wait_loading_gone(timeout=10)
            button = self.find_clickable(self.ADD_BUTTON, timeout=5)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", button
            )
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", button)
            logger.info("已点击新增按钮")
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击新增按钮失败: %s", e)
            raise
        return self

    def click_export(self):
        """点击导出按钮"""
        try:
            button = self.find_clickable(self.EXPORT_BUTTON, timeout=5)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", button
            )
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", button)
            logger.info("已点击导出按钮")
        except Exception as e:
            logger.error("点击导出按钮失败: %s", e)
            raise
        return self

    def is_batch_delete_enabled(self):
        """批量删除按钮是否可用（非 disabled 状态）"""
        try:
            self.wait_vue_stable()
            # Element Plus: disabled 按钮有 is-disabled class + disabled 属性
            locators = [
                (By.CSS_SELECTOR, "button.el-button--danger:not(.is-disabled)"),
                (By.XPATH, "//button[contains(@class,'el-button--danger') and not(@disabled)]"),
                (By.XPATH, "//button[contains(@class,'el-button--danger') and not(contains(@class,'is-disabled'))]"),
            ]
            for loc in locators:
                try:
                    btn = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located(loc)
                    )
                    if btn and btn.is_displayed():
                        classes = btn.get_attribute("class") or ""
                        disabled_attr = btn.get_attribute("disabled")
                        if "is-disabled" not in classes and disabled_attr != "true":
                            return True
                except Exception:
                    continue
            return False
        except Exception:
            return False

    def click_batch_delete(self):
        """点击批量删除按钮"""
        try:
            button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(self.BATCH_DELETE_BUTTON)
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", button
            )
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", button)
            logger.info("已点击批量删除按钮")
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击批量删除按钮失败: %s", e)
            raise
        return self

    # ══════════════════════════════════════════════════════════════════
    #  分页操作
    # ══════════════════════════════════════════════════════════════════

    def get_total_count(self):
        """获取分页总数"""
        return super().get_total_count()

    def get_total_count_text(self):
        """获取分页总数文本（JS 直接提取，绕过 Selenium visibility 检查）"""
        for _ in range(10):
            try:
                result = self.driver.execute_script("""
                    var total = document.querySelector('.el-pagination__total');
                    if (!total) return '';
                    var text = total.innerText || total.textContent || '';
                    return text.trim();
                """)
                if result and any(c.isdigit() for c in result):
                    logger.info("分页总数: %s", result)
                    return result
            except Exception:
                pass
            self._wait_loading_gone(timeout=3)
        raise TimeoutException("获取分页总数失败: 10次重试后仍未获取到")

    def click_next_page(self):
        """翻到下一页"""
        try:
            super().click_next_page()
            self._wait_loading_gone(timeout=5)
            self.wait_vue_stable()
            logger.info("已翻到下一页")
        except Exception as e:
            logger.error("翻页失败: %s", e)
            raise
        return self

    def click_prev_page(self):
        """翻到上一页"""
        try:
            button = self.find_clickable(self.PREV_PAGE, timeout=5)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", button
            )
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", button)
            self._wait_loading_gone(timeout=5)
            self.wait_vue_stable()
            logger.info("已翻到上一页")
        except Exception as e:
            logger.error("翻到上一页失败: %s", e)
            raise
        return self

    # ══════════════════════════════════════════════════════════════════
    #  页面状态检查
    # ══════════════════════════════════════════════════════════════════

    def is_table_visible(self):
        """表格是否可见"""
        return self.is_visible(self.TABLE_BODY, timeout=5)

    def is_pagination_visible(self):
        """分页组件是否可见（JS 提取绕过 Selenium visibility）"""
        try:
            result = self.driver.execute_script("""
                var total = document.querySelector('.el-pagination__total');
                if (!total) return '';
                return total.innerText || total.textContent || '';
            """)
            return bool(result.strip()) and any(c.isdigit() for c in result)
        except Exception:
            return False

    def is_loading_gone(self, timeout=5):
        """loading 遮罩是否消失"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(self.LOADING_MASK_CSS)
            )
            return True
        except TimeoutException:
            return False

    def _wait_loading_gone(self, timeout=10):
        """等待 loading 遮罩消失"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(self.LOADING_MASK_CSS)
            )
        except TimeoutException:
            pass

    def confirm_message_box(self, action_name="操作"):
        """确认 Element Plus 消息确认框 (MessageBox)"""
        try:
            locators = [
                (
                    By.XPATH,
                    "(//div[contains(@class,'el-overlay') and not(contains(@style,'display: none'))]"
                    "//div[contains(@class,'el-message-box')])[last()]"
                    "//button[.//span[normalize-space(.)='确定' or normalize-space(.)='确认']]",
                ),
                (
                    By.XPATH,
                    "(//div[contains(@class,'el-message-box') and not(contains(@style,'display: none'))])[last()]"
                    "//div[contains(@class,'el-message-box__btns')]"
                    "//button[contains(@class,'el-button--primary')]",
                ),
            ]

            button = None
            for loc in locators:
                try:
                    button = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located(loc)
                    )
                    if button and button.is_displayed():
                        break
                except Exception:
                    continue

            if not button:
                raise Exception(f"无法定位到{action_name}确认框的确定按钮")

            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", button
            )
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", button)
            logger.info("已确认 %s MessageBox", action_name)
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("确认 %s MessageBox 失败: %s", action_name, e)
            raise

    def get_toast_text(self, timeout=5):
        """获取 Toast 提示消息文本"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        "(//*[contains(@class,'el-message__content')"
                        " or contains(@class,'el-message')]"
                        "[normalize-space(.)!=''])[last()]",
                    )
                )
            )
            text = element.text.strip()
            logger.info("获取到提示消息: %s", text)
            return text
        except Exception as e:
            logger.error("获取提示消息失败: %s", e)
            return ""
