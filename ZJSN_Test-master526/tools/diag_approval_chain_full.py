"""审批链配置完整诊断 v3 — CDP点击 + 步骤配置面板采集

采集:
  1. 翻页获取全部 14 条审批链
  2. CDP点击每行"步骤配置"→ 读取 step-editor 面板内容(审批步骤+审批人)
"""
import os, sys, json, time, io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

OUTPUT = os.path.join(os.path.dirname(__file__), "diag_approval_chain_full.json")


def cdp_click(driver, x, y):
    """Send native mouse click via CDP"""
    driver.execute_cdp_cmd('Input.dispatchMouseEvent', {
        'type': 'mousePressed', 'x': x, 'y': y,
        'button': 'left', 'clickCount': 1
    })
    time.sleep(0.08)
    driver.execute_cdp_cmd('Input.dispatchMouseEvent', {
        'type': 'mouseReleased', 'x': x, 'y': y,
        'button': 'left', 'clickCount': 1
    })


def get_button_rect(driver, row_index, button_text):
    """Get center coordinates of a button in a given row"""
    return driver.execute_script("""
        const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
        if (arguments[0] > rows.length) return null;
        const cells = rows[arguments[0] - 1].querySelectorAll('td .cell');
        const lastCell = cells[cells.length - 1];
        const btns = lastCell.querySelectorAll('button');
        for (const b of btns) {
            if (b.textContent.includes(arguments[1])) {
                const r = b.getBoundingClientRect();
                return {x: r.left + r.width/2, y: r.top + r.height/2};
            }
        }
        return null;
    """, row_index, button_text)


def close_step_editor(driver):
    """Close the step editor panel if open (find close button or click outside)"""
    driver.execute_script("""
        // Try to find a close/back button in the step editor
        const closeBtn = document.querySelector('.step-editor .el-button, .step-editor button[class*="back"], .step-editor [class*="close"]');
        if (closeBtn && closeBtn.offsetParent !== null) {
            closeBtn.click();
            return 'clicked_close';
        }
        // Try clicking the "返回" or "取消" button
        const btns = document.querySelectorAll('.step-editor button');
        for (const b of btns) {
            if (b.textContent.includes('返回') || b.textContent.includes('取消') || b.textContent.includes('关闭')) {
                if (b.offsetParent !== null) { b.click(); return 'clicked_' + b.textContent.trim(); }
            }
        }
        return 'no_close_found';
    """)


def get_step_editor_data(driver):
    """Read step configuration data from the inline step-editor panel"""
    return driver.execute_script("""
        const editor = document.querySelector('.step-editor');
        if (!editor || editor.offsetParent === null) return {found: false};

        const result = {found: true};

        // Get step cards
        const cards = editor.querySelectorAll('.step-card');
        result.steps = [];
        cards.forEach((card, i) => {
            const step = {};

            // Step number
            const numEl = card.querySelector('.step-number');
            step.number = numEl ? numEl.textContent.trim() : '';

            // Try to read form fields inside the card
            const formItems = card.querySelectorAll('.el-form-item');
            formItems.forEach(fi => {
                const label = fi.querySelector('.el-form-item__label');
                const input = fi.querySelector('input');
                const select = fi.querySelector('.el-select');
                const textarea = fi.querySelector('textarea');

                const fieldName = label ? label.textContent.trim() : '';
                let value = '';
                if (input) value = input.value;
                else if (textarea) value = textarea.value;
                else if (select) {
                    const selectedEl = select.querySelector('.el-select__selected-item, .el-select__input');
                    value = selectedEl ? (selectedEl.value || selectedEl.textContent || '').trim() : '';
                }

                if (fieldName) {
                    step[fieldName] = value;
                }
            });

            // Get all text content as fallback
            step.raw_text = card.textContent.trim().substring(0, 200);

            result.steps.push(step);
        });

        // Check for add-step button
        const addBar = editor.querySelector('.add-step-bar');
        result.has_add_step = !!addBar;

        // Also get any other info (like approval chain name displayed)
        const titleEl = editor.querySelector('[class*="title"], h3, h4');
        result.title = titleEl ? titleEl.textContent.trim() : '';

        return result;
    """)


def main():
    result = {
        "diagnosed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "page": "审批链配置 — 步骤配置诊断",
        "chains": []
    }

    print("=" * 60)
    print("审批链配置 — 完整诊断 v3 (CDP点击 + 步骤配置)")
    print("=" * 60)

    base = BaseDriver()
    driver = base.open_browser()
    try:
        # Login + Navigate
        print("\n[1/3] 登录并导航...")
        ensure_logged_in(driver)
        nav = SidebarNavigator(driver)
        nav._navigate_by_js_hash("#/system/workflow/approval-chain", "diag-full")
        time.sleep(4)

        # Collect table data from all pages
        print("[2/3] 翻页采集14条审批链 + 逐行步骤配置...")
        all_chains = []
        page = 1
        while True:
            rows_data = driver.execute_script("""
                const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
                return rows.length;
            """)

            for row_idx in range(1, rows_data + 1):
                row_data = driver.execute_script("""
                    const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
                    const cells = rows[arguments[0] - 1].querySelectorAll('td .cell');
                    const data = {};
                    cells.forEach((cell, ci) => {
                        const switchEl = cell.querySelector('.el-switch');
                        data['col_' + ci] = {
                            text: cell.textContent.trim(),
                            has_switch: !!switchEl,
                            switch_checked: switchEl ? switchEl.classList.contains('is-checked') : null
                        };
                    });
                    return data;
                """, row_idx)

                name = row_data.get("col_1", {}).get("text", "")
                code = row_data.get("col_2", {}).get("text", "")
                dept = row_data.get("col_3", {}).get("text", "")
                steps_count = row_data.get("col_4", {}).get("text", "")
                status = "启用" if row_data.get("col_5", {}).get("switch_checked") else "停用"
                note = row_data.get("col_6", {}).get("text", "")

                chain = {
                    "index": len(all_chains) + 1,
                    "name": name,
                    "code": code,
                    "department": dept,
                    "steps_count": steps_count,
                    "status": status,
                    "note": note,
                    "step_details": None
                }

                print(f"  [{chain['index']}] {name} | {code}")

                # Click "步骤配置" via CDP
                rect = get_button_rect(driver, row_idx, "步骤配置")
                if rect:
                    cdp_click(driver, rect['x'], rect['y'])
                    time.sleep(2)

                    step_data = get_step_editor_data(driver)
                    if step_data.get("found"):
                        chain["step_details"] = step_data["steps"]
                        for si, s in enumerate(step_data["steps"]):
                            fields = [f"{k}={v}" for k, v in s.items() if k not in ("raw_text", "number")]
                            print(f"      步骤{si+1}: {fields}")
                    else:
                        chain["step_details"] = "step_editor_not_found"

                    # Close step editor
                    close_result = close_step_editor(driver)
                    time.sleep(2)
                    # Wait for table to re-render
                    for _ in range(10):
                        rows_count = driver.execute_script(
                            "return document.querySelectorAll('.el-table__body-wrapper tbody tr').length;"
                        )
                        if rows_count > 0:
                            break
                        time.sleep(0.5)
                else:
                    chain["step_details"] = "button_not_found"
                    print(f"      WARN: 按钮未找到")

                all_chains.append(chain)

            # Pagination check
            pagination = driver.execute_script("""
                const pagers = document.querySelectorAll('.el-pager li');
                let current = 1, total = 1;
                pagers.forEach(li => {
                    if (li.classList.contains('active') || li.classList.contains('is-active'))
                        current = parseInt(li.textContent);
                    const n = parseInt(li.textContent);
                    if (!isNaN(n) && n > total) total = n;
                });
                return {current, total};
            """)
            print(f"  Page {pagination['current']}/{pagination['total']} done, {len(all_chains)} chains so far")

            if pagination["current"] >= pagination["total"]:
                break

            # Click next page
            driver.execute_script("""
                const btn = document.querySelector('.btn-next');
                if (btn && !btn.classList.contains('disabled')) btn.click();
            """)
            time.sleep(2)
            page += 1
            if page > 5:
                break

        result["chains"] = all_chains
        result["total"] = len(all_chains)

        print(f"\n[3/3] 完成。共 {len(all_chains)} 条审批链")

    except Exception as e:
        import traceback
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        print(f"\nERROR: {e}")
    finally:
        base.close_browser()

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"保存到 {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
