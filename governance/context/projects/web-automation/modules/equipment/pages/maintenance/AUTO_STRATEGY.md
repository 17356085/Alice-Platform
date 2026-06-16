# AUTO_STRATEGY — equipment / maintenance

> 基于 TECH_ANALYSIS.md + 现有 MaintenancePage.py | 2026-06-11
> 页面类型: 标准 el-table CRUD + role="dialog" 弹窗

## 自动化目标

覆盖维保计划管理页面的搜索筛选、表格展示、分页操作和弹窗CRUD。弹窗使用 role="dialog" 结构，需覆盖 BasePage 通用定位器。

## 推荐策略

- 脚本层级: MaintenancePage → conftest.py → test_maintenance_management.py
- 断言层级: 表格数据/弹窗可见性/Toast消息/分页信息
- 数据策略: 测试数据 API 创建 → 页面操作验证 → fixture teardown API 删除
- 清理策略: CleanupTracker 注册，teardown 中 API DELETE

## 覆盖矩阵

| 用例编号 | 标题 | 优先级 | 自动化 | 理由 |
|----------|------|--------|--------|------|
| MT-01 | 页面正常加载 | P0 | ✅ | navigate + wait_table_loaded |
| MT-02 | 表格表头完整性 | P0 | ✅ | 表头列表对比 |
| MT-03 | 维保类型筛选 | P1 | ✅ | el-select 标准操作 |
| MT-04 | 状态筛选 | P1 | ✅ | el-select 标准操作 |
| MT-05 | 关键词搜索 | P1 | 🔄 | 搜索框定位待确认 |
| MT-06 | 重置搜索 | P1 | ✅ | 已有 reset 按钮定位 |
| MT-07 | 分页-翻页 | P1 | ✅ | 标准 el-pagination |
| MT-08 | 新增计划-打开弹窗 | P1 | ✅ | role="dialog" 弹窗定位已验证 |
| MT-09 | 新增计划-提交 | P1 | ✅ | dialog save + toast 验证 |
| MT-10 | 新增计划-取消 | P1 | ✅ | dialog cancel 定位已验证 |
| MT-11 | 编辑计划-数据回显 | P1 | 🔄 | el-select 回显待验证 |
| MT-12 | 编辑计划-修改保存 | P1 | 🔄 | 同上 |
| MT-13 | 生成任务 | P1 | 🔄 | 行内按钮+确认弹窗 |

## PageObject 拆分

```
MaintenancePage  ← 搜索区 + 表格 + 分页 + 弹窗CRUD
  弹窗使用 role="dialog"，覆盖 BasePage.DIALOG 等通用定位器
```

## 公共组件复用

| 方法 | 来源 | 复用状态 |
|------|------|----------|
| navigate_to() | BasePage | ✅ |
| wait_table_loaded() | BasePage | ✅ |
| click_element() | BasePage (3级降级) | ✅ |
| input_text() | BasePage | ✅ |
| get_table_data() | ElementPlusHelper | ✅ |
| get_pagination_info() | ElementPlusHelper | ✅ |
| DIALOG (覆盖) | MaintenancePage | ⚠️ 覆盖 BasePage，使用 role="dialog" |

## ROI 分析

| 指标 | 值 |
|------|-----|
| 已投入开发时间 | ~2.5 小时 |
| 维护成本 | ~0.5 小时/月 |
| 手工执行时间 | 12 分钟/次 |
| 执行频率 | 每次部署 + 每周回归 |
| 自动化率(预估) | 69% (9/13) |

## 遗留技术债

1. **页面加载慢（30s超时）**: WebDriverWait 设为30s，需关注 CI 稳定性
2. **Vue Router 可能未生效**: 回退侧边栏导航作为降级

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 | next_phase: Phase 4 | next_agent: automation-agent -->
