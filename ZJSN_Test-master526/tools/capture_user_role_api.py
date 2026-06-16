"""Capture the exact API for user-role assignment"""
import sys, time, json
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator

base = BaseDriver()
d = base.open_browser()
d.maximize_window()

# Install interceptor
d.execute_script("""
window.__captured = [];
var OX = XMLHttpRequest.prototype.open;
var OS = XMLHttpRequest.prototype.send;
XMLHttpRequest.prototype.open = function(m, u) {
    this._m = m; this._u = u; return OX.apply(this, arguments);
};
XMLHttpRequest.prototype.send = function(b) {
    var s = this;
    var cap = {type:'XHR', method:s._m, url:s._u, body:b, time:Date.now()};
    var old = s.onreadystatechange;
    s.onreadystatechange = function() {
        if (s.readyState === 4) { cap.status = s.status; cap.rt = s.responseText ? s.responseText.substring(0, 300) : ''; }
        if (old) old.apply(s, arguments);
    };
    window.__captured.push(cap);
    return OS.apply(this, arguments);
};
var OF = window.fetch;
window.fetch = function(input, init) {
    var url = typeof input === 'string' ? input : input.url;
    var method = (init && init.method) || 'GET';
    var cap = {type:'FETCH', method:method, url:url, body:init?init.body:null, time:Date.now()};
    window.__captured.push(cap);
    return OF.apply(this, arguments).then(function(r) { cap.status = r.status; return r; });
};
""")

# Login
ensure_logged_in(d)
time.sleep(2)
print('Admin logged in')

# Navigate to user management
nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/user', 'user')
time.sleep(4)
print('At user management')

# Search rbac_test_sys
d.execute_script("""
var inputs = document.querySelectorAll('input');
for (var i=0; i<inputs.length; i++) {
    var ph = inputs[i].placeholder || '';
    if (ph.indexOf('用户') !== -1) {
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
print('Searched')

# Click edit on the row
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
print('Edit dialog open')

# Open role select in the dialog
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
print('Role select opened')

# Select RBAC-SYS-ONLY
d.execute_script("""
var items = document.querySelectorAll('.el-select-dropdown__item');
for (var i=0; i<items.length; i++) {
    if ((items[i].textContent||'').indexOf('RBAC-SYS-ONLY') !== -1) {
        items[i].click(); return;
    }
}
""")
time.sleep(1)
print('Role selected')

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
time.sleep(3)
print('Confirmed')

# Print captured non-GET requests
time.sleep(1)
captured = d.execute_script('return window.__captured;')
print('\n' + '='*60)
print('NON-GET REQUESTS CAPTURED')
print('='*60)
for r in captured:
    m = r.get('method','?')
    if m == 'GET':
        continue
    url = r.get('url','')[:200]
    body = str(r.get('body',''))[:1000]
    status = r.get('status','?')
    rt = r.get('rt','')
    print('\n[%s] %s %s  status=%s' % (r['type'], m, url, status))
    if body and body != 'None' and body != 'null':
        print('  REQUEST body: %s' % body[:600])
    if rt:
        print('  RESPONSE: %s' % rt[:400])

d.quit()
