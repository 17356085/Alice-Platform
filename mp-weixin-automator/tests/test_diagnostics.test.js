/**
 * 诊断脚本 — 不跑断言，只打印当前页面结构用于调试
 */
const { MiniDriver } = require('../src/driver');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
}, 120000);

test('诊断：首页 data 结构', async () => {
  const app = driver.app;
  const page = await app.currentPage();
  if (!page) { console.log('页面未加载'); return; }

  console.log('\n=== 当前页面路径 ===');
  console.log(page.path);

  console.log('\n=== 页面 data（前 30 个 key，每行 1 个，截断长值） ===');
  const data = await page.data();
  const keys = Object.keys(data);
  console.log(`共 ${keys.length} 个 data 字段`);
  for (const k of keys.slice(0, 40)) {
    const v = JSON.stringify(data[k]);
    const short = v.length > 120 ? v.slice(0, 120) + '...' : v;
    console.log(`  ${k} = ${short}`);
  }

  console.log('\n=== 页面顶层元素（标签 + class） ===');
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
}, 30000);

test('诊断：跳转到登录页', async () => {
  const app = driver.app;
  await app.navigateTo('/pages/login/index');
  await new Promise(r => setTimeout(r, 2000));

  const page = await app.currentPage();
  console.log('\n=== 登录页 data ===');
  const data = await page.data();
  const keys = Object.keys(data);
  for (const k of keys.slice(0, 25)) {
    const v = JSON.stringify(data[k]);
    const short = v.length > 120 ? v.slice(0, 120) + '...' : v;
    console.log(`  ${k} = ${short}`);
  }
}, 30000);
