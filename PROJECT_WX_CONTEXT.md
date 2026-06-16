# 中集数科智能互联 — 微信小程序端 测试上下文文档

> **文档版本**: V2.0 | **编制日期**: 2026-06-11 | **编制人**: 测试架构组  
> **适用对象**: 小程序测试工程师 / 自动化开发 / QA 管理者  
> **小程序 AppID**: `wxb48d55a3b1e62c18`  
> **API 基准 URL**: `https://aiwechatminidemo.cimc-digital.com/`  
> **测试账号**: `13378402325` / `Ajyl@2026`  
> **基础库版本**: 3.15.2  
> **自动化工具**: 待引入 Minium / miniprogram-automator

---

## 1. 项目概述

### 1.1 基本信息

| 属性 | 值 |
|------|-----|
| 项目名称 | 中集数科智能互联（微信小程序端） |
| 系统定位 | 面向中集 LNG/化工生产园区的移动办公与数据采集平台，承担设备监控、培训考试、生产报表查阅、审批处理、化验报告录入、访客登记等现场业务 |
| 业务领域 | 智能制造 / 工业物联网 / LNG 储运化工 / HSE 安全管理 / 移动办公 |
| 用户群体 | 园区管理员、产线主管、一线操作工、培训学员、承包商、访客 |
| 开发框架 | uni-app（Vue 3 Composition API）→ 编译为微信小程序原生代码 |
| 页面数量 | **49 个页面**（6 主包 + 43 分包） |
| 分包数量 | **16 个子包**，按需懒加载 |
| 当前阶段 | 已上线运营 + 持续迭代（小程序端自动化测试尚未启动） |

### 1.2 系统定位

```
┌──────────────────────────────────────────────────┐
│         中集数科智能互联（微信小程序）              │
│                                                   │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │ 首页    │ │ 审批    │ │ 报警    │ │ 我的    │    │
│  │ 仪表盘  │ │ 列表    │ │ 列表    │ │ 中心    │    │
│  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘    │
│      │          │         │         │            │
│      ▼          ▼         ▼         ▼            │
│  ┌──────────────────────────────────────────┐    │
│  │         16 个分包（43 个页面）              │    │
│  │  📚 培训学习(14)  📊 生产报表(4)          │    │
│  │  ⚙️ 设备管理(2)   📡 传感器(2)            │    │
│  │  📹 摄像头(2)     🛢️ 储罐(2)              │    │
│  │  💰 销售管理(2)   🧪 化验管理(2)          │    │
│  │  🚶 访客管理(3)   👥 人员管理(2)          │    │
│  │  📝 我的申请(3)   💬 消息中心(2)          │    │
│  │  ⚙️ 设置(3)       📧 反馈(1)  📄 法律(2)  │    │
│  └──────────────────────────────────────────┘    │
│                                                   │
│  侧重: 移动办公 + 现场数据采集 + 培训考核         │
│        + 审批处理 + 实时监控查看                  │
└────────────────────┬─────────────────────────────┘
                     │ HTTPS + JWT Bearer Token
┌────────────────────▼─────────────────────────────┐
│          Spring Boot REST API (/api/*)            │
└──────────────────────────────────────────────────┘
```

---

## 2. 技术架构

### 2.1 前端技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 开发框架 | **uni-app**（Vue 3 Composition API） | 一套代码编译到微信小程序 |
| 编译产物 | 微信小程序原生 WXML/WXSS/JS | `compileType: "miniprogram"` |
| 编译工具 | uni-app CLI + Babel | 禁用 SWC，`minified: true`，`minifyWXSS: true`，`minifyWXML: true` |
| 基础库版本 | **3.15.2** | `libVersion` 配置 |
| UI 组件库 | **wot-design-uni** | 微信原生组件（`wd-icon` / `wd-loading` / `wd-toast` / `wd-picker` / `wd-input`） |
| 状态管理 | **Pinia** + persist 插件 | 持久化到 `wx.setStorageSync`；3 个 Store：`user` / `menu` / `exam` |
| HTTP 通信 | `wx.request` + `wx.downloadFile` | 封装于 `utils/http.js`（~200 行） |
| 认证方式 | JWT（accessToken + refreshToken） | 自动刷新 + 401 聚合队列 + 403 拦截 + 30 天过期强制登出 |
| 生物识别 | `wx.startSoterAuthentication` | 指纹（fingerPrint）/ 面容（facial），前后台切换超过 5 分钟触发 |
| 路由 | 微信原生路由 API | `wx.navigateTo` / `wx.redirectTo` / `wx.reLaunch` / `wx.navigateBack` |
| 分包策略 | `lazyCodeLoading: "requiredComponents"` | 16 个分包按需下载，首次访问延迟 200~500ms |
| 自定义 TabBar | `CustomTabBar` 组件 | 替代原生 TabBar，支持按角色动态显示 |
| Source Map | `uploadWithSourceMap: true` | 上传时附带 source map 辅助错误定位 |

### 2.2 后端服务（与 Web 后台共享）

| 层级 | 技术 | 说明 |
|------|------|------|
| 语言/框架 | Java + Spring Boot | RESTful API |
| API 前缀 | `/api/` | 统一 JSON 响应 `{ code: 0, message: "", data: {...} }` |
| 鉴权 | JWT | accessToken（2h）+ refreshToken（30d）双 token 自动续期 |
| 文件代理 | `/common/file-proxy` | 私有文件下载，自动附加 Authorization 头 |

### 2.3 目录结构

```
mp-weixin/                          # uni-app 编译产物（微信开发者工具直接打开）
├── app.js                          # 应用入口：onLaunch/onShow/onHide 生命周期管理
├── app.json                        # 全局配置：路由/分包/TabBar/窗口样式
├── app.wxss                        # 全局样式
├── common/
│   ├── vendor.js                   # uni-app + Vue 3 + Pinia 运行时（~500KB）
│   └── assets.js                   # 静态资源引用
├── config/
│   └── labSamplingConfig.js        # 化验取样点位枚举配置
├── store/                          # 状态管理（3 个 Store）
│   ├── user.js                     # 用户状态：token / userInfo / isAdmin / isLoggedIn
│   ├── menu.js                     # 菜单权限：miniappMenus / allPermissions
│   └── exam.js                     # 考试状态：questions / answers / markedQuestions / timeLeft（断点续考）
├── service/                        # API 接口层（23 个模块文件）
│   ├── alarm.js                    # 报警记录
│   ├── approval.js                 # 审批流程
│   ├── archive.js                  # 培训计划进度
│   ├── auth.js                     # 认证（密码修改 / 菜单获取）
│   ├── camera.js                   # 摄像头监控
│   ├── course.js                   # 课程学习
│   ├── dict.js                     # 数据字典
│   ├── equipment.js                # 设备管理
│   ├── exam.js                     # 考试测评
│   ├── lab.js                      # 化验报告
│   ├── my-application.js           # 我的申请
│   ├── notice.js                   # 消息通知
│   ├── personnel.js                # 人员管理
│   ├── practice.js                 # 自主练习
│   ├── production.js               # 生产报表
│   ├── sale.js                     # 销售管理
│   ├── sensor.js                   # 传感器
│   ├── system.js                   # 系统设备管理
│   ├── tank.js                     # 储罐监控
│   ├── upload.js                   # 文件上传/代理下载
│   ├── user.js                     # 用户信息/反馈
│   ├── visitor.js                  # 访客管理
│   └── wrong.js                    # 错题集
├── utils/
│   ├── http.js                     # HTTP 拦截器（401 聚合刷新 / 请求队列 / 全局 loading / 登出）
│   ├── auth.js                     # Token管理 / 安全设置 / 30天过期检查 / 生物识别设置
│   └── tabbar.js                   # 动态 TabBar 配置（6 套角色模板）
├── components/                     # 全局组件（6 个）
│   ├── CustomTabBar.{js,json,wxml,wxss}    # 自定义底部导航栏
│   ├── QuestionCard.{js,json,wxml,wxss}    # 题目卡片（5 种题型渲染）
│   ├── AnswerSheet.{js,json,wxml,wxss}     # 答题卡面板
│   ├── CountDown.{js,json,wxml,wxss}       # 考试倒计时
│   ├── Empty.{js,json,wxml,wxss}           # 空状态占位
│   └── NumberStepInput.{js,json,wxml,wxss} # 数字步进输入器
├── pages/                          # 主包页面（6 页面，4 TabBar）
│   ├── index/                      # 首页（菜单卡片仪表盘）
│   ├── login/                      # 登录页（手机号+密码 / 微信绑定）
│   ├── approval/                   # 审批列表 + 详情
│   ├── alarm/                      # 报警列表 + 详情
│   ├── mine/                       # 个人中心
│   └── demo/                       # 图标演示页
└── pages-sub/                      # 分包（16 个子包，43 页面）
    ├── study/                      # 培训学习（14 页）
    ├── report/                     # 生产报表（4 页）
    ├── equipment/                  # 设备管理（2 页）
    ├── sensor/                     # 传感器（2 页）
    ├── camera/                     # 摄像头（2 页）
    ├── tank/                       # 储罐（2 页）
    ├── sale/                       # 销售管理（2 页）
    ├── lab/                        # 化验管理（2 页）
    ├── visitor/                    # 访客管理（3 页）
    ├── person/                     # 人员管理（2 页）
    ├── my-application/             # 我的申请（3 页）
    ├── message/                    # 消息中心（2 页）
    ├── settings/                   # 设置（3 页）
    ├── feedback/                   # 意见反馈（1 页）
    └── legal/                      # 法律条款（2 页）
```

### 2.4 关键架构特征

| 特征 | 描述 | 实现位置 |
|------|------|----------|
| **Token 自动刷新 + 请求队列** | 多请求同时 401 时，`isRefreshing` 锁聚合并发，第一个触发 refresh，其余入队等待，刷新成功统一重放；失败统一登出 | `utils/http.js` |
| **30 天过期强制登出** | `isLoginExpired(30)` 检查 `lastLoginTime + 30×24×60×60×1000 < Date.now()` → 超期则 clearTokens() → wx.reLaunch 登录页 | `utils/auth.js`, `app.js` |
| **生物识别二次验证** | `app.js onShow`：`Date.now() - lastShowTime > 300000`(5min) 且 `biometricEnabled=true` → 触发指纹/面容验证 → 失败强制登出 | `app.js` |
| **动态权限菜单** | `fetchMenus()` → `GET /api/system/menu/miniapp/menus` → 返回含 `permission` 字段的菜单树 → 首页按 `permissions` Set + `isAdmin` 双重过滤 | `store/menu.js`, `pages/index/index.js` |
| **动态 TabBar** | `getTabBarConfig()` 根据 `userInfo.roles` 匹配 6 套模板 → 按 `permissions` 过滤 → 渲染 `CustomTabBar` | `utils/tabbar.js` |
| **考试断点续考** | `examStore` Pinia persist 持久化全部字段 → 重进时 `hasOngoingExam()` 判断 → 恢复 + 倒计时实时重算 | `store/exam.js` |
| **化验草稿暂存** | 表单数据按 `lab_draft_{typeId}` 存入 Storage → 下次同类型进入弹窗提示恢复 | `pages-sub/lab/index.js` |
| **文件代理下载** | 私有文件通过 `/common/file-proxy` 下载，自动附加 Authorization；支持 `path=` 本地和 `url=` 远程两种模式 | `service/upload.js` |
| **全局 Loading** | 首个 GET 请求 200ms 后显示 `wx.showLoading`，所有请求结束后自动隐藏 | `utils/http.js` |

---

## 3. 用户角色与权限模型

### 3.1 角色定义

| 角色标识 | 角色名称 | 菜单可见范围 | TabBar 显示 |
|----------|----------|-------------|-------------|
| `ROLE_ADMIN` / `admin` | 管理员 | **全部功能**（`isAdmin=true` 跳过所有权限检查） | 首页 + 审批 + 报警 + 我的 |
| `ROLE_LEADER` / `leader` | 领导层 | 首页 + 审批 + 报警 + 培训 | 首页 + 审批 + 培训 + 我的 |
| `ROLE_SUPERVISOR` / `ROLE_MANAGER` | 主管/经理 | 首页 + 审批 + 报警 + 培训 | 首页 + 审批 + 培训 + 我的 |
| `ROLE_OPERATOR` / `operator` | 操作员 | 首页 + 培训 | 首页 + 培训 + 我的 |
| `employee`（默认角色） | 普通员工 | 首页 + 培训 | 首页 + 培训 + 我的 |
| `chengbaoshang_miniapp` | 承包商 | 首页 + 培训 | 首页 + 培训 + 我的 |

### 3.2 角色→TabBar 动态映射

| 角色模板 Key | 适用角色 | Tab 列表 |
|-------------|------|------|
| `admin` | admin, ROLE_ADMIN | 首页(home) + 审批(approval) + 报警(alarm) + 我的(mine) |
| `lingdaoceng_miniapp` | leader, ROLE_LEADER | 首页 + 审批 + 培训(training) + 我的 |
| `buzhuguan_miniapp` | supervisor, manager | 首页 + 审批 + 培训 + 我的 |
| `manager` | ROLE_MANAGER | 首页 + 审批 + 报警 + 我的 |
| `yuangong` | 默认员工 | 首页 + 培训 + 我的 |
| `chengbaoshang_miniapp` | 承包商 | 首页 + 培训 + 我的 |

### 3.3 菜单权限过滤流程

```
用户登录成功
    │
    ├─ userInfo: { realName, deptName, avatar, roles[], permissions[], isAdmin }
    │
    ├─ fetchMenus() → GET /api/system/menu/miniapp/menus
    │   返回: [{ categoryId, categoryName, categoryIcon, categoryCode,
    │            stats[], items[{ id, name, path, icon, color, permission, sort, badge }] }]
    │
    └─ 首页渲染前双重过滤:
        │
        ├─ [管理员] isAdmin === true → 显示所有 category 及其全部 items（不过滤）
        │
        └─ [非管理员] isAdmin !== true
            └─ 每个 category:
                └─ category.items.filter(item => {
                       if (!item.permission) return true      // 无权限要求→保留（公共入口）
                       return permissions.has(item.permission) // 有权限要求→检查
                   })
                └─ 过滤后 items.length === 0 → 整块不渲染
```

### 3.4 权限标识符

| 权限标识 | 对应功能入口 | 页面路径 |
|------|------|------|
| `app:study:view` | 课程学习 | /pages-sub/study/study |
| `app:exam:view` | 考试测评 | /pages-sub/study/exam |
| `app:practice:view` | 自主练习 | /pages-sub/study/practice |
| `app:wrong:view` | 错题集 | /pages-sub/study/wrong |
| `app:approval:view` | 审批模块 | /pages/approval/index |
| `app:alarm:view` | 报警模块 | /pages/alarm/index |

---

## 4. 功能模块树

### 4.1 完整页面层级

```
中集智能互联 小程序 (49页面)
│
├── 🏠 首页 (pages/index/index) ── TabBar
│   ├── 顶部用户区：头像 / 姓名 / 部门 / 角色标签（管理员|领导|主管|员工）
│   ├── 菜单卡片列表（按 category 分组，动态权限过滤）
│   │   └── 每卡片: categoryIcon + categoryName + badge + stats 统计行 + items 入口列表
│   └── 下拉刷新 → fetchMenus() 重新拉取
│
├── 📋 审批 (pages/approval/index) ── TabBar
│   ├── 审批列表 (pages/approval/index)
│   │   ├── 统计数字行：待审批 / 已通过 / 已驳回 / 我发起的（4 个 badge）
│   │   ├── 4 个 Tab：待审批(pending) / 已通过(approved) / 已驳回(rejected) / 我发起的(my)
│   │   ├── 每条显示：审核类型+文字 / 日期 / 工厂+班次 / 申请人 / 申请时间
│   │   │             SAP推送状态(SUCCESS/FAILED/MANUAL/PENDING) / 修订版本号角标
│   │   ├── 无限滚动分页（触底加载更多）
│   │   └── 下拉刷新
│   └── 审批详情 (pages/approval/detail)
│       └── 完整信息 + 通过(附comment) / 驳回(附reason)操作
│
├── 🔔 报警 (pages/alarm/index) ── TabBar
│   ├── 报警列表 (pages/alarm/index)
│   │   ├── 顶部统计卡片：总数 / 紧急数 / 今日新增 / 已处理数
│   │   ├── 4 个 Tab：全部(all) / 紧急(urgent) / 一般(normal) / 已处理(processed)
│   │   ├── 每条卡片：报警类型+等级 / 设备名称 / 点位 / 当前值+单位 / 阈值
│   │   │             相对时间（刚刚/N分钟前/N小时前/N天前/完整日期）
│   │   │             等级色标: urgent→红#ff4d4f / normal→橙#faad14 / info→蓝#1890ff
│   │   └── 下拉刷新
│   └── 报警详情 (pages/alarm/detail)
│       └── 完整信息 + 处理操作 PUT .../{id}/handle?handleResult=xxx
│
├── 👤 我的 (pages/mine/index) ── TabBar
│   ├── 个人信息展示：头像 / 姓名 / 部门 / 角色
│   ├── 功能入口列表：
│   │   ├── 自主练习 → /pages-sub/study/practice
│   │   ├── 消息推送设置 → /pages-sub/settings/message-settings
│   │   ├── 安全设置 → /pages-sub/settings/security-settings
│   │   ├── 清除缓存（保留 access_token / security_settings / msg_settings）
│   │   ├── 个人资料 → /pages/mine/profile
│   │   └── 关于 → /pages/mine/about
│   └── 退出登录（clearTokens + clearMenus + wx.reLaunch）
│
├── 📚 培训学习 (pages-sub/study/) ── 分包 14 页
│   ├── 培训计划列表 (index)
│   │   ├── 总进度环形图 + 计划总数
│   │   ├── 4 个 Tab：全部 / 进行中(1) / 已完成(2) / 未开始(0)
│   │   ├── 计划卡片：名称 / 状态标签 / 已完成课程数/总课程数 / 学习时长(h)
│   │   │             考试成绩 / 进度条(%) / 点击进入 plan-detail
│   │   ├── 进行中课程区块（快捷续学入口）
│   │   └── 已完成课程区块
│   ├── 计划详情 (plan-detail)
│   ├── 课程学习 (study)
│   │   ├── 课程信息：封面/名称/分类/讲师/时长/学习人数/描述
│   │   ├── POST start-study → 视频/文档学习(webview-preview)
│   │   └── 定时上报: POST update-progress { courseId, planId, progress }
│   ├── 考试列表 (exam)
│   │   ├── 4 种状态：待考(pending) / 进行中(in_progress) / 待补考(pending_retry) / 已完成(completed)
│   │   └── 考试卡片：名称/试卷/时长(分钟)/总分/及格分/时间/允许次数/已考次数
│   ├── 答题页 (answer)
│   │   ├── 顶部：考试标题 + CountDown 倒计时
│   │   ├── QuestionCard（5 种题型: 单选/多选/判断/填空/简答）
│   │   ├── 操作栏：上一题/下一题/标记(toggleMark)/答题卡(AnswerSheet)
│   │   ├── 倒计时→0 自动提交
│   │   └── ★ 断点续考: examStore Pinia persist 持久化全部状态
│   │       ├── 恢复: currentExamId / arrangeId / questions / answers / markedQuestions
│   │       ├── 倒计时重算: timeLeft = totalDuration - floor((Date.now()-startTime)/1000)
│   │       └── timeLeft ≤ 0 → 自动提交
│   ├── 考试结果 (result)
│   │   └── 成绩/正确率/是否通过(score≥passScore) + 全部题目对照 + 错题列表
│   ├── 自主练习列表 (practice)
│   │   ├── 统计面板：总练习数/总题数/正确率/总时长
│   │   └── 历史列表(custom/wrong)
│   ├── 创建练习 (practice-create)
│   │   ├── 题型多选/数量/难度/来源(错题专项开关)
│   │   └── startPractice() → Fisher-Yates 洗牌 → 随机抽取
│   ├── 练习答题 (practice-exam)
│   ├── 练习结果 (practice-result)
│   ├── 练习详情 (practice-detail)
│   ├── 错题集 (wrong)
│   │   ├── 统计：总题数/未掌握数/已掌握数
│   │   ├── 多维度筛选：题型 + 分类树 + 掌握状态
│   │   ├── 操作：标记掌握(mastered)/收藏(collect)/取消收藏(uncollect)
│   │   └── 错题专项练习 → auto-generate → practice-exam
│   ├── 错题详情 (wrong-detail)
│   │   └── 题目/我的答案/正确答案/解析/收藏状态/掌握状态/错题次数
│   ├── 文件预览 (webview-preview)
│   │   └── WebView 内嵌 PDF/视频预览
│   └── 安全 (safety)
│
├── 📊 生产报表 (pages-sub/report/) ── 分包 4 页
│   ├── 仪表盘 (index)
│   │   ├── 指标卡片：产量/合格率(%)/运行储罐数/正常设备数
│   │   ├── 快捷入口：生产日报/储罐监控/设备状态/备件库存
│   │   ├── 储罐液位概览（tankCode + percent + 颜色条）
│   │   └── 设备状态统计（正常N/维保N/故障N）
│   ├── 生产日报 (production)
│   │   └── 日报(templateId=1)/月报(2)/班报(shift) 三模板切换 + 指标数据表格
│   ├── 手工录入 (input)
│   │   ├── 权限检查: GET .../can-manual-input?instanceId=&shiftSlot=
│   │   └── 获取模板 → POST .../manual-input
│   └── 数据调整 (adjust)
│       ├── 权限检查: GET .../can-adjust?instanceId=&shiftSlot=
│       └── 获取可调整数据 → 提交（触发审批）
│
├── ⚙️ 设备管理 (pages-sub/equipment/) ── 分包 2 页
│   ├── 设备列表 (index)
│   │   ├── 统计面板：运行数/维保数/停机数
│   │   ├── 搜索(deviceName) + 装置下拉筛选(动态加载 unitOptions)
│   │   └── 设备卡片：名称/编码/类型/装置/传感器数/状态色标
│   └── 设备详情 (detail)
│
├── 📡 传感器 (pages-sub/sensor/) ── 分包 2 页
│   ├── 传感器列表 (index)
│   │   ├── 搜索(keyword) + 状态筛选(alarmLevel: 0全部/1正常/2预警/3报警)
│   │   │              + 类型筛选(sensorType: 压力/温度/液位/流量/浓度)
│   │   ├── 统计面板：正常数/预警数/报警数/总数
│   │   └── 传感器卡片：类型动态图标 + 名称/编码/设备/当前值(2位小数)+单位/报警色标
│   └── 传感器详情 (detail)
│
├── 📹 摄像头 (pages-sub/camera/) ── 分包 2 页
│   ├── 摄像头列表 (index)
│   │   ├── 统计：在线数/离线数/总数
│   │   ├── 区域筛选（横向滚动标签+数量角标）
│   │   ├── 视图切换：卡片网格(card) / 列表(list)
│   │   └── 状态：在线(实时画面+存储状态) / 离线(离线原因)
│   └── 摄像头详情 (detail)
│
├── 🛢️ 储罐 (pages-sub/tank/) ── 分包 2 页
│   ├── 储罐列表 (index)
│   └── 储罐监控详情 (detail) — 液位/压力/温度 + 趋势图
│
├── 💰 销售管理 (pages-sub/sale/) ── 分包 2 页
│   ├── 销售仪表盘 (index)
│   │   ├── 今日/当月销售额（千分位格式化）
│   │   ├── 7 日趋势柱状图（动态高度+最大值高亮）
│   │   └── 产品类型颜色: LNG→绿/氢气→蓝/焦油→橙/其他→灰
│   └── 添加订单 (add)
│       └── 客户→产品→合同 三级级联选择
│
├── 🧪 化验管理 (pages-sub/lab/) ── 分包 2 页
│   ├── 化验报告录入 (index)
│   │   ├── 大类切换：气体(gas)/水样(water) — 带今日统计数
│   │   ├── 子类型横向滚动（20+ gas子类 / 15+ water子类）
│   │   ├── 表单：采样日期(picker)/采样时间(picker)
│   │   │         取样点位(typeCode+subCode动态枚举, 1个→自动选中)
│   │   │         班组(一班~四班)/检验员(默认userInfo.realName)/复核员/备注
│   │   ├── 指标区：按 categoryName 分组 + 字段名(单位) + 标准范围 + NumberStepInput
│   │   ├── 草稿暂存: wx.setStorageSync('lab_draft_{typeId}', data)
│   │   │   └── 下次同类型→弹窗"检测到未提交草稿，是否恢复？"
│   │   └── 提交: POST /api/lab/report → 成功弹窗(查看记录/继续录入) → 清理草稿
│   └── 历史记录 (history)
│       └── 按日期筛选化验报告列表
│
├── 🚶 访客管理 (pages-sub/visitor/) ── 分包 3 页
│   ├── 访客登记 (index)
│   │   ├── 表单：姓名/单位/手机号(/^1\d{10}$/)/来访目的
│   │   ├── 搜索被访员工: GET .../host-employees?keyword=xxx（实时联想+列表选择）
│   │   ├── 提交: POST .../register
│   │   ├── 最近记录（前 3 条）
│   │   └── 审批进度入口
│   ├── 审批进度 (progress)
│   │   └── 全部记录: 状态(approved/rejected/pending) + 时间线 + rejectReason
│   └── 访客详情 (detail)
│
├── 👥 人员管理 (pages-sub/person/) ── 分包 2 页
│   ├── 人员列表 (index) — 搜索+筛选
│   └── 人员档案 (profile) — 详情 + Tab: 证书/考试记录/培训记录/资质
│
├── 📝 我的申请 (pages-sub/my-application/) ── 分包 3 页
│   ├── 申请列表 (index) — 状态统计
│   ├── 创建申请 (create)
│   └── 申请详情 (detail)
│
├── 💬 消息中心 (pages-sub/message/) ── 分包 2 页
│   ├── 消息列表 (index)
│   │   ├── 未读数角标 GET .../unread-count
│   │   ├── 全部标为已读 PUT .../read-all
│   │   └── 消息项: 标题/内容摘要/时间/已读未读状态
│   └── 消息详情 (detail) — 进入即标为已读 PUT .../read/{id}
│
├── ⚙️ 设置 (pages-sub/settings/) ── 分包 3 页
│   ├── 消息推送设置 (message-settings)
│   │   ├── 6 类开关(alarm/approval/study/task/announcement/safety) — Storage 持久化
│   │   └── 免打扰时段(picker-view): startTime/endTime("HH:MM")
│   ├── 安全设置 (security-settings)
│   │   ├── 修改密码: 旧→新(≥6位)→确认 → 成功后强制登出
│   │   ├── 生物识别开关(指纹/面容) — 启用前触发验证
│   │   ├── 设备管理入口 → device-manage
│   │   └── 隐私政策/用户协议入口
│   └── 设备管理 (device-manage) — GET /api/system/device/my-devices
│
├── 📧 意见反馈 (pages-sub/feedback/)
│   └── 反馈表单 (index) — POST /api/personnel/feedback/submit
│
└── 📄 法律条款 (pages-sub/legal/)
    ├── 用户服务协议 (user-agreement)
    └── 隐私政策 (privacy-policy)
```

---

## 5. 核心业务流程

### 5.1 微信登录 → 权限获取 → 首页呈现

```
[小程序冷启动]
    │
    ▼
app.js onLaunch()
    │
    ├─ Storage 中有 accessToken？
    │   ├─ NO  ──→ wx.reLaunch → /pages/login/index
    │   └─ YES → isLoginExpired(30)?
    │            ├─ YES → clearTokens() → wx.reLaunch 登录页
    │            └─ NO  → getUserInfo() → GET /api/auth/info
    │                     ├─ 成功 → recordLoginTime()
    │                     │   └─ needsSecurityVerify?(biometricEnabled)
    │                     │      ├─ YES → 指纹/面容验证 → 失败 → logout()
    │                     │      └─ NO  → 进入首页
    │                     └─ 失败 → http.js 401拦截器处理
    ▼
/pages/login/index
    ├─ [方式A] 手机号+密码
    │   ├─ 校验: 11位手机号+非空密码
    │   ├─ 协议勾选（未勾选→弹窗提示）
    │   ├─ phoneLogin(phone, password) → POST /api/app/auth/phone-login
    │   └─ setTokens + fetchMenus + recordLoginTime → wx.reLaunch 首页
    │
    └─ [方式B] 微信一键登录
        ├─ wx.login() → wxLogin(code) → POST /api/app/auth/wechat/login
        └─ needBind? → bindPhone(phoneCode, bindToken) → 同上
    ▼
/pages/index/index 首页
    ├─ 读取 userInfo → 计算角色标签 (管理员/领导/主管/员工) + CSS
    ├─ 读取 miniappMenus → 双重过滤（isAdmin跳过/permissions Set检查）
    └─ 动态 TabBar: getTabBarConfig() → roles匹配模板 → permissions过滤 → CustomTabBar渲染
```

### 5.2 培训学习全链路（小程序核心业务）

```
[培训计划] GET /api/personnel/training/plan/progress/my
    │  同时加载: GET .../study-record/my-list（进行中+已完成）
    │
    ├─ 点击计划 → plan-detail
    │   └─ GET .../plan/course/list/{planId}
    │
    ├─ 点击课程 → study
    │   ├─ POST .../start-study { courseId, planId }
    │   └─ 定时上报: POST .../update-progress { courseId, planId, progress }
    │
    └─ 进入考试
        ▼
[考试列表] GET .../my-exam/list
    │  4 种状态: pending / in_progress / pending_retry / completed
    │
    └─ 开始考试 → POST .../start/{arrangeId}
        └─ examStore.initExam() → Pinia persist → navigateTo answer
        ▼
[答题页] QuestionCard(5题型) + CountDown + AnswerSheet
    │  ★ 断点续考:
    │  退出→重进→hasOngoingExam()→恢复答案+标记+倒计时(重算)
    │  timeLeft = totalDuration - floor((Date.now()-startTime)/1000)
    │  ≤0→自动提交
    │
    └─ 提交 POST .../submit/{recordId} { answers[] }
        ▼
[考试结果] GET .../result/{recordId}
    ├─ score / isPass / 全部题目对照
    └─ 错题自动入错题集
        ▼
[错题集] 分类树筛选 + 标记掌握 + 收藏 + 错题专项练习
    └─ auto-generate → practice-exam

[自主练习]
    创建: startPractice({ types, count, difficulty, fromWrong })
        → Fisher-Yates 洗牌随机抽取 → practice-exam → submit → result
```

### 5.3 报警监控闭环

```
[后端 DCS] 传感器数据超过阈值 → 报警产生
    ▼
[报警列表] GET /api/alarm/record/list + GET .../statistics
    ├─ 统计: totalCount / urgentCount / todayCount / processedCount
    ├─ 筛选: all / urgent(红) / normal(橙) / processed(灰)
    ├─ 时间: <1分钟"刚刚" / <1小时"N分钟前" / <1天"N小时前" / <7天"N天前"
    └─ 状态: pending / processing / processed
    ▼
[报警详情] GET .../{id}
    └─ 处理: PUT .../{id}/handle?handleResult=xxx
```

### 5.4 化验报告移动采集全流程

```
[小程序] /pages-sub/lab/index
    │
    ├─ 1. 加载大类: GET /api/lab/indicator-type/by-code/gas(或water)
    ├─ 2. 选择子类型 → 动态获取取样点位(labSamplingConfig.js)
    ├─ 3. 加载化验指标: GET /api/lab/indicator-field/by-type/{typeId}
    │      └─ 按 categoryName 分组渲染指标输入区
    ├─ 4. 检查草稿: wx.getStorageSync('lab_draft_{typeId}')
    │      └─ 有 → 弹窗"是否恢复？"
    ├─ 5. 填写表单: 日期/时间/点位/班组/检验员/复核员/备注 + 指标值
    ├─ 6. 草稿暂存: wx.setStorageSync('lab_draft_{typeId}', ...)
    └─ 7. 提交: POST /api/lab/report
           └─ 成功 → 清理草稿 → 弹窗(查看记录/继续录入)
```

### 5.5 访客登记 → 审批 → 入园

```
[小程序] /pages-sub/visitor/index
    │
    ├─ 填写访客信息: 姓名/单位/手机号(/^1\d{10}$/)/来访目的
    ├─ 搜索被访员工: GET .../host-employees?keyword=xxx（实时联想）
    │   └─ 显示 realName+deptName → 点击选中确认
    ├─ 提交: POST .../register
    │   └─ Success → Toast + 清空表单 + 刷新最近记录
    │
    ├─ 最近记录(前3条): GET .../records?pageNum=1&pageSize=3
    │
    └─ 审批进度 → progress
        GET .../records → 全部记录
        └─ 状态: approved / rejected(附rejectReason) / pending
    ▼
[审批通过] → 访客凭通知入园
```

---

## 6. 测试风险矩阵

### 6.1 按模块评估

| 模块 | 页面 | 风险 | 风险原因 | 缓解措施 |
|------|:---:|:---:|------|------|
| **培训学习** | 14 | 🔴 最高 | 最大分包；断点续考、5种题型、倒计时自动提交、错题集多维度筛选+分类树；**零自动化** | P0 最优先；mock 考试数据；重点覆盖断点续考、超时提交、多选/填空作答 |
| **登录** | 1 | 🔴 高 | 唯一入口；Token刷新并发竞态、30天过期、生物识别、微信绑定/手机双通道 | 覆盖双通道全路径；并发401场景；生物识别启用/验证/失败/降级 |
| **审批** | 2 | 🔴 高 | 生产审批+SAP推送联动；4Tab+无限滚动；通过/驳回级联变更 | 全状态流转覆盖；SAP标记+版本号验证；分页边界 |
| **化验管理** | 2 | 🟡 中 | 2大类+35+子类+多取样点位动态枚举；指标动态分组；草稿暂存恢复；表单校验 | 参数化全覆盖；草稿保存/恢复+typeId隔离；提交后清理 |
| **报警** | 2 | 🟡 中 | 等级判断+状态流转+统计准确性+时间格式化边界 | 统计与列表一致；3等级×3状态交叉筛选；时间各边界值 |
| **生产报表** | 4 | 🟡 中 | 三模板切换+手工录入/调整权限校验+审批联动 | 覆盖三模板；验证权限返回；录入/调整拒绝场景 |
| **首页** | 1 | 🟡 中 | 菜单按角色+权限动态过滤；角色标签计算；TabBar动态渲染 | 多角色账号比对验证；无权限入口不可见 |
| **销售管理** | 2 | 🟡 中 | 客户/产品/合同三级级联；7日趋势图动态高度计算；数字格式化 | 级联选择正确性；趋势图边界值；格式化 |
| **设备管理** | 2 | 🟡 中 | 装置下拉动态+状态筛选联动；传感器计数 | 筛选联动；计数与统计一致 |
| **传感器** | 2 | 🟡 中 | 类型(5种)×级别(3种)组合筛选；实时数值精度 | 全部组合筛选；统计面板一致 |
| **访客管理** | 3 | 🟡 中 | 员工搜索联想+手机号校验+状态流转+必填校验 | 模糊/精确/无结果；手机号边界；提交后流转 |
| **摄像头** | 2 | 🟢 低 | 仅列表+详情；区域筛选+卡片/列表视图切换 | 区域联动+视图切换 |
| **我的申请** | 3 | 🟡 中 | 创建表单+状态统计+详情 | 创建提交流程；统计一致 |
| **消息中心** | 2 | 🟢 低 | 列表+已读/未读+批量+未读数角标 | 未读数一致；全标已读后清零 |
| **设置** | 3 | 🟢 低 | 6类开关+免打扰picker+密码修改+生物识别 | 开关持久化；密码错误场景；生物识别手工 |
| **储罐** | 2 | 🟢 低 | 仅列表+详情 | 加载+实时数据 |
| **人员管理** | 2 | 🟢 低 | 只读：列表+档案+4个Tab | 筛选+各Tab加载 |
| **反馈/法律** | 3 | 🟢 低 | 简单表单/纯文本 | 基本功能 |

### 6.2 全局技术风险

| 风险项 | 等级 | 影响范围 | 缓解措施 |
|------|:---:|------|------|
| Token 刷新并发竞态 | 🔴 高 | 所有 API 请求 | `isRefreshing` 锁+队列（已实现）；专项测试并发401 |
| uni-app 编译混淆 | 🔴 高 | 调试困难，报错无法定位源码 | 源码仓库+sourceMap；测试用非压缩构建 |
| 考试断点续考一致性 | 🟡 中 | examStore Persist | 倒计时实时重算；超时自动提交边界验证 |
| 分包首次加载延迟 | 🟡 中 | 16个分包 200-500ms下载 | 首次访问增加等待；关键分包预加载 |
| Storage 满/异常 | 🟡 中 | Pinia persist 失败 | try-catch 降级；测试 Storage 异常场景 |
| 生物识别兼容性 | 🟡 中 | 部分机型不支持 | 不支持时 Toast "不支持生物识别功能" |
| wot-design-uni 样式 | 🟡 中 | 组件样式冲突 | `.wxss` 覆盖 + `styleIsolation:"shared"` |
| 化验草稿类型错配 | 🟡 中 | 切换子类型后草稿不匹配 | `lab_draft_{typeId}` 按 typeId 隔离 |

---

## 7. 自动化优先级建议

### 7.1 优先级定义

| 级别 | 定义 | 目标频率 | 建议工具 |
|:---:|------|:---:|------|
| **P0** | 必须自动化 — 核心链路、高频操作、回归开销大 | 每次提测前 | Minium / miniprogram-automator |
| **P1** | 建议自动化 — 重要但变更频率较低 | 每迭代一次 | Minium |
| **P2** | 手工即可 — 低频、依赖设备、一次性 | 按需 | 手工+探索性 |

### 7.2 各模块优先级

#### P0 — 必须自动化

| 模块 | 关键场景 | 理由 |
|------|------|------|
| 登录 | 手机号密码登录（含协议/校验）、Token过期刷新、30天过期登出 | 唯一入口，阻塞所有后续 |
| 首页 | admin/employee/contractor 三个角色菜单渲染 + TabBar 切换 | 权限过滤核心出口 |
| 培训-考试 | 列表→开始→答题(5题型)→标记→倒计时→提交→结果 | 14页分包核心链路 |
| 培训-断点续考 | 答题中退出→重进→恢复答案/标记/倒计时→继续 | 最复杂状态持久化 |
| 培训-练习 | 自定义创建→作答→提交→结果 | 高频使用 |
| 培训-错题集 | 分类树筛选+题型筛选+掌握+收藏 | 学习闭环末端 |
| 审批 | 4Tab切换+无限滚动+通过/驳回 | 核心业务 |
| 报警 | 统计面板+等级/状态筛选+详情+处理 | 核心监控 |
| 化验 | 类型×子类型×点位→指标录入→提交（参数化全覆盖） | 参数组合多，手工无法穷举 |

#### P1 — 建议自动化

| 模块 | 场景 | 理由 |
|------|------|------|
| 生产报表 | 日报/月报/班报+手工录入/调整权限 | 格式可能变更 |
| 销售 | 仪表盘趋势图+订单级联选择 | 动态图表+级联 |
| 设备 | 搜索+装置联动+状态统计 | 筛选联动回归 |
| 传感器 | 类型×级别组合筛选+统计面板 | 多维组合 |
| 摄像头 | 区域筛选+卡片/列表视图 | 特殊交互 |
| 访客 | 登记+员工搜索+进度 | 外部用户可见 |
| 人员 | 列表+档案多Tab | 多Tab数据 |
| 我的申请 | 创建+状态统计 | 流程完整性 |
| 消息 | 未读数+全标已读 | 统计一致性 |

#### P2 — 手工即可

| 模块 | 理由 |
|------|------|
| 设置（推送/安全/设备） | 低频+设备依赖 |
| 反馈/法律条款 | 简单表单/纯文本 |
| 储罐/关于/清除缓存 | 简单只读/一次性 |
| demo | 不交付 |

### 7.3 框架选型建议

| 工具 | 语言 | 优点 | 缺点 |
|------|:---:|------|------|
| **Minium**（微信官方） | Python | 官方支持、文档完整、真机/模拟器 | Python 栈 |
| **miniprogram-automator** | JS/TS | 原生 JS、可直接调 wx API | Node 环境 |
| **Airtest + poco** | Python | 跨平台、图像识别辅助 | 图像不稳定 |

---

## 8. 已完成的测试工作

### 8.1 小程序端测试现状

| 维度 | 现状 |
|------|------|
| 手工测试 | 已覆盖登录、首页、审批、报警等核心页面基本功能 |
| 自动化测试 | **零覆盖**（512 条自动化全部在 Web 管理后台端） |
| 小程序专项自动化 | **待启动**（需引入 Minium/miniprogram-automator） |

### 8.2 各模块覆盖情况

| 模块 | 页面 | 手工测试 | 自动化 | 优先级 |
|------|:---:|:---:|:---:|:---:|
| 登录 | 1 | ✅ 全流程 | ❌ | |
| 首页 | 1 | ✅ 基本 | ❌ | |
| 审批 | 2 | ✅ 基本 | ❌ | |
| 报警 | 2 | ✅ 基本 | ❌ | |
| 培训学习 | 14 | ⚠️ 部分 | ❌ | **最需自动化** |
| 化验 | 2 | ✅ 基本 | ❌ | |
| 生产报表 | 4 | ⚠️ 部分 | ❌ | |
| 访客 | 3 | ⚠️ 部分 | ❌ | |
| 设备/传感器/摄像头/储罐 | 8 | ⚠️ 部分 | ❌ | |
| 销售 | 2 | ⚠️ 部分 | ❌ | |
| 人员 | 2 | ❌ | ❌ | |
| 我的申请 | 3 | ❌ | ❌ | |
| 消息 | 2 | ❌ | ❌ | |
| 设置 | 3 | ⚠️ 部分 | ❌ | |
| 反馈/法律 | 3 | ❌ | ❌ | **未测** |

### 8.3 亟待启动的工作

| 优先级 | 工作项 | 预计 | 覆盖 |
|:---:|------|:---:|:---:|
| 1 | 搭建 Minium 自动化框架 | 2 天 | 基础架构 |
| 2 | 登录+首页 P0 用例 | 1 天 | 2 页 |
| 3 | 培训学习 P0 用例（考试+断点续考+练习+错题集） | 3 天 | 8 页 |
| 4 | 审批+报警 P0 用例 | 1 天 | 3 页 |
| 5 | 化验 P0 用例（参数化全覆盖） | 1.5 天 | 2 页 |
| 6 | 其余 P1 用例逐步补充 | 5 天 | 34 页 |
| | **合计** | **~13.5 天** | **49 页** |

---

## 9. 踩坑经验

### 9.1 小程序特有的技术难点

| # | 问题描述 | 根因 | 解决方案 | 涉及文件 |
|:---:|------|------|------|:---:|
| 1 | **uni-app 编译后代码混淆不可读** | .vue（template+render+style+logic）合并为单文件压缩 JS | 源码仓库+.vue 维护；`uploadWithSourceMap:true`；测试人员获取源码访问权限 | `project.config.json` |
| 2 | **Token 刷新并发竞态致重复登录** | 多 API 同时 401 → 各自触发 refresh → Token 错乱 | `isRefreshing` 锁+`requestQueue`：第一个刷新→其余入队→统一重放/统一登出 | `utils/http.js` |
| 3 | **生物识别验证干扰测试连续性** | 切后台>5min 回前台触发指纹/面容 → 失败强制登出 | 测试环境 `setSecuritySettings({ biometricEnabled: false })` | `app.js` |
| 4 | **断点续考倒计时恢复不准确** | persist 的 `timeLeft` 是静态快照，与客户端实际流逝时间不一致 | 恢复时重算：`totalDuration-floor((Date.now()-startTime)/1000)`；≤0→自动提交 | `store/exam.js` |
| 5 | **分包首次加载慢于预期** | 16 分包按需下载（200-500ms），测试操作在渲染前执行 | 首次 `navigateTo` 分包页+1~2s；关键分包 `preloadRule` 预加载 | `app.json` |
| 6 | **化验草稿恢复弹窗干扰自动化** | `wx.showModal` 弹窗是否出现取决于 Storage 是否有草稿 | `lab_draft_{typeId}` 隔离；测试前清理 `lab_draft_*` Storage | `pages-sub/lab/index.js` |
| 7 | **练习随机抽取偶发失败** | 某题型可用题目 < 需求数时抽取不足 | Fisher-Yates 洗牌+`slice(0,count)`；前端校验 `count≤可用总数` | `service/practice.js` |
| 8 | **wot-design-uni 样式在小程序异常** | 组件 CSS 变量与 `styleIsolation` 冲突 | 页面 `.wxss` 覆盖+`styleIsolation:"shared"` | 各页 `.wxss` |

### 9.2 业务逻辑注意事项

| # | 注意点 | 详情 |
|:---:|------|------|
| 1 | 30 天过期公式 | `Date.now()-lastLoginTime > 30×24×60×60×1000` |
| 2 | 5 分钟后台验证 | `Date.now()-lastShowTime > 300000`，仅 `biometricEnabled=true` |
| 3 | 化验取样点位 | typeCode×subCode 动态枚举；1个→自动选中，多个→picker |
| 4 | 考试 store 必须 clear | 新考试前 `clearExam()`，否则 `hasOngoingExam()===true` |
| 5 | 审批 SAP 状态 4 种 | SUCCESS/FAILED/MANUAL/PENDING，各色标不同 |
| 6 | 消息免打扰格式 | `HH:MM`，picker-view 滚轮，存储 key `msg_settings` |
| 7 | 访客手机号校验 | 正则 `/^1\d{10}$/`，仅格式不验真实性 |
| 8 | 密码修改后强制登出 | `setTimeout(logout, 1000)` → `wx.reLaunch` 登录页 |

---

## 附录 A：页面对应 API 速查表

| 页面路径 | 核心 API |
|------|------|
| `pages/login/index` | `POST /api/app/auth/phone-login`, `POST .../wechat/login`, `POST .../wechat/bind-phone` |
| `pages/index/index` | `GET /api/system/menu/miniapp/menus`, `GET /api/auth/info` |
| `pages/approval/index` | `GET /api/production/approval/pending\|approved\|my-applications` |
| `pages/approval/detail` | `GET /api/production/approval/{id}`, `POST .../approve/{id}`, `POST .../reject/{id}` |
| `pages/alarm/index` | `GET /api/alarm/record/list`, `GET .../statistics` |
| `pages/alarm/detail` | `GET /api/alarm/record/{id}`, `PUT .../{id}/handle` |
| `pages-sub/study/index` | `GET /api/personnel/training/plan/progress/my`, `GET .../study-record/my-list` |
| `pages-sub/study/study` | `GET /api/personnel/training/course/{id}`, `POST .../start-study\|update-progress` |
| `pages-sub/study/exam` | `GET /api/personnel/training/my-exam/list\|statistics` |
| `pages-sub/study/answer` | `POST .../start/{id}`, `POST .../submit/{id}` |
| `pages-sub/study/result` | `GET .../result/{id}` |
| `pages-sub/study/practice` | `GET /api/personnel/training/practice/list\|questions\|statistics` |
| `pages-sub/study/wrong` | `GET /api/personnel/training/wrong-question/list\|statistics\|category/tree` |
| `pages-sub/lab/index` | `GET /api/lab/indicator-type/by-code/{type}`, `GET .../indicator-field/by-type/{id}`, `POST /api/lab/report` |
| `pages-sub/report/production` | `GET /api/production/report-instance/daily\|monthly\|shift` |
| `pages-sub/equipment/index` | `GET /api/equipment/miniapp/device/list\|statistics\|units` |
| `pages-sub/sensor/index` | `GET /api/equipment/miniapp/sensor/list\|statistics` |
| `pages-sub/camera/index` | `GET /api/equipment/miniapp/camera/list\|statistics\|areas` |
| `pages-sub/tank/index` | `GET /api/tank/miniapp/list` |
| `pages-sub/sale/index` | `GET /api/sales/daily-report/list` |
| `pages-sub/visitor/index` | `GET /api/personnel/miniapp/visitor/host-employees`, `POST .../register` |
| `pages-sub/message/index` | `GET /api/system/notice/my`, `GET .../unread-count`, `PUT .../read-all\|read/{id}` |
| `pages-sub/settings/security-settings` | `PUT /api/auth/change-password` |
| `pages-sub/settings/device-manage` | `GET /api/system/device/my-devices` |

## 附录 B：全局组件清单

| 组件 | 用途 | 关键属性/事件 |
|------|------|------|
| `CustomTabBar` | 自定义底部导航栏 | `current-page` |
| `QuestionCard` | 5 种题型渲染 | `question`, `answer`, `showResult`, `showAnalysis` |
| `AnswerSheet` | 答题卡面板 | `questions`, `answers`, `markedQuestions`, `currentIndex` |
| `CountDown` | 考试倒计时 | `duration`(秒), `onTimeout` |
| `Empty` | 空状态占位 | `title`, `icon` |
| `NumberStepInput` | 数字步进输入 | `value`, `min`, `max`, `step` |

## 附录 C：Storage Key 清单

| Key | 用途 | 写入方 |
|------|------|------|
| `access_token` | JWT accessToken | `utils/auth.js` |
| `refresh_token` | JWT refreshToken | `utils/auth.js` |
| `bind_token` | 微信绑定临时 token | 登录流程 |
| `user_info` | 用户信息（Pinia persist） | `store/user.js` |
| `security_settings` | `{ biometricEnabled, lastLoginTime }` | `utils/auth.js` |
| `msg_settings` | `{ alarm, approval, study, task, announcement, safety, startTime, endTime }` | `pages-sub/settings/message-settings.js` |
| `lab_draft_{typeId}` | 化验草稿（按 typeId 隔离） | `pages-sub/lab/index.js` |
| `menu` | Pinia persist：菜单数据 | `store/menu.js` |
| `exam` | Pinia persist：考试全态 | `store/exam.js` |

## 附录 D：化验取样点位枚举

| 大类 | 子类 Key | 子类名称 | 取样点位 |
|------|------|------|------|
| gas | raw_gas | 原料气 | 原料气进口、原料气出口 |
| gas | deoiling | 脱油脱萘 | 脱油脱萘进口、脱油脱萘出口 |
| gas | methanation | 甲烷化 | 甲烷化进口、甲烷化出口 |
| gas | fine_desulfurization_1 | 精脱硫1 | 精脱硫1进口、精脱硫1出口 |
| gas | fine_desulfurization_2 | 精脱硫2 | 精脱硫2进口、精脱硫2出口 |
| gas | ultra_fine_inlet | 超精入口 | 超精入口 |
| gas | ultra_fine_outlet | 超精出口 | 超精出口 |
| gas | cold_box_inlet | 冷箱入口 | 冷箱入口 |
| gas | hydrogen_rich | 富氢气 | 富氢气出口 |
| gas | nitrogen_rich | 富氮气 | 富氮气出口 |
| gas | lng | LNG | LNG储罐 |
| gas | refrigerant | 制冷剂 | 制冷剂出口 |
| gas | ammonia_inlet | 入塔气 | 入塔气 |
| gas | ammonia_outlet | 出塔气 | 出塔气 |
| gas | liquid_ammonia | 液氨 | 液氨储罐 |
| water | circulating_water | 循环水 | 循环水入口、循环水出口、冷却塔 |
| water | circulating_inlet | 循环水进水 | 循环水进水口 |
| water | desalinated_water | 脱盐水 | 脱盐水槽、脱盐水出口 |
| water | desalinated_raw | 脱盐水原水 | 脱盐水原水口 |
| water | desalinated_waste | 脱盐水废水 | 脱盐水废水口 |
| water | steam_water | 汽包水 | 汽包水进口、汽包水出口 |
| water | deoxidized_water | 除氧水 | 除氧水进口、除氧水出口 |
| water | stripper | 气提塔 | 气提塔 |
| water | ammonia_boiler | 废热锅炉 | 废热锅炉 |
| water | clean_waste | 清净废水 | 清净废水口 |
| — | extra_sample | 加样 | 加样口 |

---

> **文档维护说明**：本文档聚焦微信小程序端。Web 管理后台请参考 `PROJECT_WEB_CONTEXT.md`。每次新增页面/分包、变更 API 接口、或发现新的平台特有踩坑经验后，请同步更新对应章节。
