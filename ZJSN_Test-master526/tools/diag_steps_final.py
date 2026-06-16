"""审批链步骤配置诊断 — 最终版。硬编码14条链，逐链独立诊断"""
import os, sys, json, time, io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from base.browser_driver import BaseDriver, ensure_logged_in

OUTPUT = os.path.join(os.path.dirname(__file__), "diag_approval_chain_full.json")
PAGE_URL = "https://aiwechatminidemo.cimc-digital.com/#/system/workflow/approval-chain"

# 14 known chains from v2 diagnostic
CHAINS = [
    ("承包商入场审批", "contractor_entry"),
    ("危废入库审批链", "wh_hazard_in"),
    ("危废出库审批链", "wh_hazard_out"),
    ("备件盘点审批链", "wh_stocktake"),
    ("备件入库审批链", "wh_in"),
    ("备件出库审批链", "wh_out"),
    ("备件领用申请审批链", "wh_requisition"),
    ("请假申请审批链", "leave"),
    ("其他申请审批链", "other"),
    ("访客登记审批链", "visitor"),
    ("入场申请审批链", "entry"),
    ("领用申请审批链", "spare"),
    ("设备维保审批链", "equipment"),
    ("生产报表审批流", "GLOBAL"),
]


def cdp_click(driver, x, y):
    driver.execute_cdp_cmd('Input.dispatchMouseEvent', {
        'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1
    })
    time.sleep(0.08)
    driver.execute_cdp_cmd('Input.dispatchMouseEvent', {
        'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1
    })


def wait_for_table(driver, min_rows=1, timeout=15):
    """Wait until table has at least min_rows rows"""
    for _ in range(timeout * 2):
        try:
            rc = driver.execute_script(
                "const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');"
                "return rows.length;"
            )
            if rc >= min_rows:
                return rc
        except:
            pass
        time.sleep(0.5)
    return 0


def goto_page(driver, page_num):
    """Navigate to a specific page in pagination"""
    if page_num <= 1:
        return
    # Click the page number directly
    driver.execute_script("""
        const pagers = document.querySelectorAll('.el-pager li.number');
        for (const li of pagers) {
            if (li.textContent.trim() === arguments[0].toString()) {
                li.click();
                return;
            }
        }
        // fallback: click next button N-1 times
        const btn = document.querySelector('.btn-next');
        for (let i = 1; i < arguments[0]; i++) {
            if (btn && !btn.classList.contains('disabled')) btn.click();
        }
    """, page_num)
    time.sleep(2)


def read_step_editor(driver):
    """Read step config from inline panel"""
    return driver.execute_script("""
        // Find step editor panel
        const editor = document.querySelector('.step-editor');
        if (!editor || editor.offsetParent === null) {
            // Check for any visible step-related panels
            const allPanels = document.querySelectorAll('[class*="step"]');
            const visible = [];
            allPanels.forEach(p => {
                if (p.offsetParent !== null) visible.push(p.className.substring(0, 60));
            });
            return {found: false, visible_panels: visible};
        }

        const result = {found: true, steps: []};
        const cards = editor.querySelectorAll('.step-card');
        cards.forEach(card => {
            const step = {};
            const formItems = card.querySelectorAll('.el-form-item');
            formItems.forEach(fi => {
                const label = fi.querySelector('.el-form-item__label');
                const fieldName = label ? label.textContent.trim() : '';
                if (!fieldName) return;

                const input = fi.querySelector('input');
                const textarea = fi.querySelector('textarea');
                const select = fi.querySelector('.el-select');

                let value = '';
                if (input) value = input.value;
                else if (textarea) value = textarea.value;
                else if (select) {
                    const sel = select.querySelector('.el-select__selected-item, input');
                    value = sel ? (sel.value || sel.textContent || sel.placeholder || '').trim() : '';
                }
                step[fieldName] = value || '(空)';
            });
            // add raw text for fallback
            step['_raw'] = card.textContent.trim().substring(0, 200);
            result.steps.push(step);
        });
        return result;
    """)


def main():
    result = {"diagnosed_at": time.strftime("%Y-%m-%d %H:%M:%S"), "chains": []}
    print("=" * 60)
    print("审批链步骤配置 — 逐链独立诊断 (final)")
    print("=" * 60)

    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)

        for idx, (name, code) in enumerate(CHAINS):
            chain_num = idx + 1
            page_num = ((chain_num - 1) // 10) + 1
            row_on_page = ((chain_num - 1) % 10) + 1

            print(f"[{chain_num:2d}] {name} (page={page_num}, row={row_on_page})...", end=" ", flush=True)

            chain = {"index": chain_num, "name": name, "code": code, "step_details": None}

            # Fresh navigation
            driver.get(PAGE_URL)
            time.sleep(3)

            # Wait for table
            rc = wait_for_table(driver, min_rows=1, timeout=15)
            if rc == 0:
                chain["step_details"] = {"error": "table_empty"}
                print("TABLE_EMPTY")
                result["chains"].append(chain)
                continue

            # Go to correct page
            if page_num > 1:
                goto_page(driver, page_num)
                wait_for_table(driver, min_rows=1, timeout=10)

            # Find and click step config button
            rect = driver.execute_script("""
                const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
                if (arguments[0] > rows.length) return null;
                const cells = rows[arguments[0] - 1].querySelectorAll('td .cell');
                const lastCell = cells[cells.length - 1];
                const btns = lastCell.querySelectorAll('button');
                for (const b of btns) {
                    if (b.textContent.includes('步骤配置')) {
                        const r = b.getBoundingClientRect();
                        return {x: r.left + r.width/2, y: r.top + r.height/2};
                    }
                }
                return null;
            """, row_on_page)

            if not rect:
                chain["step_details"] = {"error": "btn_not_found", "rows_on_page": rc}
                print("BTN_MISSING")
                result["chains"].append(chain)
                continue

            # CDP click
            cdp_click(driver, rect['x'], rect['y'])
            time.sleep(3)

            # Read step data
            step_data = read_step_editor(driver)
            if step_data.get("found"):
                chain["step_details"] = step_data["steps"]
                summary = []
                for s in step_data["steps"]:
                    fields = {k: v for k, v in s.items() if not k.startswith("_")}
                    summary.append(fields)
                chain["step_details"] = summary
                print(f"{len(summary)}步: {json.dumps(summary, ensure_ascii=False)}")
            else:
                chain["step_details"] = {"error": "editor_not_found", "panels": step_data.get("visible_panels", [])}
                print(f"NO_EDITOR panels={step_data.get('visible_panels', [])}")

            result["chains"].append(chain)

        print(f"\n完成! {len(result['chains'])} 条")

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
