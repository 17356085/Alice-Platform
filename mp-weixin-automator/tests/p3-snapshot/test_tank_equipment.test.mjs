/**
 * 储罐 + 设备 + 传感器 + 摄像头 — P3
 */
import { describe, it as test, before as beforeAll, after as afterAll, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { MiniDriver } from '../../src/driver.mjs';
import expect from '../../src/utils/expect.mjs';

const require = createRequire(import.meta.url);
const { config } = require('../../src/config/test.config');
const { LoginFlow } = require('../../src/flows/LoginFlow');
const { TankListPage, TankDetailPage } = require('../../src/pages/tank.page');
const { EquipmentListPage } = require('../../src/pages/equipment.page');
const { SensorListPage } = require('../../src/pages/sensor.page');
const { CameraListPage } = require('../../src/pages/camera.page');
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

describe('储罐管理', () => {
  test('储罐列表渲染 [smoke]', async () => {
    const page = new TankListPage(driver.app);
    await page.navigate();
    await page.waitForList();
    const list = await page.getTankList();
    console.log(`  储罐数: ${list.length}`);
    assert.ok(Array.isArray(list));
  });
});

describe('设备管理', () => {
  test('设备列表渲染 [smoke]', async () => {
    const page = new EquipmentListPage(driver.app);
    await page.navigate();
    await page.waitForList();
    const stats = await page.getStatistics();
    const list = await page.getDeviceList();
    console.log(`  设备统计: ${JSON.stringify(stats)}`);
    console.log(`  设备数: ${list.length}`);
    assert.ok(Array.isArray(list));
  });
});

describe('传感器管理', () => {
  test('传感器列表渲染 [smoke]', async () => {
    const page = new SensorListPage(driver.app);
    await page.navigate();
    await page.waitForList();
    const stats = await page.getStatistics();
    console.log(`  传感器统计: ${JSON.stringify(stats)}`);
    expect(typeof stats.total).toBe('number');
  });
});

describe('摄像头管理', () => {
  test('摄像头列表渲染 [smoke]', async () => {
    const page = new CameraListPage(driver.app);
    await page.navigate();
    await page.waitForList();
    const areas = await page.getAreas();
    const list = await page.getCameraList();
    console.log(`  区域数: ${areas.length}, 摄像头数: ${list.length}`);
    assert.ok(Array.isArray(list));
  });
});
