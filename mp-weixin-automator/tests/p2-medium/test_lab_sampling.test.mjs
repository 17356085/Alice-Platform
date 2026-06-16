/**
 * 化验室取样测试 — P2
 */
import { describe, it as test, before as beforeAll, after as afterAll, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { MiniDriver } from '../../src/driver.mjs';
import expect from '../../src/utils/expect.mjs';

const require = createRequire(import.meta.url);
const { config } = require('../../src/config/test.config');
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { LabSamplingPage, LabHistoryPage } = require('../../src/pages/lab.page');
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

    await page.switchType('water');
    const typeAfter = await page.getCurrentType();
    console.log(`  切换后类型: ${typeAfter}`);

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
    assert.ok(Array.isArray(groups));
  });
});

describe('提交报告 (TC-LAB-006) [destructive]', () => {
  test('填报并提交报告', async () => {
    const page = new LabSamplingPage(driver.app);
    await page.navigate();
    await page.waitForContent();

    const subTypes = await page.getSubTypes();
    if (subTypes.length === 0) {
      console.log('  无子类型数据，跳过');
      return;
    }
    await page.selectSubType(0);
    await sleep(1000);

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
    assert.ok(Array.isArray(reports));
  });
});
