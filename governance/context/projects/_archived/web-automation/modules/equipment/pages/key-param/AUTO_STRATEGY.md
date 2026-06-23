# AUTO_STRATEGY — equipment / key-param

> 基于 TECH_ANALYSIS.md + 现有 KeyParamPage.py | 2026-06-11
> 页面类型: 统计卡片 + el-table + 非标准搜索区（裸input）

## 自动化目标

覆盖关键参数监控页面的统计卡片校验、表格展示、分页和弹窗CRUD。搜索区为标准结构缺失的变体，关键词输入定位器为 C 级脆弱。

## 推荐策略

- 脚本层级: KeyParamPage → conftest.py → test_key_param.py
- 断言层级: 统计卡片数值/表格数据/弹窗可见性/运行状态文本
- 数据策略: 运行状态为纯文本（非el-tag），按列索引取值
- 清理策略: 弹窗CRUD通过API层操作，fixture teardown清理

## 覆盖矩阵

| 用例编号 | 标题 | 优先级 | 自动化 | 理由 |
|----------|------|--------|--------|------|
| KP-01 | 页面正常加载 | P0 | ✅ | navigate + 统计卡片 + 表格出现 |
| KP-02 | 统计卡片数据校验 | P0 | ✅ | 总数/正常/预警/报警 四卡片数值≥0 |
| KP-03 | 表格表头完整性 | P0 | ✅ | 9列表头校验 |
| KP-04 | 关键词搜索 | P1 | ✅ | 裸input输入 + 等待表格刷新 |
| KP-05 | 重置按钮 | P1 | ✅ | danger样式重置按钮 |
| KP-06 | 分页操作 | P1 | ✅ | 标准 el-pagination |
| KP-07 | 查看详情弹窗 | P1 | ✅ | el-dialog 标准结构 |
| KP-08 | 编辑弹窗-数据回显 | P1 | 🔄 | el-dialog CRUD |
| KP-09 | 删除操作 | P1 | 🔄 | 确认弹窗 + 表格刷新 |
| KP-10 | 运行状态校验 | P1 | ✅ | 纯文本列，按列索引读取 |

## PageObject 拆分

```
KeyParamPage  ← 统计卡片 + 搜索区（裸input+重置）+ 表格 + 分页 + 弹窗CRUD
  搜索区无标准结构 — 定位器使用复杂排除规则
  运行状态纯文本 — 自定义 get_status_text(row) 方法
```

## 公共组件复用

| 方法 | 来源 | 复用状态 |
|------|------|----------|
| navigate_to() | BasePage | ✅ |
| wait_table_loaded() | BasePage | ✅ |
| click_element() | BasePage (3级降级) | ✅ |
| get_table_data() | ElementPlusHelper | ✅ |
| get_pagination_info() | ElementPlusHelper | ✅ |
| INPUT_KEYWORD (自定义) | KeyParamPage | ⚠️ C级定位器，需关注稳定性 |

## ROI 分析

| 指标 | 值 |
|------|-----|
| 已投入开发时间 | ~2 小时 |
| 维护成本 | ~0.4 小时/月（C级定位器易碎） |
| 手工执行时间 | 10 分钟/次 |
| 执行频率 | 每次部署 + 每周回归 |
| 自动化率(预估) | 70% (7/10) |

## 遗留技术债

1. **关键词输入框无 placeholder**: C 级定位器（复杂排除规则），建议申请 `data-testid="key-param-search"`
2. **运行状态为纯文本**: 无法用 el-tag class 定位，按列索引依赖列顺序不变
3. **搜索区无标准结构**: 未来如果页面重构为标准 el-form inline，需更新定位器

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 | next_phase: Phase 4 | next_agent: automation-agent -->
