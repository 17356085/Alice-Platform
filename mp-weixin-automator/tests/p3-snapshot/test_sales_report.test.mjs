/**
 * 销售管理 + 生产报表 — P3
 */
import { describe, it as test, before as beforeAll, after as afterAll, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { MiniDriver } from '../../src/driver.mjs';
import expect from '../../src/utils/expect.mjs';

const require = createRequire(import.meta.url);
const { config } = require('../../src/config/test.config');
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { SaleListPage } = require('../../src/pages/sale.page');
const { ReportIndexPage, ProductionReportPage } = require('../../src/pages/report.page');
const { sleep } = require('../../src/utils/helpers');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
  const flow = new LoginFlow(driver.app);
  await flow.bypassLogin(config.accounts.admin);
}, { timeout: 180000 });

afterAll(async () => {
  if (driver) await driver.close();
});

// 每个测试前清空导航栈，防止 webview 累积超限
beforeEach(async () => {
  if (driver && driver.app) {
    try { await driver.app.reLaunch('/pages/index/index'); await sleep(3000); } catch {}
  }
});

describe('销售管理', () => {
  test('销售订单列表渲染 [smoke]', async () => {
    const page = new SaleListPage(driver.app);
    await page.navigate();
    await page.waitForList();
    const contracts = await page.getExecutingContracts();
    console.log(`  执行中合同数: ${contracts.length}`);
    assert.ok(Array.isArray(contracts));
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
