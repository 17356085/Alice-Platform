# Skill: module-modeling

## 目标
从现有代码和项目结构反推模块级上下文文档——无需 PRD 或产品说明。

## 输入
- 模块名（如 `warehouse`）
- PROJECT_CONTEXT.md（项目级背景）
- 代码目录：`ZJSN_Test-master526/page/<module>_page/`（Page Object 文件）
- 代码目录：`ZJSN_Test-master526/script/<module>/`（测试脚本文件）
- 治理目录：`governance/context/projects/web-automation/modules/<module>/`（已有治理文档）

## 输出
- MODULE_CONTEXT.md — 模块级上下文（基于真实代码结构）

## 规则
- **禁止编造页面名**：所有子页面必须从 `page/<module>_page/` 目录中实际存在的 Page Object 文件推导
- **禁止编造路由**：路由从 Page Object 的 URL 注释或类名推导，不确定则标注"待确认"
- 页面状态标记：✅ 已完成（有 PO + 有 test） / 🔄 有 PO 无 test / ⏳ 仅占位
- 不确定的页面/功能标注"待确认"
- 模块级风险必须基于代码实际情况（如：Page Object 无 base_page 继承、locator 使用 XPath 等）

## 执行步骤
1. **扫描 Page Object 目录**：`ls page/<module>_page/` 列出所有 `*Page.py` 文件
2. **扫描测试脚本目录**：`ls script/<module>/` 列出所有 `test_*.py` 和 `conftest.py`
3. **读取 2-3 个代表性 Page Object**：提取类名、URL 注释、核心方法
4. **读取 PROJECT_CONTEXT.md**：获取项目级背景
5. **生成 MODULE_CONTEXT.md**：基于真实代码结构，不编造

## 依赖
- templates/module-context.template.md
- workflows/sop-summary.md (§ Phase 0.5)

## 边界
- 本 Skill 不产出具体页面级文档（那是 requirement-analysis / page-analysis 的职责）
- 本 Skill 不产出测试用例（那是 testcase-design 的职责）
- 本 Skill 不做 DOM 观测（那是 page-observe 的职责）
- **禁止虚构不存在的页面或功能**

---

## Prompt 模板

### 从代码反推模块上下文

```text
你是一个测试工程师，需要为现有项目建立模块上下文文档。**该项目没有 PRD**，所有信息必须从代码中提取。

## 任务
为模块 `{{module}}` 生成 MODULE_CONTEXT.md。

## 步骤

### 第一步：扫描代码目录
使用工具扫描以下目录：
1. `ZJSN_Test-master526/page/{{module}}_page/` — Page Object 文件
2. `ZJSN_Test-master526/script/{{module}}/` — 测试脚本文件

### 第二步：读取代表性文件
- 读取 `PROJECT_CONTEXT.md`（路径：`governance/context/projects/web-automation/PROJECT_CONTEXT.md`）
- 读取 2-3 个 Page Object 文件，提取：类名、URL注释、核心方法名
- 读取 conftest.py 了解 fixture 配置

### 第三步：生成 MODULE_CONTEXT.md

输出到 `governance/context/projects/web-automation/modules/{{module}}/MODULE_CONTEXT.md`，包含：

1. **模块概述**：模块名、推测的路由前缀、推测的权限要求
2. **子页面清单**（从代码扫描结果填充，不编造）：

| 页面名称 | Page Object 类 | 推测路由 | PO状态 | 测试状态 | 备注 |
|---------|---------------|---------|--------|---------|------|
| {{从 PO 文件名推导}} | {{类名}} | {{从 URL 注释提取}} | ✅ | ✅/❌ | |

3. **页面关系图**：基于 PO 文件中的导航方法推断
4. **核心数据实体**：从 PO 代码中的表单字段/表格列推断
5. **模块级风险点**（基于代码实际情况）：
   - 如：PO 是否使用 base_page？定位器是 CSS 还是 XPath？
   - 如：conftest.py 是否配置了正确的登录/权限？
6. **自动化价值评估**：基于现有测试覆盖率

## 约束
- **禁止编造**：所有信息必须有代码依据
- 不确定的标注"待确认"
- 页面状态：✅ = PO+test 都存在，🔄 = 仅有 PO，⏳ = 仅有目录占位
```

---

## 检查清单

- [ ] 子页面清单全部来自代码扫描（非编造）
- [ ] 每个页面标注 PO 状态和测试状态
- [ ] 路由从 URL 注释提取（无注释则标注"待确认"）
- [ ] 模块风险基于代码实际情况
- [ ] 不确定信息标注"待确认"
- [ ] 页面状态使用统一图标 ✅/🔄/⏳

---

## 产出物
→ `MODULE_CONTEXT.md`，存放至 `governance/context/projects/web-automation/modules/<module>/`。
→ 输出格式参见 `templates/module-context.template.md`。
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | requirements | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->
