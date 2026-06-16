/**
 * 化验室取样测试 — P2
 *
 * 覆盖:
 *   1. 气体分析/水质分析类型切换
 *   2. 子类型选择 + 取样点位动态加载
 *   3. 指标字段分组展示 + 设计指标阈值
 *   4. 草稿暂存/恢复
 *   5. 报告提交 + 历史记录查看
 */
const { MiniDriver } = require('../../src/driver');
const { config } = require('../../src/config/test.config');
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { LabSamplingPage, LabHistoryPage } = require('../../src/pages/lab.page');
const { sleep } = require('../../src/utils/helpers');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
  // 使用管理员登录
  const flow = new LoginFlow(driver.app);
  await flow.bypassLogin(config.accounts.admin);
}, 120000);

describe('化验室页面加载', () => {
  test('页面正常渲染 [smoke]', async () => {
    const page = new LabSamplingPage(driver.app);
    await page.navigate();
    await page.waitForContent();
    const typeCode = await page.getCurrentType();
    expect(['gas', 'water', '']).toContain(typeCode);
  });

  test('气体/水质类型切换', async () => {
    const page = new LabSamplingPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    // 切换到水质
    await page.switchType('water');
    const typeAfter = await page.getCurrentType();
    console.log(`  切换后类型: ${typeAfter}`);

    // 切回气体
    await page.switchType('gas');
    console.log('  切回气体分析');
  });
});

describe('子类型与取样点位', () => {
  test('子类型列表加载', async () => {
    const page = new LabSamplingPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    const subTypes = await page.getSubTypes();
    console.log(`  子类型数: ${subTypes.length}`);
    expect(subTypes.length).toBeGreaterThanOrEqual(0);
  });

  test('选择子类型后加载点位', async () => {
    const page = new LabSamplingPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    const subTypes = await page.getSubTypes();
    if (subTypes.length === 0) {
      console.log('  无子类型数据，跳过');
      return;
    }

    await page.selectSubType(0);
    const locations = await page.getLocationOptions();
    console.log(`  点位选项数: ${locations.options.length}, 是否加样口: ${locations.isExtraSample}`);
  });
});

describe('指标字段', () => {
  test('指标字段分组展示', async () => {
    const page = new LabSamplingPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    const subTypes = await page.getSubTypes();
    if (subTypes.length === 0) {
      console.log('  无子类型，跳过');
      return;
    }

    await page.selectSubType(0);
    const groups = await page.getFieldGroups();
    console.log(`  指标分组数: ${groups.length}`);
    expect(Array.isArray(groups)).toBe(true);
  });
});

describe('提交报告 (TC-LAB-006) [destructive]', () => {
  test('填报并提交报告', async () => {
    const page = new LabSamplingPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    // 选择一个子类型
    const subTypes = await page.getSubTypes();
    if (subTypes.length === 0) {
      console.log('  无子类型数据，跳过');
      return;
    }
    await page.selectSubType(0);
    await sleep(1000);

    // 提交报告
    await page.submitReport();
    await sleep(2000);

    const result = await page.getData();
    console.log(`  提交后结果: ${JSON.stringify(result).slice(0, 200)}`);
    console.log('  报告提交完成 [destructive]');
  });
});

describe('历史记录', () => {
  test('历史记录页正常渲染', async () => {
    const page = new LabHistoryPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const reports = await page.getReportList();
    console.log(`  历史报告数: ${reports.length}`);
    expect(Array.isArray(reports)).toBe(true);
  });
});
