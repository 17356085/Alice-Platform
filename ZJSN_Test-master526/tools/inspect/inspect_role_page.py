"""页面结构分析: 访问角色管理页面 + 权限弹窗，提取完整的渲染后 DOM 结构"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

OUT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def save_json(data, filename):
    path = os.path.join(OUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [JSON saved] {path}")

def main():
    base = BaseDriver()
    driver = None
    try:
        driver = base.open_browser()
        ensure_logged_in(driver)
        driver.get('https://aiwechatminidemo.cimc-digital.com/#/system/role')
        time.sleep(3)
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        time.sleep(2)

        print("=" * 70)
        print("Phase 1: 角色管理页面基础结构")
        print("=" * 70)

        phase1 = driver.execute_script(r'''
        function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }

        var info = {};

        // 面包屑
        var bc = document.querySelector('.el-breadcrumb');
        info.breadcrumb = bc ? T(bc) : 'NOT FOUND';

        // 搜索区表单项
        var formItems = [];
        document.querySelectorAll('.el-form-item').forEach(function(item) {
            if (item.closest('.el-dialog') || item.closest('.el-dialog__wrapper')) return;
            var label = item.querySelector('.el-form-item__label');
            var labelText = label ? T(label).replace(/:$|：$/,'').replace(/\s+/g,'') : null;
            if (!labelText) return;
            var input = item.querySelector('input:not([type="hidden"])');
            var select = item.querySelector('.el-select');
            var type = input ? (select ? 'select' : 'input') : (select ? 'select' : 'unknown');
            var placeholder = '';
            var currentVal = '';
            if (input) {
                placeholder = input.placeholder || '';
                currentVal = input.value || '';
            }
            if (select) {
                var sel = select.querySelector('.el-select__selected-item:not(.el-select__placeholder)');
                if (sel) currentVal = T(sel);
                else {
                    var si = select.querySelector('input');
                    if (si) { placeholder = si.placeholder || ''; currentVal = si.value || ''; }
                }
            }
            formItems.push({label: labelText, type: type, placeholder: placeholder, currentValue: currentVal});
        });
        info.searchFormItems = formItems;

        // 页面按钮（非表格行内、非弹窗内）
        var pageBtns = [];
        document.querySelectorAll('button.el-button').forEach(function(b) {
            if (b.closest('.el-dialog')) return;
            if (b.closest('.el-table__row')) return;
            if (b.closest('.el-pagination')) return;
            var text = T(b);
            if (text) pageBtns.push({
                text: text,
                primary: b.classList.contains('el-button--primary'),
                danger: b.classList.contains('el-button--danger'),
                disabled: b.classList.contains('is-disabled')
            });
        });
        info.pageButtons = pageBtns;

        // 表格列头
        var headers = [];
        document.querySelectorAll('.el-table__header-wrapper th').forEach(function(th, i) {
            var cell = th.querySelector('.cell');
            var text = T(cell || th);
            if (text) headers.push({index: i, text: text});
        });
        info.tableHeaders = headers;

        // 表格前5行
        var rows = [];
        document.querySelectorAll('tr.el-table__row').forEach(function(row, ri) {
            if (ri >= 5) return;
            var rowData = [];
            row.querySelectorAll('td').forEach(function(td, ci) {
                var cell = td.querySelector('.cell');
                var text = T(cell || td).substring(0, 120);
                var btns = td.querySelectorAll('button');
                var btnTexts = [];
                btns.forEach(function(b) { var t = T(b); if (t) btnTexts.push(t); });
                rowData.push({
                    col: ci,
                    text: text,
                    buttons: btnTexts
                });
            });
            rows.push(rowData);
        });
        info.sampleRows = rows;
        info.totalRows = document.querySelectorAll('tr.el-table__row').length;

        // 分页
        var pag = document.querySelector('.el-pagination');
        if (pag) {
            info.pagination = {
                total: T(pag.querySelector('.el-pagination__total')),
                sizes: T(pag.querySelector('.el-pagination__sizes'))
            };
        }

        // 角色名称列表（第2列，用于后续权限操作）
        info.roleNames = [];
        document.querySelectorAll('tr.el-table__row td:nth-child(2) .cell').forEach(function(cell) {
            var t = T(cell);
            if (t) info.roleNames.push(t);
        });

        return info;
        ''')

        print(f"面包屑: {phase1.get('breadcrumb','')}")
        print(f"\n搜索区 ({len(phase1.get('searchFormItems',[]))} 项):")
        for item in phase1.get('searchFormItems', []):
            print(f"  [{item['type']:10s}] label={item['label']:8s}  placeholder={item.get('placeholder',''):20s}  value={item.get('currentValue','')}")

        print(f"\n页面按钮:")
        for b in phase1.get('pageButtons', []):
            flags = []
            if b.get('primary'): flags.append('PRIMARY')
            if b.get('danger'): flags.append('DANGER')
            if b.get('disabled'): flags.append('DISABLED')
            print(f"  {b['text']}  [{', '.join(flags) if flags else 'default'}]")

        print(f"\n表格列头 ({len(phase1.get('tableHeaders',[]))} 列):")
        for h in phase1.get('tableHeaders', []):
            print(f"  [{h['index']}] {h['text']}")

        print(f"\n表格数据 (共 {phase1.get('totalRows',0)} 行，展示前5行):")
        for r, row in enumerate(phase1.get('sampleRows', [])):
            print(f"  Row{r+1}:")
            for cell in row:
                if cell['text'] or cell['buttons']:
                    btnStr = f"  BTNS={cell['buttons']}" if cell['buttons'] else ""
                    print(f"    Col{cell['col']}: {cell['text'][:60]}{btnStr}")

        print(f"\n分页: {phase1.get('pagination',{})}")
        print(f"\n角色名称列表 (前10): {phase1.get('roleNames',[])[:10]}")

        save_json(phase1, 'page_structure_role.json')

        # ── Phase 2: 点击第一行的「权限」按钮 ──
        print("\n" + "=" * 70)
        print("Phase 2: 点击「权限」按钮 → 权限弹窗")
        print("=" * 70)

        # 找一个非admin的角色来操作（admin可能受保护）
        target_role = None
        for name in phase1.get('roleNames', []):
            if 'admin' not in name.lower() and '超级管理员' not in name:
                target_role = name
                break
        if not target_role:
            target_role = phase1.get('roleNames', [''])[0]

        print(f"目标角色: {target_role}")

        # 点击该行的「权限」按钮
        clicked = driver.execute_script(f'''
            var rows = document.querySelectorAll('tr.el-table__row');
            for (var i = 0; i < rows.length; i++) {{
                var cells = rows[i].querySelectorAll('td');
                for (var j = 0; j < cells.length; j++) {{
                    if (cells[j].innerText && cells[j].innerText.indexOf('{target_role}') !== -1) {{
                        var btns = rows[i].querySelectorAll('button');
                        for (var k = 0; k < btns.length; k++) {{
                            if (btns[k].innerText && btns[k].innerText.indexOf('权限') !== -1) {{
                                btns[k].click();
                                return 'clicked';
                            }}
                        }}
                    }}
                }}
            }}
            return 'not found';
        ''')
        print(f"点击权限按钮结果: {clicked}")
        time.sleep(3)

        # ── Phase 3: 权限弹窗结构 ──
        print("\n" + "=" * 70)
        print("Phase 3: 权限弹窗完整结构")
        print("=" * 70)

        phase3 = driver.execute_script(r'''
        function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }

        var result = {};

        // 找可见的弹窗
        var dialogs = document.querySelectorAll('.el-dialog');
        var targetDlg = null;
        dialogs.forEach(function(dlg) {
            if (dlg.offsetParent !== null || getComputedStyle(dlg).display !== 'none') {
                targetDlg = dlg;
            }
        });
        // Also check drawer
        if (!targetDlg) {
            var drawers = document.querySelectorAll('.el-drawer');
            drawers.forEach(function(d) {
                if (d.offsetParent !== null || getComputedStyle(d).display !== 'none') {
                    result.drawerMode = true;
                    targetDlg = d;
                }
            });
        }

        if (!targetDlg) {
            result.error = 'NO_VISIBLE_DIALOG';
            return result;
        }

        // 弹窗标题
        var title = targetDlg.querySelector('.el-dialog__title, .el-drawer__title');
        result.title = title ? T(title) : '';

        // -- Tab 列表 --
        var tabs = [];
        var tabElements = targetDlg.querySelectorAll('.el-tabs__item');
        tabElements.forEach(function(tab, i) {
            var text = T(tab);
            var isActive = tab.classList.contains('is-active') || tab.parentElement.classList.contains('is-active');
            tabs.push({index: i, text: text, isActive: isActive, id: tab.id || ''});
        });
        result.tabs = tabs;

        // -- 当前激活Tab的内容 --
        var activePane = targetDlg.querySelector('.el-tab-pane.is-active, .el-tab-pane[style*="block"], .el-tab-pane:not([style*="none"])');
        if (!activePane) {
            // try first visible tab pane
            var allPanes = targetDlg.querySelectorAll('.el-tab-pane');
            for (var i = 0; i < allPanes.length; i++) {
                if (getComputedStyle(allPanes[i]).display !== 'none') {
                    activePane = allPanes[i];
                    break;
                }
            }
        }

        // 提取权限树结构
        result.permissionTree = {};
        if (activePane) {
            result.activePaneContent = T(activePane).substring(0, 500);

            // 树节点
            var treeNodes = [];
            activePane.querySelectorAll('.el-tree-node').forEach(function(node, ni) {
                var content = node.querySelector('.el-tree-node__content');
                var label = node.querySelector('.el-tree-node__label');
                var checkbox = node.querySelector('.el-checkbox');
                var isExpanded = node.classList.contains('is-expanded');
                var isLeaf = !node.querySelector('.el-tree-node__children');
                var indent = 0;
                var parent = node.parentElement;
                while (parent) {
                    if (parent.classList.contains('el-tree-node')) indent++;
                    parent = parent.parentElement;
                }
                var checkboxChecked = false;
                var checkboxIndeterminate = false;
                if (checkbox) {
                    checkboxChecked = checkbox.classList.contains('is-checked');
                    checkboxIndeterminate = checkbox.classList.contains('is-indeterminate');
                }
                treeNodes.push({
                    index: ni,
                    label: label ? T(label) : '',
                    indent: indent,
                    isLeaf: isLeaf,
                    isExpanded: isExpanded,
                    checkboxChecked: checkboxChecked,
                    checkboxIndeterminate: checkboxIndeterminate
                });
            });
            result.treeNodes = treeNodes;

            // 统计
            var totalNodes = treeNodes.length;
            var checkedNodes = treeNodes.filter(function(n) { return n.checkboxChecked; }).length;
            var leafNodes = treeNodes.filter(function(n) { return n.isLeaf; }).length;
            result.treeSummary = {
                totalNodes: totalNodes,
                checkedNodes: checkedNodes,
                leafNodes: leafNodes,
                maxDepth: treeNodes.length > 0 ? Math.max.apply(null, treeNodes.map(function(n) { return n.indent; })) : 0
            };

            // Radio buttons in active pane (for data scope)
            var radios = [];
            activePane.querySelectorAll('.el-radio').forEach(function(r, i) {
                radios.push({
                    index: i,
                    text: T(r),
                    isChecked: r.classList.contains('is-checked')
                });
            });
            if (radios.length > 0) result.radios = radios;
        } else {
            result.activePaneContent = 'NO_ACTIVE_PANE';
        }

        // -- 弹窗底部按钮 --
        var footerBtns = [];
        var footer = targetDlg.querySelector('.el-dialog__footer');
        if (footer) {
            footer.querySelectorAll('button').forEach(function(b) {
                footerBtns.push({
                    text: T(b),
                    primary: b.classList.contains('el-button--primary'),
                    disabled: b.classList.contains('is-disabled')
                });
            });
        }
        result.footerButtons = footerBtns;

        return result;
        ''')

        print(f"弹窗标题: {phase3.get('title','')}")
        print(f"\nTab列表 ({len(phase3.get('tabs',[]))} 个):")
        for tab in phase3.get('tabs', []):
            active = " ◀ ACTIVE" if tab.get('isActive') else ""
            print(f"  [{tab['index']}] id={tab.get('id','')}  text={tab['text']}{active}")

        print(f"\n权限树摘要: {phase3.get('treeSummary',{})}")
        print(f"权限树节点 (共 {len(phase3.get('treeNodes',[]))} 个):")
        for node in phase3.get('treeNodes', []):
            prefix = "  " * node['indent']
            cb = ""
            if node.get('checkboxChecked'): cb = " [✓]"
            elif node.get('checkboxIndeterminate'): cb = " [-]"
            else: cb = " [ ]"
            leaf = " (leaf)" if node.get('isLeaf') else ""
            print(f"{prefix}{cb} {node['label']}{leaf}")

        if phase3.get('radios'):
            print(f"\n数据权限单选 ({len(phase3.get('radios',[]))} 个):")
            for r in phase3.get('radios', []):
                checked = " ◀ SELECTED" if r.get('isChecked') else ""
                print(f"  [{'✓' if r.get('isChecked') else '○'}] {r['text']}{checked}")

        print(f"\n弹窗底部按钮: {phase3.get('footerButtons',[])}")

        save_json(phase3, 'page_structure_role_permission_dialog.json')

        # ── Phase 4: 切换到其他Tab查看结构 ──
        print("\n" + "=" * 70)
        print("Phase 4: 切换到其他权限Tab")
        print("=" * 70)

        all_tab_data = {}
        for tab in phase3.get('tabs', []):
            tab_text = tab.get('text', '')
            tab_id = tab.get('id', '')
            if tab.get('isActive'):
                continue  # 跳过已激活的

            print(f"\n切换Tab: {tab_text} (id={tab_id})")
            # Click the tab
            clicked = driver.execute_script(f'''
                var tabs = document.querySelectorAll('.el-tabs__item');
                for (var i = 0; i < tabs.length; i++) {{
                    if (tabs[i].innerText && tabs[i].innerText.indexOf('{tab_text}') !== -1) {{
                        tabs[i].click();
                        return 'clicked';
                    }}
                }}
                return 'not found';
            ''')
            time.sleep(1.5)

            # Extract this tab's tree
            tab_data = driver.execute_script(r'''
            function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }

            var activePane = document.querySelector('.el-tab-pane.is-active');
            if (!activePane) {
                var allPanes = document.querySelectorAll('.el-tab-pane');
                for (var i = 0; i < allPanes.length; i++) {
                    if (getComputedStyle(allPanes[i]).display !== 'none') {
                        activePane = allPanes[i];
                        break;
                    }
                }
            }
            if (!activePane) return {error: 'NO_ACTIVE_PANE'};

            var treeNodes = [];
            activePane.querySelectorAll('.el-tree-node').forEach(function(node, ni) {
                var content = node.querySelector('.el-tree-node__content');
                var label = node.querySelector('.el-tree-node__label');
                var checkbox = node.querySelector('.el-checkbox');
                var isExpanded = node.classList.contains('is-expanded');
                var isLeaf = !node.querySelector('.el-tree-node__children');
                var indent = 0;
                var parent = node.parentElement;
                while (parent) {
                    if (parent.classList.contains('el-tree-node')) indent++;
                    parent = parent.parentElement;
                }
                var checkboxChecked = checkbox ? checkbox.classList.contains('is-checked') : false;
                var checkboxIndeterminate = checkbox ? checkbox.classList.contains('is-indeterminate') : false;
                treeNodes.push({
                    index: ni,
                    label: label ? T(label) : '',
                    indent: indent,
                    isLeaf: isLeaf,
                    checkboxChecked: checkboxChecked,
                    checkboxIndeterminate: checkboxIndeterminate
                });
            });

            // Also check for radios
            var radios = [];
            activePane.querySelectorAll('.el-radio').forEach(function(r, i) {
                radios.push({index: i, text: T(r), isChecked: r.classList.contains('is-checked')});
            });

            return {treeNodes: treeNodes, radios: radios, totalNodes: treeNodes.length};
            ''')

            all_tab_data[tab_text] = tab_data
            print(f"  节点数: {tab_data.get('totalNodes', 0)}")
            if tab_data.get('radios'):
                print(f"  单选: {[r['text'] for r in tab_data['radios']]}")

            # Show first few nodes
            for node in tab_data.get('treeNodes', [])[:10]:
                prefix = "    " + "  " * node['indent']
                cb = "[✓]" if node.get('checkboxChecked') else ("[-]" if node.get('checkboxIndeterminate') else "[ ]")
                print(f"{prefix}{cb} {node['label']}")

            if tab_data.get('totalNodes', 0) > 10:
                print(f"    ... 还有 {tab_data['totalNodes'] - 10} 个节点")

        save_json(all_tab_data, 'page_structure_role_all_tabs.json')

        # ── Phase 5: 关闭弹窗 → 查看新增角色弹窗 ──
        print("\n" + "=" * 70)
        print("Phase 5: 关闭权限弹窗 → 查看新增角色弹窗")
        print("=" * 70)

        # Close the permission dialog
        driver.execute_script("""
            var dialogs = document.querySelectorAll('.el-dialog');
            dialogs.forEach(function(d) {
                var cancel = d.querySelector('.el-dialog__footer button:not(.el-button--primary)');
                if (cancel) cancel.click();
            });
        """)
        time.sleep(1.5)

        # Click "新增" button
        driver.execute_script("""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].innerText && btns[i].innerText.trim() === '新增') {
                    btns[i].click();
                    return;
                }
            }
        """)
        time.sleep(2)

        phase5 = driver.execute_script(r'''
        function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }

        var result = {};
        var dialogs = document.querySelectorAll('.el-dialog');
        var targetDlg = null;
        dialogs.forEach(function(dlg) {
            if (dlg.offsetParent !== null || getComputedStyle(dlg).display !== 'none') {
                targetDlg = dlg;
            }
        });
        if (!targetDlg) { result.error = 'NO_VISIBLE_DIALOG'; return result; }

        result.title = T(targetDlg.querySelector('.el-dialog__title'));

        var formItems = [];
        targetDlg.querySelectorAll('.el-form-item').forEach(function(item) {
            var label = item.querySelector('.el-form-item__label');
            var labelText = label ? T(label).replace(/:$|：$/,'').replace(/\s+/g,'') : '';
            if (!labelText) return;
            var input = item.querySelector('input:not([type="hidden"])');
            var textarea = item.querySelector('textarea');
            var select = item.querySelector('.el-select');
            var radioGroup = item.querySelector('.el-radio-group');
            var type = 'unknown';
            var placeholder = '';
            var currentVal = '';
            var isRequired = !!item.querySelector('.is-required, .asterisk-left');

            if (input && !(select && select.querySelector('input'))) {
                type = input.type === 'password' ? 'password' : 'input';
                placeholder = input.placeholder || '';
                currentVal = input.value || '';
            } else if (textarea) {
                type = 'textarea';
                placeholder = textarea.placeholder || '';
                currentVal = textarea.value || '';
            } else if (select) {
                type = 'select';
                var sel = select.querySelector('.el-select__selected-item:not(.el-select__placeholder)');
                if (sel) currentVal = T(sel);
                else {
                    var si = select.querySelector('input');
                    if (si) { placeholder = si.placeholder || ''; currentVal = si.value || ''; }
                }
            } else if (radioGroup) {
                type = 'radio-group';
                var checked = radioGroup.querySelector('.is-checked span');
                currentVal = checked ? T(checked) : '';
            }
            formItems.push({
                label: labelText,
                type: type,
                required: isRequired,
                placeholder: placeholder,
                currentValue: currentVal
            });
        });
        result.formItems = formItems;

        var footerBtns = [];
        var footer = targetDlg.querySelector('.el-dialog__footer');
        if (footer) {
            footer.querySelectorAll('button').forEach(function(b) {
                footerBtns.push({text: T(b), primary: b.classList.contains('el-button--primary')});
            });
        }
        result.footerButtons = footerBtns;

        return result;
        ''')

        print(f"新增弹窗标题: {phase5.get('title','')}")
        print(f"表单字段 ({len(phase5.get('formItems',[]))} 个):")
        for item in phase5.get('formItems', []):
            req = " *必填" if item.get('required') else ""
            print(f"  [{item['type']:12s}] {item['label']:10s}{req}  placeholder={item.get('placeholder',''):20s}  value={item.get('currentValue','')}")
        print(f"底部按钮: {phase5.get('footerButtons',[])}")

        save_json(phase5, 'page_structure_role_add_dialog.json')

        print("\n" + "=" * 70)
        print("全部采集完成!")
        print("=" * 70)

    finally:
        if driver:
            try: driver.quit()
            except: pass

if __name__ == '__main__':
    main()
