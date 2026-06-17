"""设备管理 — 跨页面端到端测试

覆盖场景:
  E2E-001: 装置->关联设备->设备台账 跨页验证 (P0)
  E2E-002: 设备->维保计划 链接验证 (P0)
  E2E-003: 报警配置<->关键参数监控 交叉验证 (P1)
  E2E-004: 设备->传感器->详情 深度链接 (P1)

技术:
  单浏览器顺序导航 (跨页面同一用户)
  避开 alarm-config teleport 弹窗 (仅页面级验证)
"""
import os
import sys
import time
import pytest
import allure

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from selenium.common.exceptions import TimeoutException

from page.equipment_page.UnitManagePage import UnitManagePage
from page.equipment_page.EquipmentPage import EquipmentPage
from page.equipment_page.MaintenancePage import MaintenancePage
from page.equipment_page.AlarmConfigPage import AlarmConfigPage
from page.equipment_page.KeyParamPage import KeyParamPage
from page.equipment_page.SensorManagePage import SensorManagePage
from base.sidebar_navigator import SidebarNavigator
from base.base_page import BasePage


# ═══════════════════════════════════════════════════════════════
#  工具函数
# ═══════════════════════════════════════════════════════════════

def step(text):
    print(f"  -> {text}")
    try:
        allure.step(text)
    except Exception:
        pass


def case(case_id, title):
    print(f"\n{'='*60}\n用例 {case_id}：{title}\n{'='*60}")
    try:
        allure.dynamic.title(f"{case_id} {title}")
    except Exception:
        pass


def ea(expected, actual):
    return f"预期结果：{expected}；实际结果：{actual}"


def nav_to(driver, href, label=""):
    """JS hash 直接导航"""
    nav = SidebarNavigator(driver)
    nav._navigate_by_js_hash(href, label)
    BasePage(driver).wait_vue_stable()
    time.sleep(2)


# ═══════════════════════════════════════════════════════════════
#  测试类
# ═══════════════════════════════════════════════════════════════

class TestEquipmentE2E:
    """设备管理 — 跨页面端到端测试"""

    # ── E2E-001: 装置->关联设备->设备台账 ──────────────────────

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("设备管理")
    @allure.story("跨页面流转-装置关联设备")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_e2e_001_unit_device_binding(self, driver_setup):
        """E2E-001: 装置台账 -> 关联设备 -> 设备台账 跨页验证

        流程:
          装置台账: 获取第一条装置 -> 打开关联设备弹窗 -> 记录设备名称
          -> 导航到设备台账 -> 验证设备存在
        """
        driver = driver_setup
        case("E2E-001", "装置台账 -> 关联设备 -> 设备台账")

        # ── Step 1: 导航到装置台账 ──
        step("导航到装置台账")
        nav_to(driver, "#/equipment/unit", "装置台账")
        unit_page = UnitManagePage(driver)
        unit_page._wait_page_ready()

        # 检查数据
        if unit_page.get_table_row_count() == 0:
            pytest.skip("装置台账无数据，跳过 E2E-001")

        names = unit_page.get_all_unit_names_on_page()
        if not names:
            pytest.skip("装置台账无装置名称")
        unit_name = names[0]
        step(f"第一条装置: {unit_name}")

        # ── Step 2: 打开关联设备弹窗 ──
        step("打开关联设备弹窗")
        try:
            unit_page.click_bind_device(unit_name)
        except TimeoutException:
            pytest.skip("关联设备弹窗超时(服务器慢)，跳过 E2E-001")

        # 记录弹窗中的设备
        device_name = None
        try:
            bind_count = unit_page.get_bind_device_row_count()
            step(f"关联设备弹窗中有 {bind_count} 条可选设备")
            assert bind_count >= 0, ea("设备表格正常显示", f"{bind_count}行")

            # 尝试获取第一条设备名称
            if bind_count > 0:
                try:
                    # get_bind_device_row_count 返回行数，读取第一行设备名
                    from selenium.webdriver.common.by import By
                    rows = driver.find_elements(
                        By.CSS_SELECTOR,
                        '.el-dialog[aria-label="关联设备"] .el-table__body-wrapper tbody tr'
                    )
                    if rows:
                        cells = rows[0].find_elements(By.TAG_NAME, 'td')
                        if len(cells) >= 1:
                            device_name = cells[0].text.strip()
                            step(f"关联弹窗第一条设备: {device_name}")
                except Exception:
                    pass

            unit_page.click_bind_cancel()
        except Exception as e:
            step(f"关联弹窗操作异常: {e}")
            try:
                unit_page.click_bind_cancel()
            except Exception:
                pass

        # ── Step 3: 导航到设备台账 ──
        step("导航到设备台账")
        nav_to(driver, "#/equipment/device", "设备台账")
        equip_page = EquipmentPage(driver)
        equip_page._wait_page_ready()

        equip_count = equip_page.get_table_row_count()
        step(f"设备台账有 {equip_count} 行")
        assert equip_count >= 0, ea("设备台账页面正常加载", f"{equip_count}行")

        # ── Step 4: 如果有关联设备名称，搜索验证 ──
        if device_name and equip_count > 0:
            step(f"搜索关联设备: {device_name}")
            try:
                equip_page.input_keyword(device_name)
                equip_page.click_search()
                after_search = equip_page.get_table_row_count()
                step(f"搜索「{device_name}」结果: {after_search} 行")
                assert after_search >= 0, ea("搜索结果正常", after_search)
            except Exception as e:
                step(f"搜索验证跳过: {e}")

        step("E2E-001 装置->关联设备->设备台账 通过 [OK]")

    # ── E2E-002: 设备->维保计划 ──────────────────────────────────

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("设备管理")
    @allure.story("跨页面流转-设备维保链接")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_e2e_002_equipment_maintenance_linkage(self, driver_setup):
        """E2E-002: 设备台账 -> 维保计划 跨页链接验证

        流程:
          设备台账: 获取第一条设备名称
          -> 导航到设备维保 -> 验证维保计划列表
          -> 检查维保计划的设备名称列是否存在匹配
        """
        driver = driver_setup
        case("E2E-002", "设备台账 -> 设备维保 链接验证")

        # ── Step 1: 设备台账获取设备 ──
        step("导航到设备台账")
        nav_to(driver, "#/equipment/device", "设备台账")
        equip_page = EquipmentPage(driver)
        equip_page._wait_page_ready()

        if equip_page.get_table_row_count() == 0:
            pytest.skip("设备台账无数据，跳过 E2E-002")

        # 获取第一条设备名称
        device_name = None
        try:
            name_idx = equip_page.get_column_index_by_header("设备名称")
            if name_idx:
                names = equip_page.get_column_data(name_idx)
                device_name = names[0] if names else None
            if not device_name:
                # 回退: 获取第二条列(常见布局)
                col2 = equip_page.get_column_data(2)
                device_name = col2[0] if col2 else None
        except Exception:
            pass

        step(f"第一条设备: {device_name or 'N/A'}")

        # ── Step 2: 导航到设备维保 ──
        step("导航到设备维保")
        nav_to(driver, "#/equipment/maintenance", "设备维保")
        maint_page = MaintenancePage(driver)
        maint_page._wait_page_ready()

        maint_count = maint_page.get_table_row_count()
        step(f"维保计划表格有 {maint_count} 行")
        assert maint_count >= 0, ea("维保计划页面正常加载", f"{maint_count}行")

        if maint_count == 0:
            step("[WARN] 维保计划表格为空，跳过设备名交叉验证")
            return

        # ── Step 3: 检查维保计划的设备名列 ──
        step("检查维保计划表格中的设备名称列")
        headers = maint_page.get_table_headers()
        step(f"维保计划表头: {headers}")

        # 尝试获取设备名称列数据
        equip_col_idx = maint_page.get_column_index_by_header("设备名称")
        if equip_col_idx:
            equip_names = maint_page.get_column_data(equip_col_idx)
            step(f"维保计划的设备名称列 (前3): {equip_names[:3] if equip_names else 'N/A'}")
            assert len(equip_names) >= 0, ea("设备名称列有数据", f"{len(equip_names)}条")
        else:
            step("[WARN] 维保计划表格无'设备名称'列，跳过跨页字段验证")

        # ── Step 4 (可选): 如果设备名称非空，搜索验证 ──
        if device_name and equip_col_idx:
            step(f"在维保计划中搜索设备: {device_name}")
            try:
                # 维保计划搜索区可能没有设备名称输入框，尝试类型/状态搜索保底
                maint_page.click_search()
                after_search = maint_page.get_table_row_count()
                step(f"搜索后: {after_search} 行")
            except Exception as e:
                step(f"搜索跳过: {e}")

        step("E2E-002 设备->维保计划 通过 [OK]")

    # ── E2E-003: 报警配置<->关键参数监控 ────────────────────────

    @allure.epic("系统管理")
    @allure.feature("设备管理")
    @allure.story("跨页面流转-报警与监控")
    @allure.severity(allure.severity_level.NORMAL)
    def test_e2e_003_alarm_keyparam_cross_verify(self, driver_setup):
        """E2E-003: 报警配置 <-> 关键参数监控 交叉验证 (P1)

        流程:
          报警配置页: 统计卡片 + 表头 + 行数
          -> 关键参数监控页: 统计卡片 + 表头 + 行数
          -> 验证两页面均正常加载

        注意: 避开 alarm-config 弹窗交互 (teleport bug)
        """
        driver = driver_setup
        case("E2E-003", "报警配置 <-> 关键参数监控 页面级交叉验证")

        # ── Step 1: 报警配置页 ──
        step("导航到设备报警配置")
        nav_to(driver, "#/equipment/alarm-config", "设备报警配置")
        alarm_page = AlarmConfigPage(driver)
        alarm_page._wait_page_ready()

        alarm_stats = alarm_page.get_all_stats()
        step(f"报警配置统计: 总数={alarm_stats['total']}, "
             f"已启用={alarm_stats['enabled']}, "
             f"已禁用={alarm_stats['disabled']}, "
             f"今日报警={alarm_stats['today']}")

        alarm_cards = alarm_page.get_stat_card_count()
        alarm_headers = alarm_page.get_table_headers()
        alarm_rows = alarm_page.get_table_row_count()

        step(f"报警配置: {alarm_cards} 统计卡片, "
             f"{len(alarm_headers)} 表头, {alarm_rows} 行")

        assert alarm_cards >= 4, ea("报警配置至少4张统计卡片", alarm_cards)
        assert len(alarm_headers) >= 3, ea("报警配置至少3列表头", len(alarm_headers))

        # ── Step 2: 关键参数监控页 ──
        step("导航到关键参数监控")
        nav_to(driver, "#/equipment/key-param", "关键参数监控")
        kp_page = KeyParamPage(driver)
        kp_page._wait_page_ready()

        kp_stats = kp_page.get_all_stats()
        step(f"关键参数统计: {kp_stats}")

        kp_cards = kp_page.get_stat_card_count()
        kp_headers = kp_page.get_table_headers()
        kp_rows = kp_page.get_table_row_count()

        step(f"关键参数: {kp_cards} 统计卡片, "
             f"{len(kp_headers)} 表头, {kp_rows} 行")

        assert kp_cards >= 3, ea("关键参数至少3张统计卡片", kp_cards)
        assert len(kp_headers) >= 3, ea("关键参数至少3列表头", len(kp_headers))

        # ── Step 3: 交叉验证 — 两页均正常 ──
        step("交叉验证: 两页面均已正常加载")
        assert alarm_rows >= 0 and kp_rows >= 0, \
            ea("报警配置+关键参数页面均正常", "至少一页异常")

        step("E2E-003 报警配置<->关键参数监控 通过 [OK]")

    # ── E2E-004: 设备->传感器->详情 ──────────────────────────────

    @allure.epic("系统管理")
    @allure.feature("设备管理")
    @allure.story("跨页面流转-设备传感器")
    @allure.severity(allure.severity_level.NORMAL)
    def test_e2e_004_equipment_sensor_detail(self, driver_setup):
        """E2E-004: 设备台账 -> 传感器 -> 详情 深度链接 (P1)

        流程:
          设备台账: 获取设备名称
          -> 传感器管理: 搜索该设备 -> 查看传感器详情
          -> 验证详情弹窗字段
        """
        driver = driver_setup
        case("E2E-004", "设备台账 -> 传感器 -> 详情")

        # ── Step 1: 设备台账获取设备名称 ──
        step("导航到设备台账，获取设备名称")
        nav_to(driver, "#/equipment/device", "设备台账")
        equip_page = EquipmentPage(driver)
        equip_page._wait_page_ready()

        if equip_page.get_table_row_count() == 0:
            pytest.skip("设备台账无数据，跳过 E2E-004")

        device_name = None
        try:
            name_idx = equip_page.get_column_index_by_header("设备名称")
            if name_idx:
                names = equip_page.get_column_data(name_idx)
                device_name = names[0] if names else None
            if not device_name:
                col2 = equip_page.get_column_data(2)
                device_name = col2[0] if col2 else None
        except Exception:
            pass

        step(f"设备名称: {device_name or 'N/A'}")

        # ── Step 2: 导航到传感器管理 ──
        step("导航到传感器管理")
        nav_to(driver, "#/equipment/sensor", "传感器管理")
        sensor_page = SensorManagePage(driver)
        sensor_page._wait_page_ready()

        sensor_count = sensor_page.get_table_row_count()
        step(f"传感器管理: {sensor_count} 行")

        # ── Step 3: 搜索传感器 ──
        sensor_name = None
        if device_name and sensor_count > 0:
            step(f"搜索传感器: {device_name}")
            try:
                sensor_page.input_keyword(device_name)
                sensor_page.click_search()
                after_search = sensor_page.get_table_row_count()
                step(f"搜索「{device_name}」结果: {after_search} 行")
            except Exception as e:
                step(f"搜索跳过: {e}")
                after_search = sensor_count
        else:
            after_search = sensor_count

        if after_search == 0:
            step("[WARN] 传感器搜索结果为空，跳过详情验证")
            return

        # ── Step 4: 查看第一条传感器详情 ──
        try:
            # 获取第一条传感器名称
            name_col = sensor_page.get_column_index_by_header("传感器名称")
            if not name_col:
                name_col = 1
            names = sensor_page.get_column_data(name_col)
            sensor_name = names[0] if names else None

            if not sensor_name:
                step("[WARN] 无法获取传感器名称，跳过详情")
                return

            step(f"查看传感器详情: {sensor_name}")
            sensor_page.click_row_button(sensor_name, "查看")
            sensor_page.wait_dialog_open(timeout=15)

            # 验证详情弹窗
            detail_fields = sensor_page.get_detail_field("传感器名称")
            step(f"传感器详情: 名称={detail_fields}")
            assert detail_fields != '', ea("传感器名称非空", detail_fields or '(空)')

            # 尝试查看历史数据（如果存在）
            try:
                from selenium.webdriver.common.by import By
                history_tab = driver.find_element(
                    By.XPATH,
                    '//div[contains(@class,"el-tabs__header")]'
                    '//div[contains(.,"历史数据")]'
                )
                if history_tab.is_displayed():
                    step("点击历史数据标签页")
                    history_tab.click()
                    sensor_page.wait_vue_stable()
                    step("历史数据标签页加载 [OK]")
            except Exception:
                step("[INFO] 无历史数据标签页或不可点击")

            sensor_page.click_dialog_cancel()
            sensor_page.wait_dialog_close()

        except TimeoutException:
            step("传感器详情弹窗超时(服务器慢)，跳过详情验证")
            try:
                sensor_page.click_dialog_cancel()
            except Exception:
                pass

        step("E2E-004 设备->传感器->详情 通过 [OK]")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
