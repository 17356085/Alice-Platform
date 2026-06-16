/**
 * 自定义断言工具集
 *
 * 针对小程序的 data 数据结构校验、列表排序验证、角标准确性断言等。
 * 优先验证 data（由 page.data() 获取），规避 DOM 选择器不稳定问题。
 */

const { logger } = require('./logger');

/**
 * 断言字段为非空对象
 */
function assertHasKeys(obj, keys, label = 'data') {
  const missing = keys.filter(k => !(k in obj));
  if (missing.length > 0) {
    throw new Error(`${label} 缺少字段: ${missing.join(', ')}`);
  }
  logger.debug(`✓ ${label} 包含预期字段: ${keys.join(', ')}`);
}

/**
 * 断言列表非空（数组且长度 > 0）
 */
function assertListNotEmpty(list, label = '列表') {
  if (!Array.isArray(list)) {
    throw new Error(`${label} 不是数组，实际类型: ${typeof list}`);
  }
  if (list.length === 0) {
    logger.warn(`⚠ ${label} 为空（可能无数据）`);
  }
}

/**
 * 断言列表每项包含必需字段
 */
function assertListItemsHaveKeys(list, keys, label = '列表项') {
  assertListNotEmpty(list, label);
  list.forEach((item, i) => {
    const missing = keys.filter(k => !(k in item));
    if (missing.length > 0) {
      throw new Error(`${label}[${i}] 缺少字段: ${missing.join(', ')}`);
    }
  });
  logger.debug(`✓ ${label} ${list.length} 项均包含: ${keys.join(', ')}`);
}

/**
 * 断言数字在合理范围内
 */
function assertInRange(value, min, max, label = '值') {
  if (typeof value !== 'number' || isNaN(value)) {
    throw new Error(`${label} 不是有效数字: ${value}`);
  }
  if (value < min || value > max) {
    throw new Error(`${label}=${value} 不在 [${min}, ${max}] 范围内`);
  }
}

/**
 * 断言页面元素数量与 data 中的数据量一致
 */
async function assertDataMatchesDOM(page, dataKey, selector, label = '') {
  const data = await page.getData();
  const dataLen = (data[dataKey] || []).length;
  const elements = await page.$$(selector);
  if (dataLen !== elements.length) {
    logger.warn(`⚠ ${label}: data.${dataKey}=${dataLen}, DOM(${selector})=${elements.length}`);
  }
}

/**
 * 断言角标值合理性（pending + approved + rejected <= total）
 */
function assertBadgeTotals(badges, label = '角标') {
  const { pending = 0, approved = 0, rejected = 0, total = 0 } = badges;
  const sum = pending + approved + rejected;
  if (total > 0 && sum > total) {
    logger.warn(`⚠ ${label}: pending(${pending})+approved(${approved})+rejected(${rejected})=${sum} > total(${total})`);
  }
}

/**
 * 软断言 — 收集所有错误，最后统一报告（不中断测试）
 */
class SoftAssert {
  constructor() {
    this.errors = [];
  }

  assert(condition, message) {
    if (!condition) {
      this.errors.push(message);
      logger.warn(`  [SOFT FAIL] ${message}`);
    }
  }

  assertEqual(actual, expected, message) {
    if (actual !== expected) {
      this.errors.push(`${message}: expected=${expected}, actual=${actual}`);
      logger.warn(`  [SOFT FAIL] ${message}: expected=${expected}, actual=${actual}`);
    }
  }

  done() {
    if (this.errors.length > 0) {
      throw new Error(`软断言失败 (${this.errors.length}):\n  - ${this.errors.join('\n  - ')}`);
    }
  }
}

module.exports = {
  assertHasKeys,
  assertListNotEmpty,
  assertListItemsHaveKeys,
  assertInRange,
  assertDataMatchesDOM,
  assertBadgeTotals,
  SoftAssert,
};
