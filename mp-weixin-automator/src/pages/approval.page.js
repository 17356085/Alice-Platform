const { MiniPage } = require('../MiniPage');

/**
 * 审批列表页 — pages/approval/index（TabBar 页）
 *
 * 功能: 多 Tab（待审批/已通过/已驳回/我发起的）、审批操作
 */
class ApprovalListPage extends MiniPage {
  static PAGE_PATH = 'pages/approval/index';
  static IS_TAB_PAGE = true;

  /**
   * 等待列表渲染
   * 注意：uni-app 编译后 class 名带 scope ID，不能依赖原始 class 做 DOM 查询。
   * 改用 waitForDataReady 等 data 加载完成即可。
   */
  async waitForList(timeout = 15000) {
    // 给页面一些渲染时间
    await new Promise(r => setTimeout(r, 1000));
    await this.waitForDataReady(timeout);
  }

  /** 获取当前选中的 tab */
  async getCurrentTab() {
    const data = await this.getData();
    return data.g || data.currentTab || data.current || '';
  }

  /** 获取审批列表数据 */
  async getApprovalList() {
    const data = await this.getData();
    const raw = data.f || data.approvalList || data.list;
    return Array.isArray(raw) ? raw : [];
  }

  /** 获取各 Tab 的角标数 */
  async getTabBadges() {
    const data = await this.getData();
    return {
      pending: Number(data.y ?? data.pendingCount ?? data.pendingTotal ?? 0),
      approved: Number(data.h ?? data.approvedCount ?? 0),
      rejected: Number(data.x ?? data.rejectedCount ?? 0),
      my: Number(data.P ?? data.myCount ?? 0),
    };
  }

  /**
   * 切换 Tab
   * 编译后方法名可能为 switchTab / C / handleTabClick 等
   * @param {'pending'|'approved'|'rejected'|'my'} tab
   */
  async switchTab(tab) {
    const methodNames = ['switchTab', 'C', 'handleTabClick', 'onTabChange', 'changeTab'];
    let switched = false;
    for (const method of methodNames) {
      try {
        await this.callMethod(method, [tab]);
        switched = true;
        break;
      } catch {}
    }
    if (!switched) {
      // 最后兜底：尝试通过 setData 切换
      try {
        const p = await this.getPage();
        await p.setData({ g: tab });
        switched = true;
      } catch {}
    }
    await this.waitForDataReady(5000);
    console.log(`  [Approval] 切换 Tab: ${tab} (${switched ? 'ok' : 'fallback'})`);
  }

  /** 点击第 i 条审批进入详情 */
  async tapApprovalItem(index = 0) {
    // 使用 callMethod 模拟点击（比 DOM 选择器稳定）
    const list = await this.getApprovalList();
    if (list.length > index) {
      const item = list[index];
      const id = item.id || item.w;
      if (id) {
        await this.app.navigateTo(`/pages/approval/detail?id=${id}`);
        console.log(`  [Approval] 通过 navigateTo 进入详情: id=${id}`);
      }
    } else {
      throw new Error(`审批列表只有 ${list.length} 条，无法点击第 ${index} 条`);
    }
  }
}

/**
 * 审批详情页 — pages/approval/detail
 */
class ApprovalDetailPage extends MiniPage {
  static PAGE_PATH = 'pages/approval/detail';

  async waitForDetail(timeout = 10000) {
    await this.waitFor('.detail-card, .approval-detail', timeout);
    await this.waitForDataReady(timeout);
  }

  /** 获取审批详情 */
  async getDetail() {
    return this.getData();
  }

  /**
   * 审批通过
   * @param {string} [comment]  审批意见
   */
  async approve(comment = '同意') {
    await this.callMethod('approveApproval', [comment]);
    console.log(`  [Approval] 审批通过: ${comment}`);
  }

  /**
   * 审批驳回
   * @param {string} reason  驳回原因
   */
  async reject(reason) {
    await this.callMethod('rejectApproval', [reason]);
    console.log(`  [Approval] 审批驳回: ${reason}`);
  }
}

module.exports = { ApprovalListPage, ApprovalDetailPage };
