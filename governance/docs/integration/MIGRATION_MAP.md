# Migration Map

## 原则
- 先挂接
- 后收敛
- 先索引
- 后迁移
- 先模板化
- 后 Skill 化

## 旧资产映射
| 旧资产 | 新位置 | 当前动作 | 后续动作 |
| --- | --- | --- | --- |
| PROJECT_CONTEXT.md | context/projects/web-automation/PROJECT_CONTEXT.md | 引用 | 提炼稳定共性 |
| PROJECT_WEB_CONTEXT.md | context/projects/web-automation/PROJECT_CONTEXT.md | 引用 | 拆项目级事实 |
| PROJECT_WX_CONTEXT.md | context/projects/miniapp-automation/PROJECT_CONTEXT.md | 引用 | 拆项目级事实 |
| TestIntern_library/.../contexts/ | context/projects/web-automation/modules/ | 建模块索引 | 逐步对齐结构 |
| AI提示词库.md | skills/prompt-library-index.md | 已建索引 | 全量提示词仍在旧文件，已建立逐 Phase 到治理层 Skill/Template 的映射表 |
| SOP.md | workflows/sop-summary.md | 已建摘要映射 | 提取了 10 个 Phase 结构与会话规则，映射到现有 Workflow |
| Jenkinsfile | skills/ci-pipeline-analysis.md | 建索引 | 抽取规则与复用动作 |

## 当前状态
- [x] 项目索引建立
- [x] 模块索引建立
- [x] 事实源规则建立
- [x] Workflow 注册表建立（9个）
- [x] Skill 注册表建立（29个）
- [x] 模板统一命名
- [x] PROJECT_CONTEXT 扩展至 200 行（含 BasePage API + EP-001~011 + 编码规范）
- [x] code-generation 拆分为 3 个独立 Skill
- [x] 旧 AI提示词库.md 冻结（DEPRECATED 标记）
- [x] 29/29 Page Object 全部重构完成（继承 BasePage，去绝对XPath，去 time.sleep，去 print）
- [x] 测试脚本 sleep 清理完成（23 个清单文件，57→1 等）
- [x] CLAUDE.md §五 新增「代码红线」速查表 + 自检命令
- [x] CLAUDE.md 口语化路由表（21条 "你可以这样说 → Skill"）
- [x] Tank 模块 SOP 全闭环（Phase 0.5→9，100%）
- [x] TestIntern_library 重组：删 02-项目文档/04-测试报告/，SOP 归档到 05-资源与参考
- [x] 测试进度追踪 → governance/context/tracking/progress-tracking.md
- [x] governance/artifacts/ 旧报告归档至 archive/，新报告按类型分类至 bug-analysis/ test-summaries/ sop-status/ audits/ 等子目录
- [x] agents/ 标记为"规划中"
- [ ] MenuManagePage 重构（38处 time.sleep）

## 页面级映射进展
| 旧页面资产 | 新位置 | 状态 | 说明 |
| --- | --- | --- | --- |
| `contexts/system-user/pages/user-list/` | `context/projects/web-automation/modules/system-user/pages/user-list/` | 已映射 | 已同步 PAGE_CONTEXT、ANALYSIS、RISK_MODEL、TEST_DESIGN、TEST_CASES、TECH_ANALYSIS、AUTO_STRATEGY |
| `contexts/system-user/pages/user-form/` | `context/projects/web-automation/modules/system-user/pages/user-form/` | 已映射 | 已同步 PAGE_CONTEXT |
| `contexts/system-role/ROLE_CONTEXT.md` | `context/projects/web-automation/modules/system-role/pages/role-list/PAGE_CONTEXT.md` | 已映射 | 已将旧页面实测文档映射为 role-list 页面上下文 |
| `contexts/system-role/TEST_ANALYSIS.md` | `context/projects/web-automation/modules/system-role/pages/role-list/ANALYSIS.md` | 已映射 | 已将测试视角分析映射为 role-list 页面分析文档 |
| `contexts/system-role/RBAC_TEST_PLAN.md` | `context/projects/web-automation/modules/system-role/RBAC_TEST_PLAN.md` | 已映射 | 已将 RBAC 权限矩阵测试方案映射为模块级专题文档 |
| `contexts/equipment/pages/alarm-config/PAGE_CONTEXT.md` | `context/projects/web-automation/modules/equipment/pages/alarm-config/PAGE_CONTEXT.md` | 已映射 | 已将设备报警配置页面说明映射到新骨架 |
| `contexts/equipment/pages/alarm-config/PAGE_ELEMENT_POSITION.md` | `context/projects/web-automation/modules/equipment/pages/alarm-config/PAGE_ELEMENT_POSITION.md` | 已映射 | 已将元素定位文档映射到新骨架并统一文件标题 |
| `contexts/equipment/pages/camera/PAGE_CONTEXT.md` | `context/projects/web-automation/modules/equipment/pages/camera/PAGE_CONTEXT.md` | 已映射 | 已将摄像头管理页面说明映射到新骨架 |
| `contexts/equipment/pages/camera/PAGE_ELEMENT_POSITION.md` | `context/projects/web-automation/modules/equipment/pages/camera/PAGE_ELEMENT_POSITION.md` | 已映射 | 已将元素定位文档映射到新骨架并统一文件标题 |
| `contexts/equipment/pages/maintenance/PAGE_CONTEXT.md` | `context/projects/web-automation/modules/equipment/pages/maintenance/PAGE_CONTEXT.md` | 已映射 | 已将设备维保页面说明映射到新骨架 |
| `contexts/equipment/pages/maintenance/PAGE_ELEMENT_POSITION.md` | `context/projects/web-automation/modules/equipment/pages/maintenance/PAGE_ELEMENT_POSITION.md` | 已映射 | 已将元素定位文档映射到新骨架并统一文件标题 |
| `contexts/equipment/pages/key-param/PAGE_ELEMENT_POSITION.md` | `context/projects/web-automation/modules/equipment/pages/key-param/PAGE_ELEMENT_POSITION.md` | 已映射 | 旧资产为骨架，待从自动化代码补全定位器 |
| `contexts/equipment/pages/key-param/TEST_DESIGN.md` | `context/projects/web-automation/modules/equipment/pages/key-param/TEST_DESIGN.md` | 已映射 | 旧资产为骨架，PAGE_CONTEXT 为治理层补位 |
| `contexts/system-management/MODULE_CONTEXT.md` | `context/projects/web-automation/modules/system-management/MODULE_CONTEXT.md` | 已映射 | 摘要层迁移：保留子页面清单、多角色关联度分类，用户管理/角色管理下沉至独立模块，其余子模块暂留汇总层 |
| `contexts/system-management/MODULE_CONTEXT.md §5.3` | `context/projects/web-automation/modules/system-management/pages/menu-management/` | 已独立建模 | 从 system-management 汇总层拆出，通过 module-onboarding 工作流产出了 PAGE_CONTEXT + RISK_MODEL |
| `contexts/summaries/TEST_SUMMARY_template.md` | `templates/test-summary.template.md` | 已映射 | 将旧模板详细结构（统计表、Bug分布、结论检查清单）合并至治理层已有模板 |
| `contexts/README.md` | `context/README.md` | 已映射 | 将 SOP Phase 映射表、文档归属规则、使用指南提取至治理层已有 README |
