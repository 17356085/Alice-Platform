# Skill: env-checker

## 目标
测试环境就绪检查 — 验证浏览器/驱动/被测系统/账号全部可用，产出环境就绪报告。

## 输入
- 模块名称
- 被测系统 URL
- 测试账号配置 (governance/context/config/test_accounts.yaml)

## 输出
- ENV_CHECK_REPORT.md — 环境就绪报告
  - 浏览器状态 (Chrome version + ChromeDriver 版本匹配)
  - 被测系统可达性 (HTTP status + 响应时间)
  - 登录状态 (账号密码有效 + session 可用)
  - 模块页面可达性 (每页面 URL HTTP 200)
  - 依赖服务状态 (API/数据库/缓存)

## 检查项清单

| 检查项 | 方法 | 预期 |
|--------|------|------|
| Chrome 浏览器 | `chrome --version` | ≥ 120 |
| ChromeDriver | `chromedriver --version` | 版本匹配 Chrome |
| 被测系统可达 | `curl -o /dev/null -w "%{http_code}" $URL` | 200 |
| 登录可用 | Selenium 快速登录脚本 | 登录成功 |
| 模块首页 | HTTP GET 每页面 | 200 |
| API 健康 | `/health` 端点 | healthy |

## 规则
- 任一检查失败 → 标记 env_ready=false, 阻止后续执行
- 超时 10s per check
- 检查结果写入 SOPState
- 快速模式只检查 Chrome + 系统可达 + 登录 (跳过每页面)

## 依赖
- governance/context/config/test_accounts.yaml
- ZJSN_Test-master526/config/base.py (URL 配置)
- Selenium WebDriver

## 边界
- 不执行测试用例
- 不修改环境配置
- 发现问题只报告，不自动修复

---

## Prompt 模板

```text
你是一个资深测试环境工程师。请检查以下模块的测试环境就绪状态。

## 模块信息
- 模块名称：{{module_name}}
- 页面列表：{{page_list}}
- 被测系统：{{target_url}}

## 任务
1. 检查 Chrome + ChromeDriver 版本匹配
2. 检查被测系统可达性 (HTTP GET {{target_url}})
3. 尝试登录 (使用 test_accounts.yaml 中的账号)
4. 检查每个页面的 URL 可达性
5. 汇总到 ENV_CHECK_REPORT.md

## 输出格式
| 检查项 | 状态 | 详情 |
| Chrome 浏览器 | ✅/❌ | version X |
| ChromeDriver | ✅/❌ | version Y |
| 被测系统 | ✅/❌ | HTTP 200 |
| 登录 | ✅/❌ | session OK |
| {{page}} | ✅/❌ | HTTP 200 |

如任一检查失败 → env_ready = false → 停止后续执行
```
