"""审批链步骤配置诊断 — 每链独立导航，避免页面状态污染

策略:
  1. 翻页采集全部14条链名称+编码
  2. 逐链: 导航到列表页 → CDP点击步骤配置 → 采集步骤 → 记录
"""
import os, sys, json, time, io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator

OUTPUT = os.path.join(os.path.dirname(__file__), "diag_approval_chain_full.json")
BASE_URL = "https://aiwechatminidemo.cimc-digital.com/#/system/workflow/approval-chain"


def cdp_click(driver, x, y):
    driver.execute_cdp_cmd('Input.dispatchMouseEvent', {
        'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1
    })
    time.sleep(0.08)
    driver.execute_cdp_cmd('Input.dispatchMouseEvent', {
        'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1
    })


def click_step_config_button(driver, row_idx):
    """Find and CDP-click the step config button on a specific row"""
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
    """, row_idx)
    if not rect:
        return False
    cdp_click(driver, rect['x'], rect['y'])
    time.sleep(2.5)
    return True


def read_step_editor(driver):
    """Read step configuration from inline panel"""
    return driver.execute_script("""
        const editor = document.querySelector('.step-editor');
        if (!editor || editor.offsetParent === null) {
            // also check for any visible step-related panel
            const panels = document.querySelectorAll('[class*="step"]');
            const found = [];
            panels.forEach(p => {
                if (p.offsetParent !== null) found.push(p.className);
            });
            return {found: false, visible_panels: found};
        }

        const result = {found: true, steps: []};
        const cards = editor.querySelectorAll('.step-card');
        cards.forEach((card, i) => {
            const step = {};
            const formItems = card.querySelectorAll('.el-form-item');
            formItems.forEach(fi => {
                const label = fi.querySelector('.el-form-item__label');
                const input = fi.querySelector('input');
                const textarea = fi.querySelector('textarea');
                const select = fi.querySelector('.el-select');
                const fieldName = label ? label.textContent.trim() : '';
                let value = '';
                if (input) value = input.value;
                else if (textarea) value = textarea.value;
                else if (select) {
                    const sel = select.querySelector('.el-select__selected-item, input');
                    value = sel ? (sel.value || sel.textContent || '').trim() : '';
                }
                if (fieldName) step[fieldName] = value;
            });
            // Also get raw text for any unlabeled content
            step._text = card.textContent.trim().substring(0, 200);
            result.steps.push(step);
        });

        // Get approval chain title if shown
        const titleEl = editor.querySelector('[class*="title"], h3, h4');
        result.title = titleEl ? titleEl.textContent.trim() : '';
        return result;
    """)


def main():
    result = {"diagnosed_at": time.strftime("%Y-%m-%d %H:%M:%S"), "chains": []}

    print("=" * 60)
    print("审批链步骤配置 — 逐链独立诊断")
    print("=" * 60)

    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)

        # Phase 1: Quick scan to get all chain names+codes
        print("\n[Phase 1] 采集链列表...")
        nav = SidebarNavigator(driver)
        nav._navigate_by_js_hash("#/system/workflow/approval-chain", "scan")
        time.sleep(4)

        all_chains = []
        for page_num in range(1, 4):  # max 3 pages
            rows_count = driver.execute_script(
                "return document.querySelectorAll('.el-table__body-wrapper tbody tr').length;"
            )
            for ri in range(1, rows_count + 1):
                data = driver.execute_script("""
                    const cells = document.querySelectorAll('.el-table__body-wrapper tbody tr')[arguments[0]-1]
                        .querySelectorAll('td .cell');
                    return Array.from(cells).map(c => c.textContent.trim());
                """, ri)
                if len(data) >= 7:
                    all_chains.append({
                        "index": len(all_chains) + 1,
                        "name": data[1],
                        "code": data[2],
                        "department": data[3],
                        "steps_count": data[4],
                        "note": data[6] if len(data) > 6 else "",
                        "step_details": None
                    })
                    print(f"  [{len(all_chains)}] {data[1]} | {data[2]}")

            # Check pagination
            p_info = driver.execute_script("""
                const btn = document.querySelector('.btn-next');
                if (!btn || btn.classList.contains('disabled')) return {has_next: false};
                return {has_next: true};
            """)
            if not p_info.get("has_next"):
                break
            driver.execute_script("document.querySelector('.btn-next').click();")
            time.sleep(2)

        print(f"  共 {len(all_chains)} 条")

        # Phase 2: For each chain, navigate fresh and read steps
        print(f"\n[Phase 2] 逐链采集步骤配置...")
        for chain in all_chains:
            idx = chain["index"]
            row_on_page = ((idx - 1) % 10) + 1
            page_for_chain = ((idx - 1) // 10) + 1

            print(f"  [{idx}] {chain['name']}...", end=" ", flush=True)

            # Navigate fresh
            driver.get(BASE_URL)
            time.sleep(4)

            # Navigate to correct page if needed
            if page_for_chain > 1:
                for _ in range(page_for_chain - 1):
                    driver.execute_script("document.querySelector('.btn-next').click();")
                    time.sleep(2)

            # Wait for table
            for _ in range(15):
                rc = driver.execute_script(
                    "return document.querySelectorAll('.el-table__body-wrapper tbody tr').length;"
                )
                if rc >= row_on_page:
                    break
                time.sleep(0.5)

            # Click step config
            ok = click_step_config_button(driver, row_on_page)
            if not ok:
                chain["step_details"] = {"error": "button_not_found"}
                print("BTN_MISSING")
                continue

            # Read step data
            step_data = read_step_editor(driver)
            if step_data.get("found"):
                chain["step_details"] = step_data["steps"]
                details = []
                for s in step_data["steps"]:
                    fields = {k: v for k, v in s.items() if not k.startswith("_")}
                    details.append(fields)
                chain["step_details"] = details
                print(f"{len(details)}步骤: {json.dumps(details, ensure_ascii=False)}")
            else:
                chain["step_details"] = {"error": "editor_not_found", "panels": step_data.get("visible_panels", [])}
                print(f"NO_EDITOR panels={step_data.get('visible_panels', [])}")

        result["chains"] = all_chains
        result["total"] = len(all_chains)
        print(f"\n完成! {len(all_chains)} 条")

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
