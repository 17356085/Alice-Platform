"""页面结构分析工具: 访问用户管理页面，提取渲染后的 DOM 结构信息"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from selenium.webdriver.support.ui import WebDriverWait

def main():
    base = BaseDriver()
    driver = None
    try:
        driver = base.open_browser()
        ensure_logged_in(driver)
        driver.get('https://aiwechatminidemo.cimc-digital.com/#/system/user')
        time.sleep(3)
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        time.sleep(2)

        # ── Phase 1: 提取页面基础结构 ──
        info = driver.execute_script(r'''
        function getAllText(el) {
            if (!el) return '';
            return (el.innerText || el.textContent || '').trim();
        }

        var info = {};

        // 1. 面包屑
        var bc = document.querySelector('.el-breadcrumb');
        info.breadcrumb = bc ? getAllText(bc) : 'NOT FOUND';

        // 2. 搜索区表单项
        var formItems = [];
        var allFormItems = document.querySelectorAll('.el-form-item');
        allFormItems.forEach(function(item) {
            if (item.closest('.el-dialog') || item.closest('.el-dialog__wrapper')) return;
            var label = item.querySelector('.el-form-item__label');
            var labelText = label ? getAllText(label).replace(/:$|：$/,'').replace(/\s+/g,'') : null;
            if (!labelText) return;
            var input = item.querySelector('input:not([type="hidden"])');
            var select = item.querySelector('.el-select');
            var selectInput = select ? select.querySelector('input') : null;
            var selectSelected = select ? select.querySelector('.el-select__selected-item:not(.el-select__placeholder)') : null;
            var selects = item.querySelectorAll('.el-select__selected-item span');
            var selectedTexts = [];
            selects.forEach(function(s) {
                var t = getAllText(s);
                if (t && t !== labelText) selectedTexts.push(t);
            });
            var radioGroup = item.querySelector('.el-radio-group');
            var tag = 'unknown';
            var currentValue = '';
            var placeholder = '';
            if (input && !(select && selectInput)) {
                tag = 'input';
                placeholder = input.placeholder || '';
                currentValue = input.value || '';
            } else if (select) {
                tag = 'select';
                if (selectedTexts.length > 0) {
                    currentValue = selectedTexts.join(', ');
                } else if (selectSelected) {
                    currentValue = getAllText(selectSelected);
                } else if (selectInput) {
                    placeholder = selectInput.placeholder || '';
                    currentValue = selectInput.value || '';
                }
            } else if (radioGroup) {
                tag = 'radio-group';
                var checked = radioGroup.querySelector('.is-checked span');
                currentValue = checked ? getAllText(checked) : '';
            }
            formItems.push({
                label: labelText,
                type: tag,
                placeholder: placeholder,
                currentValue: currentValue
            });
        });
        info.searchFormItems = formItems;

        // 3. 搜索区按钮
        var searchBtns = [];
        var mainContent = document.querySelector('.el-main, main, section');
        if (mainContent) {
            var allBtns = mainContent.querySelectorAll('button.el-button');
            allBtns.forEach(function(b) {
                var text = getAllText(b);
                var inTable = b.closest('.el-table__row');
                var inDialog = b.closest('.el-dialog');
                var inPagination = b.closest('.el-pagination');
                if (text && !inTable && !inDialog && !inPagination) {
                    searchBtns.push({
                        text: text,
                        class: b.className.substring(0, 80),
                        disabled: b.classList.contains('is-disabled')
                    });
                }
            });
        }
        info.pageButtons = searchBtns;

        // 4. 表格头部
        var tableHeaders = [];
        var ths = document.querySelectorAll('.el-table__header-wrapper th');
        ths.forEach(function(th, i) {
            var cell = th.querySelector('.cell');
            var text = getAllText(cell || th);
            if (text) {
                tableHeaders.push({
                    index: i,
                    text: text,
                    hasCheckbox: !!th.querySelector('.el-checkbox')
                });
            }
        });
        info.tableHeaders = tableHeaders;

        // 5. 表格行（前3行+各列详情）
        var sampleRows = [];
        var rows = document.querySelectorAll('tr.el-table__row');
        for (var r = 0; r < Math.min(rows.length, 3); r++) {
            var cells = rows[r].querySelectorAll('td');
            var rowData = [];
            cells.forEach(function(td, c) {
                var cellDiv = td.querySelector('.cell');
                var cellText = getAllText(cellDiv || td);
                var checkbox = td.querySelector('.el-checkbox');
                var buttons = td.querySelectorAll('button');
                var btnTexts = [];
                buttons.forEach(function(b) { var t = getAllText(b); if (t) btnTexts.push(t); });
                var dropdown = td.querySelector('.el-dropdown');
                var switchEl = td.querySelector('.el-switch');
                var tags = td.querySelectorAll('.el-tag');
                var tagTexts = [];
                tags.forEach(function(t) { tagTexts.push(getAllText(t)); });

                rowData.push({
                    colIndex: c,
                    hasCheckbox: !!checkbox,
                    hasButtons: btnTexts.length > 0,
                    buttonTexts: btnTexts,
                    hasDropdown: !!dropdown,
                    hasSwitch: !!switchEl,
                    hasTags: tagTexts.length > 0,
                    tagTexts: tagTexts,
                    textPreview: cellText.substring(0, 150)
                });
            });
            sampleRows.push(rowData);
        }
        info.sampleRows = sampleRows;
        info.totalVisibleRows = rows.length;

        // 6. 分页
        var pag = document.querySelector('.el-pagination');
        if (pag) {
            info.pagination = {
                total: getAllText(pag.querySelector('.el-pagination__total')),
                sizes: getAllText(pag.querySelector('.el-pagination__sizes')),
            };
            var nextBtn = pag.querySelector('.btn-next');
            var prevBtn = pag.querySelector('.btn-prev');
            info.pagination.prevDisabled = prevBtn ? prevBtn.classList.contains('disabled') : null;
            info.pagination.nextDisabled = nextBtn ? nextBtn.classList.contains('disabled') : null;
            var pageNums = [];
            pag.querySelectorAll('.el-pager li').forEach(function(p) { pageNums.push(getAllText(p)); });
            info.pagination.pageNumbers = pageNums;
        }

        // 7. 侧边栏激活状态
        var activeMenu = document.querySelector('.el-menu .is-active');
        info.sidebarActive = activeMenu ? getAllText(activeMenu) : '';

        return info;
        ''')

        print("=" * 60)
        print("页面URL:", driver.current_url)
        print("面包屑:", info.get('breadcrumb', ''))
        print("侧边栏激活:", info.get('sidebarActive', ''))

        print("\n── 搜索/筛选区 ──")
        for item in info.get('searchFormItems', []):
            print(f"  [{item['type']:12s}] label={item['label']:8s} | placeholder={item.get('placeholder',''):30s} | current={item.get('currentValue','')}")

        print("\n── 页面按钮（不含表格行内）──")
        for b in info.get('pageButtons', []):
            disabled = " [DISABLED]" if b.get('disabled') else ""
            print(f"  {b['text']}{disabled}  ({b['class'][:60]})")

        print("\n── 表格列头 ──")
        for h in info.get('tableHeaders', []):
            cb = " ☑" if h.get('hasCheckbox') else ""
            print(f"  [{h['index']}] {h['text']}{cb}")

        print(f"\n── 表格数据行 (共 {info.get('totalVisibleRows',0)} 行, 展示前3行) ──")
        for r, row in enumerate(info.get('sampleRows', [])):
            print(f"\n  Row {r+1}:")
            for cell in row:
                details = []
                if cell['hasCheckbox']: details.append('CHECKBOX')
                if cell['hasButtons']: details.append(f"BTNS: {cell['buttonTexts']}")
                if cell['hasDropdown']: details.append('DROPDOWN')
                if cell['hasSwitch']: details.append('SWITCH')
                if cell['hasTags']: details.append(f"TAGS: {cell['tagTexts']}")
                print(f"    Col{cell['colIndex']}: {cell['textPreview'][:80]}")
                if details:
                    print(f"           {' | '.join(details)}")

        print(f"\n── 分页 ──")
        pag = info.get('pagination', {})
        print(f"  总数: {pag.get('total','')}")
        print(f"  每页条数: {pag.get('sizes','')}")
        print(f"  上一页禁用: {pag.get('prevDisabled')}")
        print(f"  下一页禁用: {pag.get('nextDisabled')}")
        print(f"  页码: {pag.get('pageNumbers',[])}")

        # ── Phase 2: 点开新增弹窗看字段 ──
        print("\n" + "=" * 60)
        print("Phase 2: 打开「新增」弹窗")
        driver.execute_script("""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].innerText && btns[i].innerText.trim() === '新增') {
                    btns[i].click();
                    break;
                }
            }
        """)
        time.sleep(2)

        dialog_info = driver.execute_script(r'''
        function getAllText(el) {
            if (!el) return '';
            return (el.innerText || el.textContent || '').trim();
        }

        var dialogs = document.querySelectorAll('.el-dialog');
        var result = { count: 0, dialogs: [] };
        dialogs.forEach(function(dlg, di) {
            if (!dlg.offsetParent && dlg.offsetParent !== undefined && dlg.offsetParent === null && getComputedStyle(dlg).display === 'none') return;
            var d = {};
            d.title = getAllText(dlg.querySelector('.el-dialog__title, .el-dialog__header'));
            d.width = dlg.style.width || getComputedStyle(dlg).width;

            var items = [];
            var formItems = dlg.querySelectorAll('.el-form-item');
            formItems.forEach(function(item) {
                var label = item.querySelector('.el-form-item__label');
                var labelText = label ? getAllText(label).replace(/:$|：$/,'').replace(/\s+/g,'') : '';
                var input = item.querySelector('input:not([type="hidden"])');
                var textarea = item.querySelector('textarea');
                var select = item.querySelector('.el-select');
                var treeSelect = item.querySelector('.el-tree-select');
                var cascader = item.querySelector('.el-cascader');
                var selectSelected = select ? select.querySelector('.el-select__selected-item:not(.el-select__placeholder)') : null;
                var selectInput = select ? select.querySelector('input') : null;

                var tag = 'unknown';
                var currentVal = '';
                var placeholder = '';
                var isRequired = !!item.querySelector('.el-form-item__label .required, .is-required, .asterisk-left');

                if (textarea) {
                    tag = 'textarea';
                    currentVal = textarea.value || '';
                    placeholder = textarea.placeholder || '';
                } else if (input && !selectInput) {
                    tag = 'input';
                    placeholder = input.placeholder || '';
                    currentVal = input.value || '';
                    if (input.type === 'password') tag = 'password';
                } else if (treeSelect) {
                    tag = 'tree-select';
                    if (selectSelected) currentVal = getAllText(selectSelected);
                } else if (select) {
                    tag = 'select';
                    if (selectSelected) currentVal = getAllText(selectSelected);
                    else if (selectInput) { placeholder = selectInput.placeholder || ''; currentVal = selectInput.value || ''; }
                    // try multi-select
                    var selectedItems = select.querySelectorAll('.el-select__selected-item:not(.el-select__placeholder)');
                    if (selectedItems.length > 1) {
                        tag = 'select(multi)';
                        var vals = [];
                        selectedItems.forEach(function(si) { vals.push(getAllText(si)); });
                        currentVal = vals.join(', ');
                    }
                } else if (cascader) {
                    tag = 'cascader';
                    var cascInput = cascader.querySelector('input');
                    if (cascInput) { placeholder = cascInput.placeholder || ''; currentVal = cascInput.value || ''; }
                }

                items.push({
                    label: labelText,
                    type: tag,
                    required: isRequired,
                    placeholder: placeholder,
                    currentValue: currentVal
                });
            });
            d.formItems = items;

            // footer buttons
            var footerBtns = [];
            var footer = dlg.querySelector('.el-dialog__footer');
            if (footer) {
                footer.querySelectorAll('button').forEach(function(b) {
                    footerBtns.push({text: getAllText(b), primary: b.classList.contains('el-button--primary')});
                });
            }
            d.footerButtons = footerBtns;

            result.dialogs.push(d);
            result.count++;
        });
        return result;
        ''')

        # ── 先输出 Phase 1+2 JSON ──
        out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'page_structure.json')
        partial = {
            'url': driver.current_url,
            'breadcrumb': info.get('breadcrumb',''),
            'sidebarActive': info.get('sidebarActive',''),
            'searchFormItems': info.get('searchFormItems', []),
            'pageButtons': info.get('pageButtons', []),
            'tableHeaders': info.get('tableHeaders', []),
            'sampleRows': info.get('sampleRows', []),
            'totalRows': info.get('totalVisibleRows', 0),
            'pagination': info.get('pagination', {}),
            'dialog': dialog_info,
        }
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(partial, f, ensure_ascii=False, indent=2)
        print(f"\n[Phase1+2 JSON saved to {out_path}]")

        print(f"可见弹窗数: {dialog_info.get('count', 0)}")
        for d in dialog_info.get('dialogs', []):
            print(f"\n  弹窗标题: {d['title']}")
            print(f"  弹窗宽度: {d.get('width','')}")
            print(f"  表单字段 ({len(d.get('formItems',[]))} 个):")
            for item in d.get('formItems', []):
                req = " *必填" if item.get('required') else ""
                print(f"    [{item['type']:15s}] {item['label']:10s} {req}")
                if item.get('placeholder'):
                    print(f"                       placeholder: {item['placeholder']}")
                if item.get('currentValue'):
                    print(f"                       current: {item['currentValue'][:60]}")
            print(f"  底部按钮: {d.get('footerButtons',[])}")

        # ── 关闭弹窗 ──
        driver.execute_script("""
            var dialogs = document.querySelectorAll('.el-dialog');
            dialogs.forEach(function(d) {
                var cancelBtn = d.querySelector('.el-dialog__footer button:not(.el-button--primary)');
                if (cancelBtn) cancelBtn.click();
            });
        """)
        time.sleep(1)

        # ── Phase 3: 点开一行「更多」菜单 ──
        print("\n" + "=" * 60)
        print("Phase 3: 打开行内「更多」下拉菜单")
        driver.execute_script("""
            var dropdowns = document.querySelectorAll('.el-dropdown');
            for (var i = 0; i < dropdowns.length; i++) {
                var btn = dropdowns[i].querySelector('button');
                if (btn && btn.innerText && btn.innerText.includes('更多')) {
                    btn.click();
                    break;
                }
            }
        """)
        time.sleep(1.5)

        dropdown_info = driver.execute_script(r'''
        function getAllText(el) {
            if (!el) return '';
            return (el.innerText || el.textContent || '').trim();
        }
        var items = [];
        var poppers = document.querySelectorAll('.el-popper');
        poppers.forEach(function(p) {
            if (getComputedStyle(p).display === 'none') return;
            p.querySelectorAll('.el-dropdown-menu__item, li').forEach(function(li) {
                items.push(getAllText(li));
            });
        });
        return items;
        ''')
        print(f"「更多」菜单项: {dropdown_info}")

        # ── Phase 4: 列宽度信息 ──
        print("\n" + "=" * 60)
        print("Phase 4: 表格列宽详情")
        col_info = driver.execute_script(r'''
        function getAllText(el) {
            if (!el) return '';
            return (el.innerText || el.textContent || '').trim();
        }
        var cols = [];
        var ths = document.querySelectorAll('.el-table__header-wrapper th');
        ths.forEach(function(th, i) {
            var text = getAllText(th.querySelector('.cell') || th);
            if (text) {
                var w = th.offsetWidth || th.getBoundingClientRect().width;
                cols.push({col: i, header: text, widthPx: Math.round(w)});
            }
        });
        return cols;
        ''')
        for c in col_info:
            print(f"  Col{c['col']}: {c['header']:20s} width={c['widthPx']}px")

        # ── 输出JSON ──
        output = {
            'url': driver.current_url,
            'breadcrumb': info.get('breadcrumb',''),
            'sidebarActive': info.get('sidebarActive',''),
            'searchFormItems': info.get('searchFormItems', []),
            'pageButtons': info.get('pageButtons', []),
            'tableHeaders': info.get('tableHeaders', []),
            'sampleRows': info.get('sampleRows', []),
            'totalRows': info.get('totalVisibleRows', 0),
            'pagination': info.get('pagination', {}),
            'dialog': dialog_info,
            'dropdownMenu': dropdown_info,
            'columnWidths': col_info
        }

        out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'page_structure.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\n完整JSON已保存至: {out_path}")

    finally:
        if driver:
            try: driver.quit()
            except: pass

if __name__ == '__main__':
    main()
