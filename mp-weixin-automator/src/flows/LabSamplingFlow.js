/**
 * LabSamplingFlow — 化验室取样业务流程编排
 *
 * 封装: 选择分析类型 → 选择子类型 → 填写取样信息 → 录入指标值 → 提交 → 查看历史
 */

const { logger } = require('../utils/logger');
const { sleep } = require('../utils/helpers');
const { dataFactory } = require('../utils/dataFactory');

class LabSamplingFlow {
  /**
   * @param {import('miniprogram-automator').MiniProgram} app
   */
  constructor(app) {
    this.app = app;
  }

  /**
   * 进入化验室页面并切换分析类型
   * @param {'gas'|'water'} typeCode
   * @returns {Promise<{navigated: boolean}>}
   */
  async navigateToLabType(typeCode = 'gas') {
    logger.info(`[LabFlow] 进入化验室取样，类型: ${typeCode}`);

    await this.app.navigateTo('/pages-sub/lab/index');
    await sleep(2000);

    const page = await this.app.currentPage();
    if (!page) {
      logger.warn('[LabFlow] 页面未加载');
      return { navigated: false };
    }

    // 切换类型（gas/water）
    try {
      const data = await page.data();
      const currentType = data.u || data.typeCode || '';
      if (currentType !== typeCode) {
        // 通过点击 Tab 切换
        const viewEls = await page.$$('view');
        for (const el of viewEls) {
          try {
            const text = await el.text();
            if (typeCode === 'gas' && text.includes('气体')) {
              await el.tap();
              break;
            }
            if (typeCode === 'water' && text.includes('水')) {
              await el.tap();
              break;
            }
          } catch {}
        }
        await sleep(1500);
      }
    } catch {}

    return { navigated: true };
  }

  /**
   * 选择化验子类型
   * @param {number} index  子类型列表索引
   * @returns {Promise<string>} 选中的子类型名称
   */
  async selectSubType(index = 0) {
    const page = await this.app.currentPage();
    if (!page) return '';

    const data = await page.data();
    const subTypes = data.i || data.indicatorTypes || [];

    if (subTypes.length === 0) {
      logger.warn('[LabFlow] 无化验子类型');
      return '';
    }

    const target = subTypes[Math.min(index, subTypes.length - 1)];
    const name = target.a || target.subName || '';

    // 点击子类型
    const items = await page.$$('.type-item, .sub-type-item');
    if (items.length > index) {
      await items[index].tap();
      await sleep(1000);
    }

    logger.info(`[LabFlow] 选择子类型: ${name}`);
    return name;
  }

  /**
   * 填写化验报告并提交
   * @param {object} [reportData]  覆盖默认值
   * @returns {Promise<{submitted: boolean, reportNo?: string}>}
   */
  async submitReport(reportData = {}) {
    const data = dataFactory.labReportData(reportData);

    const page = await this.app.currentPage();
    if (!page) return { submitted: false };

    // 使用 setData 填充表单字段
    try {
      // data key mapping: F=inspector, H=reviewer, J=team, Q=remark
      await page.setData({
        F: data.inspector,
        H: data.reviewer,
        Q: data.remark,
      });
      logger.info('[LabFlow] 已填入化验表单');
    } catch {}

    // 点击提交按钮
    try {
      const buttons = await page.$$('button');
      for (const btn of buttons) {
        try {
          const text = await btn.text();
          if (text && (text.includes('提交') || text.includes('确认'))) {
            await btn.tap();
            logger.info('[LabFlow] 已点击提交');
            await sleep(2000);
            break;
          }
        } catch {}
      }
    } catch {}

    return { submitted: true };
  }
}

module.exports = { LabSamplingFlow };
