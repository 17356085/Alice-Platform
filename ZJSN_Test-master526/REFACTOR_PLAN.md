# REFACTOR PLAN — ZJSN 自动化测试框架重构计划

> 版本：1.0 | 日期：2026-06-04 | 评审人：架构评审

---

## 评分概览

| 维度 | 得分 | 说明 |
|------|------|------|
| 目录结构 | 7/10 | 分层清晰，存在 tools/ 混入和 debug_output/ 污染 |
| PageObject 设计 | 7/10 | 基类完善，Locator 与逻辑未分离，部分类过大 |
| pytest 设计 | 7/10 | Fixture 分层合理，scope 策略正确，缺少参数化 |
| Selenium 设计 | 8/10 | 等待策略完善，多级降级点击是亮点，但含 time.sleep |
| 测试数据管理 | 4/10 | 无独立数据层，硬编码散落在用例中 |
| 报告体系 | 5/10 | Allure 接入但注解缺失，Excel 报告手动维护 |
| CI/CD 适配 | 3/10 | 无 Jenkinsfile，headless 写死 False，密码明文 |
| AI 协同能力 | 6/10 | 有 Prompt 目录，目录结构对 AI 友好 |

---

## 成熟度评估

**当前阶段：Level 2 — 团队内部项目**（兼具 Level 3 部分特征）

### 当前阶段特征

- 有清晰的分层架构（base / page / script）
- BasePage 封装了 Vue/Element Plus 异步等待，技术深度达到中等水平
- Fixture 体系完整（module/function/session 三级）
- 缺少 CI/CD 集成，依赖个人手动执行
- 测试数据无独立管理，硬编码散落
- 凭证明文存储，无法安全地接入流水线

### 升级路径

```
Level 2（当前） → Level 3（3个月）→ Level 4（6个月+）
     ↓                  ↓                    ↓
 团队可运行        Jenkins 流水线        测试平台 + 智能化
 手动触发          自动触发              质量门禁
 Excel 报告        Allure + 通知         覆盖率度量
```

### 关键能力缺失

1. 凭证管理（密码明文）→ 阻塞 CI/CD 接入
2. 测试数据独立管理 → 制约用例可靠性
3. Allure 业务注解 → 报告无法被测试管理者直接使用
4. 并行执行 → 测试时长无法压缩
5. 接口 Mock → E2E 依赖真实后端，不稳定

---

## 企业级对标分析

### 与腾讯/字节/阿里/美团的差距

| 能力点 | 企业级标准 | 当前项目 | 差距 |
|--------|-----------|---------|------|
| 凭证管理 | 全面使用密钥管理服务 | 明文写在 config.py | 高风险 |
| 数据驱动 | YAML/JSON + 数据工厂 + DB | 硬编码 + 少量 Excel | 明显差距 |
| 并行执行 | 分布式多机并行 | pytest-xdist 未启用 | 中等差距 |
| 测试报告 | 多维度看板 + 自动推送 | Allure 无注解 | 明显差距 |
| 稳定性 | 失败重试 + 截图 + 录屏 | 失败截图，无重试 | 中等差距 |
| 环境管理 | 多套环境动态切换 | 单一 URL 硬编码 | 明显差距 |
| CI/CD | 全自动流水线 + 质量门禁 | 无 | 明显差距 |
| 用例维护 | 测试管理平台（Allure EE/TAPD）| 文件散落 | 较大差距 |

---

## P0 — 必须改（安全 + CI 接入前提）

### P0-1：凭证从代码中移除

**问题**：`config.py:4-6` 明文存储 URL 和密码，提交到 Git 即泄露。

**方案**：
1. 创建 `.env` 文件（加入 `.gitignore`）
2. 创建 `.env.example` 作为模板提交
3. `config.py` 改为读取环境变量，保留默认值用于本地开发

```
# .env（不提交）
BASE_URL=http://8.136.215.171:8081/
DEFAULT_USERNAME=admin
DEFAULT_PASSWORD=***

# config.py 改为：
import os
from dotenv import load_dotenv
load_dotenv()
BASE_URL = os.getenv("BASE_URL", "http://localhost:8081/")
DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "admin")
DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD", "")
```

**影响文件**：`config.py`，`.env`（新增），`.env.example`（新增）

---

### P0-2：添加 .gitignore

**问题**：`artifacts/`（大量 PNG/HTML）、`allure-results/`（大量 JSON）、
`__pycache__/`、`.env` 当前无 `.gitignore` 保护。

**方案**：在项目根目录创建 `.gitignore`：

```
# 自动生成产物
artifacts/
allure-results/
debug_output/
downloads/
__pycache__/
*.pyc
.pytest_cache/

# 敏感信息
.env
*.env.local

# IDE
.vscode/
.idea/
```

---

### P0-3：headless 模式配置化（CI 必需）

**问题**：`config.py:12` `"headless": False` 硬编码，CI 环境无显示器会报错。

**方案**：通过环境变量控制：

```python
# config.py
BROWSER_CONFIG = {
    "headless": os.getenv("HEADLESS", "false").lower() == "true",
    ...
}
```

Jenkins Pipeline 中设置 `HEADLESS=true`。

---

### P0-4：消除根 conftest.py 的 Fixture 名称硬编码

**问题**：`conftest.py:36-50` `_DRIVER_FIXTURE_NAMES` 是一个手动维护的字符串列表，
每新增 Page Object Fixture 都需手动更新，极易遗漏，导致失败时无法截图。

**方案**：改为自动发现——通过检测 fixture 值是否有 `driver` 属性或 `save_screenshot` 方法，
无需维护名单。

```python
def _resolve_driver_from_item(item):
    for name in item.fixturenames:
        try:
            value = item.funcargs.get(name)
        except Exception:
            continue
        if value is None:
            continue
        if hasattr(value, "driver") and hasattr(value.driver, "save_screenshot"):
            return value.driver
        if hasattr(value, "save_screenshot"):
            return value
    return None
```

---

## P1 — 建议改（稳定性 + 可维护性）

### P1-1：消除 time.sleep 硬编码

**问题**：整个框架中存在大量 `time.sleep(0.5)`、`time.sleep(1)`、`time.sleep(3)`，
包括 `conftest.py` 的 function fixture 中 `time.sleep(5)` 等，这是不稳定的根因。

**重灾区**：
- `script/sales/conftest.py:172,184,192` — function fixture 中的 sleep
- `base/base_page.py:254,384,417,651` — 操作方法内的 sleep
- `script/sales/conftest.py:219` — `time.sleep(1)` 无条件等待

**方案**：用显式等待替代：
- `time.sleep(N)` 等待数据加载 → `WebDriverWait` 等待表格行出现
- `time.sleep(0.2)` 等待 v-model 绑定 → 可保留，但统一用 `TIMEOUT_CONFIG["micro_wait"]`
- `time.sleep(5)` 等待首次渲染 → 等待特定元素出现

---

### P1-2：sales conftest.py function fixture 过重

**问题**：`contract_page` fixture（`script/sales/conftest.py:149-197`）共 49 行，
包含多层重试、冷启动预热逻辑，违反 fixture 轻量原则，且使用了大量 `time.sleep`。

**方案**：
- fixture 只负责构造 Page Object + 等待页面稳定
- 冷启动预热迁移到 `session` 级 fixture（只做一次）
- 去除 `row_count == 0` 的分支等待，改为 `wait_table_ready()`

---

### P1-3：测试数据外置

**问题**：测试用例中大量硬编码数据（合同编号、日期、关键词等），
如 `"HT20260527"`、`"2026-05-01"` 等直接写在测试代码中。

**方案**：
1. 创建 `data/fixtures/` 目录存放 YAML/JSON 数据文件
2. 定义数据工厂函数生成动态数据（带时间戳避免冲突）
3. 用 `@pytest.mark.parametrize` + 数据文件实现数据驱动

```yaml
# data/fixtures/sales_contract.yaml
search_cases:
  - name: "精确搜索合同编号"
    contract_no: "HT20260527"
    expect_count_gte: 1
  - name: "空条件搜索"
    contract_no: ""
    expect_count_gte: 0
```

---

### P1-4：Page Object 文件过大

**问题**：部分 Page 类（如 `ContractPage.py` 约 973 行）过大，
将 Locator 定义、业务操作、等待逻辑混合，修改时影响范围不清晰。

**方案**：将 Locator 提取到独立文件：

```
page/
├── locators/
│   ├── contract_locators.py
│   ├── user_locators.py
│   └── ...
└── sales_page/
    ├── ContractPage.py    # 只含操作方法
    └── ...
```

---

### P1-5：browser_driver_edge.py 孤立文件

**问题**：`base/browser_driver_edge.py` 存在但未被任何 conftest.py 引用，
是一个未整合的代码孤岛，增加维护负担。

**方案**：
- 如需 Edge 支持，将其整合到 `browser_driver.py`，通过 `BROWSER` 环境变量切换
- 如不需要，直接删除

---

### P1-6：tools/ 目录定位问题

**问题**：`tools/` 混杂了 `generate_*.py`（报告工具）、`insert_*_data.py`（造数工具）、
`debug_*.py`（调试脚本），这些脚本不属于自动化框架核心，但和核心代码平级。

**方案**：

```
scripts/           # 运维脚本（重命名，与 script/ 区分）
├── generate/      # 报告生成
├── seed/          # 测试数据造数
└── debug/         # 调试工具
```

或移到项目根目录的 `tools/` 外层，明确告知"这不是测试代码"。

---

### P1-7：补充失败重试机制

**问题**：E2E 测试天然不稳定，当前无失败自动重试，一次网络抖动会导致用例失败计入统计。

**方案**：引入 `pytest-rerunfailures`：

```ini
# pytest.ini
addopts = -v -s --tb=short --reruns 2 --reruns-delay 1
```

```
pip install pytest-rerunfailures
```

对 `@pytest.mark.flaky` 单独标记已知不稳定用例，与正常重试区分。

---

### P1-8：Allure 注解补全

**问题**：用例已产生 Allure 原始数据，但缺少 `@allure.epic/feature/story/severity` 注解，
报告无法按业务维度聚合，测试管理者无法直接使用。

**方案**：在每个 test_*.py 顶部添加模块级注解，用例内添加 `with allure.step()`。

优先级：smoke 用例先补，然后按模块补全。

---

### P1-9：pytest.ini addopts 补全

**问题**：当前 `pytest.ini` 缺少：
- `--alluredir=allure-results`（每次需手动指定）
- `--reruns`（稳定性）
- `-p no:warnings` 或 filterwarnings 不够完整

**方案**：

```ini
[pytest]
addopts = -v -s --tb=short --alluredir=allure-results --reruns 2 --reruns-delay 1
```

---

### P1-10：conftest.py 多套 driver fixture 别名混乱

**问题**：`script/system/conftest.py` 中存在：
- `driver_setup`
- `system_logged_in_driver`（是 `driver_setup` 的 yield 别名）
- `system_logged_in_browser`（是 `system_logged_in_driver` 的别名）

三个名字指向同一个对象，新成员难以判断该用哪个。

**方案**：统一保留 `driver_setup`，删除两个别名，
在 ARCHITECTURE 文档中说明命名规范。

---

## P2 — 未来优化（平台化方向）

### P2-1：多环境切换

通过 `ENV` 环境变量切换 `config/*.py` 配置集，支持 `dev/test/staging` 多环境：

```
config/
├── base.py      # 公共配置
├── dev.py       # 开发环境
├── test.py      # 测试环境
└── staging.py   # 预发环境
```

---

### P2-2：Jenkins Pipeline

创建标准 `Jenkinsfile`：

```groovy
pipeline {
  agent any
  environment {
    HEADLESS = "true"
    BASE_URL = credentials('zjsn-test-url')
    DEFAULT_PASSWORD = credentials('zjsn-test-password')
  }
  stages {
    stage('Install') { steps { sh 'pip install -r requirements.txt' } }
    stage('Smoke')   { steps { sh 'pytest -m smoke' } }
    stage('Report')  { steps { allure includeProperties: false, jdk: '', results: [[path: 'allure-results']] } }
  }
  post {
    always { archiveArtifacts artifacts: 'artifacts/**', allowEmptyArchive: true }
    failure { emailext to: 'team@example.com', subject: '测试失败通知' }
  }
}
```

---

### P2-3：pytest-xdist 并行化

当前 `pytest-xdist` 已安装但未启用，因 module 级 driver 需要独立浏览器实例。

**前提**：每个 module 的 `driver_setup` 已是独立浏览器，理论上可以并行。

**方案**：按文件分发（`-n auto --dist=loadfile`），避免同一文件内的用例在不同进程运行。

---

### P2-4：接口 Mock 层

UI 测试中涉及"验证搜索结果为空"等场景依赖真实数据，不稳定。

**方案**：引入 `pytest-httpserver` 或 `responses` 库，
对部分 API 请求进行拦截和 Mock，使特定测试场景与真实数据解耦。

---

### P2-5：测试覆盖率度量

当前无页面功能覆盖率统计，无法量化自动化覆盖程度。

**方案**：
1. 维护 `data/coverage_matrix.xlsx`（功能点 × 自动化用例对应关系）
2. 或接入测试管理平台（如 Allure TestOps、TAPD）
3. 在 Allure 报告中通过 epic/feature/story 层级展示覆盖率

---

### P2-6：AI 辅助用例生成

当前 `Prompt/` 目录有提示词模板，可进一步扩展：

1. 根据 DOM 快照自动生成 Locator 候选
2. 根据功能描述文档生成用例骨架
3. 失败截图 + HTML 自动分析根因

---

## 执行建议

建议按以下顺序推进：

```
Week 1: P0-1 + P0-2 + P0-3（凭证安全 + CI 前提条件）
Week 2: P0-4 + P1-7 + P1-9（稳定性基础）
Week 3: P1-8（Allure 注解，smoke 用例优先）
Month 2: P1-1 + P1-2 + P1-3（sleep 清除 + 数据外置）
Month 3: P1-4 + P1-5 + P1-6 + P1-10（代码质量）
Quarter 2: P2 全系列（平台化演进）
```

---

*维护说明：每个 P0/P1 完成后，在对应条目打勾，并记录完成日期*
