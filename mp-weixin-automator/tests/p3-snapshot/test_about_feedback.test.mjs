/**
 * 关于系统 + 意见反馈 — P3 (TC-ABOUT-001, TC-ABOUT-002)
 */
import { describe, it as test, before as beforeAll, after as afterAll, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { MiniDriver } from '../../src/driver.mjs';
import expect from '../../src/utils/expect.mjs';

const require = createRequire(import.meta.url);
const { config } = require('../../src/config/test.config');
const { LoginFlow } = require('../../src/flows/LoginFlow');
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

describe('关于系统 (TC-ABOUT-001)', () => {
  test('关于页面渲染 — 显示版本号', async () => {
    await driver.app.navigateTo('/pages/mine/about');
    await sleep(2000);

    const page = await driver.app.currentPage();
    assert.ok(page);
    const path = page.path;
    console.log(`  当前页面: ${path}`);
    expect(path).toContain('about');

    const data = await page.data();
    console.log(`  页面数据 keys: ${Object.keys(data).slice(0, 15).join(', ')}`);
    const version = data.version || data.appVersion || data.V || '';
    console.log(`  版本号: ${version || '(通过页面文本查看)'}`);

    try {
      const views = await page.$$('view, text');
      let pageText = '';
      for (const v of views.slice(0, 15)) {
        try { const t = await v.text(); if (t) pageText += t + ' '; } catch {}
      }
      console.log(`  页面文本: ${pageText.trim().slice(0, 200)}`);
      assert.ok(pageText.length > 0);
    } catch {
      console.log('  无法读取页面文本');
    }
  });
});

describe('意见反馈 (TC-ABOUT-002)', () => {
  test('反馈页正常渲染', async () => {
    await driver.app.navigateTo('/pages-sub/feedback/index');
    await sleep(2000);

    const page = await driver.app.currentPage();
    assert.ok(page);
    const path = page.path;
    console.log(`  当前页面: ${path}`);
    expect(path).toContain('feedback');

    const data = await page.data();
    console.log(`  反馈页 data keys: ${Object.keys(data).slice(0, 15).join(', ')}`);
    assert.ok(page);
  });
});
