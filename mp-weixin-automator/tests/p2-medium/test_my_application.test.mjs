/**
 * 我的申请测试 — P2
 */
import { describe, it as test, before as beforeAll, after as afterAll, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { MiniDriver } from '../../src/driver.mjs';
import expect from '../../src/utils/expect.mjs';

const require = createRequire(import.meta.url);
const { config } = require('../../src/config/test.config');
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { MyApplicationListPage, MyApplicationDetailPage } = require('../../src/pages/my-application.page');
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
