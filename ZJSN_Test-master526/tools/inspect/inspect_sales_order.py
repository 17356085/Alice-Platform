"""检查销售订单页面实际 HTML 结构 — 用于验证分析报告中的假设

运行方式：
    cd ZJSN_Test-master526
    python tools/inspect/inspect_sales_order.py

输出：
    - 表头列名列表
    - 每个列的 HTML 片段
    - 按钮文本
    - 搜索区输入框信息
    - 分页区结构
    - 截图 + HTML 源码保存到 artifacts/ 目录
"""
import logging
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium.webdriver.common.by import By
from base.browser_driver import BaseDriver, ensure_logged_in

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts", "inspections")


def safe_text(el):
    """安全获取元素文本"""
    try:
        return (el.text or el.get_attribute("textContent") or "").strip()
    except Exception:
        return ""


def inspect():
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("=== 启动浏览器 ===")
    base = BaseDriver()
    driver = base.open_browser()

    try:
        logger.info("=== 登录系统 ===")
        ensure_logged_in(driver)

        # ================================================================
        # 导航到销售订单页面
        # ================================================================
        logger.info("=== 导航到销售订单页面 ===")
        from base.sidebar_navigator import SidebarNavigator
        nav = SidebarNavigator(driver)
        nav.navigate_to("销售管理", "销售订单")
        time.sleep(3)  # 等待 Vue 渲染

        # 保存截图
        screenshot_path = os.path.join(ARTIFACTS_DIR, f"sales_order_{timestamp}.png")
        driver.save_screenshot(screenshot_path)
        logger.info("截图已保存: %s", screenshot_path)

        # 保存完整 HTML
        html_path = os.path.join(ARTIFACTS_DIR, f"sales_order_{timestamp}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info("HTML 源码已保存: %s", html_path)

        print("\n" + "=" * 80)
        print("                    📋 销售订单页面 — 实际结构检查")
        print("=" * 80)

        # ================================================================
        # 1. 当前 URL
        # ================================================================
        print(f"\n▶ 当前 URL: {driver.current_url}")

        # ================================================================
        # 2. 搜索区 — 输入框
        # ================================================================
        print("\n" + "-" * 60)
        print("  【搜索区 — 输入框】")
        print("-" * 60)

        # 查找所有 input
        all_inputs = driver.find_elements(By.CSS_SELECTOR, 'input:not([type="hidden"])')
        print(f"  页面可见 input 数量: {len([i for i in all_inputs if i.is_displayed()])}")
        for inp in all_inputs:
            try:
                if inp.is_displayed():
                    placeholder = inp.get_attribute("placeholder") or ""
                    input_type = inp.get_attribute("type") or "text"
                    css_class = inp.get_attribute("class") or ""
                    print(f"    input[type={input_type}] placeholder=\"{placeholder}\" class=\"{css_class[:60]}\"")
            except Exception:
                pass

        # ================================================================
        # 3. 搜索区 — el-select 下拉框
        # ================================================================
        print("\n" + "-" * 60)
        print("  【搜索区 — el-select 下拉框】")
        print("-" * 60)

        selects = driver.find_elements(By.CSS_SELECTOR, '.el-select')
        print(f"  页面 el-select 数量: {len(selects)}")
        for i, sel in enumerate(selects):
            try:
                if sel.is_displayed():
                    placeholder_span = sel.find_elements(By.CSS_SELECTOR, '.el-select__placeholder')
                    placeholder = placeholder_span[0].text if placeholder_span else ""
                    selected_span = sel.find_elements(By.CSS_SELECTOR, '.el-select__selected-item')
                    selected = selected_span[0].text if selected_span else ""
                    print(f"    [{i}] placeholder=\"{placeholder}\" selected=\"{selected}\"")
            except Exception as e:
                print(f"    [{i}] (获取信息失败: {e})")

        # ================================================================
        # 4. 搜索区 — 按钮
        # ================================================================
        print("\n" + "-" * 60)
        print("  【搜索区 — 按钮】")
        print("-" * 60)

        # 搜索表单区域内的所有按钮
        # 尝试多种可能的父容器
        buttons = driver.find_elements(By.CSS_SELECTOR, 'button.el-button')
        print(f"  页面 el-button 数量: {len(buttons)}")
        for i, btn in enumerate(buttons):
            try:
                if btn.is_displayed():
                    btn_text = safe_text(btn)
                    btn_class = btn.get_attribute("class") or ""
                    is_primary = "el-button--primary" in btn_class
                    print(f"    [{i}] \"{btn_text}\" primary={is_primary} class=\"{btn_class[:80]}\"")
            except Exception:
                pass

        # ================================================================
        # 5. 表格 — 表头
        # ================================================================
        print("\n" + "-" * 60)
        print("  【表格 — 表头列名】")
        print("-" * 60)

        # 方式1: .el-table__header-wrapper th .cell
        header_cells = driver.find_elements(By.CSS_SELECTOR, '.el-table__header-wrapper th .cell')
        if not header_cells:
            header_cells = driver.find_elements(By.CSS_SELECTOR, 'thead th .cell')
        if not header_cells:
            header_cells = driver.find_elements(By.CSS_SELECTOR, 'thead th')

        print(f"  表头列数: {len(header_cells)}")
        for i, cell in enumerate(header_cells, 1):
            text = safe_text(cell)
            print(f"    列 {i}: \"{text}\"")

        # ================================================================
        # 6. 表格 — 第一行数据（含 HTML 片段）
        # ================================================================
        print("\n" + "-" * 60)
        print("  【表格 — 第一行数据】")
        print("-" * 60)

        rows = driver.find_elements(By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')
        if not rows:
            rows = driver.find_elements(By.CSS_SELECTOR, 'tbody tr.el-table__row')
        if not rows:
            rows = driver.find_elements(By.CSS_SELECTOR, 'tbody tr')

        print(f"  可见数据行数: {len(rows)}")

        if rows:
            first_row = rows[0]
            cells = first_row.find_elements(By.TAG_NAME, 'td')
            print(f"  第一行列数: {len(cells)}")
            for i, cell in enumerate(cells, 1):
                # 获取行内 HTML 片段，重点关注 el-tag、button 等组件
                inner_html = cell.get_attribute("innerHTML") or ""
                # 截取前 200 字符
                snippet = inner_html[:200].replace("\n", " ")
                text = safe_text(cell)
                print(f"    列 {i}: text=\"{text[:50]}\"")
                if 'el-tag' in inner_html:
                    # 详细分析 Tag
                    tags = cell.find_elements(By.CSS_SELECTOR, 'span.el-tag')
                    for tag in tags:
                        tag_class = tag.get_attribute("class") or ""
                        tag_text = safe_text(tag)
                        print(f"           → el-tag: \"{tag_text}\" class=\"{tag_class}\"")
                if 'el-button' in inner_html:
                    btns = cell.find_elements(By.CSS_SELECTOR, 'button.el-button')
                    for b in btns:
                        b_text = safe_text(b)
                        b_class = b.get_attribute("class") or ""
                        print(f"           → el-button: \"{b_text}\" class=\"{b_class}\"")

        # ================================================================
        # 7. 分页区
        # ================================================================
        print("\n" + "-" * 60)
        print("  【分页区】")
        print("-" * 60)

        pagination = driver.find_elements(By.CSS_SELECTOR, '.el-pagination')
        if pagination:
            pag_text = safe_text(pagination[0])
            print(f"  分页区文本: \"{pag_text}\"")

            # 总条数
            total_el = driver.find_elements(By.CSS_SELECTOR, '.el-pagination__total')
            if total_el:
                print(f"  总条数: \"{safe_text(total_el[0])}\"")

            # 每页条数 select
            size_selects = driver.find_elements(By.CSS_SELECTOR, '.el-pagination .el-select')
            print(f"  每页条数 Select 数量: {len(size_selects)}")

            # 翻页按钮
            prev_btn = driver.find_elements(By.CSS_SELECTOR, '.el-pagination button.btn-prev')
            next_btn = driver.find_elements(By.CSS_SELECTOR, '.el-pagination button.btn-next')
            prev_disabled = prev_btn[0].get_attribute("disabled") if prev_btn else "N/A"
            next_disabled = next_btn[0].get_attribute("disabled") if next_btn else "N/A"
            print(f"  上一页 disabled={prev_disabled}")
            print(f"  下一页 disabled={next_disabled}")

            # 页码
            page_numbers = driver.find_elements(By.CSS_SELECTOR, '.el-pagination .el-pager li')
            print(f"  页码按钮: {[safe_text(p) for p in page_numbers]}")

        # ================================================================
        # 8. 搜索区容器 class
        # ================================================================
        print("\n" + "-" * 60)
        print("  【搜索区容器结构】")
        print("-" * 60)

        # 推测搜索区的外层容器
        container_patterns = [
            '.search-wrapper', '.search-form', '.el-form',
            '.filter-container', '.search-container',
            '.table-search', '.page-search',
        ]
        for pattern in container_patterns:
            containers = driver.find_elements(By.CSS_SELECTOR, pattern)
            if containers:
                for c in containers[:2]:
                    c_class = c.get_attribute("class") or ""
                    try:
                        c_displayed = c.is_displayed()
                    except Exception:
                        c_displayed = False
                    if c_displayed:
                        print(f"  {pattern}: class=\"{c_class[:100]}\"")
                        # 列出子元素标签
                        children = c.find_elements(By.XPATH, './*')
                        child_tags = [(ch.tag_name, ch.get_attribute("class") or "") for ch in children[:20]]
                        for tag, cls in child_tags:
                            print(f"    └─ <{tag}> class=\"{cls[:80]}\"")
                        break

        # ================================================================
        # 9. 结论摘要
        # ================================================================
        print("\n" + "=" * 80)
        print("                    结论摘要（用于修正 PageObject）")
        print("=" * 80)
        print(f"  表头列数: {len(header_cells)}")
        print(f"  表头: {[safe_text(c) for c in header_cells]}")
        print(f"  数据行第一行列数: {len(rows[0].find_elements(By.TAG_NAME, 'td')) if rows else 0}")

        btn_texts = []
        for b in buttons:
            try:
                if b.is_displayed():
                    btn_texts.append(safe_text(b))
            except Exception:
                pass
        print(f"  页面可见按钮文本: {btn_texts}")

        print("\n" + "=" * 80)
        logger.info("检查完成！")
        logger.info("截图: %s", screenshot_path)
        logger.info("HTML: %s", html_path)

    finally:
        logger.info("=== 关闭浏览器 ===")
        base.close_browser()


if __name__ == "__main__":
    inspect()
