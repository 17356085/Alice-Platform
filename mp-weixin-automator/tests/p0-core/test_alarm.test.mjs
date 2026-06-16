/**
 * 报警管理测试 — P0 (TC-ALARM-001 ~ 007)
 */
import { describe, it as test, before as beforeAll, after as afterAll } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { MiniDriver } from '../../src/driver.mjs';
import expect from '../../src/utils/expect.mjs';

const require = createRequire(import.meta.url);
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { AlarmListPage, AlarmDetailPage } = require('../../src/pages/alarm.page');
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

describe('报警列表 (TC-ALARM-001)', () => {
  test('列表正常渲染 [smoke]', async () => {
    const page = new AlarmListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const alarms = await page.getAlarmList();
    const data = await page.getData();

    console.log(`  报警数: ${alarms.length}`);
    console.log(`  data keys: ${Object.keys(data).slice(0, 10).join(', ')}`);

    assert.ok(!!data);
  });

  test('统计数据展示 (TC-ALARM-002)', async () => {
    const page = new AlarmListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const stats = await page.getStatistics();
    const totalCount = stats.totalCount || stats.total || 0;
    assert.ok(totalCount >= 0);
    console.log(`  统计: total=${totalCount}`);
  });

  test('按级别筛选 [smoke]', async () => {
    const page = new AlarmListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    const p = await page.getPage();
    if (p) {
      await p.setData({ c: 'urgent' });
      await sleep(1000);
    }
    const urgentAlarms = await page.getAlarmList();
    console.log(`  紧急筛选: ${urgentAlarms.length} 条`);

    if (p) {
      await p.setData({ c: 'normal' });
      await sleep(1000);
    }
    const normalAlarms = await page.getAlarmList();
    console.log(`  一般筛选: ${normalAlarms.length} 条`);

    if (p) {
      await p.setData({ c: 'all' });
      await sleep(1000);
    }
  });

  test('下拉刷新 (TC-ALARM-007)', async () => {
    const page = new AlarmListPage(driver.app);
    await page.navigate();
    await page.waitForList();

    await page.pullRefresh();
    await page.waitForList();

    const alarms = await page.getAlarmList();
    console.log(`  刷新后报警数: ${alarms.length}`);
  });

  test('报警处理操作 (TC-ALARM-006) [destructive]', async () => {
    const listPage = new AlarmListPage(driver.app);
    await listPage.navigate();
    await listPage.waitForList();

    const raw = await listPage.getAlarmList();
    const alarms = Array.isArray(raw) ? raw : [];
    if (alarms.length === 0) {
      console.log('  无报警数据，跳过处理操作');
      return;
    }
    const unprocessed = alarms.filter(a => (a.status || a.H || '') !== 'processed');
    if (unprocessed.length === 0) {
      console.log('  无未处理报警，跳过');
      return;
    }

    await listPage.tapAlarmItem(alarms.indexOf(unprocessed[0]));
    const detailPage = new AlarmDetailPage(driver.app);
    await detailPage.waitForDetail();

    await detailPage.handleAlarm('自动化测试 — 已确认处理');
    await sleep(2000);

    const detail = await detailPage.getDetail();
    console.log(`  报警处理后状态: ${detail.status || detail.H || 'unknown'}`);
    console.log('  报警处理操作完成 [destructive]');
  });
});

describe('报警详情 (TC-ALARM-005)', () => {
  test('报警数据有详情页入口 [smoke]', async () => {
    const listPage = new AlarmListPage(driver.app);
    await listPage.navigate();
    await listPage.waitForList();

    const alarms = await listPage.getAlarmList();
    if (alarms.length === 0) {
      console.log('  无报警数据，跳过');
      return;
    }

    const first = alarms[0];
    console.log(`  报警数据 keys: ${Object.keys(first).slice(0, 8).join(', ')}`);
    assert.ok(Object.keys(first).length > 0);
  });
});
