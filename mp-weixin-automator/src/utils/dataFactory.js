/**
 * 测试数据工厂
 *
 * 生成测试所需的模板数据，避免硬编码。
 * 数据模板来自 data/templates/ 目录的 JSON 文件。
 */

const path = require('path');
const fs = require('fs');

/**
 * 加载模板 JSON 文件
 * @param {string} name  模板文件名（不含 .json）
 * @returns {object}
 */
function loadTemplate(name) {
  const filePath = path.resolve(__dirname, '..', '..', 'data', 'templates', `${name}.json`);
  if (!fs.existsSync(filePath)) {
    return {};
  }
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

/**
 * 生成唯一标识符
 */
function uid(prefix = 'test') {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

/**
 * 当前日期字符串 YYYY-MM-DD
 */
function today() {
  return new Date().toISOString().slice(0, 10);
}

/**
 * 当前时间字符串 HH:MM
 */
function nowTime() {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

/**
 * 访客登记数据模板
 * @param {object} [overrides]  覆盖字段
 * @returns {object}
 */
function visitorData(overrides = {}) {
  const template = loadTemplate('visitor');
  return {
    visitorName: template.visitorName || `访客${uid('v')}`,
    company: template.company || '自动化测试公司',
    phone: template.phone || `1${String(Math.floor(Math.random() * 9e8 + 1e8))}`,
    visitPurpose: template.visitPurpose || '业务洽谈',
    ...overrides,
  };
}

/**
 * 化验报告数据模板
 * @param {object} [overrides]
 * @returns {object}
 */
function labReportData(overrides = {}) {
  return {
    inspector: '自动化测试员',
    reviewer: '自动化复核员',
    team: '一班',
    sampleDate: today(),
    sampleTime: nowTime(),
    remark: `自动化测试_${uid()}`,
    ...overrides,
  };
}

/**
 * 审批意见数据
 * @param {'approve'|'reject'} type
 * @returns {string}
 */
function approvalComment(type = 'approve') {
  const id = uid();
  return type === 'approve'
    ? `同意——自动化测试_${id}`
    : `驳回——信息不全_${id}`;
}

/**
 * 登录凭证
 * @param {string} phone
 * @param {string} password
 * @returns {{phone: string, password: string}}
 */
function loginCredentials(phone, password) {
  return { phone, password };
}

module.exports = {
  loadTemplate,
  uid,
  today,
  nowTime,
  visitorData,
  labReportData,
  approvalComment,
  loginCredentials,
};
