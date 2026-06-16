require('dotenv').config({ path: require('path').resolve(__dirname, '.env') });

// 测试超时（毫秒）
jest.setTimeout(parseInt(process.env.TEST_TIMEOUT || '120000', 10));
