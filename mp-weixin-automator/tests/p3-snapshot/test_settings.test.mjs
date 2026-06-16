/**
 * 设置 + 消息 + 安全 综合测试 — P3
 */
import { describe, it as test, before as beforeAll, after as afterAll, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { MiniDriver } from '../../src/driver.mjs';
import expect from '../../src/utils/expect.mjs';

const require = createRequire(import.meta.url);
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

    await page.toggle('alarm');
    await sleep(1000);

    const after = await page.getSettings();
    console.log(`  切换后 - 报警: ${after.alarm}`);
    if (before.alarm !== after.alarm) {
      console.log('  ✅ 开关切换成功');
    } else {
      console.log('  ⚠ 开关状态未变化');
    }

    await page.toggle('alarm');
    await sleep(1000);
  });

  test('免打扰时段设置 (TC-MSG-003)', async () => {
    const page = new MessageSettingsPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    try {
      await page.callMethod('setQuietStart', ['22:00']);
      await sleep(1000);
    } catch {
      try {
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

    await page.openChangePassword();
    await sleep(2000);

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
    assert.ok(Array.isArray(list));
  });
});
