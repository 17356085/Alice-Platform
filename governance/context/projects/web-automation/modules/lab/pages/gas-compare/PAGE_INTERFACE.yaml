好的，收到任务。我将基于 **lab 模块** 的 **gas-compare 页面**，启动完整的页面分析流程。

根据系统规范，此过程将产出以下三个文件，并存放在 `pages/lab/gas-compare/` 目录下：
1.  `PAGE_CONTEXT.md` - 页面元素清单
2.  `PAGE_ELEMENT_POSITION.md` - 元素定位器设计
3.  `PAGE_INTERFACE.yaml` - 自动化接口定义（作为后处理步骤自动生成）

---

### 信息采集请求

为了进行精准分析，请提供以下任意一项或多项信息：

▶️ **选项一：页面截图（推荐）**
提供 **2-3** 张页面关键区域的截图：
1.  **整体页面**：展示页面的完整布局、顶部/左侧菜单、主内容区域。
2.  **核心操作区**：如果页面包含搜索/筛选区，请提供该区域的清晰截图。
3.  **表格/列表与操作**：如果页面包含数据表格，请提供表格区域（包含所有列标题）以及“操作”列的截图。

▶️ **选项二：关键区域HTML源码**
提供页面搜索区、表格区和主要弹窗的 HTML 片段。

▶️ **选项三：页面URL**
如果系统已部署且可访问，提供页面 URL，我可以尝试直接访问抓取。

```text
示例回复：
模块: lab，页面: gas-compare
截图：[请上传截图]
或
URL: http://your-domain/lab/gas-compare
或
HTML源码：[关键区域的HTML]
```

---

### 预期产出样例（基于假设的“气体对比”页面设计）

在收到您的输入前，我先根据页面名称“气体对比”及常见实验室系统特性，推测一个可能的结构作为分析基准。**请注意，以下内容仅为演示，实际产出将基于您提供的具体素材。**

#### 1. PAGE_CONTEXT.md 片段（页面结构分析）

| 区域 | 元素ID | 元素描述 | 控件类型 | 备注 |
|------|--------|----------|----------|------|
| **搜索区** | gas-type | 气体类型 | el-select | 支持多选，选项来源：`/api/gas-types` |
| **搜索区** | compare-type | 对比类型 | el-select | 选项: 标准气体对比, 气体组分对比 |
| **搜索区** | start-date | 开始日期 | el-date-picker | 绑定 `v-model="query.startDate"` |
| **搜索区** | end-date | 结束日期 | el-date-picker | 绑定 `v-model="query.endDate"` |
| **搜索区** | search-btn | 查询按钮 | el-button | 触发`handleSearch()` |
| **搜索区** | reset-btn | 重置按钮 | el-button | 触发`handleReset()` |
| **数据区** | table-results | 对比结果表格 | el-table | 展示气体对比分析数据 |
| **表格列** | col-gas-name | 气体名称 | 文本 |  |
| **表格列** | col-standard-value | 标准值 | 数字 | 可能带单位 |
| **表格列** | col-measured-value | 实测值 | 数字 | 可能带单位 |
| **表格列** | col-deviation | 偏差 | 数字 | 计算公式：`(实测值-标准值)/标准值 * 100%` |
| **操作列** | col-operation | 操作 | el-button | 包含“详情”和“导出”按钮 |
| **分页区** | pagination | 分页器 | el-pagination | 位于表格底部 |

#### 2. PAGE_ELEMENT_POSITION.md 片段（定位器设计）

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|--------|----------|--------|------------|----------|
| gas-type | B | `.gas-compare-search .el-select[prop='gasType']` | B | `//label[contains(text(),'气体类型')]/following-sibling::div//input` (C级) |
| compare-type | C | `//label[contains(text(),'对比类型')]/following-sibling::div//input` | C | 无稳定A/B级选择器，需向开发申请 `data-testid` |
| start-date | B | `.gas-compare-search .el-date-editor[prop='startDate']` | B |  |
| search-btn | A | `//button/span[text()='查询']` | C | `button:has(span:text('查询'))` (B级，若支持) |
| table-results | B | `.el-table[data-table-name='gas-compare-results']` | B | 或通过 `el-table` 的 `key` 属性定位 |

#### 3. PAGE_INTERFACE.yaml 片段（自动化接口定义）

```yaml
# 此文件由 page-analysis skill 自动生成，供 automation-agent 消费
page: gas-compare
module: lab
base_url: http://8.136.215.171:8081/lab/gas-compare
elements:
  gas_type_select:
    locator: "#gas-type-select"
    type: Select
    query_api: /api/gas-types
    options:
      - label: 氮气
        value: N2
      - label: 氧气
        value: O2
  search_button:
    locator: "//button/span[text()='查询']"
    type: Button
  comparison_table:
    locator: ".el-table[data-table-name='gas-compare-results']"
    type: Table
    columns:
      - name: 气体名称
        field: gasName
      - name: 标准值
        field: standardValue
      - name: 偏差
        field: deviation
    operation_columns:
      - name: 详情
        type: Button
        locator: ".el-button--detail"
      - name: 导出
        type: Button
        locator: ".el-button--export"
wait_strategies:
  default_wait: WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".gas-compare-page")))
  table_load: WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")))
```

**请您提供上述任一类型的素材，我将立即开始生成最终的页面分析文档。**