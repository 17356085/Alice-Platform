# WorkStudy — 鞍集涂源管理系统 · AI 辅助测试开发项目

> AI 第一入口为 [`CLAUDE.md`](CLAUDE.md)。新 AI 进入项目后请先阅读该文件。

---

## 项目结构（30 秒速览）

```
WorkStudy/
├── CLAUDE.md                 ← 必读：口语化入口 + 项目全景 + 编码红线
├── governance/               ← 治理层（唯一事实源 + Skill + Workflow）
│   ├── context/              ← 项目/模块/页面上下文（7个模块已映射）
│   ├── skills/               ← 29 个 Skill（含 Prompt 模板）
│   ├── workflows/            ← 9 个标准化流程
│   └── templates/            ← 11 个输出格式模板
│
├── ZJSN_Test-master526/      ← Web 自动化测试工程（Python + Selenium + pytest）
├── mp-weixin-automator/      ← 小程序自动化测试工程（Node.js）
├── mp-weixin/                ← 微信小程序源码（参考）
│
└── TestIntern_library/       ← ⚠️ 已冻结的历史存档
```

## 快速入口

| 你想做什么 | 路径 |
|-----------|------|
| 了解全部能力 | [`CLAUDE.md`](CLAUDE.md) → 口语化入口（21条"你可以这样说"） |
| 查看当前测试进度 | [`governance/context/tracking/progress-tracking.md`](governance/context/tracking/progress-tracking.md) |
| 查看编码规范 | [`CLAUDE.md`](CLAUDE.md) → §五 代码红线 |
| 了解治理层设计 | [`governance/README.md`](governance/README.md) |
| 查看 Skill 注册表 | [`governance/skills/skill-registry.yaml`](governance/skills/skill-registry.yaml) |

## 技术栈

| 维度 | 内容 |
|------|------|
| Web 前端 | Vue 3 + Element Plus |
| Web 自动化 | Python 3 + pytest + Selenium + Allure |
| 小程序自动化 | Node.js + mp-weixin-automator |
| CI/CD | Jenkins |
