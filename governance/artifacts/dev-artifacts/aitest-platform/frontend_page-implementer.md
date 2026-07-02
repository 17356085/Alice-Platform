## 无法继续执行 — 缺少必要输入

当前 `frontend/page-implementer` 技能的所需输入全部缺失，无法生成页面。以下是缺失项总结：

### 缺失的上下文文件
| 文件 | 状态 |
|---|---|
| `COMPONENT_TREE.md` | ❌ 文件不存在 |
| `API_CONTRACTS.md` | ❌ 文件不存在 |

### 缺失的模板变量
| 变量 | 说明 |
|---|---|
| `{{PageName}}` | 页面名称（如 `UserList`） |
| `{{RoutePath}}` | 路由路径（如 `/users`） |
| `{{PageDescription}}` | 页面职责描述 |
| `{{CHILD_COMPONENTS_LIST}}` | 子组件清单及其 Props/Events 接口 |
| `{{PAGE_API_ENDPOINTS}}` | 页面需要调用的 API 端点 |
| `{{STORE_DEFINITION}}` | Pinia Store 定义 |

### RAG 知识库查询
| 查询 | 结果 |
|---|---|
| `rag.search` | ❌ 无可用 provider |
| `rag.business_rules` | ❌ 无可用 provider |

---

### 下一步建议

请提供以下任一信息，我可以继续：

1. **具体页面名称**和所在模块（如 "equipment 模块的 EquipmentList 页面"）
2. **子组件 YAML**（`PROPS_INTERFACE.yaml` 内容）
3. **API 契约定义**（页面需要调用的端点）
4. **Pinia Store 代码**

或者，如果你有可访问的项目仓库，可以告诉我路径，我来读取相关文件。