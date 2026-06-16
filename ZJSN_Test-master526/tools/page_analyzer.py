"""快速页面分析工具 — 打开指定页面并导出 DOM 结构信息"""
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base.browser_driver import BaseDriver, ensure_logged_in
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def analyze_page(route: str):
    """打开页面并导出结构信息"""
    driver_obj = BaseDriver()
    driver_obj.setup_driver(headless=False)
    driver = driver_obj.driver

    try:
        # 登录
        ensure_logged_in(driver)

        # JS hash 导航到目标页面
        print(f"\n{'='*60}")
        print(f"导航到: {route}")
        print(f"{'='*60}")
        driver.execute_script(f"window.location.hash = '{route}';")
        time.sleep(3)

        # 等待页面渲染
        wait = WebDriverWait(driver, 15)
        try:
            wait.until(lambda d: d.execute_script("return document.readyState;") == "complete")
        except:
            pass
        time.sleep(2)

        # 关闭可能的遮罩层
        driver.execute_script("""
            document.querySelectorAll('.el-loading-mask').forEach(e => e.remove());
        """)

        # ── 1. 页面基本信息 ──
        print("\n### 页面标题:", driver.title)
        print("### 当前URL:", driver.current_url)

        # ── 2. 搜索/筛选区（增强版：多种方式查找） ──
        print("\n### 搜索/筛选区 (el-form-item)")
        search_items = driver.execute_script("""
            const results = [];
            document.querySelectorAll('.el-form-item').forEach(item => {
                const label = item.querySelector('.el-form-item__label');
                const input = item.querySelector('input');
                const select = item.querySelector('select');
                const textarea = item.querySelector('textarea');
                const selectTrigger = item.querySelector('.el-select');
                const datePicker = item.querySelector('.el-date-editor');
                const cascader = item.querySelector('.el-cascader');

                const labelText = label ? label.textContent.trim() : '';
                let controlType = 'unknown';
                let placeholder = '';
                let value = '';

                if (input) {
                    controlType = input.type || 'text';
                    placeholder = input.placeholder || '';
                    value = input.value || '';
                } else if (select) {
                    controlType = 'select';
                } else if (textarea) {
                    controlType = 'textarea';
                } else if (selectTrigger) {
                    controlType = 'el-select';
                    const ph = selectTrigger.querySelector('input');
                    placeholder = ph ? ph.placeholder || '' : '';
                } else if (datePicker) {
                    controlType = 'el-date-picker';
                    const ph = datePicker.querySelector('input');
                    placeholder = ph ? ph.placeholder || '' : '';
                } else if (cascader) {
                    controlType = 'el-cascader';
                    const ph = cascader.querySelector('input');
                    placeholder = ph ? ph.placeholder || '' : '';
                }

                if (labelText || controlType !== 'unknown') {
                    results.push({label: labelText, type: controlType, placeholder: placeholder, value: value});
                }
            });
            return results;
        """)
        for item in search_items:
            print(f"  [{item['type']}] {item['label']} | placeholder='{item['placeholder']}' | value='{item['value']}'")

        # Fallback: 查找所有 input 和 select 元素
        print("\n### 搜索/筛选区 (所有 input/select 直接查找)")
        all_inputs = driver.execute_script("""
            const results = [];
            const mainArea = document.querySelector('.el-main, main, .app-main, [class*=\"main\"]')
                          || document.querySelector('#app');
            if (!mainArea) return results;
            const inputs = mainArea.querySelectorAll('input:not([type=\"hidden\"]):not([disabled])');
            inputs.forEach(inp => {
                if (inp.offsetParent !== null) {
                    results.push({
                        type: inp.type || 'text',
                        placeholder: inp.placeholder || '',
                        value: inp.value || '',
                        name: inp.name || '',
                        className: inp.className || ''
                    });
                }
            });
            return results;
        """)
        for inp in all_inputs:
            print(f"  <input type={inp['type']}> placeholder='{inp['placeholder']}' value='{inp['value']}' name='{inp['name']}' class='{inp['className'][:60]}'")

        # ── 3. 按钮区 ──
        print("\n### 按钮区（含位置信息）")
        buttons = driver.execute_script("""
            const results = [];
            document.querySelectorAll('button.el-button:not(.el-pagination button)').forEach(btn => {
                const text = btn.textContent.trim();
                const cls = btn.className;
                // 获取父级上下文
                let parent = btn.closest('.el-dialog, .el-drawer, .el-table, .search-area, .toolbar, [class*="search"], [class*="toolbar"], [class*="header"]');
                const inDialog = btn.closest('.el-dialog:not([style*="display: none"]), .el-drawer');
                const inTable = btn.closest('.el-table__body-wrapper, .el-table__fixed-right');
                let location = 'page';
                if (inDialog) location = 'dialog';
                else if (inTable) location = 'table-row';

                results.push({
                    text: text,
                    class: cls,
                    visible: btn.offsetParent !== null,
                    location: location,
                    parentClass: parent ? parent.className.substring(0, 50) : 'N/A'
                });
            });
            return results;
        """)
        for btn in buttons:
            vis = '✅' if btn['visible'] else '❌'
            print(f"  {vis} [{btn['location']:10s}] [{btn['class'][:60]:60s}] '{btn['text']}' parent={btn['parentClass']}".encode('utf-8', errors='replace').decode('utf-8', errors='replace'))

        # ── 4. 表格区 ──
        print("\n### 表格列标题")
        columns = driver.execute_script("""
            const results = [];
            document.querySelectorAll('.el-table__header-wrapper th').forEach(th => {
                const text = th.textContent.trim();
                const cls = th.className;
                const width = th.style.width || th.getAttribute('width') || 'auto';
                if (text) {
                    results.push({header: text, class: cls, width: width});
                }
            });
            return results;
        """)
        if columns:
            for col in columns:
                print(f"  📊 {col['header']} (width={col['width']})")
        else:
            print("  ⚠️ 未找到表格列标题")

        # ── 5. 表格行数 ──
        row_count = driver.execute_script("""
            return document.querySelectorAll('.el-table__body-wrapper tbody tr.el-table__row').length;
        """)
        print(f"\n### 表格数据行数: {row_count}")

        # 操作列按钮
        print("\n### 行内操作按钮")
        action_btns = driver.execute_script("""
            const results = [];
            document.querySelectorAll('.el-table__body-wrapper tbody tr.el-table__row:first-child .el-button').forEach(btn => {
                results.push({text: btn.textContent.trim(), class: btn.className, visible: btn.offsetParent !== null});
            });
            return results;
        """)
        if action_btns:
            for ab in action_btns:
                print(f"  🔘 {ab}")
        else:
            print("  (无数据行或无操作按钮)")

        # ── 6. 分页区 ──
        print("\n### 分页区")
        pagination = driver.execute_script("""
            const p = document.querySelector('.el-pagination');
            if (!p) return null;
            return {
                total: (document.querySelector('.el-pagination__total') || {}).textContent || '',
                sizes: Array.from(document.querySelectorAll('.el-pagination__sizes .el-select-dropdown__item')).map(e => e.textContent.trim()),
                currentSize: (document.querySelector('.el-pagination__sizes input') || {}).value || ''
            };
        """)
        if pagination:
            print(f"  {pagination}")
        else:
            print("  ⚠️ 未找到分页器")

        # ── 7. 统计卡片区 ──
        print("\n### 统计卡片/汇总区")
        stats = driver.execute_script("""
            const results = [];
            document.querySelectorAll('.el-statistic, .stat-card, .summary-card, [class*="statistic"], [class*="summary"]').forEach(card => {
                const title = card.querySelector('.el-statistic__head, .title, .label, h4, h5');
                const value = card.querySelector('.el-statistic__content, .value, .number, .count');
                results.push({
                    label: title ? title.textContent.trim() : '',
                    value: value ? value.textContent.trim() : card.textContent.trim().substring(0, 50)
                });
            });
            return results;
        """)
        if stats:
            for s in stats:
                print(f"  📈 {s['label']}: {s['value']}")
        else:
            print("  (无统计卡片)")

        # ── 8. Tab 页签 ──
        print("\n### Tab 页签")
        tabs = driver.execute_script("""
            const results = [];
            document.querySelectorAll('.el-tabs__item').forEach(tab => {
                results.push(tab.textContent.trim());
            });
            return results;
        """)
        if tabs:
            for t in tabs:
                print(f"  📑 {t}")

        # ── 9. 弹窗分析：点击"新增入库" ──
        print("\n### 点击'新增入库' → 弹窗分析")
        try:
            # 找到并点击新增入库按钮
            add_btn = driver.execute_script("""
                const btns = document.querySelectorAll('button.el-button');
                for (const btn of btns) {
                    if (btn.textContent.includes('新增入库') && btn.offsetParent !== null) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            """)
            if add_btn:
                time.sleep(2)
                # 分析弹窗
                dialog_info = driver.execute_script("""
                    const dialog = document.querySelector('.el-dialog:not([style*="display: none"]), .el-drawer:not([style*="display: none"])');
                    if (!dialog) return {error: '未找到弹窗'};

                    const title = dialog.querySelector('.el-dialog__title, .el-drawer__title');
                    const formItems = dialog.querySelectorAll('.el-form-item');
                    const fields = [];
                    formItems.forEach(item => {
                        const label = item.querySelector('.el-form-item__label, label');
                        const input = item.querySelector('input:not([type="hidden"])');
                        const select = item.querySelector('select');
                        const textarea = item.querySelector('textarea');
                        const selectTrigger = item.querySelector('.el-select');
                        const datePicker = item.querySelector('.el-date-editor');
                        const cascader = item.querySelector('.el-cascader');
                        const required = item.classList.contains('is-required') || item.querySelector('.el-form-item__label .required, .is-required');

                        let controlType = 'unknown';
                        let placeholder = '';
                        if (textarea) {
                            controlType = 'textarea';
                            placeholder = textarea.placeholder || '';
                        } else if (input) {
                            controlType = input.type || 'text';
                            placeholder = input.placeholder || '';
                        } else if (select) {
                            controlType = 'select';
                        } else if (selectTrigger) {
                            controlType = 'el-select';
                            const ph = selectTrigger.querySelector('input');
                            placeholder = ph ? ph.placeholder || '' : '';
                        } else if (datePicker) {
                            controlType = 'el-date-picker';
                            const ph = datePicker.querySelector('input');
                            placeholder = ph ? ph.placeholder || '' : '';
                        } else if (cascader) {
                            controlType = 'el-cascader';
                            const ph = cascader.querySelector('input');
                            placeholder = ph ? ph.placeholder || '' : '';
                        }

                        const labelText = label ? label.textContent.trim() : '';
                        if (labelText || controlType !== 'unknown') {
                            fields.push({
                                label: labelText,
                                type: controlType,
                                placeholder: placeholder,
                                required: !!required
                            });
                        }
                    });

                    // 弹窗按钮
                    const buttons = [];
                    dialog.querySelectorAll('button.el-button').forEach(btn => {
                        buttons.push(btn.textContent.trim());
                    });

                    return {
                        title: title ? title.textContent.trim() : 'N/A',
                        width: dialog.style.width || dialog.offsetWidth + 'px',
                        fields: fields,
                        buttons: buttons
                    };
                """)
                print(f"  弹窗标题: {dialog_info.get('title', 'N/A')}")
                print(f"  弹窗宽度: {dialog_info.get('width', 'N/A')}")
                print(f"  表单字段:")
                for f in dialog_info.get('fields', []):
                    req = ' *必填' if f.get('required') else ''
                    print(f"    [{f['type']}] {f['label']} | placeholder='{f['placeholder']}'{req}")
                print(f"  弹窗按钮: {dialog_info.get('buttons', [])}")

                # 关闭弹窗
                driver.execute_script("""
                    const dialog = document.querySelector('.el-dialog:not([style*="display: none"])');
                    if (dialog) {
                        const cancelBtn = dialog.querySelector('.el-button:not(.el-button--primary)');
                        if (cancelBtn) cancelBtn.click();
                    }
                """)
                time.sleep(1)
            else:
                print("  ⚠️ 未找到'新增入库'按钮")
        except Exception as e:
            print(f"  ❌ 弹窗分析失败: {e}")

        # ── 10. 页面整体HTML结构 ──
        print("\n### 页面主内容区 HTML 摘要 (前 3000 字符)")
        html_snippet = driver.execute_script("""
            const main = document.querySelector('.el-main, main, .main-content, .app-main, [class*="main"]')
                      || document.querySelector('#app');
            if (!main) return 'NOT FOUND';
            // 移除脚本和样式
            let html = main.innerHTML;
            html = html.replace(/<script[\\s\\S]*?<\\/script>/gi, '');
            html = html.replace(/<style[\\s\\S]*?<\\/style>/gi, '');
            html = html.replace(/<svg[\\s\\S]*?<\\/svg>/gi, '[SVG]');
            return html.substring(0, 3000);
        """)
        print(html_snippet[:3000])

        print(f"\n{'='*60}")
        print("分析完成！")
        print(f"{'='*60}")

    finally:
        time.sleep(2)
        driver_obj.close_browser()


if __name__ == '__main__':
    # 默认分析环保入库页面
    route = sys.argv[1] if len(sys.argv) > 1 else '/warehouse/hazard/in-order'
    analyze_page(route)
