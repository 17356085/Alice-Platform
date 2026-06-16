const { logger } = require('./utils/logger');
const { sleep } = require('./utils/helpers');

/**
 * 是否是可重试的 DevTools 超时错误
 */
function isRetryableTimeout(err) {
  const msg = (err && err.message) || '';
  return msg.includes('timeout');
}

/**
 * MiniPage — 小程序 Page Object 基类
 *
 * 封装 miniprogram-automator 的 Page 实例操作。
 * 每个子类对应一个小程序页面，提供该页面的业务操作接口。
 *
 * 内置 DevTools 超时重试：当操作返回 "timeout" 协议错误时自动重试（最多 3 次，每次间隔 2s）。
 *
 * 用法:
 *   class AlarmListPage extends MiniPage {
 *     static PAGE_PATH = 'pages/alarm/index';
 *     static IS_TAB_PAGE = true;
 *
 *     async waitForList() { ... }
 *     async getAlarmCount() { ... }
 *   }
 *
 *   const page = new AlarmListPage(driver.app);
 *   await page.navigate();
 *   const count = await page.getAlarmCount();
 */
class MiniPage {
  /**
   * 子类覆盖 — 页面路径（如 'pages/alarm/index'）
   * @type {string}
   */
  static PAGE_PATH = '';

  /**
   * 子类覆盖 — 是否为 TabBar 页面（Tab 页用 switchTab，否则 navigateTo）
   * @type {boolean}
   */
  static IS_TAB_PAGE = false;

  /**
   * @param {import('miniprogram-automator').MiniProgram} app
   */
  constructor(app) {
    this.app = app;
    this.path = this.constructor.PAGE_PATH;
    /** @type {import('miniprogram-automator').Page|null} */
    this._page = null;
    /** 重试次数 */
    this._maxRetries = 3;
    /** 重试间隔(ms) */
    this._retryDelay = 2000;
  }

  // ==================================================================
  //  内部：超时重试包装器
  // ==================================================================

  /**
   * 包装 automator 操作，遇到 "timeout" 错误自动重试
   * @param {Function} fn  异步操作函数
   * @param {number} [maxRetries]  最大重试次数（默认 3）
   * @param {string} [label]  日志标签
   */
  async _withRetry(fn, maxRetries = this._maxRetries, label = '') {
    let lastErr;
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await fn();
      } catch (err) {
        lastErr = err;
        if (!isRetryableTimeout(err)) throw err;
        if (i < maxRetries - 1) {
          const tag = label ? ` [${label}]` : '';
          logger.warn(`DevTools 超时，重试 ${i + 2}/${maxRetries}${tag}`);
          await sleep(this._retryDelay);
          // 重试前刷新 page 引用
          try { this._page = await this.app.currentPage(); } catch {}
        }
      }
    }
    throw lastErr;
  }

  // ==================================================================
  //  导航
  // ==================================================================

  /**
   * 导航到当前页面
   * @param {object} [query]  URL 查询参数，如 { id: 123 }
   */
  async navigate(query) {
    // 确保路径以 / 开头（automator 需要绝对路径）
    let url = this.path.startsWith('/') ? this.path : '/' + this.path;
    if (query) {
      const params = Object.entries(query)
        .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
        .join('&');
      url += `?${params}`;
    }

    logger.info(`导航到页面: ${url} (tab=${this.constructor.IS_TAB_PAGE})`);

    await this._withRetry(async () => {
      if (this.constructor.IS_TAB_PAGE) {
        await this.app.switchTab(url);
      } else {
        await this.app.navigateTo(url);
      }
    }, 4, 'navigate');  // 增加到 4 次重试，共 8s

    return this._waitPageReady();
  }

  /**
   * 重新启动到当前页面（reLaunch）
   */
  async reLaunch(query) {
    let url = this.path;
    if (query) {
      const params = Object.entries(query)
        .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
        .join('&');
      url += `?${params}`;
    }
    await this._withRetry(() => this.app.reLaunch(url), 2, 'reLaunch');
    return this._waitPageReady();
  }

  /** 返回上一页 */
  async navigateBack() {
    await this._withRetry(() => this.app.navigateBack(), 2, 'navigateBack');
  }

  // ==================================================================
  //  页面实例操作
  // ==================================================================

  /**
   * 获取当前 Page 实例（已打开页面自动更新）
   * @returns {Promise<import('miniprogram-automator').Page>}
   */
  async getPage() {
    this._page = await this._withRetry(() => this.app.currentPage(), 3, 'currentPage');
    return this._page;
  }

  /**
   * 获取页面 data（Vue 响应式数据快照）
   * @returns {Promise<object>}
   */
  async getData() {
    const page = await this.getPage();
    return page ? await this._withRetry(() => page.data(), 3, 'page.data') : {};
  }

  /**
   * 调用页面方法
   * @param {string}   methodName  方法名
   * @param {any[]}    args        参数数组
   * @returns {Promise<any>}
   */
  async callMethod(methodName, args = []) {
    const page = await this.getPage();
    if (!page) {
      throw new Error(`页面未打开: ${this.path}`);
    }
    logger.debug(`调用方法: ${methodName}(${JSON.stringify(args)})`);
    return this._withRetry(() => page.callMethod(methodName, args), 3, `callMethod:${methodName}`);
  }

  // ==================================================================
  //  元素查询
  // ==================================================================

  /**
   * 查询单个元素
   * @param {string} selector  如 '.alarm-item', '#btn-login'
   * @returns {Promise<import('miniprogram-automator').Element|null>}
   */
  async $(selector) {
    const page = await this.getPage();
    return page ? this._withRetry(() => page.$(selector), 2, `$:${selector}`) : null;
  }

  /**
   * 查询所有匹配元素
   * @param {string} selector
   * @returns {Promise<import('miniprogram-automator').Element[]>}
   */
  async $$(selector) {
    const page = await this.getPage();
    return page ? this._withRetry(() => page.$$(selector), 3, `$$:${selector}`) : [];
  }

  /**
   * 等待元素出现
   * @param {string} selector
   * @param {number} [timeout]  毫秒
   */
  async waitFor(selector, timeout = 10000) {
    const page = await this.getPage();
    if (page) {
      await this._withRetry(() => page.waitFor(selector, { timeout }), 3, `waitFor:${selector}`);
    }
  }

  // ==================================================================
  //  交互操作
  // ==================================================================

  /** 点击元素 */
  async tap(selector) {
    const el = await this.$(selector);
    if (el) {
      await this._withRetry(() => el.tap(), 3, `tap:${selector}`);
    } else {
      throw new Error(`未找到元素: ${selector}`);
    }
  }

  /** 输入文本 */
  async input(selector, text) {
    const el = await this.$(selector);
    if (el) {
      await this._withRetry(() => el.input(text), 3, `input`);
    } else {
      throw new Error(`未找到输入框: ${selector}`);
    }
  }

  /** 获取元素文本 */
  async text(selector) {
    const el = await this.$(selector);
    return el ? (await this._withRetry(() => el.text(), 3, `text`)) || '' : '';
  }

  /** 获取元素属性 */
  async attribute(selector, name) {
    const el = await this.$(selector);
    return el ? (await this._withRetry(() => el.attribute(name), 3, `attr:${name}`)) || '' : '';
  }

  // ==================================================================
  //  内部方法
  // ==================================================================

  /**
   * 等待页面就绪
   * @param {number} [timeout]  毫秒
   */
  async _waitPageReady(timeout = 30000) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      try {
        const page = await this.app.currentPage();
        if (page) {
          this._page = page;
          return;
        }
      } catch {
        // 页面还未加载
      }
      await sleep(300);
    }
    logger.warn(`页面加载超时: ${this.path}`);
  }

  /**
   * 等待页面数据加载完成（检测 loading 状态变化）
   * @param {number} [timeout]  毫秒
   */
  async waitForDataReady(timeout = 30000) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      const data = await this.getData();
      const loading = data.loading !== undefined ? data.loading
        : data.isLoading !== undefined ? data.isLoading
        : false;
      if (!loading) {
        return;
      }
      await sleep(500);
    }
    logger.warn(`数据加载超时: ${this.path}`);
  }
}

module.exports = { MiniPage };
