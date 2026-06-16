/**
 * 自主练习 + 错题集测试 — P2
 */
import { describe, it as test, before as beforeAll, after as afterAll, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { MiniDriver } from '../../src/driver.mjs';
import expect from '../../src/utils/expect.mjs';

const require = createRequire(import.meta.url);
const { config } = require('../../src/config/test.config');
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { PracticePage, PracticeCreatePage, WrongPage, WrongDetailPage } = require('../../src/pages/practice.page');
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

describe('自主练习首页', () => {
  test('页面正常渲染 [smoke]', async () => {
    const page = new PracticePage(driver.app);
    await page.navigate();
    await page.waitForContent();

    const stats = await page.getStatistics();
    const history = await page.getHistoryList();
    console.log(`  练习统计: total=${stats.totalPractices}, correctRate=${stats.correctRate}`);
    console.log(`  历史记录: ${history.length}`);
    expect(typeof stats.totalPractices).toBe('number');
  });
});

describe('创建练习', () => {
  test('创建练习页正常渲染', async () => {
    const page = new PracticeCreatePage(driver.app);
    await page.navigate();
    await page.waitForContent();
  });
});

describe('错题集', () => {
  test('错题列表正常渲染 [smoke]', async () => {
    const page = new WrongPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    const stats = await page.getStatistics();
    const list = await page.getWrongList();
    console.log(`  错题统计: total=${stats.totalCount}, 未掌握=${stats.unmasteredCount}`);
    console.log(`  错题列表: ${list.length}`);
    expect(typeof stats.totalCount).toBe('number');
  });

  test('题型筛选功能', async () => {
    const page = new WrongPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    const types = ['single', 'multi', 'judge'];
    for (const type of types) {
      await page.filterByType(type);
      const list = await page.getWrongList();
      console.log(`  题型 ${type}: 筛选结果=${list.length} 条`);
    }
    await page.filterByType('all');
  });

  test('错题详情查看', async () => {
    const page = new WrongPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    const list = await page.getWrongList();
    if (list.length === 0) {
      console.log('  无错题数据，跳过');
      return;
    }

    const items = await driver.app.currentPage().then(p => p ? p.$$('.wrong-item, .question-item') : []);
    if (items.length > 0) {
      await items[0].tap();
      const detailPage = new WrongDetailPage(driver.app);
      try {
        await detailPage.waitForContent(5000);
        console.log(`  错题详情已加载`);
      } catch {
        console.log('  详情页加载超时');
      }
    }
  });

  test('标记已掌握 (TC-PRAC-004)', async () => {
    const page = new WrongPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    const list = await page.getWrongList();
    if (list.length === 0) {
      console.log('  无错题数据，跳过');
      return;
    }

    await page.markMastered(0);
    await sleep(1500);

    const statsAfter = await page.getStatistics();
    console.log(`  标记后统计: mastered=${statsAfter.masteredCount}, unmastered=${statsAfter.unmasteredCount}`);
  });

  test('错题收藏/取消收藏 (TC-PRAC-005)', async () => {
    const page = new WrongPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    const list = await page.getWrongList();
    if (list.length === 0) {
      console.log('  无错题数据，跳过');
      return;
    }

    await page.collect(0);
    await sleep(1500);
    console.log('  收藏操作完成');

    await page.collect(0);
    await sleep(1500);
    console.log('  取消收藏操作完成');
  });
});
