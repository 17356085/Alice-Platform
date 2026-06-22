"""DCS 定位器诊断 — 逐页检查 6 个 skip 涉及的定位器
用法: cd ZJSN_Test-master526 && python tools/dcs_locator_diag.py
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium.webdriver.common.by import By
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator

RESULTS = {}
base = BaseDriver()
driver = base.open_browser()
ensure_logged_in(driver)

# ── Helper: proper navigation ──
def go_to(route):
    """Proper hash navigation: go to welcome first, then set hash"""
    driver.execute_script("window.location.hash = '#/welcome';")
    time.sleep(0.5)
    driver.execute_script(f"window.location.hash = '{route}';")
    # Wait for Vue Router
    for _ in range(20):
        h = driver.execute_script("return window.location.hash;")
        if route in h:
            break
        time.sleep(0.3)
    time.sleep(2)

# ── Helper: check element presence ──
def check(desc, by, selector):
    """Return {count, visible, sample_texts}"""
    try:
        els = driver.find_elements(by, selector)
        visible = [e for e in els if e.is_displayed()]
        texts = []
        for e in visible[:8]:
            t = e.text.strip()[:60]
            if t:
                texts.append(t)
        return {"count_total": len(els), "count_visible": len(visible), "sample_texts": texts}
    except Exception as e:
        return {"error": str(e)[:120]}

# ══════════════════════════════════════════════════════════
#  PAGE 1: all-data (#/all-data)
# ══════════════════════════════════════════════════════════
print("=" * 60)
print("PAGE 1: all-data")
go_to("#/all-data")
r = {}

# Issue: test_006_select_row — 表格行是否存在?
r["table"] = check("table", By.CSS_SELECTOR, ".el-table")
r["table_rows"] = check("table_rows", By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")
r["table_rows_el"] = check("table_rows_el", By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr.el-table__row")
r["checkbox"] = check("checkbox", By.CSS_SELECTOR, ".el-checkbox__input")
r["any_tr"] = check("any_tr", By.TAG_NAME, "tr")

# Dump table body HTML for debugging
try:
    tbody = driver.find_element(By.CSS_SELECTOR, ".el-table__body-wrapper")
    r["tbody_sample"] = tbody.get_attribute("innerHTML")[:500]
except:
    r["tbody_sample"] = "NOT FOUND"

# Buttons
for btn in ["新增", "编辑", "删除", "导入", "导出", "搜索", "重置", "刷新"]:
    r[f"btn_{btn}"] = check(f"btn_{btn}", By.XPATH,
        f'//button[contains(normalize-space(),"{btn}")]')

RESULTS["all-data"] = r
print(f"  table={r['table']['count_total']}, rows_el={r['table_rows_el']['count_visible']}, any_tr={r['any_tr']['count_total']}")
print(f"  buttons: {[k for k,v in r.items() if k.startswith('btn_') and v.get('count_visible',0)>0]}")

# ══════════════════════════════════════════════════════════
#  PAGE 2: common-data (#/common-data)
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PAGE 2: common-data")
go_to("#/common-data")
r = {}

# Issue: test_004_click_card — 卡片定位器
r["cards_el"] = check("el-card", By.CSS_SELECTOR, ".el-card")
r["cards_point"] = check("point-card", By.CSS_SELECTOR, ".point-card, .data-card")
r["cards_any"] = check("any-card", By.CSS_SELECTOR, '[class*="card"]')
r["search_input"] = check("search", By.CSS_SELECTOR, 'input[placeholder*="点位"], input[placeholder*="名称"]')

# Card details
for card_sel in ['.el-card', '.point-card', '.data-card', '[class*="card"]']:
    try:
        cards = driver.find_elements(By.CSS_SELECTOR, card_sel)
        if cards:
            r[f"card_{card_sel[:20]}_count"] = len(cards)
            r[f"card_{card_sel[:20]}_text0"] = cards[0].text[:100] if cards[0].text else "(empty)"
    except:
        pass

# Buttons
for btn in ["新增", "删除", "清空", "恢复默认", "搜索", "重置"]:
    r[f"btn_{btn}"] = check(f"btn_{btn}", By.XPATH,
        f'//button[contains(normalize-space(),"{btn}")]')

RESULTS["common-data"] = r
print(f"  cards_el={r['cards_el']['count_visible']}, cards_point={r['cards_point']['count_visible']}")
print(f"  search_input={r['search_input']['count_visible']}")

# ══════════════════════════════════════════════════════════
#  PAGE 3: point-config (#/point-config)
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PAGE 3: point-config")
go_to("#/point-config")
r = {}

# Issue: test_002_search — 搜索按钮 DOM
r["table_rows"] = check("rows", By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr.el-table__row")
r["search_input"] = check("search", By.CSS_SELECTOR, 'input[placeholder*="点位"], input[placeholder*="名称"]')

# ALL buttons — see what's available
all_btns = driver.find_elements(By.XPATH, '//button')
r["all_buttons"] = [b.text.strip()[:30] for b in all_btns if b.text.strip() and b.is_displayed()]

# Try different search button locators
for loc_name, by, sel in [
    ("xpath_search", By.XPATH, '//button[normalize-space(.//span)="搜索"]'),
    ("xpath_query", By.XPATH, '//button[normalize-space(.//span)="查询"]'),
    ("xpath_contains", By.XPATH, '//button[contains(normalize-space(),"搜索") or contains(normalize-space(),"查询")]'),
    ("css_btn", By.CSS_SELECTOR, 'button.el-button--primary'),
]:
    r[f"search_{loc_name}"] = check(loc_name, by, sel)

RESULTS["point-config"] = r
print(f"  rows={r['table_rows']['count_visible']}, all_btns={r['all_buttons'][:10]}")

# ══════════════════════════════════════════════════════════
#  PAGE 4: upload-log (#/upload-log)
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PAGE 4: upload-log")
go_to("#/upload-log")
r = {}

# Issue: test_003_search, test_006_detail
r["table_rows"] = check("rows", By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr.el-table__row")
r["table"] = check("table", By.CSS_SELECTOR, ".el-table")

all_btns = driver.find_elements(By.XPATH, '//button')
r["all_buttons"] = [b.text.strip()[:30] for b in all_btns if b.text.strip() and b.is_displayed()]

# Search locators
for loc_name, by, sel in [
    ("xpath_search", By.XPATH, '//button[normalize-space(.//span)="搜索"]'),
    ("xpath_query", By.XPATH, '//button[normalize-space(.//span)="查询"]'),
    ("xpath_contains", By.XPATH, '//button[contains(normalize-space(),"搜索") or contains(normalize-space(),"查询")]'),
]:
    r[f"search_{loc_name}"] = check(loc_name, by, sel)

# Detail button — check row buttons
try:
    rows = driver.find_elements(By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr.el-table__row")
    if rows:
        row_btns = rows[0].find_elements(By.TAG_NAME, "button")
        r["first_row_buttons"] = [b.text.strip()[:20] for b in row_btns if b.text.strip()]
        r["first_row_html"] = rows[0].get_attribute("innerHTML")[:400]
    else:
        r["first_row_buttons"] = "NO ROWS"
except Exception as e:
    r["first_row_error"] = str(e)[:200]

# Stat cards
for stat_sel in ['.stat-total', '.stat-success', '.stat-fail', '.stat-abnormal',
                 '.el-statistic__content', '.total-count', '.success-count', '.fail-count']:
    try:
        el = driver.find_element(By.CSS_SELECTOR, stat_sel)
        r[f"stat_{stat_sel[:15]}"] = el.text[:40] if el.text else "(empty)"
    except:
        pass

RESULTS["upload-log"] = r
print(f"  rows={r['table_rows']['count_visible']}, all_btns={r['all_buttons'][:10]}")
print(f"  first_row_btns={r.get('first_row_buttons','N/A')}")

# ── Cleanup ──
driver.quit()

# ── Summary ──
print("\n\n" + "=" * 60)
print("DIAGNOSTIC SUMMARY")
print("=" * 60)
for page, data in RESULTS.items():
    print(f"\n--- {page} ---")
    # Print key findings compactly
    for k, v in data.items():
        if isinstance(v, dict) and v.get("count_visible", 0) > 0:
            texts = v.get("sample_texts", [])
            print(f"  {k}: {v.get('count_visible')} visible {texts[:3] if texts else ''}")
        elif isinstance(v, list):
            print(f"  {k}: {v}")
        elif isinstance(v, str) and len(v) < 100:
            print(f"  {k}: {v}")

# Save full JSON
with open("tools/dcs_locator_diag_result.json", "w", encoding="utf-8") as f:
    json.dump(RESULTS, f, ensure_ascii=False, indent=2)
print("\nFull results → tools/dcs_locator_diag_result.json")
