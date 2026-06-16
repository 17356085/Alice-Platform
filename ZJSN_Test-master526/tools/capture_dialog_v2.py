"""快速弹窗 DOM 捕获 — 修正版

捕获新增储罐弹窗的完整 DOM（el-dialog 容器 + 表单字段）。
已确认 tank 弹窗使用 Element Plus 组件 (el-dialog, el-button, el-form-item)。
"""
import json, logging, os, sys, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.browser_driver import BaseDriver, ensure_logged_in
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("dialog-capture")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE_DIR, "artifacts", "dom_capture")
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs(OUT, exist_ok=True)


def save(name, content):
    p = os.path.join(OUT, f"{name}_{TS}")
    if isinstance(content, (dict, list)):
        p += ".json"
        with open(p, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
    else:
        p += ".html"
        with open(p, "w", encoding="utf-8") as f:
            f.write(str(content))
    log.info("  -> %s", os.path.basename(p))


def main():
    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        driver.get("https://aiwechatminidemo.cimc-digital.com/#/tank/monitor")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.data-table, .stats-cards"))
        )
        log.info("页面已加载")

        # 点击新增储罐
        add_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"新增储罐")]'))
        )
        add_btn.click()
        time.sleep(2)

        # JS: 提取完整 el-dialog
        result = driver.execute_script("""
        // 1. 找可见的完整 el-dialog 容器(不是子元素 footer/header)
        var dialogs = document.querySelectorAll(
            '.el-dialog:not([style*="display: none"]):not([style*="display:none"])'
        );
        var dlg = null;
        for (var i = 0; i < dialogs.length; i++) {
            if (dialogs[i].tagName === 'DIV' && dialogs[i].offsetParent !== null) {
                dlg = dialogs[i];
                break;
            }
        }
        // 兜底
        if (!dlg) {
            var overlays = document.querySelectorAll(
                '.el-overlay:not([style*="display: none"]) .el-dialog'
            );
            for (var j = 0; j < overlays.length; j++) {
                if (overlays[j].offsetParent !== null) {
                    dlg = overlays[j];
                    break;
                }
            }
        }

        // 2. 提取表单字段 (el-form-item)
        var fields = [];
        var formItems = dlg ? dlg.querySelectorAll('.el-form-item') : [];
        formItems.forEach(function(item, idx) {
            var label = item.querySelector('.el-form-item__label');
            var input = item.querySelector('input, textarea, select');
            var labelText = label ? label.innerText.trim() : '';
            fields.push({
                index: idx,
                label: labelText,
                input_tag: input ? input.tagName : 'NONE',
                input_type: input ? (input.type || '') : '',
                input_placeholder: input ? (input.placeholder || '') : '',
                input_class: input ? (input.className || '') : '',
                el_form_item_class: item.className || '',
                el_form_item_required: item.className.indexOf('is-required') >= 0
            });
        });

        // 3. 提取 dialog 标题
        var header = dlg ? dlg.querySelector('.el-dialog__header') : null;
        var title = header ? header.innerText.trim() : '';

        // 4. 提取所有按钮
        var buttons = dlg ? Array.from(dlg.querySelectorAll('button')).map(function(b) {
            return { text: b.innerText.trim(), class: b.className };
        }) : [];

        return { title: title, fields: fields, buttons: buttons,
                 dlg_class: dlg ? dlg.className : 'N/A',
                 dlg_html: dlg ? dlg.outerHTML.substring(0, 8000) : 'NO_DIALOG' };
        """)

        save("el_dialog_full_fields", result.get("fields", []))
        save("el_dialog_full_meta", {
            "title": result.get("title", ""),
            "dlg_class": result.get("dlg_class", ""),
            "buttons": result.get("buttons", []),
            "field_count": len(result.get("fields", []))
        })
        save("el_dialog_full_html", result.get("dlg_html", ""))

        # 打印摘要
        log.info("标题: %s", result.get("title"))
        log.info("字段数: %d", len(result.get("fields", [])))
        for f in result.get("fields", []):
            log.info("  [%s] %s (%s) placeholder=%s required=%s",
                     "✓" if f.get("input_tag") != "NONE" else "✗",
                     f.get("label"), f.get("input_type"),
                     f.get("input_placeholder"), f.get("el_form_item_required"))

    finally:
        base.close_browser()


if __name__ == "__main__":
    main()
