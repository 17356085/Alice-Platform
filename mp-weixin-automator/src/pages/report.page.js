/**
 * 生产报表 Page Objects — pages-sub/report/index + production + input + adjust
 *
 * 功能: 生产数据首页（储罐概览+统计）、日报/月报/交接班、手工录入、数据调整
 */
const { MiniPage } = require('../MiniPage');

class ReportIndexPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/report/index';

  async waitForContent(timeout = 15000) {
    await this.waitFor('.report-page, .production-page', timeout);
    await this.waitForDataReady(timeout);
  }

  async getStatistics() {
    const data = await this.getData();
    return {
      productionOutput: data.k || data.productionOutput || '',
      qualificationRate: data.l || data.qualificationRate || '',
      runningTanks: data.m || data.runningTanks || '',
      normalEquipment: data.n || data.normalEquipment || '',
    };
  }

  async getTankOverview() {
    const data = await this.getData();
    return data.o || data.tankCards || [];
  }

  async getDeviceStatus() {
    const data = await this.getData();
    return {
      normal: data.r || data.a?.normal || 0,
      maintenance: data.s || data.a?.maintenance || 0,
      fault: data.t || data.a?.fault || 0,
    };
  }
}

class ProductionReportPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/report/production';

  async waitForContent(timeout = 15000) {
    await this.waitFor('.report-content, .production-report', timeout);
    await this.waitForDataReady(timeout);
  }

  async getReportType() {
    const data = await this.getData();
    return data.reportType || data.templateId || '';
  }

  async getReportData() {
    return this.getData();
  }

  /** 切换报表类型（日报/月报/交接班） */
  async switchReportType(type) {
    await this.callMethod('switchReportType', [type]);
    await this.waitForDataReady(5000);
  }
}

class ReportInputPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/report/input';

  async waitForContent(timeout = 10000) {
    await this.waitFor('.input-form, .report-input', timeout);
    await this.waitForDataReady(timeout);
  }
}

class ReportAdjustPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/report/adjust';

  async waitForContent(timeout = 10000) {
    await this.waitFor('.adjust-form, .report-adjust', timeout);
    await this.waitForDataReady(timeout);
  }
}

module.exports = { ReportIndexPage, ProductionReportPage, ReportInputPage, ReportAdjustPage };
