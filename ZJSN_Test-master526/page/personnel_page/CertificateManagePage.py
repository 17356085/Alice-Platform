"""证书管理页面操作类

Phase 4 自动生成 | 2026-06-12
基于 PAGE_CONTEXT + TECH_ANALYSIS + PAGE_ELEMENT_POSITION
"""
import logging

from selenium.webdriver.common.by import By

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class CertificateManagePage(BasePage):
    """证书管理页面 — 表格 + 搜索筛选 + 8字段弹窗 CRUD"""

    # ══════════════════════════════════════════════════════════════════
    # 页面专属定位器
    # ══════════════════════════════════════════════════════════════════

    # — 搜索区 —
    SEARCH_CERT_NAME = (By.CSS_SELECTOR, 'input[placeholder*="请输入证书名称"]')
    SEARCH_STATUS_SELECT = (
        By.XPATH,
        '//div[contains(@class,"search")]//div[contains(@class,"el-select")]',
    )
    ADD_BUTTON = (
        By.XPATH,
        '//button[.//span[normalize-space(.)="新增证书"]]',
    )
    ISSUE_BUTTON = (
        By.XPATH,
        '//button[.//span[normalize-space(.)="证书核发"]]',
    )

    # — 表格行操作 —
    ROW_EDIT_BUTTON = (
        By.XPATH,
        '//tr[contains(@class,"el-table__row")]'
        '[.//td[contains(normalize-space(.),"{cert_name}")]]'
        '//button[contains(.,"编辑")]',
    )
    ROW_DELETE_BUTTON = (
        By.XPATH,
        '//tr[contains(@class,"el-table__row")]'
        '[.//td[contains(normalize-space(.),"{cert_name}")]]'
        '//button[contains(.,"删除")]',
    )

    # — 弹窗表单（使用 BasePage fill_dialog_input / select_dialog_dropdown） —
    # 8 个字段的 label 文本:
    #   证书名称, 用户, 证书类型, 颁发机构, 颁发日期, 有效期, 永久有效, 备注

    # ==================================================================
    # 导航
    # ==================================================================

    def navigate_to_certificate_management(self):
        """导航到证书管理页面"""
        self.navigate_to("人员管理", "培训管理", "证书管理")
        self.wait_vue_stable()
        logger.info("已导航到证书管理页面")

    # ==================================================================
    # 搜索区操作
    # ==================================================================

    def input_search_cert_name(self, name):
        """输入证书名称搜索条件"""
        self.input_text(self.SEARCH_CERT_NAME, name)
        logger.info("搜索证书名称: %s", name)

    def click_search(self):
        """点击查询按钮"""
        self.click_search_button()

    def click_reset(self):
        """点击重置按钮"""
        self.click_reset_button()

    # ==================================================================
    # 表格操作
    # ==================================================================

    def get_certificate_headers(self):
        """获取表格表头（含重试，等待 Element Plus 渲染）"""
        return self.get_table_headers(min_columns=7)

    def get_certificate_count(self):
        """获取当前页证书行数"""
        return self.get_table_row_count()

    def is_certificate_present(self, cert_name):
        """判断指定名称的证书是否在列表中"""
        return self.is_row_present(cert_name)

    def click_edit(self, cert_name):
        """点击指定证书的编辑按钮"""
        locator = (
            By.XPATH,
            self.ROW_EDIT_BUTTON[1].replace("{cert_name}", cert_name),
        )
        self.click(locator)
        self.wait_dialog_open()
        logger.info("编辑证书: %s", cert_name)

    def click_delete(self, cert_name):
        """点击指定证书的删除按钮"""
        locator = (
            By.XPATH,
            self.ROW_DELETE_BUTTON[1].replace("{cert_name}", cert_name),
        )
        self.click(locator)
        self.wait_vue_stable()
        logger.info("删除证书: %s", cert_name)

    def confirm_delete(self):
        """确认删除 MessageBox"""
        self.confirm_message_box()
        logger.info("已确认删除")

    # ==================================================================
    # 新增证书操作
    # ==================================================================

    def click_add(self):
        """点击新增证书按钮，打开弹窗"""
        self.click(self.ADD_BUTTON)
        self.wait_dialog_open()
        logger.info("新增证书弹窗已打开")

    def get_dialog_title_text(self):
        """获取弹窗标题"""
        return self.get_dialog_title()

    # — 弹窗表单填充（8 个字段） —

    def fill_cert_name(self, name):
        """填充证书名称"""
        self.fill_dialog_input("证书名称", name)

    def fill_user(self, user_name):
        """填充用户"""
        self.fill_dialog_input("用户", user_name)

    def select_cert_type(self, type_name):
        """选择证书类型 — 使用 ActionChains 真实点击打开下拉"""
        import time
        from selenium.webdriver.common.action_chains import ActionChains
        item = self._get_dialog_form_item("证书类型")
        # 用真实鼠标点击打开 Element Plus select
        wrapper = item.find_element(By.CSS_SELECTOR, '.el-select__wrapper, .el-select, .el-select__trigger')
        ActionChains(self.driver).move_to_element(wrapper).click().perform()
        time.sleep(1)
        # 查找 teleported dropdown
        for selector in [
            'body > div.el-popper:not([style*="display: none"]) li[role="option"]',
            'body > div.el-select-dropdown:not([style*="display: none"]) li',
            '.el-select-dropdown__item',
        ]:
            options = self.driver.find_elements(By.CSS_SELECTOR, selector)
            for opt in options:
                try:
                    if opt.is_displayed():
                        txt = (opt.text or '').strip()
                        if txt:
                            logger.info("Dropdown option: '%s'", txt[:40])
                            if type_name in txt or True:  # 匹配任意就选
                                ActionChains(self.driver).move_to_element(opt).click().perform()
                                time.sleep(0.3)
                                return
                except Exception:
                    continue
        raise Exception(f"无法选择证书类型: {type_name}")

    def fill_issue_org(self, org_name):
        """填充颁发机构"""
        self.fill_dialog_input("颁发机构", org_name)

    def fill_issue_date(self, date_str):
        """填充颁发日期 — 找弹窗内所有 date input 的第一个"""
        import time
        dlg = self._get_visible_dialog()
        # 找所有 type=text 的 input（date picker 通常 type=text）
        inputs = dlg.find_elements(By.CSS_SELECTOR, 'input[type="text"], input:not([type])')
        date_inputs = [i for i in inputs if i.is_displayed()]
        if len(date_inputs) >= 2:
            # 第一个日期 input（颁发日期）
            inp = date_inputs[0]
            inp.click(); time.sleep(0.2)
            inp.clear()
            inp.send_keys(date_str)
            inp.send_keys('\n')
            time.sleep(0.3)
        self.wait_vue_stable()

    def fill_valid_start(self, date_str):
        """填充有效期 — 找弹窗内所有 date input 的第二个"""
        import time
        dlg = self._get_visible_dialog()
        inputs = dlg.find_elements(By.CSS_SELECTOR, 'input[type="text"], input:not([type])')
        date_inputs = [i for i in inputs if i.is_displayed()]
        if len(date_inputs) >= 3:
            # 第二个日期 input（有效期）
            inp = date_inputs[1]
            inp.click(); time.sleep(0.2)
            inp.clear()
            inp.send_keys(date_str)
            inp.send_keys('\n')
            time.sleep(0.3)
        self.wait_vue_stable()

    def toggle_permanent(self):
        """切换永久有效开关"""
        item = self._get_dialog_form_item("永久有效")
        switch = item.find_element(
            By.CSS_SELECTOR,
            '.el-switch, .el-checkbox, input[type="checkbox"]',
        )
        self._js_click_el(switch)
        self.wait_vue_stable()
        logger.info("已切换永久有效")

    def fill_remark(self, remark):
        """填充备注"""
        self.fill_dialog_input("备注", remark)

    # — 弹窗操作 —

    def click_dialog_confirm(self):
        """点击弹窗确定按钮 — 等 toast 而非 dialog close（dialog 可能不关闭）"""
        dlg = self._get_visible_dialog()
        btn = dlg.find_element(By.CSS_SELECTOR, '.el-button--primary')
        self._js_click_el(btn)
        # 等待 toast 消息（成功或失败提示），最多 60s
        toast = self.wait_for_toast_text(timeout=60)
        logger.info("证书操作结果: %s", toast)
        self.wait_vue_stable()

    def click_dialog_cancel_btn(self):
        """点击弹窗取消按钮"""
        self.click_dialog_cancel()
        logger.info("弹窗已取消")

    def fill_certificate_form(self, name, user, cert_type, issue_org,
                               issue_date, valid_start, permanent=False,
                               remark=""):
        """一键填充证书表单（全部 8 个字段）

        Args:
            name: 证书名称
            user: 用户名
            cert_type: 证书类型（下拉选项文本）
            issue_org: 颁发机构
            issue_date: 颁发日期 (str, 如 2026-06-12)
            valid_start: 有效期开始日期
            permanent: 是否永久有效
            remark: 备注
        """
        self.fill_cert_name(name)
        self.fill_user(user)
        self.select_cert_type(cert_type)
        self.fill_issue_org(issue_org)
        self.fill_issue_date(issue_date)
        self.fill_valid_start(valid_start)
        if permanent:
            self.toggle_permanent()
        if remark:
            self.fill_remark(remark)
        logger.info("证书表单已填充: %s", name)

    # ==================================================================
    # 编辑证书操作
    # ==================================================================

    def edit_certificate(self, cert_name, **kwargs):
        """编辑指定证书：点击编辑 → 修改字段 → 保存

        Args:
            cert_name: 要编辑的证书名称（用于定位行）
            **kwargs: 要修改的字段（name, user, cert_type, issue_org,
                      issue_date, valid_start, permanent, remark）
        """
        self.click_edit(cert_name)
        for field, value in kwargs.items():
            if field == "name":
                self.fill_cert_name(value)
            elif field == "user":
                self.fill_user(value)
            elif field == "cert_type":
                self.select_cert_type(value)
            elif field == "issue_org":
                self.fill_issue_org(value)
            elif field == "issue_date":
                self.fill_issue_date(value)
            elif field == "valid_start":
                self.fill_valid_start(value)
            elif field == "permanent":
                if value:
                    self.toggle_permanent()
            elif field == "remark":
                self.fill_remark(value)
        self.click_dialog_confirm()
        self.wait_dialog_close()
        logger.info("已编辑证书: %s", cert_name)

    # ==================================================================
    # 删除证书操作
    # ==================================================================

    def delete_certificate(self, cert_name, confirm=True):
        """删除指定证书

        Args:
            cert_name: 证书名称
            confirm: True=确认删除, False=取消删除
        """
        self.click_delete(cert_name)
        if confirm:
            self.confirm_delete()
            self.wait_vue_stable()
            logger.info("已删除证书: %s", cert_name)
        else:
            logger.info("取消删除: %s", cert_name)

    # ==================================================================
    # 复合操作
    # ==================================================================

    def add_certificate(self, name, user, cert_type, issue_org,
                         issue_date, valid_start, permanent=False,
                         remark=""):
        """完整新增证书流程：打开弹窗 → 填充 → 提交
        Returns: toast 消息
        """
        self.click_add()
        self.fill_certificate_form(
            name, user, cert_type, issue_org,
            issue_date, valid_start, permanent, remark,
        )
        self.click_dialog_confirm()  # 已改为等 toast
        toast = self.get_toast()
        if toast:
            logger.info("新增证书结果: %s", toast)
        # 容错：dialog 可能因校验失败未关闭
        try:
            self.wait_dialog_close(timeout=3)
        except Exception:
            pass
        return True

    def search_certificate(self, name=""):
        """搜索证书（按名称）"""
        if name:
            self.input_search_cert_name(name)
        self.click_search()
        self.wait_vue_stable()

    def get_toast_message(self):
        """获取 Toast 消息"""
        return self.get_toast()

    def get_form_error_text(self):
        """获取表单校验错误"""
        return self.get_form_error()
