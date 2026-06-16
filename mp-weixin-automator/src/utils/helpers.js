/**
 * 帮助函数集
 */
const fs = require('fs');
const path = require('path');

/**
 * 等待指定毫秒
 * @param {number} ms
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 保存截图到 artifacts 目录
 * @param {import('miniprogram-automator').MiniProgram} app
 * @param {string} name  文件名（不含扩展名）
 */
async function saveScreenshot(app, name) {
  try {
    const screenshotDir = process.env.SCREENSHOT_DIR || './artifacts/screenshots';
    const dir = path.resolve(__dirname, '..', '..', screenshotDir);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    const filePath = path.join(dir, `${name}_${Date.now()}.png`);
    const page = await app.currentPage();
    if (page && page.screenshot) {
      await page.screenshot({ path: filePath });
      console.log(`  截图已保存: ${filePath}`);
    }
  } catch (err) {
    console.warn('截图失败:', err.message);
  }
}

/**
 * 重试异步操作
 * @param {Function} fn      异步函数
 * @param {number}   retries 最大重试次数
 * @param {number}   delay   重试间隔(ms)
 */
async function retry(fn, retries = 3, delay = 1000) {
  let lastErr;
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      if (i < retries - 1) {
        console.warn(`  重试 ${i + 1}/${retries}: ${err.message}`);
        await sleep(delay);
      }
    }
  }
  throw lastErr;
}

module.exports = { sleep, saveScreenshot, retry };
