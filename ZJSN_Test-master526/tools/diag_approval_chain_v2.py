"""审批链配置深度诊断 v2 -- 翻页全量采集 + 步骤配置详情

采集:
  1. 翻页获取全部 14 条审批链
  2. 逐行点击"步骤配置"→ 采集审批步骤 + 审批人
  3. 搜索区完整字段
  4. 弹窗字段 + 适用部门可选项
"""
import os, sys, json, time, io
from datetime import datetime

# Fix GBK encoding issues on Windows
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

OUTPUT = os.path.join(os.path.dirname(__file__), "diag_approval_chain.json")


def js(driver, script, *args):
    try:
        return driver.execute_script(script, *args)
    except Exception as e:
        return f"JS_ERROR: {e}"


def get_page_rows(driver):
    """Get all visible table row data on current page"""
    return js(driver, """
        const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
        const data = [];
        rows.forEach((row, idx) => {
            const cells = row.querySelectorAll('td .cell');
            const rowData = {};
            cells.forEach((cell, ci) => {
                const switchEl = cell.querySelector('.el-switch');
                const text = cell.textContent.trim();
                const btns = Array.from(cell.querySelectorAll('button')).map(b => b.textContent.trim());
                rowData['col_' + ci] = {
                    text: text,
                    has_switch: !!switchEl,
                    switch_checked: switchEl ? switchEl.classList.contains('is-checked') : null,
                    buttons: btns
                };
            });
            data.push(rowData);
        });
        return data;
    """)


def get_pagination_info(driver):
    """Get current page, total pages"""
    return js(driver, """
        const pagers = document.querySelectorAll('.el-pager li');
        let current = 1, total = 1;
        pagers.forEach(li => {
            if (li.classList.contains('active') || li.classList.contains('is-active'))
                current = parseInt(li.textContent);
            const n = parseInt(li.textContent);
            if (!isNaN(n) && n > total) total = n;
        });
        return {current: current, total: total};
    """)


def click_next_page(driver):
    """Click next page button"""
    js(driver, """
        const btn = document.querySelector('.btn-next');
        if (btn && !btn.classList.contains('disabled')) btn.click();
    """)


def click_step_config(driver, row_index):
    """Click '步骤配置' button on given row (1-indexed).
    First closes any open overlay to avoid interference."""
    # Close any open overlay first
    close_any_overlay(driver)
    time.sleep(0.5)
    return js(driver, """
        const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
        if (arguments[0] > rows.length) return false;
        const cells = rows[arguments[0] - 1].querySelectorAll('td .cell');
        const lastCell = cells[cells.length - 1];
        const btns = lastCell.querySelectorAll('button');
        for (const b of btns) {
            if (b.textContent.includes('步骤配置')) {
                b.click();
                return true;
            }
        }
        return false;
    """, row_index)


def get_step_config_dialog(driver):
    """Get step configuration dialog/drawer content"""
    time.sleep(3)
    return js(driver, """
        // Try el-dialog first, then el-drawer
        let container = document.querySelector('.el-dialog:not([style*="display: none"])');
        if (!container) {
            container = document.querySelector('.el-drawer:not([style*="display: none"])');
        }
        if (!container) {
            // Try any visible overlay with a table
            const overlays = document.querySelectorAll('.el-overlay');
            for (const ov of overlays) {
                if (ov.offsetParent !== null && ov.querySelector('.el-table')) {
                    container = ov;
                    break;
                }
            }
        }
        if (!container) return {found: false};

        // Get title from dialog-title or drawer title
        const titleEl = container.querySelector('.el-dialog__title') ||
                        container.querySelector('.el-drawer__title') ||
                        container.querySelector('[class*="title"]');
        const title = titleEl ? titleEl.textContent.trim() : '';

        // Get the table
        const table = container.querySelector('.el-table');
        const headers = table ? Array.from(table.querySelectorAll('.el-table__header-wrapper th .cell'))
            .map(el => el.textContent.trim()).filter(Boolean) : [];

        const steps = [];
        if (table) {
            const rows = table.querySelectorAll('.el-table__body-wrapper tbody tr');
            rows.forEach(row => {
                const cells = row.querySelectorAll('td .cell');
                const step = {};
                cells.forEach((cell, ci) => {
                    const text = cell.textContent.trim();
                    const selectEl = cell.querySelector('.el-select');
                    step['col_' + ci] = {
                        text: text,
                        has_select: !!selectEl
                    };
                });
                steps.push(step);
            });
        }

        return {
            found: true,
            title: title,
            headers: headers,
            steps: steps,
            step_count: steps.length
        };
    """)


def close_any_overlay(driver):
    """Close any open dialog/drawer/overlay"""
    js(driver, """
        // Try dialog close button
        let closeBtn = document.querySelector('.el-dialog:not([style*="display: none"]) .el-dialog__headerbtn');
        if (closeBtn) { closeBtn.click(); return; }
        // Try drawer close button
        closeBtn = document.querySelector('.el-drawer:not([style*="display: none"]) .el-drawer__close-btn');
        if (closeBtn) { closeBtn.click(); return; }
        // Try any close/× button in visible overlay
        const overlays = document.querySelectorAll('.el-overlay');
        for (const ov of overlays) {
            if (ov.offsetParent === null) continue;
            const xBtn = ov.querySelector('.el-dialog__headerbtn, .el-drawer__close-btn, [class*="close"]');
            if (xBtn) { xBtn.click(); return; }
            const cancelBtn = Array.from(ov.querySelectorAll('button'))
                .find(b => b.textContent.includes('取消') || b.textContent.includes('关闭'));
            if (cancelBtn) { cancelBtn.click(); return; }
        }
    """)


def main():
    result = {
        "diagnosed_at": datetime.now().isoformat(),
        "page": "审批链配置",
        "route": "#/system/workflow/approval-chain",
        "chains": [],
        "pagination": {},
    }

    print("=" * 60)
    print("审批链配置 -- 深度诊断 v2（翻页 + 步骤配置）")
    print("=" * 60)

    base = BaseDriver()
    driver = base.open_browser()
    try:
        # ── Login + Navigate ──
        print("\n[1/4] 登录并导航...")
        ensure_logged_in(driver)
        nav = SidebarNavigator(driver)
        nav._navigate_by_js_hash("#/system/workflow/approval-chain", "diag-v2")
        time.sleep(4)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".el-table__body-wrapper"))
            )
        except:
            print("WARNING: 表格未加载")

        # ── 1. Table headers ──
        headers = js(driver, """
            return Array.from(document.querySelectorAll('.el-table__header-wrapper th .cell'))
                .map(el => el.textContent.trim()).filter(Boolean);
        """)
        result["table_headers"] = headers
        print(f"表头: {headers}")

        # ── 2. Paginate through all pages ──
        print("\n[2/4] 翻页采集全部审批链...")
        all_rows = []
        page = 1
        while True:
            pagination = get_pagination_info(driver)
            rows = get_page_rows(driver)
            print(f"  Page {page}: {len(rows)} rows, pagination={pagination}")
            all_rows.extend(rows)

            if pagination["current"] >= pagination["total"] or pagination["total"] <= 1:
                break
            click_next_page(driver)
            time.sleep(2)
            page += 1
            if page > 10:  # safety
                break

        result["pagination"] = {"total_pages": pagination.get("total", 1), "total_rows": len(all_rows)}
        print(f"  总计: {len(all_rows)} 条审批链")

        # Build chain list
        for i, row in enumerate(all_rows):
            name = row.get("col_1", {}).get("text", "") if "col_1" in row else ""
            code = row.get("col_2", {}).get("text", "") if "col_2" in row else ""
            dept = row.get("col_3", {}).get("text", "") if "col_3" in row else ""
            steps_count = row.get("col_4", {}).get("text", "") if "col_4" in row else ""
            status = "启用" if row.get("col_5", {}).get("switch_checked") else "停用"
            note = row.get("col_6", {}).get("text", "") if "col_6" in row else ""
            chain = {
                "index": i + 1,
                "name": name,
                "code": code,
                "department": dept,
                "steps_count": steps_count,
                "status": status,
                "note": note,
                "step_details": []
            }
            result["chains"].append(chain)
            print(f"  [{i+1}] {name} | {code} | {steps_count}步 | {status} | {note}")

        # ── 3. Click "步骤配置" for each chain ──
        print(f"\n[3/4] 逐行点击'步骤配置'采集审批步骤...")
        # Navigate back to page 1
        js(driver, """
            const firstPage = document.querySelector('.el-pager li.number');
            if (firstPage) firstPage.click();
        """)
        time.sleep(2)

        for chain_idx in range(len(result["chains"])):
            chain = result["chains"][chain_idx]
            row_num = chain_idx + 1

            # Check if we need to paginate
            pagination = get_pagination_info(driver)
            rows_on_page = len(get_page_rows(driver))
            if row_num > rows_on_page and pagination["current"] < pagination["total"]:
                click_next_page(driver)
                time.sleep(2)

            # Calculate row index on current page
            current_page = get_pagination_info(driver)["current"]
            rows_per_page = 10  # el-table default
            row_on_page = ((row_num - 1) % rows_per_page) + 1

            print(f"  [{chain['index']}] {chain['name']} -- 点击步骤配置...")

            clicked = click_step_config(driver, row_on_page)
            if not clicked:
                print(f"    WARN: 步骤配置按钮未找到")
                chain["step_details"] = {"error": "button not found"}
                continue

            step_data = get_step_config_dialog(driver)
            if not step_data.get("found"):
                print(f"    WARN: 步骤配置弹窗未打开")
                chain["step_details"] = {"error": "dialog not found"}
                continue

            chain["step_dialog_title"] = step_data.get("title", "")
            chain["step_headers"] = step_data.get("headers", [])
            chain["step_details"] = []

            for si, step in enumerate(step_data.get("steps", [])):
                detail = {}
                for ck, cv in step.items():
                    detail[ck] = cv
                chain["step_details"].append(detail)
                # Print readable summary
                texts = [v["text"] for v in step.values()]
                print(f"      步骤{si+1}: {texts}")

            print(f"    → {len(chain['step_details'])} 个审批步骤")
            close_any_overlay(driver)
            time.sleep(1.5)

        # ── 4. Search area & dialog fields ──
        print(f"\n[4/4] 采集搜索区和弹窗字段...")
        result["search_area"] = js(driver, """
            const formItems = document.querySelectorAll('.el-form-item');
            const items = [];
            formItems.forEach(fi => {
                const label = fi.querySelector('.el-form-item__label');
                const input = fi.querySelector('input');
                const select = fi.querySelector('.el-select');
                items.push({
                    label: label ? label.textContent.trim() : '',
                    type: select ? 'el-select' : (input ? 'el-input' : 'unknown'),
                    placeholder: input ? input.placeholder : ''
                });
            });
            return items;
        """)

        # ── Save ──
        print("\n" + "=" * 60)
        print(f"诊断完成，保存到 {OUTPUT}")

    except Exception as e:
        import traceback
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        print(f"\nERROR: {e}")
    finally:
        base.close_browser()

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("Done.")


if __name__ == "__main__":
    main()
