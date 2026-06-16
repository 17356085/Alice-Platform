"""诊断新增报告单弹窗的 label 文本"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.browser_driver import BaseDriver, ensure_logged_in
from page.lab_page.GasAnalysisReportPage import GasAnalysisReportPage

base = BaseDriver(); d = base.open_browser()
try:
    ensure_logged_in(d)
    time.sleep(2)
    GasAnalysisReportPage(d).navigate_to_gas_analysis_report()

    page = GasAnalysisReportPage(d)
    print("[1] 点击新增报告单...")
    page.click_add()
    time.sleep(2)

    # 提取弹窗中所有 label 文本
    labels = d.execute_script("""
        var dialog = document.querySelector('.el-dialog:not([style*="display: none"])');
        if (!dialog) return 'NO DIALOG FOUND';
        var labels = dialog.querySelectorAll('label');
        var result = [];
        for (var i=0; i<labels.length; i++) {
            var text = labels[i].textContent.trim();
            var cls = labels[i].className;
            result.push('[' + i + '] class="' + cls + '" text="' + text + '"');
        }
        return result.join('\\n');
    """)
    print("[2] 弹窗 labels:")
    print(labels)

    # 保存弹窗HTML
    html = d.execute_script("""
        var dialog = document.querySelector('.el-dialog:not([style*="display: none"])');
        return dialog ? dialog.innerHTML.substring(0, 5000) : 'NO DIALOG';
    """)
    with open("debug_output/dialog_html.txt", "w", encoding="utf-8") as f:
        f.write(html)
    print("[3] 弹窗 HTML 已保存")

finally:
    base.close_browser()
