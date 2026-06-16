"""Final: API role+menus, UI perms, UI user create, UI sidebar verify"""
import sys, time, json
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.LoginPage import LoginPage
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

PWD = "Ajyl@2026"
USERNAME = "rbac_test_%d" % int(time.time() % 100000)
print("Target: %s / %s" % (USERNAME, PWD))

base = BaseDriver()
d = base.open_browser()
d.maximize_window()
ensure_logged_in(d)
time.sleep(2)

def api(method, path, body=None):
    d.set_script_timeout(15)
    js = '' if body is None else 'body: JSON.stringify(%s),' % json.dumps(body, ensure_ascii=False)
    return d.execute_script('''
        return fetch("https://aiwechatminidemo.cimc-digital.com''' + path + '''", {
            method: "''' + method + '''",
            headers: { "Content-Type": "application/json",
                "Authorization": "Bearer " + JSON.parse(
                    decodeURIComponent(document.cookie.split("authorized-token=")[1].split(";")[0])
                ).accessToken },
            ''' + js + '''
        }).then(function(r) { return r.json(); });
    ''')

# ---- 1. API: Create role + menus ----
resp = api("POST", "/api/system/role", {"roleName":"RBAC-SYS-ONLY","roleSort":91,"status":"1","remark":"test"})
time.sleep(1)
rid = None
for r in api("GET","/api/system/role/list?pageNum=1&pageSize=100").get("data",{}).get("records",[]):
    if r.get("roleName") == "RBAC-SYS-ONLY": rid = r["id"]
print("Role: %s" % rid)

# Skip API menus - UI will set them properly
# API: set menu structure (type 1+2+3) - needed for sidebar
menus = api("GET","/api/system/menu/list?pageNum=1&pageSize=500").get("data",{}).get("records",[])
tree = {}; [tree.setdefault(m.get("parentId",0),[]).append(m["id"]) for m in menus]
def collect(pid, r): [r.append(cid) or collect(cid, r) for cid in tree.get(pid,[])]
mids = []
for m in menus:
    if m.get("menuName")=="系统管理" and m.get("menuType")==1 and m.get("parentId")==0:
        mids.append(m["id"]); collect(m["id"], mids)
api("PUT","/api/system/role/%s/menus"%rid, mids)
api("PUT","/api/system/role/%s/data-scope"%rid,{"dataScope":1})
print("API menus: %d (for sidebar structure)" % len(mids))

# ---- 2. UI: Open permission dialog, toggle one, save ----
nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/role','perm'); time.sleep(4)
# Wait for table rows to appear
WebDriverWait(d, 10).until(lambda x: x.execute_script(
    "return document.querySelectorAll('.el-table__body-wrapper tbody tr').length > 0;"
))
print("Table loaded, rows: %d" % d.execute_script("return document.querySelectorAll('.el-table__body-wrapper tbody tr').length;"))
time.sleep(1)

result = d.execute_script("""
try {
 var rows=document.querySelectorAll('.el-table__body-wrapper tbody tr');
 for(var i=0;i<rows.length;i++){
  var txt=(rows[i].textContent||'').trim();
  if(txt.indexOf('RBAC-SYS-ONLY')!==-1){
   var btns=rows[i].querySelectorAll('button');
   for(var j=0;j<btns.length;j++){
    var bt=(btns[j].textContent||'').trim();
    if(bt==='权限'||bt.indexOf('权限')!==-1){btns[j].click();return 'clicked_'+bt;}
   }
   return 'row_found_no_perm_btn';
  }
 }
 return 'not_found_in_'+rows.length+'_rows';
}catch(e){return 'error: '+e.message;}
""")
print("Perm click: %s" % result)
time.sleep(2)
tab_ok = d.execute_script("var t=document.querySelector('#tab-operations');if(t){t.click();return true;}return false;")
print("PC tab: %s" % tab_ok)
time.sleep(2)
# Expand all groups first
d.execute_script("""
var arrows=document.querySelectorAll('.perm-group__arrow');
for(var i=0;i<arrows.length;i++){if(arrows[i].offsetParent)arrows[i].click();}
""")
time.sleep(1)
# Toggle ALL unchecked permission checkboxes (skip group-level value="on")
toggled = d.execute_script("""
var count=0;
var cbs=document.querySelectorAll('.el-dialog .el-checkbox');
for(var i=0;i<cbs.length;i++){
 if(cbs[i].classList.contains('is-checked')) continue;
 var inp=cbs[i].querySelector('input[type=\"checkbox\"]');
 if(!inp||inp.value==='on') continue;
 var inner=cbs[i].querySelector('.el-checkbox__inner');
 if(inner&&inner.offsetParent){inner.click();count++; if(count>=500) break;}
}
return 'toggled_'+count;
""")
print("Perms toggled: %s" % toggled)
time.sleep(1)
# Save
saved = d.execute_script("""
var dlg=document.querySelector('.el-dialog:not([style*=\"display:none\"])');
if(!dlg){var ds=document.querySelectorAll('.el-dialog');for(var i=0;i<ds.length;i++){if(ds[i].offsetParent){dlg=ds[i];break}}}
if(!dlg)return 'no_dlg';
var btn=dlg.querySelector('button.el-button--primary');
if(btn){btn.click();return 'saved';}
return 'no_btn';
""")
print("Perm save: %s" % saved)
time.sleep(2)
print("Toast: %s" % (d.execute_script("var e=document.querySelector('.el-message__content');return e?e.textContent.trim():'';") or 'NONE'))

# ---- 3. UI: Create user ----
for u in api("GET","/api/system/user/list?pageNum=1&pageSize=5&username="+USERNAME).get("data",{}).get("records",[]):
    api("DELETE","/api/system/user/%s"%u["id"])

nav._navigate_by_js_hash('#/system/user','user'); time.sleep(3)
d.execute_script("""
var btns=document.querySelectorAll('button');
for(var i=0;i<btns.length;i++){if((btns[i].textContent||'').trim()==='新增'){btns[i].click();break;}}""")
time.sleep(3)
print("Add dialog opened")

# Fill form
for inp in d.find_elements(By.CSS_SELECTOR,'.el-dialog input'):
    try:
        ph = inp.get_attribute('placeholder') or ''
        if '用户' in ph:
            inp.click(); inp.send_keys(Keys.CONTROL+'a'); inp.send_keys(USERNAME)
        elif '姓名' in ph:
            inp.click(); inp.send_keys(Keys.CONTROL+'a'); inp.send_keys('SYS-Test')
        elif '手机' in ph:
            inp.send_keys('138%08d' % int(time.time()%100000000))
        elif inp.get_attribute('type') == 'password':
            inp.click()
            for _ in range(30): inp.send_keys(Keys.BACKSPACE)
            inp.send_keys(PWD)
    except: pass
time.sleep(0.3)
print("Form filled")

# Handle selects: 0=dept, 1=skip(user-type), 2=role
for idx, sel in enumerate(d.find_elements(By.CSS_SELECTOR,'.el-dialog .el-select__wrapper')):
    if idx == 1: continue
    try:
        d.execute_script("arguments[0].scrollIntoView({block:'center'});", sel)
        sel.click(); time.sleep(0.8)
        opts = [o for o in d.find_elements(By.CSS_SELECTOR,'.el-select-dropdown__item') if o.is_displayed()]
        if idx == 2:
            for o in opts:
                if 'RBAC-SYS-ONLY' in (o.text or ''): o.click(); print("Role selected"); break
        elif opts:
            opts[0].click(); print("Dept selected")
        time.sleep(0.5)
    except Exception as e:
        print("Select %d err: %s" % (idx, str(e)[:50]))
print("Selects done")

# Confirm
user_created = d.execute_script("""
var dlg=document.querySelector('.el-dialog:not([style*=\"display:none\"])');
if(!dlg){var ds=document.querySelectorAll('.el-dialog');for(var i=0;i<ds.length;i++){if(ds[i].offsetParent){dlg=ds[i];break}}}
if(!dlg)return 'no_dlg';
var btns=dlg.querySelectorAll('button');
for(var i=0;i<btns.length;i++){if((btns[i].textContent||'').indexOf('确定')!==-1){btns[i].click();return 'clicked';}}
return 'no_confirm_btn';
""")
print("User confirm: %s" % user_created)
time.sleep(3)
toast = d.execute_script("var e=document.querySelector('.el-message__content');return e?e.textContent.trim():'';")
print("Create toast: %s" % (toast or 'NONE'))

# ---- 4. Verify: navigate to login, login as new user ----
d.get("https://aiwechatminidemo.cimc-digital.com/"); time.sleep(4)
lp = LoginPage(d)
# Wait for login form
WebDriverWait(d, 10).until(lambda x: lp.is_login_page() or x.execute_script("return document.querySelector('input[type=\"password\"]')!=null;"))
lp.input_username(USERNAME); lp.input_password(PWD)
d.execute_script("document.querySelector('.el-button--primary').click();")
try: WebDriverWait(d, 20).until(lambda x: "#/login" not in (x.current_url or ''))
except: print("Login timeout"); d.quit(); sys.exit(1)
lp.wait_vue_stable(); time.sleep(3)

menus = d.execute_script("""
var m=[];document.querySelectorAll('.el-menu > li.el-sub-menu > .el-sub-menu__title span')
 .forEach(function(s){var t=(s.innerText||'').trim();if(t)m.push(t);});
document.querySelectorAll('.el-menu > li.el-menu-item span')
 .forEach(function(s){var t=(s.innerText||'').trim();if(t)m.push(t);});
return m;""")
print("SIDEBAR(%d): %s" % (len(menus), menus))
if len(menus) > 0: print("*** SUCCESS ***")
else: print("*** EMPTY ***")
d.quit()
