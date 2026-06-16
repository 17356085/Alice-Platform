"""Tank 模块 DOM 捕获 — 一次性脚本

流程:
  1. 启动浏览器 → admin 登录
  2. 导航到 tank monitor → 点"新增储罐" → JS 提取弹窗 HTML + 表单字段
  3. 关闭弹窗 → 点"导入" → 提取导入弹窗 HTML
  4. 点"导出" → 等下载文件 (确认导出成功)
  5. 导航到 tank report → 提取 chart DOM

输出:
  artifacts/dom_capture/
    tank_add_dialog.html       — 新增弹窗完整 HTML
    tank_add_dialog_fields.json — 表单字段结构化 metadata
    tank_import_dialog.html    — 导入弹窗 HTML
    tank_toast.html            — toast/消息提示 HTML (如有)
    tank_report_chart.html     — 日报表趋势图区域 HTML
"""
import json
import logging
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base.browser_driver import BaseDriver, ensure_logged_in

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("capture-tank-dom")

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ZJSN_Test-master526/
OUTPUT_DIR = os.path.join(_BASE, "artifacts", "dom_capture")
TS = datetime.now().strftime("%Y%m%d_%H%M%S")


def save_file(name, content):
    path = os.path.join(OUTPUT_DIR, f"{name}_{TS}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if isinstance(content, (dict, list)):
        path += ".json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
    else:
        path += ".html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(content))
    logger.info("  -> saved: %s", os.path.basename(path))
    return path


def js_extract_visible_dialog(driver):
    """JS: 提取当前可见弹窗的 outerHTML + 表单字段 metadata"""
    result = driver.execute_script("""
    function getVisibleDialog() {
        // 按优先级匹配: 1) 自定义 dialog class (非 el- 前缀的)  2) el-dialog  3) 任意对话框容器
        var selectors = [
            '[class*="dialog"]:not([style*="display: none"])',
            '[class*="Dialog"]:not([style*="display: none"])',
            '.el-dialog:not([style*="display: none"])',
            '.el-overlay:not([style*="display: none"]) .el-dialog'
        ];
        for (var i = 0; i < selectors.length; i++) {
            var els = document.querySelectorAll(selectors[i]);
            for (var j = els.length - 1; j >= 0; j--) {
                if (els[j].offsetParent !== null) {
                    return els[j];
                }
            }
        }
        // 兜底: 找所有 dialog 容器中最后一个可见的
        var allDialogs = document.querySelectorAll(
            '[class*="dialog"], [class*="Dialog"], [class*="modal"], [class*="Modal"]'
        );
        for (var k = allDialogs.length - 1; k >= 0; k--) {
            if (allDialogs[k].offsetParent !== null) {
                return allDialogs[k];
            }
        }
        return null;
    }

    function extractFields(dialog) {
        if (!dialog) return [];
        var fields = [];
        // 找所有 input / select / textarea
        var inputs = dialog.querySelectorAll('input, select, textarea');
        inputs.forEach(function(el, idx) {
            var field = {
                index: idx,
                tag: el.tagName.toLowerCase(),
                type: el.type || '',
                name: el.name || '',
                placeholder: el.placeholder || '',
                class: el.className || '',
                id: el.id || ''
            };
            // 尝试找关联 label
            if (el.id) {
                var labelEl = dialog.querySelector('label[for="' + el.id + '"]');
                if (labelEl) field.label = labelEl.innerText.trim();
            }
            if (!field.label) {
                // 从父级容器找 label
                var parent = el.closest(
                    '.form-item, .el-form-item, .field-item, [class*="form-row"], ' +
                    'div[class*="form"], td, .form-group'
                );
                if (parent) {
                    var lbl = parent.querySelector('label, .label, .field-label, ' +
                        '[class*="label"], span:first-child');
                    if (lbl) field.label = lbl.innerText.trim();
                }
            }
            fields.push(field);
        });
        return fields;
    }

    function extractButtons(dialog) {
        if (!dialog) return [];
        var btns = dialog.querySelectorAll('button');
        return Array.from(btns).slice(0, 10).map(function(b) {
            return {
                text: b.innerText.trim().substring(0, 30),
                class: b.className || '',
                type: b.type || ''
            };
        });
    }

    var dialog = getVisibleDialog();
    var html = dialog ? dialog.outerHTML : 'NO_VISIBLE_DIALOG';
    return {
        html: html,
        tagName: dialog ? dialog.tagName : 'N/A',
        className: dialog ? dialog.className : 'N/A',
        fields: extractFields(dialog),
        buttons: extractButtons(dialog)
    };
    """)
    return result


def js_extract_toast(driver):
    """JS: 提取可见的 toast/消息提示 HTML"""
    return driver.execute_script("""
    var selectors = [
        '.el-message:not([style*="display: none"])',
        '.el-message__content',
        '.toast:not([style*="display: none"])',
        '[class*="toast"]:not([style*="display: none"])',
        '[class*="message"]:not([style*="display: none"])',
        '.el-notification:not([style*="display: none"])',
        '.ant-message-notice-content'
    ];
    for (var i = 0; i < selectors.length; i++) {
        var els = document.querySelectorAll(selectors[i]);
        for (var j = 0; j < els.length; j++) {
            if (els[j].offsetParent !== null || els[j].innerText.trim()) {
                return {
                    html: els[j].outerHTML,
                    text: els[j].innerText.trim(),
                    className: els[j].className
                };
            }
        }
    }
    return { html: 'NO_TOAST_FOUND', text: '', className: '' };
    """)


def js_extract_chart_area(driver):
    """JS: 提取图表区域 DOM"""
    return driver.execute_script("""
    var selectors = [
        '.chart-section', '.chart-container', '[class*="chart"]',
        '[class*="trend"]', '.stats-section', '.stat-cards'
    ];
    var result = {};
    selectors.forEach(function(sel) {
        var els = document.querySelectorAll(sel);
        if (els.length > 0) {
            result[sel] = {
                count: els.length,
                html: Array.from(els).slice(0, 3).map(function(e) {
                    return e.outerHTML.substring(0, 2000);
                }).join('\\n---\\n')
            };
        }
    });
    if (Object.keys(result).length === 0) {
        // 兜底: 取 body 中可能包含图表的区域
        var body = document.body.innerText;
        result['body_preview'] = body.substring(0, 500);
    }
    return result;
    """)


def main():
    logger.info("=== Tank DOM Capture ===")
    logger.info("Output: %s", OUTPUT_DIR)

    base = BaseDriver()
    driver = base.open_browser()

    try:
        # ── 1. 登录 ──
        logger.info("Step 1: 登录...")
        ensure_logged_in(driver)

        # ── 2. Monitor: 新增弹窗 ──
        logger.info("Step 2: 导航到储罐监控管理...")
        driver.get("https://aiwechatminidemo.cimc-digital.com/#/tank/monitor")
        time.sleep(3)

        # 等待页面加载
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.data-table, .stats-cards"))
            )
            logger.info("  页面已加载")
        except Exception:
            logger.warning("  页面可能未完全加载")

        # 点击"新增储罐"
        logger.info("Step 3: 点击新增储罐...")
        from selenium.webdriver.common.by import By
        try:
            add_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"新增储罐")]'))
            )
            add_btn.click()
            time.sleep(2)
        except Exception as e:
            logger.error("  找不到'新增储罐'按钮: %s", e)
            save_file("tank_page_source", driver.page_source)

        # 提取弹窗 DOM
        logger.info("Step 4: 提取新增弹窗 DOM...")
        dialog_data = js_extract_visible_dialog(driver)
        save_file("tank_add_dialog", dialog_data["html"])
        save_file("tank_add_dialog_fields", {
            "tagName": dialog_data["tagName"],
            "className": dialog_data["className"],
            "fields": dialog_data["fields"],
            "buttons": dialog_data["buttons"]
        })

        # ── 3. 关闭弹窗 ──
        logger.info("Step 5: 关闭弹窗...")
        try:
            close_btns = driver.find_elements(By.XPATH, '//button[contains(.,"取消") or contains(.,"关闭")]')
            for b in close_btns:
                if b.is_displayed():
                    driver.execute_script("arguments[0].click();", b)
                    break
            time.sleep(1)
        except Exception:
            pass

        # ── 4. 导入弹窗 ──
        logger.info("Step 6: 点击导入...")
        try:
            import_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"导入")]'))
            )
            import_btn.click()
            time.sleep(2)
        except Exception as e:
            logger.error("  找不到'导入'按钮: %s", e)

        import_data = js_extract_visible_dialog(driver)
        save_file("tank_import_dialog", import_data["html"])
        save_file("tank_import_dialog_fields", {
            "tagName": import_data["tagName"],
            "className": import_data["className"],
            "fields": import_data["fields"],
            "buttons": import_data["buttons"]
        })

        # 关闭导入弹窗
        try:
            close_btns = driver.find_elements(By.XPATH, '//button[contains(.,"取消") or contains(.,"关闭")]')
            for b in close_btns:
                if b.is_displayed():
                    driver.execute_script("arguments[0].click();", b)
                    break
            time.sleep(1)
        except Exception:
            pass

        # ── 5. Toast 捕获 ──
        logger.info("Step 7: 触发 toast (搜索)...")
        try:
            search_input = driver.find_element(By.CSS_SELECTOR, "input.filter-input")
            search_input.clear()
            search_input.send_keys("TEST")
            search_btn = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary")
            search_btn.click()
            time.sleep(2)
        except Exception as e:
            logger.warning("  搜索触发失败: %s", e)

        toast_data = js_extract_toast(driver)
        save_file("tank_toast", toast_data)

        # ── 6. Report: 图表 DOM ──
        logger.info("Step 8: 导航到储罐日报表...")
        driver.get("https://aiwechatminidemo.cimc-digital.com/#/tank/report")
        time.sleep(5)

        chart_data = js_extract_chart_area(driver)
        save_file("tank_report_chart", json.dumps(chart_data, ensure_ascii=False, indent=2))

        # ── 7. 导出 ──
        logger.info("Step 9: 点击导出...")
        try:
            export_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"导出")]'))
            )
            export_btn.click()
            time.sleep(5)
            # 检查下载目录
            dl = getattr(driver, "download_dir", base.download_dir)
            if dl:
                files = [f for f in os.listdir(dl) if not f.endswith('.crdownload')]
                logger.info("  下载目录文件: %s", files)
        except Exception as e:
            logger.error("  导出失败: %s", e)

    finally:
        logger.info("清理: 关闭浏览器...")
        base.close_browser()

    logger.info("=== DOM Capture Complete ===")
    logger.info("检查输出: %s", OUTPUT_DIR)


if __name__ == "__main__":
    main()
