# AUTO_STRATEGY — equipment / alarm-config

> 产出于 automation-implementation Workflow 实战验证（2026-06-11）
> 基于：TECH_ANALYSIS.md + 现有测试脚本 test_alarm_config.py

## 自动化目标
覆盖设备报警配置页的稳定功能：统计卡片校验、搜索筛选、表格展示、分页操作。
弹窗 CRUD 因 Element Plus 2.x filterable select is_displayed 问题，暂通过 API 层验证。

## 推荐策略
- 脚本层级：AlarmConfigPage（主页面）→ conftest.py → test_alarm_config.py
- 断言层级：页面级（元素可见）+ 数据级（表格内容/统计数字）+ API级（弹窗CRUD绕过UI）
- 数据策略：`data/alarm_config_data.py` 提供表头集合、搜索关键词等常量
- 清理策略：API 层增删操作在 fixture teardown 中清理

## 覆盖矩阵

| 用例编号 | 标题 | 优先级 | 自动化 | 理由 |
|----------|------|--------|--------|------|
| AC-01 | 页面正常加载 | P0 | ✅ | 冒烟必测，navigate() + wait_table_loaded() |
| AC-02 | 表格表头正确显示 | P0 | ✅ | 表头集合 data-driven 校验 |
| AC-03 | 搜索输入框可见 | P0 | ✅ | 元素存在性断言 |
| AC-04 | 新增按钮可见 | P0 | ✅ | 权限校验基础 |
| AC-05 | 统计卡片数据校验 | P0 | ✅ | 统计数字非空/格式校验 |
| (P1) | 关键词搜索 | P1 | ✅ | 已有 search() 方法 |
| (P1) | 报警类型筛选 | P1 | ✅ | select_option() 已验证 |
| (P2+) | 新增弹窗-提交 | P2 | 🔄 API绕过 | el-select filterable is_displayed 坑 |
| (P2+) | 编辑弹窗-数据回显 | P2 | 🔄 API绕过 | 同上 |
| (P2+) | 启用/禁用开关 | P2 | ❌(暂) | el-switch click 不可靠 |

## PageObject 拆分
```
AlarmConfigPage  ← 统计卡片 + 搜索区 + 表格 + 分页（稳定已验证）
(AlarmConfigDialog) ← 弹窗CRUD（标记 @skip，待 Element Plus 2.x 适配方案）
```

## 公共组件复用
| 方法 | 来源 | 复用状态 |
|------|------|----------|
| navigate_to() | BasePage | ✅ |
| wait_table_loaded() | BasePage | ✅ |
| wait_loading_disappear() | BasePage | ✅ |
| input_text() | BasePage | ✅ |
| click_element() | BasePage (3级降级) | ✅ |
| select_option() | ElementPlusHelper | 部分可用 |
| get_table_data() | ElementPlusHelper | ✅ |
| get_pagination_info() | ElementPlusHelper | ✅ |

## ROI 分析
| 指标 | 值 |
|------|----|
| 已投入开发时间 | ~3 小时（已有可运行代码） |
| 维护成本 | ~0.5 小时/月（定位器偶尔调整） |
| 手工执行时间 | 10 分钟/次 |
| 执行频率 | 每次部署后 + 每周回归 |
| 当前状态 | P0/P1 稳定执行中 |

## 遗留技术债
1. **el-select filterable + teleport**：需要研究 ElementPlusHelper 扩展方案（如用 JS 直接操作 body 层选项）
2. **el-switch 操作**：需要稳定的 click 降级方案
3. **弹窗多实例**：当页面上有多个 el-dialog 时，需更精确的弹窗定位策略
