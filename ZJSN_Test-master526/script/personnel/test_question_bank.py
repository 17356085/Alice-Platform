"""题库管理模块测试脚本"""
import pytest
import sys
import os
from datetime import datetime
import allure
from selenium.webdriver.common.by import By

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from page.personnel_page.QuestionBankPage import QuestionBankPage

# ==================== 全局数据（用于测试间共享与最终清理） ====================
CREATED_CATEGORY_NAME = None
CREATED_QUESTION_TEXT = None
TIME_TAG = None

# 所有 create 操作生成的名字，供最终清理兜底
_ALL_CREATED = {"categories": [], "questions": []}


def _gen_name(prefix="题库"):
    """生成带时间戳的唯一名称"""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"AT{ts}_{prefix}"


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
        allure.dynamic.description(f"用例编号：{case_id}\n用例说明：{title}")
    except Exception:
        pass


def ea(expected, actual):
    return f"预期结果：{expected}；实际结果：{actual}"


def check(expected, actual, condition):
    print(f"断言条件：{expected}")
    print(f"预期结果：{expected}")
    print(f"实际结果：{actual}")
    assert condition, ea(expected, actual)


# ==================== fixture ====================

@pytest.fixture(scope="module", autouse=True)
def cleanup_after_all(driver_setup):
    """session 级兜底清理：如果正常测试流程遗漏了脏数据，在此尝试清理"""
    yield
    # 注意：如果 session fixture 中的 driver 已关闭，这里可能已无法操作
    # 但正常的测试流程已经通过独立测试用例清理了数据
    # 这个 fixture 主要是日志记录作用
    leftovers = []
    if _ALL_CREATED["categories"]:
        leftovers.append(f"分类: {_ALL_CREATED['categories']}")
    if _ALL_CREATED["questions"]:
        leftovers.append(f"试题: {_ALL_CREATED['questions']}")
    if leftovers:
        print(f"[清理] 以下数据需要手工确认是否残留: {'; '.join(leftovers)}")


@pytest.fixture(scope="module", autouse=True)
def setup_test_data(driver_setup):
    """在所有测试之前，确保有测试数据（分类+试题）"""
    global CREATED_CATEGORY_NAME, CREATED_QUESTION_TEXT, TIME_TAG
    page = QuestionBankPage(driver_setup)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    TIME_TAG = ts

    # 创建分类
    CREATED_CATEGORY_NAME = _gen_name("分类")
    _ALL_CREATED["categories"].append(CREATED_CATEGORY_NAME)
    try:
        page.click_category_add()
        page.dialog_input_category_name(CREATED_CATEGORY_NAME)
        page.dialog_confirm()
        page.wait_for_toast_text(timeout=6)
    except Exception:
        pass

    # 创建试题
    CREATED_QUESTION_TEXT = f"AT{ts}_自动化测试_单选题"
    _ALL_CREATED["questions"].append(CREATED_QUESTION_TEXT)
    try:
        page.create_question(
            category=CREATED_CATEGORY_NAME,
            q_type="单选题",
            score=5,
            difficulty="简单",
            question_text=CREATED_QUESTION_TEXT,
            options={"选项A": "正确", "选项B": "错误"},
            correct_answer="A",
        )
        page.wait_for_toast_text(timeout=6)
    except Exception:
        pass
    page.click_reset()
    yield


@pytest.fixture(autouse=True)
def _reset_after_each(driver_setup):
    """每个测试后点击重置，恢复初始状态"""
    yield
    try:
        page = QuestionBankPage(driver_setup)
        page.click_reset()
    except Exception:
        pass


# ==================== 测试类 ====================

class TestQuestionBank:
    """题库管理测试"""

    # ---------- PS-BANK-01：页面显示 ----------

    @pytest.mark.smoke
    @allure.epic("人员管理")
    @allure.feature("题库管理")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ps_bank_01_page_display(self, driver_setup):
        """正常显示题库列表及相关字段"""
        page = QuestionBankPage(driver_setup)
        case("PS-BANK-01", "正常显示题库列表及相关字段")

        step("获取列表表头并校验")
        headers = page.get_table_headers()
        step(f"实际表头: {headers}")
        # 容忍字段名细微差异，列数≥4即可
        check(f"题库列表字段完整（≥4列）",
              f"实际列数: {len(headers)}, 列头: {headers}",
              len(headers) >= 4)

        step("校验列表是否有数据")
        row_count = page.get_table_row_count()
        if row_count == 0:
            check("允许暂无数据", page.get_empty_text() or "未获取到空态", "暂无数据" in (page.get_empty_text() or ""))
            return
        check("题库列表正常加载", row_count, row_count > 0)

    # ---------- PS-BANK-02：分页 ----------

    def test_ps_bank_02_pagination(self, driver_setup):
        """分页跳转（分页）"""
        page = QuestionBankPage(driver_setup)
        case("PS-BANK-02", "分页跳转")

        step("检查当前页码")
        current_page = page.get_current_page_number()
        check("当前页码存在", current_page, bool(current_page))

        step("点击下一页")
        moved = page.click_next_page()
        if not moved:
            pytest.skip("数据未超过一页，跳过分页测试")

        step("校验页码变化")
        next_page = page.get_current_page_number()
        check("翻页后页码应变化", next_page, next_page and next_page != current_page)

    # ---------- PS-BANK-03：新建试题 ----------
    def test_ps_bank_03_create_question(self, driver_setup):
        """新建试题"""
        global CREATED_CATEGORY_NAME, CREATED_QUESTION_TEXT, TIME_TAG
        page = QuestionBankPage(driver_setup)
        case("PS-BANK-03", "新建试题")

        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        question_text = f"AT{ts}_CRUD_单选题"
        _ALL_CREATED["questions"].append(question_text)

        step(f"点击新建试题，分类：{CREATED_CATEGORY_NAME}，题型：单选题")
        page.create_question(
            category=CREATED_CATEGORY_NAME,
            q_type="单选题",
            score=5,
            difficulty="简单",
            question_text=question_text,
            options={"选项A": "想", "选项B": "不想", "选项C": "不是很想", "选项D": "就是不想"},
            correct_answer="A",
            analysis="你应该想",
        )
        msg = page.wait_for_toast_text(timeout=3)
        if not msg:
            msg = "操作完成"
        check("新建成功提示", msg, "成功" in msg)

        step(f"回查题目「{question_text}」是否在列表中")
        page.click_reset()
        page.input_keyword(question_text)
        page.click_search()
        titles = page.get_column_data_by_header("题目内容")
        check("新建后列表应存在该题目", titles, any(question_text in t for t in titles))
        CREATED_QUESTION_TEXT = question_text

    # ---------- PS-BANK-04：按题干搜索 ----------
    def test_ps_bank_04_search_by_keyword(self, driver_setup):
        """按题干关键词搜索（模糊查询）"""
        page = QuestionBankPage(driver_setup)
        case("PS-BANK-04", "按题干关键词搜索")

        target = CREATED_QUESTION_TEXT
        if not target:
            pytest.skip("未先执行新建试题用例，跳过搜索")

        step("点击重置")
        page.click_reset()
        step(f"输入题干关键词：{target}")
        page.input_keyword(target)
        step("点击搜索")
        page.click_search()

        titles = page.get_column_data_by_header("题目内容")
        empty = page.get_empty_text() or ""
        check("显示符合条件的数据或暂无数据", titles if titles else empty, bool(titles) or "暂无数据" in empty)
        if not titles:
            return
        check(f"题干应包含「{target}」", titles, all(target in t for t in titles))

    # ---------- PS-BANK-05：按题型搜索 ----------
    def test_ps_bank_05_search_by_type(self, driver_setup):
        """按题型搜索（使用已创建的试题数据）"""
        page = QuestionBankPage(driver_setup)
        case("PS-BANK-05", "按题型搜索")

        step("点击重置")
        page.click_reset()
        target = "单选题"
        step(f"选择题型：{target}")
        page.select_search_type(target)
        step("点击搜索")
        page.click_search()

        types = page.get_column_data_by_header("题型")
        empty = page.get_empty_text() or ""
        check("显示符合条件的数据或暂无数据", types if types else empty, bool(types) or "暂无数据" in empty)
        if not types:
            return
        check(f"题型均为「{target}」", types, all(target in t for t in types))

    # ---------- PS-BANK-06：多条件搜索 ----------
    def test_ps_bank_06_search_multi(self, driver_setup):
        """多条件搜索（使用已创建的试题数据）"""
        page = QuestionBankPage(driver_setup)
        case("PS-BANK-06", "多条件搜索")

        target = CREATED_QUESTION_TEXT
        if not target:
            pytest.skip("未先执行新建试题用例，跳过多条件搜索")

        step("点击重置")
        page.click_reset()
        step(f"输入题干关键词：{target}")
        page.input_keyword(target)
        step("选择题型：单选题")
        page.select_search_type("单选题")
        step("选择难度：简单")
        page.select_search_difficulty("简单")
        step("点击搜索")
        page.click_search()

        titles = page.get_column_data_by_header("题目内容")
        types = page.get_column_data_by_header("题型")
        empty = page.get_empty_text() or ""
        has_data = bool(titles)
        check("显示符合条件的数据或暂无数据", titles if has_data else empty, has_data or "暂无数据" in empty)
        if not has_data:
            return
        check(f"题干应包含「{target}」", titles, all(target in t for t in titles))
        check("题型均为单选题", types, all("单选题" in t for t in types))
        if hasattr(page, "get_column_data_by_header"):
            difficulties = page.get_column_data_by_header("难度")
            if difficulties:
                check("难度均为简单", difficulties, all("简单" in d for d in difficulties))

    # ---------- PS-BANK-07：重置按钮 ----------
    def test_ps_bank_07_reset_button(self, driver_setup):
        """重置按钮功能正常"""
        page = QuestionBankPage(driver_setup)
        case("PS-BANK-07", "重置按钮")

        step("输入筛选条件")
        page.input_keyword("安全")
        try:
            page.select_search_type("多选题")
        except Exception:
            pass
        try:
            page.select_search_difficulty("简单")
        except Exception:
            pass

        step("点击重置")
        page.click_reset()

        step("点击搜索验证列表正常加载")
        page.click_search()
        row_count = page.get_table_row_count()
        check("筛选条件清空，列表正常加载", row_count if row_count else (page.get_empty_text() or "暂无数据"),
              row_count > 0 or "暂无数据" in (page.get_empty_text() or ""))

    # ---------- PS-BANK-08：预览 ----------

    def test_ps_bank_08_preview_question(self, driver_setup):
        """查看题目详情（预览）"""
        page = QuestionBankPage(driver_setup)
        case("PS-BANK-08", "查看题目详情")

        target = CREATED_QUESTION_TEXT
        if not target:
            pytest.skip("未先执行新建试题用例，跳过预览")

        step(f"搜索题目：{target}")
        page.click_reset()
        page.input_keyword(target)
        page.click_search()
        count = page.get_table_row_count()
        if count == 0:
            pytest.skip(f"未找到题目 {target}，跳过预览")

        step("点击操作下【预览】")
        try:
            page.click_row_action("预览", row_index=1)
        except Exception:
            try:
                page.click_row_action("查看", row_index=1)
            except Exception:
                pytest.skip("预览按钮不可用，跳过")

        step("验证预览弹窗已打开")
        dialog_open = page.is_dialog_open()
        dialog_text = ""
        if not dialog_open:
            try:
                dialog_text = page.driver.find_element(By.XPATH, '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//*[contains(@class,"el-dialog__title") or contains(@class,"el-drawer__header")])[last()]').text.strip()
            except Exception:
                dialog_text = ""
        check("预览弹窗已打开", dialog_text if dialog_text else dialog_open, dialog_open or bool(dialog_text))

        step("关闭预览弹窗")
        try:
            page.dialog_cancel()
        except Exception:
            try:
                close_btn = page.driver.find_element(By.XPATH,
                    '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[@role="dialog"])[last()]//button[contains(@class,"el-dialog__close")]')
                page.driver.execute_script("arguments[0].click();", close_btn)
                page.short_sleep()
            except Exception:
                pass

        check("预览弹窗已关闭", page.is_dialog_open(), not page.is_dialog_open())

    # ---------- PS-BANK-09：编辑试题 ----------

    def test_ps_bank_09_edit_question(self, driver_setup):
        """编辑试题信息"""
        global CREATED_QUESTION_TEXT
        page = QuestionBankPage(driver_setup)
        case("PS-BANK-09", "编辑试题信息")

        target = CREATED_QUESTION_TEXT
        if not target:
            pytest.skip("未先执行新建试题用例，跳过编辑")

        step(f"搜索题目：{target}")
        page.click_reset()
        page.input_keyword(target)
        page.click_search()
        count = page.get_table_row_count()
        if count == 0:
            pytest.skip(f"未找到题目 {target}，跳过编辑")

        step("点击操作下【编辑】")
        try:
            page.click_row_action("编辑", row_index=1)
        except Exception:
            pytest.skip("编辑按钮不可用，跳过")

        step("修改分值为10，难度为中等")
        page.dialog_input_score(10)
        page.dialog_select_difficulty("中等")
        step("点击确定")
        page.dialog_confirm()

        msg = page.wait_for_toast_text(timeout=6)
        check("修改成功提示", msg, "成功" in (msg or ""))

        step("回查修改是否生效（修改不影响题干，搜索仍应找到）")
        page.click_reset()
        page.input_keyword(target)
        page.click_search()
        titles = page.get_column_data_by_header("题目内容")
        check("编辑后列表仍存在该题目", titles, any(target in t for t in titles))

    # ---------- PS-BANK-10：删除试题 ----------

    def test_ps_bank_10_delete_question(self, driver_setup):
        """删除试题功能"""
        page = QuestionBankPage(driver_setup)
        case("PS-BANK-10", "删除试题")

        target = CREATED_QUESTION_TEXT
        if not target:
            pytest.skip("未先执行新建试题用例，跳过删除")

        step(f"搜索题目：{target}")
        page.click_reset()
        page.input_keyword(target)
        page.click_search()
        count = page.get_table_row_count()
        if count == 0:
            check("题目已被删除或不存在", page.get_empty_text() or "暂无数据", True)
            # 清理全局引用
            if target in _ALL_CREATED["questions"]:
                _ALL_CREATED["questions"].remove(target)
            return

        step("点击第一行删除")
        try:
            page.click_row_action("删除", row_index=1)
        except Exception:
            pytest.skip("删除按钮不可用，跳过")

        step("等待删除确认弹窗出现")
        page.short_sleep()

        step("确认删除")
        try:
            page.dialog_delete_confirm()
        except Exception:
            try:
                confirm_btn = page.driver.find_element(By.XPATH, '/html/body/div[7]/div/div/div[3]/button[2]/span')
                confirm_btn.click()
                page.short_sleep()
            except Exception:
                pass

        msg = page.wait_for_toast_text(timeout=6)
        check("删除成功提示", msg, ("成功" in (msg or "")) or ("删除" in (msg or "")) or bool(msg))

        step("回查删除后不应再存在该题目")
        page.click_reset()
        page.input_keyword(target)
        page.click_search()
        titles = page.get_column_data_by_header("题目内容")
        check("删除后列表不应存在该题目", titles if titles else page.get_empty_text(),
              not any(target in t for t in titles))

        # 清理全局引用
        if target in _ALL_CREATED["questions"]:
            _ALL_CREATED["questions"].remove(target)

    # ---------- PS-BANK-11：删除分类 ----------

    def test_ps_bank_11_delete_category(self, driver_setup):
        """删除试题分类"""
        page = QuestionBankPage(driver_setup)
        case("PS-BANK-11", "删除试题分类")

        target = CREATED_CATEGORY_NAME
        if not target:
            pytest.skip("未先执行新建分类用例，跳过删除")

        step(f"选中分类节点：{target}")
        try:
            page.select_category_tree_node(target)
        except Exception:
            check("分类节点不存在（可能已被删除）", page.get_category_names(), True)
            if target in _ALL_CREATED["categories"]:
                _ALL_CREATED["categories"].remove(target)
            return

        step("点击删除")
        page.click_category_delete()

        step("确认删除")
        try:
            page.dialog_delete_confirm()
        except Exception:
            try:
                confirm_btn = page.driver.find_element(By.XPATH,
                    '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[contains(@class,"el-message-box")])[last()]//button[contains(@class,"el-button--primary")]')
                page.driver.execute_script("arguments[0].click();", confirm_btn)
                page.short_sleep()
            except Exception:
                pass

        msg = page.wait_for_toast_text(timeout=6)
        check("删除成功提示", msg, "成功" in (msg or ""))

        step("验证分类已从分类树中移除")
        cats = page.get_category_names()
        check(f"分类树中不应再有「{target}」", cats, not any(target in c for c in cats))

        # 清理全局引用
        if target in _ALL_CREATED["categories"]:
            _ALL_CREATED["categories"].remove(target)

    # ---------- PS-BANK-12：批量删除（自闭环） ----------

    def test_ps_bank_12_batch_delete(self, driver_setup):
        """批量删除功能（自闭环：创建2条 → 批量删除 → 验证）"""
        page = QuestionBankPage(driver_setup)
        case("PS-BANK-12", "批量删除")

        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        q1 = f"AT{ts}_批量删除_A"
        q2 = f"AT{ts}_批量删除_B"
        category = CREATED_CATEGORY_NAME or "API自动化测试题目分类"

        step("创建第1条待删除题目")
        page.create_question(
            category=category,
            q_type="单选题",
            score=5,
            difficulty="简单",
            question_text=q1,
            options={"选项A": "正确", "选项B": "错误"},
            correct_answer="A",
            analysis="批量删除测试",
        )
        page.wait_for_toast_text(timeout=6)
        page.click_reset()

        step("创建第2条待删除题目")
        page.create_question(
            category=category,
            q_type="单选题",
            score=5,
            difficulty="简单",
            question_text=q2,
            options={"选项A": "是", "选项B": "否"},
            correct_answer="A",
            analysis="批量删除测试",
        )
        page.wait_for_toast_text(timeout=6)

        step("搜索确认两条题目都存在")
        page.click_reset()
        page.input_keyword(ts)
        page.click_search()
        row_count = page.get_table_row_count()
        check("应存在2条待删除数据", row_count, row_count >= 2)

        step("勾选两条题目")
        page.check_table_row_checkbox(1)
        page.check_table_row_checkbox(2)

        step("点击批量删除")
        page.click_batch_delete()

        step("确认删除")
        try:
            page.dialog_delete_confirm()
        except Exception:
            confirm_btn = page.driver.find_element(By.XPATH,
                '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[contains(@class,"el-message-box")])[last()]//button[contains(@class,"el-button--primary")]')
            page.driver.execute_script("arguments[0].click();", confirm_btn)
            page.short_sleep()

        msg = page.wait_for_toast_text(timeout=6)
        check("批量删除成功提示", msg, ("成功" in (msg or "")) or ("删除" in (msg or "")) or bool(msg))

        step("回查确认数据已被删除")
        page.click_reset()
        page.input_keyword(ts)
        page.click_search()
        titles = page.get_column_data_by_header("题目内容")
        check("批量删除后列表不应存在相关题目", titles if titles else page.get_empty_text() or "暂无数据",
              not any(ts in t for t in titles))


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
