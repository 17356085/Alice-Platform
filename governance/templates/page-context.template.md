# PAGE_CONTEXT Template

> 使用方式：复制本模板 → 替换所有字段为实际内容 → 删除 `<!-- -->` 注释。

## 基本信息
- 页面ID：<!-- e.g. "alarm-config" — 英文短横线 -->
- 页面名称：<!-- e.g. "设备报警配置" — 从面包屑/菜单获取 -->
- 所属模块：<!-- e.g. "设备管理（equipment）" -->
- 页面入口：<!-- e.g. "左侧菜单 → 设备管理 → 设备报警配置" -->
- 路由 / 标识：<!-- e.g. "#/equipment/alarm-config" -->

## 页面职责
- <!-- e.g. "展示设备报警规则列表，支持按名称/类型/状态搜索" -->
- <!-- e.g. "提供报警规则的新增、编辑、删除操作" -->

## 核心元素
- 查询区：<!-- e.g. "报警名称输入框 + 报警类型下拉框 + 状态下拉框 + 搜索按钮 + 重置按钮" -->
- 列表区：<!-- e.g. "el-table：报警名称/报警类型/阈值/状态/创建时间/操作(编辑+删除)" 共6列 -->
- 表单区：<!-- e.g. "新增/编辑弹窗内的 el-form：名称(input)/类型(select)/阈值(input-number)/描述(textarea)" -->
- 操作按钮：<!-- e.g. "新增(表格上方)、编辑(行内)、删除(行内)" -->
- 弹窗：<!-- e.g. "新增/编辑弹窗(居中, 600px宽) + 删除确认弹窗(居中, 420px宽)" -->

## 关键交互
- <!-- e.g. "搜索按钮 → 表格数据异步刷新 → loading 遮罩" -->
- <!-- e.g. "新增按钮 → 弹窗展开 → 填写表单 → 确认 → 表格刷新 + toast提示" -->
- <!-- e.g. "删除按钮 → 确认弹窗 → 确认 → 记录消失 + toast提示" -->

## 权限与角色
- 可见角色：<!-- e.g. "admin、设备管理员" -->
- 可操作角色：<!-- e.g. "admin（全部操作）、设备管理员（新增/编辑，不可删除）" -->
- 特殊限制：<!-- e.g. "操作工仅可见报警列表，无操作按钮" -->

## 特殊行为
- 异步加载：<!-- e.g. "表格数据、下拉选项异步加载；搜索后 loading 遮罩 300-800ms" -->
- 动态渲染：<!-- e.g. "状态列使用 el-tag（启用=绿色/禁用=红色）；v-if 控制操作按钮显隐" -->
- 前端校验：<!-- e.g. "名称必填≤50字符；阈值0-1000数字" -->
- 后端校验：<!-- e.g. "名称唯一性校验；阈值关联设备类型合法性" -->

## 依赖
- 接口：<!-- e.g. "GET /api/alarm/list, POST /api/alarm/add, PUT /api/alarm/{id}, DELETE /api/alarm/{id}" -->
- 上下游页面：<!-- e.g. "上游：设备台账页；下游：无" -->

---

## 示例填充

以下是一个完整填充的 PAGE_CONTEXT.md（设备报警配置页）：

```markdown
# PAGE_CONTEXT — equipment / alarm-config

## 基本信息
- 页面ID：alarm-config
- 页面名称：设备报警配置
- 所属模块：设备管理（equipment）
- 页面入口：左侧菜单 → 设备管理 → 设备报警配置
- 路由：#/equipment/alarm-config

## 页面职责
- 展示设备报警规则列表，支持按名称/类型/状态搜索
- 提供报警规则的新增、编辑、删除操作

## 核心元素
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| search-input | 报警名称搜索框 | el-input | 搜索区 | placeholder="请输入报警名称" |
| search-type | 报警类型下拉 | el-select | 搜索区 | 温度/压力/流量 |
| search-btn | 搜索按钮 | el-button | 搜索区 | 文字="搜索" |
| reset-btn | 重置按钮 | el-button | 搜索区 | 文字="重置" |
| add-btn | 新增按钮 | el-button | 搜索区 | 文字="新增" |
| table | 报警配置表格 | el-table | 表格区 | 6列+操作列 |
| col-name | 报警名称列 | text | 表格区 | |
| col-status | 状态列 | el-tag | 表格区 | 启用=绿/禁用=红 |
| col-actions | 操作列 | buttons | 表格区 | 编辑+删除 |
| dialog | 新增/编辑弹窗 | el-dialog | 弹窗 | 600px宽，居中 |
| dialog-confirm | 确认按钮 | el-button | 弹窗 | 文字="确定" |
| pagination | 分页器 | el-pagination | 底部 | 默认10条/页 |

## 关键交互
- 搜索→表格异步刷新→loading遮罩
- 新增→弹窗展开→填写→确认→表格刷新+toast
- 删除→确认弹窗→确认→记录消失+toast

## 权限与角色
- 可见角色：admin、设备管理员、操作工
- 可操作角色：admin(全部)、设备管理员(新增/编辑)
- 特殊限制：操作工仅可查看

## 特殊行为
- 异步加载：表格数据异步；loading 300-800ms
- 动态渲染：状态列 el-tag 动态颜色；v-if 控制按钮
- 前端校验：名称必填≤50字符；阈值0-1000

## 依赖
- 接口：GET/POST/PUT/DELETE /api/alarm/*
- 上下游页面：上游-设备台账
```










<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: template-meta -->
> last_verified: 2026-06-18 10:54 | sync_progress.py
<!-- ⚠️ AUTO-GENERATED SECTION END: template-meta -->