"""摄像头管理页面 Page Object — 基于实际 HTML 结构（首次运行失败纠正）

==== 页面结构（实际页面 v.s. 推断）====
  实际发现: 该页面为摄像头监控看板（卡片网格），非表格CRUD页面
  - 8个 .stat-card：4个仪表盘卡片 + 4个摄像头统计卡片
  - 统计卡片使用 stat-value / stat-label（非推断的 BEM 命名 stat-card__value）
  - 搜索区使用 search-item 布局（非 search-wrapper）
  - 摄像头以 monitor-cell 卡片网格展示（非 el-table）
  - 带分页组件 el-pagination
  - 弹窗使用 el-overlay-dialog 模态框

==== 页面组件 ====
  1. 统计卡片（8个 .stat-card，使用 stat-value / stat-label）
     - 仪表盘：今日LNG产量、今日H2产量、LNG库存、设备在线/总数
     - 摄像头：摄像头总数、在线、离线、故障
  2. 搜索筛选区（.search-item）
     - 关键词输入、在线状态下拉、故障状态下拉
     - ✅/❌ 分段切换（纯/segmented）
  3. 摄像头监控卡片网格（.monitor-cell × N）
     - 每个卡片含：标题、屏幕画面区域、位置、IP、操作按钮、状态标签
  4. 分页（el-pagination）— 控制卡片网格分页
  5. 弹窗（el-overlay-dialog）— 详情/预览等

==== 弹窗组件 [推断] ====
  A. 新增/编辑弹窗 — 摄像头信息表单
  B. 详情弹窗 — el-descriptions 只读展示
  C. 视频预览弹窗 — 视频播放器

==== 定位策略 ====
  CSS_SELECTOR 优先（实际页面 class + Element Plus 标准类 + placeholder）
  文本匹配使用相对 XPath 保底
  不使用 data-v-* / el-id-* / nth-child
"""

import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class CameraManagePage(BasePage):
    """摄像头管理页面（监控看板卡片式布局）"""

    # ==================================================================
    #  统计卡片 — 使用实际 stat-value / stat-label class
    #  注意：页面存在 8 张卡片（4仪表盘 + 4摄像头统计）
    # ==================================================================
    STAT_CARD = (By.CSS_SELECTOR, '.stat-card')

    # 摄像头统计卡片（从第5张开始为摄像头相关）
    # 通过 stat-label 文本区分
    STAT_TOTAL = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-label") and normalize-space(.)="摄像头总数"]]'
        '//div[contains(@class,"stat-value")]',
    )
    STAT_ONLINE = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-label") and normalize-space(.)="在线"]]'
        '//div[contains(@class,"stat-value")]',
    )
    STAT_OFFLINE = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-label") and normalize-space(.)="离线"]]'
        '//div[contains(@class,"stat-value")]',
    )
    STAT_FAULT = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-label") and normalize-space(.)="故障"]]'
        '//div[contains(@class,"stat-value")]',
    )

    # 通用 stat 定位器
    STAT_LABEL = (By.CSS_SELECTOR, '.stat-label')
    STAT_VALUE = (By.CSS_SELECTOR, '.stat-value')

    # ==================================================================
    #  搜索筛选区 — 使用实际 search-item class
    # ==================================================================
    SEARCH_ITEM = (By.CSS_SELECTOR, '.search-item')

    # 关键词输入框 — 实际 placeholder="摄像头名称"
    INPUT_KEYWORD = (
        By.CSS_SELECTOR,
        '.search-item input[placeholder*="摄像头"], '
        '.search-item .el-input__inner',
    )

    # ==================================================================
    #  摄像头监控卡片网格 — 替代 el-table
    # ==================================================================
    MONITOR_CELL = (By.CSS_SELECTOR, '.monitor-cell')
    MONITOR_CELL_HEADER = (By.CSS_SELECTOR, '.monitor-cell-header')
    MONITOR_SCREEN = (By.CSS_SELECTOR, '.monitor-screen')
    CELL_TITLE = (By.CSS_SELECTOR, '.cell-title')
    CELL_LOCATION = (By.CSS_SELECTOR, '.cell-location')
    CELL_IP = (By.CSS_SELECTOR, '.cell-ip')
    MONITOR_CELL_FOOTER = (By.CSS_SELECTOR, '.monitor-cell-footer')
    MONITOR_CELL_ACTIONS = (By.CSS_SELECTOR, '.monitor-cell-actions')

    # 注意：如果卡片网格带分页，需页内滚动或切页采集
    # 无 table，所以 TABLE_ROWS/TABLE_EMPTY 等不适用

    # ==================================================================
    #  分页区
    # ==================================================================
    PAGINATION = (By.CSS_SELECTOR, '.el-pagination')
    PAGE_TOTAL = (By.CSS_SELECTOR, '.el-pagination__total')
    PAGE_NEXT = (By.CSS_SELECTOR, '.el-pagination .btn-next:not([disabled])')
    PAGE_PREV = (By.CSS_SELECTOR, '.el-pagination .btn-prev:not([disabled])')
    PAGE_SIZE_SELECT = (
        By.CSS_SELECTOR,
        '.el-pagination__sizes .el-select',
    )
    PAGE_JUMPER_INPUT = (
        By.CSS_SELECTOR,
        '.el-pagination__jump .el-input__inner',
    )

    # ==================================================================
    #  弹窗区 — 通用弹窗
    # ==================================================================
    # 弹窗使用 el-overlay-dialog + el-modal-dialog 结构
    OVERLAY_DIALOG = (By.CSS_SELECTOR, '.el-overlay-dialog')
    DIALOG_TITLE_TEXT = (
        By.CSS_SELECTOR,
        '.el-overlay-dialog .el-dialog__title',
    )

    # 详情弹窗 [推断]
    DETAIL_DIALOG = (
        By.CSS_SELECTOR,
        '.el-overlay-dialog[aria-label*="详情"]',
    )

    # 视频预览弹窗 [推断]
    PREVIEW_DIALOG = (
        By.CSS_SELECTOR,
        '.el-overlay-dialog[aria-label*="预览"], '
        '.el-overlay-dialog[aria-label*="播放"]',
    )

    # ==================================================================
    #  页面就绪 — 等待策略
    # ==================================================================

    def navigate_to_camera_management(self):
        """左侧导航：设备管理 → 摄像头管理"""
        logger.info("导航到: 设备管理 → 摄像头管理")
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '.el-menu,.sidebar-container')
                )
            )
        except TimeoutException:
            logger.warning("侧边栏未在10秒内加载，继续尝试导航")
        self.wait_vue_stable()
        self.wait_vue_stable()
        self.navigate_to("设备管理", "摄像头管理")
        self._wait_page_ready()

    def _wait_page_ready(self, timeout=25):
        """页面完全就绪：loading消失 → 统计卡片有值 → 监控卡片就绪"""
        self._wait_loading_gone(timeout)
        try:
            self.wait_stats_loaded(timeout=min(timeout, 8))
        except TimeoutException:
            logger.warning("统计卡片未加载到数值, 继续等待监控卡片")
        self._wait_cells_ready(timeout=min(timeout, 10))

    def wait_stats_loaded(self, timeout=10):
        """等待任意 .stat-value 有非空文本（使用实际 class）"""
        WebDriverWait(self.driver, timeout).until(
            lambda d: any(
                (el.text or '').strip() != ''
                for el in d.find_elements(By.CSS_SELECTOR, '.stat-value')
            )
        )

    def _wait_cells_ready(self, timeout=10):
        """等待监控卡片就绪：loading消失 + Vue稳定"""
        self._wait_loading_gone(timeout)
        self.wait_vue_stable()

    # ==================================================================
    #  统计卡片 — 使用实际 stat-value / stat-label
    # ==================================================================

    def get_stat_total(self):
        """读取摄像头总数"""
        return self.get_text(self.STAT_TOTAL)

    def get_stat_online(self):
        """读取在线摄像头数"""
        return self.get_text(self.STAT_ONLINE)

    def get_stat_offline(self):
        """读取离线摄像头数"""
        return self.get_text(self.STAT_OFFLINE)

    def get_stat_fault(self):
        """读取故障摄像头数"""
        return self.get_text(self.STAT_FAULT)

    def get_all_stats(self):
        """获取所有统计卡片数值字典"""
        return {
            'total': self.get_stat_total(),
            'online': self.get_stat_online(),
            'offline': self.get_stat_offline(),
            'fault': self.get_stat_fault(),
        }

    def get_stat_card_count(self):
        """获取统计卡片数量（含仪表盘卡片，共8张）"""
        return len(self.find_all(self.STAT_CARD))

    def get_stat_labels_text(self):
        """获取所有统计卡片标签文本"""
        els = self.find_all(self.STAT_LABEL)
        return [e.text.strip() for e in els if e.text.strip()]

    def get_stat_values_text(self):
        """获取所有统计卡片数值文本"""
        els = self.find_all(self.STAT_VALUE)
        return [e.text.strip() for e in els if e.text.strip()]

    # ==================================================================
    #  搜索筛选
    # ==================================================================

    def input_keyword(self, keyword):
        """输入搜索关键词"""
        self.input_text(self.INPUT_KEYWORD, keyword)

    def click_search(self):
        """触发搜索（页面使用输入即搜模式，输入后发送回车）"""
        logger.debug("搜索输入后发送回车触发查询")
        self.input_text(self.INPUT_KEYWORD, '\n')
        self.wait_vue_stable()
        self._wait_cells_ready()

    # ==================================================================
    #  监控卡片操作
    # ==================================================================

    def get_cell_count(self):
        """获取当前页监控卡片数量"""
        cells = self.find_all(self.MONITOR_CELL)
        return len([c for c in cells if c.is_displayed()])

    def get_cell_titles(self):
        """获取所有监控卡片的标题文本"""
        els = self.find_all(self.CELL_TITLE)
        return [e.text.strip() for e in els if e.text.strip()]

    def get_cell_locations(self):
        """获取所有监控卡片的位置文本"""
        els = self.find_all(self.CELL_LOCATION)
        return [e.text.strip() for e in els if e.text.strip()]

    def get_cell_ips(self):
        """获取所有监控卡片的IP文本"""
        els = self.find_all(self.CELL_IP)
        return [e.text.strip() for e in els if e.text.strip()]

    def is_cell_present(self, title_text):
        """判断是否存在指定标题的监控卡片"""
        cells = self.find_all(self.MONITOR_CELL)
        for cell in cells:
            try:
                title_el = cell.find_element(By.CSS_SELECTOR, '.cell-title')
                if title_text in (title_el.text or ''):
                    return True
            except Exception:
                continue
        return False

    def click_cell_action(self, title_text, action_text='查看'):
        """点击指定卡片上的操作按钮 [推断]

        在 monitor-cell-actions 内查找按钮，避免页面其他按钮干扰
        """
        cells = self.find_all(self.MONITOR_CELL)
        for cell in cells:
            try:
                title_el = cell.find_element(By.CSS_SELECTOR, '.cell-title')
                if title_text in (title_el.text or ''):
                    actions = cell.find_element(
                        By.CSS_SELECTOR, '.monitor-cell-actions'
                    )
                    btn = actions.find_element(
                        By.XPATH, f'.//button[contains(.,"{action_text}")]'
                    )
                    self._js_click_el(btn)
                    self.wait_vue_stable()
                    return True
            except Exception:
                continue
        logger.warning("未找到卡片「%s」上的操作按钮「%s」", title_text, action_text)
        return False

    def get_cell_status_tag(self, title_text):
        """获取指定卡片的在线状态标签文本 [推断]"""
        cells = self.find_all(self.MONITOR_CELL)
        for cell in cells:
            try:
                title_el = cell.find_element(By.CSS_SELECTOR, '.cell-title')
                if title_text in (title_el.text or ''):
                    tag = cell.find_element(
                        By.CSS_SELECTOR, '.el-tag .el-tag__content, .el-tag'
                    )
                    return (tag.text or '').strip()
            except Exception:
                continue
        return ''

    # ==================================================================
    #  分页操作
    # ==================================================================

    def get_total_count(self):
        """获取分页总条数"""
        try:
            text = self.get_text(self.PAGE_TOTAL)
            digits = ''.join(filter(str.isdigit, text or ''))
            return int(digits) if digits else 0
        except (ValueError, TypeError, TimeoutException):
            return 0

    def get_current_page(self):
        """获取当前页码"""
        try:
            el = self.find(
                (By.CSS_SELECTOR, '.el-pagination .el-pager li.is-active'),
                timeout=3,
            )
            return int(el.text.strip())
        except Exception:
            return 1

    def click_next_page(self):
        """点击下一页"""
        self.click(self.PAGE_NEXT)
        self._wait_cells_ready()

    def click_prev_page(self):
        """点击上一页"""
        self.click(self.PAGE_PREV)
        self._wait_cells_ready()

    def jump_to_page(self, page_num):
        """跳转至指定页"""
        el = self.find(self.PAGE_JUMPER_INPUT)
        self._scroll_into_view(el)
        el.clear()
        el.send_keys(str(page_num))
        el.send_keys('\n')
        self.wait_vue_stable()
        self._wait_cells_ready()

    # ==================================================================
    #  弹窗通用操作
    # ==================================================================

    def get_dialog_title(self, timeout=None):
        """获取当前弹窗标题"""
        return self.get_text(self.DIALOG_TITLE_TEXT, timeout)

    def wait_overlay_dialog_open(self, timeout=None):
        """等待遮罩弹窗打开 [推断]"""
        self.wait_vue_stable()
        return self.find_visible(self.OVERLAY_DIALOG, timeout)

    def click_overlay_dialog_close(self):
        """关闭遮罩弹窗 [推断]"""
        try:
            close_btn = self.find(
                (By.CSS_SELECTOR, '.el-overlay-dialog .el-dialog__headerbtn')
            )
            self._js_click_el(close_btn)
        except Exception:
            # 兜底：点击遮罩外部
            self.click_dialog_cancel()
        self.wait_vue_stable()

    # ==================================================================
    #  视频预览弹窗 [推断]
    # ==================================================================

    def wait_video_loaded(self, timeout=15):
        """等待视频播放器加载完成 [推断]

        检测 <video> 元素的 readyState >= 2 (HAVE_CURRENT_DATA)
        Returns:
            True 表示视频加载成功，False 表示超时
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script(
                    "var v = document.querySelector('.el-overlay-dialog video');"
                    "return v && v.readyState >= 2;"
                )
            )
            return True
        except TimeoutException:
            logger.warning("视频加载超时（%ss），可能推流地址不可达", timeout)
            return False

    @staticmethod
    def get_available_stat_labels():
        """返回已知的摄像头统计卡片标签（供测试断言参考）"""
        return ['摄像头总数', '在线', '离线', '故障']
