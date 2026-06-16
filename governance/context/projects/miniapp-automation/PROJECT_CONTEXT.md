# Miniapp Automation Project Context

## 项目目标
为微信小程序端（鞍集涂源管理系统）建立 AI 辅助测试开发治理结构。

## 当前技术栈
- Node.js
- miniprogram-automator（微信官方自动化库）
- 页面对象（Page Object）+ Flow（业务流程）+ Role（角色切换）
- 测试分层：smoke → p0-core → p1-high → p2-medium → p3-snapshot

## 项目结构
```
mp-weixin-automator/
├── src/
│   ├── driver.js / driver.mjs     ← 驱动层
│   ├── MiniPage.js                ← Page Object 基类
│   ├── config/test.config.js      ← 测试配置
│   ├── pages/          (20 files) ← Page Object 层
│   ├── flows/          (4 files)  ← 业务流程封装
│   ├── roles/          (2 files)  ← 角色切换/验证
│   └── utils/          (6 files)  ← 工具函数
└── tests/
    ├── smoke/          (1 file)   ← 冒烟测试
    ├── p0-core/        (3 files)  ← 核心功能
    ├── p1-high/        (1 file)   ← 高优先级
    ├── p2-medium/      (5 files)  ← 中等优先级
    └── p3-snapshot/    (4 files)  ← 快照/回归
```

## 模块覆盖（按源码 pages/ 映射）
| 模块 | Page Objects | 测试文件 | 说明 |
|------|:---:|:---:|------|
| home | home.page.js | test_home.test.js | 首页/数据看板 |
| login | login.page.js | test_login.test.js | 登录/多角色 |
| alarm | alarm.page.js | test_alarm.test.js | 报警 |
| equipment | equipment.page.js | test_tank_equipment.test.js | 设备台账 |
| tank | tank.page.js | test_tank_equipment.test.js | 储罐 |
| sensor | sensor.page.js | test_tank_equipment.test.js | 传感器 |
| camera | camera.page.js | — | 摄像头 |
| lab | lab.page.js | test_lab_sampling.test.js | 化验室取样 |
| sale | sale.page.js | test_sales_report.test.js | 销售 |
| report | report.page.js | test_sales_report.test.js | 报表 |
| person | person.page.js | test_personnel.test.js | 人员管理 |
| study | study.page.js | test_study_exam_flow.test.js | 在线学习 |
| exam | exam.page.js | test_study_exam_flow.test.js | 考试 |
| practice | practice.page.js | test_practice_wrong.test.js | 自主练习/错题本 |
| approval | approval.page.js | test_approval_flow.test.js | 审批 |
| message | message.page.js | — | 消息通知 |
| mine | mine.page.js | — | 个人中心 |
| my-application | my-application.page.js | test_my_application.test.js | 我的申请 |
| settings | settings.page.js | test_settings.test.js | 设置 |
| visitor | visitor.page.js | test_visitor.test.js | 访客管理 |

## 项目级稳定共性
- 以业务模块为核心组织上下文
- Flow 层封装跨页面业务流程（Login→Approval→Exam→LabSampling）
- Role 层支持运行时角色切换验证
- 测试优先级分层执行（smoke → p0 → p1 → p2 → p3）

## 本文件只维护
- 项目目标、技术边界、模块治理规则、协作入口
