/**
 * apiLogin — 通过 HTTP API 获取认证令牌
 *
 * 小程序 UI 自动化中，标准做法是跳过 UI 登录环节，
 * 直接调用登录 API 获取 Token，然后注入到小程序存储。
 * 这样避免了 setData + button tap 方式的不稳定性。
 */
const https = require('https');
const http = require('http');
const { URL } = require('url');
const { config } = require('../config/test.config');

/**
 * 调用登录 API
 * @param {string} phone    手机号
 * @param {string} password 密码
 * @returns {Promise<{accessToken: string, refreshToken: string, userInfo: object|null}>}
 */
async function loginByApi(phone, password) {
  const baseUrl = config.baseUrl;
  const url = new URL('/api/app/auth/phone-login', baseUrl);

  const body = JSON.stringify({ phone, password });

  return new Promise((resolve, reject) => {
    const client = baseUrl.startsWith('https') ? https : http;
    const options = {
      hostname: url.hostname,
      port: url.port || (baseUrl.startsWith('https') ? 443 : 80),
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
      timeout: 30000,
    };

    const req = client.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          if (result.code === 200 || result.code === 0) {
            resolve({
              accessToken: result.data.accessToken,
              refreshToken: result.data.refreshToken || '',
              userInfo: result.data.userInfo || null,
            });
          } else {
            reject(new Error(`登录API返回错误: code=${result.code}, message=${result.message || '未知'}`));
          }
        } catch (e) {
          reject(new Error(`解析登录响应失败: ${e.message}, raw: ${data.slice(0, 200)}`));
        }
      });
    });

    req.on('error', (e) => reject(new Error(`登录网络请求失败: ${e.message}`)));
    req.on('timeout', () => { req.destroy(); reject(new Error('登录请求超时')); });
    req.write(body);
    req.end();
  });
}

/**
 * 获取用户信息
 * @param {string} accessToken
 * @returns {Promise<object>}
 */
async function getUserInfoByApi(accessToken) {
  const baseUrl = config.baseUrl;
  const url = new URL('/api/auth/info', baseUrl);

  return new Promise((resolve, reject) => {
    const client = baseUrl.startsWith('https') ? https : http;
    const options = {
      hostname: url.hostname,
      port: url.port || (baseUrl.startsWith('https') ? 443 : 80),
      path: url.pathname,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
      timeout: 10000,
    };

    const req = client.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          if (result.code === 200 || result.code === 0) {
            resolve(result.data);
          } else {
            reject(new Error(`获取用户信息失败: ${result.message}`));
          }
        } catch (e) {
          reject(new Error(`解析用户信息失败: ${e.message}`));
        }
      });
    });

    req.on('error', (e) => reject(new Error(`获取用户信息网络请求失败: ${e.message}`)));
    req.on('timeout', () => { req.destroy(); reject(new Error('获取用户信息请求超时')); });
    req.end();
  });
}

module.exports = { loginByApi, getUserInfoByApi };
