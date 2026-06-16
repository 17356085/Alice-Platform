/**
 * 设置 Page Objects — pages-sub/settings/message-settings + security-settings + device-manage
 *
 * 功能: 消息通知开关+免打扰时段、修改密码+生物识别开关+设备管理
 */
const { MiniPage } = require('../MiniPage');

class MessageSettingsPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/settings/message-settings';

  async waitForContent(timeout = 10000) {
    await this.waitFor('.settings-page, .message-settings', timeout);
    await this.waitForDataReady(timeout);
  }

  async getSettings() {
    const data = await this.getData();
    return {
      alarm: data.o?.alarm ?? true,
      approval: data.o?.approval ?? true,
      study: data.o?.study ?? true,
      task: data.o?.task ?? true,
      announcement: data.o?.announcement ?? false,
      safety: data.o?.safety ?? true,
      quietStart: data.o?.startTime || '',
      quietEnd: data.o?.endTime || '',
    };
  }

  /** 切换某个开关 */
  async toggle(key) {
    await this.callMethod('toggleSetting', [key]);
    await this.waitForDataReady(1000);
  }
}

class SecuritySettingsPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/settings/security-settings';

  async waitForContent(timeout = 10000) {
    await this.waitFor('.security-settings, .settings-page', timeout);
    await this.waitForDataReady(timeout);
  }

  async getBiometricEnabled() {
    const data = await this.getData();
    return data.a || data.biometricEnabled || false;
  }

  /** 打开修改密码弹窗 */
  async openChangePassword() {
    await this.callMethod('openChangePassword');
  }

  /** 切换生物识别 */
  async toggleBiometric() {
    await this.callMethod('toggleBiometric');
  }
}

class DeviceManagePage extends MiniPage {
  static PAGE_PATH = 'pages-sub/settings/device-manage';

  async waitForContent(timeout = 10000) {
    await this.waitFor('.device-list, .device-manage', timeout);
    await this.waitForDataReady(timeout);
  }

  async getDeviceList() {
    const data = await this.getData();
    return data.deviceList || data.records || [];
  }
}

module.exports = { MessageSettingsPage, SecuritySettingsPage, DeviceManagePage };
