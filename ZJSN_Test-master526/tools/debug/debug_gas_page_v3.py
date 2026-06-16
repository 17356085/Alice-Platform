"""调试脚本 v3 — 深度检查页面渲染内容"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.browser_driver import BaseDriver, ensure_logged_in

base = BaseDriver()
driver = base.open_browser()
try:
    print("[1] 登录...")
    ensure_logged_in(driver)
    time.sleep(2)

    print("[2] JS hash 跳转...")
    driver.execute_script("window.location.hash = '#/lab/gas/report';")
    time.sleep(5)

    print("[3] 等待更长时间 (5s)...")
    time.sleep(5)

    driver.save_screenshot("debug_output/gas_page_v3.png")

    info = driver.execute_script("""
        var result = {};
        result.url = window.location.href;

        // 检查主内容区
        var appMain = document.querySelector('.app-main, .main-container, [class*=main]');
        if (appMain) {
            result.appMainHTML = appMain.innerHTML.substring(0, 3000);
            result.appMainText = (appMain.textContent || '').trim().substring(0, 1000);
        }

        // 检查 router-view 内容
        var routerView = document.querySelector('router-view, [class*=router]');
        if (!routerView) {
            routerView = document.querySelector('#app > div:nth-child(2), .el-container > div:last-child');
        }
        if (routerView) {
            result.routerViewHTML = routerView.innerHTML.substring(0, 3000);
        }

        // 检查是否有 loading 遮罩
        var loading = document.querySelectorAll('.el-loading-mask, [class*=loading]');
        result.loadingMasks = loading.length;
        for (var l = 0; l < loading.length; l++) {
            if (loading[l].offsetHeight > 0) {
                result['loading_' + l] = 'visible';
            }
        }

        // 检查是否有 iframe
        var iframes = document.querySelectorAll('iframe');
        result.iframeCount = iframes.length;

        // 查找所有 input 元素
        var inputs = document.querySelectorAll('input:not([type=hidden])');
        var inputInfo = [];
        for (var i = 0; i < inputs.length; i++) {
            var inp = inputs[i];
            if (inp.offsetHeight > 0) {
                inputInfo.push({
                    type: inp.type,
                    placeholder: (inp.placeholder || ''),
                    class: String(inp.className).substring(0, 40),
                });
            }
        }
        result.inputs = inputInfo;

        // 查找所有可见的大块内容
        var allDivs = document.querySelectorAll('div[class]');
        var meaningfulDivs = [];
        for (var d = 0; d < allDivs.length; d++) {
            var el = allDivs[d];
            if (el.offsetHeight < 100 || el.offsetWidth < 200) continue;
            var cls = String(el.className).substring(0, 60);
            var text = (el.textContent || '').trim().substring(0, 80);
            if (text.length > 10) {
                meaningfulDivs.push(cls + ' -> ' + text);
            }
        }
        result.meaningfulDivs = meaningfulDivs.slice(0, 20);

        return JSON.stringify(result, null, 2);
    """)

    with open("debug_output/gas_page_v3_info.json", "w", encoding="utf-8") as f:
        f.write(info)
    print("[4] JSON 已保存到 debug_output/gas_page_v3_info.json")
    # 打印不包含中文的关键信息
    import json
    data = json.loads(info)
    for k in ['url', 'loadingMasks', 'iframeCount', 'inputs']:
        print(f"  {k}: {data.get(k)}")
    print(f"  appMainText (first 200): {data.get('appMainText', '')[:200]}")
    print(f"  meaningfulDivs count: {len(data.get('meaningfulDivs', []))}")

finally:
    base.close_browser()
