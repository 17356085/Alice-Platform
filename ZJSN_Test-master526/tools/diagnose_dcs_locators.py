"""诊断 DCS 5 页面实际 DOM，输出关键元素定位信息"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base.browser_driver import BaseDriver, ensure_logged_in
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ROUTES = {
    "monitor": "#/monitor",
    "all-data": "#/all-data",
    "common-data": "#/common-data",
    "point-config": "#/point-config",
    "upload-log": "#/upload-log",
}

def diagnose_page(driver, page_name, route):
    """提取页面关键 DOM 信息"""
    print(f"\n{'='*60}")
    print(f"  PAGE: {page_name} ({route})")
    print(f"{'='*60}")

    driver.execute_script(f"window.location.hash = '{route}';")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.el-table, .el-card, .el-pagination, .el-input'))
    )
    import time; time.sleep(0.5)

    # 收集所有 input placeholder
    inputs = driver.find_elements(By.CSS_SELECTOR, 'input[placeholder]')
    print("\n  [INPUTS with placeholder]")
    for inp in inputs:
        ph = inp.get_attribute('placeholder')
        name = inp.get_attribute('name') or ''
        cls = inp.get_attribute('class')[:80] if inp.get_attribute('class') else ''
        if ph:
            print(f"    placeholder='{ph}' name='{name}' class='{cls}'")

    # 收集所有 button span
    buttons = driver.find_elements(By.CSS_SELECTOR, 'button span')
    print("\n  [BUTTONS with span text]")
    for btn in buttons:
        text = btn.text.strip()
        if text:
            parent_cls = btn.find_element(By.XPATH, '..').get_attribute('class')[:60] if btn.find_element(By.XPATH, '..') else ''
            print(f"    text='{text}' parent_class='{parent_cls}'")

    # 表格列
    table_headers = driver.find_elements(By.CSS_SELECTOR, '.el-table__header th .cell')
    if table_headers:
        print("\n  [TABLE HEADERS]")
        for th in table_headers:
            print(f"    '{th.text.strip()}'")

    # 表格第一行
    first_row = driver.find_elements(By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')
    if first_row:
        print(f"\n  [TABLE ROWS] count={len(first_row)}")
        cells = first_row[0].find_elements(By.TAG_NAME, 'td')
        print("    Row[0]:", [c.text[:30] for c in cells])

    # 检查是否有新增按钮
    add_btns = driver.find_elements(By.XPATH, '//button[.//span[text()="新增"] or .//span[text()="新增点位"] or .//span[text()="新增参数"]]')
    if add_btns:
        print(f"\n  [ADD BUTTONS] found {len(add_btns)}")

    # 分页
    pagination = driver.find_elements(By.CSS_SELECTOR, '.el-pagination__total')
    if pagination:
        print(f"\n  [PAGINATION] {pagination[0].text}")

    # 卡片（monitor/common-data）
    cards = driver.find_elements(By.CSS_SELECTOR, '.el-card, [class*="card"]:not(.el-card__body)')
    if cards:
        print(f"\n  [CARDS] count={len(cards)}")
        if cards:
            print(f"    Card[0] text: {cards[0].text[:100]}")


if __name__ == '__main__':
    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        for name, route in ROUTES.items():
            try:
                diagnose_page(driver, name, route)
            except Exception as e:
                print(f"  ERROR: {e}")
    finally:
        base.close_browser()
