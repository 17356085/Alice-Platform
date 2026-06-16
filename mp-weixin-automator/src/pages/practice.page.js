/**
 * 自主练习 + 错题集 Page Objects — pages-sub/study/practice + wrong
 *
 * 功能:
 *   PracticePage:   练习历史列表、练习统计、创建练习入口
 *   PracticeCreate: 自定义组卷（题型/数量/难度）
 *   PracticeExam:   练习答题页（复用 AnswerPage 核心逻辑）
 *   PracticeResult: 练习结果页
 *   WrongPage:      错题列表、分类树、题型/掌握状态筛选、收藏/掌握标记
 *   WrongDetail:    错题详情（题目/错误答案/正确答案/解析）
 */
const { MiniPage } = require('../MiniPage');

class PracticePage extends MiniPage {
  static PAGE_PATH = 'pages-sub/study/practice';

  async waitForContent(timeout = 15000) {
    await this.waitFor('.practice-header, .practice-list', timeout);
    await this.waitForDataReady(timeout);
  }

  async getStatistics() {
    const data = await this.getData();
    return {
      totalPractices: data.totalPractices || data.totalPracticeCount || 0,
      correctRate: data.correctRate || 0,
    };
  }

  async getHistoryList() {
    const data = await this.getData();
    return data.practiceList || data.records || [];
  }

  /** 创建新练习 */
  async goCreate() {
    await this.callMethod('goCreate');
  }
}

class PracticeCreatePage extends MiniPage {
  static PAGE_PATH = 'pages-sub/study/practice-create';

  async waitForContent(timeout = 10000) {
    await this.waitFor('.create-form, .practice-create', timeout);
    await this.waitForDataReady(timeout);
  }

  /** 开始练习 */
  async startPractice(type = 'custom', questionCount = 10) {
    const page = await this.getPage();
    if (page) {
      // 设置题型和数量
      await page.setData({
        questionCount: questionCount,
        practiceType: type,
      });
    }
    await this.callMethod('startPractice');
    await this.waitForDataReady(5000);
  }
}

class WrongPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/study/wrong';

  async waitForContent(timeout = 15000) {
    await this.waitFor('.wrong-header, .wrong-list', timeout);
    await this.waitForDataReady(timeout);
  }

  async getStatistics() {
    const data = await this.getData();
    return {
      totalCount: data.totalCount || 0,
      unmasteredCount: data.unmasteredCount || 0,
      masteredCount: data.masteredCount || 0,
    };
  }

  async getWrongList() {
    const data = await this.getData();
    return data.wrongList || data.records || [];
  }

  /** 获取题目分类树 */
  async getCategoryTree() {
    const data = await this.getData();
    return data.categoryTree || data.categories || [];
  }

  /**
   * 按题型筛选
   * @param {'single'|'multi'|'judge'|'fill'|'short_answer'|'all'} type
   */
  async filterByType(type) {
    await this.callMethod('filterByType', [type]);
    await this.waitForDataReady(5000);
  }

  /** 标记已掌握 */
  async markMastered(index = 0) {
    await this.callMethod('markMastered', [index]);
  }

  /** 收藏 */
  async collect(index = 0) {
    await this.callMethod('collect', [index]);
  }
}

class WrongDetailPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/study/wrong-detail';

  async waitForContent(timeout = 10000) {
    await this.waitFor('.detail-card, .question-detail', timeout);
    await this.waitForDataReady(timeout);
  }

  async getDetail() {
    return this.getData();
  }
}

module.exports = {
  PracticePage, PracticeCreatePage, PracticeExam: null, PracticeResult: null,
  WrongPage, WrongDetailPage,
};
