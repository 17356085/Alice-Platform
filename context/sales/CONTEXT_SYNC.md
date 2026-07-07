## context-sync 模块已读取

**模块名称**: sales  
**所属项目**: context-sync  
**功能**: 同步项目上下文到 governance 目录  
**输入**: 项目目录结构、.tlo/ 或 project.yaml  
**输出**: governance/context/projects/{id}/project.yaml、governance/context/projects/{id}/MODULE_INDEX.md  

### 模块执行情况
当前项目 **context-sync** 已正确识别。该模块负责将项目结构同步至 governance 目录，确保项目元数据（name、url、modules）被写入 project.yaml，并自动生成 MODULE_INDEX.md 索引文件。

### 输出文件示例
- **project.yaml**: 包含 `name`、`url`、`modules` 字段
- **MODULE_INDEX.md**: 列出所有模块名称