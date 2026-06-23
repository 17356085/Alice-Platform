# AUTO_STRATEGY — lab（化验室取样，6页面）

> 2026-06-12 | 3类统一PO + function级fixture + arguments[0]传参

## 一、自动化等级

| 页面 | 等级 | 策略 | 用例 |
| --- | :---: | --- | :---: |
| gas-analysis-report | **A** (完整) | 展示+筛选+位置切换+新增+导出 | 10 |
| gas-compare | **B** (核心) | 页面加载+日期搜索+双位置对比 | 4 |
| gas-indicator | **B** (核心) | 只读展示+表头校验 | 4 |
| water-report | **B** (核心) | 页面加载+位置切换+日期搜索+新增弹窗 | 5 |
| water-compare | **B** (核心) | 页面加载+日期搜索+双位置对比 | 4 |
| water-indicator | **B** (核心) | 只读展示+表头校验 | 4 |

## 二、架构决策

### 统一 PO（gas/water 对称）
- **LabIndicatorPage(sub)** — indicator 页 gas/water 共用
- **LabComparePage(sub)** — compare 页 gas/water 共用
- **WaterAnalysisReportPage** — report 页 water 独立

### Fixture 策略
```python
# ❌ 旧：session 级 — 跨文件竞态
@pytest.fixture(scope="session")
def gas_report_page(lab_logged_in_driver): ...

# ✅ 新：function 级 — 每次独立
@pytest.fixture(scope="function")
def gas_indicator_page(lab_logged_in_driver): ...
```

### JS 传参
```python
# ❌ 禁止：字符串拼接 → 语法错误
# ✅ 必须：arguments[0]
execute_script('...indexOf(arguments[0])...', text)
```

## 三、代码组织

```
page/lab_page/
├── GasAnalysisReportPage.py   # 气体报告单（成熟PO）
├── LabComparePage.py          # 对比页（gas/water共用）
├── LabIndicatorPage.py        # 指标页（gas/water共用）
└── WaterAnalysisReportPage.py # 水质报告单

script/lab/
├── conftest.py                # 7 fixtures
├── test_gas_analysis_report.py # 10 cases
├── test_compare.py            # 5 cases
├── test_gas_compare.py        # 2 cases
├── test_gas_indicator.py      # 2 cases
├── test_indicator.py          # 4 cases
├── test_water_compare.py      # 2 cases
├── test_water_indicator.py    # 2 cases
└── test_water_report.py       # 5 cases
```

## 四、运行策略

```bash
pytest script/lab/ -v                    # 全量回归
pytest script/lab/ -m smoke -v           # 快速冒烟
pytest script/lab/test_gas_analysis_report.py -v  # 单文件调试
```
