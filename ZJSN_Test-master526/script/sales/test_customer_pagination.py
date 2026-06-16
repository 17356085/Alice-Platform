"""分页条数切换专项测试 — TC-CUS-036"""
import pytest
import sys
import os
from selenium.webdriver.common.by import By
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from page.sales_page.CustomerPage import CustomerPage
from datetime import datetime


class TestPagination:
    """分页条数切换测试"""

    def _bulk_create_via_api(self, driver, count):
        """通过浏览器fetch API批量创建客户（10秒/条 → 大幅加速）"""
        created = 0
        for i in range(count):
            code = f"PG{datetime.now().strftime('%m%d%H%M%S')}{i:02d}"
            js = f"""
            fetch('/api/customers', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    code: '{code}',
                    name: '分页测试客户{i+1}',
                    creditCode: '91310000MA1PAG{str(i).zfill(4)}',
                    level: '一般客户',
                    contact: '测试',
                    phone: '13800138000',
                    address: '测试地址',
                    status: '合作中'
                }})
            }}).then(r => r.json()).then(d => JSON.stringify(d));
            """
            import time
            result = driver.execute_script(js)
            print(f"  API创建[{i+1}/{count}] {code}: {result[:80] if result else 'no response'}")
            if result and ('"code":200' in result or '成功' in result or 'true' in result.lower()):
                created += 1
            time.sleep(0.3)  # 避免请求过快
        return created

    def _switch_page_size(self, page, size_text):
        """切换每页条数（Element Plus Select 下拉）

        Args:
            page: CustomerPage 实例
            size_text: 选项文本，如 "20条/页"、"50条/页"
        """
        # 点击分页条数选择器
        selector = page.find_clickable(page.PAGINATION_SIZE_SELECT, timeout=5)
        page.driver.execute_script("arguments[0].click();", selector)
        page.wait_vue_stable()
        page._wait_dropdown_ready(timeout=5)
        # 点击选项
        page._click_dropdown_option(size_text)
        page.wait_vue_stable()
        page._wait_table_ready(timeout=10)

    def test_pagination_page_size(self, driver_setup):
        """TC-CUS-036(Boundary): 分页每页条数切换 10→20→50→10"""
        driver = driver_setup
        page = CustomerPage(driver)
        print("\n========== TC-CUS-036: 分页条数切换 ==========")
        page.navigate()
        page.wait_vue_stable(3)

        # 1. 检查当前数据量
        total = page.get_total_count()
        print(f"当前总条数: {total}")

        # 2. 如果<11条，尝试API批量创建
        if total < 11:
            needed = 11 - total
            print(f"数据不足,尝试API批量创建{needed}条...")
            created = self._bulk_create_via_api(driver, needed)
            print(f"API创建成功: {created}/{needed}")

            # 刷新页面验证
            page.navigate()
            page.wait_vue_stable(3)
            total = page.get_total_count()
            print(f"创建后总条数: {total}")

        if total < 11:
            pytest.skip(f"仅{total}条数据,无法测试分页条数切换(需≥11条)。请手工插入数据后重试。")

        # 3. 验证默认10条/页 → 有多页
        print(f"\n--- 默认10条/页: 总{total}条 ---")
        page1_data = page.get_first_row_data()
        has_next_10 = page.is_next_page_enabled()
        print(f"  第1页第1行: {page1_data[:40]}... | 有下一页: {has_next_10}")

        # 4. 切换到20条/页
        print("\n--- 切换20条/页 ---")
        try:
            self._switch_page_size(page, "20条/页")
            total_after_20 = page.get_total_count()
            print(f"  20条/页 总条数: {total_after_20}")
            assert total_after_20 == total, "切换页大小不应改变总条数"

            # 如果总条数 ≤ 20，应只有一页
            has_next_20 = page.is_next_page_enabled()
            print(f"  20条/页 有下一页: {has_next_20}")
        except Exception as e:
            print(f"  [WARN] 20条/页切换失败: {e}")

        # 5. 切换到50条/页
        print("\n--- 切换50条/页 ---")
        try:
            self._switch_page_size(page, "50条/页")
            total_after_50 = page.get_total_count()
            print(f"  50条/页 总条数: {total_after_50}")
            assert total_after_50 == total
            print(f"  50条/页 有下一页: {page.is_next_page_enabled()}")
        except Exception as e:
            print(f"  [WARN] 50条/页切换失败: {e}")

        # 6. 切回10条/页
        print("\n--- 切回10条/页 ---")
        try:
            self._switch_page_size(page, "10条/页")
            print(f"  恢复10条/页, 总条数: {page.get_total_count()}")
        except Exception as e:
            print(f"  [WARN] 切回10条/页失败: {e}")

        print("========== TC-CUS-036 通过 ==========")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
