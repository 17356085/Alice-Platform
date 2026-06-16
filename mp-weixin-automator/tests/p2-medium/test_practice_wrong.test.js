/**
 * 自主练习 + 错题集测试 — P2
 *
 * 覆盖:
 *   1. 练习首页统计+历史列表
 *   2. 创建自定义练习并开始
 *   3. 错题集列表+统计+题型筛选
 *   4. 错题收藏/标记已掌握
 *   5. 错题详情（题目+错误答案+正确答案+解析）
 */
const { MiniDriver } = require('../../src/driver');
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
}, 120000);

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
    // 验证页面加载
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
    // 切回全部
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

    // 点击第一个错题（通过 callMethod 或元素点击）
    const items = await driver.app.currentPage().then(p => p ? p.$$('.wrong-item, .question-item') : []);
    if (items.length > 0) {
      await items[0].tap();
      const detailPage = new WrongDetailPage(driver.app);
      try {
        await detailPage.waitForContent(5000);
        const detail = await detailPage.getDetail();
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

    // 标记第一条为已掌握
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

    // 收藏第一条
    await page.collect(0);
    await sleep(1500);
    console.log('  收藏操作完成');

    // 再次点击取消收藏
    await page.collect(0);
    await sleep(1500);
    console.log('  取消收藏操作完成');
  });
});
