# Skill: evidence-collector

## 目标
测试失败时自动采集多维证据 — 截图、DOM snapshot、Console logs、Network trace、Timeline。为 Failure Analyst 提供完整证据链。

## 触发时机
Execution Agent 检测到测试失败后，在进入 Failure Analyst 之前自动调用。

## 输入
- 失败测试 ID (如 `test_alarm_config.py::test_create_alarm`)
- 失败时间戳
- 被测页面 URL
- WebDriver session (如可用)

## 输出
- EVIDENCE_BUNDLE.json — 结构化证据包
  ```json
  {
    "test_id": "test_alarm_config.py::test_create_alarm",
    "timestamp": "2026-06-23T10:30:00",
    "evidence": {
      "screenshot": "governance/artifacts/screenshots/equipment/alarm-fail-001.png",
      "dom_snapshot": "<html>...失败时刻的完整 DOM</html>",
      "console_logs": ["[ERROR] Uncaught TypeError: ...", "[WARN] ..."],
      "network_trace": [{"url": "/api/alarm", "status": 500, "body": "..."}],
      "timeline": {"page_load": 2.3, "render": 1.1, "api_wait": 4.5, "total": 8.2}
    },
    "environment": {
      "browser": "Chrome 130",
      "viewport": "1920x1080",
      "os": "Windows 11"
    }
  }
  ```

## 采集方法

| 证据类型 | 采集方法 | 工具 |
|---------|---------|------|
| 截图 | `driver.save_screenshot()` 全页 + 失败元素区域 | Selenium |
| DOM | `driver.page_source` 或 `driver.execute_script("return document.documentElement.outerHTML")` | Selenium |
| Console | `driver.get_log("browser")` 过滤 ERROR/WARN | Selenium |
| Network | `driver.execute_script("return window.performance.getEntries()")` 或 BrowserMob Proxy | Performance API |
| Timeline | `performance.timing` + 自定义打点 | Performance API |

## 规则
- 截图保留全页 + 失败元素局部（裁剪到 800×600）
- DOM 截断到 5000 字符（LLM 上下文限制）
- Console 仅保留 ERROR + WARN，去重
- Network 仅保留失败请求 (status ≥ 400) + 最慢的 3 个请求
- 证据包大小 ≤ 2MB（含 base64 截图）
- 存储路径: `governance/artifacts/evidence/{module}/{test_id}-{timestamp}/`

## 依赖
- Selenium WebDriver (需 session 存活)
- ZJSN_Test-master526/base/browser_driver.py

## 边界
- 不分析根因（那是 root-cause-analyzer 的职责）
- 不修复问题（那是 Automation Developer 的职责）
- WebDriver 已关闭时仅采集 trace 日志中的错误信息

---

## Prompt 模板

```text
你是一个测试证据采集专家。测试 {{test_id}} 刚刚失败，请采集多维证据。

## 任务
1. 截图当前页面（全页 + 失败元素局部）
2. 提取 DOM snapshot（截断到 5000 字符）
3. 收集 Console ERROR/WARN 日志
4. 收集 Network 失败请求（status ≥ 400）
5. 收集 Performance Timeline
6. 打包到 EVIDENCE_BUNDLE.json

## 约束
- 证据包 ≤ 2MB
- DOM/Console/Network 去重
- 如果 WebDriver 已断开，仅从 trace log 提取错误信息
```
