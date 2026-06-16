/**
 * 冒烟测试 — 每次提交必跑，目标 < 5 分钟
 *
 * 覆盖: 启动→API登录注入→首页渲染→Tab切换→退出
 */
const { MiniDriver } = require('../../src/driver');
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { config } = require('../../src/config/test.config');
const { HomePage } = require('../../src/pages/home.page');
const { ApprovalListPage } = require('../../src/pages/approval.page');
const { LoginPage } = require('../../src/pages/login.page');
const { sleep } = require('../../src/utils/helpers');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
}, 120000);

describe('冒烟: 登录 → 首页 → 核心Tab → 退出', () => {
  test('API注入登录并渲染首页 [smoke]', async () => {
    const flow = new LoginFlow(driver.app);
    const result = await flow.bypassLogin(config.accounts.admin);
    expect(result.success).toBe(true);
  }, 60000);

  test('首页菜单加载正常 [smoke]', async () => {
    const page = new HomePage(driver.app);
    await page.navigate();
    await page.waitForContent();
    const rendered = await page.isRendered();
    expect(rendered).toBe(true);
  }, 30000);

  test('审批Tab可切换 [smoke]', async () => {
    const page = new ApprovalListPage(driver.app);
    await page.navigate();
    await page.waitForList(30000);
    const list = await page.getApprovalList();
    console.log(`  审批列表数: ${list ? list.length : 'null'}`);
    expect(Array.isArray(list)).toBe(true);
  }, 60000);

  test('退出登录回到登录页 [smoke]', async () => {
    const flow = new LoginFlow(driver.app);
    const backToLogin = await flow.logout();
    expect(backToLogin).toBe(true);
  }, 30000);
});
