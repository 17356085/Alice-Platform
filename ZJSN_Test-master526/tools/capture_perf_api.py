"""Capture network via Performance API (browser-level, immune to JS prototype issues)"""
import sys, time, json
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator

base = BaseDriver()
d = base.open_browser()
d.maximize_window()

# Enable Performance logging and install interceptor BEFORE navigation
d.execute_script("""
// Use PerformanceObserver to capture ALL resource timing
window.__perfEntries = [];
try {
    var po = new PerformanceObserver(function(list) {
        var entries = list.getEntries();
        for (var i = 0; i < entries.length; i++) {
            window.__perfEntries.push({
                name: entries[i].name,
                type: entries[i].entryType,
                initiatorType: entries[i].initiatorType,
                duration: entries[i].duration
            });
        }
    });
    po.observe({type: 'resource', buffered: true});
} catch(e) { console.log('PO error:', e); }

// Also try XHR interception AFTER page is ready
setTimeout(function() {
    var OX = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.send = function(b) {
        window.__perfEntries.push({name: this._u || '?', type: 'xhr-late', method: this._m || '?'});
        return (function(body) { return XMLHttpRequest.prototype.send.apply(this, arguments); }).call(this, b);
    };
    XMLHttpRequest.prototype.open = function(m, u) {
        this._m = m; this._u = u; return OX.apply(this, arguments);
    };
}, 1000);
""")

ensure_logged_in(d)
time.sleep(2)
print('Logged in')

# Navigate
nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/user', 'user')
time.sleep(5)

# Record current entry count as baseline
baseline = d.execute_script('return window.__perfEntries.length;')
print('Baseline entries: %d' % baseline)

# Search for rbac_test_sys
d.execute_script("""
var inputs = document.querySelectorAll('input');
for (var i=0; i<inputs.length; i++) {
    if ((inputs[i].placeholder||'').indexOf('用户') !== -1) {
        inputs[i].value = 'rbac_test_sys';
        inputs[i].dispatchEvent(new Event('input', {bubbles:true}));
        break;
    }
}
var btns = document.querySelectorAll('button');
for (var j=0; j<btns.length; j++) {
    if ((btns[j].textContent||'').indexOf('搜索') !== -1) { btns[j].click(); break; }
}
""")
time.sleep(3)

# Click edit
d.execute_script("""
var rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
for (var i=0; i<rows.length; i++) {
    if ((rows[i].textContent||'').indexOf('rbac_test_sys') !== -1) {
        var btns = rows[i].querySelectorAll('td:last-child button');
        for (var j=0; j<btns.length; j++) {
            if ((btns[j].textContent||'').indexOf('编辑') !== -1) {
                btns[j].click(); return;
            }
        }
    }
}
""")
time.sleep(3)

# Open role select
d.execute_script("""
var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
if (!dlg) { var ds = document.querySelectorAll('.el-dialog'); for (var i=0; i<ds.length; i++) { if (ds[i].offsetParent) { dlg=ds[i]; break; } } }
if (!dlg) return;
var selects = dlg.querySelectorAll('.el-select');
for (var s=0; s<selects.length; s++) {
    var fi = selects[s].closest('.el-form-item');
    if (fi) {
        var lb = fi.querySelector('.el-form-item__label');
        if (lb && (lb.textContent||'').indexOf('角色') !== -1) {
            var tr = selects[s].querySelector('.el-select__wrapper, .select-trigger, .el-input__wrapper');
            if (tr) tr.click(); else selects[s].click();
            return;
        }
    }
}
""")
time.sleep(1.5)

# Select role
d.execute_script("""
var items = document.querySelectorAll('.el-select-dropdown__item');
for (var i=0; i<items.length; i++) {
    if ((items[i].textContent||'').indexOf('RBAC-SYS-ONLY') !== -1) {
        items[i].click(); return;
    }
}
""")
time.sleep(1)

# Click confirm
d.execute_script("""
var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
if (!dlg) return;
var btns = dlg.querySelectorAll('button.el-button--primary');
for (var i=0; i<btns.length; i++) {
    var t = (btns[i].textContent||'').trim();
    if (t && t.indexOf('取消') === -1) { btns[i].click(); return; }
}
""")
time.sleep(4)
print('Save clicked')

# Print NEW entries since baseline
print('\n' + '='*60)
print('NEW NETWORK ENTRIES (since baseline %d)' % baseline)
print('='*60)
entries = d.execute_script('return window.__perfEntries;')
new_entries = entries[baseline:] if entries else []
for e in new_entries:
    name = e.get('name','')[:200]
    etype = e.get('type','?')
    method = e.get('method','')
    if 'api' in name.lower() or 'fetch' in etype.lower() or 'xhr' in etype.lower() or method:
        print('[%s] %s %s' % (etype, method, name))
    elif 'xmlhttprequest' in str(e.get('initiatorType','')).lower():
        print('[%s] %s %s' % (etype, method, name))

# Also check for ANY new entries to confirm capture is working
if not new_entries:
    print('No new entries captured!')
    # Check if PerformanceObserver is working
    all_entries = d.execute_script('return window.__perfEntries.length;')
    print('Total entries: %d, baseline was: %d' % (all_entries or 0, baseline))
else:
    print('Total new entries: %d' % len(new_entries))

d.quit()
