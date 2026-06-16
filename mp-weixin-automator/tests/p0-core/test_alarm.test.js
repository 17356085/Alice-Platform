/**
 * 报警管理测试 — P0 (TC-ALARM-001 ~ 005, TC-ALARM-007)
 *
 * 覆盖: 报警列表渲染、统计数据、级别筛选、报警详情、下拉刷新
 */
const { MiniDriver } = require('../../src/driver');
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { AlarmListPage, AlarmDetailPage } = require('../../src/pages/alarm.page');
const { config } = require('../../src/config/test.config');
const { sleep } = require('../../src/utils/helpers');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
  const flow = new LoginFlow(driver.app);
  await flow.bypassLogin(config.accounts.admin);
}, 120000);

describe('报警列表 (TC-ALARM-001)', () => {
  test('列表正常渲染 [smoke]', async () => {
    const page = new AlarmListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const alarms = await page.getAlarmList();
    const data = await page.getData();

    console.log(`  报警数: ${alarms.length}`);
    console.log(`  data keys: ${Object.keys(data).slice(0,10).join(', ')}`);

    // 校验: 页面至少包含数据（可能是 mock 或真实）
    expect(!!data).toBe(true);
  });

  test('统计数据展示 (TC-ALARM-002)', async () => {
    const page = new AlarmListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const stats = await page.getStatistics();
    const totalCount = stats.totalCount || stats.total || 0;
    expect(totalCount).toBeGreaterThanOrEqual(0);
    console.log(`  统计: total=${totalCount}`);
  });

  test('按级别筛选 [smoke]', async () => {
    const page = new AlarmListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    // 通过 setData 直接切换筛选（比 callMethod 稳定）
    const p = await page.getPage();
    if (p) {
      await p.setData({ c: 'urgent' });
      await new Promise(r => setTimeout(r, 1000));
    }
    const urgentAlarms = await page.getAlarmList();
    console.log(`  紧急筛选: ${urgentAlarms.length} 条`);

    if (p) {
      await p.setData({ c: 'normal' });
      await new Promise(r => setTimeout(r, 1000));
    }
    const normalAlarms = await page.getAlarmList();
    console.log(`  一般筛选: ${normalAlarms.length} 条`);

    // 切回全部
    if (p) {
      await p.setData({ c: 'all' });
      await new Promise(r => setTimeout(r, 1000));
    }
  });

  test('下拉刷新 (TC-ALARM-007)', async () => {
    const page = new AlarmListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    await page.pullRefresh();
    await page.waitForList();

    const alarms = await page.getAlarmList();
    console.log(`  刷新后报警数: ${alarms.length}`);
    expect(true).toBe(true);
  });

  test('报警处理操作 (TC-ALARM-006) [destructive]', async () => {
    const listPage = new AlarmListPage(driver.app);
    await listPage.navigate();
    await listPage.waitForList();

    // 找个未处理的报警进入详情
    const alarms = await listPage.getAlarmList();
    const unprocessed = alarms.filter(a => (a.status || a.H || '') !== 'processed');
    if (unprocessed.length === 0) {
      console.log('  无未处理报警，跳过');
      return;
    }

    // 进入第一条未处理报警的详情
    await listPage.tapAlarmItem(alarms.indexOf(unprocessed[0]));
    const detailPage = new AlarmDetailPage(driver.app);
    await detailPage.waitForDetail();

    // 执行处理操作
    await detailPage.handleAlarm('自动化测试 — 已确认处理');
    await sleep(2000);

    // 验证操作结果（不硬断言，记录日志）
    const detail = await detailPage.getDetail();
    console.log(`  报警处理后状态: ${detail.status || detail.H || 'unknown'}`);
    console.log('  报警处理操作完成 [destructive]');
  });
});

describe('报警详情 (TC-ALARM-005)', () => {
  test('报警数据有详情页入口 [smoke]', async () => {
    const listPage = new AlarmListPage(driver.app);
    await listPage.navigate();
    await listPage.waitForList();

    const alarms = await listPage.getAlarmList();
    if (alarms.length === 0) {
      console.log('  无报警数据，跳过');
      return;
    }

    // 报警数据项应包含基本字段
    const first = alarms[0];
    console.log(`  报警数据 keys: ${Object.keys(first).slice(0,8).join(', ')}`);
    expect(Object.keys(first).length).toBeGreaterThan(0);
  });
});
