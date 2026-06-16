# 鞍集（凌源）管理系统 — 项目级测试上下文文档

> **文档版本**: v4.0 | **编制日期**: 2026-06-11 | **编制人**: 测试架构组  
> **适用对象**: 测试工程师 / 自动化开发 / QA 管理者  
> **Web 管理后台**: `https://aiwechatminidemo.cimc-digital.com/`（Vue 3 + Element Plus）  
> **微信小程序**: AppID `wxb48d55a3b1e62c18`（uni-app → 微信原生）  
> **测试账号**: `admin` / `Ajyl@2026`  
> **自动化框架**: pytest + Selenium（Web端）；待引入 Minium（小程序端）

---

## 1. 项目概述

### 1.1 基本信息

| 属性 | 值 |
|------|-----|
| 项目名称 | 鞍集（凌源）管理系统（又名"中集数科智能互联"） |
| 系统定位 | 面向中集 LNG/化工生产园区的综合工业互联平台，覆盖设备监控、培训考核、生产报表、审批流程、化验管理、访客登记等核心业务 |
| 业务领域 | 智能制造 / 工业物联网 / LNG 储运化工 / HSE 安全管理 |
| 用户群体 | 园区管理员、产线主管、一线操作工、培训学员、承包商、访客 |
| 部署模式 | **Web 管理后台**（Vue 3 + Element Plus）+ **微信小程序端**（uni-app → 微信原生）双端 |
| 后端技术 | Java + Spring Boot，RESTful JSON API，JWT 鉴权 |
| 当前阶段 | 已上线运营 + 持续迭代（Web端全模块回归测试进行中，通过率 ~64%） |

### 1.2 双端定位

```
┌──────────────────────────────────────────────────────────────────┐
│                    鞍集（凌源）管理系统                             │
│                                                                  │
│  ┌─────────────────────────────┐  ┌───────────────────────────┐  │
│  │     Web 管理后台 (PC)        │  │   微信小程序端 (Mobile)      │  │
│  │                             │  │                           │  │
│  │  Vue 3 + Element Plus      │  │  uni-app → 微信原生        │  │
│  │  Hash 路由 #/system/user   │  │  分包路由 /pages-sub/...   │  │
│  │                             │  │                           │  │
│  │  侧重：后台管理 + CRUD +     │  │  侧重：移动办公 + 数据采集  │  │
│  │  配置 + 数据分析            │  │  + 培训考核 + 审批处理     │  │
│  │                             │  │                           │  │
│  │  用户：管理员/主管/HR       │  │  用户：一线员工/承包商/访客 │  │
│  └──────────┬──────────────────┘  └──────────┬────────────────┘  │
│             │                                │                   │
│             └───────────┬────────────────────┘                   │
│                         ▼                                        │
│              ┌─────────────────────┐                             │
│              │  Spring Boot REST    │                             │
│              │  /api/* 统一 JSON    │                             │
│              │  JWT 双Token 鉴权    │                             │
│              └─────────────────────┘                             │
└──────────────────────────────────────────────────────────────────┘
```

### 1.3 双端差异速览

| 维度 | Web 管理后台 | 微信小程序端 |
|------|-------------|-------------|
| 页面数量 | ~30 个路由页面（SPA） | 49 个页面（6主包 + 43分包） |
| 核心功能 | 数据管理（CRUD）、配置、报表、日志 | 数据查看、移动采集、培训考试、审批处理 |
| UI 框架 | Element Plus (el-table/el-dialog/el-form) | wot-design-uni (wd-icon/wd-picker/wd-loading) |
| 路由模式 | Vue Router Hash `#/system/user` | 微信原生 `wx.navigateTo` |
| 状态管理 | Pinia → localStorage | Pinia → wx.setStorageSync |
| 独有功能 | 角色/菜单/字典/参数配置、日志审计、定时任务、系统监控 | 生物识别验证、微信登录绑定、考试断点续考、化验草稿暂存 |
| 认证 | 用户名密码登录 + JWT | 手机号密码 / 微信一键登录 + JWT + 生物识别二次验证 |

---

## 2. 技术架构

### 2.1 Web 管理后台

| 层级 | 技术 | 说明 |
|------|------|------|
| 框架 | Vue 3 | Composition API + `<script setup>` |
| UI 库 | Element Plus | 企业级组件库（el-table / el-dialog / el-form / el-pagination / el-tree） |
| 构建工具 | Vite | 按路由代码分割 |
| 状态管理 | Pinia | 持久化至 localStorage |
| 路由 | Vue Router 4 | Hash 模式 `#/`，动态路由从后端加载 |
| HTTP | Axios | 请求/响应拦截器，自动 refreshToken |
| 图标 | Element Plus Icons + Remix Icons + Tabler Icons | 多图标集混用 |

### 2.2 微信小程序端

| 层级 | 技术 | 说明 |
|------|------|------|
| 开发框架 | uni-app（Vue 3 Composition API） | 编译目标：微信小程序 |
| 编译产物 | 微信原生 WXML/WXSS/JS | `compileType: "miniprogram"` |
| UI 组件库 | wot-design-uni | 微信原生组件（wd-icon / wd-loading / wd-toast / wd-picker） |
| 状态管理 | Pinia + persist 插件 | 持久化到 `wx.setStorageSync` |
| HTTP 通信 | `wx.request` 封装 → `utils/http.js` | Token 自动刷新 + 401 聚合队列 + 全局 loading |
| 生物识别 | `wx.startSoterAuthentication` | 指纹/面容，前后台切换 >5min 触发 |
| 路由 | 微信原生路由 | `wx.navigateTo` / `wx.redirectTo` / `wx.reLaunch` |
| 分包策略 | `lazyCodeLoading: "requiredComponents"` | 16 个子包按需下载 |
| 基础库 | 3.15.2 | — |

### 2.3 后端服务（双端共享）

| 层级 | 技术 | 说明 |
|------|------|------|
| 框架 | Java + Spring Boot | RESTful API |
| API 前缀 | `/api/` | 统一 JSON 响应 `{ code, message, data, timestamp }` |
| 鉴权 | JWT（accessToken 2h + refreshToken 30d） | 双端共享鉴权机制 |
| 权限模型 | RBAC（角色 → 菜单权限 + 数据范围） | `system:user:list` 格式 |
| 文件存储 | MinIO / OSS | `/common/file-proxy` 代理下载 |

### 2.4 小程序端目录结构

```
mp-weixin/
├── app.js              # 应用入口：Token检查、生物识别验证
├── app.json            # 路由注册、分包配置、TabBar定义
├── store/
│   ├── user.js         # 用户状态（token/userInfo/isAdmin）
│   ├── menu.js         # 菜单权限状态（miniappMenus/allPermissions）
│   └── exam.js         # 考试状态（断点续考持久化）
├── service/            # API 服务层（23 个模块）
├── utils/
│   ├── http.js         # HTTP 拦截器（401聚合刷新 + 请求队列）
│   ├── auth.js         # Token管理/30天过期检查/安全设置
│   └── tabbar.js       # 动态TabBar（6套角色模板）
├── components/         # 全局组件（6个）
│   ├── CustomTabBar / QuestionCard / AnswerSheet
│   ├── CountDown / Empty / NumberStepInput
├── pages/              # 主包（6页面）
│   ├── index/ login/ approval/ alarm/ mine/ demo/
└── pages-sub/          # 分包（16个子包，43页面）
    ├── study/ report/ equipment/ sensor/ camera/
    ├── tank/ sale/ lab/ visitor/ person/
    ├── my-application/ message/ settings/ feedback/ legal/
```

---

## 3. 用户角色与权限模型

### 3.1 角色定义（双端通用）

| 角色标识 | 角色名称 | Web 后台权限范围 | 小程序 TabBar 显示 |
|----------|----------|-----------------|-------------------|
| `admin` / `ROLE_ADMIN` | 超级管理员 | **全部功能**（isAdmin=true 跳过权限检查） | 首页 + 审批 + 报警 + 我的 |
| `commonAdmin` | 普通管理员 | 系统管理 + 设备管理 + 销售 + 人员（受 DataScope 约束） | — |
| `ROLE_LEADER` / `leader` | 领导层 | 数据查看权限为主 | 首页 + 审批 + 培训 + 我的 |
| `ROLE_MANAGER` | 部门主管 | 本部门数据查看 + 部分管理 | 首页 + 审批 + 培训 + 我的 |
| `ROLE_OPERATOR` / `operator` | 操作员 | 首页 + 培训（数据采集） | 首页 + 培训 + 我的 |
| `employee`（默认） | 普通员工 | 首页 + 个人中心 | 首页 + 培训 + 我的 |
| `chengbaoshang_miniapp` | 承包商 | 小程序限定的首页+培训 | 首页 + 培训 + 我的 |

### 3.2 权限模型

```
                          ┌─────────────────┐
                          │    用户 (User)    │
                          └────────┬────────┘
                                   │ 多对多
                          ┌────────▼────────┐
                          │    角色 (Role)    │
                          │  roleCode/scope  │
                          └────────┬────────┘
                                   │ 多对多               ┌──────────────┐
              ┌────────────────────┼────────────────────│  数据范围     │
              ▼                    ▼                    │  DataScope    │
    ┌─────────────────┐  ┌──────────────┐              │  1=全部       │
    │  菜单权限 (Menu)  │  │ 按钮权限      │              │  2=自定义     │
    │  app:study:view  │  │ system:user: │              │  3=本部门     │
    │  app:exam:view   │  │   add/edit/  │              │    及下级     │
    │  ...             │  │   remove/... │              └──────────────┘
    └─────────────────┘  └──────────────┘
```

### 3.3 关键权限标识符

| 权限标识 | 对应功能 | 端 |
|------|------|:---:|
| `system:user:list/add/edit/remove` | 用户管理 CRUD | Web |
| `system:role:list/add/edit/remove` | 角色管理 CRUD | Web |
| `system:menu:list/add/edit/remove` | 菜单管理 CRUD | Web |
| `app:study:view` | 课程学习入口 | 小程序 |
| `app:exam:view` | 考试测评入口 | 小程序 |
| `app:practice:view` | 自主练习入口 | 小程序 |
| `app:wrong:view` | 错题集入口 | 小程序 |
| `app:approval:view` | 审批模块入口 | 小程序 |
| `app:alarm:view` | 报警模块入口 | 小程序 |

---

## 4. 功能模块树

### 4.1 Web 管理后台菜单树

```
Web 管理后台 (Vue 3 + Element Plus)
│
├── 🏠 首页 / 控制台
│
├── ⚙️ 系统管理
│   ├── 用户管理            # /system/user（列表+弹窗：CRUD/分配角色/重置密码/启停）
│   ├── 角色管理            # /system/role（列表+弹窗：CRUD/分配菜单/数据范围）
│   ├── 菜单管理            # /system/menu（树形表格：CRUD/图标/排序/权限标识）
│   ├── 组织管理（部门）     # /system/org（树形表格：CRUD/负责人/联系电话）
│   ├── 岗位管理            # /system/post（列表+弹窗：岗位编码/类型/等级）
│   ├── 字典管理            # /system/dict（字典类型+字典数据两级管理）
│   ├── 参数设置            # /system/params（列表+弹窗：参数键名/值/类型/模块）
│   ├── 通知管理            # /system/notice（列表+弹窗：标题/类型/内容/发布）
│   ├── 日志管理
│   │   ├── 登录日志        # /system/login-log
│   │   ├── 操作日志        # /system/operation-log
│   │   └── 系统日志        # /system/system-log
│   ├── 定时任务            # /system/timed-task
│   ├── 接口管理            # /system/api
│   ├── 系统监控            # /system/monitor
│   └── 工作流管理          # /system/workflow
│
├── 🔧 设备管理
│   ├── 装置台账            # /equipment/unit（列表+弹窗：CRUD/搜索/分页/导入/关联设备）
│   ├── 设备台账            # /equipment/device（列表+弹窗：设备编码/类型/装置/状态）
│   ├── 设备报警配置        # /equipment/alarm-config（报警名称/类型/等级/阈值/条件/通知方式）
│   ├── 设备维保            # /equipment/maintenance（计划名称/周期/上次维保/下次维保/状态 — 26列宽表）
│   ├── 传感器管理          # /equipment/sensor（搜索/多维度筛选/报警级别/类型）
│   ├── 摄像头管理          # /equipment/camera（区域筛选/在线状态/卡片/列表视图）
│   └── 关键参数监控        # /equipment/key-param（表单/卡片布局）
│
├── 🛢️ 储罐管理            # /tank（储罐列表+详情监控）
│
├── 🧪 化验管理
│   ├── 气体分析报告        # /lab/gas（报告录入/历史记录）
│   └── 水样分析报告        # /lab/water
│
├── 📊 生产管理
│   ├── 生产报表            # /production/report（日报/月报/班报+指标数据）
│   └── 生产审批            # /production/approval（审批列表+通过/驳回）
│
├── 👥 人员管理
│   ├── 员工管理            # /personnel/employee（照片/姓名/工号/性别/岗位/证书 — 10列）
│   ├── 培训计划            # /personnel/train-plan（计划名称/类型/方式/时间/课程/发布状态 — 9列）
│   ├── 课程管理            # /personnel/course
│   ├── 题库管理            # /personnel/question-bank（题型/内容/类别/难度/分值 — 7列）
│   ├── 试卷管理            # /personnel/paper（试卷名称/类型/组卷方式/题目数/总分 — 9列）
│   └── 考试管理            # /personnel/exam（考试名称/试卷/人数/状态/发布 — 10列）
│
├── 💰 销售管理
│   ├── 客户管理            # /sales/customer（编码/名称/联系人/电话/等级/状态 — 7列）
│   ├── 合同管理            # /sales/contract（编号/客户/产品/金额/未执行额/日期/状态 — 8列）
│   ├── 销售订单            # /sales/sales-order（单号/客户/产品/净重/车牌/关联合同 — 8列）
│   └── 销售日报            # /sales/daily-report
│
├── 📡 DCS 数据管理         # /dcs（数据采集点位配置）
│
└── 📋 工作流               # 流程定义/流程实例
```

### 4.2 微信小程序端页面树

```
微信小程序 (uni-app → 微信原生)
│
├── 🏠 首页 (pages/index/index) ── TabBar
│   └── 角色标签 + 动态菜单卡片仪表盘（按权限过滤）
│
├── 📋 审批 (pages/approval/index) ── TabBar
│   ├── 审批列表（待审批/已通过/已驳回/我发起的 — 4 Tab）
│   └── 审批详情（通过/驳回操作）
│
├── 🔔 报警 (pages/alarm/index) ── TabBar
│   ├── 报警列表（全部/紧急/一般/已处理 — 4 Tab + 统计面板）
│   └── 报警详情（处理操作）
│
├── 👤 我的 (pages/mine/index) ── TabBar
│   ├── 自主练习 / 消息设置 / 安全设置
│   ├── 清除缓存 / 个人资料 / 关于
│   └── 退出登录
│
├── 📚 培训学习 (pages-sub/study/) ── 分包 14 页
│   ├── 培训计划 (index)
│   ├── 计划详情 (plan-detail)
│   ├── 课程学习 (study)
│   ├── 考试列表 (exam) → 答题页 (answer) → 结果 (result)
│   ├── 自主练习 (practice) → 创建 (practice-create) → 答题 (practice-exam)
│   │   → 结果 (practice-result) → 详情 (practice-detail)
│   ├── 错题集 (wrong) → 错题详情 (wrong-detail)
│   ├── 文件预览 (webview-preview)
│   └── 安全 (safety)
│
├── 📊 生产报表 (pages-sub/report/) ── 分包 4 页
│   ├── 仪表盘 (index) / 生产日报 (production)
│   ├── 手工录入 (input) / 数据调整 (adjust)
│
├── ⚙️ 设备管理 (pages-sub/equipment/) ── 分包 2 页
├── 📡 传感器 (pages-sub/sensor/) ── 分包 2 页
├── 📹 摄像头 (pages-sub/camera/) ── 分包 2 页
├── 🛢️ 储罐 (pages-sub/tank/) ── 分包 2 页
├── 💰 销售 (pages-sub/sale/) ── 分包 2 页
├── 🧪 化验 (pages-sub/lab/) ── 分包 2 页
├── 🚶 访客 (pages-sub/visitor/) ── 分包 3 页
├── 👥 人员 (pages-sub/person/) ── 分包 2 页
├── 📝 申请 (pages-sub/my-application/) ── 分包 3 页
├── 💬 消息 (pages-sub/message/) ── 分包 2 页
├── ⚙️ 设置 (pages-sub/settings/) ── 分包 3 页
├── 📧 反馈 (pages-sub/feedback/) ── 分包 1 页
└── 📄 法律 (pages-sub/legal/) ── 分包 2 页
```

### 4.3 双端功能对照

| 业务域 | Web 后台 | 小程序 |
|------|---------|--------|
| 用户/角色/菜单管理 | ✅ CRUD 全功能 | ❌ |
| 设备/传感器/摄像头 | ✅ CRUD + 搜索筛选 | ✅ 查看 + 搜索筛选（只读） |
| 储罐监控 | ✅ 列表 | ✅ 列表 + 实时监控详情 |
| 化验报告 | ✅ 录入/历史（Web 表单） | ✅ 移动端录入/草稿暂存/历史 |
| 生产报表 | ✅ 日报/月报/班报 + 审批 | ✅ 日报/月报/班报 + 手工录入/调整 |
| 培训计划/课程 | ✅ CRUD 管理 | ✅ 学习 + 进度跟踪 |
| 考试/题库/试卷 | ✅ CRUD 管理 | ✅ 考试/练习/错题集（考试端） |
| 销售/合同/订单 | ✅ CRUD 全功能 | ✅ 仪表盘 + 添加订单 |
| 访客管理 | ❌ | ✅ 登记/选择被访员工/进度跟踪 |
| 我的申请 | ❌ | ✅ 申请列表/创建/详情 |
| 消息中心 | ✅ 通知管理 | ✅ 消息列表/全部标为已读 |
| 系统监控/日志/定时任务 | ✅ | ❌ |
| 生物识别验证 | ❌ | ✅ 指纹/面容 |
| 微信登录/绑定 | ❌ | ✅ wx.login |

---

## 5. 核心业务流程

### 5.1 用户创建 → 角色分配 → 权限生效（Web 后台 → 小程序）

```
[Web 后台] 系统管理 → 用户管理
    │
    ├─ 1. 新增用户
    │   POST /api/system/user
    │   填写: username / name / password / phone / deptId / roleIds / postId
    │
    ├─ 2. 分配角色
    │   PUT /api/system/user/role { userId, roleIds: [2, 5] }
    │   角色决定: 菜单可见权限 + 按钮操作权限
    │
    ├─ 3. 角色关联菜单
    │   [Web] 系统管理 → 角色管理 → 分配菜单
    │   PUT /api/system/role/menu { roleId, menuIds: [...] }
    │   菜单项携带 permission 标识（如 app:study:view）
    │
    └─ 4. 权限生效
        ├─ Web 后台: 侧边栏动态渲染（Vue Router 动态路由 + 按钮 v-permission）
        └─ 小程序: fetchMenus() → GET /api/system/menu/miniapp/menus
            → 首页按 permissions + isAdmin 过滤菜单卡片
            → TabBar 按 roles 匹配模板动态渲染
```

### 5.2 培训学习全链路（小程序端）

```
[小程序] 培训学习分包
    │
    ├─ 培训计划列表  GET /api/personnel/training/plan/progress/my
    │   └─ 点击计划 → 计划详情 GET .../plan/course/list/{planId}
    │
    ├─ 课程学习
    │   ├─ POST .../start-study → 获取学习记录
    │   └─ 定时上报: POST .../update-progress { courseId, planId, progress }
    │
    ├─ 考试
    │   ├─ 考试列表 GET .../my-exam/list
    │   ├─ 开始考试 POST .../start/{arrangeId}
    │   │   └─ examStore.initExam() 持久化到 Storage（断点续考）
    │   ├─ 答题（5种题型：单选/多选/判断/填空/简答）+ 倒计时
    │   │   └─ 超时自动提交
    │   ├─ 提交 POST .../submit/{recordId}
    │   └─ 结果 GET .../result/{recordId} → 错题入错题集
    │
    ├─ 自主练习
    │   ├─ 创建: 选择题型/数量/难度/来源(错题专项)
    │   ├─ startPractice → Fisher-Yates 随机抽取题目
    │   └─ 提交 → 结果
    │
    └─ 错题集
        ├─ 分类树筛选 + 题型/掌握状态筛选
        ├─ 标记掌握 PUT .../{id}/mastered
        └─ 收藏 PUT .../{id}/collect
```

### 5.3 报警监控闭环

```
[后端 DCS] 设备传感器数据采集
    │ 超阈值 → 报警产生
    ▼
[小程序 或 Web]
    ├─ 报警列表: GET /api/alarm/record/list + /statistics
    │   筛选: all / urgent(红色) / normal(橙色) / info(蓝色) / processed(灰色)
    │   相对时间: <1分钟→"刚刚" / <1小时→"N分钟前" / <1天→"N小时前"
    │
    ├─ 报警详情: GET /api/alarm/record/{id}
    │
    └─ 处理: PUT /api/alarm/record/{id}/handle?handleResult=xxx
        状态: pending → processing → processed
```

### 5.4 化验报告采集 → 审批（双端协同）

```
[小程序端] 移动采集
    ├─ 选择大类: gas(气体) / water(水样)
    ├─ 选择子类型（20+ gas子类 / 15+ water子类）
    ├─ 动态加载取样点位（labSamplingConfig.js 枚举）
    ├─ 动态加载化验指标字段 GET /api/lab/indicator-field/by-type/{id}
    ├─ 填写指标值 + 检验员/复核员
    ├─ 草稿暂存 → Storage lab_draft_{typeId}
    └─ 提交 POST /api/lab/report
    ▼
[Web 后台] 查看/管理
    └─ 化验报告列表 GET /api/lab/report/list
```

### 5.5 访客登记 → 审批 → 入园（小程序端）

```
[小程序] 访客管理
    ├─ 填写访客信息: visitorName / company / phone(1开头11位) / visitPurpose
    ├─ 搜索被访员工: GET /api/personnel/miniapp/visitor/host-employees?keyword=xxx
    │   └─ 实时联想 → 选择 → 显示 realName + deptName
    └─ 提交: POST /api/personnel/miniapp/visitor/register
    ▼
[后端] 审批流程（被访员工/部门负责人）
    ▼
[小程序] 审批进度 GET /api/personnel/miniapp/visitor/records
    ├─ 状态: pending → approved / rejected
    └─ 拒绝原因: rejectReason
    ▼
[审批通过] → 访客凭通知入园
```

---

## 6. 测试风险矩阵

### 6.1 按模块评估

| 模块 | 端 | 风险 | 风险原因 | 缓解措施 |
|------|:---:|:---:|------|------|
| **培训学习** | 小程序 | 🔴 高 | 14 页最大分包；考试断点续考、5 种题型、倒计时自动提交、错题集多维度筛选；**零自动化** | P0 优先自动化；mock 考试数据；重点覆盖断点续考恢复、超时提交、多选/填空作答 |
| **系统-用户管理** | Web | 🔴 高 | 批量删除不可逆；重置密码明文泄露风险；角色越权分配；RBAC 种子数据缺失导致12条权限用例全挂 | 二次确认 + 软删除；操作日志审计；自动化覆盖权限矩阵 |
| **系统-角色/菜单** | Web | 🔴 高 | 角色-菜单权限分配错误直接影响全系统权限体系 | 权限矩阵回归；定期审计；自动化比对预期权限 |
| **审批** | 双端 | 🔴 高 | 生产报表审批 + SAP 推送状态联动；通过/驳回级联变更 | 全状态流转覆盖；SAP 推送标记验证；revision 版本号 |
| **登录/认证** | 双端 | 🔴 高 | Token 刷新并发竞态；30 天过期；生物识别兼容性；微信绑定流程 | 专项测试并发 401；多机型兼容测试；Token 刷新队列验证 |
| **化验管理** | 双端 | 🟡 中 | 2大类+20+子类型+多取样点位组合；指标动态加载；草稿恢复 typeId 匹配 | 参数化覆盖类型×点位；验证草稿存储/恢复；提交后清理 |
| **合同管理** | Web | 🟡 中 | 状态流转复杂（草稿→执行中→终止→完成）；10 条 CRUD 全部失败（弹窗定位器） | 三级降级定位策略；逐状态验证流转条件 |
| **销售管理** | 双端 | 🟡 中 | 客户/产品/合同三级级联；7日趋势图动态计算 | 验证级联数据正确性；趋势图边界值 |
| **设备管理** | Web | 🟡 中 | 维保 26 列宽表 + 装置筛选联动 + CRUD 弹窗 | 表头 JS 提取；覆盖装置下拉动态加载 |
| **传感器** | 双端 | 🟡 中 | 类型+报警级别多维筛选 + 实时数值精度 | 覆盖所有类型×级别筛选组合 |
| **生产报表** | 双端 | 🟡 中 | 日报/月报/班报三种模板；手工录入/调整权限校验 | 覆盖三模板切换；验证权限返回 |
| **访客管理** | 小程序 | 🟡 中 | 被访员工搜索联想 + 手机号校验 + 审批状态流转 | 搜索匹配/无结果/选择覆盖 |
| **报警** | 双端 | 🟡 中 | 统计数值准确性 + 时间格式化边界 + 等级×状态筛选组合 | 统计值与列表一致性；时间边界 |
| **摄像头** | 双端 | 🟢 低 | 仅列表+详情，无 CRUD | 区域筛选 + 视图切换 |
| **储罐** | 双端 | 🟢 低 | 仅列表+监控详情 | 列表加载 + 实时数据 |
| **人员管理** | 双端 | 🟢 低 | 只读为主（列表/档案/证书/资质） | 列表筛选 + 档案 Tab |
| **消息中心** | 双端 | 🟢 低 | 消息列表/已读标记/批量操作 | 未读数统计 + 全部标为已读 |
| **设置** | 小程序 | 🟢 低 | 8类推送开关 + 免打扰 picker + 密码修改 + 生物识别 | 推送开关持久化；密码错误场景 |

### 6.2 全局技术风险

| 风险项 | 等级 | 影响范围 | 缓解措施 |
|------|:---:|------|------|
| Token 刷新并发竞态 | 🔴 高 | 双端 HTTP 层 | 已有 `isRefreshing` 锁 + 请求队列；专项测试并发 401 |
| 页面渲染时序（Web） | 🔴 高 | Web 端 40% 失败根因 | 8s 全局等待 + `wait_page_content_ready()` 表格列数稳定轮询 |
| Element Plus 定位器变化 | 🔴 高 | Web 端 35% 失败根因 | CSS→XPath→JS 文本搜索三级降级 |
| uni-app 编译混淆 | 🔴 高 | 小程序调试困难 | 源码仓库 + sourceMap；`uploadWithSourceMap:true` |
| 小程序分包首次加载延迟 | 🟡 中 | 16 个分包 200-500ms 下载 | 测试脚本增加首次访问等待；关键分包预加载 |
| 考试断点续考数据不一致 | 🟡 中 | 小程序 examStore | `timeLeft = totalDuration - (Date.now() - startTime)/1000` |
| Storage 满/异常 | 🟡 中 | Pinia persist | try-catch 降级；测试 Storage 异常场景 |
| 生物识别兼容性 | 🟡 中 | 小程序多机型 | 不支持时 Toast 提示降级 |

---

## 7. 自动化优先级建议

### 7.1 Web 管理后台

#### P0 — 必须自动化

| 模块 | 场景 | 理由 |
|------|------|------|
| 系统-用户管理 | CRUD + 搜索 + 分页 + 重置密码 + 批量删除 (15条) | RBAC 入口，错误影响全局 |
| 系统-角色管理 | CRUD + 分配菜单 + 数据范围 | 权限体系核心 |
| 系统-菜单管理 | 树形表格 CRUD + 权限标识 | 动态路由数据源 |
| 设备-装置台账 | CRUD + 搜索 + 分页 + 导入 | 设备数据基础 |
| 销售-客户管理 | CRUD + 搜索 + 分页 | 销售数据基础 |
| 销售-销售订单 | CRUD + 级联选择 | 核心交易数据 |

#### P1 — 建议自动化

| 模块 | 场景 |
|------|------|
| 系统-字典/参数/通知/岗位 | CRUD + 搜索 |
| 系统-日志（登录/操作/系统） | 列表 + 搜索 + 筛选 |
| 设备-传感器/摄像头/维保/报警配置 | 列表 + 筛选 + CRUD |
| 人员-员工/培训计划/课程/题库/试卷/考试 | CRUD + 搜索 |
| 销售-合同/销售日报 | CRUD + 状态流转 |
| 化验 | 报告录入 + 历史 |
| 生产 | 报表查看 + 审批 |

#### P2 — 手工即可

| 模块 | 理由 |
|------|------|
| 系统-定时任务/接口管理/系统监控 | 低频 + 运维场景 |
| 工作流管理 | 高度动态 |
| DCS 数据管理 | 配置型 |

### 7.2 微信小程序端

#### P0 — 必须自动化

| 模块 | 场景 | 理由 |
|------|------|------|
| 登录 | 手机号密码登录 + 30天过期 + Token 刷新 | 唯一入口 |
| 首页 | 不同角色的菜单渲染 + TabBar 切换 | 权限过滤逻辑出口 |
| 培训-考试 | 开始→答题(5题型)→标记→倒计时→提交→结果 | 14页核心链路 |
| 培训-断点续考 | 退出→重进→恢复答案/标记/倒计时 | 复杂状态持久化 |
| 培训-练习 | 自定义创建→作答→提交→结果 | 高频使用 |
| 培训-错题集 | 分类筛选 + 标记掌握 + 收藏 | 学习闭环末端 |
| 审批 | 4Tab切换 + 详情 + 通过/驳回 | 核心业务 |
| 报警 | 统计 + 筛选 + 详情 + 处理 | 核心监控 |
| 化验 | 类型切换→子类型→点位→指标→提交（参数化） | 参数组合多 |

#### P1 — 建议自动化

| 模块 | 场景 |
|------|------|
| 生产报表 | 日报/月报/班报 + 手工录入权限 |
| 销售 | 仪表盘 + 订单添加级联 |
| 设备/传感器 | 搜索 + 筛选联动 + 统计面板 |
| 访客 | 登记 + 员工搜索 + 进度 |
| 消息 | 未读数 + 全部标为已读 |

#### P2 — 手工即可

| 模块 | 理由 |
|------|------|
| 设置 | 低频 + 设备依赖 |
| 反馈/法律条款 | 简单表单/纯文本 |
| 储罐/摄像头 | 只读展示 |
| 清除缓存/关于 | 一次性验证 |

---

## 8. 已完成的测试工作

### 8.1 Web 管理后台

| 阶段 | 日期 | 总用例 | 通过 | 通过率 | 关键成果 |
|------|------|:---:|:---:|:---:|------|
| 首次全量 | 2026-06-10（修复前） | 491 | 74 | **15%** | 发现 356 ERROR — 侧边栏 JS hash 导航失效 |
| P0+P1 修复 | 2026-06-10（修复后） | 491 | 299 | **61%** | JS hash + 超时 60s + 渲染等待 |
| P2 深度修复 | 2026-06-11 | 512 | 325 | **64%** | 三级降级定位 + 8s 渲染等待 |
| **目标** | 进行中 | 512 | **400+** | **78%+** | 见下方修复计划 |

**模块级覆盖：**

| 模块 | 用例 | 通过 | 失败 | 跳过 | 通过率 |
|------|:---:|:---:|:---:|:---:|:---:|
| lab | 10 | 10 | 0 | 0 | ✅ 100% |
| equipment | 105 | 65 | 23 | 17 | 🟡 62% |
| system | 170 | 111 | 49 | 10 | 🟡 65% |
| personnel | 113 | 70 | 36 | 7 | 🟡 62% |
| sales | 114 | 69 | 25 | 17 | 🟡 64% |
| **合计** | **512** | **325** | **133** | **51** | **~64%** |

**剩余修复计划：**

| 优先级 | 修复内容 | 预计 | 预期新增 |
|:---:|------|:---:|:---:|
| 1 | 逐页增加 get_table_* retry | 1h | +25 |
| 2 | 对比实际表头更新断言 | 0.5h | +20 |
| 3 | 修复 CRUD 定位器 | 2h | +20 |
| 4 | RBAC 种子数据脚本 | 0.5h | +12 |
| | | **4h** | **→78%+** |

### 8.2 微信小程序端

| 维度 | 现状 |
|------|------|
| 手工测试 | 已覆盖登录、首页、审批、报警等核心页面基本功能 |
| 自动化测试 | **零覆盖**（自动化全部在 Web 端） |
| 小程序专项 | 待启动（需引入 Minium/miniprogram-automator） |

---

## 9. 踩坑经验

### 9.1 Web 后台

| # | 问题 | 根因 | 解决方案 | 涉及文件 |
|:---:|------|------|------|------|
| 1 | **侧边栏导航 356 ERROR** | SPA 路由切换时侧边栏等待超时不够(5s) + CSS选择器不稳定 | JS `location.hash` 直接操作路由 + 全局渲染等待 5s→8s + `_wait_page_content_ready()` 表格列数稳定轮询 | `base/sidebar_navigator.py` |
| 2 | **表头断言大规模失败** (30+用例) | 后端 API 字段调整后测试断言硬编码列名未同步 | JS 提取实际表头（6次重试 + 稳定检测）+ 建立实际表头对照表 | `base/base_page.py` |
| 3 | **CRUD 弹窗按钮定位失效** (合同/用户/角色) | Element Plus 组件 class/placeholder 动态变化 | CSS → XPath → JS 文本搜索三级降级 | `base/base_page.py` |
| 4 | **RBAC 权限测试全挂** (12条) | 测试角色/用户种子数据未预置 | 编写 `ensure_seed_data` fixture | `script/conftest.py` |
| 5 | **分页组件差异** | el-pagination 在不同版本中 DOM 结构略有差异 | `click_next_page` / `select_page_size` 使用 JS 文本搜索降级 | `base/base_page.py` |

### 9.2 微信小程序

| # | 问题 | 根因 | 解决方案 | 涉及文件 |
|:---:|------|------|------|------|
| 1 | **uni-app 编译混淆** | .vue→单文件.js，代码压缩合并不可读 | 源码仓库 + `uploadWithSourceMap:true` | `project.config.json` |
| 2 | **Token 刷新并发** | 多请求同时 401 重复触发 refresh | `isRefreshing` 锁 + 请求队列，刷新成功统一重放 | `utils/http.js` |
| 3 | **生物识别 5min 验证** | 前后台切换超过 300000ms 触发指纹/面容 | 测试时设置 `biometricEnabled=false` 跳过 | `app.js` |
| 4 | **断点续考倒计时不准** | persist 的 timeLeft 是静态值 | 恢复时重算：`totalDuration - (Date.now()-startTime)/1000` | `store/exam.js` |
| 5 | **化验草稿类型错配** | 切换子类型后 Storage 草稿与当前类型不对应 | `lab_draft_{typeId}` 按类型 ID 隔离 | `pages-sub/lab/index.js` |
| 6 | **分包首次加载慢** | 16个分包首次需下载 200-500ms | 测试脚本对首次访问增加 1-2s 等待 | `app.json` |

### 9.3 通用经验教训

| # | 教训 | 建议 |
|:---:|------|------|
| 1 | **渲染时序是最大根因** (Web 40% 失败) | 所有操作前确保渲染等待 + 表格稳定检测 |
| 2 | **定位器不要耦合 UI 框架内部 class** | 使用 JS 文本搜索 + 推动开发添加 `data-testid` |
| 3 | **种子数据缺失致全模块挂** | 每个模块 conftest 需 seed data fixture |
| 4 | **小程序工具链空白** | 尽快引入 minium/miniprogram-automator |
| 5 | **Storage 状态污染** | 每用例前后清理 Storage + 独立测试账号 |

---

## 附录 A：Web 后台实际表头对照表

```
alarm_config:     报警名称, 报警类型, 关联设备, 报警等级, 报警条件, 阈值类型, 阈值数值, 通知方式, 状态, 创建时间, 操作
sensor:           同上(11列)
unit:             装置名称, 装置编码, 所属区域, 装置类型, 负责人, 联系电话, 关联设备, 状态, 备注, 创建时间, 操作
maintenance:      计划名称, 计划类型, 设备名称, 维保类型, 周期(天), 上次维保, 下次维保, 状态... (26列)
user:             用户名, 姓名, 手机号, 角色, 组织机构, 状态, 上次登录, 操作 (8列)
role:             角色名称, 角色编码, 排序, 数据范围, 状态, 备注, 创建时间, 操作 (8列)
org:              组织机构, 组织编码, 负责人, 联系电话, 员工数量, 状态, 操作 (7列)
notice:           通知标题, 通知类型, 通知内容, 状态, 发布人, 创建时间, 操作 (7列)
dict:             字典标签, 字典键值, 排序, 状态, 备注, 创建时间, 操作 (7列)
params:           参数名称, 参数键名, 参数值, 参数类型, 业务模块, 备注, 创建时间, 操作 (8列)
customer:         客户编码, 客户名称, 联系人, 联系电话, 客户等级, 合作状态, 操作 (7列)
contract:         合同编号, 客户名称, 产品, 合同金额(万), 未执行额, 生效日期, 状态, 操作 (8列)
sales_order:      销售单号, 客户名称, 产品名称, 净重(吨), 车牌号, 创建时间, 关联合同, 操作 (8列)
employee:         照片, 姓名, 工号, 性别, 出生日期, 岗位, 手机号码, 证书, 状态, 操作 (10列)
post:             岗位名称, 岗位编码, 所属部门, 岗位类型, 岗位等级, 在岗人数, 状态, 操作 (8列)
train_plan:       计划名称, 培训类型, 培训方式, 时间范围, 发布人, 关联课程, 状态, 发布状态, 操作 (9列)
question_bank:    题型, 题目内容, 类别, 难度, 分值, 创建时间, 操作 (7列)
paper:            试卷名称, 试卷类型, 组卷方式, 题目数量, 总分, 创建时间, 创建人员, 状态, 操作 (9列)
exam:             考试名称, 关联试卷, 开始时间, 结束时间, 考试人数, 已考人数, 考试状态, 发布状态, 操作 (10列)
```

## 附录 B：双端 API 端点对照

| 业务域 | API 前缀 | Web 后台 | 小程序 |
|------|------|:---:|:---:|
| 认证 | `/api/app/auth/*`, `/api/auth/*` | ✅ | ✅ |
| 系统管理 | `/api/system/*` | ✅ CRUD | ❌ |
| 菜单权限 | `/api/system/menu/miniapp/menus` | ❌ | ✅ |
| 设备 | `/api/equipment/miniapp/*` | ❌ | ✅ |
| 设备 | `/api/equipment/*` | ✅ | ❌ |
| 报警 | `/api/alarm/record/*` | ✅ | ✅ |
| 培训 | `/api/personnel/training/*` | ✅ 管理 | ✅ 学员 |
| 考试 | `/api/personnel/training/my-exam/*` | ❌ | ✅ |
| 练习 | `/api/personnel/training/practice/*` | ❌ | ✅ |
| 错题 | `/api/personnel/training/wrong-question/*` | ❌ | ✅ |
| 生产报表 | `/api/production/*` | ✅ | ✅ |
| 审批 | `/api/production/approval/*` | ✅ | ✅ |
| 销售 | `/api/sales/*` | ✅ | ✅ |
| 化验 | `/api/lab/*` | ✅ | ✅ |
| 储罐 | `/api/tank/*` | ✅ | ✅ |
| 人员 | `/api/personnel/employee/*` | ✅ | ✅ |
| 访客 | `/api/personnel/miniapp/visitor/*` | ❌ | ✅ |
| 申请 | `/api/system/miniapp/workflow/*` | ❌ | ✅ |
| 消息 | `/api/system/notice/*` | ✅ | ✅ |

---

> **文档维护说明**：本文档覆盖 Web 管理后台 + 微信小程序双端。每次新增模块/页面、变更 API、发现新踩坑经验后，请同步更新对应章节。模块级详细文档请参考 `TestIntern_library/02-项目文档/contexts/` 下各模块的 MODULE_CONTEXT.md。
