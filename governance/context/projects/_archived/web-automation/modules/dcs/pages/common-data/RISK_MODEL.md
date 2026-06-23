# RISK_MODEL — DCS 常用点位（Common-Data）

## 风险矩阵

| ID | 风险 | 可能性 | 影响 | 等级 | 缓解 |
|----|------|:-----:|:---:|:----:|------|
| R-COM-01 | Vue Draggable 拖拽排序 JS 模拟不可靠 | H | M | **高** | 拖拽测试用 JS 脚本，失败时 skip |
| R-COM-02 | 右键菜单由 Teleport 渲染到 body | M | M | **中** | 菜单项用 `el-popper` 或 `[role="menu"]` 选择器 |
| R-COM-03 | 卡片为空时 `get_card_count()=0` | M | L | **低** | 所有卡片操作前检查 count > 0 |
| R-COM-04 | 恢复默认操作不可逆 | L | H | **中** | destructive 标记，测试前确认数据可恢复 |

## 测试影响
- **拖拽**: 非关键路径，失败不阻塞
- **右键菜单**: 用 ActionChains + 全局选择器
- **空状态**: 页面可能无卡片，smoke 测试允许 count=0
