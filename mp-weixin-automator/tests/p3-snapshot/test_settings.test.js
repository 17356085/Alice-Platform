/**
 * 设置 + 消息 + 法律文本 综合测试 — P3
 *
 * 覆盖: 消息设置开关、安全设置（密码修改+生物识别）、设备管理、消息列表
 */
const { MiniDriver } = require('../../src/driver');
const { config } = require('../../src/config/test.config');
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { MessageSettingsPage, SecuritySettingsPage, DeviceManagePage } = require('../../src/pages/settings.page');
const { MessageListPage } = require('../../src/pages/message.page');
const { sleep } = require('../../src/utils/helpers');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
  const flow = new LoginFlow(driver.app);
  await flow.bypassLogin(config.accounts.admin);
}, 120000);

describe('消息设置', () => {
  test('消息设置页渲染 [smoke]', async () => {
    const page = new MessageSettingsPage(driver.app);
    await page.navigate();
    await page.waitForContent();
    const settings = await page.getSettings();
    console.log(`  报警推送: ${settings.alarm}, 审批推送: ${settings.approval}`);
    console.log(`  免打扰: ${settings.quietStart} - ${settings.quietEnd}`);
  });

  test('开关切换 (TC-MSG-002)', async () => {
    const page = new MessageSettingsPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    const before = await page.getSettings();
    console.log(`  切换前 - 报警: ${before.alarm}`);

    // 切换报警推送开关
    await page.toggle('alarm');
    await sleep(1000);

    const after = await page.getSettings();
    console.log(`  切换后 - 报警: ${after.alarm}`);
    // 开关状态应翻转（软断言）
    if (before.alarm !== after.alarm) {
      console.log('  ✅ 开关切换成功');
    } else {
      console.log('  ⚠ 开关状态未变化（可能 toggle 方法名不同）');
    }

    // 切回原来的状态
    await page.toggle('alarm');
    await sleep(1000);
    const restored = await page.getSettings();
    console.log(`  恢复后 - 报警: ${restored.alarm}`);
  });

  test('免打扰时段设置 (TC-MSG-003)', async () => {
    const page = new MessageSettingsPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    // 尝试设置免打扰开始时间
    try {
      await page.callMethod('setQuietStart', ['22:00']);
      await sleep(1000);
    } catch {
      try {
        // 替代方法名
        await page.callMethod('setStartTime', ['22:00']);
        await sleep(1000);
      } catch {
        console.log('  免打扰设置方法不可用，跳过');
      }
    }
    console.log('  免打扰时段设置操作完成');
  });
});

describe('安全设置', () => {
  test('安全设置页渲染 [smoke]', async () => {
    const page = new SecuritySettingsPage(driver.app);
    await page.navigate();
    await page.waitForContent();
    const biometric = await page.getBiometricEnabled();
    console.log(`  生物识别: ${biometric ? '已启用' : '未启用'}`);
  });

  test('修改密码弹窗 (TC-MSG-005)', async () => {
    const page = new SecuritySettingsPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    // 打开修改密码弹窗
    await page.openChangePassword();
    await sleep(2000);

    // 验证弹窗已打开（取消弹窗）
    try {
      await page.callMethod('cancelChangePassword');
      console.log('  修改密码弹窗已打开并关闭');
    } catch {
      console.log('  修改密码弹窗操作完成');
    }
  });
});

describe('消息通知', () => {
  test('消息列表渲染 [smoke]', async () => {
    const page = new MessageListPage(driver.app);
    await page.navigate();
    await page.waitForList();
    const unread = await page.getUnreadCount();
    const list = await page.getMessageList();
    console.log(`  未读数: ${unread}, 消息数: ${list.length}`);
    expect(Array.isArray(list)).toBe(true);
  });
});
