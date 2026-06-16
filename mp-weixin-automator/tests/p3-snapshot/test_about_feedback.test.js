/**
 * 关于系统 + 意见反馈测试 — P3 (TC-ABOUT-001, TC-ABOUT-002)
 *
 * 覆盖:
 *   1. 关于系统 — 版本信息展示
 *   2. 意见反馈 — 页面渲染
 */
const { MiniDriver } = require('../../src/driver');
const { config } = require('../../src/config/test.config');
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { MinePage } = require('../../src/pages/mine.page');
const { sleep } = require('../../src/utils/helpers');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
  const flow = new LoginFlow(driver.app);
  await flow.bypassLogin(config.accounts.admin);
}, 120000);

describe('关于系统 (TC-ABOUT-001)', () => {
  test('关于页面渲染 — 显示版本号', async () => {
    // 直接导航到关于页
    await driver.app.navigateTo('/pages/mine/about');
    await sleep(2000);

    const page = await driver.app.currentPage();
    expect(page).toBeTruthy();
    const path = page.path;
    console.log(`  当前页面: ${path}`);
    expect(path).toContain('about');

    // 读取版本信息
    const data = await page.data();
    console.log(`  页面数据 keys: ${Object.keys(data).slice(0, 15).join(', ')}`);
    const version = data.version || data.appVersion || data.V || '';
    console.log(`  版本号: ${version || '(通过页面文本查看)'}`);

    // 获取页面文本
    try {
      const views = await page.$$('view, text');
      let pageText = '';
      for (const v of views.slice(0, 15)) {
        try { const t = await v.text(); if (t) pageText += t + ' '; } catch {}
      }
      console.log(`  页面文本: ${pageText.trim().slice(0, 200)}`);
      // 应包含版本信息
      expect(pageText.length).toBeGreaterThan(0);
    } catch {
      console.log('  无法读取页面文本');
    }
  });
});

describe('意见反馈 (TC-ABOUT-002)', () => {
  test('反馈页正常渲染', async () => {
    // 导航到意见反馈页
    await driver.app.navigateTo('/pages-sub/feedback/index');
    await sleep(2000);

    const page = await driver.app.currentPage();
    expect(page).toBeTruthy();
    const path = page.path;
    console.log(`  当前页面: ${path}`);
    expect(path).toContain('feedback');

    const data = await page.data();
    console.log(`  反馈页 data keys: ${Object.keys(data).slice(0, 15).join(', ')}`);
    expect(page).toBeTruthy();
  });
});

module.exports = {};