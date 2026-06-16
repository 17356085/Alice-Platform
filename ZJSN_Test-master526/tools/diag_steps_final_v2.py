"""审批链步骤配置诊断 — 最终版: about:blank 强制刷新 + CDP click"""
import os, sys, json, time, io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from base.browser_driver import BaseDriver, ensure_logged_in

OUTPUT = os.path.join(os.path.dirname(__file__), "diag_steps_detail.json")
PAGE = 'https://aiwechatminidemo.cimc-digital.com/#/system/workflow/approval-chain'

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
    time.sleep(0.12)
    driver.execute_cdp_cmd('Input.dispatchMouseEvent', {
        'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1
    })


def main():
    result = {"diagnosed_at": time.strftime("%Y-%m-%d %H:%M:%S"), "chains": []}
    print("=" * 60)
    print("审批链步骤配置 — about:blank 强制刷新 + CDP")
    print("=" * 60)

    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)

        for idx, (name, code) in enumerate(CHAINS):
            cn = idx + 1
            pg = ((cn - 1) // 10) + 1
            row = ((cn - 1) % 10) + 1

            print(f"[{cn:2d}] {name} (pg={pg},row={row})...", end=" ", flush=True)
            chain = {"index": cn, "name": name, "code": code, "step_details": None}

            # about:blank → chain page (force fresh SPA load)
            driver.get('about:blank')
            time.sleep(0.5)
            driver.get(PAGE)
            time.sleep(4)

            # Wait for table
            rc = 0
            for _ in range(30):
                try:
                    rc = driver.execute_script(
                        "return document.querySelectorAll('.el-table__body-wrapper tbody tr').length;"
                    )
                    if rc > 0:
                        break
                except:
                    pass
                time.sleep(0.5)
            if rc == 0:
                chain["step_details"] = {"error": "table_empty"}
                print("TABLE_EMPTY")
                result["chains"].append(chain)
                continue

            # Navigate to correct page if needed
            if pg > 1:
                driver.execute_script("""
                    const pagers = document.querySelectorAll('.el-pager li.number');
                    for (const li of pagers) {
                        if (li.textContent.trim() === arguments[0].toString()) { li.click(); return; }
                    }
                    const btn = document.querySelector('.btn-next');
                    for (let i = 1; i < arguments[0]; i++) {
                        if (btn && !btn.classList.contains('disabled')) btn.click();
                    }
                """, pg)
                time.sleep(2)
                for _ in range(10):
                    rc = driver.execute_script(
                        "return document.querySelectorAll('.el-table__body-wrapper tbody tr').length;"
                    )
                    if rc >= row:
                        break
                    time.sleep(0.5)

            # Find step config button, scroll into view
            rect = driver.execute_script("""
                const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
                if (arguments[0] > rows.length) return null;
                rows[arguments[0]-1].scrollIntoView({block: 'center'});
                const cells = rows[arguments[0]-1].querySelectorAll('td .cell');
                const lastCell = cells[cells.length-1];
                const btns = lastCell.querySelectorAll('button');
                for (const b of btns) {
                    if (b.textContent.includes('步骤配置')) {
                        const r = b.getBoundingClientRect();
                        return {x: r.left + r.width/2, y: r.top + r.height/2};
                    }
                }
                return null;
            """, row)

            if not rect:
                chain["step_details"] = {"error": "btn_not_found", "rows": rc, "row": row}
                print(f"BTN_MISSING(rows={rc})")
                result["chains"].append(chain)
                continue

            # CDP click
            cdp_click(driver, rect['x'], rect['y'])

            # Wait for step editor (up to 10s)
            found = False
            for _ in range(20):
                time.sleep(0.5)
                visible = driver.execute_script(
                    "return !!(document.querySelector('.step-editor')?.offsetParent);"
                )
                if visible:
                    found = True
                    break

            if not found:
                # what panels are visible?
                panels = driver.execute_script("""
                    return Array.from(document.querySelectorAll('[class*="step"]'))
                        .filter(el => el.offsetParent !== null)
                        .map(el => el.className.substring(0, 60));
                """)
                chain["step_details"] = {"error": "editor_not_found", "panels": panels}
                print(f"NO_EDITOR panels={panels}")
                result["chains"].append(chain)
                continue

            # Read step data
            data = driver.execute_script("""
                const editor = document.querySelector('.step-editor');
                const result = {steps: []};
                const cards = editor.querySelectorAll('.step-card');
                cards.forEach(card => {
                    const step = {};
                    card.querySelectorAll('.el-form-item').forEach(fi => {
                        const label = fi.querySelector('.el-form-item__label');
                        const fname = label ? label.textContent.trim() : '';
                        if (!fname) return;
                        const input = fi.querySelector('input');
                        const textarea = fi.querySelector('textarea');
                        let v = '';
                        if (input) v = input.value;
                        else if (textarea) v = textarea.value;
                        step[fname] = v || '(空)';
                    });
                    result.steps.push(step);
                });
                return result;
            """)

            chain["step_details"] = [
                {k: v for k, v in s.items()}
                for s in data.get("steps", [])
            ]
            summary = " | ".join(
                f"S{i+1}:{s.get('步骤名称','?')}({s.get('审批模式','?')})"
                for i, s in enumerate(chain["step_details"])
            )
            print(summary)

            result["chains"].append(chain)

    except Exception as e:
        import traceback
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        print(f"\nERROR: {e}")
    finally:
        base.close_browser()

    success = sum(1 for c in result["chains"] if isinstance(c.get("step_details"), list))
    fail = len(result["chains"]) - success
    print(f"\n完成: {success}/{len(result['chains'])} 成功, {fail} 失败")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"保存到 {OUTPUT}")


if __name__ == "__main__":
    main()
