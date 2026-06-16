const { MiniPage } = require('../MiniPage');

/**
 * 报警列表页 — pages/alarm/index（TabBar 页）
 *
 * 功能: 报警列表展示、按级别筛选、报警统计、跳转详情
 */
class AlarmListPage extends MiniPage {
  static PAGE_PATH = 'pages/alarm/index';
  static IS_TAB_PAGE = true;

  /** 等待列表渲染 */
  async waitForList(timeout = 15000) {
    await new Promise(r => setTimeout(r, 1000));
    await this.waitForDataReady(timeout);
  }

  /** 获取报警列表数据（从页面 data，确保返回数组） */
  async getAlarmList() {
    const data = await this.getData();
    const raw = data.i || data.filteredList || data.alarmList || [];
    return Array.isArray(raw) ? raw : [];
  }

  /** 获取报警统计数据 */
  async getStatistics() {
    const data = await this.getData();
    return data.s || data.statistics || {};
  }

  /**
   * 按级别筛选
   * @param {'all'|'urgent'|'normal'|'processed'} level
   */
  async filterByLevel(level) {
    await this.callMethod('switchTab', [level]);
    // fallback: 如果 callMethod 的方法名不同，试试直接 setData
    await this.waitForDataReady(5000);
    console.log(`  [Alarm] 筛选: ${level}`);
  }

  /** 获取筛选项的角标数据 */
  async getFilterTabs() {
    const data = await this.getData();
    return data.d || data.filterTabs || [];
  }

  /** 点击第 i 条报警进入详情 */
  async tapAlarmItem(index = 0) {
    const list = await this.getAlarmList();
    if (list.length > index) {
      const item = list[index];
      const id = item.id || item.v;
      if (id) {
        await this.app.navigateTo(`/pages/alarm/detail?id=${id}`);
        console.log(`  [Alarm] 通过 navigateTo 进入详情: id=${id}`);
      }
    } else {
      throw new Error(`报警列表只有 ${list.length} 条，无法点击第 ${index} 条`);
    }
  }

  /** 下拉刷新 */
  async pullRefresh() {
    await this.callMethod('onPullDownRefresh');
    await this.waitForDataReady(5000);
  }
}

/**
 * 报警详情页 — pages/alarm/detail
 */
class AlarmDetailPage extends MiniPage {
  static PAGE_PATH = 'pages/alarm/detail';

  async waitForDetail(timeout = 10000) {
    await this.waitFor('.detail-card, .alarm-detail', timeout);
    await this.waitForDataReady(timeout);
  }

  /** 获取报警详情数据 */
  async getDetail() {
    return this.getData();
  }

  /**
   * 处理报警
   * @param {string} result  处理结果描述
   */
  async handleAlarm(result) {
    await this.callMethod('handleAlarm', [result]);
    await this.waitForDataReady(5000);
  }
}

module.exports = { AlarmListPage, AlarmDetailPage };
