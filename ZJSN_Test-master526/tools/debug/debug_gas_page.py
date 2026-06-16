"""调试脚本 — 检查气体分析报告单页面的表格结构"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.browser_driver import BaseDriver, ensure_logged_in

base = BaseDriver()
driver = base.open_browser()
try:
    print("[1] 登录...")
    ensure_logged_in(driver)
    time.sleep(2)

    print("[2] JS hash 跳转到气体分析报告单页面...")
    driver.execute_script("window.location.hash = '#/lab/gas/report';")
    time.sleep(5)  # 等待 Vue 渲染

    driver.save_screenshot("debug_output/gas_page.png")
    print("[3] 截图已保存")

    info = driver.execute_script("""
        var result = {};

        // 页面标题
        var title = document.querySelector('.page-title, .el-breadcrumb, h1, h2, h3, [class*=title]');
        if (title) result.pageTitle = title.textContent.trim().substring(0, 60);

        // 查找所有表格相关元素
        var tables = document.querySelectorAll('table');
        result.tableCount = tables.length;

        var elTables = document.querySelectorAll('[class*=el-table]');
        result.elTableElements = elTables.length;

        // 查找表头
        var thSelectors = ['th', '.el-table__header th', '[class*=header] th', '.cell'];
        for (var s = 0; s < thSelectors.length; s++) {
            var els = document.querySelectorAll(thSelectors[s]);
            result['th_' + thSelectors[s].replace(/[^a-z_-]/g, '_')] = els.length;
        }

        // 实际获取表头文本 - 尝试多种选择器
        var headerSelectors = [
            '.el-table__header-wrapper th .cell',
            '.el-table__header th .cell',
            'thead th',
            'th .cell',
            'th',
        ];
        for (var h = 0; h < headerSelectors.length; h++) {
            var headers = document.querySelectorAll(headerSelectors[h]);
            if (headers.length > 0) {
                var texts = [];
                for (var i = 0; i < headers.length; i++) {
                    texts.push((headers[i].textContent || '').trim());
                }
                result['headers_via_' + h + '_' + headerSelectors[h].substring(0, 20)] = texts;
            }
        }

        // 查找所有带 class 的 div，看是否有自定义表格容器
        var allDivs = document.querySelectorAll('div[class]');
        var tableContainers = [];
        for (var d = 0; d < allDivs.length; d++) {
            var cls = String(allDivs[d].className);
            if (cls.indexOf('table') >= 0 || cls.indexOf('grid') >= 0 || cls.indexOf('data') >= 0) {
                tableContainers.push(cls.substring(0, 80));
            }
        }
        result.tableContainerClasses = tableContainers.slice(0, 10);

        // 查找标签栏元素
        var tabs = document.querySelectorAll('.el-tabs__item, [class*=tab], [class*=tag]');
        var tabTexts = [];
        for (var t = 0; t < tabs.length; t++) {
            if (tabs[t].offsetHeight > 0) {
                tabTexts.push((tabs[t].textContent || '').trim().substring(0, 20));
            }
        }
        result.tabTexts = tabTexts.slice(0, 30);

        // 查找按钮
        var buttons = document.querySelectorAll('button');
        var btnTexts = [];
        for (var b = 0; b < buttons.length; b++) {
            if (buttons[b].offsetHeight > 0) {
                btnTexts.push((buttons[b].textContent || '').trim().substring(0, 20));
            }
        }
        result.buttons = btnTexts;

        // URL
        result.url = window.location.href;

        return JSON.stringify(result, null, 2);
    """)

    print("[4] 页面信息:")
    print(info)

    with open("debug_output/gas_page_info.json", "w", encoding="utf-8") as f:
        f.write(info)
    print("\n[5] 已保存到 debug_output/gas_page_info.json")

finally:
    base.close_browser()
