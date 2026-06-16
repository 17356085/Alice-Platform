const { MiniPage } = require('../MiniPage');

/**
 * 首页 — pages/index/index（TabBar 页）
 */
class HomePage extends MiniPage {
  static PAGE_PATH = '/pages/index/index';
  static IS_TAB_PAGE = true;

  /** 等待首页渲染 */
  async waitForContent(timeout = 15000) {
    // 首页用自定义菜单 grid 布局，等待任何展示容器
    await new Promise(r => setTimeout(r, 2000));
    try { await this.waitFor('view', timeout); } catch {}
  }

  /** 获取菜单分类列表（从 page data 读取） */
  async getMenuCategories() {
    const data = await this.getData();
    return data.g || data.menuCategories || [];
  }

  /** 获取所有菜单项名称列表 */
  async getAllMenuNames() {
    const categories = await this.getMenuCategories();
    const names = [];
    for (const cat of categories) {
      const items = cat.i || cat.items || [];
      for (const item of items) {
        names.push(item.f || item.name || '');
      }
    }
    return names.filter(Boolean);
  }

  /** 获取页面上的文本片段 */
  async getPageText() {
    try {
      const views = await this.$$('view, text');
      const texts = [];
      for (const v of views.slice(0, 20)) {
        try {
          const t = await v.text();
          if (t && t.trim()) texts.push(t.trim());
        } catch {}
      }
      return texts.join(' | ');
    } catch {
      return '';
    }
  }

  /** 检查首页是否正常渲染 */
  async isRendered() {
    const text = await this.getPageText();
    return text.length > 0;
  }
}

module.exports = { HomePage };
