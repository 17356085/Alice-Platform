"""审批链配置页面诊断脚本 — 采集实际页面数据

采集内容:
  1. 表格: 所有行的全部列数据
  2. 搜索区: 字段类型/placeholder
  3. 新增弹窗: 默认值 + el-select 可选项
  4. 编辑弹窗(第一行): 各字段回显值

输出: diag_approval_chain.json
"""
import os, sys, json, time
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

OUTPUT = os.path.join(os.path.dirname(__file__), "diag_approval_chain.json")

def js(driver, script, *args):
    """Execute JS, return parsed result or raw"""
    try:
        result = driver.execute_script(script, *args)
        return result
    except Exception as e:
        return f"JS_ERROR: {e}"

def main():
    result = {
        "diagnosed_at": datetime.now().isoformat(),
        "page": "审批链配置",
        "route": "#/system/workflow/approval-chain",
    }

    print("=" * 60)
    print("审批链配置 — 浏览器诊断")
    print("=" * 60)

    base = BaseDriver()
    driver = base.open_browser()
    try:
        # ── Login + Navigate ──
        print("\n[1/5] 登录并导航到审批链配置...")
        ensure_logged_in(driver)
        nav = SidebarNavigator(driver)
        nav._navigate_by_js_hash("#/system/workflow/approval-chain", "diag-approval-chain")
        time.sleep(4)

        # Wait for table
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".el-table__body-wrapper"))
            )
        except:
            print("WARNING: 表格未在10s内加载")

        # ── 1. Table Data ──
        print("[2/5] 采集表格数据...")
        headers = js(driver, """
            return Array.from(document.querySelectorAll('.el-table__header-wrapper th .cell'))
                .map(el => el.textContent.trim()).filter(Boolean);
        """)
        result["table_headers"] = headers
        print(f"  表头: {headers}")

        rows_data = js(driver, """
            const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
            const data = [];
            rows.forEach((row, idx) => {
                const cells = row.querySelectorAll('td .cell');
                const rowData = {};
                cells.forEach((cell, ci) => {
                    // Get text, also check for el-switch
                    const switchEl = cell.querySelector('.el-switch');
                    const text = cell.textContent.trim();
                    rowData['col_' + ci] = {
                        text: text,
                        has_switch: !!switchEl,
                        switch_checked: switchEl ? switchEl.classList.contains('is-checked') : null,
                        has_button: !!cell.querySelector('button'),
                        buttons: Array.from(cell.querySelectorAll('button')).map(b => b.textContent.trim())
                    };
                });
                data.push(rowData);
            });
            return data;
        """)
        result["table_rows"] = rows_data
        print(f"  行数: {len(rows_data)}")
        for i, row in enumerate(rows_data):
            texts = [v["text"] for v in row.values()]
            print(f"  Row {i+1}: {texts}")

        # ── 2. Search Area ──
        print("[3/5] 采集搜索区信息...")
        search_info = js(driver, """
            const formItems = document.querySelectorAll('.el-form-item');
            const items = [];
            formItems.forEach(fi => {
                const label = fi.querySelector('.el-form-item__label');
                const input = fi.querySelector('input');
                const select = fi.querySelector('.el-select');
                const placeholder = input ? input.placeholder : '';
                items.push({
                    label: label ? label.textContent.trim() : '',
                    type: select ? 'el-select' : (input ? 'el-input' : 'unknown'),
                    placeholder: placeholder
                });
            });
            return items;
        """)
        result["search_area"] = search_info
        for s in search_info:
            print(f"  搜索字段: label={s['label']}, type={s['type']}, placeholder={s['placeholder']}")

        # ── 3. Add Dialog ──
        print("[4/5] 采集新增弹窗...")
        # Click add button
        js(driver, """
            const btns = document.querySelectorAll('button');
            for (const b of btns) {
                if (b.textContent.includes('新增') || b.textContent.includes('添加') || b.textContent.includes('新建')) {
                    b.click();
                    break;
                }
            }
        """)
        time.sleep(3)

        dialog_title = js(driver, """
            const dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
            if (!dlg) return 'NOT_FOUND';
            const title = dlg.querySelector('.el-dialog__title');
            return title ? title.textContent.trim() : 'NO_TITLE';
        """)
        result["add_dialog_title"] = dialog_title
        print(f"  弹窗标题: {dialog_title}")

        dialog_fields = js(driver, """
            const dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
            if (!dlg) return [];
            const items = dlg.querySelectorAll('.el-form-item');
            const fields = [];
            items.forEach(fi => {
                const label = fi.querySelector('.el-form-item__label');
                const input = fi.querySelector('input');
                const textarea = fi.querySelector('textarea');
                const select = fi.querySelector('.el-select');
                const switchEl = fi.querySelector('.el-switch');
                const field = {
                    label: label ? label.textContent.trim() : '',
                    type: select ? 'el-select' : (textarea ? 'el-textarea' : (switchEl ? 'el-switch' : (input ? 'el-input' : 'unknown'))),
                    placeholder: input ? input.placeholder : (textarea ? textarea.placeholder : ''),
                    value: input ? input.value : (textarea ? textarea.value : ''),
                    switch_checked: switchEl ? switchEl.classList.contains('is-checked') : null,
                };
                // For el-select, try to get options
                if (select) {
                    // Click to open dropdown
                    const trigger = select.querySelector('.el-select__input') || select.querySelector('input');
                    if (trigger) trigger.click();
                }
                fields.push(field);
            });
            return fields;
        """)
        result["add_dialog_fields"] = dialog_fields
        for f in dialog_fields:
            print(f"  字段: {f}")

        # Get select options after opening dropdowns
        time.sleep(1)
        select_options = js(driver, """
            const allOptions = {};
            const dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
            if (!dlg) return allOptions;
            const selects = dlg.querySelectorAll('.el-select');
            selects.forEach((sel, si) => {
                // Find the popper
                const poppers = document.querySelectorAll('.el-select-dropdown:not([style*="display: none"])');
                if (poppers.length > 0) {
                    const options = poppers[poppers.length-1].querySelectorAll('.el-select-dropdown__item');
                    allOptions['select_' + si] = Array.from(options).map(o => o.textContent.trim());
                }
            });
            return allOptions;
        """)
        result["add_dialog_select_options"] = select_options
        for k, v in select_options.items():
            print(f"  Select选项 {k}: {v}")

        # Close add dialog
        js(driver, """
            const dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
            if (dlg) {
                const cancelBtn = dlg.querySelector('.el-dialog__footer button');
                if (cancelBtn) cancelBtn.click();
            }
        """)
        time.sleep(1)

        # ── 4. Edit Dialog (first row) ──
        print("[5/5] 采集编辑弹窗(第一行)...")
        if len(rows_data) > 0:
            # Click first row edit
            first_edit_clicked = js(driver, """
                const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
                if (rows.length === 0) return false;
                const lastCell = rows[0].querySelectorAll('td .cell');
                const actionCell = lastCell[lastCell.length - 1];
                const editBtn = actionCell.querySelector('button');
                if (editBtn && (editBtn.textContent.includes('编辑') || editBtn.textContent.includes('修改'))) {
                    editBtn.click();
                    return true;
                }
                // Try clicking any button
                const btns = actionCell.querySelectorAll('button');
                for (const b of btns) {
                    if (b.textContent.includes('编辑')) { b.click(); return true; }
                }
                return false;
            """)
            result["edit_dialog_opened"] = first_edit_clicked

            if first_edit_clicked:
                time.sleep(3)
                edit_title = js(driver, """
                    const dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
                    return dlg ? dlg.querySelector('.el-dialog__title').textContent.trim() : 'NOT_FOUND';
                """)
                result["edit_dialog_title"] = edit_title
                print(f"  编辑弹窗标题: {edit_title}")

                edit_fields = js(driver, """
                    const dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
                    if (!dlg) return [];
                    const items = dlg.querySelectorAll('.el-form-item');
                    const fields = [];
                    items.forEach(fi => {
                        const label = fi.querySelector('.el-form-item__label');
                        const input = fi.querySelector('input');
                        const textarea = fi.querySelector('textarea');
                        const select = fi.querySelector('.el-select');
                        const switchEl = fi.querySelector('.el-switch');
                        fields.push({
                            label: label ? label.textContent.trim() : '',
                            type: select ? 'el-select' : (textarea ? 'el-textarea' : (switchEl ? 'el-switch' : (input ? 'el-input' : 'unknown'))),
                            placeholder: input ? input.placeholder : (textarea ? textarea.placeholder : ''),
                            value: input ? input.value : (textarea ? textarea.value : ''),
                            switch_checked: switchEl ? switchEl.classList.contains('is-checked') : null,
                        });
                    });
                    return fields;
                """)
                result["edit_dialog_fields"] = edit_fields
                for f in edit_fields:
                    print(f"  字段: {f}")

                # Close edit dialog
                js(driver, """
                    const dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
                    if (dlg) {
                        const cancelBtn = Array.from(dlg.querySelectorAll('.el-dialog__footer button'))
                            .find(b => b.textContent.includes('取消'));
                        if (cancelBtn) cancelBtn.click();
                    }
                """)
            else:
                print("  SKIP: 无法点击第一行编辑按钮")
        else:
            result["edit_dialog_opened"] = False
            print("  SKIP: 无表格数据")

        # ── Save ──
        print("\n" + "=" * 60)
        print(f"诊断完成，保存到 {OUTPUT}")

    except Exception as e:
        result["error"] = str(e)
        print(f"\nERROR: {e}")
    finally:
        base.close_browser()

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("Done.")


if __name__ == "__main__":
    main()
