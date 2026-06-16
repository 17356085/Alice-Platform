/**
 * 登录流程测试 — P0 (TC-LOGIN-001 ~ 006)
 *
 * 覆盖: 登录页渲染、手机号登录（API注入）、退出登录
 */
const { MiniDriver } = require('../../src/driver');
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { LoginPage } = require('../../src/pages/login.page');
const { HomePage } = require('../../src/pages/home.page');
const { MinePage } = require('../../src/pages/mine.page');
const { config } = require('../../src/config/test.config');
const { sleep } = require('../../src/utils/helpers');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
}, 120000);

describe('登录页渲染 (TC-LOGIN-001)', () => {
  test('登录页正常渲染 [smoke]', async () => {
    const page = new LoginPage(driver.app);
    await page.navigate();
    await page.waitForReady();
    const isLogin = await page.isOnLoginPage();
    expect(isLogin).toBe(true);
  }, 30000);
});

describe('登录流程 (TC-LOGIN-002)', () => {
  test('API注入登录并渲染首页 [smoke]', async () => {
    const flow = new LoginFlow(driver.app);
    const result = await flow.bypassLogin(config.accounts.admin);
    expect(result.success).toBe(true);
  }, 60000);
});

describe('退出登录 (TC-LOGIN-006)', () => {
  test('退出登录 → 回到登录页 [smoke]', async () => {
    const flow = new LoginFlow(driver.app);
    const backToLogin = await flow.logout();
    expect(backToLogin).toBe(true);
  }, 30000);
});

describe('密码可见性切换 (TC-LOGIN-003)', () => {
  test('密码明文/密文切换', async () => {
    const page = new LoginPage(driver.app);
    await page.navigate();
    await page.waitForReady();

    // 先填入密码
    const p = await page.getPage();
    expect(p).toBeTruthy();
    await p.setData({ h: 'testPassword123' });
    await sleep(500);

    // 获取切换前的状态（密码输入框 type）
    const dataBefore = await page.getData();
    const isPwdHiddenBefore = dataBefore.e !== true; // e 可能是 showPwd 编译后 key
    console.log(`  密码隐藏状态(before): ${isPwdHiddenBefore}`);

    // 点击密码可见性切换按钮（编译后的方法名是 j）
    await page.callMethod('j');
    await sleep(500);

    const dataAfter = await page.getData();
    const isPwdHiddenAfter = dataAfter.e !== true;
    console.log(`  密码隐藏状态(after): ${isPwdHiddenAfter}`);

    // 切换后状态应翻转
    expect(isPwdHiddenAfter).not.toBe(isPwdHiddenBefore);
  });
});

describe('用户协议/隐私政策跳转 (TC-LOGIN-004, TC-LOGIN-005)', () => {
  test('点击用户协议跳转到用户协议页', async () => {
    const page = new LoginPage(driver.app);
    await page.navigate();
    await page.waitForReady();

    // 调用用户协议跳转方法
    await page.callMethod('o');
    await sleep(2000);

    // 验证当前页是用户协议页
    const current = await driver.app.currentPage();
    console.log(`  跳转后页面路径: ${current ? current.path : 'null'}`);
    expect(current).toBeTruthy();
    expect(current.path).toContain('user-agreement');
  });

  test('点击隐私政策跳转到隐私政策页', async () => {
    const page = new LoginPage(driver.app);
    await page.navigate();
    await page.waitForReady();

    // 调用隐私政策跳转方法
    await page.callMethod('p');
    await sleep(2000);

    // 验证当前页是隐私政策页
    const current = await driver.app.currentPage();
    console.log(`  跳转后页面路径: ${current ? current.path : 'null'}`);
    expect(current).toBeTruthy();
    expect(current.path).toContain('privacy-policy');
  });
});
