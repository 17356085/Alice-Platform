/**
 * 访客管理 Page Objects — pages-sub/visitor/index + progress + detail
 *
 * 功能: 访客登记（信息录入+员工搜索）、登记进度、详情追踪
 */
const { MiniPage } = require('../MiniPage');

class VisitorRegisterPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/visitor/index';

  async waitForContent(timeout = 15000) {
    await this.waitFor('.visitor-form, .register-page', timeout);
    await this.waitForDataReady(timeout);
  }

  /** 获取表单数据 */
  async getFormData() {
    const data = await this.getData();
    return {
      visitorName: data.b || data.visitorName || '',
      company: data.d || data.company || '',
      phone: data.f || data.phone || '',
      hostEmployee: data.h || data.hostEmployee || '',
      visitPurpose: data.l || data.visitPurpose || '',
    };
  }

  /** 获取最近的登记记录列表 */
  async getRecentRecords() {
    const data = await this.getData();
    return data.s || data.records || [];
  }

  /**
   * 填写访客信息并提交
   * @param {{visitorName, company, phone, visitPurpose}} info
   */
  async fillAndSubmit(info) {
    const page = await this.getPage();
    if (page) {
      await page.setData({
        b: info.visitorName || '',
        d: info.company || '',
        f: info.phone || '',
        l: info.visitPurpose || '',
      });
    }
    // 点击提交按钮
    const buttons = await this.$$('button');
    for (const btn of buttons) {
      try {
        const text = await btn.text();
        if (text && text.includes('提交')) {
          await btn.tap();
          break;
        }
      } catch {}
    }
    await this.waitForDataReady(5000);
  }

  /** 搜索被访员工 */
  async searchHost(keyword) {
    const page = await this.getPage();
    if (page) {
      await page.setData({ B: keyword });
    }
    await this.callMethod('searchHost', [keyword]);
    await this.waitForDataReady(3000);
  }

  /** 获取搜索结果 */
  async getSearchResults() {
    const data = await this.getData();
    return data.D || data.hostEmployees || [];
  }
}

class VisitorProgressPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/visitor/progress';

  async waitForList(timeout = 10000) {
    await this.waitFor('.record-item, .progress-list', timeout);
    await this.waitForDataReady(timeout);
  }

  async getRecords() {
    const data = await this.getData();
    return data.recordList || data.records || [];
  }
}

class VisitorDetailPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/visitor/detail';

  async waitForDetail(timeout = 10000) {
    await this.waitFor('.detail-card, .visitor-detail', timeout);
    await this.waitForDataReady(timeout);
  }

  async getDetail() {
    return this.getData();
  }
}

module.exports = { VisitorRegisterPage, VisitorProgressPage, VisitorDetailPage };
