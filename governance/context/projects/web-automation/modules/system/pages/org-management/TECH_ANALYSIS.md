# TECH_ANALYSIS — system / org-management

## 分析对象
- 模块：system
- 页面：组织管理
- 自动化目标：覆盖搜索/CRUD/树操作的 Page Object (OrgManagePage)

## 技术要点

### Element Plus 组件识别
| 组件类型 | 用途 | 特殊性 |
|----------|------|--------|
| el-input | 组织名称搜索框 | placeholder="组织名称" |
| el-select (×2) | 组织类型+状态下拉 | 选项异步加载 |
| el-table (tree) | 树形组织表格 | el-table__row + 树展开/折叠 |
| el-dialog | 新增/编辑弹窗 | 含6个表单字段 |
| el-button | 搜索/重置/新增/导出/查看/编辑/删除 | 通过文字区分 |
| el-pagination | 分页器 | |

### 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 组织名称搜索框 | XPATH | `//input[contains(@placeholder,"组织名称")]` | A | placeholder稳定 |
| 搜索按钮 | XPATH | `//button[.//span[normalize-space(.)="搜索"]]` | A | 文字固定 |
| 新增按钮 | XPATH | `//button[.//span[normalize-space(.)="新增"]]` | A | 文字固定 |
| 表格行 | XPATH | `//tr[contains(@class,"el-table__row")]` | B | 行索引动态 |
| 第1行编辑 | XPATH | `(//tr[contains(@class,"el-table__row")])[1]//td[last()]//button[2]` | B | 索引参数化 |
| 弹窗 | CSS | `.el-dialog:not([style*="display: none"])` | B | 排除隐藏 |
| 确认弹窗 | CSS | `.el-message-box` | A | |

### 异步等待策略
| 场景 | 等待条件 | 代码 |
|------|----------|------|
| 页面加载 | 表格出现 | `wait.until(EC.presence_of_element_located(TABLE))` |
| 搜索完成 | loading消失 | `wait.until(EC.invisibility_of_element_located(LOADING))` |
| 弹窗打开 | 弹窗可见 | `wait.until(EC.visibility_of_element_located(DIALOG))` |
| 树展开 | 子节点出现 | `wait.until(EC.presence_of_element_located(CHILD_ROWS))` |

## 实现建议
- Page Object: OrgManagePage 继承 BasePage，复用搜索/表格/分页方法
- Fixture: module scope driver，通过 JS hash 导航到 `#/system/dept`
- 清理策略: teardown 中按名称前缀删除测试部门

## 风险与限制
- 树形结构: el-table tree-props，子节点懒加载需额外等待
- 树节点操作: 展开/折叠需定位 expand-icon
- 行内新增: 每行"新增"按钮用于添加子部门，与工具栏"新增"不同
