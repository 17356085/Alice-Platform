/**
 * 销售管理 Page Objects — pages-sub/sale/index + add
 *
 * 功能: 销售订单列表（日报表图表+执行中合同）、新增订单
 */
const { MiniPage } = require('../MiniPage');

class SaleListPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/sale/index';

  async waitForList(timeout = 15000) {
    await this.waitFor('.sale-page, .sales-page', timeout);
    await this.waitForDataReady(timeout);
  }

  async getDailyReport() {
    const data = await this.getData();
    return data.dailyReport || data.reportData || [];
  }

  async getExecutingContracts() {
    const data = await this.getData();
    return data.contractList || data.contracts || [];
  }
}

class SaleAddPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/sale/add';

  async waitForContent(timeout = 10000) {
    await this.waitFor('.add-form, .sale-add', timeout);
    await this.waitForDataReady(timeout);
  }
}

module.exports = { SaleListPage, SaleAddPage };
