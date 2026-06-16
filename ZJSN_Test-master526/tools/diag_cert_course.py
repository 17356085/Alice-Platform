"""诊断 certificate + course 页面 DOM — 查找 dialog submit 超时 + 按钮 XPath 不匹配根因

Usage: python tools/diag_cert_course.py
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from selenium.webdriver.common.by import By

driver = None
try:
    base = BaseDriver()
    driver = base.open_browser()
    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)

    # ══════════════════════════════════════════════════════════════════
    # 1. 诊断 certificate 页面 — 新增弹窗 DOM
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("【诊断 1】certificate — 新增证书弹窗 DOM")
    print("=" * 60)

    nav._navigate_by_js_hash("#/personnel/training/certificate", "certificate")
    time.sleep(3)

    # 找新增证书按钮
    from base.base_page import BasePage
    bp = BasePage(driver)
    bp.wait_vue_stable()

    # 打印页面上所有 button 文本
    buttons = driver.find_elements(By.XPATH, '//button')
    print("\n--- 证书管理页面所有按钮 ---")
    for i, btn in enumerate(buttons):
        try:
            txt = (btn.text or '').strip()
            cls = btn.get_attribute('class') or ''
            if txt:
                print(f"  [{i}] text='{txt[:50]}' class='{cls[:80]}' visible={btn.is_displayed()}")
        except Exception:
            pass

    # 点击新增证书按钮
    add_btn = None
    for btn in buttons:
        try:
            if '新增' in (btn.text or '') and btn.is_displayed():
                add_btn = btn
                break
        except Exception:
            pass

    if add_btn:
        print(f"\n找到新增按钮: '{add_btn.text}' → JS click")
        driver.execute_script("arguments[0].click();", add_btn)
        time.sleep(3)

        # 弹窗 DOM
        dialogs = driver.find_elements(By.CSS_SELECTOR, '.el-dialog, .el-overlay-dialog, [role="dialog"]')
        print(f"\n--- 弹窗数量: {len(dialogs)} ---")
        for i, dlg in enumerate(dialogs):
            try:
                if dlg.is_displayed():
                    title = dlg.find_element(By.CSS_SELECTOR, '.el-dialog__title, [class*="title"]')
                    print(f"  可见弹窗 [{i}]: title='{(title.text or '').strip()[:60]}'")
                    # 打印弹窗内所有按钮
                    dlg_btns = dlg.find_elements(By.XPATH, './/button')
                    print(f"  弹窗内按钮:")
                    for j, db in enumerate(dlg_btns):
                        try:
                            print(f"    [{j}] text='{(db.text or '').strip()[:40]}' class='{(db.get_attribute('class') or '')[:60]}'")
                        except Exception:
                            pass
            except Exception as e:
                print(f"  弹窗 [{i}]: {e}")

        # 检查弹窗 primary 按钮和尝试 JS click
        primary_btns = driver.find_elements(By.CSS_SELECTOR, '.el-dialog .el-button--primary, [role="dialog"] .el-button--primary')
        print(f"\n弹窗内 primary 按钮数: {len(primary_btns)}")
        for pb in primary_btns:
            try:
                if pb.is_displayed():
                    print(f"  primary btn: text='{(pb.text or '').strip()[:40]}' enabled={pb.is_enabled()}")
            except Exception:
                pass
    else:
        print("❌ 未找到新增证书按钮!")

    # ══════════════════════════════════════════════════════════════════
    # 2. 诊断 course 页面 — 按钮 XPath
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("【诊断 2】course — 新增课程按钮 XPath")
    print("=" * 60)

    nav._navigate_by_js_hash("#/personnel/training/course", "course")
    time.sleep(3)
    bp.wait_vue_stable()

    buttons2 = driver.find_elements(By.XPATH, '//button')
    print(f"\n--- 课程管理页面所有按钮 (共 {len(buttons2)} 个) ---")
    for i, btn in enumerate(buttons2):
        try:
            txt = (btn.text or '').strip()
            cls = btn.get_attribute('class') or ''
            outer = btn.get_attribute('outerHTML') or ''
            if txt or 'el-button' in cls:
                print(f"  [{i}] text='{txt[:60]}' class='{cls[:80]}' visible={btn.is_displayed()}")
                # 检查 XPath 是否匹配
                span = btn.find_elements(By.XPATH, './/span')
                span_texts = [s.text.strip() for s in span if s.text.strip()]
                if span_texts:
                    print(f"       inner spans: {span_texts[:3]}")
        except Exception:
            pass

    # 尝试各种 XPath 查找新增按钮
    xpath_variants = [
        '//button[contains(.,"新增")]',
        '//button[.//span[contains(.,"新增")]]',
        '//button[normalize-space(.)="新增课程" or normalize-space(.)="新增"]',
        '//button[contains(@class,"el-button--primary")][contains(.,"新增")]',
        '//*[contains(@class,"el-button")][contains(.,"新增")]',
    ]
    print("\n--- XPath 变体匹配测试 ---")
    for xp in xpath_variants:
        els = driver.find_elements(By.XPATH, xp)
        visible = [e for e in els if e.is_displayed()]
        print(f"  '{xp[:70]}...' → {len(els)} found, {len(visible)} visible")

except Exception as e:
    print(f"诊断异常: {e}")
    import traceback
    traceback.print_exc()
finally:
    if driver:
        driver.quit()
    print("\n诊断完成")
