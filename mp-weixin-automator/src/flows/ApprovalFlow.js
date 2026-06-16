/**
 * ApprovalFlow — 审批工作流业务流程编排
 *
 * 封装: 审批列表 → 各Tab切换验证 → 进入详情 → 通过/驳回 → 结果验证
 */

const { ApprovalListPage, ApprovalDetailPage } = require('../pages/approval.page');
const { logger } = require('../utils/logger');
const { sleep } = require('../utils/helpers');
const { dataFactory } = require('../utils/dataFactory');

class ApprovalFlow {
  /**
   * @param {import('miniprogram-automator').MiniProgram} app
   */
  constructor(app) {
    this.app = app;
  }

  /**
   * 验证审批列表各Tab切换及角标
   * @returns {Promise<{tabs: object, badges: object}>}
   */
  async verifyAllTabs() {
    const listPage = new ApprovalListPage(this.app);
    await listPage.navigate();
    await listPage.waitForList();

    const badges = await listPage.getTabBadges();
    logger.info(`[ApprovalFlow] 角标: pending=${badges.pending}, approved=${badges.approved}, rejected=${badges.rejected}, my=${badges.my}`);

    const tabs = ['pending', 'approved', 'rejected', 'my'];
    const tabResults = {};

    for (const tab of tabs) {
      await listPage.switchTab(tab);
      await sleep(1000);
      const current = await listPage.getCurrentTab();
      const list = await listPage.getApprovalList();
      tabResults[tab] = { currentTab: current, itemCount: list.length };
      logger.info(`[ApprovalFlow] Tab "${tab}": 当前=${current}, 项数=${list.length}`);
    }

    return { tabs: tabResults, badges };
  }

  /**
   * 审批通过流程
   * @param {string} [comment]
   * @returns {Promise<boolean>}
   */
  async approveFirstPending(comment) {
    const msg = comment || dataFactory.approvalComment('approve');
    const listPage = new ApprovalListPage(this.app);
    await listPage.navigate();
    await listPage.waitForList();
    await listPage.switchTab('pending');
    await sleep(1000);

    const list = await listPage.getApprovalList();
    if (list.length === 0) {
      logger.warn('[ApprovalFlow] 无待审批项，跳过');
      return false;
    }

    await listPage.tapApprovalItem(0);
    await sleep(1000);

    const detailPage = new ApprovalDetailPage(this.app);
    await detailPage.waitForDetail();
    await detailPage.approve(msg);
    logger.info(`[ApprovalFlow] ✅ 审批通过: ${msg}`);
    return true;
  }

  /**
   * 审批驳回流程
   * @param {string} [reason]
   * @returns {Promise<boolean>}
   */
  async rejectFirstPending(reason) {
    const msg = reason || dataFactory.approvalComment('reject');
    const listPage = new ApprovalListPage(this.app);
    await listPage.navigate();
    await listPage.waitForList();
    await listPage.switchTab('pending');
    await sleep(1000);

    const list = await listPage.getApprovalList();
    if (list.length === 0) {
      logger.warn('[ApprovalFlow] 无待审批项，跳过');
      return false;
    }

    await listPage.tapApprovalItem(0);
    await sleep(1000);

    const detailPage = new ApprovalDetailPage(this.app);
    await detailPage.waitForDetail();
    await detailPage.reject(msg);
    logger.info(`[ApprovalFlow] ✅ 审批驳回: ${msg}`);
    return true;
  }
}

module.exports = { ApprovalFlow };
