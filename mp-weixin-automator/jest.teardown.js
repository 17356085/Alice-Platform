const { MiniDriver } = require('./src/driver');

module.exports = async () => {
  const driver = MiniDriver.getInstance();
  if (driver.isConnected) {
    console.log('[globalTeardown] 释放连接...');
    await driver.close();
  }
};
