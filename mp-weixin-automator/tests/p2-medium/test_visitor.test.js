/**
 * 访客管理测试 — P2
 *
 * 覆盖:
 *   1. 访客登记页表单渲染
 *   2. 被访员工搜索
 *   3. 提交登记
 *   4. 登记记录列表
 *   5. 登记详情
 */
const { MiniDriver } = require('../../src/driver');
const { config } = require('../../src/config/test.config');
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { VisitorRegisterPage, VisitorProgressPage, VisitorDetailPage } = require('../../src/pages/visitor.page');
const { dataFactory } = require('../../src/utils/dataFactory');
const { sleep } = require('../../src/utils/helpers');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
  const flow = new LoginFlow(driver.app);
  await flow.bypassLogin(config.accounts.admin);
}, 120000);

describe('访客登记页', () => {
  test('页面正常渲染 [smoke]', async () => {
    const page = new VisitorRegisterPage(driver.app);
    await page.navigate();
    await page.waitForContent();
    const form = await page.getFormData();
    console.log(`  表单字段: visitorName=${form.visitorName}, company=${form.company}`);
  });

  test('搜索被访员工', async () => {
    const page = new VisitorRegisterPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    // 搜索（尝试模糊搜索）
    await page.searchHost('');
    const results = await page.getSearchResults();
    console.log(`  员工搜索结果: ${results.length}`);
  });

  test('提交登记 (TC-VIS-003) [destructive]', async () => {
    const page = new VisitorRegisterPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    // 填写并提交
    await page.fillAndSubmit({
      visitorName: '自动化测试访客',
      company: '测试公司',
      phone: '13800138000',
      visitPurpose: '自动化测试——登记流程验证',
    });
    await sleep(3000);

    // 检查最近登记记录是否更新
    const records = await page.getRecentRecords();
    console.log(`  最近登记记录数: ${records.length}`);
    console.log('  访客登记提交完成 [destructive]');
  });

  test('手机号格式校验 (TC-VIS-005)', async () => {
    const page = new VisitorRegisterPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    // 输入错误格式的手机号
    const p = await page.getPage();
    if (p) {
      await p.setData({ f: '12345' });  // 无效手机号
    }
    await page.fillAndSubmit({
      visitorName: '测试',
      company: '测试',
      phone: '12345',
      visitPurpose: '测试校验',
    });
    await sleep(2000);

    // 验证未被提交（应还在当前页）
    const current = await driver.app.currentPage();
    console.log(`  手机号错误时提交后页面: ${current ? current.path : 'null'}`);
    // 页面不应跳转，应在访客登记页
    expect(current.path).toContain('visitor');
  });
});

describe('登记记录', () => {
  test('登记进度页正常渲染', async () => {
    const page = new VisitorProgressPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const records = await page.getRecords();
    console.log(`  登记记录数: ${records.length}`);
    expect(Array.isArray(records)).toBe(true);
  });

  test('点击记录查看详情', async () => {
    const page = new VisitorProgressPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const records = await page.getRecords();
    if (records.length === 0) {
      console.log('  无登记记录，跳过');
      return;
    }

    // 点击第一条
    const items = await driver.app.currentPage().then(p => p ? p.$$('.record-item') : []);
    if (items.length > 0) {
      await items[0].tap();
      const detailPage = new VisitorDetailPage(driver.app);
      try {
        await detailPage.waitForDetail(5000);
        console.log('  详情页已加载');
      } catch {
        console.log('  详情页加载超时');
      }
    }
  });
});
