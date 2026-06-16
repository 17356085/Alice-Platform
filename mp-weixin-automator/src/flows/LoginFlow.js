/**
 * LoginFlow — 登录鉴权业务流程编排
 */
const { LoginPage } = require('../pages/login.page');
const { HomePage } = require('../pages/home.page');
const { MinePage } = require('../pages/mine.page');
const { loginByApi } = require('../utils/apiLogin');
const { logger } = require('../utils/logger');
const { sleep } = require('../utils/helpers');

class LoginFlow {
  constructor(app) {
    this.app = app;
  }

  /**
   * 登录（超容错）
   */
  async bypassLogin(credentials) {
    logger.info('[LoginFlow] === 登录 ===');

    // 1. 已登录检测
    const homePage = new HomePage(this.app);
    for (let i = 0; i < 3; i++) {
      try { if (await homePage.isRendered()) { logger.info('[LoginFlow] ⏭ 已登录'); await this._clearStack(); return { success: true }; } } catch {}
      await sleep(1000);
    }

    // 2. API token 注入（静默）
    try {
      const tokens = await loginByApi(credentials.phone, credentials.password);
      await this.app.callWxMethod('setStorage', { key: 'access_token', data: tokens.accessToken });
    } catch {}

    // 3. UI 登录
    const result = await this.fullLogin(credentials);
    if (result.success) {
      await this._clearStack();
    }
    return result;
  }

  /** 清除导航栈，释放 webview，避免 "webview count limit exceed" */
  async _clearStack() {
    try {
      await this.app.reLaunch('/pages/index/index');
      await sleep(3000);
      logger.info('[LoginFlow] 导航栈已清除');
    } catch (e) {
      logger.warn(`[LoginFlow] 清除导航栈失败: ${e.message}`);
    }
  }

  /** UI 登录 */
  async fullLogin(credentials) {
    logger.info('[LoginFlow] UI登录...');

    // 检当前页，非登录页才导航
    let curPath = '';
    try { const cp = await this.app.currentPage(); curPath = cp ? cp.path : ''; } catch {}
    if (!curPath.includes('login')) {
      try { await new LoginPage(this.app).navigate(); } catch (e) { logger.warn(`navigate fail: ${e.message}`); }
    }

    // 填表 + 点击
    try {
      const lp = new LoginPage(this.app);
      await lp.waitForReady();
      await lp.loginByPhone(credentials.phone, credentials.password);
    } catch (e) { logger.warn(`login op fail: ${e.message}`); }

    // 轮询首页（最多 20s）
    const hp = new HomePage(this.app);
    for (let i = 0; i < 20; i++) {
      await sleep(1000);
      try { if (await hp.isRendered()) { logger.info(`✅ login ok (${i + 1}s)`); return { success: true }; } } catch {}
    }
    logger.warn('login timeout');
    return { success: false };
  }

  async verifyHomeMenus() {
    const homePage = new HomePage(this.app);
    await homePage.navigate();
    const data = await homePage.getData();
    const categories = data.g || data.menuCategories || [];
    return { menuCount: categories.length, categories: categories.map(c => c.d || '') };
  }

  async logout() {
    logger.info('[LoginFlow] 退出登录');
    const minePage = new MinePage(this.app);
    await minePage.navigate();
    await minePage.logout();
    const loginPage = new LoginPage(this.app);
    for (let i = 0; i < 15; i++) {
      await sleep(1000);
      try { if (await loginPage.isOnLoginPage()) { logger.info(`✅ logout (${i + 1}s)`); return true; } } catch {}
    }
    return false;
  }
}

module.exports = { LoginFlow };
