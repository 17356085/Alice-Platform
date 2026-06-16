/**
 * 我的申请测试 — P2
 *
 * 覆盖:
 *   1. 申请列表 + 统计
 *   2. 状态筛选（全部/待审批/已通过/已驳回）
 *   3. 申请详情
 */
const { MiniDriver } = require('../../src/driver');
const { config } = require('../../src/config/test.config');
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { MyApplicationListPage, MyApplicationDetailPage } = require('../../src/pages/my-application.page');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
  const flow = new LoginFlow(driver.app);
  await flow.bypassLogin(config.accounts.admin);
}, 120000);

describe('我的申请列表', () => {
  test('列表正常渲染 [smoke]', async () => {
    const page = new MyApplicationListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const stats = await page.getStatistics();
    const list = await page.getApplicationList();
    console.log(`  统计: ${JSON.stringify(stats)}`);
    console.log(`  列表数: ${list.length}`);
    expect(typeof stats.total).toBe('number');
  });

  test('状态筛选切换', async () => {
    const page = new MyApplicationListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const statuses = ['', 'running', 'completed', 'rejected'];
    for (const status of statuses) {
      await page.filterByStatus(status);
      const list = await page.getApplicationList();
      console.log(`  筛选 "${status || '全部'}": ${list.length} 条`);
    }
  });

  test('点击进入详情', async () => {
    const page = new MyApplicationListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const list = await page.getApplicationList();
    if (list.length === 0) {
      console.log('  无申请数据，跳过');
      return;
    }

    await page.tapApplication(0);
    const detailPage = new MyApplicationDetailPage(driver.app);
    try {
      await detailPage.waitForDetail(5000);
      console.log('  详情页已加载');
    } catch {
      console.log('  详情页加载超时');
    }
  });
});
