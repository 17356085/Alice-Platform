"""演示模式视觉增强 — 元素高亮、动效闪烁、终端美化

使用方式：
    from base.demo_effects import inject_demo_effects, demo_banner
    inject_demo_effects(driver)  # 注入后所有交互自动带高亮动效
"""

import logging
import sys
import time

logger = logging.getLogger(__name__)

# ── 效果配置 ──────────────────────────────────────────────────────
DEMO_CONFIG = {
    "highlight_color": "#ff6a00",       # 高亮颜色（橙色）
    "highlight_width": "3px",
    "highlight_glow": "0 0 16px #ff6a00, 0 0 32px rgba(255,106,0,0.4)",
    "flash_duration_ms": 200,           # 高亮持续毫秒
    "click_delay": 0.25,                # 点击后额外停顿
    "type_delay": 0.03,                 # 逐字输入间隔
    "show_badge": True,                 # 显示操作标签
}


def _safe_print(text: str) -> None:
    """安全打印，自动处理 GBK 无法编码的字符（Windows 终端兼容）"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 替换无法编码的字符为 ?
        encoded = text.encode(sys.stdout.encoding or 'gbk', errors='replace')
        print(encoded.decode(sys.stdout.encoding or 'gbk', errors='replace'))


def inject_demo_effects(driver) -> None:
    """注入全局交互视觉效果（JavaScript 层拦截 click / input 事件）

    效果：
      - 点击前：元素橙色辉光闪烁 350ms
      - 输入时：光标处蓝色脉冲
      - 右上角浮动操作标签
    """
    js = """
    (function() {
        if (window.__demoEffectsInjected) return;
        window.__demoEffectsInjected = true;

        const COLOR = '""" + DEMO_CONFIG["highlight_color"] + """';
        const GLOW = '""" + DEMO_CONFIG["highlight_glow"] + """';
        const FLASH_MS = """ + str(DEMO_CONFIG["flash_duration_ms"]) + """;

        // 创建浮动标签
        const badge = document.createElement('div');
        badge.id = '__demo_badge__';
        badge.style.cssText = `
            position: fixed; top: 12px; right: 16px; z-index: 99999;
            background: linear-gradient(135deg, #ff6a00, #ee0979);
            color: #fff; padding: 8px 18px; border-radius: 20px;
            font-family: 'Segoe UI', system-ui, sans-serif;
            font-size: 13px; font-weight: 700;
            letter-spacing: 0.5px;
            box-shadow: 0 4px 20px rgba(255,106,0,0.5);
            pointer-events: none; opacity: 0;
            transition: opacity 0.3s ease, transform 0.3s ease;
            transform: translateY(-8px);
        `;
        document.body.appendChild(badge);

        function showBadge(text) {
            badge.textContent = '[DEMO] ' + text;
            badge.style.opacity = '1';
            badge.style.transform = 'translateY(0)';
            clearTimeout(badge._timer);
            badge._timer = setTimeout(() => {
                badge.style.opacity = '0';
                badge.style.transform = 'translateY(-8px)';
            }, 1200);
        }

        function flashElement(el) {
            if (!el || el === document.body || el === document.documentElement) return;
            const origOutline = el.style.outline;
            const origOutlineOffset = el.style.outlineOffset;
            const origBoxShadow = el.style.boxShadow;
            const origTransition = el.style.transition;

            el.style.transition = 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)';
            el.style.outline = '3px solid ' + COLOR;
            el.style.outlineOffset = '3px';
            el.style.boxShadow = GLOW;

            setTimeout(function() {
                el.style.outline = origOutline;
                el.style.outlineOffset = origOutlineOffset;
                el.style.boxShadow = origBoxShadow;
                setTimeout(function() { el.style.transition = origTransition; }, 150);
            }, FLASH_MS);
        }

        // 拦截 click 事件（捕获阶段，比业务逻辑先触发）
        document.addEventListener('click', function(e) {
            flashElement(e.target);
            var tag = (e.target.tagName || '').toLowerCase();
            var label = e.target.getAttribute('placeholder') ||
                        (e.target.textContent || '').trim().slice(0, 20) ||
                        (tag + (e.target.className ? '.' + e.target.className.split(' ')[0] : ''));
            showBadge('Click: ' + label);
        }, true);

        // 拦截 input 事件
        document.addEventListener('input', function(e) {
            flashElement(e.target);
            showBadge('Typing...');
        }, true);

        // 拦截 change 事件
        document.addEventListener('change', function(e) {
            flashElement(e.target);
            if (e.target.tagName === 'SELECT' || e.target.type === 'checkbox' || e.target.type === 'radio') {
                showBadge('Changed');
            }
        }, true);

        // 拦截 focus 事件（输入框聚焦微微高亮）
        document.addEventListener('focus', function(e) {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
                e.target.style.transition = 'box-shadow 0.2s ease';
                e.target.style.boxShadow = '0 0 0 2px rgba(255,106,0,0.3)';
            }
        }, true);

        document.addEventListener('blur', function(e) {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
                e.target.style.boxShadow = '';
            }
        }, true);

        console.log('%c[DEMO] Visual effects activated %c| Highlight + Flash + Badge',
            'color:#ff6a00;font-size:14px;font-weight:bold;',
            'color:#888;');
    })();
    """
    try:
        driver.execute_script(js)
        logger.info("[DEMO] Visual effects injected into browser")
    except Exception as e:
        logger.warning("Demo effects injection failed (non-critical): %s", e)


def demo_banner(text: str, width: int = 72) -> None:
    """打印醒目的终端横幅（GBK 安全）"""
    _safe_print("")
    _safe_print("+" + "=" * (width - 2) + "+")
    for line in text.split("\n"):
        line = line.strip()
        _safe_print("|" + line.center(width - 2) + "|")
    _safe_print("+" + "=" * (width - 2) + "+")
    _safe_print("")
