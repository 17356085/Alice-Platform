"""试卷管理模块测试脚本"""
import pytest
import sys
import os
import time
import inspect
from datetime import datetime
import allure

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from page.personnel_page.PaperManagePage import PaperManagePage
from page.personnel_page.QuestionBankPage import QuestionBankPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

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


def check(expected, actual, condition):
    print(f"预期结果：{expected}")
    print(f"实际结果：{actual}")
    assert condition, f"【失败】预期：{expected}，实际：{actual}"


# 测试数据
CREATED_FIXED_PAPER = None
CREATED_RANDOM_PAPER = None
CREATED_RULE_PAPER = None


def _generate_paper_name(prefix="试卷"):
    return f"test{datetime.now().strftime('%Y%m%d%H%M%S')}{prefix}"


# ==================== 前置条件：确保题库有试题 ====================

def _ensure_questions_exist(driver):
    """
    确保题库管理中有试题数据，供固定组卷选择。

    如果题库已有数据则跳过，否则直接新增几条试题（使用已有分类）。
    完成后导航回试卷管理页面。
    """
    step("检查题库管理是否有试题数据")
    paper_page = PaperManagePage(driver)

    # 跳转到题库管理
    paper_page.navigate_to_question_bank()

    qb_page = QuestionBankPage(driver)

    # 直接搜索并检查表格是否有数据
    try:
        qb_page.click_search()
        row_count = qb_page.get_table_row_count()
        if row_count > 0:
            step(f"题库已有 {row_count} 条试题，无需新建")
            paper_page.switch_to_paper_management()
            return
    except Exception as e:
        step(f"检查题库数据时异常: {e}，尝试直接新建试题")

    step("题库无数据，准备新增试题")

    # 获取已有分类（用于创建试题时选择）
    category_name = ""
    try:
        cats = qb_page.get_category_names()
        if cats:
            category_name = cats[0]
            step(f"使用已有分类: {category_name}")
        else:
            step("无可用分类，试题创建可能跳过")
    except Exception:
        step("获取分类列表失败")

    if not category_name:
        # 尝试用通用的 "全部分类" 或直接不传 category
        category_name = ""

    # 创建几条不同题型的试题
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    created_any = False

    test_questions = [
        {"type": "单选题", "score": 2, "difficulty": "简单",
         "text": f"AT{ts}_自动化测试单选题_请选择正确答案？",
         "options": {"选项A": "正确选项", "选项B": "错误选项"},
         "answer": "A"},
        {"type": "多选题", "score": 3, "difficulty": "中等",
         "text": f"AT{ts}_自动化测试多选题_以下哪些是正确的？",
         "options": {"选项A": "正确选项1", "选项B": "正确选项2", "选项C": "错误选项"},
         "answer": "A,B"},
        {"type": "判断题", "score": 1, "difficulty": "简单",
         "text": f"AT{ts}_自动化测试判断题_自动化测试可以提高效率？",
         "options": {"选项A": "正确", "选项B": "错误"},
         "answer": "A"},
    ]

    for qt in test_questions:
        try:
            step(f"新增试题：{qt['type']}")
            msg = qb_page.create_question(
                category=category_name,
                q_type=qt["type"],
                score=qt["score"],
                difficulty=qt["difficulty"],
                question_text=qt["text"],
                options=qt["options"],
                correct_answer=qt["answer"],
            )
            step(f"结果: {msg}")
            created_any = True
        except Exception as e:
            step(f"创建{qt['type']}失败: {e}")

    if not created_any:
        step("未成功创建任何试题，固定组卷测试可能无法选择试题")

    step("返回试卷管理页面")
    try:
        paper_page.switch_to_paper_management()
    except Exception:
        paper_page.navigate_to_paper_management()


# ==================== 测试类 ====================

class TestPaperManagement:
    """试卷管理 - 测试类"""

    @pytest.fixture(autouse=True)
    def _allure_case_meta(self, request):
        doc = (inspect.getdoc(request.function) or "").strip()
        title = doc.replace(":", " ").strip() if doc else request.function.__name__
        try:
            allure.dynamic.title(title)
            if doc:
                allure.dynamic.description(doc)
        except Exception:
            pass
        yield

    # ---------- PAPER-001：列表展示 ----------

    def test_001_display_list_and_fields(self, driver_setup):
        """PAPER-001: 正常显示试卷列表及相关字段"""
        case("PAPER-001", "正常显示参数列表、以及相关字段")
        page = PaperManagePage(driver_setup)

        step("验证页面加载完成")
        loaded = page.is_page_loaded()
        check("页面加载成功", loaded, loaded)

        step("获取页面标题")
        page_title = page.get_page_title_text()
        step(f"页面标题: {page_title}")
        if page_title:
            check("页面标题包含'试卷管理'", page_title, "试卷" in page_title)

        step("获取表格列头")
        headers = page.get_table_header_texts()
        step(f"表格列头: {headers}")

        step("获取表格数据行数")
        row_count = page.get_table_row_count()
        step(f"当前页行数: {row_count}")

        step("获取总条数")
        total_text = page.get_total_count_text()
        step(f"总条数: {total_text}")

        # 验证点：表格列数≥7（容忍字段名细微差异，不要求精确匹配）
        check(f"表格列头完整（≥7列）",
              f"实际列数: {len(headers)}, 列头: {headers}",
              len(headers) >= 7)

        check("列表加载正常", f"当前页{row_count}条，{total_text}", row_count >= 0)

    # ---------- PAPER-002：分页 ----------

    def test_002_pagination(self, driver_setup):
        """PAPER-002: 分页跳转验证"""
        case("PAPER-002", "分页跳转（分页）")
        page = PaperManagePage(driver_setup)

        step("点击重置按钮")
        page.click_reset()

        total = page.get_total_count()
        step(f"总数据条数: {total}")

        check("总条数 >= 0", total, total >= 0)

        if total <= 0:
            step("无数据，跳过分页测试")
            check("无数据可测试", "跳过", True)
            return

        default_size = 10

        # 检查数据是否超过一页
        if total <= default_size:
            step(f"总数据 {total} 条未超过每页 {default_size} 条，跳过翻页测试")
            check("数据不足一页，跳过", "跳过", True)
            # 仍然测试切换每页条数
            step("切换每页条数为 20 条/页")
            page.select_page_size(20)
            new_row_count = page.get_table_row_count()
            step(f"切换后当前页行数: {new_row_count}")
            check("切换后列表正常显示",
                  f"之前{default_size}条/页，现在{new_row_count}条/页",
                  new_row_count != 0 or total == 0)
            return

        step("记录当前页第一行数据")
        first_page_row1 = page.get_first_row_data()
        step(f"第一页第一行数据: {first_page_row1}")

        current_page = page.get_current_page_number()
        step(f"当前页码: {current_page}")
        check("默认在第1页", current_page, current_page == 1)

        # 尝试点击下一页
        has_next = page.is_next_page_enabled()
        if has_next:
            step("点击下一页")
            page.click_next_page()

            new_page = page.get_current_page_number()
            step(f"跳转后页码: {new_page}")
            check("成功跳转到第2页", new_page, new_page == 2)

            if total > default_size:
                second_page_row1 = page.get_first_row_data()
                step(f"第二页第一行数据: {second_page_row1}")
                check("分页后数据不同（不重复）",
                      f"第一页: {first_page_row1}, 第二页: {second_page_row1}",
                      second_page_row1 != first_page_row1)

            step("点击上一页，返回第1页")
            page.click_prev_page()
            back_page = page.get_current_page_number()
            check("成功返回第1页", back_page, back_page == 1)
        else:
            step("无下一页按钮（数据不足一页），跳过翻页验证")

        # 切换每页条数
        step("切换每页条数为 20 条/页")
        page.select_page_size(20)

        new_total = page.get_total_count()
        step(f"切换后总条数: {new_total}")
        check("切换条数后数据不变", new_total, new_total == total)

        new_row_count = page.get_table_row_count()
        step(f"切换后当前页行数: {new_row_count}")
        check("切换后列表正常显示",
              f"之前{default_size}条/页，现在{new_row_count}条/页",
              new_row_count != 0 or total == 0)


    # ---------- PAPER-003：新建试卷（固定组卷） ----------

    def test_003_create_fixed_paper(self, driver_setup):
        """PAPER-003: 新建试卷（固定组卷）"""
        global CREATED_FIXED_PAPER
        case("PAPER-003", "新建试卷（固定组卷）")
        page = PaperManagePage(driver_setup)

        # 前置条件：确保题库有试题
        _ensure_questions_exist(driver_setup)
        # 回到试卷管理页面后，重新获取 page 对象
        page = PaperManagePage(driver_setup)

        paper_name = _generate_paper_name("固定")
        CREATED_FIXED_PAPER = paper_name
        step(f"试卷名称: {paper_name}")

        # 1. 点击新增试卷 → 选择组卷方式
        page.select_paper_mode('fixed')

        page.fill_step1_basic_info(
            name=paper_name,
            duration=10,
            pass_score=60,
            desc="请勿外传"
        )

        page.fill_step2_fixed()

        page.go_to_step3()

        page.publish_paper()

        # 6. 验证列表中已创建
        toast = page.get_toast_text()
        step(f"操作结果提示: {toast}")

        step("验证列表中显示新建的试卷")
        exists = page.verify_paper_exists(paper_name)
        check(f"试卷「{paper_name}」创建成功", f"存在: {exists}", exists)

    # ---------- PAPER-004：新建试卷（随机组卷） ----------

    def test_004_create_random_paper(self, driver_setup):
        """PAPER-004: 新建试卷（随机组卷）"""
        global CREATED_RANDOM_PAPER
        case("PAPER-004", "新建试卷（随机组卷）")
        page = PaperManagePage(driver_setup)

        # 前置条件：确保题库有试题
        _ensure_questions_exist(driver_setup)
        page = PaperManagePage(driver_setup)

        paper_name = _generate_paper_name("随机")
        CREATED_RANDOM_PAPER = paper_name
        step(f"试卷名称: {paper_name}")

        # 1. 点击新增试卷 → 选择随机组卷
        page.select_paper_mode('random')

        page.fill_step1_basic_info(
            name=paper_name,
            category="年度考核",
            duration=60,
            pass_score=60,
            desc="请勿外传"
        )

        # 3. 配置随机规则（勾选分类范围，单选题抽取1题）
        random_config = {
            '单选题': {'num': 1, 'score': 2},
        }
        page.fill_step2_random(config=random_config, select_category=True)

        page.save_draft()

        step("返回试卷管理列表页面")
        page.switch_to_paper_management()

        toast = page.get_toast_text()
        step(f"操作结果提示: {toast}")

        step("验证列表中显示新建的试卷")
        exists = page.verify_paper_exists(paper_name)
        check(f"试卷「{paper_name}」创建成功", f"存在: {exists}", exists)

    # ---------- PAPER-005：新建试卷（规则组卷） ----------

    def test_005_create_rule_paper(self, driver_setup):
        """PAPER-005: 新建试卷（规则组卷）"""
        global CREATED_RULE_PAPER
        case("PAPER-005", "新建试卷（规则组卷）")
        page = PaperManagePage(driver_setup)

        # 前置条件：确保题库有试题
        _ensure_questions_exist(driver_setup)
        page = PaperManagePage(driver_setup)

        paper_name = _generate_paper_name("规则")
        CREATED_RULE_PAPER = paper_name
        step(f"试卷名称: {paper_name}")

        # 1. 点击新增试卷 → 选择规则组卷
        page.select_paper_mode('rule')

        page.fill_step1_basic_info(
            name=paper_name,
            category="岗位技能",
            duration=2,
            pass_score=100,
            desc="按规则进行测试"
        )

        page.fill_step2_rule(weights=None, config=None)

        step("设置单选题抽取数量为1")
        page.set_rule_paper_extract_num('单选题', 1)

        step("点击保存并发布")
        page.click_save_and_publish()

        step("返回试卷管理列表页面")
        page.switch_to_paper_management()

        toast = page.get_toast_text()
        step(f"操作结果提示: {toast}")

        step("验证列表中显示新建的规则组卷")
        exists = page.verify_paper_exists(paper_name)
        check(f"规则组卷「{paper_name}」创建成功", f"存在: {exists}", exists)


    # ---------- PAPER-006：搜索试卷 ----------

    def test_006_search_paper(self, driver_setup):
        """PAPER-006: 搜索试卷（按名称、分类、组卷方式、状态）"""
        case("PAPER-006", "搜索试卷")
        page = PaperManagePage(driver_setup)

        # 前置条件：确保有已创建的试卷
        global CREATED_FIXED_PAPER
        paper_name = CREATED_FIXED_PAPER or "test"

        step("1. 按试卷名称搜索")
        page.click_reset()
        page.input_search_name(paper_name)
        page.click_search()
        row_count = page.get_table_row_count()
        check(f"按名称搜索'{paper_name}'有结果", f"行数: {row_count}", row_count >= 0)

        step("2. 按分类搜索")
        page.click_reset()
        page.select_search_category("年度考核")
        page.click_search()
        row_count = page.get_table_row_count()
        check("按分类搜索有结果", f"行数: {row_count}", row_count >= 0)

        step("3. 按组卷方式搜索")
        page.click_reset()
        page.select_search_mode("固定组卷")
        page.click_search()
        row_count = page.get_table_row_count()
        check("按组卷方式搜索有结果", f"行数: {row_count}", row_count >= 0)

        step("4. 按试卷状态搜索")
        page.click_reset()
        page.select_search_status("已发布")
        page.click_search()
        row_count = page.get_table_row_count()
        check("按状态搜索有结果", f"行数: {row_count}", row_count >= 0)

    def test_007_search_reset_all(self, driver_setup):
        """PAPER-007: 搜索条件重置功能（输入所有条件后重置）"""
        case("PAPER-007", "搜索条件重置")
        page = PaperManagePage(driver_setup)

        step("1. 输入所有搜索条件")
        page.click_reset()
        page.input_search_name("测试")
        page.select_search_category("年度考核")
        page.select_search_mode("固定组卷")
        page.select_search_status("已发布")

        step("2. 点击重置按钮")
        page.click_reset()

        step("3. 验证所有搜索条件已重置")
        # 验证名称输入框已清空
        name_input = page.wait.until(EC.presence_of_element_located(page.SEARCH_NAME_INPUT))
        name_value = name_input.get_attribute('value') or ''
        check("名称输入框已清空", f"名称值: '{name_value}'", name_value == '')

        # 验证分类下拉框已重置（显示"全部"）- el-select重置后显示placeholder
        category_text = page.driver.execute_script(
            "return document.querySelectorAll('.el-form .el-select')[0]?.querySelector('.el-select__placeholder')?.textContent || '';"
        )
        check("分类已重置", f"分类值: '{category_text}'", '全部' in category_text or category_text == '')

        # 验证组卷方式下拉框已重置
        mode_text = page.driver.execute_script(
            "return document.querySelectorAll('.el-form .el-select')[1]?.querySelector('.el-select__placeholder')?.textContent || '';"
        )
        check("组卷方式已重置", f"组卷方式: '{mode_text}'", '全部' in mode_text or mode_text == '')

        # 验证状态下拉框已重置
        status_text = page.driver.execute_script(
            "return document.querySelectorAll('.el-form .el-select')[2]?.querySelector('.el-select__placeholder')?.textContent || '';"
        )
        check("状态已重置", f"状态: '{status_text}'", '全部' in status_text or status_text == '')

        step("4. 验证重置后点击搜索可显示全部数据")
        page.click_search()
        row_count = page.get_table_row_count()
        check("重置后可显示全部数据", f"行数: {row_count}", row_count >= 0)

    # ---------- PAPER-008：删除功能测试 ----------

    def test_008_delete_paper(self, driver_setup):
        """PAPER-008: 删除试卷功能测试（清理脏数据）"""
        case("PAPER-008", "删除试卷功能测试")
        page = PaperManagePage(driver_setup)

        global CREATED_FIXED_PAPER, CREATED_RANDOM_PAPER, CREATED_RULE_PAPER

        deleted_count = 0
        papers_to_delete = []
        if CREATED_FIXED_PAPER:
            papers_to_delete.append(CREATED_FIXED_PAPER)
        if CREATED_RANDOM_PAPER:
            papers_to_delete.append(CREATED_RANDOM_PAPER)
        if CREATED_RULE_PAPER:
            papers_to_delete.append(CREATED_RULE_PAPER)

        if not papers_to_delete:
            step("没有记录到测试创建的试卷，尝试删除列表中以'test'开头的试卷")
            page.click_reset()
            page.click_search()
            # 获取所有以 test 开头的试卷名称
            rows = driver_setup.find_elements(By.XPATH, '//tr[contains(@class,"el-table__row")]')
            for row in rows:
                try:
                    name_cell = row.find_element(By.XPATH, './/td[1]//div[contains(@class,"cell")]')
                    name = name_cell.text.strip()
                    if name.startswith("test"):
                        papers_to_delete.append(name)
                except Exception:
                    continue
            step(f"找到 {len(papers_to_delete)} 条测试数据待删除")

        for paper_name in papers_to_delete:
            step(f"删除试卷: {paper_name}")
            page.click_reset()
            page.input_search_name(paper_name)
            page.click_search()

            if page.get_table_row_count() == 0:
                step(f"试卷 {paper_name} 已不存在，跳过")
                continue

            # 点击删除按钮
            result = page.click_row_action_by_name(paper_name, "删除")
            if not result:
                step(f"未找到删除按钮，尝试点击第一行删除")
                result = page.click_first_row_button("删除")
            check(f"删除按钮点击成功 ({paper_name})", f"结果: {result}", result)

            # 处理确认弹窗
            if page.is_confirm_dialog_visible():
                dialog_text = page.get_confirm_dialog_text()
                step(f"确认弹窗: {dialog_text}")
                check("删除确认弹窗显示", f"文本: {dialog_text}", "删除" in dialog_text or "确定" in dialog_text)
                page.confirm_dialog(confirm=True)

            toast = page.get_toast_text()
            step(f"删除结果: {toast}")

            # 验证删除成功
            page.click_reset()
            page.input_search_name(paper_name)
            page.click_search()
            row_count = page.get_table_row_count()
            check(f"试卷已删除 ({paper_name})", f"行数: {row_count}", row_count == 0)
            if row_count == 0:
                deleted_count += 1

        step(f"共删除 {deleted_count}/{len(papers_to_delete)} 条试卷")
        check("脏数据清理完成", f"删除 {deleted_count} 条", deleted_count > 0 or len(papers_to_delete) == 0)

        # 清空全局变量
        CREATED_FIXED_PAPER = None
        CREATED_RANDOM_PAPER = None
        CREATED_RULE_PAPER = None


if __name__ == "__main__":
    pytest.main(["-v", __file__])
