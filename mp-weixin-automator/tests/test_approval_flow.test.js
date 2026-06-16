/**
 * @jest-environment node
 *
 * 审批工作流测试 — P1
 *
 * 覆盖:
 *   1. 审批列表各 Tab 切换
 *   2. 角标数字合理性
 *   3. 进入详情页
 *   4. 审批通过/驳回操作（destructive）
 */
const { MiniDriver } = require('../src/driver');
const { ApprovalListPage, ApprovalDetailPage } = require('../src/pages/approval.page');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
});

// 连接由 jest.teardown.js 统一关闭

describe('审批列表', () => {
  test('待审批列表渲染 [smoke]', async () => {
    const page = new ApprovalListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const currentTab = await page.getCurrentTab();
    const list = await page.getApprovalList();
    console.log(`  当前 Tab: ${currentTab}, 列表数: ${list.length}`);
    expect(Array.isArray(list)).toBe(true);
  });

  test('各 Tab 切换与角标 [smoke]', async () => {
    // 使用已登录状态，直接导航到审批页
    const page = new ApprovalListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    // 获取各 Tab 角标
    const badges = await page.getTabBadges();
    console.log(`  角标: ${JSON.stringify(badges)}`);

    // 切换到各 Tab 验证
    const tabs = ['approved', 'rejected', 'my', 'pending'];
    for (const tab of tabs) {
      await page.switchTab(tab);
      const current = await page.getCurrentTab();
      expect(current).toBe(tab);

      const list = await page.getApprovalList();
      console.log(`  Tab "${tab}": 列表数=${list.length}`);
    }
  });

  test('审批列表数据合理性', async () => {
    const page = new ApprovalListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const badges = await page.getTabBadges();

    // 角标和非应大于等于0
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
    expect(detail).toBeTruthy();
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
