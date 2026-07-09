# Phase 7 Acceptance Matrix

| Tracking ID | Status | ETA | 测试项 | 负责人 | Reviewer | 回滚点 |
| --- | --- | --- | --- | --- | --- | --- |
| PH7-PR-7.1 | Done | 1 day | Kernel 契约评审、Facade 边界走查、依赖方向检查 | TL | Runtime Owner, Platform Owner | 回退 Kernel 契约与文档基线 |
| PH7-PR-7.2 | Done | 2 days | SDK Engine 执行回归、`_internal.graph` 旁路清理检查、最小 Mock Provider smoke | Runtime Owner | TL, QA Reviewer | 回退 standalone Engine 调用链 |
| PH7-PR-7.3 | Done | 2 days | CLI/Server/Chat 统一 Kernel 集成测试、结果语义一致性测试、平台增量语义回归 | Platform Owner | Runtime Owner, TL | 回退 Platform Facade 到旧工厂接线 |
| PH7-PR-7.4 | Done | 3 days | Port 注入测试、Capability/Memory/Knowledge/Replay/MCP 适配测试、动态导入消除检查 | Runtime Owner | MCP Owner, Knowledge Owner, TL | 回退显式 Port 注入层，保留原 Bridge |
| PH7-PR-7.5 | Done | 2 days | workspace package 安装测试、测试收集检查、Docker/CI 构建 smoke、最小发布链验证 | Infra Owner | QA Reviewer, TL | 回退 CI/Docker/打包链改动 |
| PH7-PR-7.6 | Done | 2 days | clean env wheel 安装、`import alice_engine` smoke、Kernel Contract Test、无 `aitest` 独立执行验证 | QA Reviewer | Runtime Owner, Platform Owner, TL | 回退独立发布门禁与契约测试 |

## 线上验收操作清单

建议优先在一台可访问 PyPI、Docker Hub、GitHub Actions 的环境执行以下命令。

Windows / PowerShell 一键验收：

```powershell
pwsh -File .\scripts\phase7_acceptance.ps1 `
  -WorkspaceMode fresh `
  -PythonPath C:\Python311\python.exe `
  -DockerTag aitest-phase7-ci
```

当前本机离线受限场景的降级跑法：

```powershell
pwsh -File .\scripts\phase7_acceptance.ps1 `
  -WorkspaceMode reuse `
  -PythonPath D:\Desktop\Alice\.venv\Scripts\python.exe `
  -SkipDocker `
  -UseSystemSitePackagesForStandalone
```

GitHub Actions 线上验收：

1. 推送当前分支并打开 PR。
2. 确认以下 job 全部为绿色：
   - `Test (Python 3.11)`
   - `Test (Python 3.12)`
   - `SDK Standalone (Python 3.11)`
   - `Build Docker image`

## 预期结果

- workspace import smoke 输出 `workspace imports OK`
- collect-only 接近 `1346 collected`
- CI 风格测试接近 `1344 passed, 2 skipped`
- standalone wheel smoke 输出 `standalone wheel smoke OK`
- Docker 构建阶段成功产出 `aitest-phase7-ci` 或指定 tag 的镜像
- 若容器启动足够快，`/health` 返回 HTTP 200；若未及时启动，脚本会给 warning，但不应掩盖构建本身是否成功
- GitHub Actions 中 `sdk-standalone` 不应再出现旧字段 `request.request_id` 引发的 smoke 失败

## 判定口径

- `PH7-PR-7.5` 已转为 `Done` 的前提：
  - 脚本 fresh 模式或等价线上命令完成 workspace install、collect、pytest、docker build
  - GitHub Actions 的 `test` 与 `build` job 真实跑绿
- `PH7-PR-7.6` 已转为 `Done` 的前提：
  - clean env wheel 安装成功
  - `import alice_engine` 不加载 `aitest`
  - standalone smoke 通过，且 `Engine(..., kernel=...)` 路径通过
  - GitHub Actions 的 `sdk-standalone` job 真实跑绿
