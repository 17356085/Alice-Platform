/**
 * MiniDriver — 微信小程序自动化连接管理（ESM 版，单例）
 *
 * 使用 @weapp-vite/miniprogram-automator + 手动 DevTools 启动 + 端口扫描
 *
 * 流程:
 *   1. 尝试连接已有 DevTools（若配置 WECHAT_WS_PORT）
 *   2. 自动启动 DevTools CLI + 启用自动化 + 扫描 WS 端口
 *   3. 连接自动化 WS → 返回 MiniProgram 实例
 */
import path from 'node:path';
import fs from 'node:fs';
import net from 'node:net';
import { spawn, execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const _require = createRequire(import.meta.url);

function loadEnv() {
  try {
    const dotenv = _require('dotenv');
    dotenv.config({ path: path.resolve(__dirname, '..', '.env') });
  } catch {}
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

/** 扫描本地端口，找到能建立 automator 连接的端口 */
async function scanAutomatorPort(timeout = 20000) {
  const start = Date.now();
  const SCAN_PORTS = [9420, 9421, 9422];
  const automator = _require('miniprogram-automator');

  while (Date.now() - start < timeout) {
    for (const port of SCAN_PORTS) {
      if (!await isPortOpen(port)) continue;
      try {
        const app = await automator.connect({ wsEndpoint: `ws://127.0.0.1:${port}` });
        if (app) { console.log(`  ✅ 端口 ${port} 连接成功`); return app; }
      } catch {}
    }
    await sleep(1000);
  }
  return null;
}

/** 查找开发者工具进程 PID */
function findDevToolsPid() {
  // 方法1: 通过 HTTP 服务端口查找
  try {
    const out = execSync(
      process.platform === 'win32'
        ? 'netstat -ano | findstr "44740"'
        : 'netstat -ano 2>/dev/null | grep "44740"',
      { encoding: 'utf8', timeout: 5000, shell: true }
    );
    for (const line of out.split('\n')) {
      if (!line.includes('LISTENING')) continue;
      const parts = line.trim().split(/\s+/);
      const pid = parts[parts.length - 1];
      if (pid && pid !== '0' && !isNaN(parseInt(pid))) return pid;
    }
  } catch {}
  // 方法2: 通过自动化 WS 端口（9420）查找
  try {
    const out = execSync(
      process.platform === 'win32'
        ? 'netstat -ano | findstr "9420"'
        : 'netstat -ano 2>/dev/null | grep "9420"',
      { encoding: 'utf8', timeout: 5000, shell: true }
    );
    for (const line of out.split('\n')) {
      if (!line.includes('LISTENING')) continue;
      const parts = line.trim().split(/\s+/);
      const pid = parts[parts.length - 1];
      if (pid && pid !== '0' && !isNaN(parseInt(pid))) return pid;
    }
  } catch {}
  return null;
}

/** 获取某进程的所有监听端口（纯 Node.js 实现） */
function findProcessPorts(pid) {
  try {
    const out = execSync(
      process.platform === 'win32'
        ? `netstat -ano | findstr "${pid}"`
        : `netstat -ano 2>/dev/null | grep "${pid}"`,
      { encoding: 'utf8', timeout: 5000, shell: true }
    );
    const ports = [];
    for (const line of out.split('\n')) {
      if (!line.includes('LISTENING')) continue;
      const parts = line.trim().split(/\s+/);
      const addr = parts[1] || '';
      const port = parseInt(addr.split(':').pop(), 10);
      if (!isNaN(port) && port > 0) ports.push(port);
    }
    return [...new Set(ports)];
  } catch {}
  return [];
}

/** 检查端口是否可连（TCP 层面） */
function isPortOpen(port, host = '127.0.0.1') {
  return new Promise(resolve => {
    const s = new net.Socket();
    s.setTimeout(1000);
    s.on('connect', () => { s.destroy(); resolve(true); });
    s.on('error', () => { s.destroy(); resolve(false); });
    s.on('timeout', () => { s.destroy(); resolve(false); });
    s.connect(port, host);
  });
}

/** 构建 CLI 执行前缀（处理中文路径） */
function buildCmdPrefix(cliPath) {
  const hasChinese = /[^\x00-\x7F]/.test(cliPath);
  if (process.platform === 'win32' && hasChinese) {
    return { file: process.env.comspec || 'cmd', args: ['/c', cliPath], shell: true };
  }
  return { file: cliPath, args: [], shell: false };
}

/** 执行 CLI 命令 */
function runCli(cliPath, projectPath, subcmd, extraArgs = []) {
  return new Promise((resolve) => {
    const prefix = buildCmdPrefix(cliPath);
    const args = [...prefix.args, subcmd, '--project', projectPath, ...extraArgs];
    console.log(`[MiniDriver] CLI: ${subcmd} ...`);
    const proc = spawn(prefix.file, args, {
      stdio: 'pipe', windowsHide: true, ...(prefix.shell ? { shell: true } : {})
    });
    let output = '';
    proc.stdout?.on('data', d => output += d);
    proc.stderr?.on('data', d => output += d);
    proc.on('exit', () => resolve(output));
    proc.on('error', () => resolve(output));
    setTimeout(() => resolve(output), 30000);
  });
}

/** 确保 DevTools 自动化已启用 */
async function ensureDevToolsRunning(cliPath, projectPath) {
  // 先检查 9420 是否已开放
  if (await isPortOpen(9420)) {
    console.log('[MiniDriver] 自动化端口 9420 已开放');
    return true;
  }
  // 执行 auto 启用自动化
  console.log('[MiniDriver] 启用自动化...');
  await runCli(cliPath, projectPath, 'auto', ['--auto-port', '9420']);
  await sleep(10000);
  return true;
}

class MiniDriver {
  static _instance = null;
  app = null;
  _connected = false;

  constructor() {}

  static getInstance() {
    if (!MiniDriver._instance) {
      MiniDriver._instance = new MiniDriver();
    }
    return MiniDriver._instance;
  }

  get isConnected() {
    return this._connected && this.app !== null;
  }

  async launch(opts = {}) {
    if (this._connected && this.app) {
      console.log('[MiniDriver] 已有连接，复用实例');
      return this.app;
    }
    // 清掉旧引用
    this.app = null;
    this._connected = false;

    loadEnv();

    const projectPath = path.resolve(
      __dirname, '..',
      opts.projectPath || process.env.MINI_PROJECT_PATH || '../mp-weixin'
    );

    if (!fs.existsSync(projectPath)) {
      throw new Error(`小程序项目路径不存在: ${projectPath}`);
    }

    const wsPort = opts.wsPort || process.env.WECHAT_WS_PORT || '';
    const cliPath = opts.cliPath || process.env.WECHAT_CLI_PATH || '';

    const mod = await import('@weapp-vite/miniprogram-automator');

    // 模式 1: 直接连接已有端口（使用原生 miniprogram-automator，更稳定）
    if (wsPort) {
      try {
        console.log(`[MiniDriver] 连接 ws://127.0.0.1:${wsPort}`);
        const automator = _require('miniprogram-automator');
        this.app = await automator.connect({ wsEndpoint: `ws://127.0.0.1:${wsPort}` });
        this._connected = true;
        console.log('[MiniDriver] ✅ 连接成功');
        return this.app;
      } catch (err) {
        console.log(`[MiniDriver] 连接失败: ${err.message}`);
      }
    }

    // 模式 2: 启动 DevTools + 端口扫描
    if (cliPath) {
      await ensureDevToolsRunning(cliPath, projectPath);
      console.log('[MiniDriver] 扫描自动化端口...');
      const app = await scanAutomatorPort(30000);
      if (app) {
        this.app = app;
        this._connected = true;
        console.log('[MiniDriver] ✅ 自动化连接成功');
        return this.app;
      }
      console.log('[MiniDriver] 端口扫描超时');
    }

    // 模式 3: DevTools 无法使用，提示用户
    throw new Error(
      `无法连接微信开发者工具。\n` +
      `请手动执行以下步骤后重试：\n` +
      `  1. 打开开发者工具: cli.bat open --project ${projectPath}\n` +
      `  2. 启用自动化: cli.bat auto --project ${projectPath}\n` +
      `  3. 设置 WECHAT_WS_PORT=<自动化端口> 到 .env\n` +
      `CLI路径: ${cliPath || '未配置'}\n` +
      `项目路径: ${projectPath}`
    );
  }

  /**
   * 释放连接。保留实例供后续测试复用，但关闭活跃的 WebSocket。
   */
  async close() {
    if (this.app) {
      if (typeof this.app.disconnect === 'function') {
        try { this.app.disconnect(); } catch {}
      }
    }
    this.app = null;
    this._connected = false;
  }

  /** 强制断开连接（仅在所有测试完成后调用） */
  async forceClose() {
    if (this.app) {
      try {
        if (typeof this.app.disconnect === 'function') {
          this.app.disconnect();
        }
      } catch (err) {
        console.warn('[MiniDriver] 断开时出错:', err.message);
      }
      this.app = null;
      this._connected = false;
      console.log('[MiniDriver] 已强制断开');
    }
  }
}

export { MiniDriver };
