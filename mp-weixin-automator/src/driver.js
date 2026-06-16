const path = require('path');
const fs = require('fs');

require('dotenv').config({ path: path.resolve(__dirname, '..', '.env') });

/**
 * MiniDriver — 微信小程序自动化连接管理（单例）
 *
 * 连接已开启自动化的微信开发者工具实例。
 * 前置条件：
 *   1. 微信开发者工具已启动
 *   2. 设置 → 安全 → 服务端口已开启
 *   3. 小程序项目已打开
 *   4. 自动化已启用: cli.bat auto --project <path>
 */
class MiniDriver {
  static _instance = null;
  app = null;
  _connected = false;

  constructor() {}

  static getInstance() {
    if (!MiniDriver._instance) {
      MiniDriver._instance = new MiniDriver();
    }
    return MiniDriver._instance;
  }

  get isConnected() {
    return this._connected && this.app !== null;
  }

  async launch(opts = {}) {
    if (this._connected) {
      console.log('[MiniDriver] 已有连接，复用实例');
      return this.app;
    }

    const projectPath = path.resolve(
      __dirname, '..',
      opts.projectPath || process.env.MINI_PROJECT_PATH || '../mp-weixin'
    );

    if (!fs.existsSync(projectPath)) {
      throw new Error(
        `小程序项目路径不存在: ${projectPath}\n请检查 .env 中的 MINI_PROJECT_PATH`
      );
    }

    const wsPort = opts.wsPort || process.env.WECHAT_WS_PORT || '9420';
    const wsEndpoint = `ws://127.0.0.1:${wsPort}`;

    console.log(`[MiniDriver] 连接开发者工具: ${wsEndpoint}`);
    const automator = require('miniprogram-automator');

    try {
      this.app = await automator.connect({ wsEndpoint });
      this._connected = true;
      console.log('[MiniDriver] ✅ 连接成功');
      return this.app;
    } catch (err) {
      this._connected = false;
      throw new Error(
        `无法连接微信开发者工具 (${wsEndpoint})。\n` +
        `请确认:\n` +
        `  1. 微信开发者工具已启动\n` +
        `  2. 设置 → 安全 → 服务端口已开启（设为 ${wsPort}）\n` +
        `  3. 已运行自动化: cli.bat auto --project ${projectPath}\n` +
        `原始错误: ${err.message}`
      );
    }
  }

  async close() {
    if (this.app) {
      try {
        // 仅释放引用，不断开 DevTools（便于共享连接）
        console.log('[MiniDriver] 释放连接引用');
      } catch (err) {
        console.warn('[MiniDriver] 断开时出错:', err.message);
      }
      this.app = null;
      this._connected = false;
    }
  }
}

module.exports = { MiniDriver };
