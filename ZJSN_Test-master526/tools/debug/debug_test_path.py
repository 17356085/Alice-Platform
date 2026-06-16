"""模拟测试代码的完整路径，记录每步状态"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.browser_driver import BaseDriver, ensure_logged_in

base = BaseDriver()
driver = base.open_browser()
try:
    print("[1] 登录...")
    ensure_logged_in(driver)
    print(f"    登录后 URL: {driver.current_url}")
    time.sleep(2)

    print("[2] driver.get 导航到气体分析...")
    driver.get("http://8.136.215.171:8081/#/lab/gas/report")
    print(f"    get 后 URL: {driver.current_url}")

    # 模仿测试的等待步骤
    for i in range(1, 16):
        time.sleep(1)
        th_count = driver.execute_script("return document.querySelectorAll('thead th').length;")
        body_count = driver.execute_script("return document.querySelectorAll('tbody').length;")
        print(f"    t+{i}s: thead th={th_count}, tbody={body_count}, URL={driver.current_url.split('#')[1] if '#' in driver.current_url else 'N/A'}")
        if th_count > 0:
            ths = driver.execute_script("""
                var ths = document.querySelectorAll('thead th');
                var texts = [];
                for (var i=0; i<Math.min(ths.length,5); i++) texts.push(ths[i].textContent.trim());
                return texts;
            """)
            print(f"    表头前5列: {ths}")
            break

    driver.save_screenshot("debug_output/test_path_final.png")
    print("[3] 截图已保存")

finally:
    base.close_browser()
