/**
 * 人员管理 Page Objects — pages-sub/person/index + profile
 *
 * 功能: 人员列表+搜索、个人档案（基本信息/岗位/资质/培训记录/考试记录）
 */
const { MiniPage } = require('../MiniPage');

class PersonListPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/person/index';

  async waitForList(timeout = 15000) {
    await this.waitFor('.person-list, .employee-list', timeout);
    await this.waitForDataReady(timeout);
  }

  async getStatistics() {
    const data = await this.getData();
    return {
      total: data.totalCount || 0,
    };
  }

  async getPersonList() {
    const data = await this.getData();
    return data.personList || data.records || [];
  }

  /** 搜索 */
  async search(keyword) {
    await this.callMethod('search', [keyword]);
    await this.waitForDataReady(3000);
  }
}

class PersonProfilePage extends MiniPage {
  static PAGE_PATH = 'pages-sub/person/profile';

  async waitForContent(timeout = 10000) {
    await this.waitFor('.profile-card, .person-profile', timeout);
    await this.waitForDataReady(timeout);
  }

  async getProfile() {
    return this.getData();
  }

  async getCertificates() {
    const data = await this.getData();
    return data.certificates || [];
  }

  async getTrainingRecords() {
    const data = await this.getData();
    return data.trainingRecords || [];
  }

  async getExamRecords() {
    const data = await this.getData();
    return data.examRecords || [];
  }
}

module.exports = { PersonListPage, PersonProfilePage };
