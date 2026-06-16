"""调试脚本 — 检查侧边栏实际 HTML 结构

运行：python tools/debug/debug_sidebar.py
用途：登录后截图 + 导出侧边栏 HTML，用于修复导航定位器
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base.browser_driver import BaseDriver, ensure_logged_in


def main():
    base = BaseDriver()
    driver = base.open_browser()
    try:
        print("[1] 登录中...")
        ensure_logged_in(driver)
        time.sleep(2)

        print("[2] 保存页面截图...")
        driver.save_screenshot("debug_output/sidebar_full_page.png")

        print("[3] 导出侧边栏 HTML 结构...")
        # 用 JS 提取侧边栏的所有 class 和文本
        sidebar_info = driver.execute_script("""
            var results = [];

            // 尝试多种常见的侧边栏选择器
            var selectors = [
                '.el-menu', '.sidebar-container', '.el-aside .el-menu',
                '[class*="sidebar"]', '[class*="side-menu"]', '[class*="menu"]',
                'nav', '.el-container > div:first-child ul'
            ];

            for (var s = 0; s < selectors.length; s++) {
                var containers = document.querySelectorAll(selectors[s]);
                for (var c = 0; c < containers.length; c++) {
                    var el = containers[c];
                    if (el.offsetHeight === 0) continue;

                    results.push('=== Container: ' + selectors[s] + ' ===');
                    results.push('Tag: ' + el.tagName);
                    results.push('Class: ' + (el.className || '(none)'));
                    results.push('');

                    // 获取所有可点击的子元素（3层深）
                    var items = el.querySelectorAll('li, div, span, button');
                    for (var i = 0; i < items.length; i++) {
                        var item = items[i];
                        if (item.offsetHeight === 0) continue;
                        var text = (item.textContent || '').trim().replace(/\\s+/g, ' ');
                        if (text.length > 80 || !text) continue;

                        var tag = item.tagName;
                        var cls = (item.className || '').toString().substring(0, 60);
                        var role = item.getAttribute('role') || '';
                        results.push(
                            '<' + tag + '> ' +
                            'class="' + cls + '" ' +
                            (role ? 'role="' + role + '" ' : '') +
                            'text="' + text + '"'
                        );
                    }
                }
            }
            return results.join('\\n');
        """)

        output_path = "debug_output/sidebar_structure.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(sidebar_info)

        print(f"[4] 侧边栏结构已保存到: {output_path}")
        print(f"[5] 截图已保存到: debug_output/sidebar_full_page.png")
        print("\n=== 侧边栏结构预览 ===")
        # 只打印包含"化验"或"气体"或"menu"的行
        for line in sidebar_info.split("\n"):
            lower = line.lower()
            if any(k in lower for k in ["化验", "气体", "menu", "submenu", "container", "==="]):
                print(line)

    finally:
        base.close_browser()


if __name__ == "__main__":
    main()
