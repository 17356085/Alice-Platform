/**
 * 储罐管理 Page Objects — pages-sub/tank/index + detail
 */
const { MiniPage } = require('../MiniPage');

class TankListPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/tank/index';

  async waitForList(timeout = 15000) {
    await this.waitFor('.tank-list, .tank-page', timeout);
    await this.waitForDataReady(timeout);
  }

  async getTankList() {
    const data = await this.getData();
    return data.tankList || data.records || [];
  }
}

class TankDetailPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/tank/detail';

  async waitForDetail(timeout = 15000) {
    await this.waitFor('.tank-detail, .monitor-page', timeout);
    await this.waitForDataReady(timeout);
  }

  async getDetail() {
    return this.getData();
  }
}

module.exports = { TankListPage, TankDetailPage };
