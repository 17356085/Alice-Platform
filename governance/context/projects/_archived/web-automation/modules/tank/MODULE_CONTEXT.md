# MODULE_CONTEXT — tank

## 基本信息
- 模块ID：tank
- 模块名称：储罐管理
- 所属项目：web-automation
- 入口菜单：储罐管理
- 相关角色：admin、储罐管理员、操作工（查看）

## 模块定位
储罐管理负责 LNG 储罐的实时监控与日报表统计，是生产监控链路的核心模块。用户可查看储罐的液位、温度、压力等实时参数以及每日产量/库存汇总。

## 核心业务规则
- 储罐监控数据实时刷新（WebSocket 或定时轮询）
- 储罐日报表按日期汇总产量、消耗、库存
- 数据只读展示（无新增/编辑/删除操作）

## 模块边界
- 包含：储罐监控管理、储罐日报表
- 不包含：储罐的物理设备配置（属于 equipment 模块）、LNG 销售数据（属于 sales 模块）

## 关键页面

| 页面ID | 页面名称 | 路由 | 状态 | 说明 |
|--------|----------|------|------|------|
| monitor | 储罐监控管理 | #/tank/monitor | ✅ 已完成 | 储罐实时参数面板，含统计卡片/搜索/表格/CRUD |
| report | 储罐日报表 | #/tank/report | ✅ 已完成 | 按日统计产量/消耗/库存 + 趋势图 |
| alarm-config | 报警配置 | N/A | ⏳ 待开发 | 规划中的功能，前端未实现 |

## 风险概览
| 风险ID | 描述 | 等级 | 缓解措施 |
|--------|------|------|----------|
| RISK-TANK-001 | 实时监控数据延迟或断连，影响生产决策 | P0 | 页面需展示数据更新时间戳 + 断连自动重连提示 |
| RISK-TANK-002 | 日报表数据与后端统计口径不一致 | P0 | 页面需标注统计口径说明，测试需交叉验证 |
| RISK-TANK-003 | 非授权用户查看储罐敏感数据 | P1 | 页面权限校验 + 接口鉴权 |

## 依赖关系
- 上游：设备管理（equipment）— 储罐作为设备台账中的实体
- 下游：生产报表（production）— 日报表数据可能汇总到生产报表

## 自动化代码
- Page Objects：`page/tank_page/TankMonitorPage.py` (267行, 40+ 定位器) + `TankReportPage.py` (163行, 20+ 定位器)
- 测试脚本：`script/tank/test_tank_monitor.py` (10用例, smoke标记3条) + `test_tank_report.py` (6用例, smoke标记2条)
- conftest 路由配置：monitor → `#/tank/monitor`, report → `#/tank/report`
- 测试执行：最后执行 2026-06-11，16用例: 15通过 + 1跳过，通过率 93.8%

## 治理备注
- 本文件由 `module-modeling` Skill 在 2026-06-11 实战验证中产出
- 页面级信息基于 `sidebar_navigator.py` 路由和 `PROJECT_KNOWLEDGE.md` 模块树推断
- 页面元素已通过浏览器实地访问确认（2026-06-11），PAGE_CONTEXT + TEST_DESIGN + AUTO_STRATEGY 全部完成
- 自定义 UI 框架差异已沉淀到 PROJECT_CONTEXT.md § 已确认的模块 UI 框架差异（UI-001~007）
- 旧 `contexts/储罐管理/` 目录为空，此为首次建模，已演变为完整治理目录


<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-stats -->
<!-- Source: tools/sync_progress.py — regenerated on each SOP run -->
## 自动统计数据 (更新于 2026-06-18 10:54)

| 指标 | 数值 |
|------|:---:|
| 测试文件 | 6 (script/tank/test_*.py) |
| Page Object | 4 (page/tank_page/*.py) |
| 治理文档 | 21 .md 文件 |
| TECH_ANALYSIS | 3 |
| AUTO_STRATEGY | 3 |
| RISK_MODEL | 3 |
| PAGE_CONTEXT | 4 |
| SOP 状态 | completed |
| Phase 完成 | Automation, Bug Analysis, Data Sanitization, Execute & Debug, Knowledge, Project Init, Report, Requirement, Test Design |

> 此段由 sync_progress.py 自动更新。手动编辑会被覆盖。
<!-- ⚠️ AUTO-GENERATED SECTION END: module-stats -->