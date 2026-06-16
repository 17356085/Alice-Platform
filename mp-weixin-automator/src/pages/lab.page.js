/**
 * 化验室取样页 — pages-sub/lab/index + history
 *
 * 功能: 气体/水质分析类型切换、子类型选择、取样信息录入、指标值填写
 *       草稿暂存/恢复、提交报告、查看历史记录
 */
const { MiniPage } = require('../MiniPage');

class LabSamplingPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/lab/index';

  async waitForContent(timeout = 15000) {
    await this.waitFor('.form-card, .sampling-form, .lab-page', timeout);
    await this.waitForDataReady(timeout);
  }

  /** 获取当前分析类型 (gas/water) */
  async getCurrentType() {
    const data = await this.getData();
    return data.u || data.typeCode || '';
  }

  /** 获取子类型列表 */
  async getSubTypes() {
    const data = await this.getData();
    return data.i || data.indicatorTypes || [];
  }

  /** 获取当前选中的子类型 */
  async getCurrentSubType() {
    const data = await this.getData();
    const subTypes = data.i || data.indicatorTypes || [];
    for (const st of subTypes) {
      if (st.c === 1 || st.selected) {
        return st.a || st.subName || '';
      }
    }
    return '';
  }

  /** 获取取样点位选项列表 */
  async getLocationOptions() {
    const data = await this.getData();
    // w=是否为加样口, T=点位选项列表, C=点位选项值
    return {
      isExtraSample: data.w || data.isExtraSample || false,
      options: data.T || data.locationOptions || [],
      selected: data.z || data.sampleLocation || '',
    };
  }

  /** 获取指标字段分组列表 */
  async getFieldGroups() {
    const data = await this.getData();
    return data.S || data.fieldGroups || [];
  }

  /** 获取表单字段值 */
  async getFormData() {
    const data = await this.getData();
    return {
      inspector: data.F || '',
      reviewer: data.H || '',
      team: data.J || '',
      sampleDate: data.n || data.sampleDate || '',
      sampleTime: data.r || data.sampleTime || '',
      remark: data.Q || data.remark || '',
    };
  }

  /**
   * 切换分析类型
   * @param {'gas'|'water'} typeCode
   */
  async switchType(typeCode) {
    await this.callMethod('switchType', [typeCode]);
    await this.waitForDataReady(5000);
  }

  /**
   * 选择子类型（按索引）
   * @param {number} index
   */
  async selectSubType(index) {
    const subTypes = await this.getSubTypes();
    if (index < subTypes.length) {
      const target = subTypes[index];
      await this.callMethod('selectSubType', [target.b || target.id]);
      await this.waitForDataReady(5000);
    }
  }

  /** 提交报告 */
  async submitReport() {
    await this.callMethod('submitReport');
    await this.waitForDataReady(5000);
  }

  /** 暂存草稿 */
  async saveDraft() {
    await this.callMethod('saveDraft');
  }
}

/**
 * 化验历史记录页 — pages-sub/lab/history
 */
class LabHistoryPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/lab/history';

  async waitForList(timeout = 10000) {
    await this.waitFor('.history-item, .report-list', timeout);
    await this.waitForDataReady(timeout);
  }

  async getReportList() {
    const data = await this.getData();
    return data.reportList || data.records || [];
  }
}

module.exports = { LabSamplingPage, LabHistoryPage };
