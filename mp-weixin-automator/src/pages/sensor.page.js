/**
 * 传感器管理 Page Objects — pages-sub/sensor/index + detail
 */
const { MiniPage } = require('../MiniPage');

class SensorListPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/sensor/index';

  async waitForList(timeout = 15000) {
    await this.waitFor('.sensor-list, .sensor-page', timeout);
    await this.waitForDataReady(timeout);
  }

  async getStatistics() {
    const data = await this.getData();
    return {
      total: data.totalCount || 0,
      online: data.onlineCount || 0,
      offline: data.offlineCount || 0,
    };
  }

  async getSensorList() {
    const data = await this.getData();
    return data.sensorList || data.records || [];
  }
}

class SensorDetailPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/sensor/detail';

  async waitForDetail(timeout = 10000) {
    await this.waitFor('.sensor-detail, .detail-card', timeout);
    await this.waitForDataReady(timeout);
  }

  async getDetail() {
    return this.getData();
  }
}

module.exports = { SensorListPage, SensorDetailPage };
