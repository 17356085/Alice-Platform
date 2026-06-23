# Miniapp Automation Module Index

## 当前模块清单（按源码 pages/ 映射）

| 模块ID | 模块名称 | Page Object | 测试文件 | 测试层级 | 治理文档 | 状态 |
|------|------|------|------|:--------:|:--------:|:----:|
| home | 首页 | home.page.js | test_home.test.js | smoke | ⏳ 待建模 | active |
| login | 登录 | login.page.js | test_login.test.js | p0 | ⏳ 待建模 | active |
| alarm | 告警 | alarm.page.js | test_alarm.test.js | p0 | ⏳ 待建模 | active |
| equipment | 设备管理 | equipment.page.js | test_tank_equipment.test.js | p3 | ⏳ 待建模 | active |
| tank | 储罐管理 | tank.page.js | test_tank_equipment.test.js | p3 | ⏳ 待建模 | active |
| sensor | 传感器 | sensor.page.js | test_tank_equipment.test.js | p3 | ⏳ 待建模 | active |
| camera | 摄像头 | camera.page.js | — | — | ⏳ 待建模 | active |
| lab | 化验室取样 | lab.page.js | test_lab_sampling.test.js | p2 | ⏳ 待建模 | active |
| sale | 销售 | sale.page.js | test_sales_report.test.js | p3 | ⏳ 待建模 | active |
| report | 报表 | report.page.js | test_sales_report.test.js | p3 | ⏳ 待建模 | active |
| person | 人员管理 | person.page.js | test_personnel.test.js | p2 | ⏳ 待建模 | active |
| study | 在线学习 | study.page.js | test_study_exam_flow.test.js | p1 | ⏳ 待建模 | active |
| exam | 考试 | exam.page.js | test_study_exam_flow.test.js | p1 | ⏳ 待建模 | active |
| practice | 练习/错题 | practice.page.js | test_practice_wrong.test.js | p2 | ⏳ 待建模 | active |
| approval | 审批 | approval.page.js | test_approval_flow.test.js | p1 | ⏳ 待建模 | active |
| message | 消息通知 | message.page.js | — | — | ⏳ 待建模 | active |
| mine | 个人中心 | mine.page.js | — | — | ⏳ 待建模 | active |
| my-application | 我的申请 | my-application.page.js | test_my_application.test.js | p2 | ⏳ 待建模 | active |
| settings | 设置 | settings.page.js | test_settings.test.js | p3 | ⏳ 待建模 | active |
| visitor | 访客管理 | visitor.page.js | test_visitor.test.js | p2 | ⏳ 待建模 | active |

## 文档缺口

| 缺少的文档 | 说明 |
|-----------|------|
| MODULE_CONTEXT.md | 20 个模块均缺（仅占位 README） |
| PAGE_CONTEXT.md | 20 个模块均缺 |
| RISK_MODEL.md等 | 全部待建 |

## 模块治理规则
- 每个模块至少应具备 MODULE_CONTEXT（Phase 0.5）
- 页面级资产按 pages/<page>/ 组织
- 优先级分层：smoke > p0 > p1 > p2 > p3
- 优先为 p0-core 模块（home/login/alarm）建立上下文

## 当前治理状态
- ✅ 项目级：PROJECT_CONTEXT + MODULE_INDEX
- ⏳ 模块级：20 个模块待建模
- ⏳ 文档级：全部模块缺上下文（后续批次补充）

## 代码缺口
| 模块 | Page Object | 测试脚本 | 建议 |
|------|:-----------:|:--------:|------|
| camera（摄像头） | ✅ 有 | ❌ 无 | 后续补充测试 |
| message（消息通知） | ✅ 有 | ❌ 无 | 后续补充测试 |
| mine（个人中心） | ✅ 有 | ❌ 无 | 后续补充测试 |
