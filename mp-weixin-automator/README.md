# 鞍集（涂源）管理系统 — 小程序 UI 自动化测试

> 基于 **Node.js + Jest + miniprogram-automator**，直接驱动微信开发者工具运行小程序。

---

## 设计原则

1. **API 不复现** — 后端接口由 Web 端 pytest 覆盖（`ZJSN_Test-master526/`），小程序只测客户端 UI
2. **优先级驱动** — 按 PROJECT_WX_CONTEXT.md 定义的 P0 > P1 > P2 > P3 逐级建设
3. **Page Object 模式** — 每个小程序页面对应一个 PO，封装元素查询+业务操作
4. **Flow 复用层** — 跨页面的业务流程（如考试全链路）抽为 Flow，多测试文件共享
5. **多角色专项** — 独立的多角色切换机制，验证 TabBar/菜单/页面拦截的权限差异

---

## 架构总览

```
mp-weixin-automator/
│
├── .env                          # 环境变量（不提交）
├── .env.example                  # 环境变量模板
├── jest.config.js                # Jest 配置
├── jest.setup.js                 # 全局 setup
├── jest.teardown.js              # 全局 teardown（关闭开发者工具连接）
│
├── src/                          # ═══ 框架源码 ═══
│   ├── driver.js                 # MiniDriver 单例 — 微信开发者工具连接管理
│   ├── MiniPage.js               # Page Object 基类
│   │
│   ├── config/
│   │   └── test.config.js        # 测试配置中心（账号池/URL/超时/角色映射）
│   │
│   ├── pages/                    # ═══ Page Object 层 ═══
│   │   ├── login.page.js         # [P0] 登录页
│   │   ├── home.page.js          # [P0] 首页
│   │   ├── alarm.page.js         # [P0] 报警列表+详情
│   │   ├── approval.page.js      # [P1] 审批列表+详情
│   │   ├── study.page.js         # [P1] 培训学习首页
│   │   ├── exam.page.js          # [P1] 考试列表+答题+成绩
│   │   ├── mine.page.js          # [P0] 我的（用户信息+退出）
│   │   │
│   │   ├── lab.page.js           # [P2] 化验室取样录入+历史
│   │   ├── report.page.js        # [P2] 生产报表（日报/月报/交接班）
│   │   ├── practice.page.js      # [P2] 自主练习+错题集
│   │   ├── visitor.page.js       # [P2] 访客登记+进度追踪
│   │   ├── my-application.page.js# [P2] 我的申请
│   │   ├── tank.page.js          # [P3] 储罐列表+监控详情
│   │   ├── equipment.page.js     # [P3] 设备列表+详情
│   │   ├── sensor.page.js        # [P3] 传感器列表+详情
│   │   ├── camera.page.js        # [P3] 摄像头管理
│   │   ├── sale.page.js          # [P3] 销售订单+日报表
│   │   ├── person.page.js        # [P3] 人员列表+档案
│   │   ├── settings.page.js      # [P3] 消息设置+安全设置+设备管理
│   │   └── message.page.js       # [P3] 消息通知
│   │
│   ├── flows/                    # ═══ 业务流程编排层 ═══
│   │   ├── LoginFlow.js          # 登录→菜单加载→生物识别验证
│   │   ├── ExamFlow.js           # 培训计划→学习→考试→答题→提交→成绩
│   │   ├── ApprovalFlow.js       # 审批列表→详情→通过/驳回→状态验证
│   │   ├── LabSamplingFlow.js    # 化验类型切换→取样→指标录入→提交→历史
│   │   └── VisitorFlow.js        # 登记→搜索员工→提交→审批追踪
│   │
│   ├── roles/                    # ═══ 多角色测试 ═══
│   │   ├── RoleSwitcher.js       # 账号切换+登录+Token管理
│   │   └── RoleVerifier.js       # TabBar/菜单/页面拦截 权限验证器
│   │
│   └── utils/                    # ═══ 工具层 ═══
│       ├── logger.js             # 日志工具
│       ├── helpers.js            # 通用帮助（sleep/screenshot/retry/waitForNetworkIdle）
│       ├── assertions.js         # 自定义断言（data结构校验/列表排序/角标准确性）
│       ├── network.js            # 弱网模拟（延迟/丢包/断网恢复）
│       └── dataFactory.js        # 测试数据工厂（自动生成/模板填充）
│
├── tests/                        # ═══ 测试用例（按优先级+模块组织） ═══
│   ├── smoke/                    # 冒烟测试（每次提交必跑，<5分钟）
│   │   └── test_smoke.test.js    # 登录→首页渲染→核心Tab可切换
│   │
│   ├── p0-core/                  # P0: 核心入口+安全关键路径
│   │   ├── test_login.test.js    # 登录页渲染、手机号登录、微信登录、退出
│   │   ├── test_home.test.js     # 首页菜单加载、角色标签、下拉刷新
│   │   └── test_alarm.test.js    # 报警列表+统计+筛选+详情+处理
│   │
│   ├── p1-high/                  # P1: 高风险+高频使用
│   │   ├── test_approval.test.js # 审批多Tab切换+通过/驳回+SAP状态
│   │   ├── test_exam_full.test.js# 考试全链路（计划→学习→答题→提交→成绩）
│   │   └── test_role_permissions.test.js  # 多角色权限矩阵（6角色×TabBar×菜单）
│   │
│   ├── p2-medium/                # P2: 中频使用模块
│   │   ├── test_lab_sampling.test.js     # 化验室取样（气体/水质双线）
│   │   ├── test_practice_wrong.test.js   # 自主练习+错题集
│   │   ├── test_visitor.test.js          # 访客登记全流程
│   │   └── test_my_application.test.js   # 我的申请
│   │
│   └── p3-snapshot/              # P3: 快照/简单验证
│       ├── test_tank_equipment.test.js   # 储罐+设备+传感器+摄像头
│       ├── test_sales_report.test.js     # 销售+生产报表
│       └── test_settings.test.js         # 消息设置+安全设置+法律文本
│
├── data/                         # ═══ 测试数据 ═══
│   ├── fixtures/
│   │   ├── auth.json             # 测试账号池（多角色）
│   │   ├── exam.json             # 考试测试数据
│   │   ├── lab.json              # 化验室测试数据
│   │   └── permissions.json      # 角色-权限矩阵期望值
│   └── templates/
│       └── visitor.json          # 访客登记模板
│
└── artifacts/                    # 测试产物（gitignore）
    ├── screenshots/              # 失败截图
    └── report/                   # HTML 报告
```

---

## 环境要求

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Node.js | ≥ 18 | 推荐 LTS |
| 微信开发者工具 | ≥ 1.06 | 需安装并登录 |
| 操作系统 | Windows/Mac | 微信开发者工具仅支持这两个平台 |

---

## 用例文档

所有测试用例在 `TESTCASES.md` 文件中统一管理，手工测试 + 自动化测试共用同一套基线：

```bash
# 查看全部测试用例（104 条）
less TESTCASES.md

# 快速定位：按编号搜索特定用例
grep "TC-LAB-006" TESTCASES.md
```

每条用例标注了：
- **自动化** `✅` — 测试框架已覆盖，运行对应 npm script 即可
- **手工** `✅` — 需要手工执行
- 手工测试人员以 `TESTCASES.md` 为执行依据，在对应行标注执行结果和问题

---

## 快速开始

### 1. 安装依赖

```bash
cd mp-weixin-automator
npm install
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env，配置 WECHAT_CLI_PATH 指向微信开发者工具 cli.bat/cli
```

### 3. 运行测试

```bash
# 冒烟测试（最快，< 5 分钟）
npm run test:smoke

# P0 核心（每次提交必跑）
npm run test:p0

# P0 + P1 回归（每次发布前）
npm run test:regression

# 按模块
npm run test:login
npm run test:alarm
npm run test:approval
npm run test:exam
npm run test:roles        # 多角色权限

# 全部测试
npm test
```

---

## 核心架构详解

### 1. MiniPage 基类

所有 Page Object 继承自此基类，提供统一的导航、元素查询、数据读取、方法调用能力。

```js
class SomeListPage extends MiniPage {
  static PAGE_PATH = 'pages-sub/xxx/index';  // 页面路径
  static IS_TAB_PAGE = false;                 // 是否 Tab 页

  async waitForList() { ... }    // 等待列表渲染
  async getList() { ... }        // 获取列表数据（优先 data 而非 DOM）
  async tapItem(index) { ... }   // 点击列表项
}
```

### 2. Flow 层 — 跨页面流程复用

Flow 编排多个 Page Object 完成完整业务链路，避免测试文件中重复编排逻辑。

```js
// src/flows/ExamFlow.js
class ExamFlow {
  async fullExamCycle(credentials) {
    const loginPage = new LoginPage(app);
    await loginPage.login(credentials);

    const studyPage = new StudyPage(app);
    await studyPage.navigate();

    const examPage = new ExamListPage(app);
    await examPage.startExam(0);

    const answerPage = new AnswerPage(app);
    await answerPage.answerAll([...]);
    await answerPage.submit();

    const resultPage = new ExamResultPage(app);
    return resultPage.getScore();
  }
}
```

### 3. 多角色测试机制

```js
// src/roles/RoleSwitcher.js
const switcher = new RoleSwitcher(app);
await switcher.loginAs('yuangong');        // 员工角色
const tabs = await switcher.getVisibleTabs();  // → [首页, 培训, 我的]
await switcher.loginAs('admin');          // 管理员角色
const tabs2 = await switcher.getVisibleTabs(); // → [首页, 审批, 报警, 我的]
```

### 4. 数据优先策略

优先通过 `page.callMethod()` + `page.data()` 获取业务数据验证，减少对 DOM 选择器的依赖（uni-app 编译后 class 名不稳定）。

---

## 测试矩阵

| 优先级 | 模块 | 测试文件 | 当前用例数 | 目标用例数 |
|:---:|------|------|:---:|:---:|
| **P0** | 登录/鉴权 | test_login.test.js | 3 | 8 |
| **P0** | 首页 | test_home.test.js | 2 | 6 |
| **P0** | 报警管理 | test_alarm.test.js | 7 | 10 |
| **P1** | 审批工作流 | test_approval.test.js | 7 | 12 |
| **P1** | 培训考试 | test_exam_full.test.js | 5 | 15 |
| **P1** | 多角色权限 | test_role_permissions.test.js | 0 | 12 |
| **P2** | 化验室取样 | test_lab_sampling.test.js | 0 | 8 |
| **P2** | 练习+错题 | test_practice_wrong.test.js | 0 | 6 |
| **P2** | 访客管理 | test_visitor.test.js | 0 | 5 |
| **P2** | 我的申请 | test_my_application.test.js | 0 | 5 |
| **P3** | 设备/储罐/传感器/摄像头 | test_tank_equipment.test.js | 0 | 8 |
| **P3** | 销售+报表 | test_sales_report.test.js | 0 | 6 |
| **P3** | 设置+消息 | test_settings.test.js | 0 | 5 |
| — | 冒烟测试 | test_smoke.test.js | 0 | 5 |
| | **合计** | | **~26** | **~111** |

---

## CI 集成

```bash
npm install
npx jest --verbose                           # 全量
npx jest --testPathPattern=tests/smoke       # 冒烟
npx jest --testPathPattern=tests/p0-core     # P0
npx jest --reporters=jest-html-reporters     # HTML 报告
```
