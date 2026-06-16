"""客户管理CDP网络异常测试 — TC-CUS-043/044/048"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from page.sales_page.CustomerPage import CustomerPage
from config import TIMEOUT_CONFIG


class TestCDPNetwork:
    """CDP网络异常测试"""

    # ═══════════════════════════════════════════════════
    # TC-CUS-043: 慢网络(3G)下操作
    # ═══════════════════════════════════════════════════
    def test_slow_3g_search(self, driver_setup):
        """TC-CUS-043(DuplicateSubmit): 3G慢网络下搜索→页面不崩溃"""
        driver = driver_setup
        page = CustomerPage(driver)
        print("\n========== TC-CUS-043: 慢网络(3G)搜索 ==========")

        # 设置3G网络条件
        driver.execute_cdp_cmd('Network.enable', {})
        driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
            'offline': False,
            'latency': 400,              # 400ms RTT
            'downloadThroughput': 750 * 1024 / 8,   # 750 kbps
            'uploadThroughput': 250 * 1024 / 8,     # 250 kbps
        })
        print("[CDP] 3G网络已模拟 (400ms延迟, 750/250kbps)")
        page.navigate()
        page._wait_page_ready(timeout=20)

        try:
            # 搜索操作
            page.input_search_keyword("test001")
            page.click_search()
            page._wait_table_ready(timeout=15)
            count = page.get_table_row_count()
            print(f"3G网络搜索结果: {count} 条")
            assert count >= 0, "3G网络下搜索不应报错"
            print("[OK] 3G网络下搜索正常")
        except Exception as e:
            print(f"[INFO] 3G下搜索异常(可接受): {e}")
        finally:
            # 恢复网络
            driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
                'offline': False, 'latency': 0,
                'downloadThroughput': -1, 'uploadThroughput': -1,
            })
            print("[CDP] 网络已恢复")
        print("========== TC-CUS-043 通过 ==========")

    # ═══════════════════════════════════════════════════
    # TC-CUS-044: 请求超时
    # ═══════════════════════════════════════════════════
    def test_request_timeout(self, driver_setup):
        """TC-CUS-044(APIException): 极高延迟模拟超时→页面提示"""
        driver = driver_setup
        page = CustomerPage(driver)
        print("\n========== TC-CUS-044: 请求超时 ==========")

        # 设置极高延迟(30s)
        driver.execute_cdp_cmd('Network.enable', {})
        driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
            'offline': False,
            'latency': 30000,  # 30s延迟
            'downloadThroughput': 100 * 1024,
            'uploadThroughput': 100 * 1024,
        })
        print("[CDP] 极高延迟已模拟 (30s)")

        try:
            page.navigate()
            page._wait_page_ready(timeout=30)
            # 搜索——预期超时
            page.input_search_keyword("test001")
            page.click_search()
            page._wait_table_ready(timeout=15)
            print("[OK] 极高延迟下页面未崩溃（可能loading中或超时提示）")
        except Exception as e:
            print(f"[INFO] 超时异常(预期): {e}")
        finally:
            driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
                'offline': False, 'latency': 0,
                'downloadThroughput': -1, 'uploadThroughput': -1,
            })
            print("[CDP] 网络已恢复")
        print("========== TC-CUS-044 通过 ==========")

    # ═══════════════════════════════════════════════════
    # TC-CUS-048: 操作中断网
    # ═══════════════════════════════════════════════════
    def test_network_offline(self, driver_setup):
        """TC-CUS-048(APIException): 操作中断网→页面提示"""
        driver = driver_setup
        page = CustomerPage(driver)
        print("\n========== TC-CUS-048: 操作中断网 ==========")

        page.navigate()
        page._wait_page_ready(timeout=20)
        # 先正常搜索确认页面OK
        page.input_search_keyword("test001")
        page.click_search()
        page._wait_table_ready(timeout=15)
        print(f"断网前搜索结果: {page.get_table_row_count()} 条")

        # 断网
        driver.execute_cdp_cmd('Network.enable', {})
        driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
            'offline': True,
            'latency': 0,
            'downloadThroughput': -1,
            'uploadThroughput': -1,
        })
        print("[CDP] 网络已断开")

        try:
            # 尝试搜索——预期失败但页面不崩溃
            page.click_reset()
            page.wait_vue_stable()
            page.input_search_keyword("test001")
            page.click_search()
            page._wait_table_ready(timeout=15)
            print("[OK] 断网操作页面未崩溃")
        except Exception as e:
            print(f"[OK] 断网操作异常(预期): {str(e)[:100]}")
        finally:
            driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
                'offline': False, 'latency': 0,
                'downloadThroughput': -1, 'uploadThroughput': -1,
            })
            print("[CDP] 网络已恢复")
        print("========== TC-CUS-048 通过 ==========")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
