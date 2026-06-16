#!/usr/bin/env node
/**
 * 全量测试运行器 — 独立进程版 + DevTools 批次重启
 *
 * 每个测试文件独立进程运行，避免一个文件超时拖垮其他文件。
 * 每 N 个文件后重启 DevTools，彻底清除 webview 累积。
 *
 * 用法: node run-tests.mjs
 */
import path from 'node:path';
import fs from 'node:fs';
import net from 'node:net';
import { fileURLToPath } from 'node:url';
import { spawn, execSync } from 'node:child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPORT_FILE = path.join(__dirname, 'artifacts', 'test-report.txt');

// ── 配置 ────────────────────────────────────────────
const BATCH_SIZE = 4;           // 每批运行 N 个文件后重启 DevTools
const DEVTOOLS_PORT = 44740;    // DevTools HTTP 端口
const AUTO_PORT = 9420;         // 自动化 WS 端口
const RESTART_WAIT = 45000;     // 重启后等待时间(ms)

// ── 从 .env 读取配置 ──────────────────────────────────
function loadEnv() {
  const envPath = path.join(__dirname, '.env');
  const env = { ...process.env };
  if (fs.existsSync(envPath)) {
    const content = fs.readFileSync(envPath, 'utf8');
    for (const line of content.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eqIdx = trimmed.indexOf('=');
      if (eqIdx === -1) continue;
      const key = trimmed.slice(0, eqIdx).trim();
      const val = trimmed.slice(eqIdx + 1).trim();
      if (!env[key]) env[key] = val;
    }
  }
  return env;
}

const env = loadEnv();
const CLI_PATH = env.WECHAT_CLI_PATH || 'D:/myprogram/微信web开发者工具/cli.bat';
const PROJECT_PATH = env.MINI_PROJECT_PATH
  ? path.resolve(__dirname, env.MINI_PROJECT_PATH)
  : path.resolve(__dirname, '..', 'mp-weixin');

// ── 测试文件列表（按优先级排序） ──────────────────────
const TEST_FILES = [
  'tests/smoke/test_smoke.test.mjs',
  'tests/p0-core/test_login.test.mjs',
  'tests/p0-core/test_home.test.mjs',
  'tests/p0-core/test_alarm.test.mjs',
  'tests/test_approval_flow.test.mjs',
  'tests/test_study_exam_flow.test.mjs',
  'tests/p1-high/test_role_permissions.test.mjs',
  'tests/p2-medium/test_lab_sampling.test.mjs',
  'tests/p2-medium/test_my_application.test.mjs',
  'tests/p2-medium/test_practice_wrong.test.mjs',
  'tests/p2-medium/test_visitor.test.mjs',
  'tests/p2-medium/test_personnel.test.mjs',
  'tests/p3-snapshot/test_tank_equipment.test.mjs',
  'tests/p3-snapshot/test_sales_report.test.mjs',
  'tests/p3-snapshot/test_settings.test.mjs',
  'tests/p3-snapshot/test_about_feedback.test.mjs',
  'tests/test_diagnostics.test.mjs',
];

// ── DevTools 重启 ────────────────────────────────────

/** 检查端口是否可连 */
function isPortOpen(port, host = '127.0.0.1') {
  return new Promise(resolve => {
    const s = new net.Socket();
    s.setTimeout(2000);
    s.on('connect', () => { s.destroy(); resolve(true); });
    s.on('error', () => { s.destroy(); resolve(false); });
    s.on('timeout', () => { s.destroy(); resolve(false); });
    s.connect(port, host);
  });
}

/** 执行 CLI 命令（处理中文路径） */
function runCli(args, timeout = 30000) {
  return new Promise((resolve) => {
    const hasChinese = /[^\x00-\x7F]/.test(CLI_PATH);
    const proc = spawn(
      hasChinese ? (process.env.comspec || 'cmd') : CLI_PATH,
      hasChinese ? ['/c', CLI_PATH, ...args] : args,
      { stdio: 'pipe', windowsHide: true, ...(hasChinese ? { shell: true } : {}) }
    );
    let output = '';
    proc.stdout?.on('data', d => output += d);
    proc.stderr?.on('data', d => output += d);
    const timer = setTimeout(() => { try { proc.kill(); } catch {}; resolve(output); }, timeout);
    proc.on('exit', () => { clearTimeout(timer); resolve(output); });
    proc.on('error', () => { clearTimeout(timer); resolve(output); });
  });
}

/** 等待端口就绪 */
async function waitForPort(port, timeout = 30000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    if (await isPortOpen(port)) return true;
    await sleep(2000);
  }
  return false;
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

/**
 * 重启微信开发者工具
 * 步骤: quit → 等待 → open → 等待 → auto → 等待端口就绪
 */
async function restartDevTools() {
  console.log('\n🔄 [DevTools] 正在重启...');

  for (let attempt = 0; attempt < 2; attempt++) {
    if (attempt > 0) console.log('  🔄 [DevTools] 重试重启...');

    // 1. 关闭
    console.log('  [1/4] 关闭 DevTools...');
    await runCli(['quit']);
    await sleep(8000);

    // 2. 打开项目
    console.log('  [2/4] 打开项目...');
    await runCli(['open', '--project', PROJECT_PATH, '--port', String(DEVTOOLS_PORT)]);
    await sleep(12000);

    // 3. 启用自动化
    console.log('  [3/4] 启用自动化...');
    await runCli(['auto', '--project', PROJECT_PATH, '--auto-port', String(AUTO_PORT)]);
    await sleep(8000);

    // 4. 等待自动化端口就绪
    console.log('  [4/4] 等待自动化端口...');
    const ready = await waitForPort(AUTO_PORT, RESTART_WAIT);
    if (ready) {
      console.log('✅ [DevTools] 重启完成，自动化端口就绪\n');
      return true;
    }
    console.log(`⚠️ [DevTools] 重启超时 (attempt ${attempt + 1}/2)\n`);
  }

  console.log('❌ [DevTools] 重启失败，继续尝试...\n');
  return false;
}

// ── 测试输出解析 ──────────────────────────────────────

function parseSpecOutput(output) {
  const tests = [];
  let currentSuite = '';
  let currentTest = null;

  for (const line of output.split('\n')) {
    const sm = line.match(/^▶ (.+)$/);
    if (sm) { currentSuite = sm[1].trim(); continue; }

    const pm = line.match(/^  ✔ (.+?) \([\d.]+ms\)$/);
    if (pm) { tests.push({ suite: currentSuite, name: pm[1].trim(), passed: true, error: '' }); currentTest = null; continue; }

    const fm = line.match(/^  ✖ (.+?) \([\d.]+ms\)$/);
    if (fm) { currentTest = { suite: currentSuite, name: fm[1].trim(), passed: false, error: '' }; tests.push(currentTest); continue; }

    if (currentTest && !currentTest.passed) {
      const t = line.trim();
      if (t && (t.startsWith('Error:') || t.startsWith('AssertionError'))) {
        currentTest.error += t.slice(0, 120) + ' ';
      }
    }
  }
  return tests;
}

function runTestFile(filePath) {
  return new Promise((resolve) => {
    const fullPath = path.resolve(__dirname, filePath);
    if (!fs.existsSync(fullPath)) {
      resolve({ file: filePath, tests: [], status: 'skipped' });
      return;
    }

    const proc = spawn(process.execPath, ['--test', '--test-concurrency', '1', '--test-reporter', 'spec', fullPath], {
      cwd: __dirname,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, PATH: process.env.PATH },
    });

    let stdout = '';
    proc.stdout.on('data', (d) => { stdout += d.toString(); });
    proc.stderr.on('data', (d) => { stdout += d.toString(); });

    const timer = setTimeout(() => {
      proc.kill('SIGTERM');
      const tests = parseSpecOutput(stdout);
      resolve({ file: filePath, tests, status: 'timeout', raw: stdout.slice(-500) });
    }, 300000);

    proc.on('exit', (code) => {
      clearTimeout(timer);
      const tests = parseSpecOutput(stdout);
      resolve({ file: filePath, tests, status: code === 0 ? 'passed' : 'failed', raw: stdout.slice(-500) });
    });
  });
}

// ── 报告生成 ──────────────────────────────────────────

function generateReport(results, duration) {
  const lines = [];
  const now = new Date();

  lines.push('='.repeat(70));
  lines.push(`  中集数科智能互联 — 小程序自动化测试报告`);
  lines.push(`  时间: ${now.toLocaleString('zh-CN')}`);
  lines.push(`  总耗时: ${duration}s`);
  lines.push('='.repeat(70));
  lines.push('');

  let totalPassed = 0;
  let totalFailed = 0;

  for (const r of results) {
    if (r.status === 'skipped') { lines.push(`  ⏭ ${r.file}\n`); continue; }

    const passed = r.tests.filter(t => t.passed).length;
    const failed = r.tests.filter(t => !t.passed).length;
    totalPassed += passed;
    totalFailed += failed;

    const icon = failed === 0 && r.status !== 'timeout' ? '✅' : '❌';
    lines.push(`  ${icon} ${r.file}  (${r.status})`);
    if (r.status === 'timeout') lines.push(`     ⚠ 超时 180s`);

    for (const t of r.tests) {
      if (t.passed) {
        lines.push(`       ✅ ${t.name}`);
      } else {
        lines.push(`       ❌ ${t.name}`);
        if (t.error) lines.push(`          原因: ${t.error.slice(0, 150)}`);
      }
    }

    if (r.tests.length === 0 && r.raw) {
      const errLine = r.raw.split('\n').find(l => l.includes('Error') || l.includes('连接') || l.includes('connect'));
      if (errLine) lines.push(`      ⚠ ${errLine.trim().slice(0, 120)}`);
    }
    lines.push('');
  }

  const total = totalPassed + totalFailed;
  lines.push('='.repeat(70));
  lines.push(`  汇总`);
  lines.push('='.repeat(70));
  lines.push(`  总测试文件: ${results.filter(r => r.status !== 'skipped').length}`);
  lines.push(`  总测试用例: ${total}`);
  lines.push(`  通过: ${totalPassed}  (${total > 0 ? (totalPassed / total * 100).toFixed(1) : 0}%)`);
  lines.push(`  失败: ${totalFailed}  (${total > 0 ? (totalFailed / total * 100).toFixed(1) : 0}%)`);
  lines.push('');

  return lines.join('\n');
}

// ── 主流程 ────────────────────────────────────────────

async function main() {
  const artifactsDir = path.join(__dirname, 'artifacts');
  if (!fs.existsSync(artifactsDir)) fs.mkdirSync(artifactsDir, { recursive: true });

  const start = Date.now();
  const results = [];

  for (let i = 0; i < TEST_FILES.length; i++) {
    // 每 BATCH_SIZE 个文件后重启 DevTools（第一批除外）
    if (i > 0 && i % BATCH_SIZE === 0) {
      console.log(`\n📦 批次 ${Math.floor(i / BATCH_SIZE) + 1}/${Math.ceil(TEST_FILES.length / BATCH_SIZE)} — 重启 DevTools...`);
      await restartDevTools();
    }

    const file = TEST_FILES[i];
    const result = await runTestFile(file);
    results.push(result);

    const p = result.tests.filter(t => t.passed).length;
    const f = result.tests.filter(t => !t.passed).length;
    console.log(`  ${result.status === 'passed' ? '✅' : '❌'} ${file}  (${p}通过/${f}失败)`);
  }

  const duration = ((Date.now() - start) / 1000).toFixed(1);
  const report = generateReport(results, duration);

  fs.writeFileSync(REPORT_FILE, report, 'utf8');
  console.log(`\n${report}`);
  console.log(`  报告已保存: ${REPORT_FILE}\n`);
}

main();
