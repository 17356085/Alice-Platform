module.exports = {
  setupFiles: ['./jest.setup.js'],
  globalTeardown: './jest.teardown.js',
  testEnvironment: 'node',
  transform: {},  // 禁用 transform，避免 ESM 兼容问题
  testTimeout: parseInt(process.env.TEST_TIMEOUT || '120000', 10),
  verbose: true,
  testMatch: [
    '**/tests/smoke/**/*.test.js',
    '**/tests/p0-core/**/*.test.js',
    '**/tests/p1-high/**/*.test.js',
    '**/tests/p2-medium/**/*.test.js',
    '**/tests/p3-snapshot/**/*.test.js',
    '**/tests/**/*.test.js',   // 兼容旧路径
  ],
  reporters: [
    'default',
    ...(process.env.CI ? [['jest-html-reporters', {
      publicPath: './artifacts/report',
      filename: 'report.html',
      expand: true,
    }]] : []),
  ],
  // 测试文件按优先级顺序运行（smoke 最先）
  testSequencer: undefined,
  maxConcurrency: 1,   // 微信开发者工具不支持并发
};
