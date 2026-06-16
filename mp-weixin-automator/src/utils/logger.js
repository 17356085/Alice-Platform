/**
 * 简单的带时间戳的日志工具
 */

function timestamp() {
  const now = new Date();
  return now.toISOString().replace('T', ' ').slice(0, 19);
}

const logger = {
  info(...args) {
    console.log(`[${timestamp()}] [INFO]`, ...args);
  },
  warn(...args) {
    console.warn(`[${timestamp()}] [WARN]`, ...args);
  },
  error(...args) {
    console.error(`[${timestamp()}] [ERROR]`, ...args);
  },
  debug(...args) {
    if (process.env.DEBUG) {
      console.log(`[${timestamp()}] [DEBUG]`, ...args);
    }
  },
};

module.exports = { logger, timestamp };
