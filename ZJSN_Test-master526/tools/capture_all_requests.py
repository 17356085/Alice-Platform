"""Capture ALL XHR/fetch requests during edit-dialog save"""
import sys, time, json
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

base = BaseDriver()
d = base.open_browser()
d.maximize_window()

# Install interceptor — capture ALL methods, filter later
d.execute_script("""
window.__all = [];
(function() {
    var OX = XMLHttpRequest.prototype.open;
    var OS = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(m, u) {
        this._m = m; this._u = u; return OX.apply(this, arguments);
    };
    XMLHttpRequest.prototype.send = function(b) {
        window.__all.push({method: this._m, url: this._u, body: b ? String(b).substring(0,600) : null});
        return OS.apply(this, arguments);
    };
})();
""")

ensure_logged_in(d)
time.sleep(2)
print('Admin logged in')

nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/user', 'user')
time.sleep(4)

# Clear previous capture (page load requests)
d.execute_script('window.__all = [];')
print('Capture buffer cleared')

# Search
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
time.sleep(2)

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

# Save: try multiple confirm button patterns
d.execute_script("""
var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
if (!dlg) {
    var ds = document.querySelectorAll('.el-dialog');
    for (var i=0; i<ds.length; i++) { if (ds[i].offsetParent) { dlg=ds[i]; break; } }
}
if (!dlg) return;
// Try footer button first
var footer = dlg.querySelector('.el-dialog__footer');
var container = footer || dlg;
var btns = container.querySelectorAll('button');
for (var i=0; i<btns.length; i++) {
    var t = (btns[i].textContent||'').trim();
    console.log('Button:', t);
    if (t === '确定' || t === '确认' || t === '保存') {
        btns[i].click(); return;
    }
}
// Fallback: primary button
var pb = dlg.querySelector('button.el-button--primary');
if (pb) pb.click();
""")
time.sleep(4)
print('Saved')

# Print ALL captured requests
print('\n' + '='*60)
print('ALL CAPTURED REQUESTS')
print('='*60)
all_reqs = d.execute_script('return window.__all;')
for r in (all_reqs or []):
    m = r.get('method','?')
    url = r.get('url','')[:200]
    body = r.get('body','') or ''
    print('[%s] %s  body=%s' % (m, url, body[:300]))

d.quit()
