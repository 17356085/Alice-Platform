# TestIntern Library — 历史知识库（存档区）

> ⚠️ **本目录已于 2026-06-11 冻结为历史存档。**
>
> **新内容请统一写入 `governance/` 治理层。**
>
> - 上下文/模块文档 → `governance/context/`
> - 测试报告 → Allure 生成 + `governance/context/*/summaries/`
> - 模板 → `governance/templates/`
> - Skill/Prompt → `governance/skills/`
> - 工作流 → `governance/workflows/`

---

## 保留内容

| 目录 | 内容 | 说明 |
|------|------|------|
| **01-学习笔记/** | 踩坑经验集、学习笔记 | 可继续补充，属个人学习记录 |
| **03-工作日志/** | 日报/周报模板 | 临时工作记录，可继续使用 |
| **05-资源与参考/** | SOP 全量文档、已冻结的 AI提示词库 | 历史参考，新 SOP 摘要见 `governance/workflows/sop-summary.md` |

## 已迁移/删除

| 原目录 | 迁移目标 | 状态 |
|--------|----------|:----:|
| 02-项目文档/contexts/ | `governance/context/` | ✅ 已迁移 |
| 02-项目文档/_templates/ | `governance/templates/` | ✅ 已迁移 |
| 02-项目文档/testcases/ | 对应模块 `TEST_CASES.md` | ✅ 已迁移 |
| 02-项目文档/测试进度追踪.md | `governance/context/progress-tracking.md` | ✅ 已迁移 |
| 04-测试报告/ | Allure | ✅ 已淘汰 |

## 项目信息

| 属性 | 值 |
|------|-----|
| **项目名称** | 鞍集（凌源）管理系统 |
| **被测系统** | Web管理端（Vue3 + Element Plus）+ 微信小程序 |
| **测试框架** | Python + pytest + Selenium + Allure |
| **最新治理层** | `governance/` |
