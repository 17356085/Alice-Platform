# PAGE_CONTEXT — system-management / monitor-management

> 最后诊断：2026-06-12

## 页面信息

| 属性 | 值 |
| --- | --- |
| 页面名称 | 系统监控 |
| 路由 | `#/system/monitor` |
| 所属模块 | 系统管理 |
| 页面类型 | 监控仪表盘（指标卡片 + 图表） |
| Page Object | [MonitorManagePage.py](ZJSN_Test-master526/page/system_page/MonitorManagePage.py) (~150行) |
| 测试脚本 | [test_monitor_management.py](ZJSN_Test-master526/script/system/test_monitor_management.py) (4 cases) |
| 测试结果 | 2P/0F/2S standalone; 0P/2F/2S full-regression |
| 自动化状态 | ⚠️ 环境依赖严重，全量回归页面不渲染 |

## 页面定位

系统监控页面是**运维仪表盘**，展示系统运行的关键指标（如服务状态、内存使用、请求统计等）。页面内容依赖后端监控数据推送。

## 页面关键功能

### 指标卡片区

| 指标 | 类型 | 说明 |
| --- | :---: | --- |
| 服务状态 | 状态标签 | 运行中/停止 |
| 内存使用 | 进度条/数值 | JVM/系统内存 |
| 请求统计 | 数值 | QPS/总请求数 |
| 在线用户 | 数值 | 当前在线数 |

### 图表区

| 图表 | 类型 | 说明 |
| --- | :---: | --- |
| 请求趋势 | 折线图 | 时间轴请求量 |
| 响应时间 | 柱状图 | 各接口耗时 |

### 操作区

| 控件 | 类型 | 说明 |
| --- | :---: | --- |
| 刷新按钮 | `<el-button>` | 手动刷新监控数据 |

## 关键定位策略

| 操作 | 方法 | 策略 |
| --- | --- | --- |
| 页面加载检测 | `is_page_loaded()` | 检测指标卡片/图表容器是否渲染 |
| 获取指标值 | `get_metric_values()` | 查找 metric-card 元素 |
| 点击刷新 | `click_refresh()` | 查找刷新按钮 |

## 已知坑位

1. **页面内容空白**：全量回归时页面不渲染任何指标卡片/图表。**怀疑原因**：
   - 监控数据依赖后端 WebSocket/SSE 推送，测试环境可能未配置
   - 监控服务（如 Spring Boot Actuator）可能未启动
   - 单独跑时 2/4 通过（页面加载 + 基本元素检测），全量回归 0/4（页面完全空白）
2. **需要环境依赖**：不同于 CRUD 页面，监控仪表盘是数据驱动的可视化页面
3. **刷新按钮可能不存在**：页面空白时无刷新按钮可点击

## 测试建议

- 单独运行（非全量回归）时页面基本可加载
- 优先验证页面加载（test_01）+ 基本元素存在
- 指标数值类断言设宽松阈值（指标值可能为0）
- 考虑添加 `pytest.mark.skipif` 环境检测

## 与其他页面的关系

- 监控的 API 接口 → 来自 [接口管理](api-management/PAGE_CONTEXT.md) 中的 Swagger 定义
- 系统运行数据 → 独立于业务页面，属运维层
