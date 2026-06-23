# TEST_DESIGN — lab（化验室取样，6页面）

> 基于 32 条用例全量回归结果 | 2026-06-12

## 一、测试范围

| 页面 | 路由 | PO | 用例数 | 策略 |
| --- | --- | --- | :---: | --- |
| 气体分析报告单 | `#/lab/gas/report` | GasAnalysisReportPage | 10 | 展示+筛选+位置切换+新增+统计+导出 |
| 气体分析对比 | `#/lab/gas/compare` | LabComparePage(sub=gas) | 4 | 页面加载+日期搜索+双位置查询+同位置守卫 |
| 气体分析设计指标 | `#/lab/gas/indicator` | LabIndicatorPage(sub=gas) | 4 | 页面展示+表头校验+行数验证 |
| 水质分析报告单 | `#/lab/water/report` | WaterAnalysisReportPage | 5 | 页面加载+按钮+位置切换+日期搜索+新增弹窗 |
| 水质分析对比 | `#/lab/water/compare` | LabComparePage(sub=water) | 4 | 页面加载+日期搜索+双位置查询+同位置守卫 |
| 水质分析设计指标 | `#/lab/water/indicator` | LabIndicatorPage(sub=water) | 4 | 页面展示+表头校验+行数验证 |
| **合计** | | **3 类 PO** | **31** | |

## 二、测试分层

| 层级 | 内容 | 用例数 | 结果 |
| :---: | --- | :---: | :---: |
| **L1 — 冒烟** | 页面加载 + 元素检测 | 12 | ✅ |
| **L2 — 功能** | 搜索/筛选/位置切换/新增/导出 | 17 | ✅ |
| **L3 — 边界** | 空状态/同位置守卫 | 2 | ✅ |
| **L4 — 异常** | 网络/接口错误 | 0 | ⚪ 未覆盖 |

## 三、核心设计策略

### gas/water 对称设计
```python
gas_compare = LabComparePage(driver, sub='gas')     # 气体
water_compare = LabComparePage(driver, sub='water') # 水质
```

### 表格检测降级（非标准表格）
```python
rows = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr, .report-table tbody tr')
```

### JS 传参规范
所有 `execute_script` 中的动态文本统一用 `arguments[0]`，禁止字符串拼接。

## 四、数据策略

| 策略 | 说明 |
| --- | --- |
| 报告单数据依赖已有 | 不创建新报告单（需真实业务数据），仅验证弹窗可打开 |
| 指标数据只读 | 不执行写操作，仅验证展示 |
| 对比页先查后验 | 先执行查询操作，再验证表格加载 |
| 冒烟优先 | L1 覆盖全部 6 页面，L2 聚焦可交互功能 |
