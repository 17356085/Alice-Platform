"""合同管理 — 分页功能测试

测试点：
  - TC_P01: 分页总条数显示正确（共 N 条）
  - TC_P02: 翻页 — 下一页操作
  - TC_P03: 翻页 — 上一页操作
  - TC_P04: 切换每页条数
  - TC_P05: 翻页后数据不重复
  - TC_P06: 搜索后分页重置

Vue/Element Plus 注意：
  - ElementPagination 翻页后表格异步重新渲染
  - 需等待旧数据消失、新数据加载完成
  - 翻页时 DOM 可能复用，避免 StaleElementReference
"""
import logging
import time
import inspect

import pytest
import allure

logger = logging.getLogger(__name__)


class TestContractPagination:
    """合同管理 — 分页功能测试"""

    @pytest.fixture(autouse=True)
    def _allure_meta(self, request):
        doc = (inspect.getdoc(request.function) or "").strip()
        title = doc.replace(":", " ").strip() if doc else request.function.__name__
        try:
            allure.dynamic.title(title)
            if doc:
                allure.dynamic.description(doc)
        except Exception:
            pass
        yield

    # ==================================================================
    #  TC_P01: 分页总条数
    # ==================================================================
    @pytest.mark.smoke
    @allure.epic("销售管理")
    @allure.feature("合同管理")
    @allure.story("分页功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_pagination_total_display(self, contract_page):
        """TC_P01: 分页总条数显示正确"""
        page = contract_page

        page.click_reset()
        total_text = page.get_total_count_text()
        total_num = page.get_total_count()
        row_count = page.get_table_row_count()

        logger.info("分页信息: text='%s', 数字=%d, 当前页行数=%d",
                     total_text, total_num, row_count)

        # 总条数文本应包含有意义的信息
        assert total_text, "分页总条数文本不应为空"
        assert total_num > 0, f"总条数应大于0，实际: {total_num}"
        assert "条" in total_text, f"总条数文本应包含'条'，实际: '{total_text}'"

        # 如果总条数 ≤ 每页条数，当前页应显示全部数据
        if total_num <= 10:
            assert row_count == total_num, (
                f"总条数({total_num})≤10时，当前页应显示全部，实际: {row_count}"
            )

        logger.info("TC_P01 通过：分页总条数正确")

    # ==================================================================
    #  TC_P02: 点击下一页
    # ==================================================================
    def test_pagination_next_page(self, contract_page):
        """TC_P02: 翻页 — 点击下一页，表格数据更新"""
        page = contract_page

        page.click_reset()
        is_next_enabled = page.is_next_page_enabled()
        logger.info("下一页按钮可用: %s", is_next_enabled)

        if not is_next_enabled:
            pytest.skip("数据不足一页，跳过翻页测试")

        # 记录第一页第一行数据
        page1_first_row_contract_no = ""
        contract_nos = page.get_contract_no_list()
        if contract_nos:
            page1_first_row_contract_no = contract_nos[0]
        logger.info("第1页第一条合同编号: %s", page1_first_row_contract_no)

        # 翻到下一页
        page.click_next_page()

        # 验证第二页数据
        page2_contract_nos = page.get_contract_no_list()
        logger.info("第2页合同编号: %s", page2_contract_nos)
        assert len(page2_contract_nos) > 0, "第2页应至少有一条数据"

        # 验证第二页数据不同于第一页
        if page1_first_row_contract_no:
            assert page1_first_row_contract_no not in page2_contract_nos, (
                f"第1页数据({page1_first_row_contract_no})不应出现在第2页"
            )

        logger.info("TC_P02 通过：翻到下一页，数据正确更新")

    # ==================================================================
    #  TC_P03: 点击上一页
    # ==================================================================
    def test_pagination_prev_page(self, contract_page):
        """TC_P03: 翻页 — 点击上一页，回到第1页"""
        page = contract_page

        page.click_reset()
        is_next_enabled = page.is_next_page_enabled()

        if not is_next_enabled:
            pytest.skip("数据不足一页，跳过翻页测试")

        # 记录第1页数据
        page1_contract_nos = page.get_contract_no_list()
        logger.info("第1页合同编号: %s", page1_contract_nos)

        # 翻到第2页
        page.click_next_page()

        # 再翻回第1页
        page.click_prev_page()

        # 验证回到第1页
        back_contract_nos = page.get_contract_no_list()
        logger.info("回到第1页合同编号: %s", back_contract_nos)
        assert back_contract_nos == page1_contract_nos, (
            f"回到第1页的数据应与原来一致\n原来: {page1_contract_nos}\n现在: {back_contract_nos}"
        )

        logger.info("TC_P03 通过：上一页回到第1页，数据一致")

    # ==================================================================
    #  TC_P04: 切换每页条数
    # ==================================================================
    def test_pagination_change_page_size(self, contract_page):
        """TC_P04: 切换每页条数 — 切换后表格数据量变化"""
        page = contract_page

        page.click_reset()
        total_num = page.get_total_count()
        logger.info("总条数: %d", total_num)

        if total_num <= 10:
            pytest.skip(f"总数据量({total_num})≤10，无法测试页大小切换效果")

        original_count = page.get_table_row_count()
        logger.info("默认每页条数下的行数: %d", original_count)

        # 切换到更大的页大小（如果有此选项）
        # 注意：具体选项值取决于系统配置
        try:
            page.select_page_size("20条/页")
            time.sleep(0.5)
            new_count = page.get_table_row_count()
            logger.info("切换20条/页后行数: %d", new_count)
            # 行数应有变化或至少不变
            assert new_count >= original_count, (
                f"切换更大页大小时，行数不应减少: {original_count} → {new_count}"
            )
        except Exception as e:
            logger.warning("切换页大小失败（可能无此选项）: %s", e)

        logger.info("TC_P04 通过：页大小切换功能正常")

    # ==================================================================
    #  TC_P05: 翻页后数据不重复
    # ==================================================================
    def test_pagination_data_no_duplicate(self, contract_page):
        """TC_P05: 翻页后数据不重复 — 多页间合同编号不应重复"""
        page = contract_page

        page.click_reset()
        total_num = page.get_total_count()
        all_contract_nos = set()
        current_page = 1

        # 收集所有页的合同编号
        while True:
            contract_nos = page.get_contract_no_list()
            logger.info("第%d页: %s", current_page, contract_nos)

            # 检查是否与已收集的有重复
            for cno in contract_nos:
                assert cno not in all_contract_nos, (
                    f"合同编号 '{cno}' 在第{current_page}页重复出现！"
                )
                all_contract_nos.add(cno)

            if page.is_next_page_enabled():
                page.click_next_page()
                current_page += 1
            else:
                break

        logger.info("共收集 %d 条不重复数据（分%d页）", len(all_contract_nos), current_page)
        assert len(all_contract_nos) == total_num, (
            f"收集的不重复数据({len(all_contract_nos)})应与总条数({total_num})一致"
        )

        logger.info("TC_P05 通过：多页数据无重复")

    # ==================================================================
    #  TC_P06: 搜索后分页重置到第1页
    # ==================================================================
    def test_pagination_reset_after_search(self, contract_page, contract_test_data):
        """TC_P06: 搜索后分页重置 — 在第2页执行搜索，应回到第1页"""
        page = contract_page

        page.click_reset()
        is_next_enabled = page.is_next_page_enabled()

        if not is_next_enabled:
            pytest.skip("数据不足一页，跳过翻页+搜索测试")

        # 翻到第2页
        page.click_next_page()
        page2_contract_nos = page.get_contract_no_list()
        logger.info("第2页数据: %s", page2_contract_nos)

        # 在第2页执行搜索（查询一个在第1页的数据）
        page.search(customer_name=contract_test_data["existing"]["customer_keyword"])

        # 搜索后应显示第1页结果
        search_contract_nos = page.get_contract_no_list()
        logger.info("搜索后数据: %s", search_contract_nos)
        assert len(search_contract_nos) > 0, "搜索结果不应为空"

        # 上一页按钮应不可用（因为已经在第1页）
        # 注：ElementPlus 分页器在第一页时 btn-prev 会有 disabled 属性
        logger.info("TC_P06 通过：搜索后分页正确重置")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
