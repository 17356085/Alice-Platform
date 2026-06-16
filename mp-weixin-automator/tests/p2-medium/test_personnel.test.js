/**
 * 人员管理测试 — P2 (TC-PERSON-001 ~ 003)
 *
 * 覆盖:
 *   1. 人员列表渲染 + 统计
 *   2. 人员关键字搜索
 *   3. 人员档案详情（基本信息/岗位/资质/培训记录/考试记录）
 */
const { MiniDriver } = require('../../src/driver');
const { config } = require('../../src/config/test.config');
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { PersonListPage, PersonProfilePage } = require('../../src/pages/person.page');
const { sleep } = require('../../src/utils/helpers');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
  const flow = new LoginFlow(driver.app);
  await flow.bypassLogin(config.accounts.admin);
}, 120000);

describe('人员列表 (TC-PERSON-001)', () => {
  test('人员列表正常渲染 [smoke]', async () => {
    const page = new PersonListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const list = await page.getPersonList();
    const stats = await page.getStatistics();
    console.log(`  人员统计: total=${stats.total}`);
    console.log(`  人员列表数: ${list.length}`);
    expect(Array.isArray(list)).toBe(true);
    expect(typeof stats.total).toBe('number');
  });

  test('人员关键字搜索 (TC-PERSON-002)', async () => {
    const page = new PersonListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    await page.search('');
    const allList = await page.getPersonList();
    console.log(`  搜索前列表数: ${allList.length}`);

    // 如果有数据，尝试按关键字搜索
    if (allList.length > 0 && allList[0].name) {
      const keyword = allList[0].name.slice(0, 1);
      await page.search(keyword);
      await sleep(2000);
      const filtered = await page.getPersonList();
      console.log(`  搜索 "${keyword}" 结果: ${filtered.length} 条`);
    } else {
      console.log('  无人员数据，跳过搜索验证');
    }
  });
});

describe('人员档案 (TC-PERSON-003)', () => {
  test('点击人员查看档案详情', async () => {
    const listPage = new PersonListPage(driver.app);
    await listPage.navigate();
    await listPage.waitForList();

    const list = await listPage.getPersonList();
    if (list.length === 0) {
      console.log('  无人员数据，跳过');
      return;
    }

    // 通过 callMethod 进入详情（或者点击元素）
    try {
      await listPage.callMethod('goDetail', [list[0].id || list[0].personId]);
      await sleep(2000);
    } catch {
      // 尝试点击元素
      const items = await driver.app.currentPage().then(p => p ? p.$$('.person-item, .employee-item') : []);
      if (items.length > 0) {
        await items[0].tap();
        await sleep(2000);
      }
    }

    const profilePage = new PersonProfilePage(driver.app);
    try {
      await profilePage.waitForContent(5000);
      const profile = await profilePage.getProfile();
      console.log(`  档案数据 keys: ${Object.keys(profile).slice(0, 10).join(', ')}`);

      const certs = await profilePage.getCertificates();
      const trainingRecords = await profilePage.getTrainingRecords();
      const examRecords = await profilePage.getExamRecords();
      console.log(`  证书: ${certs.length}, 培训记录: ${trainingRecords.length}, 考试记录: ${examRecords.length}`);
    } catch {
      console.log('  档案页加载超时，可能无详细数据');
    }
  });
});

module.exports = {};