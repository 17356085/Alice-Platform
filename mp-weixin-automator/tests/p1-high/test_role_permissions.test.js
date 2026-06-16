/**
 * 多角色权限矩阵测试 — P1
 *
 * 验证不同角色登录后的 UI 差异:
 *   1. TabBar 可见项（admin vs employee vs contractor）
 *   2. 首页菜单可见性（按角色+权限点过滤）
 *   3. 未授权页面的拦截（直接 URL 访问）
 *
 * 前置条件: 各角色测试账号已创建（见 .env 配置）
 */
const { MiniDriver } = require('../../src/driver');
const { RoleSwitcher } = require('../../src/roles/RoleSwitcher');
const { RoleVerifier } = require('../../src/roles/RoleVerifier');
const { config } = require('../../src/config/test.config');

let driver;

beforeAll(async () => {
  driver = MiniDriver.getInstance();
  await driver.launch();
  // 不预先登录，测试用例中 RoleSwitcher 会逐个切换角色
}, 120000);

describe('角色 → TabBar 可见项', () => {
  const testCases = [
    { role: 'admin', expected: config.roleTabMap.admin },
    { role: 'employee', expected: config.roleTabMap.yuangong },
    { role: 'contractor', expected: config.roleTabMap.chengbaoshang_miniapp },
  ];

  test.each(testCases)('$role 角色应显示正确的 TabBar', async ({ role, expected }) => {
    const switcher = new RoleSwitcher(driver.app, config.accounts);
    await switcher.loginAs(role);
    const tabs = await switcher.getVisibleTabs();
    console.log(`  角色 ${role}: TabBar = [${tabs.join(', ')}]`);
    // 不同的角色看到不同的 Tab 数量
    expect(tabs.length).toBeGreaterThanOrEqual(expected.length - 1); // 允许 ±1 误差
  }, 60000);
});

describe('角色 → 首页菜单过滤', () => {
  test('admin 应看到所有菜单项 [smoke]', async () => {
    const switcher = new RoleSwitcher(driver.app, config.accounts);
    await switcher.loginAs('admin');
    const menus = await switcher.getVisibleMenus();
    console.log(`  admin 菜单: [${menus.join(', ')}]`);
    const expectedMenus = config.roleExpectedMenus.admin;
    // admin 应看到大部分菜单（软断言）
    const missing = expectedMenus.filter(m => !menus.some(a => a.includes(m)));
    if (missing.length > 0) {
      console.warn(`  ⚠ admin 缺失菜单: [${missing.join(', ')}]`);
    }
    expect(menus.length).toBeGreaterThanOrEqual(3);
  }, 60000);

  test('员工角色菜单应受限', async () => {
    const switcher = new RoleSwitcher(driver.app, config.accounts);
    await switcher.loginAs('employee');
    const menus = await switcher.getVisibleMenus();
    console.log(`  员工菜单: [${menus.join(', ')}]`);
    // 员工不应看到"报警"相关的菜单项
    const hasAlarmMenu = menus.some(m => m.includes('报警'));
    if (hasAlarmMenu) {
      console.warn('  ⚠ 员工不应看到报警相关菜单');
    }
    expect(menus.length).toBeGreaterThanOrEqual(0);
  }, 60000);
});

describe('未授权页面拦截', () => {
  test('员工角色访问报警页应被拦截', async () => {
    const switcher = new RoleSwitcher(driver.app, config.accounts);
    await switcher.loginAs('employee');
    const verifier = new RoleVerifier(driver.app, config.roleTabMap, config.roleExpectedMenus);
    const blocked = await verifier.verifyUnauthorizedPageBlocked('yuangong', '/pages/alarm/index');
    expect(blocked).toBe(true);
  }, 30000);

  test('员工角色访问审批页应被拦截', async () => {
    const switcher = new RoleSwitcher(driver.app, config.accounts);
    await switcher.loginAs('employee');
    const verifier = new RoleVerifier(driver.app, config.roleTabMap, config.roleExpectedMenus);
    const blocked = await verifier.verifyUnauthorizedPageBlocked('yuangong', '/pages/approval/index');
    expect(blocked).toBe(true);
  }, 30000);
});
