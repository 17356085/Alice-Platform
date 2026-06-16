# TECH_ANALYSIS — equipment / camera

> 从现有 CameraManagePage.py 代码提取定位器 | 2026-06-11
> 页面类型: 监控看板卡片网格（非标准el-table CRUD）

## Element Plus 组件识别

| 组件 | 用途 | 定位特点 |
|------|------|----------|
| stat-card (自定义) | 8张统计卡片 | 自定义 class stat-value/stat-label，非BEM |
| monitor-cell (自定义) | 摄像头卡片网格 | 自定义布局，含标题/画面/IP/状态/按钮 |
| el-pagination | 分页器 | 标准 Element Plus 分页 |
| el-overlay-dialog | 弹窗（详情/编辑/预览） | 模态框，非 el-dialog class |
| search-item (自定义) | 搜索筛选区 | 自定义布局，含 input/dropdown/分段切换 |

## 定位器设计表

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 统计卡片容器 | CSS | `.stat-card` | A | 页面唯一 |
| 摄像头总数 | XPATH | `//div[contains(@class,"stat-card")][.//div[contains(@class,"stat-label") and normalize-space(.)="摄像头总数"]]//div[contains(@class,"stat-value")]` | A | |
| 在线数 | XPATH | `//div[contains(@class,"stat-card")][.//div[contains(@class,"stat-label") and normalize-space(.)="在线"]]//div[contains(@class,"stat-value")]` | A | |
| 离线数 | XPATH | `//div[contains(@class,"stat-card")][.//div[contains(@class,"stat-label") and normalize-space(.)="离线"]]//div[contains(@class,"stat-value")]` | A | |
| 故障数 | XPATH | `//div[contains(@class,"stat-card")][.//div[contains(@class,"stat-label") and normalize-space(.)="故障"]]//div[contains(@class,"stat-value")]` | A | |
| 摄像头网格单元 | CSS | `.monitor-cell` | A | 卡片网格 |
| 监控画面区域 | CSS | `.monitor-screen` | B | 视频/截图区域 |
| 摄像头名称 | CSS | `.cell-title` | B | 每个monitor-cell内的标题 |
| 摄像头IP | CSS | `.cell-ip` | B | |
| 摄像头位置 | CSS | `.cell-location` | B | |
| 操作按钮区 | CSS | `.cell-actions` | B | |
| 编辑按钮 | XPATH | `.//button[contains(.,'编辑')]` | B | 行内按钮 |
| 弹窗 | CSS | `.el-overlay-dialog` | B | 非标准 el-dialog |
| 弹窗标题 | CSS | `.el-overlay-dialog .el-dialog__title` | B | |
| 弹窗确认 | CSS | `.el-overlay-dialog .el-button--primary` | B | |
| 分页器 | CSS | `.el-pagination` | A | |

## 异步等待策略

| 场景 | 等待条件 | 实现 |
|------|----------|------|
| 页面加载 | monitor-cell 出现 | `WebDriverWait(driver, 15).until(EC.presence_of_element_located(MONITOR_CELL))` |
| 卡片网格刷新 | stat-card 出现 | `presence_of_all_elements_located(STAT_CARD)` |
| 弹窗打开 | el-overlay-dialog visible | `visibility_of_element_located(DIALOG)` |
| 弹窗关闭 | dialog invisible | `invisibility_of_element_located(DIALOG)` |

## 已知技术难点

| 问题 | 影响 | 处理 |
|------|------|------|
| 非标准 el-table 布局 | 无法复用 BasePage 表格方法 | 自定义 get_monitor_cells() / get_stat_values() |
| 视频预览弹窗 | video 元素可能跨域 | 暂不自动化视频播放验证 |
| 仪表盘统计卡片与摄像头卡片混排 | 8张.card位于同一容器 | 按 stat-label 文字区分，索引不可靠 |

## 代码映射

- Page Object: `page/equipment_page/CameraManagePage.py`
- 测试脚本: `script/equipment/test_camera_management.py`
- conftest: `script/equipment/conftest.py`

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 | next_phase: Phase 3.5/4 | next_agent: automation-agent -->
