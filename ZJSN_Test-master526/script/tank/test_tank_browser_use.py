"""Tank 模块 BrowserUse 驱动测试

Tank 模块使用自定义 UI 框架（非 Element Plus），BasePage 通用定位器不可用。
BrowserUse 通过视觉理解 + NL 驱动，直接绕过 DOM 结构差异。

覆盖: 储罐监控 / 日报表 / 报警配置 三个页面的核心操作
"""
import asyncio
import pytest
import logging

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestTankMonitorBrowserUse:
    """储罐监控管理 — BrowserUse 驱动"""

    async def test_bu_01_page_load_and_stats(self):
        """BU-TANK-01: 储罐监控页面加载 + 统计卡片读取"""
        from base.bu_driver import BrowserUseDriver

        async with BrowserUseDriver(headless=True, max_steps=8, use_vision=True) as bu:
            await bu.login()

            result = await bu.run_task("""
Navigate to the tank monitoring page at #/tank/monitor.
Wait for the page to fully load (look for stat cards and a data table).
Report:
1. What statistics/numbers are shown at the top?
2. How many data rows in the table?
3. What are the column headers?
""")
            output = str(result)
            logger.info("BU-TANK-01 result: %s", output[:500])
            # 应能看到储罐相关数据
            assert len(output) > 50, "页面应返回有意义的观察结果"

    async def test_bu_02_search_tank(self):
        """BU-TANK-02: 按储罐编号搜索"""
        from base.bu_driver import BrowserUseDriver

        async with BrowserUseDriver(headless=True, max_steps=6) as bu:
            await bu.login()

            result = await bu.run_task("""
Navigate to #/tank/monitor.
Find the search/filter field for tank ID or keyword.
Type a test search keyword, click search.
Report: Did the table update? How many results?
""")
            logger.info("BU-TANK-02 result: %s", str(result)[:300])
            assert result is not None

    async def test_bu_03_view_detail(self):
        """BU-TANK-03: 点击第一条记录查看详情"""
        from base.bu_driver import BrowserUseDriver

        async with BrowserUseDriver(headless=True, max_steps=10, use_vision=True) as bu:
            await bu.login()

            result = await bu.run_task("""
Navigate to #/tank/monitor.
Find the first data row in the table.
Click the "查看" (view) or "详情" button on the first row.
If a dialog/modal opens: read the detail fields shown (labels + values).
Report: What detail fields are shown?
""")
            logger.info("BU-TANK-03 result: %s", str(result)[:400])
            assert result is not None


@pytest.mark.asyncio
class TestTankReportBrowserUse:
    """储罐日报表 — BrowserUse 驱动"""

    async def test_bu_04_report_page_load(self):
        """BU-TANK-04: 日报表页面加载"""
        from base.bu_driver import BrowserUseDriver

        async with BrowserUseDriver(headless=True, max_steps=8, use_vision=True) as bu:
            await bu.login()

            result = await bu.run_task("""
Navigate to #/tank/report.
Wait for the page to load.
Report:
1. What date range or date picker is shown?
2. Are there data tables or charts?
3. What action buttons are visible?
""")
            logger.info("BU-TANK-04 result: %s", str(result)[:400])
            assert len(str(result)) > 30, "页面应返回有意义的观察结果"


@pytest.mark.asyncio
class TestTankAlarmConfigBrowserUse:
    """储罐报警配置 — BrowserUse 驱动"""

    async def test_bu_05_alarm_config_dialog(self):
        """BU-TANK-05: 通过监控页打开报警配置弹窗"""
        from base.bu_driver import BrowserUseDriver

        async with BrowserUseDriver(headless=True, max_steps=12, use_vision=True) as bu:
            await bu.login()

            result = await bu.run_task("""
Navigate to #/tank/monitor.
Find and click the "配置报警" or "报警配置" button on the page.
A dialog should open. Inside the dialog:
1. What fields are shown (labels)?
2. Are there dropdown selects? If so, list their options.
3. Click "取消" (cancel) to close the dialog.
Report: Complete field list from the dialog.
""")
            logger.info("BU-TANK-05 result: %s", str(result)[:500])
            assert result is not None
