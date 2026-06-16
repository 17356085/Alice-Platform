/**
 * 测试配置中心
 *
 * 所有测试账号、URL、超时、角色映射集中管理。
 * .env 中的变量通过 process.env 注入，此处做解析和默认值处理。
 */
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '..', '..', '.env') });

const config = {
  // ── 环境 ──
  env: process.env.ENV || 'test',
  baseUrl: process.env.BASE_URL || 'https://aiwechatminidemo.cimc-digital.com',

  // ── 项目路径 ──
  miniProjectPath: path.resolve(__dirname, '..', '..',
    process.env.MINI_PROJECT_PATH || '../mp-weixin'),

  // ── 超时（毫秒） ──
  timeout: {
    default: parseInt(process.env.TEST_TIMEOUT || '120000', 10),
    navigation: 30000,
    element: 15000,
    dataReady: 30000,
    login: 30000,
    examSubmit: 30000,
    weakNetwork: 60000,
  },

  // ── 测试账号池（手机号登录，密码统一 Ajyl@2026）──
  accounts: {
    admin: {
      username: 'admin',
      phone: process.env.ADMIN_PHONE || '13411572537',
      password: process.env.ADMIN_PASSWORD || 'Ajyl@2026',
      description: '超级管理员 — 全部权限',
      expectedTabs: ['home', 'approval', 'alarm', 'mine'],
      expectedRole: '管理员',
    },
    manager: {
      username: 'tjw',
      phone: process.env.MANAGER_PHONE || '15521061110',
      password: process.env.MANAGER_PASSWORD || 'Ajyl@2026',
      description: '部门经理 — 审批+报警权限',
      expectedTabs: ['home', 'approval', 'alarm', 'mine'],
      expectedRole: '部门经理',
    },
    employee: {
      username: 'Test001',
      phone: process.env.EMPLOYEE_PHONE || '17189202123',
      password: process.env.EMPLOYEE_PASSWORD || 'Ajyl@2026',
      description: '普通员工 — 仅培训+我的',
      expectedTabs: ['home', 'training', 'mine'],
      expectedRole: '员工',
    },
    contractor: {
      username: 'Test002',
      phone: process.env.CONTRACTOR_PHONE || '18129104567',
      password: process.env.CONTRACTOR_PASSWORD || 'Ajyl@2026',
      description: '承包商 — 仅培训+我的',
      expectedTabs: ['home', 'training', 'mine'],
      expectedRole: '承包商',
    },
    // 备用/其他账号
    chenqian: {
      username: 'chenqian',
      phone: '13378402325',
      password: 'Ajyl@2026',
      description: 'chenqian 账号',
    },
    Test003: {
      username: 'Test003',
      phone: '13567842120',
      password: 'Ajyl@2026',
      description: 'Test003 账号',
    },
    Test004: {
      username: 'Test004',
      phone: '15928104327',
      password: 'Ajyl@2026',
      description: 'Test004 账号',
    },
    rbactest: {
      username: 'rbactest1781155271',
      phone: '13881155271',
      password: 'Ajyl@2026',
      description: 'RBAC 测试账号',
    },
  },

  // ── 角色-TabBar 期望映射 ──
  roleTabMap: {
    admin: ['home', 'approval', 'alarm', 'mine'],
    admin_miniapp: ['home', 'approval', 'alarm', 'mine'],
    lingdaoceng_miniapp: ['home', 'approval', 'training', 'mine'],
    buzhuguan_miniapp: ['home', 'approval', 'training', 'mine'],
    manager: ['home', 'approval', 'alarm', 'mine'],
    yuangong: ['home', 'training', 'mine'],
    chengbaoshang_miniapp: ['home', 'training', 'mine'],
  },

  // ── 角色-首页菜单可见性期望 ──
  roleExpectedMenus: {
    admin: ['生产报表', '储罐监控', '设备管理', '传感器管理', '摄像头管理',
            '化验室取样', '销售管理', '在线学习', '考试测评', '自主练习',
            '错题集', '访客管理', '我的申请', '人员管理'],
    yuangong: ['在线学习', '考试测评', '自主练习', '错题集'],
    chengbaoshang_miniapp: ['在线学习', '考试测评', '自主练习', '错题集'],
  },

  // ── TabBar 配置（与 app.json 和 utils/tabbar.js 保持一致） ──
  tabBars: {
    home: { pagePath: '/pages/index/index', text: '首页', icon: 'home' },
    approval: { pagePath: '/pages/approval/index', text: '审批', icon: 'check-circle' },
    alarm: { pagePath: '/pages/alarm/index', text: '报警', icon: 'notification' },
    training: { pagePath: '/pages-sub/study/index', text: '培训', icon: 'books' },
    mine: { pagePath: '/pages/mine/index', text: '我的', icon: 'user' },
  },

  // ── 化验室取样静态配置（与 config/labSamplingConfig.js 保持一致） ──
  labSampling: {
    gasLocations: {
      raw_gas: ['原料气进口', '原料气出口'],
      deoiling: ['脱油脱萘进口', '脱油脱萘出口'],
      methanation: ['甲烷化进口', '甲烷化出口'],
      lng: ['LNG储罐'],
    },
    waterLocations: {
      circulating_water: ['循环水入口', '循环水出口', '冷却塔'],
      desalinated_water: ['脱盐水槽', '脱盐水出口'],
    },
  },

  // ── 截图配置 ──
  screenshotDir: process.env.SCREENSHOT_DIR || './artifacts/screenshots',
  screenshotOnFailure: process.env.SCREENSHOT_ON_FAILURE !== 'false',
};

module.exports = { config };
