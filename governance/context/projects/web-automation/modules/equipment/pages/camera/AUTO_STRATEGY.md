# AUTO_STRATEGY — equipment / camera

> 基于 TECH_ANALYSIS.md + 现有 CameraManagePage.py | 2026-06-11
> 页面类型: 监控看板卡片网格（非标准 el-table CRUD）

## 自动化目标

覆盖摄像头管理页面的统计卡片校验、监控卡片网格展示、分页和搜索筛选。视频预览弹窗因跨域问题暂不自动化。

## 推荐策略

- 脚本层级: CameraManagePage → conftest.py → test_camera_management.py
- 断言层级: 统计卡片数值/摄像头网格数量/元素可见性
- 数据策略: 统计卡片值非空校验为主，不依赖具体数值
- 清理策略: 无写入操作，无需清理

## 覆盖矩阵

| 用例编号 | 标题 | 优先级 | 自动化 | 理由 |
|----------|------|--------|--------|------|
| CM-01 | 页面正常加载 | P0 | ✅ | navigate + 统计卡片出现 + 监控网格出现 |
| CM-02 | 统计卡片数据校验 | P0 | ✅ | 摄像头总数/在线/离线/故障 四卡片数值≥0且逻辑一致 |
| CM-03 | 摄像头网格展示 | P0 | ✅ | monitor-cell 数量>0，每格含标题/画面/IP |
| CM-04 | 关键词搜索 | P1 | ✅ | 输入关键词，网格更新 |
| CM-05 | 在线状态筛选 | P1 | ✅ | 筛选"在线"，结果均为在线 |
| CM-06 | 故障状态筛选 | P1 | 🔄 | 筛选"故障"，结果均为故障 |
| CM-07 | 分页操作 | P1 | ✅ | 翻页后monitor-cell变化 |
| CM-08 | 摄像头详情弹窗 | P2 | ❌ | video元素可能跨域 |
| CM-09 | 视频实时预览 | P2 | ❌ | 跨域+性能不稳定 |

## PageObject 拆分

```
CameraManagePage  ← 统计卡片 + 搜索筛选 + 监控网格 + 分页
(CameraDialog)    ← 弹窗（详情/编辑/预览），部分标记 @skip
```

## 公共组件复用

| 方法 | 来源 | 复用状态 |
|------|------|----------|
| navigate_to() | BasePage | ✅ |
| wait_page_ready() | BasePage | ✅ |
| click_element() | BasePage (3级降级) | ✅ |
| get_stat_values() | CameraManagePage (自定义) | 特有方法 |
| get_monitor_cells() | CameraManagePage (自定义) | 特有方法 |

## ROI 分析

| 指标 | 值 |
|------|-----|
| 已投入开发时间 | ~2 小时 |
| 维护成本 | ~0.3 小时/月 |
| 手工执行时间 | 8 分钟/次 |
| 执行频率 | 每次部署 + 每周回归 |
| 自动化率(预估) | 67% (6/9) |

## 遗留技术债

1. **视频预览弹窗**: video 跨域不可自动化
2. **仪表盘卡片混排**: 8张stat-card属不同业务域，定位器按label区分
3. **monitor-cell 动态数量**: 卡片网格随筛选动态变化

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 | next_phase: Phase 4 | next_agent: automation-agent -->
