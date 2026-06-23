# Governance Context — 平台运行时配置

> 本目录存放平台引擎运行时所需的配置文件和索引。**不存放项目业务数据**（项目数据在 TestingProject 各项目 `.tlo/` 下）。

## 目录内容

| 路径 | 用途 | 更新方式 |
|------|------|----------|
| `environments.yaml` | 项目环境注册（URL、凭证引用） | 手动 + CLI `aitest project register` |
| `project-index.yaml` | 活跃项目索引 | CLI 自动 + 手动 |
| `known-issues.yaml` | 已知问题注册表（Element Plus / Selenium 坑位） | 平台自动 + 手动 |
| `shared-language.md` | 平台术语 + 业务术语歧义消除 | 手动 |
| `source-of-truth.md` | 事实来源声明 | 手动 |
| `config/test_accounts.yaml` | 测试账号凭证（技能 `env-checker` / `data-preparer` 引用） | 手动 |
| `interfaces/` | 数据接口 schema 定义 | 手动 |
| `tracking/` | 治理修复追踪（治理验证冲刺产物） | 手动 |
| `projects/dev-platform/` | 平台自身开发文档 | 手动 |
| `projects/_archived/` | 已归档项目上下文（历史参考） | 手动 |

## 与 .tlo/ 的关系

ADR-001 规定：项目上下文跟随项目。平台不再在此目录存放项目业务数据。

```
Alice (平台)
├── governance/context/   ← 平台级配置（本目录）
│   └── projects/_archived/  ← 已归档旧项目数据
│
TestingProject (项目数据)
├── ZJSN_Test-master526/.tlo/   ← ZJSN 项目上下文
├── mp-weixin/.tlo/             ← 小程序源码上下文
└── mp-weixin-automator/.tlo/   ← 小程序自动化上下文
```

## 新增配置规则

- 平台运行时需要读取的配置 → 放本目录
- 项目特有的业务知识 → 放项目 `.tlo/knowledge/`
- 架构决策 / 计划文档 → 放 `docs/`（非本目录）
- ADR → 放 `docs/adr/`
