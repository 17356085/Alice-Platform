const { MiniPage } = require('../MiniPage');

/**
 * 培训学习首页 — pages-sub/study/index（子包页面）
 *
 * 功能: 培训计划进度、学习记录、课程列表
 */
class StudyPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/study/index';

  async waitForContent(timeout = 15000) {
    await new Promise(r => setTimeout(r, 1000));
    await this.waitForDataReady(timeout);
  }

  /** 获取培训计划列表 */
  async getTrainingPlans() {
    const data = await this.getData();
    return data.u || data.plans || data.planList || [];
  }

  /** 获取学习记录 */
  async getStudyRecords() {
    const data = await this.getData();
    return data.s || data.studyRecords || data.recentStudies || [];
  }

  /** 获取学习进度 */
  async getProgress() {
    const data = await this.getData();
    return {
      overall: data.g ?? data.overallProgress ?? data.totalProgress ?? 0,
      completed: data.s?.length ?? data.completedCount ?? 0,
      total: data.plans?.length ?? data.totalCount ?? 0,
    };
  }

  /** 点击课程 */
  async tapCourse(index = 0) {
    const list = await this.getStudyRecords();
    if (list.length > index) {
      const item = list[index];
      const courseId = item.courseId || item.j;
      if (courseId) {
        await this.app.navigateTo(`/pages-sub/study/study?courseId=${courseId}`);
      }
    }
  }
}

module.exports = { StudyPage };
