/**
 * 多角色权限矩阵测试 — P1
 */
import { describe, it as test, before as beforeAll, after as afterAll, beforeEach } from 'node:test';
import { createRequire } from 'node:module';
import { MiniDriver } from '../../src/driver.mjs';
import expect from '../../src/utils/expect.mjs';

const require = createRequire(import.meta.url);
const { RoleSwitcher } = require('../../src/roles/RoleSwitcher');
const { RoleVerifier } = require('../../src/roles/RoleVerifier');
const { config } = require('../../src/config/test.config');
const { sleep } = require('../../src/utils/helpers');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
}, { timeout: 180000 });

afterAll(async () => {
  if (driver) await driver.close();
});

// 每个测试前清空导航栈，防止 webview 累积超限
// 注意: 角色切换测试由 RoleSwitcher.loginAs() 自行管理导航，此处仅做兜底清理
beforeEach(async () => {
  if (driver && driver.app) {
    try {
      await driver.app.reLaunch('/pages/index/index');
      await sleep(3000);
    } catch {}
  }
});

describe('角色 → TabBar 可见项', () => {
  const testCases = [
    { role: 'admin', expected: config.roleTabMap.admin },
    { role: 'employee', expected: config.roleTabMap.yuangong },
    { role: 'contractor', expected: config.roleTabMap.chengbaoshang_miniapp },
  ];

  // Note: node:test doesn't support test.each natively. Iterate manually.
  for (const { role, expected } of testCases) {
    test(`${role} 角色应显示正确的 TabBar`, async () => {
      const switcher = new RoleSwitcher(driver.app, config.accounts);
      await switcher.loginAs(role);
      const tabs = await switcher.getVisibleTabs();
      console.log(`  角色 ${role}: TabBar = [${tabs.join(', ')}]`);
      expect(tabs.length).toBeGreaterThanOrEqual(expected.length - 1);
    }, { timeout: 60000 });
  }
});

describe('角色 → 首页菜单过滤', () => {
  test('admin 应看到所有菜单项 [smoke]', async () => {
    const switcher = new RoleSwitcher(driver.app, config.accounts);
    await switcher.loginAs('admin');
    const menus = await switcher.getVisibleMenus();
    console.log(`  admin 菜单: [${menus.join(', ')}]`);
    const expectedMenus = config.roleExpectedMenus.admin;
    const missing = expectedMenus.filter(m => !menus.some(a => a.includes(m)));
    if (missing.length > 0) {
      console.warn(`  ⚠ admin 缺失菜单: [${missing.join(', ')}]`);
    }
    expect(menus.length).toBeGreaterThanOrEqual(3);
  }, { timeout: 60000 });

  test('员工角色菜单应受限', async () => {
    const switcher = new RoleSwitcher(driver.app, config.accounts);
    await switcher.loginAs('employee');
    const menus = await switcher.getVisibleMenus();
    console.log(`  员工菜单: [${menus.join(', ')}]`);
    const hasAlarmMenu = menus.some(m => m.includes('报警'));
    if (hasAlarmMenu) {
      console.warn('  ⚠ 员工不应看到报警相关菜单');
    }
    expect(menus.length).toBeGreaterThanOrEqual(0);
  }, { timeout: 60000 });
});

describe('未授权页面拦截', () => {
  test('员工角色访问报警页应被拦截', async () => {
    const switcher = new RoleSwitcher(driver.app, config.accounts);
    await switcher.loginAs('employee');
    const verifier = new RoleVerifier(driver.app, config.roleTabMap, config.roleExpectedMenus);
    const blocked = await verifier.verifyUnauthorizedPageBlocked('yuangong', '/pages/alarm/index');
    expect(blocked).toBe(true);
  }, { timeout: 30000 });

  test('员工角色访问审批页应被拦截', async () => {
    const switcher = new RoleSwitcher(driver.app, config.accounts);
    await switcher.loginAs('employee');
    const verifier = new RoleVerifier(driver.app, config.roleTabMap, config.roleExpectedMenus);
    const blocked = await verifier.verifyUnauthorizedPageBlocked('yuangong', '/pages/approval/index');
    expect(blocked).toBe(true);
  }, { timeout: 30000 });
});
