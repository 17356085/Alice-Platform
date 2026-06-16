"""诊断 P2 5 个页面的搜索区元素，输出真实 placeholder 和按钮文本。

用法: cd ZJSN_Test-master526 && python tools/diagnose_warehouse_p2.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from base.base_page import BasePage

PAGES = [
    ("hazard-stock",    "库管管理", "环保危废管理", "库存查询",   "#/warehouse/hazard/stock"),
    ("hazard-io-record","库管管理", "环保危废管理", "出入库明细", "#/warehouse/hazard/io-record"),
    ("hazard-item",     "库管管理", "环保危废管理", "物品管理",   "#/warehouse/hazard/item"),
    ("reagent-item",    "库管管理", "三剂消耗管理", "物品管理",   "#/warehouse/reagent/item"),
    ("reagent-fill",    "库管管理", "三剂消耗管理", "装填管理",   "#/warehouse/reagent/fill"),
]

def diagnose_page(driver, page_id, top_menu, sub_menu, item_name, href):
    print(f"\n{'='*60}")
    print(f"[DIAG] {page_id}  ->  {top_menu} / {sub_menu} / {item_name}")
    print(f"{'='*60}")

    nav = SidebarNavigator(driver)
    bp = BasePage(driver)

    nav._navigate_by_js_hash(href, page_id)
    bp.wait_vue_stable()
    bp._wait_loading_gone(timeout=15)
    time.sleep(0.5)

    # 1. all input placeholders
    inputs = driver.execute_script("""
        var inputs = document.querySelectorAll('input[placeholder]');
        var results = [];
        inputs.forEach(function(el) {
            var ph = el.getAttribute('placeholder');
            if (ph && results.indexOf(ph) === -1) results.push(ph);
        });
        return results;
    """)
    print(f"  [inputs] {inputs}")

    # 2. all button texts on page (deduped, <=10 chars)
    buttons = driver.execute_script("""
        var btns = document.querySelectorAll('button');
        var texts = [];
        btns.forEach(function(el) {
            var t = el.textContent.trim();
            if (t && t.length <= 10 && texts.indexOf(t) === -1) texts.push(t);
        });
        return texts;
    """)
    print(f"  [buttons] {buttons}")

    # 3. table column count
    col_count = driver.execute_script(
        "return document.querySelectorAll('.el-table__header-wrapper th').length;"
    )
    print(f"  [columns] {col_count}")

    # 4. row count
    row_count = driver.execute_script(
        "return document.querySelectorAll('.el-table__body-wrapper tbody tr').length;"
    )
    print(f"  [rows] {row_count}")

    return {
        "page_id": page_id,
        "placeholders": inputs,
        "buttons": buttons,
        "columns": col_count,
        "rows": row_count,
    }


def main():
    results = []
    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        from selenium.webdriver.support.ui import WebDriverWait
        try:
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script(
                    "return document.querySelectorAll('.el-menu-item, .el-sub-menu__title').length > 5"
                )
            )
        except Exception:
            time.sleep(3)

        for page_id, top, sub, item, href in PAGES:
            try:
                r = diagnose_page(driver, page_id, top, sub, item, href)
                results.append(r)
            except Exception as e:
                print(f"  [ERROR] {e}")
                results.append({"page_id": page_id, "error": str(e)})

    finally:
        base.close_browser()

    out_path = os.path.join(os.path.dirname(__file__), "p2_diagnosis.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
