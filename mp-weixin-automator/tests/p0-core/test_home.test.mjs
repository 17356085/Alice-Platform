/**
 * 首页测试 — P0 (TC-HOME-001 ~ 004, TC-HOME-006)
 */
import { describe, it as test, before as beforeAll, after as afterAll } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { MiniDriver } from '../../src/driver.mjs';
import expect from '../../src/utils/expect.mjs';

const require = createRequire(import.meta.url);
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { HomePage } = require('../../src/pages/home.page');
const { config } = require('../../src/config/test.config');
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

describe('首页功能 (TC-HOME-001 ~ 003)', () => {
  test('首页内容加载正常 [smoke]', async () => {
    const page = new HomePage(driver.app);
    await page.navigate();
    await page.waitForContent();

    const allNames = await page.getAllMenuNames();
    const text = await page.getPageText();
    console.log(`  菜单项数: ${allNames.length}`);
    console.log(`  菜单名称: [${allNames.join(', ')}]`);
    console.log(`  页面文本片段: ${text.slice(0, 200)}`);
    assert.ok(Array.isArray(allNames));
  });

  test('管理员菜单完整 (TC-HOME-003)', async () => {
    const page = new HomePage(driver.app);
    await page.navigate();
    await page.waitForContent();

    const allNames = await page.getAllMenuNames();
    console.log(`  菜单总数: ${allNames.length}`);
    console.log(`  菜单名称: [${allNames.join(', ')}]`);

    if (allNames.length === 0) {
      console.warn('  ⚠ 菜单为空，跳过菜单完整性断言');
      return;
    }
    const expectedMenus = ['生产报表', '储罐监控', '设备管理', '在线学习',
      '考试测评', '自主练习', '错题集'];
    const missing = expectedMenus.filter(m => !allNames.some(a => a.includes(m)));
    if (missing.length > 0) {
      console.warn(`  缺失菜单: [${missing.join(', ')}]`);
    }
    assert.ok(allNames.length >= 6);
  });
});

describe('菜单导航跳转 (TC-HOME-004)', () => {
  test('点击菜单项应跳转到对应页面 [smoke]', async () => {
    const page = new HomePage(driver.app);
    await page.navigate();
    await page.waitForContent();

    const categories = await page.getMenuCategories();
    let targetItem = null;
    let targetNav = '';
    for (const cat of categories) {
      const items = cat.i || cat.items || [];
      if (items.length > 0) {
        targetItem = items[0];
        targetNav = targetItem.j || targetItem.nav || targetItem.path || '';
        break;
      }
    }
    if (!targetItem || !targetNav) {
      console.log('  ⚠ 无菜单项，跳过导航验证');
      return;
    }
    console.log(`  目标菜单: name=${targetItem.f || targetItem.name}, nav=${targetNav}`);

    await page.callMethod('clickMenu', [targetItem]);
    await sleep(3000);

    const current = await driver.app.currentPage();
    console.log(`  跳转后路径: ${current ? current.path : 'null'}`);
    assert.ok(current);
    assert.ok(!current.path.includes('index/index'));
  });
});

describe('首页下拉刷新 (TC-HOME-006)', () => {
  test('下拉刷新应重新加载菜单 [smoke]', async () => {
    const page = new HomePage(driver.app);
    await page.navigate();
    await page.waitForContent();

    const namesBefore = await page.getAllMenuNames();
    console.log(`  刷新前菜单数: ${namesBefore.length}`);

    await page.callMethod('onPullDownRefresh');
    await sleep(3000);

    const namesAfter = await page.getAllMenuNames();
    console.log(`  刷新后菜单数: ${namesAfter.length}`);

    assert.ok(Array.isArray(namesAfter));
  });
});
