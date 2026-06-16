"""Debug: test different ways to click checkbox in assign-role dialog"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator

base = BaseDriver()
driver = None
try:
    driver = base.open_browser()
    driver.maximize_window()
    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)
    nav.navigate_to("系统管理", "用户管理")
    time.sleep(3)

    # Search and click 分配角色 via text
    driver.execute_script("""
        var inp = document.querySelector('input[placeholder*="搜索"]');
        if(inp){inp.value='rbac_test_hr';inp.dispatchEvent(new Event('input',{bubbles:true}));}
    """)
    time.sleep(0.5)
    driver.execute_script("""
        document.querySelectorAll('button').forEach(function(b){
            if(b.innerText&&b.innerText.trim()==='查询')b.click();
        });
    """)
    time.sleep(2)

    driver.execute_script("""
        var rows=document.querySelectorAll('tr.el-table__row');
        for(var i=0;i<rows.length;i++){
            if(rows[i].innerText.indexOf('rbac_test_hr')===-1)continue;
            var btns=rows[i].querySelectorAll('button');
            for(var k=0;k<btns.length;k++){
                var t=(btns[k].innerText||'').trim();
                if(t==='分配角色'){btns[k].click();return;}
            }
        }
    """)
    time.sleep(3)

    title = driver.execute_script("return document.querySelector('.el-dialog .el-dialog__title')?.innerText||'';")
    print(f"Dialog: '{title}'")

    if '分配角色' not in title:
        print("Wrong dialog!")
        sys.exit(1)

    # Find the checkbox label for "RBAC-仅人员管理"
    checkbox = driver.execute_script("""
        var dlg = document.querySelector('.el-dialog');
        if(!dlg) return null;
        var labels = dlg.querySelectorAll('label.el-checkbox');
        for(var i=0;i<labels.length;i++){
            var t = (labels[i].innerText||'').trim();
            if(t === 'RBAC-仅人员管理') {
                return { html: labels[i].outerHTML.substring(0, 500), isChecked: labels[i].classList.contains('is-checked') };
            }
        }
        return null;
    """)
    print(f"Checkbox state before: {json.dumps(checkbox, ensure_ascii=False)}")

    # Method 1: Click the label via Selenium ActionChains
    print("\nMethod 1: ActionChains click on label...")
    label = driver.find_element(By.XPATH,
        "//div[contains(@class,'el-dialog')]//label[contains(@class,'el-checkbox')][.//span[text()='RBAC-仅人员管理']]")
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", label)
    time.sleep(0.5)
    ActionChains(driver).move_to_element(label).click(label).perform()
    time.sleep(1)

    state1 = driver.execute_script("""
        var dlg = document.querySelector('.el-dialog');
        if(!dlg) return null;
        var labels = dlg.querySelectorAll('label.el-checkbox');
        for(var i=0;i<labels.length;i++){
            var t = (labels[i].innerText||'').trim();
            if(t === 'RBAC-仅人员管理') {
                var input = labels[i].querySelector('.el-checkbox__original');
                var cb = labels[i];
                return { isChecked: cb.classList.contains('is-checked'),
                         inputChecked: input ? input.checked : 'no_input',
                         classList: cb.className };
            }
        }
        return null;
    """)
    print(f"  After click: {state1}")

    # Now click confirm to submit
    print("\nClicking confirm...")
    driver.execute_script("""
        var dlg=document.querySelector('.el-dialog');
        if(dlg){var btn=dlg.querySelector('.el-dialog__footer button.el-button--primary');if(btn)btn.click();}
    """)
    time.sleep(2)
    toast = driver.execute_script("return document.querySelector('.el-message__content')?.innerText||'';")
    print(f"Toast: {toast}")

    # Verify
    token = None
    for c in driver.get_cookies():
        if c['name'] == 'authorized-token':
            import urllib.parse
            td = json.loads(urllib.parse.unquote(c['value']))
            token = td.get('accessToken')
            break
    if token:
        v = driver.execute_script(f"""
            return fetch('https://aiwechatminidemo.cimc-digital.com/api/system/user/list?pageNum=1&pageSize=20&username=rbac_test_hr',{{
                headers:{{'Authorization':'Bearer {token}'}}
            }}).then(r=>r.json());
        """)
        u = v.get('data',{}).get('records',[{}])[0]
        print(f"roleIds after: {u.get('roleIds',[])}")

finally:
    if driver:
        try: base.close_browser()
        except: pass
