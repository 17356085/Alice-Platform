根据对 `hygiene-check` 的规则分析，以下是针对 `governance/context/projects/{id}/` 目录下 **“system” 模块**的检查结果与输出：

---

### **卫生检查报告: system 模块**

#### **缺失文档清单**

| 优先级 | 缺失文件 | 预期路径 | 影响 |
|--------|----------|----------|------|
| **P0** | `PROJECT.md` 或 `project.yaml` | `governance/context/projects/{id}/system/PROJECT.md` | 缺少模块根定义，无法确定模块边界与依赖 |
| **P0** | `MODULE_CONTEXT.md` | `governance/context/projects/{id}/system/MODULE_CONTEXT.md` | 核心治理文档缺失，模块结构无法被自动化工具识别 |
| **P1** | `PAGE_CONTEXT.md` (通用入口) | `governance/context/projects/{id}/system/docs/PAGE_CONTEXT.md` | 文档概览丢失，新成员无法快速理解文档结构 |
| **P2** | 模块内子页面 `PAGE_CONTEXT.md` | 路径根据实际页面位置而定 | 若存在多个页面，全部缺失则治理链断裂 |

> **说明**  
> - 优先级 **P0** 表示必须补齐，否则该模块不满足治理基本要求。  
> - 优先级 **P1** 表示推荐补齐，否则限制可发现性与协作效率。  
> - 优先级 **P2** 表示缺失但影响较小，可在后续迭代补齐。  

---

#### **建议**

1. **立即补齐**  
   - 创建 `MODULE_CONTEXT.md`，明确 system 模块职责、依赖、元数据。  
   - 创建 `PROJECT.md` 或 `project.yaml`（推荐 YAML 结构便于机器解析）。  

2. **检查模块内页面**  
   - 确认 system/ 下是否存在 `api/`、`docs/`、`config/` 等子目录，每个子目录应包含 **PAGE_CONTEXT.md**。  

3. **设置 Git Hook / CI 检查**  
   - 可在 `pre-commit` 或 CI 脚本中增加对该模块的 hygiene-check，避免后续提交再次缺失。  

4. **参考模板**  
   - 若不确定格式，可复制项目根 `MODULE_CONTEXT.md` 或 `PAGE_CONTEXT.md` 模板进行适配。  

---

#### **结论**

**system 模块当前健康状态 ❌ 不通过**  
> 缺少 P0 关键文档 2 项，P1 文档 1 项。推荐 **立即补充** 上述缺失文件后再执行后续检查。