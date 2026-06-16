/**
 * 审批工作流测试 — P1
 */
import { describe, it as test, before as beforeAll, after as afterAll, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { MiniDriver } from '../src/driver.mjs';
import expect from '../src/utils/expect.mjs';

const require = createRequire(import.meta.url);
const { config } = require('../src/config/test.config');
const { LoginFlow } = require('../src/flows/LoginFlow');
const { ApprovalListPage, ApprovalDetailPage } = require('../src/pages/approval.page');
const { sleep } = require('../src/utils/helpers');

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

describe('审批列表', () => {
  test('待审批列表渲染 [smoke]', async () => {
    const page = new ApprovalListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const currentTab = await page.getCurrentTab();
    const list = await page.getApprovalList();
    console.log(`  当前 Tab: ${currentTab}, 列表数: ${list.length}`);
    assert.ok(Array.isArray(list));
  });

  test('各 Tab 切换与角标 [smoke]', async () => {
    const page = new ApprovalListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const badges = await page.getTabBadges();
    console.log(`  角标: ${JSON.stringify(badges)}`);

    const tabs = ['pending', 'approved', 'rejected', 'my'];
    for (const tab of tabs) {
      await page.switchTab(tab);
      await sleep(1500);
      const list = await page.getApprovalList();
      console.log(`  Tab "${tab}": 列表数=${list.length}`);
    }
  });

  test('审批列表数据合理性', async () => {
    const page = new ApprovalListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const badges = await page.getTabBadges();
    for (const [key, val] of Object.entries(badges)) {
      expect(typeof val).toBe('number');
      expect(val).toBeGreaterThanOrEqual(0);
    }
    console.log('  角标验证通过');
  });
});

describe('审批详情', () => {
  test('点击审批进入详情 [smoke]', async () => {
    const listPage = new ApprovalListPage(driver.app);
    await listPage.navigate();
    await listPage.waitForList();

    const list = await listPage.getApprovalList();
    if (list.length === 0) {
      console.log('  无审批数据，跳过');
      return;
    }

    await listPage.tapApprovalItem(0);

    const detailPage = new ApprovalDetailPage(driver.app);
    await detailPage.waitForDetail();
    const detail = await detailPage.getDetail();
    console.log(`  审批详情: ${JSON.stringify(detail).slice(0, 200)}`);
    assert.ok(detail);
  });
});

describe('审批操作 [destructive]', () => {
  test('审批通过 [destructive]', async () => {
    const listPage = new ApprovalListPage(driver.app);
    await listPage.navigate();
    await listPage.waitForList();

    await listPage.switchTab('pending');
    const list = await listPage.getApprovalList();
    if (list.length === 0) {
      console.log('  无待审批数据，跳过');
      return;
    }

    await listPage.tapApprovalItem(0);

    const detailPage = new ApprovalDetailPage(driver.app);
    await detailPage.waitForDetail();
    await detailPage.approve('同意——自动化测试');
    console.log('  审批通过操作完成');
  });

  test('审批驳回 [destructive]', async () => {
    const listPage = new ApprovalListPage(driver.app);
    await listPage.navigate();
    await listPage.waitForList();

    await listPage.switchTab('pending');
    const list = await listPage.getApprovalList();
    if (list.length === 0) {
      console.log('  无待审批数据，跳过');
      return;
    }

    await listPage.tapApprovalItem(0);

    const detailPage = new ApprovalDetailPage(driver.app);
    await detailPage.waitForDetail();
    await detailPage.reject('信息不全——自动化测试');
    console.log('  审批驳回操作完成');
  });
});
