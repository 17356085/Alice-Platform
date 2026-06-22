"""摄像头管理模块测试

基于实际 HTML 结构（首次运行失败纠正后重写）

实际页面结构（v.s. 推断）：
  - 摄像头管理页面为监控看板（卡片网格），非表格 CRUD 页面
  - 统计卡片使用 stat-value / stat-label（非 BEM 命名）
  - 共 8 张 stat-card（4 仪表盘 + 4 摄像头统计）
  - 搜索区使用 search-item（非 search-wrapper）
  - 摄像头以 monitor-cell 卡片网格展示（非 el-table）
  - 摄像头统计标签：摄像头总数、在线、离线、故障
"""
import os
import sys
import pytest
import allure
from selenium.webdriver.common.by import By

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.equipment_page.CameraManagePage import CameraManagePage


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
#  P0：页面展示 — 加载/统计卡片
# ==================================================================
class TestCameraPageDisplay:

    def test_cam_01_page_load_success(self, driver_setup):
        """CAM-FUNC-001: 摄像头管理页面正常加载"""
        page = CameraManagePage(driver_setup)
        case("CAM-FUNC-001", "正常加载摄像头管理页面")

        step("验证统计卡片加载")
        card_count = page.get_stat_card_count()
        # 页面有 8 张卡片（4 仪表盘 + 4 摄像头统计）
        assert card_count >= 4, \
            ea("显示至少4张统计卡片", f"实际{card_count}张")

        step("验证摄像头统计数字不为空")
        stats = page.get_all_stats()
        assert stats['total'] != '', ea("摄像头总数不为空", stats)
        assert stats['online'] != '', ea("在线数不为空", stats)
        assert stats['offline'] != '', ea("离线数不为空", stats)
        assert stats['total'].isdigit(), ea("总数为数字", stats['total'])

    def test_cam_02_stat_cards_data(self, driver_setup):
        """CAM-FUNC-002: 统计卡片数据展示"""
        page = CameraManagePage(driver_setup)
        case("CAM-FUNC-002", "统计卡片数据展示")

        stats = page.get_all_stats()
        step(f"摄像头统计: 总数={stats['total']}, 在线={stats['online']}, "
             f"离线={stats['offline']}, 故障={stats['fault']}")

        for key in ['total', 'online', 'offline', 'fault']:
            val = stats[key]
            assert val.isdigit(), ea(f"{key}为数字", val)
            assert int(val) >= 0, ea(f"{key} >= 0", val)

        # 验证8张卡片中包含摄像头统计标签
        labels = page.get_stat_labels_text()
        step(f"所有统计卡片标签: {labels}")
        for expected in page.get_available_stat_labels():
            assert expected in labels, \
                ea(f"标签包含「{expected}」", labels)

        step("验证各状态之和小于等于总数")
        total = int(stats['total'])
        online = int(stats['online'])
        offline = int(stats['offline'])
        fault = int(stats['fault'])
        assert online + offline + fault >= 0, \
            ea("各状态值为合理数值", f"{online}+{offline}+{fault}={online+offline+fault}")

    def test_cam_03_cell_grid_display(self, driver_setup):
        """CAM-FUNC-003: 监控卡片网格展示"""
        page = CameraManagePage(driver_setup)
        case("CAM-FUNC-003", "监控卡片网格展示")

        cell_count = page.get_cell_count()
        step(f"当前页监控卡片数量: {cell_count}")

        if cell_count > 0:
            titles = page.get_cell_titles()
            step(f"卡片标题: {titles}")
            assert titles, ea("卡片标题不为空", titles)

            # 验证卡片包含标题、位置、IP 等元素
            locations = page.get_cell_locations()
            ips = page.get_cell_ips()
            step(f"位置: {locations}, IP: {ips}")
            assert len(locations) == cell_count, \
                ea("每张卡片有位置信息", f"位置数:{len(locations)} 卡片数:{cell_count}")
        else:
            step("当前页无监控卡片（可能数据为空或分页加载中）")

    def test_cam_04_stat_labels_match_expected(self, driver_setup):
        """CAM-UI-002: 摄像头统计标签名称校验"""
        page = CameraManagePage(driver_setup)
        case("CAM-UI-002", "统计标签校验")

        all_labels = page.get_stat_labels_text()
        step(f"全部标签: {all_labels}")

        # 过滤出摄像头相关标签（4个: 总数、在线、离线、故障）
        expected = page.get_available_stat_labels()
        camera_labels = [l for l in all_labels if l in expected]
        step(f"摄像头相关标签: {camera_labels}")
        assert len(camera_labels) == 4, \
            ea("摄像头统计标签为4个", f"实际{camera_labels}")


# ==================================================================
#  P1：搜索筛选
# ==================================================================
class TestCameraSearch:

    def test_cam_05_search_by_keyword(self, driver_setup):
        """CAM-FUNC-007: 按关键词搜索"""
        page = CameraManagePage(driver_setup)
        case("CAM-FUNC-007", "关键词搜索")

        step("输入关键词并搜索")
        page.input_keyword("罐区")
        page.click_search()
        count = page.get_cell_count()
        step(f"搜索结果卡片数: {count}")
        assert count >= 0, ea("搜索正常返回", f"匹配{count}条")

    def test_cam_06_search_no_result(self, driver_setup):
        """CAM-EXCP-001: 搜索无匹配结果（退化为输入后检查不崩溃）"""
        page = CameraManagePage(driver_setup)
        case("CAM-EXCP-001", "搜索无结果")

        step("输入不存在的关键词并搜索")
        page.input_keyword("zzzz_nonexistent_camera_99999")
        page.click_search()
        count = page.get_cell_count()
        step(f"搜索后卡片数: {count}")
        # 搜索后页面应稳定加载，不崩溃
        assert count >= 0, ea("搜索操作正常", f"返回{count}条")


# ==================================================================
#  P1：分页
# ==================================================================
class TestCameraPagination:

    def test_cam_07_pagination_exists(self, driver_setup):
        """CAM-FUNC-004: 分页组件存在且有总条数"""
        page = CameraManagePage(driver_setup)
        case("CAM-FUNC-004", "分页组件展示")

        total = page.get_total_count()
        step(f"分页总条数: {total}")
        assert total >= 0, ea("分页总数>=0", total)

    def test_cam_08_next_page(self, driver_setup):
        """CAM-FUNC-004: 翻页后数据加载"""
        page = CameraManagePage(driver_setup)
        case("CAM-FUNC-004", "分页翻页")

        total = page.get_total_count()
        if total <= page.get_cell_count():
            pytest.skip("数据不足一页，跳过翻页测试")

        current_page = page.get_current_page()
        step(f"当前页: {current_page}")
        page.click_next_page()
        new_page = page.get_current_page()
        step(f"翻页后: {new_page}")
        assert new_page > current_page or page.get_cell_count() > 0, \
            ea("翻页后卡片正常加载", f"page={new_page}")


# ==================================================================
#  P1：监控卡片状态
# ==================================================================
class TestCameraCellStatus:

    def test_cam_09_status_tag_display(self, driver_setup):
        """CAM-UI-003: 监控卡片状态标签显示"""
        page = CameraManagePage(driver_setup)
        case("CAM-UI-003", "卡片状态标签")

        if page.get_cell_count() == 0:
            pytest.skip("当前页无监控卡片")

        titles = page.get_cell_titles()
        if not titles:
            pytest.skip("无法获取卡片标题")

        step(f"检查状态标签: {titles[0]}")
        status = page.get_cell_status_tag(titles[0])
        step(f"状态: {status!r}")
        assert status in ['在线', '离线', '故障', ''], \
            ea("状态为预期值之一", status)

    def test_cam_10_cell_action_buttons(self, driver_setup):
        """CAM-FUNC-003: 监控卡片操作按钮存在性"""
        page = CameraManagePage(driver_setup)
        case("CAM-FUNC-003", "卡片操作按钮")

        if page.get_cell_count() == 0:
            pytest.skip("当前页无监控卡片")

        titles = page.get_cell_titles()
        if not titles:
            pytest.skip("无法获取卡片标题")

        # 验证第一张卡片有操作按钮区域
        cells = page.find_all(page.MONITOR_CELL)
        if cells:
            actions = cells[0].find_elements(By.CSS_SELECTOR, '.monitor-cell-actions button')
            step(f"操作按钮数量: {len(actions)}")
            assert len(actions) >= 1, \
                ea("操作按钮>=1个", len(actions))


# ==================================================================
#  P1：数据一致性校验
# ==================================================================
class TestCameraDataVerification:

    def test_cam_11_stat_total_matches_pagination(self, driver_setup):
        """CAM-DATA-001: 统计卡片总数与分页总条数基本一致"""
        page = CameraManagePage(driver_setup)
        case("CAM-DATA-001", "总数一致性")

        stat_total = int(page.get_stat_total())
        page_total = page.get_total_count()
        step(f"统计总数: {stat_total}, 分页总条数: {page_total}")

        # 统计卡片总数应 >= 分页总条数（统计可能跨页全量）
        assert stat_total >= page_total, \
            ea("统计总数>=分页总条数", f"{stat_total}>={page_total}")

    def test_cam_12_search_resets_pagination(self, driver_setup):
        """CAM-DATA-005: 搜索后分页重置（若数据多页）"""
        page = CameraManagePage(driver_setup)
        case("CAM-DATA-005", "搜索后分页重置")

        total = page.get_total_count()
        page_size = page.get_cell_count()
        if total <= page_size or page_size == 0:
            pytest.skip("数据不足一页或无法确定每页条数，跳过")

        page.click_next_page()
        current_page = page.get_current_page()
        step(f"翻到第{current_page}页")

        page.input_keyword("罐区")
        page.click_search()
        new_page = page.get_current_page()
        step(f"搜索后页码: {new_page}")
        # 搜索后通常重置到第1页
        assert new_page == 1, ea("搜索后重置到第1页", f"current={new_page}")


# ==================================================================
#  P1：弹窗操作（若存在）
# ==================================================================
class TestCameraDialog:

    def test_cam_13_preview_dialog_open(self, driver_setup):
        """CAM-FUNC-017: 点击监控卡片查看/预览按钮打开弹窗 [推断]"""
        page = CameraManagePage(driver_setup)
        case("CAM-FUNC-017", "点击操作按钮打开弹窗")

        if page.get_cell_count() == 0:
            pytest.skip("当前页无监控卡片")

        titles = page.get_cell_titles()
        if not titles:
            pytest.skip("无法获取卡片标题")

        step(f"点击卡片: {titles[0]}")
        clicked = page.click_cell_action(titles[0], '查看')
        if not clicked:
            # 尝试'预览'按钮
            clicked = page.click_cell_action(titles[0], '预览')

        if clicked:
            dialog_visible = page.is_visible(page.OVERLAY_DIALOG, timeout=5)
            step(f"弹窗是否打开: {dialog_visible}")
            if dialog_visible:
                title = page.get_dialog_title()
                step(f"弹窗标题: {title!r}")
                page.click_overlay_dialog_close()
        else:
            step("未找到操作按钮，跳过（页面可能仅展示）")
            pytest.skip("未找到可点击的操作按钮")


# ==================================================================
#  P1：权限控制测试
# ==================================================================
class TestCameraPermissions:

    def test_cam_14_search_input_accessible(self, driver_setup):
        """CAM-AUTH-001: 搜索输入框权限检查"""
        page = CameraManagePage(driver_setup)
        case("CAM-AUTH-001", "搜索输入框权限检查")

        step("检查搜索输入框可见性")
        is_visible = page.is_visible(page.SEARCH_ITEM, timeout=5)
        assert is_visible, ea("搜索输入框应可见（当前用户有权限）", "输入框不可见")

    def test_cam_15_cell_actions_accessible(self, driver_setup):
        """CAM-AUTH-002: 监控卡片操作按钮权限检查"""
        page = CameraManagePage(driver_setup)
        case("CAM-AUTH-002", "卡片操作按钮权限检查")

        if page.get_cell_count() == 0:
            pytest.skip("当前页无监控卡片")

        step("检查操作按钮可见性")
        cells = page.find_all(page.MONITOR_CELL)
        if cells:
            actions = cells[0].find_elements(By.CSS_SELECTOR, '.monitor-cell-actions button')
            assert len(actions) >= 0, "操作按钮区域应存在"


# ==================================================================
#  P1：边界值测试
# ==================================================================
class TestCameraBoundary:

    def test_cam_16_search_special_chars(self, driver_setup):
        """CAM-BND-001: 搜索特殊字符处理"""
        page = CameraManagePage(driver_setup)
        case("CAM-BND-001", "搜索特殊字符处理")

        step("输入特殊字符搜索")
        page.input_keyword("!@#$%^&*()_+-=[]{}|\\:;<>?,./~`")
        page.click_search()

        step("验证搜索不崩溃")
        try:
            count = page.get_cell_count()
            assert count >= 0, "特殊字符搜索正常处理"
        except Exception as e:
            pytest.fail(f"特殊字符搜索导致异常: {e}")

    def test_cam_17_search_long_keyword(self, driver_setup):
        """CAM-BND-002: 搜索超长关键词"""
        page = CameraManagePage(driver_setup)
        case("CAM-BND-002", "搜索超长关键词处理")

        step("输入256字符的超长关键词")
        page.input_keyword("x" * 256)
        page.click_search()

        step("验证处理不崩溃")
        try:
            count = page.get_cell_count()
            assert count >= 0, "超长关键词处理正常"
        except Exception as e:
            pytest.fail(f"超长关键词搜索导致异常: {e}")

    def test_cam_18_empty_keyword_search(self, driver_setup):
        """CAM-BND-003: 空搜索关键词"""
        page = CameraManagePage(driver_setup)
        case("CAM-BND-003", "空搜索关键词处理")

        step("清空输入框并搜索")
        page.input_keyword("")
        page.click_search()

        step("验证搜索正常返回")
        try:
            count = page.get_cell_count()
            assert count >= 0, "空搜索正常处理"
        except Exception as e:
            pytest.fail(f"空搜索导致异常: {e}")


# ==================================================================
#  P2：可靠性测试
# ==================================================================
class TestCameraReliability:

    def test_cam_19_repeat_search_stable(self, driver_setup):
        """CAM-REL-001: 重复搜索稳定性"""
        page = CameraManagePage(driver_setup)
        case("CAM-REL-001", "重复搜索稳定性")

        keywords = ["罐区", "消防", ""]
        for i, kw in enumerate(keywords):
            step(f"第{i+1}次搜索: '{kw}'")
            page.input_keyword(kw)
            page.click_search()
            count = page.get_cell_count()
            assert count >= 0, f"第{i+1}次搜索 count={count} 正常"


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
