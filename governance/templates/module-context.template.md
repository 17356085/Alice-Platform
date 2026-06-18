# MODULE_CONTEXT Template

> 使用方式：复制本模板 → 替换所有 `- ` 开头的占位行为实际内容 → 删除 `<!-- -->` 注释。

## 基本信息
- 模块ID：<!-- e.g. "equipment" — 英文短横线，与代码目录一致 -->
- 模块名称：<!-- e.g. "设备管理" — 从菜单/面包屑获取 -->
- 所属项目：<!-- e.g. "web-automation" -->
- 入口菜单：<!-- e.g. "设备管理"（一级菜单）-->
- 相关角色：<!-- e.g. "admin、设备管理员、操作工" -->

## 模块职责
- <!-- e.g. "设备台账管理、报警规则配置、维保工单调度" -->
- <!-- e.g. "摄像头实时监控与回放" -->

## 核心业务规则
- <!-- e.g. "设备编号全局唯一，不可重复" -->
- <!-- e.g. "报警规则必须关联至少一个设备" -->

## 模块边界
- 包含：<!-- e.g. "报警配置、摄像头管理、关键参数监控、维保管理" -->
- 不包含：<!-- e.g. "储罐监控（属于 tank 模块）、用户权限配置（属于 system-role 模块）" -->

## 关键页面
| 页面ID | 页面名称 | 路由 | 状态 | 说明 |
|--------|----------|------|------|------|
| <!-- alarm-config --> | <!-- 设备报警配置 --> | <!-- #/equipment/alarm-config --> | <!-- ✅ 已完成 --> | <!-- CRUD + 搜索 + 分页 --> |
| <!-- camera --> | <!-- 摄像头管理 --> | <!-- #/equipment/camera --> | <!-- ⏳ 待分析 --> | |
| <!-- ... --> | | | | |

> 状态标记：✅ 已完成 / 🔄 进行中 / ⏳ 待开始

## 风险概览
| 风险ID | 描述 | 等级 | 缓解措施 |
|--------|------|------|----------|
| <!-- RISK-XXX-001 --> | <!-- e.g. "误删除正在使用的报警规则" --> | <!-- P0 --> | <!-- e.g. "删除前弹窗二次确认 + 后端校验引用关系" --> |
| <!-- RISK-XXX-002 --> | <!-- ... --> | <!-- P1 --> | |

## 依赖关系
- 上游：<!-- e.g. "system-role（权限配置）、system-user（用户数据）" -->
- 下游：<!-- e.g. "production（生产报表引用设备数据）" -->

## 相关资产
- 页面上下文：<!-- e.g. "modules/equipment/pages/alarm-config/PAGE_CONTEXT.md" -->
- 测试设计：<!-- e.g. "modules/equipment/pages/alarm-config/TEST_DESIGN.md" -->
- 自动化脚本：<!-- e.g. "page/equipment_page/AlarmConfigPage.py" -->

---

## 示例填充

以下是一个完整填充的 MODULE_CONTEXT.md（设备管理模块）：

```markdown
# MODULE_CONTEXT — equipment

## 基本信息
- 模块ID：equipment
- 模块名称：设备管理
- 所属项目：web-automation
- 入口菜单：设备管理
- 相关角色：admin、设备管理员、操作工（只读）

## 模块职责
- 设备台账管理：设备新增/编辑/删除/搜索
- 报警规则配置：报警阈值设定、通知方式
- 关键参数监控：实时参数（温度/压力/流量）展示
- 摄像头管理：实时画面与历史回放

## 核心业务规则
- 设备编号全局唯一
- 报警规则必须关联至少一个设备
- 维保工单关闭前需上传维修记录

## 模块边界
- 包含：报警配置、摄像头管理、关键参数监控、维保管理、传感器管理、装置管理
- 不包含：储罐监控（tank模块）、用户权限（system-role模块）

## 关键页面
| 页面ID | 页面名称 | 路由 | 状态 | 说明 |
|--------|----------|------|------|------|
| alarm-config | 设备报警配置 | #/equipment/alarm-config | ✅ | CRUD+搜索+分页 |
| camera | 摄像头管理 | #/equipment/camera | ✅ | 实时画面+回放 |
| key-param | 关键参数监控 | #/equipment/key-param | 🔄 | 图表+阈值配置 |
| maintenance | 设备维保 | #/equipment/maintenance | ✅ | 工单管理 |
| sensor-manage | 传感器管理 | #/equipment/sensor | ⏳ | |
| unit-manage | 装置管理 | #/equipment/unit | ⏳ | |

## 风险概览
| 风险ID | 描述 | 等级 | 缓解措施 |
|--------|------|------|----------|
| RISK-EQ-001 | 误删报警规则导致监控失效 | P0 | 删除确认+引用校验 |
| RISK-EQ-002 | 传感器数据延迟影响决策 | P1 | 数据更新时间戳展示 |

## 依赖关系
- 上游：system-role、system-user
- 下游：production（生产报表引用设备数据）

## 相关资产
- 页面上下文：modules/equipment/pages/*/PAGE_CONTEXT.md
- 自动化脚本：page/equipment_page/*.py
```






<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: template-meta -->
> last_verified: 2026-06-17 21:52 | sync_progress.py
<!-- ⚠️ AUTO-GENERATED SECTION END: template-meta -->