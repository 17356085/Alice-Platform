# TEST_DESIGN — equipment / camera

> 基于 PAGE_CONTEXT + TECH_ANALYSIS + AUTO_STRATEGY | 2026-06-11

## 1. 页面加载 (P0)
- CM-01: 正常加载→统计卡片+监控网格+分页可见 ✅
- CM-02: 统计卡片数据校验(总数/在线/离线/故障) ✅
- CM-03: 摄像头网格展示(monitor-cell≥1) ✅

## 2. 搜索筛选 (P1)
- CM-04: 关键词搜索→网格更新 ✅
- CM-05: 在线状态筛选→结果均为在线 ✅
- CM-06: 故障状态筛选→结果均为故障 🔄

## 3. 分页 (P1)
- CM-07: 翻页→monitor-cell变化 ✅

## 4. 弹窗 (P2)
- CM-08: 摄像头详情弹窗 ❌(video跨域)
- CM-09: 视频实时预览 ❌

## 覆盖: P0=3/3 ✅ | P1=3/4 | P2=0/2 | 自动化率67%(6/9)

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 | next_agent: automation-agent -->
