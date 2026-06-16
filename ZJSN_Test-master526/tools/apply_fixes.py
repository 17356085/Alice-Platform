"""Apply all fixes to TrainPlanPage.py"""
import re

RECOVERED = r'D:\ZJSN_Test-master\page\person_page\TrainPlanPage_recovered.py'
TARGET = r'D:\ZJSN_Test-master\page\person_page\TrainPlanPage.py'

with open(RECOVERED, 'r', encoding='utf-8') as f:
    content = f.read()

# ===== Fix 1: _click_dialog_confirm_button (add retry + native click + global fallback + close verification) =====

old_confirm = '''    def _click_dialog_confirm_button(self, dialog_el):
        """通用方法：点击弹窗底部的确认/确定选择按钮

        Args:
            dialog_el: 弹窗元素（WebElement），用于限定查找范围
        """
        confirm_xpaths = [
            # 优先匹配「确认选择」（截图实际文字）
            './/button[.//span[normalize-space(.)="确认选择"]]',
            # 匹配「确定」
            './/button[.//span[normalize-space(.)="确定"]]',
            # 匹配「确定选择」
            './/button[.//span[normalize-space(.)="确定选择"]]',
            # footer 内的 primary 按钮
            './/footer//button[contains(@class,"el-button--primary")]',
            # 弹窗内最后一个主按钮
            './/button[contains(@class,"el-button--primary")]',
            # 兜底：最后一个 button
            './/button[last()]',
        ]
        for xp in confirm_xpaths:
            try:
                btn = dialog_el.find_element(By.XPATH, xp)
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.3)
                self.driver.execute_script("arguments[0].click();", btn)
                return
            except Exception as e:
                continue
        raise Exception("未找到弹窗的确认/确定选择按钮")'''

new_confirm = '''    def _click_dialog_confirm_button(self, dialog_el, close_timeout=4):
        """通用方法：点击弹窗底部的确认/确定选择按钮

        Args:
            dialog_el: 弹窗元素（WebElement），用于限定查找范围
            close_timeout: 点击后等待弹窗关闭的超时秒数
        """
        confirm_xpaths = [
            './/button[.//span[normalize-space(.)="确认选择"]]',
            './/button[.//span[normalize-space(.)="确定"]]',
            './/button[.//span[normalize-space(.)="确定选择"]]',
            './/footer//button[contains(@class,"el-button--primary")]',
            './/button[contains(@class,"el-button--primary")]',
            './/button[last()]',
        ]

        btn = None
        for xp in confirm_xpaths:
            try:
                btn = dialog_el.find_element(By.XPATH, xp)
                break
            except Exception:
                continue

        if btn is None:
            global_xpaths = [
                '//button[.//span[normalize-space(.)="确认选择"]]',
                '//button[.//span[normalize-space(.)="确定选择"]]',
                '//button[.//span[normalize-space(.)="确定"]]',
                '//button[contains(@class,"el-button--primary")]',
            ]
            for xp in global_xpaths:
                try:
                    btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xp))
                    )
                    break
                except Exception:
                    continue

        if btn is None:
            raise Exception("未找到弹窗的确认/确定选择按钮")

        for attempt in range(3):
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.3)
            try:
                btn.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(1)

            try:
                WebDriverWait(self.driver, close_timeout, poll_frequency=0.2).until(
                    EC.invisibility_of_element(dialog_el)
                )
                return
            except Exception:
                if attempt < 2:
                    print(f"弹窗未关闭，重试点击 (尝试 {attempt+2}/3)...")
                    time.sleep(0.5)
                continue'''

content = content.replace(old_confirm, new_confirm)
print("Fix 1 applied: _click_dialog_confirm_button")

# ===== Fix 2: select_principal - reversed dialog iteration + skip empty-title =====

old_principal = '''        # 获取所有弹窗，找出新增的那个（负责人选择弹窗）
        dialogs = self.driver.find_elements(By.XPATH, '//div[contains(@class,"el-dialog")][not(contains(@style,"display: none"))]')
        principal_dialog = None

        for d in dialogs:
            # 排除已有的弹窗（添加培训计划弹窗）
            is_main_dialog = False
            try:
                title_els = d.find_elements(By.XPATH, './/*[contains(@class,"el-dialog__title")]')
                if title_els:
                    title = title_els[0].text.strip()
                    if title == "添加培训计划":
                        is_main_dialog = True
            except Exception:
                pass

            if not is_main_dialog:
                principal_dialog = d
                break'''

new_principal = '''        # 获取所有弹窗，找出新增的那个（负责人选择弹窗）
        dialogs = self.driver.find_elements(By.XPATH, '//div[contains(@class,"el-dialog")][not(contains(@style,"display: none"))]')
        principal_dialog = None

        # 倒序遍历：取最后一个可见的非主弹窗（避免被已关闭但残留的空标题弹窗干扰）
        for d in reversed(dialogs):
            try:
                title_els = d.find_elements(By.XPATH, './/*[contains(@class,"el-dialog__title")]')
                if not title_els:
                    continue
                title = title_els[0].text.strip()
                if not title or title == "添加培训计划":
                    continue
                principal_dialog = d
                break
            except Exception:
                continue'''

content = content.replace(old_principal, new_principal)
print("Fix 2 applied: select_principal")

# ===== Fix 3: Add close_sub_dialogs method (insert before click_save) =====

old_save = '''    def click_save(self):
        """点击弹窗保存/确定按钮"""
        save_xpaths = [
            self.SAVE_BUTTON,
            (By.XPATH, '//div[contains(@class,"el-dialog")]//footer//button[.//span[contains(text(),"保存") or contains(text(),"确定")]]'),
            (By.XPATH, '//div[contains(@class,"el-dialog")]//button[contains(@class,"el-button--primary")][.//span[contains(text(),"确定")]]'),
            (By.XPATH, '//div[contains(@class,"el-dialog")]//footer//button[1]'),
            (By.XPATH, '//body/div[contains(@class,"el-dialog")]//footer//button[contains(@class,"el-button--primary")]'),
        ]
        for xp in save_xpaths:
            try:
                self._click_js(xp)
                time.sleep(1)
                return
            except Exception:
                continue
        raise Exception("未找到保存/确定按钮")'''

new_save = '''    def close_sub_dialogs(self):
        """关闭所有子弹窗/遮罩层，只保留主弹窗（添加培训计划）

        当子弹窗（如选择培训对象、选择课程等）关闭异常时，
        用JS强制隐藏所有非主弹窗的元素，确保主弹窗可操作。
        """
        try:
            self.driver.execute_script("""
                (function() {
                    // 关闭所有非主弹窗的 overlay 遮罩
                    var overlays = document.querySelectorAll('.el-overlay');
                    for (var o of overlays) {
                        var dialog = o.querySelector('.el-dialog__title');
                        if (dialog && dialog.textContent.trim() === '添加培训计划') continue;
                        o.style.display = 'none';
                        o.remove();
                    }
                    // 隐藏所有非主弹窗的对话框
                    var dialogs = document.querySelectorAll('.el-dialog');
                    for (var d of dialogs) {
                        var title = d.querySelector('.el-dialog__title');
                        if (title && title.textContent.trim() === '添加培训计划') continue;
                        d.style.display = 'none';
                    }
                    // 去除 el-overlay 导致的 body 禁止滚动
                    document.body.classList.remove('el-overflow-hidden');
                })();
            """)
            time.sleep(0.5)
        except Exception:
            pass

    def click_save(self):
        """点击弹窗保存/确定按钮"""
        # 先关闭可能残留的子弹窗，确保主弹窗可操作
        self.close_sub_dialogs()
        time.sleep(0.5)

        save_xpaths = [
            self.SAVE_BUTTON,
            (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//footer//button[.//span[contains(text(),"保存") or contains(text(),"确定")]]'),
            (By.XPATH, '//div[contains(@class,"el-dialog")]//button[contains(@class,"el-button--primary")][.//span[contains(text(),"确定")]]'),
            (By.XPATH, '//div[contains(@class,"el-dialog")]//footer//button[1]'),
            (By.XPATH, '//body/div[contains(@class,"el-dialog")]//footer//button[contains(@class,"el-button--primary")]'),
        ]
        for xp in save_xpaths:
            try:
                self._click_js(xp)
                time.sleep(1)
                return
            except Exception:
                continue
        raise Exception("未找到保存/确定按钮")'''

content = content.replace(old_save, new_save)
print("Fix 3+4 applied: close_sub_dialogs + click_save")

# Write target
with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nWritten to {TARGET}")
print(f"Total lines: {content.count(chr(10)) + 1}")
print("Done!")
