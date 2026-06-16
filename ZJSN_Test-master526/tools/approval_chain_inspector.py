"""审批链步骤配置批量查看 v3 — 每次独立访问"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.browser_driver import BaseDriver, ensure_logged_in

def inspect_chain(chain_name):
    """独立检查一个审批链的步骤配置"""
    d = BaseDriver()
    d.setup_driver(headless=False)
    driver = d.driver
    try:
        ensure_logged_in(driver)
        driver.execute_script("window.location.hash = '#/system/workflow/approval-chain';")
        time.sleep(6)

        # 点击步骤配置
        ok = driver.execute_script(f"""
            const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr.el-table__row');
            for (const row of rows) {{
                if (row.textContent.includes('{chain_name}')) {{
                    const btns = row.querySelectorAll('.el-button');
                    for (const btn of btns) {{
                        if (btn.textContent.includes('步骤配置')) {{
                            btn.click();
                            return true;
                        }}
                    }}
                }}
            }}
            return false;
        """)
        if not ok:
            print(f"  ?? 未找到'{chain_name}'")
            return None

        time.sleep(3)

        # 获取当前页面文本
        text = driver.execute_script("""
            const main = document.querySelector('.el-main, main, .app-main, [class*="main-content"]');
            if (!main) return document.body.textContent.substring(0, 800);
            return main.textContent.replace(/\\s+/g, ' ').trim().substring(0, 800);
        """)
        return text
    finally:
        d.close_browser()

# 逐个检查
chains = [
    "备件入库审批链",
    "备件出库审批链",
    "备件盘点审批链",
    "备件领用申请审批链",
]

for name in chains:
    print(f"\n{'='*60}")
    print(f"?? {name}")
    print(f"{'='*60}")
    result = inspect_chain(name)
    if result:
        # 提取关键信息
        for keyword in ['步骤名称', '审批人', '审批模式', '会签', '或签', '主管', '仓管', '库管']:
            pass
        print(result[:600])
    time.sleep(2)
