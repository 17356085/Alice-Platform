"""审批链步骤配置诊断 — 每链独立浏览器会话，彻底隔离状态

策略: 每链新建浏览器 → 登录 → 导航 → CDP点击 → 采集 → 关闭浏览器
"""
import os, sys, json, time, io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator

OUTPUT = os.path.join(os.path.dirname(__file__), "diag_steps_detail.json")
PAGE_URL = "https://aiwechatminidemo.cimc-digital.com/#/system/workflow/approval-chain"

# 14 known chains
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


def diagnose_one_chain(chain_num, name, code):
    """Open fresh browser, navigate, click step config, read data, close browser.
    Returns dict with chain info + step_details."""
    chain = {"index": chain_num, "name": name, "code": code, "step_details": None}
    page_num = ((chain_num - 1) // 10) + 1
    row_on_page = ((chain_num - 1) % 10) + 1

    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)

        # Navigate to chain page
        nav = SidebarNavigator(driver)
        nav._navigate_by_js_hash("#/system/workflow/approval-chain", f"diag-{chain_num}")
        time.sleep(4)

        # Wait for table
        rc = 0
        for _ in range(20):
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
            return chain

        # Navigate to page if needed
        if page_num > 1:
            driver.execute_script("""
                const pagers = document.querySelectorAll('.el-pager li.number');
                for (const li of pagers) {
                    if (li.textContent.trim() === arguments[0].toString()) { li.click(); return; }
                }
                // fallback
                const btn = document.querySelector('.btn-next');
                for (let i = 1; i < arguments[0]; i++) {
                    if (btn && !btn.classList.contains('disabled')) btn.click();
                }
            """, page_num)
            time.sleep(2)
            for _ in range(10):
                rc = driver.execute_script(
                    "return document.querySelectorAll('.el-table__body-wrapper tbody tr').length;"
                )
                if rc >= row_on_page:
                    break
                time.sleep(0.5)

        # Find step config button
        rect = driver.execute_script("""
            const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
            if (arguments[0] > rows.length) return null;
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
        """, row_on_page)

        if not rect:
            chain["step_details"] = {"error": "btn_not_found", "rows_on_page": rc, "row": row_on_page}
            return chain

        # CDP click
        cdp_click(driver, rect['x'], rect['y'])
        time.sleep(3)

        # Read step editor
        step_data = driver.execute_script("""
            const editor = document.querySelector('.step-editor');
            if (!editor || editor.offsetParent === null) return {found: false};

            const result = {found: true, steps: []};
            const cards = editor.querySelectorAll('.step-card');
            cards.forEach(card => {
                const step = {};
                card.querySelectorAll('.el-form-item').forEach(fi => {
                    const label = fi.querySelector('.el-form-item__label');
                    const fname = label ? label.textContent.trim() : '';
                    if (!fname) return;

                    const input = fi.querySelector('input');
                    const textarea = fi.querySelector('textarea');
                    const select = fi.querySelector('.el-select');

                    let v = '';
                    if (input) v = input.value;
                    else if (textarea) v = textarea.value;
                    else if (select) {
                        const s = select.querySelector('.el-select__selected-item, input');
                        v = s ? (s.value || s.textContent || s.placeholder || '').trim() : '';
                    }
                    step[fname] = v || '(空)';
                });
                step['_raw'] = card.textContent.trim().substring(0, 300);
                result.steps.push(step);
            });
            return result;
        """)

        if step_data.get("found"):
            chain["step_details"] = [
                {k: v for k, v in s.items() if not k.startswith("_")}
                for s in step_data["steps"]
            ]
        else:
            chain["step_details"] = {"error": "editor_not_found"}

        return chain

    except Exception as e:
        chain["step_details"] = {"error": str(e)[:200]}
        return chain
    finally:
        base.close_browser()


def main():
    result = {"diagnosed_at": time.strftime("%Y-%m-%d %H:%M:%S"), "chains": []}
    print("=" * 60)
    print("审批链步骤配置 — 逐链独立浏览器诊断")
    print("=" * 60)

    for idx, (name, code) in enumerate(CHAINS):
        cn = idx + 1
        print(f"[{cn:2d}/{len(CHAINS)}] {name}...", end=" ", flush=True)

        chain = diagnose_one_chain(cn, name, code)
        details = chain.get("step_details")

        if isinstance(details, list):
            summary = []
            for s in details:
                summary.append(f"{s.get('步骤名称','?')}|模式={s.get('审批模式','?')}|审批人={s.get('审批人','?')}")
            print(f"{len(details)}步: {'; '.join(summary)}")
        elif isinstance(details, dict) and details.get("error"):
            print(f"FAIL: {details['error']}")
        else:
            print(f"UNKNOWN: {details}")

        result["chains"].append(chain)

    result["total"] = len(result["chains"])
    success = sum(1 for c in result["chains"] if isinstance(c.get("step_details"), list))
    print(f"\n完成: {success}/{len(result['chains'])} 成功")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"保存到 {OUTPUT}")


if __name__ == "__main__":
    main()
