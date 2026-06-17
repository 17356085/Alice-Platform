# Skill: architecture/project-scanner

### 目标
扫描目标项目目录，分析文件结构、现有框架、依赖配置，生成结构化的 PROJECT_STRUCTURE.md。

### 输入
- 目标项目根目录路径
- 已有的 package.json / requirements.txt / pyproject.toml（如存在）
- 可选：项目类型提示（frontend / backend / fullstack）

### 输出
- `PROJECT_STRUCTURE.md`：包含目录树、文件类型统计、框架检测结果、入口文件识别

### 规则
- 必须基于实际文件扫描，不可推断不存在的内容
- 目录树使用 markdown 代码块展示（tree 命令格式）
- 检测项：框架类型（Vue/React/FastAPI/Express）、构建工具（Vite/Webpack）、语言（TS/JS/Python）
- 识别入口文件（main.ts / app.vue / main.py / index.ts）

### 依赖
- 无前置依赖

### 边界
- 不修改任何文件
- 不安装依赖
- 不运行代码
- 只分析目录结构和配置文件内容

### 检查清单
- [ ] 目录树完整（不遗漏子目录）
- [ ] 框架已识别（Vue/React/FastAPI/Express/其他）
- [ ] 构建工具已识别
- [ ] 语言版本已记录
- [ ] 入口文件已标注
- [ ] 输出格式符合 PROJECT_STRUCTURE.md 模板

### 产出物
- 文件路径: `{{module_dir}}/PROJECT_STRUCTURE.md`
- 格式: Markdown，含 `## 目录树` `## 技术检测` `## 入口文件` `## 关键文件清单`

---

## Prompt 模板

> 以下 Prompt 可直接复制到 AI 对话中使用。替换 `{{ }}` 占位符即可。

```text
你是一个资深全栈架构师。请扫描以下项目目录，生成结构化的项目结构分析文档。

## 项目根目录
{{PROJECT_ROOT}}

## 任务
1. 遍历项目根目录下的所有文件和子目录
2. 识别使用的框架（Vue 3 / React / FastAPI / Express / 其他）
3. 识别构建工具（Vite / Webpack / 无）
4. 识别语言和版本（TypeScript / JavaScript / Python）
5. 找到入口文件（main.ts / app.vue / main.py / index.ts）
6. 统计文件类型分布（.vue / .tsx / .py / .ts / .js 各多少个）

## 输出格式
```markdown
# 项目结构分析 — {{PROJECT_NAME}}

## 目录树
` ` `
{{tree 输出}}
` ` `

## 技术检测
| 检测项 | 结果 |
|--------|------|
| 框架 | {{框架名}} |
| 构建工具 | {{构建工具}} |
| 语言 | {{语言及版本}} |
| 包管理器 | npm / pip / poetry |

## 入口文件
- `{{入口文件路径}}`

## 关键文件清单
| 文件 | 类型 | 说明 |
|------|------|------|
| ... | ... | ... |

## 文件统计
| 扩展名 | 数量 |
|--------|------|
| .vue | N |
| .ts | N |
| .py | N |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | architecture | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->