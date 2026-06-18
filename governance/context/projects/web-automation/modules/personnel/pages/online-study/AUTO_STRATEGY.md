```markdown
# AUTO_STRATEGY.md

> **模块**: personnel | **页面**: online-study | **策略制定日期**: 2026-06-18  
> **参考来源**: PAGE_CONTEXT.md (示例), TECH_ANALYSIS.md (推断), 通用 Element Plus 实践  

---

## 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|---------|------|--------|----------|------|
| TC-001 | 页面正常加载（标题、面包屑、表格显示） | P0 | ✅ | 基础冒烟，定位器稳定 |
| TC-002 | 搜索: 按课程名称精确搜索 | P0 | ✅ | 核心功能，输入框有固定 id |
| TC-003 | 搜索: 按课程分类下拉筛选 | P1 | ✅ | 下拉选择定位稳定，但需处理动态选项 |
| TC-004 | 搜索: 按状态下拉筛选 (上架/下架) | P1 | ✅ | 同上 |
| TC-005 | 搜索: 按创建日期范围筛选 | P1 | ✅ | date-picker 需交互，但 Element Plus 定位器稳定 |
| TC-006 | 搜索: 组合多条件搜索 | P0 | ✅ | P0 级组合场景 |
| TC-007 | 重置搜索条件 | P0 | ✅ | 重置后表单清空、表格刷新 |
| TC-008 | 新建课程（填写所有必填项后保存） | P0 | ✅ | 弹窗表单操作，P0核心 |
| TC-009 | 新建课程：必填项为空时保存失败 | P1 | ✅ | 表单校验，自动化可验证错误提示 |
| TC-010 | 编辑课程（修改课程名称后保存） | P0 | ✅ | 与新建共用弹窗，需区分 |
| TC-011 | 删除课程（取消删除） | P1 | ✅ | 确认弹窗可定位 |
| TC-012 | 删除课程（确认删除） | P0 | ✅ | 核心数据操作 |
| TC-013 | 上架/下架课程（开关切换） | P0 | ✅ | 表格内开关操作 |
| TC-014 | 分页：切换每页条数 | P1 | ✅ | el-pagination 定位稳定 |
| TC-015 | 分页：点击下一页/上一页 | P1 | ✅ | 同上 |
| TC-016 | 分页：跳转到指定页码（若有输入框） | P2 | ❌ | 非通用功能，优先级低，手动验证更高效 |
| TC-017 | 空数据状态显示 | P1 | ✅ | 可通过清空表格数据触发，但需数据准备 |
| TC-018 | 查看课程进度（导航到进度页） | P2 | ❌ | 属于跨页面跳转，建议手动探索 |
| TC-019 | 左侧分类树点击筛选 | P1 | ✅ | 树定位稳定，但需处理异步加载 |
| TC-020 | 课程名称链接点击跳转详情 | P2 | ❌ | 链接跳转属于页面导航，手动测试更合理 |

### 风险标注
- **TC-003/TC-004/TC-008/TC-010**: 下拉选项、标签颜色等依赖接口返回数据，需在测试数据准备阶段保障。若后端接口不稳定，定位器风险中。
- **TC-019**: 左侧分类树可能采用异步加载，需 wait 子树节点出现。

---

## 2. PageObject 拆分方案

| Page 类 | 职责 | 对应页面区域 | 备注 |
|---------|------|-------------|------|
| `OnlineStudyPage` | 在线学习主页面，包含搜索区、表格、分页、左侧树、顶部操作按钮 | 搜索/表格/分页/左侧树/新建按钮 | 继承 `BasePage` |
| `CourseDialog` | 新建/编辑课程弹窗，包含表单字段、保存/取消按钮 | 弹窗区域 | 独立类，构造函数接收 `dialog` 根元素定位器或页面对象（推荐传入 `OnlineStudyPage` 实例后定位弹窗） |

### 拆分依据
- 一个页面一个主 Page 类 → `OnlineStudyPage`
- 复杂弹窗独立 → `CourseDialog` 便于封装表单操作方法，与主页面解耦
- 共用的元素（如加载状态、空状态）在 `OnlineStudyPage` 中定义，`CourseDialog` 可调用 `page.wait_loading_disappear()` 等

---

## 3. 公共组件复用分析

### 复用的 BasePage / ElementPlusHelper 方法

| 页面操作 | BasePage 方法 | ElementPlusHelper 扩展 | 备注 |
|---------|--------------|-----------------------|------|
| 输入文本 (el-input) | `input_text(locator, text)` | 无（使用标准 CSS 定位+clear） | 直接调用 BasePage |
| 单击按钮 (el-button) | `click(locator)` | 无 | |
| 选择下拉 (el-select) | `select_option(locator, option_text)` | 需要封装：点击 el-select → 点击 el-option | 可封装到 ElementPlusHelper 或 Page 内部 |
| 选择日期范围 (el-date-picker) | `select_date_range(locator, start, end)` | 需要封装：点击输入框 → 设置 start → 设置 end | |
| 弹窗等待 | `wait_until_visible(locator)` | 无 | |
| 表格行操作 | `click_table_action(locator, row_index, action_text)` | 可封装到 helper | 需定位表格行内按钮 |
| 分页切换 | `select_page_size(locator, size)` | 封装到 ElementPlusHelper | |
| 上传图片 (el-upload) | `upload_file(locator, file_path)` | 需处理隐藏 input | 可复用 BasePage 的 `input_text` 注入 file path |
| 树节点展开/选择 (el-tree) | `click(locator_of_node)` | 封装 `expand_tree_node` | 需按文本或索引定位 |

### 需要扩展 ElementPlusHelper 的方法
- `el_select_option(locator, option_text)`
- `el_date_picker_range(locator, start_date, end_date)`
- `el_pagination_set_size(locator, size)`
- `el_switch_toggle(locator)` — 开关组件可能需额外操作
- `el_upload_file(locator, file_path)`

---

## 4. 等待策略建议

### 页面特有的异步行为

| 操作 | 异步行为 | 建议等待策略 |
|------|---------|-------------|
| 页面加载 | 表格数据异步加载，v-loading 显示 | `wait_loading_disappear(locator_of_table)` — 通用 BasePage 方法 |
| 搜索/重置 | 搜索后表格刷新，loading 出现 | 同上 |
| 新建/编辑保存 | 保存后弹窗关闭，表格刷新 | 等待弹窗消失 (`wait_until_invisible(dialog)`)，再等待表格 loading |
| 删除确认 | 确认后表格刷新 | 等待确认弹窗消失 + 表格 loading |
| 切换每页条数 | 表格重新加载 | 等待 loading + 分页信息更新 |
| 选择下拉选项 | 下拉列表出现 | 使用 `visibility_of_element_located` 等待 el-option 可见 |
| 日期选择器 | 日期面板弹出 | 等待日期面板可见（建议使用显式等待） |
| 左侧分类树加载 | 树节点可能异步加载 | 等待 `el-tree-node__label` 出现 |

### 建议的等待封装
```python
# 在 OnlineStudyPage 中
def wait_table_loaded(self):
    self.wait_loading_disappear(self.table_locator)

def wait_dialog_closed(self):
    self.wait_until_invisible(self.dialog_locator)

def wait_tree_loaded(self):
    self.wait_until_present(self.tree_locator)
    # 可进一步等待第一个节点出现
```

---

## 5. ROI 分析

### 估算参数

| 项目 | 数值 | 说明 |
|------|------|------|
| 预估自动化开发时间 | **16 小时** | 含 PageObject 编写（8h）+ 公共方法扩展（3h）+ 测试用例脚本（5h） |
| 预估维护成本 | **2 小时/月** | 定位器随 UI 变更调整、数据准备脚本维护 |
| 手工执行全部 P0+P1 用例 | **20 分钟/次** | 包含登录、点击、验证等步骤，平均 15 个 P0+P1 用例 |
| 手工执行频率 | **每周 3 次** (回归) + **每次上线前 1 次** | 假设每月 4 次上线 + 12 次周回归 = 16 次/月 |
| 自动化执行时间 | **5 分钟/次** | 含环境准备、执行、报告生成 |
| 自动化执行频率 | 同手工，16 次/月 | |

### ROI 计算（3 个月周期）

- **手工总耗时**: (20 min + 5 min 环境准备) × 16 次/月 × 3 月 = 25 min × 48 = **1200 分钟 = 20 小时**
- **自动化总耗时开发**: 16 小时 + 每月维护 2h × 3 = 16 + 6 = **22 小时**
- **自动化执行总耗时**: 5 min × 48 = 240 min = **4 小时**
- **自动化净收益**: 手动耗时 - 自动化耗时 = 20 - (22 + 4) = **-6 小时**（前 3 月投入略高）

> **注**: 3 个月后维护成本稳定，累计收益逐渐转正。  
> **第 6 个月收益**: 手动 40h - (16 开发 + 12 维护 + 8 执行) = 40 - 36 = **+4 小时**  
> **第 12 个月收益**: 手动 80h - (16 + 24 + 16) = 80 - 56 = **+24 小时**

### 结论
- **短周期（<3 月）**: ROI 为负，但自动化节省了人工重复劳动，且提升回归信心。
- **长周期（>6 月）**: ROI 显著为正，强烈建议自动化 P0/P1 用例。
- **一次性操作（如批量导入模板下载）**: 不自动化。
- **高风险用例（如删除数据后的恢复）**: 需配合数据清理 Fixture，可适当降级为 P2，暂不自动化。

> 最终建议：投入 16 小时建立基础自动化框架，优先覆盖 P0 用例（TC-001, TC-002, TC-006, TC-007, TC-008, TC-010, TC-012, TC-013）。P1 用例在后续迭代中按需补充。
```