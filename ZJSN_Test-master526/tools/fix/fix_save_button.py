"""Fix SAVE_BUTTON locator and click_save xpaths to handle div.el-dialog__footer instead of <footer> tag"""
import re

path = r'D:\ZJSN_Test-master\page\person_page\TrainPlanPage.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: SAVE_BUTTON locator (change //footer --> SVG_J... no, use class-based footer selector)
old_save_btn = '''    SAVE_BUTTON = (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//footer//button[.//span[contains(text(),"保存") or contains(text(),"确定")]]')'''

new_save_btn = '''    SAVE_BUTTON = (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//*[contains(@class,"el-dialog__footer") or self::footer]//button[.//span[contains(text(),"保存") or contains(text(),"确定")]]')'''

if old_save_btn in content:
    content = content.replace(old_save_btn, new_save_btn)
    print("SAVE_BUTTON locator fixed")
else:
    print("SAVE_BUTTON not found, checking actual content...")
    for i, line in enumerate(content.split('\n')):
        if 'SAVE_BUTTON' in line and 'footer' in line:
            print(f"  Line {i}: {line}")

# Fix 2: click_save method - replace all footer xpaths
old_click_save = '''    def click_save(self):
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

new_click_save = '''    def click_save(self):
        """点击弹窗保存/确定按钮"""
        # 先关闭可能残留的子弹窗，确保主弹窗可操作
        self.close_sub_dialogs()
        time.sleep(0.5)

        save_xpaths = [
            self.SAVE_BUTTON,
            (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//*[contains(@class,"el-dialog__footer") or self::footer]//button[.//span[contains(text(),"保存") or contains(text(),"确定")]]'),
            (By.XPATH, '//div[contains(@class,"el-dialog")]//*[contains(@class,"el-dialog__footer") or self::footer]//button[.//span[contains(text(),"保存") or contains(text(),"确定")]]'),
            (By.XPATH, '//div[contains(@class,"el-dialog")]//button[contains(@class,"el-button--primary")][.//span[contains(text(),"保存") or contains(text(),"确定")]]'),
            (By.XPATH, '//div[contains(@class,"el-dialog")]//button[.//span[contains(text(),"保存")]]'),
            (By.XPATH, '//div[contains(@class,"el-dialog")]//button[contains(@class,"el-button--primary")]'),
        ]
        for xp in save_xpaths:
            try:
                self._click_js(xp)
                time.sleep(1)
                return
            except Exception:
                continue
        raise Exception("未找到保存/确定按钮")'''

if old_click_save in content:
    content = content.replace(old_click_save, new_click_save)
    print("click_save method fixed")
else:
    print("click_save text not found, checking...")
    if 'def click_save' in content:
        idx = content.find('def click_save')
        end = content.find('def click_cancel', idx)
        print(content[idx:end])

# Fix 3: Also fix CANCEL_BUTTON and other locators
content = content.replace(
    "//footer//button[.//span[contains(text(),\"取消\")]]",
    "//*[contains(@class,\"el-dialog__footer\") or self::footer]//button[.//span[contains(text(),\"取消\")]]"
)
print("CANCEL_BUTTON locator fixed")

# Fix 4: TARGET_SELECT_CONFIRM - also uses //footer
content = content.replace(
    "//footer//button[.//span[contains(text(),\"确定\")]]",
    "//*[contains(@class,\"el-dialog__footer\") or self::footer]//button[.//span[contains(text(),\"确定\")]]"
)
print("TARGET_SELECT_CONFIRM locator fixed")

# Write back
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\nAll save button fixes applied!")
print(f"Total lines: {content.count(chr(10))}")
