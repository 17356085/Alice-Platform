# MODULE_CONTEXT — personnel

## 基本信息
- 模块ID：personnel
- 模块名称：人员管理
- 所属项目：web-automation
- 入口菜单：人员管理（一级菜单）
- 相关角色：admin、部门主管、培训管理员、普通员工

## 模块定位
人员管理是鞍集涂源管理系统的核心业务模块，涵盖员工档案管理、岗位管理、以及完整的培训考试体系（课程→题库→试卷→考试→成绩→证书全链路）。该模块代码量最大（~10,600行），自动化覆盖最完整。

## 核心业务规则
- 员工信息与岗位关联，岗位变更需审批
- 培训课程→培训计划→考试排程形成完整培训链路
- 题库按题型分类（单选/多选/判断/填空/简答）
- 试卷由题库抽题生成，支持手动选题和自动组卷
- 考试评分自动计算客观题，主观题需人工阅卷
- 证书与培训记录关联，完成培训后自动生成

## 模块边界
- 包含：员工管理、岗位管理、培训管理（课程/计划/题库/试卷/考试/在线学习/证书等 13 个子页面）
- 不包含：用户账号管理（属于 system-user）、角色权限配置（属于 system-role）、审批流（属于审批模块）

## 文档缺口
> ⚠️ 以下文档因历史原因暂缺，2026-06 前未安排批量补充。后续模块迭代时逐步补齐。

| 缺少的文档 | 涉及页面 | 计划 |
|-----------|----------|------|
| RISK_MODEL.md（6维度风险） | 全部7个页面 | 后续补充 |
| TEST_DESIGN.md（测试设计） | 全部7个页面 | 后续补充 |
| TEST_CASES.md（测试用例） | 全部7个页面 | 后续补充 |
| AUTO_STRATEGY.md（自动化策略） | 全部7个页面 | 后续补充 |

> 当前状态：每个页面已有 PAGE_CONTEXT.md + TECH_ANALYSIS.md，可直接进入 Phase 2。
> 
> 
> 📌 **2026-06-12 更新**: 4 个需要测试的页面 Phase 1 全部完成：
> - ✅ certificate (证书管理) — PAGE_CONTEXT + PAGE_ELEMENT_POSITION
> - ✅ practice (自主练习) — PAGE_CONTEXT + PAGE_ELEMENT_POSITION  
> - ✅ study-record (学习记录) — PAGE_CONTEXT + PAGE_ELEMENT_POSITION
> - ✅ wrong-question (错题本) — PAGE_CONTEXT + PAGE_ELEMENT_POSITION
> - ⚠️ 三个个人端页面(practice/study-record/wrong-question)当前无数据，表格列为推断，需录入测试数据后确认

## 关键页面

### 工厂人员管理组
| 页面ID | 页面名称 | 路由 | 状态 | 代码 |
|--------|----------|------|------|------|
| employee | 员工管理 | #/personnel/employee | ✅ 已覆盖 | EmployeeManagePage.py (123行) |
| post | 岗位管理 | #/personnel/post | ✅ 已覆盖 | PostManagePage.py (542行) |

### 培训管理组 (12 pages)
| 页面ID | 页面名称 | 路由 | 状态 | 代码 |
|--------|----------|------|------|------|
| course | 课程管理 | #/personnel/training/course | ✅ 已覆盖 | CourseManagePage.py (570行) |
| plan | 培训计划 | #/personnel/training/plan | ✅ 已覆盖 | TrainPlanPage.py (1528行) |
| question | 题库管理 | #/personnel/training/question | ✅ 已覆盖 | QuestionBankPage.py (702行) |
| paper | 试卷管理 | #/personnel/training/paper | ✅ 已覆盖 | PaperManagePage.py (1531行) |
| exam | 考试管理 | #/personnel/training/examArrange | ✅ 已覆盖 | ExamManagePage.py (856行) |
| certificate | 证书管理 | #/personnel/training/certificate | ❌ 隐藏(visible:0) | CertificateManagePage.py |
| practice | 自主练习 | #/personnel/training/practice | ✅ 已覆盖 | PracticePage.py |
| study-record | 学习记录 | #/personnel/training/studyRecord | ✅ 已覆盖 | StudyRecordPage.py |
| wrong-question | 错题本 | #/personnel/training/wrongQuestion | ✅ 已覆盖 | WrongQuestionPage.py |
| my-exam | 考试测评 | #/personnel/training/my-exam | 🟡 待评估 — 考试入口 | — |
| exam-record | 考试记录 | #/personnel/training/examRecord | 🟢 低优先级 | — |
| online-study | 在线学习 | #/personnel/training/onlineStudy | 🟢 低优先级 | — |
| my-archive | 个人学习档案 | #/personnel/training/my-archive | 🟢 低优先级 | — |

### 承包商管理组 (5 pages)
| 页面ID | 页面名称 | 路由 | 状态 | 代码 |
|--------|----------|------|------|------|
| contractor-unit | 承包商单位 | #/personnel/contractor | ✅ 已覆盖 | ContractorUnitPage.py |
| contractor-personnel | 承包商人员 | #/personnel/contractor (共享) | ✅ 已覆盖 | ContractorPersonnelPage.py |
| entry-approval | 入场审批 | #/personnel/contractor/approval | ✅ 已覆盖 | EntryApprovalPage.py |
| entry-record | 入场记录 | #/personnel/contractor/record | ✅ 已覆盖 | EntryRecordPage.py |
| entry-confirm | 入场确认 | #/personnel/contractor/confirm | ✅ 已覆盖 (new 2026-06-15) | EntryConfirmPage.py |

### 访客管理组 (1 page)
| 页面ID | 页面名称 | 路由 | 状态 | 代码 |
|--------|----------|------|------|------|
| visitor | 访客管理 | #/personnel/visitor | ❌ 无覆盖 (visible:0) | — |

## 风险概览
| 风险ID | 描述 | 等级 | 缓解措施 |
|--------|------|------|----------|
| RISK-PERS-001 | 试卷自动组卷逻辑复杂，抽题规则错误导致考试不公平 | P0 | 参数化验证组卷规则（题型分布/难度分布/分值） |
| RISK-PERS-002 | 考试提交时网络中断导致答案丢失 | P0 | 前端本地暂存答案 + 断网重试 |
| RISK-PERS-003 | 员工信息与用户账号数据不一致 | P1 | 数据一致性校验 + 定时同步 |
| RISK-PERS-004 | 培训证书生成逻辑错误（完成条件判断） | P1 | 参数化验证证书生成条件 |
| RISK-PERS-005 | 大量题库数据下页面性能问题 | P2 | 分页 + 虚拟滚动 |

## 依赖关系
- 上游：system-user（用户基础数据）、system-role（角色权限）
- 下游：审批模块（岗位变更审批）

## 自动化代码
- Page Objects：`page/personnel_page/`（16 个文件，~10,500 行）
- 测试脚本：`script/personnel/`（16 个文件，~3,500 行）
- conftest：`script/personnel/conftest.py`（16 条 hash 路由 + 4 个 teardown）
- 数据文件：暂无独立 data 文件
- 🆕 2026-06-15: 新增 EntryConfirmPage.py + test_entry_confirm.py（入场确认，6P/0F/3S）

## 治理备注
- 本文件由 `module-modeling` Skill 在 2026-06-11 产出
- 旧 `contexts/人员管理/` 目录不存在，此为首次建模
- 15 个子页面中 7 个已有自动化代码
- 8 个未覆盖页面经 2026-06-12 Selenium 实机分析，**4 个需要测试**（certificate/practice/study-record/wrong-question），详细报告见 `governance/artifacts/audits/personnel-untested-pages-analysis.md`（原"纯前端展示"判断已修正）
- TrainPlanPage 有 recovered 版本（代码恢复）


<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-stats -->
<!-- Source: tools/sync_progress.py — regenerated on each SOP run -->
## 自动统计数据 (更新于 2026-06-17 16:53)

| 指标 | 数值 |
|------|:---:|
| 测试文件 | 18 (script/personnel/test_*.py) |
| Page Object | 17 (page/personnel_page/*.py) |
| 治理文档 | 99 .md 文件 |
| TECH_ANALYSIS | 16 |
| AUTO_STRATEGY | 12 |
| RISK_MODEL | 11 |
| PAGE_CONTEXT | 17 |
| SOP 状态 | completed |
| Phase 完成 | Automation, Bug Analysis, Data Sanitization, Execute & Debug, Knowledge, Project Init, Report, Requirement, Test Design |

> 此段由 sync_progress.py 自动更新。手动编辑会被覆盖。
<!-- ⚠️ AUTO-GENERATED SECTION END: module-stats -->