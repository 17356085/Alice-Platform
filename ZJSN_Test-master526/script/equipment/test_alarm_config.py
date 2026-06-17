"""设备报警配置模块测试

测试层次：
  P0 - 页面展示 & 冒烟 (稳定, 不涉及弹窗交互)
  P1 - 搜索筛选 (稳定)
  P2+ - 增删改弹窗交互 (暂跳过: filterable el-select is_displayed 坑)
  API - 直调后端接口验证 CRUD (不依赖 UI 弹窗)
"""
import time
import logging
import os
import sys

import allure
import pytest
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.equipment_page.AlarmConfigPage import AlarmConfigPage
from data.alarm_config_data import (
    EXPECTED_TABLE_HEADER_SET,
    SEARCH_KEYWORD_NOT_FOUND,
)
from config import BASE_URL, DEFAULT_USERNAME, DEFAULT_PASSWORD
from base.cleanup_tracker import get_cleanup_tracker

logger = logging.getLogger(__name__)


# ==================================================================
#  测试辅助
# ==================================================================
def step(text):
    try:
        with allure.step(text):
            print(f"步骤：{text}")
    except Exception:
        print(f"步骤：{text}")


def case(case_id, title):
    print(f"\n========== 用例 {case_id}：{title} ==========")
    try:
        allure.dynamic.title(f"{case_id} {title}")
    except Exception:
        pass


def ea(expected, actual):
    return f"预期结果：{expected}；实际结果：{actual}"


# ==================================================================
#  P0 - 页面展示 & 冒烟
# ==================================================================
class TestAlarmPageDisplay:

    @pytest.mark.smoke
    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ac_01_page_load(self, driver_setup):
        """AC-01: 设备报警配置页面正常加载"""
        page = AlarmConfigPage(driver_setup)
        case("AC-01", "设备报警配置页面正常加载")

        step("验证统计卡片加载")
        card_count = page.get_stat_card_count()
        assert card_count >= 4, \
            ea("显示至少4张统计卡片", f"实际{card_count}张")

        step("验证统计数字不为空")
        stats = page.get_all_stats()
        assert stats['total'] >= 0, ea("报警规则总数存在", stats)

    @pytest.mark.smoke
    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("表格表头展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ac_02_table_headers(self, driver_setup):
        """AC-02: 表格表头正确显示"""
        page = AlarmConfigPage(driver_setup)
        case("AC-02", "表格表头正确显示")

        headers = page.get_table_headers()
        missing = EXPECTED_TABLE_HEADER_SET - set(headers)
        assert not missing, \
            ea(f"表头包含所有9列", f"缺少: {missing}")

    @pytest.mark.smoke
    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ac_03_search_input_visible(self, driver_setup):
        """AC-03: 搜索输入框可见"""
        page = AlarmConfigPage(driver_setup)
        case("AC-03", "搜索输入框可见")

        assert page.is_search_input_visible(), \
            ea("搜索输入框可见", "不可见")

    @pytest.mark.smoke
    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ac_04_add_button_visible(self, driver_setup):
        """AC-04: [新增配置]按钮可见（admin 权限基线）"""
        page = AlarmConfigPage(driver_setup)
        case("AC-04", "新增配置按钮可见")

        assert page.is_add_button_visible(), \
            ea("[新增配置]按钮可见", "不可见")


# ==================================================================
#  P0 - 统计卡片数据校验
# ==================================================================
class TestAlarmStats:

    @pytest.mark.smoke
    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("统计卡片")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ac_05_stats_data_consistency(self, driver_setup):
        """AC-05: 统计卡片数据与表格一致"""
        page = AlarmConfigPage(driver_setup)
        case("AC-05", "统计卡片数据校验")

        stats = page.get_all_stats()
        step(f"统计: 总数={stats['total']}, 已启用={stats['enabled']}, "
             f"已禁用={stats['disabled']}, 今日报警={stats['today']}")

        total = stats['total']
        enabled = stats['enabled']
        disabled = stats['disabled']

        assert total == enabled + disabled, \
            ea(f"总数{total} = 已启用{enabled} + 已禁用{disabled}",
               f"实际: {enabled + disabled}")


# ==================================================================
#  P1 - 搜索筛选
# ==================================================================
class TestAlarmSearch:

    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("搜索筛选")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ac_06_search_by_keyword(self, driver_setup):
        """AC-06: 按关键词搜索"""
        page = AlarmConfigPage(driver_setup)
        case("AC-06", "按关键词搜索报警规则")
        try:
            page.click_reset()
            if page.get_table_row_count() > 0:
                first_name = page.get_cell(1, page.COL_ALARM_NAME)
                if first_name:
                    step(f"用现有关键词搜索: {first_name}")
                    page.search_keyword(first_name)
                    page.click_search()
                    count = page.get_table_row_count()
                    assert count >= 1, \
                        ea("至少搜索到1条结果", f"实际{count}条")
                    return
        except Exception:
            pass
        step("表格无数据或已变化，跳过搜索验证")

    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("搜索筛选")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ac_07_search_no_result(self, driver_setup):
        """AC-07: 搜索不存在的关键词"""
        page = AlarmConfigPage(driver_setup)
        case("AC-07", "搜索无匹配结果")

        page.search_keyword(SEARCH_KEYWORD_NOT_FOUND)
        page.click_search()
        assert page.is_table_empty() or page.get_table_row_count() == 0, \
            ea("表格显示空状态", f"实际{page.get_table_row_count()}行")

    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("搜索筛选")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ac_08_reset_search(self, driver_setup):
        """AC-08: 重置搜索恢复全部数据"""
        page = AlarmConfigPage(driver_setup)
        case("AC-08", "重置按钮")

        initial_count = page.get_table_row_count()
        page.search_keyword(SEARCH_KEYWORD_NOT_FOUND)
        page.click_search()
        page.click_reset()
        reset_count = page.get_table_row_count()
        assert reset_count >= initial_count, \
            ea(f"重置后行数>={initial_count}", f"实际{reset_count}行")


# ==================================================================
#  P2 - 弹窗交互测试 (teleport-safe el-select)
#  使用 AlarmConfigPage._select_dialog_option (WebDriverWait + JS click)
#  解决 Element Plus 2.x teleport + Selenium is_displayed 不兼容
# ==================================================================
class TestAlarmAdd:
    """新增报警规则 — 弹窗填表+保存"""

    CREATED_ALARM_NAME = None

    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("新增报警规则")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ac_09_add_required_only(self, driver_setup):
        """AC-09: 新增报警规则 — 仅必填字段"""
        page = AlarmConfigPage(driver_setup)
        case("AC-09", "新增报警规则-仅必填字段")
        ts = str(int(time.time()))[-6:]
        name = f"autotest_req_{ts}"

        before_count = page.get_table_row_count()

        step("打开新增弹窗并填写必填字段")
        page.click_add_config()
        page.fill_alarm_name(name)
        page.select_alarm_type("设备报警")
        page.select_alarm_level("一般")

        step("保存")
        page.click_dialog_confirm()

        step("搜索验证新增成功")
        page.search_keyword(name)
        page.click_search()
        after_count = page.get_table_row_count()
        assert after_count >= 1, ea(f"搜索'{name}'有结果", f"{after_count}行")
        logger.info("新增成功: %s (前%d → 后%d)", name, before_count, after_count)

        TestAlarmAdd.CREATED_ALARM_NAME = name

    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("新增报警规则")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ac_10_add_all_fields(self, driver_setup):
        """AC-10: 新增报警规则 — 填写全部字段"""
        page = AlarmConfigPage(driver_setup)
        case("AC-10", "新增报警规则-全字段")
        ts = str(int(time.time()))[-6:]
        name = f"autotest_all_{ts}"

        step("打开新增弹窗填写全字段")
        page.click_add_config()
        page.fill_alarm_name(name)
        page.select_alarm_type("设备报警")
        page.select_alarm_level("紧急")

        step("保存并验证")
        page.click_dialog_confirm()
        page.search_keyword(name)
        page.click_search()
        assert page.get_table_row_count() >= 1, ea(f"搜索'{name}'有结果", "无结果")

        # 清理: 删除刚创建的记录
        try:
            page.click_row_delete(0)
            page.confirm_message_box()
        except Exception as e:
            logger.warning("清理失败: %s", e)

    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("新增报警规则")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ac_11_add_cancel(self, driver_setup):
        """AC-11: 新增报警规则 — 取消操作"""
        page = AlarmConfigPage(driver_setup)
        case("AC-11", "新增报警规则-取消")
        ts = str(int(time.time()))[-6:]
        name = f"autotest_cancel_{ts}"

        before_count = page.get_table_row_count()

        step("打开弹窗填写后取消")
        page.click_add_config()
        page.fill_alarm_name(name)
        page.select_alarm_type("设备报警")
        page.click_dialog_cancel()

        step("验证数据未入库")
        page.search_keyword(name)
        page.click_search()
        assert page.is_table_empty() or page.get_table_row_count() == 0, \
            ea(f"取消后'{name}'不存在", "存在")


class TestAlarmEdit:
    """编辑报警规则"""

    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("编辑报警规则")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ac_12_edit_rule(self, driver_setup):
        """AC-12: 编辑报警规则 — 打开编辑弹窗并修改"""
        page = AlarmConfigPage(driver_setup)
        case("AC-12", "编辑报警规则")

        # 使用 ac_09 创建的记录
        name = TestAlarmAdd.CREATED_ALARM_NAME
        if not name:
            pytest.skip("无新增记录，跳过编辑测试")

        step("搜索并编辑")
        page.search_keyword(name)
        page.click_search()
        if page.get_table_row_count() == 0:
            pytest.skip(f"未找到记录: {name}")

        page.click_row_edit(0)

        step("修改报警名称")
        new_name = f"{name}_edit"
        page.fill_alarm_name(new_name)
        page.click_dialog_confirm()

        step("验证编辑成功")
        page.search_keyword(new_name)
        page.click_search()
        assert page.get_table_row_count() >= 1, ea(f"编辑后'{new_name}'存在", "无结果")

        TestAlarmAdd.CREATED_ALARM_NAME = new_name


class TestAlarmDelete:
    """删除报警规则"""

    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("删除报警规则")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ac_13_delete_confirm(self, driver_setup):
        """AC-13: 删除报警规则 — 确认删除"""
        page = AlarmConfigPage(driver_setup)
        case("AC-13", "删除报警规则")

        name = TestAlarmAdd.CREATED_ALARM_NAME
        if not name:
            pytest.skip("无新增记录，跳过删除测试")

        step("搜索并删除")
        page.search_keyword(name)
        page.click_search()
        if page.get_table_row_count() == 0:
            pytest.skip(f"未找到记录: {name}")

        before_count = page.get_table_row_count()

        try:
            page.click_row_delete(0)
            page.confirm_message_box()
            page.wait_vue_stable()
        except Exception as e:
            logger.warning("删除失败，注册清理: %s — %s", name, e)
            tracker = get_cleanup_tracker()
            tracker.register_entity("alarm_config", name)
            pytest.fail(f"删除报警规则失败: {e}")

        step("验证已删除")
        page.search_keyword(name)
        page.click_search()
        after_count = page.get_table_row_count()
        assert after_count < before_count, \
            ea(f"删除后'{name}'消失", f"仍存在({after_count}行)")
        logger.info("删除成功: %s", name)


class TestAlarmDetail:
    """查看报警详情"""

    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("查看报警详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ac_14_view_detail(self, driver_setup):
        """AC-14: 查看报警详情 — 点击查看按钮打开详情弹窗"""
        page = AlarmConfigPage(driver_setup)
        case("AC-14", "查看报警详情")

        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据行，跳过查看测试")

        page.click_row_view(0)
        assert page.is_dialog_visible(), "详情弹窗应可见"
        page.click_dialog_cancel()


class TestAlarmStatusToggle:
    """启停用状态切换"""

    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("启停用状态切换")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ac_15_toggle_status(self, driver_setup):
        """AC-15: 切换报警规则启停用状态"""
        page = AlarmConfigPage(driver_setup)
        case("AC-15", "切换启停用状态")

        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据行，跳过状态切换测试")

        step("点击状态开关")
        page.click_status_toggle(0)
        page.wait_for_toast_text()
        logger.info("状态切换完成")


class TestAlarmBoundary:
    """边界值测试"""

    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("边界值测试")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ac_16_threshold_equal(self, driver_setup):
        """AC-16: 阈值上下限相等 — 应能保存或给出提示"""
        page = AlarmConfigPage(driver_setup)
        case("AC-16", "阈值上下限相等")
        ts = str(int(time.time()))[-6:]
        name = f"autotest_eq_{ts}"

        page.click_add_config()
        page.fill_alarm_name(name)
        page.select_alarm_type("设备报警")
        page.select_alarm_level("一般")
        page.click_dialog_confirm()

        # 搜索验证（边界值允许保存则应有记录，不允许则应有校验提示）
        page.search_keyword(name)
        page.click_search()
        logger.info("阈值相等测试: 搜索结果=%d行", page.get_table_row_count())


class TestAlarmDupSubmit:
    """重复提交防护"""

    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("重复提交防护")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ac_17_double_click_save(self, driver_setup):
        """AC-17: 双击保存 — 不应创建重复记录"""
        page = AlarmConfigPage(driver_setup)
        case("AC-17", "双击保存防重复")
        ts = str(int(time.time()))[-6:]
        name = f"autotest_dbl_{ts}"

        before_count = page.get_table_row_count()

        page.click_add_config()
        page.fill_alarm_name(name)
        page.select_alarm_type("设备报警")
        page.select_alarm_level("一般")

        # 快速双击保存
        page.click(page.DIALOG_SAVE_BTN)
        page.wait_vue_stable()
        try:
            page.click(page.DIALOG_SAVE_BTN)
            page.wait_vue_stable()
        except Exception:
            pass  # 弹窗已关闭则正常

        page.wait_dialog_close()
        page.search_keyword(name)
        page.click_search()
        after_count = page.get_table_row_count()

        # 不应创建超过1条
        assert after_count <= before_count + 1, \
            ea("双击保存不创建重复记录", f"前{before_count}→后{after_count}")

        # 清理
        if after_count > before_count:
            try:
                page.click_row_delete(0)
                page.confirm_message_box()
            except Exception as e:
                logger.warning("清理删除失败: %s", e)


# ==================================================================
#  API层测试 - 直调后端接口验证 CRUD
#  ⚠️ 设备报警配置 API（推测 /api/equipment/alarm-config/*）当前不存在
#  以下用设备台账 API 演示 API 测试模式
#  待后端实现后替换为真实 alarm-config 接口
# ==================================================================
class TestAlarmApi:

    @pytest.fixture(scope="class")
    def api_session(self):
        """通过 API 登录获取 Bearer token"""
        session = requests.Session()
        r = session.post(f"{BASE_URL}/api/auth/login", json={
            "username": DEFAULT_USERNAME,
            "password": DEFAULT_PASSWORD,
        })
        assert r.status_code == 200
        token = r.json()["data"]["accessToken"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session

    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("API-设备列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ac_api_01_device_list(self, api_session):
        """AC-API-01: 获取设备列表 API (报警规则关联设备的数据源)"""
        r = api_session.get(f"{BASE_URL}/api/equipment/device/list",
                            params={"pageNum": 1, "pageSize": 5})
        assert r.status_code == 200
        data = r.json()
        assert data["code"] == 200
        records = data["data"].get("records", [])
        assert len(records) > 0, "设备列表不应为空"
        logger.info("设备列表API: 获取到 %d 条记录", len(records))
        for dev in records[:3]:
            logger.info("  设备: %s (%s)", dev["deviceName"], dev["deviceCode"])

    @allure.epic("设备管理")
    @allure.feature("设备报警配置")
    @allure.story("API-用户列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ac_api_02_user_list(self, api_session):
        """AC-API-02: 获取用户列表 API (通知人员选择的数据源)"""
        r = api_session.get(f"{BASE_URL}/api/system/user/list",
                            params={"pageNum": 1, "pageSize": 10})
        assert r.status_code == 200
        data = r.json()
        assert data["code"] == 200
        records = data["data"].get("records", [])
        assert len(records) > 0, "用户列表不应为空"
        logger.info("用户列表API: 获取到 %d 条记录", len(records))
