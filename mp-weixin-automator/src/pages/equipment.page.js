/**
 * 设备管理 Page Objects — pages-sub/equipment/index + detail
 */
const { MiniPage } = require('../MiniPage');

class EquipmentListPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/equipment/index';

  async waitForList(timeout = 15000) {
    await this.waitFor('.equipment-list, .device-list', timeout);
    await this.waitForDataReady(timeout);
  }

  async getStatistics() {
    const data = await this.getData();
    return {
      total: data.totalCount || 0,
      running: data.runningCount || 0,
      maintenance: data.maintenanceCount || 0,
    };
  }

  async getDeviceList() {
    const data = await this.getData();
    return data.deviceList || data.records || [];
  }
}

class EquipmentDetailPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/equipment/detail';

  async waitForDetail(timeout = 10000) {
    await this.waitFor('.equipment-detail, .device-detail', timeout);
    await this.waitForDataReady(timeout);
  }

  async getDetail() {
    return this.getData();
  }
}

module.exports = { EquipmentListPage, EquipmentDetailPage };
