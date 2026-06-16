/**
 * 我的申请 Page Objects — pages-sub/my-application/index + create + detail
 *
 * 功能: 申请列表（状态筛选+统计）、新建申请、申请详情
 */
const { MiniPage } = require('../MiniPage');

class MyApplicationListPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/my-application/index';

  async waitForList(timeout = 15000) {
    await this.waitFor('.application-list, .app-list', timeout);
    await this.waitForDataReady(timeout);
  }

  async getStatistics() {
    const data = await this.getData();
    return {
      total: data.r?.total || 0,
      pending: data.r?.pending || 0,
      approved: data.r?.approved || 0,
      rejected: data.r?.rejected || 0,
    };
  }

  async getApplicationList() {
    const data = await this.getData();
    return data.i || data.records || [];
  }

  /**
   * 筛选状态
   * @param {''|'running'|'completed'|'rejected'} status
   */
  async filterByStatus(status) {
    await this.callMethod('filterByStatus', [status]);
    await this.waitForDataReady(5000);
  }

  /** 点击申请项进入详情 */
  async tapApplication(index = 0) {
    const items = await this.$$('.app-item, .application-card');
    if (items.length > index) {
      await items[index].tap();
    }
  }
}

class MyApplicationCreatePage extends MiniPage {
  static PAGE_PATH = 'pages-sub/my-application/create';

  async waitForContent(timeout = 10000) {
    await this.waitFor('.create-form, .app-create', timeout);
    await this.waitForDataReady(timeout);
  }
}

class MyApplicationDetailPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/my-application/detail';

  async waitForDetail(timeout = 10000) {
    await this.waitFor('.detail-card, .app-detail', timeout);
    await this.waitForDataReady(timeout);
  }

  async getDetail() {
    return this.getData();
  }
}

module.exports = { MyApplicationListPage, MyApplicationCreatePage, MyApplicationDetailPage };
