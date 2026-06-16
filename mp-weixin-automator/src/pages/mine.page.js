const { MiniPage } = require('../MiniPage');

/**
 * 我的页面 — pages/mine/index（TabBar 页）
 *
 * 编译后结构：
 *   <view class="logout-card" bindtap="{{A}}">退出登录</view>
 *   — 不是 button，是 view！
 */
class MinePage extends MiniPage {
  static PAGE_PATH = '/pages/mine/index';
  static IS_TAB_PAGE = true;

  async waitForContent(timeout = 10000) {
    try { await this.waitFor('.mine-page', timeout); } catch {}
  }

  /** 退出登录 — 点击 logout-card view */
  async logout() {
    await this.waitForContent();

    // 查找 class="logout-card" 的 view 元素
    try {
      const el = await this.$('.logout-card');
      if (el) {
        await el.tap();
        console.log('[Mine] 点击退出登录');
        await new Promise(r => setTimeout(r, 3000));
        return;
      }
    } catch (e) {
      console.log('[Mine] 点击 logout-card 失败:', e.message);
    }

    // fallback: 找任何含"退出"文本的元素
    try {
      const views = await this.$$('view, text');
      for (const v of views) {
        try {
          const t = await v.text();
          if (t && t.includes('退出')) {
            await v.tap();
            console.log('[Mine] 点击含"退出"的元素');
            break;
          }
        } catch {}
      }
    } catch (e) {
      console.log('[Mine] 未找到退出入口:', e.message);
    }
  }
}

module.exports = { MinePage };
