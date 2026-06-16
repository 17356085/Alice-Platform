# TEST_DESIGN — equipment / maintenance

> 基于 PAGE_CONTEXT + TECH_ANALYSIS + AUTO_STRATEGY | 2026-06-11

## 1. 页面加载 (P0)
- MT-01: 正常加载(30s超时)→表格+搜索区+分页可见 ✅
- MT-02: 表格表头完整性 ✅

## 2. 搜索筛选 (P1)
- MT-03: 维保类型筛选(el-select) ✅
- MT-04: 状态筛选(el-select) ✅
- MT-05: 关键词搜索 🔄
- MT-06: 重置搜索 ✅

## 3. 分页 (P1)
- MT-07: 翻页→数据变化 ✅

## 4. 弹窗CRUD (P1) — role="dialog" 结构
- MT-08: 新增计划-打开弹窗 ✅
- MT-09: 新增计划-提交→Toast ✅
- MT-10: 新增计划-取消 ✅
- MT-11: 编辑-数据回显 🔄
- MT-12: 编辑-修改保存 🔄

## 5. 行内操作 (P1)
- MT-13: 生成任务 🔄

## 覆盖: P0=2/2 ✅ | P1=8/11 | 总计13 | 自动化率69%(9/13)

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 | next_agent: automation-agent -->
