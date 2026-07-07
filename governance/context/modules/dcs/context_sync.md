好的，我们来为 `dcs` 模块定义它的核心功能、接口、操作指引和清单。

---

## 模块: `dcs`

### 1. 模块元信息
- **名称**: dcs (Directory Context Sync)
- **简称**: dcs
- **功能**: 同步项目上下文到 governance 目录。
- **类型**: 核心上下文管理模块 / 工具
- **状态**: 活跃 (Active)

### 2. 目标与职责
   - **主要功能**: 作为“写入”指令，将当前运行的项目（由 `.tlo/` 或 `project.yaml` 定义）的模块结构提取并同步到 `.tlo/../governance/` 目录中。
   - **数据同步**: 从项目的根目录提取模块列表，并更新 `governance/context/projects/{project-id}/` 目录下的文件。
   - **文档生成**: 基于扫描到的模块，自动生成并更新 `MODULE_INDEX.md` 文件，形成一个可导航的模块目录。

### 3. 输入
   - **项目定义**: 位于项目根目录下的 `.tlo/` 文件夹或 `project.yaml` 文件。用于确定项目名称（name）、远程仓库地址（url）和 `id`。
   - **目录结构**: 指项目根目录本身，用于扫描所有叶子节点目录（即模块）。

### 4. 输出
   - **`project.yaml`**: 强制输出。写入到 `governance/context/projects/{id}/project.yaml`。
   - **`MODULE_INDEX.md`**: 强制输出。写入到 `governance/context/projects/{id}/MODULE_INDEX.md`。

### 5. 工作流程
   1.  **初始化**: 加载项目根目录下的 `.tlo/` 或 `project.yaml`，提取 `id`、`name` 和 `url`。
   2.  **模块扫描**: 扫描项目根目录，识别所有直接子文件夹，形成模块列表。
   3.  **写入 `project.yaml`**: 将步骤1和2的信息整理并写入目标文件。
   4.  **生成 `MODULE_INDEX.md`**: 遍历模块列表，为每个模块生成一个包含其核心功能和依赖的摘要，并形成一个可链接的 Markdown 列表。

### 6. 核心逻辑与规则
   - **规则1**: `project.yaml` 必须具备完整的 `name` 和 `url`。
   - **规则2**: `MODULE_INDEX.md` 必须列出该项目所有已识别的模块。
   - **规则3**: 如果目标文件已存在，`dcs` 模块在写入前必须确认是否需要覆盖或合并。

### 7. 依赖
   - **内部依赖**: 无。
   - **外部依赖**: 无。

### 8. 交互接口
   - **命令行**: 无独立 CLI。由主工具调用。
   - **函数调用**: `sync_project_context(project_root_path: str, governance_base_path: str) -> dict`

### 9. 验证标准
   - `project.yaml` 存在且包含 `name` + `url` 字段。
   - `MODULE_INDEX.md` 列出所有模块，且格式正确（Markdown 链接有效）。

### 10. 约束
   - 模块仅能操作 `governance/context/` 目录下的文件。
   - 模块不应对项目目录本身进行写操作。

### 11. 清单
- [ ] 文档（README，设计文档）：待定
- [ ] 日志集成：待定
- [ ] 错误处理：待定
- [ ] 测试用例：待定
- [ ] API 接口定义：待定