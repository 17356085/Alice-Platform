/**
 * 摄像头管理 Page Objects — pages-sub/camera/index + detail
 */
const { MiniPage } = require('../MiniPage');

class CameraListPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/camera/index';

  async waitForList(timeout = 15000) {
    await this.waitFor('.camera-list, .camera-page', timeout);
    await this.waitForDataReady(timeout);
  }

  async getAreas() {
    const data = await this.getData();
    return data.areaList || data.areas || [];
  }

  async getCameraList() {
    const data = await this.getData();
    return data.cameraList || data.records || [];
  }

  async getStatistics() {
    const data = await this.getData();
    return {
      total: data.totalCount || 0,
      areaCount: data.areaCount || 0,
    };
  }

  /** 按区域筛选 */
  async filterByArea(area) {
    await this.callMethod('filterByArea', [area]);
    await this.waitForDataReady(5000);
  }
}

class CameraDetailPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/camera/detail';

  async waitForDetail(timeout = 10000) {
    await this.waitFor('.camera-detail, .detail-card', timeout);
    await this.waitForDataReady(timeout);
  }

  async getDetail() {
    return this.getData();
  }
}

module.exports = { CameraListPage, CameraDetailPage };
