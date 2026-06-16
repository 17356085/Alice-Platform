/**
 * 弱网/网络异常模拟工具
 *
 * 通过微信开发者工具的 Network 面板模拟弱网条件。
 * 注意：miniprogram-automator 对网络模拟的支持有限，
 * 当前通过以下方式间接模拟：
 *   1. 利用开发者工具 CLI 参数 --network
 *   2. 通过 navigateTo 前强制等待模拟延迟
 *   3. 通过 app.evaluate() 拦截 wx.request（如果支持）
 */

const { logger } = require('./logger');
const { sleep } = require('./helpers');

/**
 * 网络条件预设
 */
const NETWORK_PRESETS = {
  wifi: { label: 'WiFi', delay: 0, lossRate: 0 },
  '4g': { label: '4G', delay: 100, lossRate: 0 },
  '3g': { label: '3G', delay: 500, lossRate: 0.02 },
  '2g': { label: '2G', delay: 2000, lossRate: 0.05 },
  offline: { label: '离线', delay: Infinity, lossRate: 1 },
};

/**
 * 网络条件模拟器
 */
class NetworkSimulator {
  constructor(app) {
    this.app = app;
    this._currentPreset = 'wifi';
    this._originalRequest = null;
  }

  /**
   * 设置网络条件（仅影响请求等待时间，非真实网络模拟）
   * @param {'wifi'|'4g'|'3g'|'2g'|'offline'} preset
   */
  setPreset(preset) {
    if (!NETWORK_PRESETS[preset]) {
      throw new Error(`未知网络预设: ${preset}，可选: ${Object.keys(NETWORK_PRESETS).join(', ')}`);
    }
    this._currentPreset = preset;
    logger.info(`[Network] 切换到: ${NETWORK_PRESETS[preset].label}`);
  }

  /** 获取当前模拟延迟(ms) */
  get delay() {
    return NETWORK_PRESETS[this._currentPreset].delay;
  }

  /** 获取当前丢包率 */
  get lossRate() {
    return NETWORK_PRESETS[this._currentPreset].lossRate;
  }

  /** 是否离线 */
  get isOffline() {
    return this._currentPreset === 'offline';
  }

  /**
   * 模拟网络请求等待（按当前延迟）
   */
  async simulateLatency() {
    if (this.isOffline) return;
    const delay = this.delay;
    if (delay > 0) {
      await sleep(delay);
    }
  }

  /**
   * 模拟丢包 — 按丢包率随机决定是否"丢失"
   * @returns {boolean} true=包丢失
   */
  simulatePacketLoss() {
    return Math.random() < this.lossRate;
  }

  /**
   * 切换到弱网（3G）
   */
  async goSlow() {
    this.setPreset('3g');
  }

  /**
   * 断网
   */
  async goOffline() {
    this.setPreset('offline');
  }

  /**
   * 恢复网络
   */
  async goOnline(preset = '4g') {
    this.setPreset(preset);
    logger.info('[Network] 网络恢复');
  }
}

// 单例
let _instance = null;

function getNetworkSimulator(app) {
  if (!_instance) {
    _instance = new NetworkSimulator(app);
  }
  return _instance;
}

module.exports = { NetworkSimulator, getNetworkSimulator, NETWORK_PRESETS };
