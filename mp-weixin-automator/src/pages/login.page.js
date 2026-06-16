const { MiniPage } = require('../MiniPage');

/**
 * 登录页 — pages/login/index
 *
 * 编译后 data 映射:
 *   {{d}} = phone 值,  {{h}} = password 值
 *   bindtap="{{l}}" = 登录提交方法
 *   bindtap="{{j}}" = 密码可见性切换
 *   bindtap="{{o}}/{{p}}" = 用户协议/隐私政策链接
 */
class LoginPage extends MiniPage {
  static PAGE_PATH = '/pages/login/index';

  async waitForReady(timeout = 15000) {
    try { await this.waitFor('.login-page', timeout); } catch {}
  }

  async isOnLoginPage() {
    try {
      // 查看是否有登录表单特有的元素
      const data = await this.getData();
      // 'd' 是 phone, 'h' 是 password — 这两个 key 同时存在说明在登录页
      return typeof data.d === 'string' && typeof data.h === 'string';
    } catch {
      return false;
    }
  }

  /**
   * 手机号 + 密码登录
   */
  async loginByPhone(phone, password) {
    console.log(`[Login] 登录: ${phone}`);

    // 等待 login 页面就绪
    await this.waitForReady(15000);

    // 填表 + 点击（容忍 getPage 超时）
    let page;
    for (let i = 0; i < 5; i++) {
      try {
        page = await this.app.currentPage();
        if (page) break;
      } catch {}
      await new Promise(r => setTimeout(r, 2000));
    }

    if (page) {
      try { await page.setData({ d: phone, h: password, n: true }); } catch {}
      console.log('[Login] 已填入并勾选');
      await new Promise(r => setTimeout(r, 500));
    }

    // 点击登录按钮
    try {
      const buttons = await page.$$('button');
      for (const btn of buttons) {
        try {
          const text = await btn.text();
          if (text && (text.includes('登录') || text.includes('Login'))) {
            await btn.tap();
            console.log('[Login] 已点击登录按钮');
            break;
          }
        } catch {}
      }
    } catch (e) {
      console.log('[Login] 点击按钮失败:', e.message);
    }

    // 等待跳转
    await new Promise(r => setTimeout(r, 3000));
  }
}

module.exports = { LoginPage };
