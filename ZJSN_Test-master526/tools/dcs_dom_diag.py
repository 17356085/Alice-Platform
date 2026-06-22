"""DCS DOM 诊断脚本 — 扫描 5 页面，输出实际元素状态"""
import json, sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

from selenium.webdriver.common.by import By
from base.browser_driver import BaseDriver, ensure_logged_in
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PAGES = {
    "all-data": "#/all-data",
    "common-data": "#/common-data",
    "monitor": "#/monitor",
    "point-config": "#/point-config",
    "upload-log": "#/upload-log",
}

DIAGNOSTICS = {
    "search_input": (By.CSS_SELECTOR, 'input[placeholder*="点位"], input[placeholder*="名称"], input[placeholder*="参数"], input[placeholder*="错误"], input[placeholder*="设备"]'),
    "buttons": (By.XPATH, '//button[contains(@class,"el-button")]'),
    "table": (By.CSS_SELECTOR, '.el-table'),
    "table_rows": (By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row'),
    "cards": (By.CSS_SELECTOR, '.el-card, [class*="card"]'),
    "pagination": (By.CSS_SELECTOR, '.el-pagination'),
    "selects": (By.CSS_SELECTOR, '.el-select'),
    "date_pickers": (By.CSS_SELECTOR, '.el-date-editor'),
    "dialogs": (By.CSS_SELECTOR, '.el-dialog'),
    "loading": (By.CSS_SELECTOR, '.el-loading-mask'),
}

base = BaseDriver()
driver = base.open_browser()
ensure_logged_in(driver)

results = {}

for page_name, route in PAGES.items():
    print(f"\n{'='*60}")
    print(f"PAGE: {page_name} → {route}")
    print(f"{'='*60}")

    driver.execute_script(f"window.location.hash = '{route}';")
    time.sleep(3)

    page_result = {}

    for diag_name, (by, selector) in DIAGNOSTICS.items():
        try:
            els = driver.find_elements(by, selector)
            count = len(els)
            texts = []
            for el in els[:10]:
                try:
                    t = el.text[:80] if el.text else ""
                    if t.strip():
                        texts.append(t)
                except:
                    pass

            page_result[diag_name] = {"count": count, "sample_texts": texts[:5]}

            if diag_name == "buttons":
                page_result[diag_name]["all_button_texts"] = texts

            print(f"  {diag_name}: {count} found {texts[:3] if texts else ''}")
        except Exception as e:
            page_result[diag_name] = {"count": "ERROR", "error": str(e)[:100]}
            print(f"  {diag_name}: ERROR {str(e)[:100]}")

    # Special: check for add/edit/delete buttons
    for btn_text in ["新增", "编辑", "删除", "导入", "导出", "搜索", "重置", "刷新", "详情", "清空"]:
        try:
            btns = driver.find_elements(By.XPATH, f'//button[contains(.,"{btn_text}")]')
            if btns:
                page_result[f"btn_{btn_text}"] = len(btns)
                print(f"  btn_{btn_text}: {len(btns)} visible")
        except:
            pass

    # Check stat cards for upload-log
    if page_name == "upload-log":
        for stat_type in ["total", "success", "fail", "abnormal"]:
            for sel in [f'.stat-{stat_type}', f'.{stat_type}-count']:
                try:
                    els = driver.find_elements(By.CSS_SELECTOR, sel)
                    if els:
                        page_result[f"stat_{stat_type}"] = {"count": len(els), "text": els[0].text[:60]}
                        print(f"  stat_{stat_type}: {els[0].text[:60]}")
                except:
                    pass

    results[page_name] = page_result

driver.quit()

print("\n\n===== DIAGNOSTIC SUMMARY =====")
print(json.dumps(results, ensure_ascii=False, indent=2))
