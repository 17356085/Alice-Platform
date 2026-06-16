"""侧边栏导航器 — 统一的菜单导航组件

==== 定位策略（按优先级）====
  1. href 属性：最稳定，路由变更时 href 必然对应更新
     [href="#/system/dict"]
  2. 菜单文字 + el-menu-item：href 不可用时保底
     //li[contains(@class,"el-menu-item")]//span[normalize-space(.)="{text}"]

==== 使用方式 ====
  from base.sidebar_navigator import SidebarNavigator

  nav = SidebarNavigator(driver)
  nav.navigate_to("系统管理", "字典管理")            # 一级子菜单 → 叶子
  nav.navigate_to("人员管理", "培训管理", "课程管理") # 二级嵌套
  nav.navigate_to("控制台")                          # 顶级菜单（无子菜单）

  或通过 BasePage 快捷方法：
  self.navigate_to("系统管理", "字典管理")

==== 菜单结构 ====
  el-menu
  ├── el-menu-item           → 叶子菜单（有 href）
  ├── el-sub-menu            → 一级子菜单（可展开）
  │   ├── el-menu-item       → 叶子
  │   └── el-sub-menu        → 二级子菜单（如 日志管理、培训管理、工作流管理）
  │       └── el-menu-item   → 叶子
  ...

==== 注意事项 ====
  - 当前未展开的子菜单需要先点击展开，再点击子项
  - 已展开的子菜单（有 is-opened class）跳过展开步骤
  - 菜单项可能被侧边栏滚动隐藏，点击前自动 scrollIntoView
"""
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger(__name__)


class SidebarNavigator:
    """侧边栏菜单导航器

    使用 href 属性作为主定位策略（不受菜单文字变更、DOM层级变动影响）。
    支持多级嵌套子菜单自动展开。
    """

    # ── 定位器 ──────────────────────────────────────────────────
    # Menu item by href — 最稳定，路由映射关系不会轻易变
    MENU_ITEM_BY_HREF = (
        By.CSS_SELECTOR,
        'li.el-menu-item a[href="{href}"], '
        'li.el-menu-item[href="{href}"]',
    )
    # Menu item by text — href 不可用时的保底
    MENU_ITEM_BY_TEXT = (
        By.XPATH,
        '//li[contains(@class,"el-menu-item")]'
        '//span[contains(normalize-space(.),"{text}")]',
    )
    # Sub-menu title — 用于展开子菜单
    SUBMENU_TITLE_BY_TEXT = (
        By.XPATH,
        '//div[contains(@class,"el-sub-menu__title")]'
        '//span[contains(normalize-space(.),"{text}")]',
    )
    # Sub-menu 是否已展开
    SUBMENU_OPENED = (
        By.XPATH,
        '//li[contains(@class,"el-sub-menu") and contains(@class,"is-opened")]'
        '//div[contains(@class,"el-sub-menu__title")]'
        '//span[contains(normalize-space(.),"{text}")]',
    )

    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout, poll_frequency=0.5)

    # ==================================================================
    #  公共方法
    # ==================================================================

    def navigate_to(self, *menu_path):
        """导航到目标菜单项

        Args:
            *menu_path: 菜单路径，从顶级开始。例如：
                ("系统管理", "字典管理")           → 一级子菜单 → 叶子
                ("系统管理", "日志管理", "登录日志") → 二级嵌套
                ("控制台",)                        → 顶级叶子菜单

        Returns:
            bool: 是否导航成功

        Raises:
            TimeoutException: 菜单项未找到

        Example:
            >>> nav = SidebarNavigator(driver)
            >>> nav.navigate_to("系统管理", "字典管理")
        """
        if not menu_path:
            raise ValueError("menu_path 不能为空")

        logger.info("侧边栏导航: %s", " → ".join(menu_path))

        # ── 统一处理：JS hash 优先 ──
        leaf = menu_path[-1]
        href = self._text_to_href(leaf)
        if href:
            try:
                return self._navigate_by_js_hash(href, leaf)
            except Exception as exc:
                logger.debug("JS hash 导航失败 (%s)，回退到侧边栏点击", exc)

        # 如果是单个顶级菜单（无子菜单层级，如"控制台"），直接点击
        if len(menu_path) == 1:
            return self._click_menu_item(menu_path[0])

        # 多级路径：展开子菜单 + 点击叶子
        return self._navigate_nested(menu_path)

    def navigate_to_by_href(self, href):
        """直接按 href 跳转（跳过菜单展开逻辑）

        适合已知确切路由的场景，如 #/system/dict

        Example:
            >>> nav.navigate_to_by_href("#/system/dict")
        """
        logger.info("侧边栏 href 导航: %s", href)
        return self._click_menu_item(href=href)

    def is_menu_expanded(self, sub_menu_title):
        """检查指定子菜单是否已展开"""
        xpath = self.SUBMENU_OPENED[1].format(text=sub_menu_title)
        try:
            self.driver.find_element(By.XPATH, xpath)
            return True
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════
    #  href → 菜单文字 映射表
    #  用途：根据当前 URL 反向查找所在的菜单路径
    #  注意：以下映射基于已知的侧边栏结构，后续新增页面需同步更新
    # ══════════════════════════════════════════════════════════════

    # 一级子菜单 → 下级 href 列表（用于自动确定导航路径）
    HREF_TO_PATH = {
        "#/": ["控制台"],
        "#/system/user": ["系统管理", "用户管理"],
        "#/system/role": ["系统管理", "角色管理"],
        "#/system/menu": ["系统管理", "菜单管理"],
        "#/system/dept": ["系统管理", "组织管理"],
        "#/system/dict": ["系统管理", "字典管理"],
        "#/system/config": ["系统管理", "参数设置"],
        "#/system/log/login-log": ["系统管理", "日志管理", "登录日志"],
        "#/system/log/oper-log": ["系统管理", "日志管理", "操作日志"],
        "#/system/log/system-log": ["系统管理", "日志管理", "系统日志"],
        "#/system/job": ["系统管理", "定时任务"],
        "#/system/notice": ["系统管理", "通知管理"],
        "#/system/api": ["系统管理", "接口管理"],
        "#/system/monitor": ["系统管理", "系统监控"],
        "#/system/workflow/todo": ["系统管理", "工作流管理", "待我审批"],
        "#/system/workflow/history": ["系统管理", "工作流管理", "我已审批"],
        "#/system/workflow/my-applications": ["系统管理", "工作流管理", "我发起的"],
        "#/system/workflow/sap-push-log": ["系统管理", "工作流管理", "SAP推送日志"],
        "#/system/workflow/approval-chain": ["系统管理", "工作流管理", "审批链配置"],
        "#/equipment/unit": ["设备管理", "装置台账"],
        "#/equipment/device": ["设备管理", "设备台账"],
        "#/equipment/sensor": ["设备管理", "传感器管理"],
        "#/equipment/maintenance": ["设备管理", "设备维保"],
        "#/equipment/camera": ["设备管理", "摄像头管理"],
        "#/equipment/key-param": ["设备管理", "关键参数监控"],
        "#/equipment/alarm-config": ["设备管理", "设备报警配置"],
        "#/tank/monitor": ["储罐管理", "储罐监控管理"],
        "#/tank/report": ["储罐管理", "储罐日报表"],
        "#/monitor": ["DCS数据", "关键参数监控"],
        "#/all-data": ["DCS数据", "全部点位"],
        "#/common-data": ["DCS数据", "常用点位"],
        "#/point-config": ["DCS数据", "点位配置"],
        "#/upload-log": ["DCS数据", "上传日志"],
        "#/lab/gas/report": ["化验室取样", "气体分析报告单"],
        "#/lab/gas/compare": ["化验室取样", "气体分析对比"],
        "#/lab/gas/indicator": ["化验室取样", "气体分析设计指标"],
        "#/lab/water/report": ["化验室取样", "水质分析报告单"],
        "#/lab/water/compare": ["化验室取样", "水质分析对比"],
        "#/lab/water/indicator": ["化验室取样", "水质分析设计指标"],
        "#/personnel/training/course": ["人员管理", "培训管理", "课程管理"],
        "#/personnel/training/plan": ["人员管理", "培训管理", "培训计划"],
        "#/personnel/training/question": ["人员管理", "培训管理", "题库管理"],
        "#/personnel/training/paper": ["人员管理", "培训管理", "试卷管理"],
        "#/personnel/training/examArrange": ["人员管理", "培训管理", "考试管理"],
        "#/personnel/training/examRecord": ["人员管理", "培训管理", "考试记录"],
        "#/personnel/training/my-exam": ["人员管理", "培训管理", "考试测评"],
        "#/personnel/training/onlineStudy": ["人员管理", "培训管理", "在线学习"],
        "#/personnel/training/wrongQuestion": ["人员管理", "培训管理", "错题本"],
        "#/personnel/training/practice": ["人员管理", "培训管理", "自主练习"],
        "#/personnel/training/studyRecord": ["人员管理", "培训管理", "学习记录"],
        "#/personnel/training/my-archive": ["人员管理", "培训管理", "个人学习档案"],
        "#/personnel/training/certificate": ["人员管理", "培训管理", "证书管理"],
        "#/personnel/employee": ["人员管理", "员工管理"],
        "#/personnel/post": ["人员管理", "岗位管理"],
        "#/personnel/contractor": ["人员管理", "承包商管理", "承包商单位"],
        # 承包商人员与单位共用路由 #/personnel/contractor，通过侧边栏 nest-menu 切换视图
        "#/personnel/contractor/approval": ["人员管理", "承包商管理", "入场审批"],
        "#/personnel/contractor/record": ["人员管理", "承包商管理", "入场记录"],
        "#/personnel/contractor/confirm": ["人员管理", "承包商管理", "入场确认"],
        "#/production/daily-report": ["生产管理", "日报表管理"],
        "#/production/shift-report": ["生产管理", "交接班日报表"],
        "#/production/monthly-report": ["生产管理", "生产月报表"],
        "#/production/shift-team-config": ["生产管理", "班次班组配置"],
        "#/production/business-type-config": ["生产管理", "业务类型配置"],
        "#/sales/customer": ["销售管理", "客户管理"],
        "#/sales/contract": ["销售管理", "合同管理"],
        "#/sales/order": ["销售管理", "销售订单"],
        "#/sales/measurement": ["销售管理", "销售日报表"],
        # ── 库管管理（15页，3子模块）──
        # 环保危废管理 (hazard) — 5页
        "#/warehouse/hazard/in-order": ["库管管理", "环保危废管理", "入库"],
        "#/warehouse/hazard/out-order": ["库管管理", "环保危废管理", "出库"],
        "#/warehouse/hazard/stock": ["库管管理", "环保危废管理", "库存查询"],
        "#/warehouse/hazard/io-record": ["库管管理", "环保危废管理", "出入库明细表"],
        "#/warehouse/hazard/item": ["库管管理", "环保危废管理", "物品管理"],
        # 备品备件管理 (spare) — 8页
        "#/warehouse/spare/in-order": ["库管管理", "备品备件管理", "入库"],
        "#/warehouse/spare/out-order": ["库管管理", "备品备件管理", "出库"],
        "#/warehouse/spare/stock": ["库管管理", "备品备件管理", "库存查询"],
        "#/warehouse/spare/stocktake": ["库管管理", "备品备件管理", "库存盘点"],
        "#/warehouse/spare/stock-adjust": ["库管管理", "备品备件管理", "盘点调整"],
        "#/warehouse/spare/io-record": ["库管管理", "备品备件管理", "出入库记录"],
        "#/warehouse/spare/requisition": ["库管管理", "备品备件管理", "领用申请"],
        "#/warehouse/spare/item": ["库管管理", "备品备件管理", "物品管理"],
        # 三剂消耗管理 (reagent) — 2页
        "#/warehouse/reagent/item": ["库管管理", "三剂消耗管理", "物品管理"],
        "#/warehouse/reagent/fill": ["库管管理", "三剂消耗管理", "装填管理"],
    }

    # ==================================================================
    #  内部方法
    # ==================================================================

    def _navigate_nested(self, menu_path):
        """处理多级菜单路径：JS hash 优先，侧边栏点击兜底"""
        *parents, leaf = menu_path

        # ── 策略1：JS hash 直接跳转（最可靠，绕过侧边栏折叠/选择器问题）──
        href = self._text_to_href(leaf)
        if href:
            try:
                self._navigate_by_js_hash(href, leaf)
                return True
            except Exception as exc:
                logger.debug("JS hash 导航失败 (%s)，回退到侧边栏点击: %s", leaf, exc)

        # ── 策略2：侧边栏点击（兜底）──
        for i, title in enumerate(parents):
            if self.is_menu_expanded(title):
                logger.debug("子菜单已展开: %s", title)
                continue
            logger.debug("展开子菜单: %s", title)
            try:
                self._click_submenu_title(title)
            except Exception:
                logger.debug("侧边栏展开失败: %s，继续尝试", title)

        return self._click_menu_item(leaf)

    def _navigate_by_js_hash(self, href, label=""):
        """通过 window.location.hash 直接导航（绕过侧边栏）

        JS hash 导航后，等待 Vue Router + Element Plus 异步表格完全渲染。
        关键：必须等 AJAX 数据返回 + 表格列稳定，否则测试会看到不完整的页面。
        """
        logger.info("JS hash 导航: %s → %s", label, href)

        # 关键：确保当前在已登录的 app 首页 (#/welcome)，
        # 否则 hash 导航可能被 auth guard 重定向
        self._ensure_on_welcome()

        # 设置 hash（仅改 hash fragment，不触发整页重载）
        self.driver.execute_script(f"window.location.hash = '{href}';")
        logger.debug("hash 已设置: %s", href)

        # 等待目标页面渲染完成
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: href in d.execute_script("return window.location.hash;")
            )
        except TimeoutException:
            logger.warning("hash 未在 10s 内生效，当前: %s",
                self.driver.execute_script("return window.location.hash;"))

        self._wait_page_content_ready()
        return True

    def _ensure_on_welcome(self):
        """确保浏览器在已登录的首页，不在登录页"""
        for _ in range(3):
            h = self.driver.execute_script("return window.location.hash;")
            if h in ("", "#/", "#/welcome", "#/index"):
                return
            if h == "#/login":
                logger.debug("仍在登录页，等待跳转...")
                time.sleep(3)
                continue
            # 已在某个内容页，直接返回
            return
        logger.warning("可能仍在登录页，尝试强制跳转 welcome")
        self.driver.execute_script("window.location.hash = '#/welcome';")
        time.sleep(3)

    def _wait_page_content_ready(self, timeout=20):
        """等待 Vue SPA 页面内容完全渲染

        自适应策略：
        - 有 .el-table 的页面：等表格列数稳定
        - 无表格页面（dashboard/form）：等 Vue 动画完成 + 固定等待
        """
        # 阶段1：基础页面 + 无 loading 遮罩
        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: d.execute_script(
                    "return document.readyState === 'complete' && "
                    "!document.querySelector('.el-loading-mask')"
                )
            )
        except TimeoutException:
            pass

        # 阶段2：Vue 动画完成
        try:
            from base.base_page import BasePage
            BasePage(self.driver).wait_vue_stable(timeout=10)
        except Exception:
            pass
        time.sleep(1)

        # 阶段3：检测是否有表格，有则等待表格列数稳定
        has_table = self.driver.execute_script(
            "return !!document.querySelector('.el-table__header-wrapper')"
        )
        if has_table:
            deadline = time.time() + timeout
            last_count = -1
            stable_count = 0
            while time.time() < deadline:
                try:
                    current_count = self.driver.execute_script(
                        "return document.querySelectorAll('.el-table__header-wrapper th').length;"
                    )
                except Exception:
                    current_count = 0

                if current_count > 0 and current_count == last_count:
                    stable_count += 1
                    if stable_count >= 3:
                        logger.debug("表格就绪: %d 列", current_count)
                        break
                else:
                    stable_count = 0
                    last_count = current_count
                time.sleep(0.5)
        else:
            # 无表格页面：等 Vue 稳定 + 额外等待
            try:
                from base.base_page import BasePage
                BasePage(self.driver).wait_vue_stable(timeout=5)
            except Exception:
                pass

        # 阶段4：等待表格数据就绪（有行数据或分页显示非零总数）
        deadline2 = time.time() + 10
        while time.time() < deadline2:
            has_data = self.driver.execute_script("""
                var rows = document.querySelectorAll('.el-table__body-wrapper tbody tr.el-table__row');
                if (rows.length > 0) return true;
                var pag = document.querySelector('.el-pagination__total');
                if (pag && /\\d+/.test(pag.textContent)) {
                    var m = pag.textContent.match(/\\d+/);
                    return m && parseInt(m[0]) > 0;
                }
                return false;
            """)
            if has_data:
                break
            time.sleep(1)

        # 阶段5：固定等待异步子组件
        time.sleep(5)

    def _click_submenu_title(self, title):
        """点击子菜单标题以展开"""
        xpath = self.SUBMENU_TITLE_BY_TEXT[1].format(text=title)
        el = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        self._scroll_and_click(el)

    def _click_menu_item(self, text=None, href=None):
        """点击叶子菜单项

        优先使用 href 定位（CSS_SELECTOR，最稳定），
        文本定位作为保底（XPath）。
        """
        # 策略1：按文本映射到已知 href
        if href is None and text:
            href = self._text_to_href(text)

        # 策略2：CSS_SELECTOR 按 href 定位
        if href:
            css = self.MENU_ITEM_BY_HREF[1].format(href=href)
            try:
                el = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, css))
                )
                self._scroll_and_click(el)
                logger.info("导航成功 (href): %s", href)
                return True
            except TimeoutException:
                logger.debug("CSS href 定位失败: %s，尝试文本定位", href)

        # 策略3：XPath 按文本定位 → 优先点击 <a> 标签触发 Vue Router
        if text:
            # 3a. 尝试按文本找到 <a> 标签（href 方式）
            a_xpath = (
                f'//li[contains(@class,"el-menu-item")]'
                f'//a[contains(normalize-space(.),"{text}")]'
            )
            try:
                el = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, a_xpath))
                )
                self._scroll_and_click(el)
                logger.info("导航成功 (a tag): %s", text)
                return True
            except TimeoutException:
                pass

            # 3b. 保底：点击 <li> 本身
            li_xpath = (
                f'//li[contains(@class,"el-menu-item")]'
                f'[contains(normalize-space(.),"{text}")]'
            )
            el = self.wait.until(EC.element_to_be_clickable((By.XPATH, li_xpath)))
            self._scroll_and_click(el)
            logger.info("导航成功 (li tag): %s", text)
            return True

        raise TimeoutException(
            f"无法定位菜单项: text={text}, href={href}"
        )

    def _text_to_href(self, text):
        """根据菜单文字查找对应的 href

        从 HREF_TO_PATH 中反向查找：遍历所有路径，找到末尾匹配的 href。
        """
        for href, path in self.HREF_TO_PATH.items():
            if path and path[-1] == text:
                return href
        # 顶级菜单（如"控制台"）
        for href, path in self.HREF_TO_PATH.items():
            if len(path) == 1 and path[0] == text:
                return href
        return None

    def _scroll_and_click(self, element):
        """滚动到可见区域 + JS 点击（绕过 Element UI 动画遮挡）"""
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                element,
            )
        except Exception:
            pass
        time.sleep(0.15)
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)
        time.sleep(0.3)
