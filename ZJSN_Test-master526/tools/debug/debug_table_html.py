"""调试 — 保存主内容区完整 HTML"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.browser_driver import BaseDriver, ensure_logged_in

base = BaseDriver()
driver = base.open_browser()
try:
    print("[1] 登录 + 导航...")
    ensure_logged_in(driver)
    time.sleep(2)
    driver.execute_script("window.location.hash = '#/lab/gas/report';")
    time.sleep(5)

    # 保存完整 HTML
    html = driver.execute_script("""
        // 找到主内容区
        var main = document.querySelector('.main-container, .app-main, [class*=main]');
        if (!main) main = document.body;
        return main.innerHTML;
    """)

    with open("debug_output/main_content.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[2] HTML 已保存 ({len(html)} 字符)")

    # 重点找表格相关标签
    info = driver.execute_script("""
        var result = {};
        var main = document.querySelector('.main-container, .app-main') || document.body;

        // 查找所有包含 'row' 'cell' 'col' 'grid' 的元素
        var all = main.querySelectorAll('*');
        var tagCounts = {};
        for (var i = 0; i < all.length; i++) {
            var tag = all[i].tagName.toLowerCase();
            tagCounts[tag] = (tagCounts[tag] || 0) + 1;
        }
        result.tagCounts = tagCounts;

        // 查找 table/tr/td/th/thead/tbody
        result.tableTags = {
            table: main.querySelectorAll('table').length,
            tr: main.querySelectorAll('tr').length,
            td: main.querySelectorAll('td').length,
            th: main.querySelectorAll('th').length,
            thead: main.querySelectorAll('thead').length,
            tbody: main.querySelectorAll('tbody').length,
        };

        return JSON.stringify(result, null, 2);
    """)
    print("[3] 标签统计:")
    print(info)

finally:
    base.close_browser()
