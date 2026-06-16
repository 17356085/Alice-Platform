/**
 * 诊断脚本 — 不跑断言，只打印当前页面结构用于调试
 */
import { describe, it as test, before as beforeAll, after as afterAll } from 'node:test';
import { createRequire } from 'node:module';
import { MiniDriver } from '../src/driver.mjs';

const require = createRequire(import.meta.url);
const { config } = require('../src/config/test.config');
const { LoginFlow } = require('../src/flows/LoginFlow');
const { sleep } = require('../src/utils/helpers');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
  // 登录以便诊断页面能看到实际数据
  const flow = new LoginFlow(driver.app);
  await flow.bypassLogin(config.accounts.admin);
}, { timeout: 180000 });

afterAll(async () => {
  if (driver) await driver.close();
});

test('诊断：首页 data 结构', async () => {
  const app = driver.app;
  const page = await app.currentPage();
  if (!page) { console.log('页面未加载'); return; }

  console.log('\n=== 当前页面路径 ===');
  console.log(page.path);

  console.log('\n=== 页面 data（前 30 个 key） ===');
  const data = await page.data();
  const keys = Object.keys(data);
  console.log(`共 ${keys.length} 个 data 字段`);
  for (const k of keys.slice(0, 40)) {
    const v = JSON.stringify(data[k]);
    const short = v.length > 120 ? v.slice(0, 120) + '...' : v;
    console.log(`  ${k} = ${short}`);
  }

  console.log('\n=== 页面顶层元素 ===');
  try {
    const topEls = await page.$$('view, navigator, text, button, input, image, scroll-view, swiper');
    for (const el of topEls.slice(0, 30)) {
      try {
        const tag = await el.tagName();
        const cls = await el.attribute('class');
        console.log(`  <${tag}> .${cls || '(none)'}`);
      } catch {}
    }
  } catch (e) {
    console.log('元素扫描失败:', e.message);
  }
}, { timeout: 30000 });

test('诊断：跳转到登录页', async () => {
  const app = driver.app;
  await app.navigateTo('/pages/login/index');
  await sleep(2000);

  const page = await app.currentPage();
  console.log('\n=== 登录页 data ===');
  const data = await page.data();
  const keys = Object.keys(data);
  for (const k of keys.slice(0, 25)) {
    const v = JSON.stringify(data[k]);
    const short = v.length > 120 ? v.slice(0, 120) + '...' : v;
    console.log(`  ${k} = ${short}`);
  }
}, { timeout: 30000 });
