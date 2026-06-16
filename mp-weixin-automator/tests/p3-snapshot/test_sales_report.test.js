/**
 * 销售管理 + 生产报表 综合测试 — P3
 *
 * 覆盖: 销售订单列表+图表、日报表、生产报表切换
 */
const { MiniDriver } = require('../../src/driver');
const { config } = require('../../src/config/test.config');
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { SaleListPage } = require('../../src/pages/sale.page');
const { ReportIndexPage, ProductionReportPage } = require('../../src/pages/report.page');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
  const flow = new LoginFlow(driver.app);
  await flow.bypassLogin(config.accounts.admin);
}, 120000);

describe('销售管理', () => {
  test('销售订单列表渲染 [smoke]', async () => {
    const page = new SaleListPage(driver.app);
    await page.navigate();
    await page.waitForList();
    const contracts = await page.getExecutingContracts();
    console.log(`  执行中合同数: ${contracts.length}`);
    expect(Array.isArray(contracts)).toBe(true);
  });
});

describe('生产报表', () => {
  test('生产报表首页渲染 [smoke]', async () => {
    const page = new ReportIndexPage(driver.app);
    await page.navigate();
    await page.waitForContent();
    const stats = await page.getStatistics();
    console.log(`  产量: ${stats.productionOutput}, 合格率: ${stats.qualificationRate}`);
  });

  test('生产报表详情页渲染', async () => {
    const page = new ProductionReportPage(driver.app);
    await page.navigate();
    await page.waitForContent();
    const data = await page.getReportData();
    console.log('  报表页已加载');
  });
});
