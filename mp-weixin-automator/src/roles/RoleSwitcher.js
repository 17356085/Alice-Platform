/**
 * RoleSwitcher — 多角色账号切换器
 *
 * 支持在测试中快速切换不同角色账号，验证不同权限下的 UI 差异。
 * 使用 API 登录注入的方式切换角色（跳过了不稳定的 UI 登录操作）。
 *
 * 用法:
 *   const switcher = new RoleSwitcher(app, config.accounts);
 *   await switcher.loginAs('admin');     // 管理员
 *   await switcher.loginAs('yuangong');  // 员工
 */

const { LoginPage } = require('../pages/login.page');
const { MinePage } = require('../pages/mine.page');
const { HomePage } = require('../pages/home.page');
const { loginByApi, getUserInfoByApi } = require('../utils/apiLogin');
const { logger } = require('../utils/logger');
const { sleep } = require('../utils/helpers');

class RoleSwitcher {
  /**
   * @param {import('miniprogram-automator').MiniProgram} app
   * @param {object} accounts  — test.config.js 中的 accounts 对象
   */
  constructor(app, accounts) {
    this.app = app;
    this.accounts = accounts;
    this._currentRole = null;
  }

  /** 当前已登录的角色标识 */
  get currentRole() {
    return this._currentRole;
  }

  /**
   * 以指定角色登录（API 注入方式）
   * @param {string} roleKey  如 'admin', 'yuangong', 'manager'
   * @returns {Promise<void>}
   */
  async loginAs(roleKey) {
    const account = this.accounts[roleKey];
    if (!account) {
      throw new Error(`未知角色: ${roleKey}。可用角色: ${Object.keys(this.accounts).join(', ')}`);
    }

    if (this._currentRole === roleKey) {
      logger.info(`[RoleSwitcher] 已是角色 ${roleKey}，跳过`);
      return;
    }

    logger.info(`[RoleSwitcher] 切换到角色: ${roleKey} (${account.description})`);

    // HTTP API 获取 Token
    const tokens = await loginByApi(account.phone, account.password);
    let userInfo = tokens.userInfo;
    if (!userInfo) {
      try { userInfo = await getUserInfoByApi(tokens.accessToken); } catch {}
    }

    // 注入存储
    try {
      await this.app.callWxMethod('setStorage', { key: 'access_token', data: tokens.accessToken });
      await this.app.callWxMethod('setStorage', { key: 'refresh_token', data: tokens.refreshToken || '' });
      if (userInfo) {
        await this.app.callWxMethod('setStorage', { key: 'user_info', data: JSON.stringify(userInfo) });
      }
    } catch (err) {
      logger.warn(`[RoleSwitcher] 存储注入失败: ${err.message}`);
    }

    // 更新 Pinia Store
    try {
      await this.app.evaluate(function(token, refreshToken, info) {
        try {
          const { useUserStore } = require('./store/user');
          const store = useUserStore();
          store.token = token;
          store.refreshToken = refreshToken;
          store.userInfo = info;
        } catch (e) {
          console.warn('[RoleSwitcher] evaluate更新store失败:', e.message);
        }
      }, tokens.accessToken, tokens.refreshToken || '', userInfo);
    } catch {}

    // 导航到首页（用 reLaunch 确保页面重新加载，读取最新 token）
    try {
      await this.app.reLaunch('/pages/index/index');
      await sleep(3000);
    } catch (err) {
      logger.warn(`[RoleSwitcher] 导航失败: ${err.message}`);
    }

    this._currentRole = roleKey;
    logger.info(`[RoleSwitcher] ✅ 角色 ${roleKey} 登录完成`);
  }

  /**
   * 切换角色
   * @param {string} roleKey
   */
  async switchTo(roleKey) {
    return this.loginAs(roleKey);
  }

  /**
   * 获取当前可见的 TabBar 项
   * @returns {Promise<string[]>}
   */
  async getVisibleTabs() {
    const page = await this.app.currentPage();
    if (!page) return [];
    try {
      const tabs = await page.callMethod('getTabBarConfig');
      return Array.isArray(tabs)
        ? tabs.map(t => t.pagePath).filter(Boolean)
        : [];
    } catch {
      const data = await page.data();
      return data.tabList || data.tabBarList || [];
    }
  }

  /**
   * 获取首页菜单项列表
   * @returns {Promise<string[]>} 菜单名称列表
   */
  async getVisibleMenus() {
    const homePage = new HomePage(this.app);
    await homePage.navigate();
    const data = await homePage.getData();
    const categories = data.g || data.menuCategories || [];
    const menuNames = [];
    for (const cat of categories) {
      const items = cat.i || cat.items || [];
      for (const item of items) {
        menuNames.push(item.f || item.name || '');
      }
    }
    return menuNames.filter(Boolean);
  }
}

module.exports = { RoleSwitcher };

