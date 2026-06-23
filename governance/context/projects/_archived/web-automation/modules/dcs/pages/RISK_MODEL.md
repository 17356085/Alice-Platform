我需要先读取已有的 `alarm-config` 页面上下文，作为参考格式，然后为 dcs 模块的 alarm-config 页面执行风险建模。

<tool_call>
{"name": "read_file", "parameters": {"path": ".kiro/context/modules/dcs/pages/alarm-config/PAGE_CONTEXT.md"}}
</tool_call>
<tool_response>
# PAGE_CONTEXT.md — 报警配置页

## 页面基本信息

| 字段 | 值 |
|------|-----|
| 页面ID | dcs-alarm-config |
| 页面名称 | 报警配置 |
| URL路径 | `/dcs/alarm-config` |
| 所属模块 | dcs |
| 页面类型 | 配置管理页（列表 + 弹窗编辑） |

## 页面功能

| 功能ID | 功能名称 | 描述 |
|--------|---------|------|
| F-001 | 报警列表展示 | 以表格形式展示所有报警配置项 |
| F-002 | 新增报警配置 | 通过弹窗表单新增报警规则 |
| F-003 | 编辑报警配置 | 通过弹窗表单编辑现有报警规则 |
| F-004 | 删除报警配置 | 删除选中的报警配置项 |
| F-005 | 启用/禁用报警 | 切换报警配置的启用状态 |
| F-006 | 搜索/筛选 | 按条件筛选报警配置列表 |

## 业务规则

| 规则ID | 规则描述 | 严重性 |
|--------|---------|--------|
| BR-001 | 报警阈值上限必须大于下限 | 高 |
| BR-002 | 同一设备同一参数不能有重复的激活报警配置 | 高 |
| BR-003 | 已启用的报警配置不能直接删除，必须先禁用 | 高 |
| BR-004 | 报警延迟时间范围：0-3600秒 | 中 |
| BR-005 | 报警级别分为：紧急/重要/一般 三级 | 中 |
| BR-006 | 关联设备被删除时，对应报警配置应自动禁用 | 高 |

## 数据字段

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| 配置名称 | string | 是 | 长度 2-50 字符 |
| 关联设备 | select | 是 | 从设备列表选取 |
| 监测参数 | select | 是 | 依赖关联设备动态加载 |
| 报警阈值下限 | number | 是 | 数值，单位由参数决定 |
| 报警阈值上限 | number | 是 | 数值，必须 > 下限 |
| 报警级别 | select | 是 | 紧急/重要/一般 |
| 报警延迟 | number | 否 | 0-3600秒，默认0 |
| 备注 | textarea | 否 | 最长 200 字符 |

## 页面状态

| 状态 | 描述 |
|------|------|
| 列表加载中 | 表格 loading 骨架屏 |
| 列表为空 | 展示空状态提示 |
| 弹窗打开 | 遮罩层 + 表单弹窗 |
| 提交中 | 按钮 loading，防止重复提交 |
| 操作成功 | Toast 提示 + 列表刷新 |
| 操作失败 | Toast 错误提示，弹窗保持打开 |

## 关联模块/页面

| 关联对象 | 关系 |
|---------|------|
| equipment 模块 - 设备列表 | 报警配置依赖设备数据，设备下拉来源于此 |
| dcs - 实时监测页 | 报警配置激活后，触发实时监测页的报警展示 |
| dcs - 历史查询页 | 报警事件记录可在历史查询页查询 |

## 接口信息（来源：PAGE_INTERFACE.yaml）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/dcs/alarm-configs` | GET | 获取报警配置列表 |
| `/api/dcs/alarm-configs` | POST | 新增报警配置 |
| `/api/dcs/alarm-configs/{id}` | PUT | 更新报警配置 |
| `/api/dcs/alarm-configs/{id}` | DELETE | 删除报警配置 |
| `/api/dcs/alarm-configs/{id}/toggle` | PATCH | 启用/禁用报警配置 |
| `/api/equipment/devices` | GET | 获取设备列表（用于下拉） |
| `/api/equipment/devices/{id}/params` | GET | 获取设备参数列表（动态加载） |
</tool_response>

<tool_call>
{"name": "read_file", "parameters": {"path": ".kiro/context/modules/dcs/pages/alarm-config/PAGE_INTERFACE.yaml"}}
</tool_call>
<tool_response>
openapi: "3.0.0"
info:
  title: DCS 报警配置接口
  version: "1.0"

paths:
  /api/dcs/alarm-configs:
    get:
      summary: 获取报警配置列表
      parameters:
        - name: page
          in: query
          schema:
            type: integer
        - name: pageSize
          in: query
          schema:
            type: integer
        - name: keyword
          in: query
          schema:
            type: string
        - name: status
          in: query
          schema:
            type: string
            enum: [active, inactive]
        - name: deviceId
          in: query
          schema:
            type: string
      responses:
        "200":
          description: 列表数据
          content:
            application/json:
              schema:
                type: object
                properties:
                  total: { type: integer }
                  list:
                    type: array
                    items:
                      $ref: '#/components/schemas/AlarmConfig'
        "401":
          description: 未认证
        "403":
          description: 无权限

    post:
      summary: 新增报警配置
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AlarmConfigInput'
      responses:
        "201":
          description: 创建成功
        "400":
          description: 参数校验失败
        "409":
          description: 同设备同参数已存在激活配置

  /api/dcs/alarm-configs/{id}:
    put:
      summary: 更新报警配置
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AlarmConfigInput'
      responses:
        "200":
          description: 更新成功
        "400":
          description: 参数校验失败
        "404":
          description: 配置不存在
        "409":
          description: 同设备同参数已存在激活配置

    delete:
      summary: 删除报警配置
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: 删除成功
        "400":
          description: 启用状态不允许删除
        "404":
          description: 配置不存在

  /api/dcs/alarm-configs/{id}/toggle:
    patch:
      summary: 启用/禁用报警配置
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  enum: [active, inactive]
      responses:
        "200":
          description: 操作成功
        "400":
          description: 同设备同参数已存在激活配置（启用时）
        "404":
          description: 配置不存在

  /api/equipment/devices:
    get:
      summary: 获取设备列表（供下拉选择）
      responses:
        "200":
          description: 设备列表

  /api/equipment/devices/{id}/params:
    get:
      summary: 获取设备参数列表
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: 参数列表
        "404":
          description: 设备不存在

components:
  schemas:
    AlarmConfig:
      type: object
      properties:
        id: { type: string }
        name: { type: string }
        deviceId: { type: string }
        deviceName: { type: string }
        paramId: { type: string }
        paramName: { type: string }
        thresholdLow: { type: number }
        thresholdHigh: { type: number }
        level: { type: string, enum: [critical, major, minor] }
        delay: { type: integer }
        status: { type: string, enum: [active, inactive] }
        remark: { type: string }
        createdAt: { type: string, format: date-time }
        updatedAt: { type: string, format: date-time }

    AlarmConfigInput:
      type: object
      required: [name, deviceId, paramId, thresholdLow, thresholdHigh, level]
      properties:
        name: { type: string, minLength: 2, maxLength: 50 }
        deviceId: { type: string }
        paramId: { type: string }
        thresholdLow: { type: number }
        thresholdHigh: { type: number }
        level: { type: string, enum: [critical, major, minor] }
        delay: { type: integer, minimum: 0, maximum: 3600 }
        remark: { type: string, maxLength: 200 }
</tool_response>

<tool_call>
{"name": "read_file", "parameters": {"path": ".kiro/context/modules/dcs/pages/alarm-config/PAGE_ELEMENT_POSITION.md"}}
</tool_call>
<tool_response>
# PAGE_ELEMENT_POSITION.md — 报警配置页

## 整体布局

```
┌─────────────────────────────────────────────────────────┐
│  [搜索框]  [状态筛选▼]  [设备筛选▼]          [新增报警] │
├─────────────────────────────────────────────────────────┤
│  配置名称  关联设备  监测参数  阈值范围  级别  状态  操作 │
│  ────────────────────────────────────────────────────── │
│  row-1                                                  │
│  row-2                                                  │
│  ...                                                    │
├─────────────────────────────────────────────────────────┤
│                        [分页器]                          │
└─────────────────────────────────────────────────────────┘
```

## 弹窗布局（新增/编辑）

```
┌──────────────────────────────────┐
│  新增报警配置              [×]   │
├──────────────────────────────────┤
│  配置名称*  [________________]   │
│  关联设备*  [____▼]              │
│  监测参数*  [____▼]              │
│  阈值下限*  [______]             │
│  阈值上限*  [______]             │
│  报警级别*  [____▼]              │
│  报警延迟   [______] 秒          │
│  备注       [________________]   │
│                  [取消]  [确认]  │
└──────────────────────────────────┘
```

## 元素定位索引

| 元素ID | 说明 | 定位策略 | 选择器 |
|--------|------|---------|--------|
| EL-001 | 搜索框 | CSS | `.search-input input` |
| EL-002 | 状态筛选下拉 | CSS | `.status-filter` |
| EL-003 | 设备筛选下拉 | CSS | `.device-filter` |
| EL-004 | 新增按钮 | CSS | `.btn-add-alarm` |
| EL-005 | 表格 | CSS | `.alarm-config-table` |
| EL-006 | 表格行 | XPath | `//tr[contains(@class,'el-table__row')]` |
| EL-007 | 编辑按钮（行内） | XPath | `.//button[contains(@class,'btn-edit')]` |
| EL-008 | 删除按钮（行内） | XPath | `.//button[contains(@class,'btn-delete')]` |
| EL-009 | 启用/禁用开关 | CSS | `.el-switch` |
| EL-010 | 弹窗 | CSS | `.alarm-config-dialog` |
| EL-011 | 配置名称输入框 | CSS | `.alarm-config-dialog .field-name input` |
| EL-012 | 关联设备下拉 | CSS | `.alarm-config-dialog .field-device` |
| EL-013 | 监测参数下拉 | CSS | `.alarm-config-dialog .field-param` |
| EL-014 | 阈值下限输入框 | CSS | `.alarm-config-dialog .field-threshold-low input` |
| EL-015 | 阈值上限输入框 | CSS | `.alarm-config-dialog .field-threshold-high input` |
| EL-016 | 报警级别下拉 | CSS | `.alarm-config-dialog .field-level` |
| EL-017 | 报警延迟输入框 | CSS | `.alarm-config-dialog .field-delay input` |
| EL-018 | 备注文本框 | CSS | `.alarm-config-dialog .field-remark textarea` |
| EL-019 | 确认按钮 | CSS | `.alarm-config-dialog .btn-confirm` |
| EL-020 | 取消按钮 | CSS | `.alarm-config-dialog .btn-cancel` |
| EL-021 | 分页器 | CSS | `.el-pagination` |
| EL-022 | 删除确认弹窗确认按钮 | CSS | `.el-message-box__btns .el-button--primary` |
```
</tool_response>

现在检查是否已有模板文件和已有的 RISK_MODEL 产出物。
<tool_call>
{"name": "find_files", "parameters": {"pattern": "**/templates/risk-model*", "explanation": "Find risk model template"}}
</tool_call>
<tool_response>
["templates/risk-model.template.md"]
</tool_response>

<tool_call>
{"name": "read_file", "parameters": {"path": "templates/risk-model.template.md"}}
</tool_call>
<tool_response>
# RISK_MODEL.md — {{页面名称}}

> **版本**: 1.0 | **创建时间**: {{日期}} | **对应页面**: {{页面ID}}
> **状态**: Draft

---

## 风险汇总

| 风险ID | 维度 | 风险描述 | 等级 | 缓解措施 | 自动化覆盖 |
|--------|------|---------|------|---------|-----------|
| RISK-XXX-001 | 业务 | ... | P0 | ... | ❌ 未覆盖 |

---

## 1. 业务风险

### RISK-XXX-001
- **描述**:
- **触发场景**:
- **影响**:
- **等级**: P0
- **缓解措施**:
- **自动化覆盖**: ❌ 未覆盖

---

## 2. 权限风险

---

## 3. 数据风险

---

## 4. 接口风险

---

## 5. UI/UX 风险

---

## 6. 性能风险

---

## 附录：自动化覆盖率统计

| 等级 | 总数 | 已覆盖 | 未覆盖 | 覆盖率 |
|------|------|--------|--------|--------|
| P0 | - | - | - | - |
| P1 | - | - | - | - |
| P2 | - | - | - | - |
</tool_response>

<tool_call>
{"name": "find_files", "parameters": {"pattern": "**/alarm-config/RISK*", "explanation": "Check if RISK_MODEL already exists"}}
</tool_call>
<tool_response>
[]
</tool_response>

所有输入已就绪，开始产出两份文档。
<tool_call>
{"name": "write_file", "parameters": {"path": ".kiro/context/modules/dcs/pages/alarm-config/RISK_MODEL.md", "content": "# RISK_MODEL.md — 报警配置页\n\n> **版本**: 1.0 | **创建时间**: 2026-06-17 | **对应页面**: dcs-alarm-config\n> **状态**: Draft\n\n---\n\n## 风险汇总\n\n| 风险ID | 维度 | 风险描述 | 等级 | 缓解措施 | 自动化覆盖 |\n|--------|------|---------|------|---------|----------|\n| RISK-ALARM-001 | 业务 | 误删已启用报警配置，导致关键设备失去报警保护 | P0 | 前后端双重拦截：启用状态禁止删除 | ❌ 未覆盖 |\n| RISK-ALARM-002 | 业务 | 同设备同参数创建重复激活配置，导致报警逻辑冲突 | P0 | 后端 409 + 前端提示；启用时同样校验 | ❌ 未覆盖 |\n| RISK-ALARM-003 | 业务 | 阈值上限 ≤ 下限被保存，导致报警永不触发或持续触发 | P0 | 前端提交前校验 + 后端 400 拦截 | ❌ 未覆盖 |\n| RISK-ALARM-004 | 业务 | 关联设备被删除后报警配置未自动禁用，持续引用已删除设备 | P1 | 设备删除级联禁用报警配置（BR-006） | ❌ 未覆盖 |\n| RISK-ALARM-005 | 权限 | 无权限用户通过直接访问 URL `/dcs/alarm-config` 获取配置列表 | P0 | 路由守卫 + 接口 401/403 拦截 | ❌ 未覆盖 |\n| RISK-ALARM-006 | 权限 | 只读角色通过接口直接调用 POST/PUT/DELETE 绕过前端按钮禁用 | P0 | 后端必须校验操作权限，不依赖前端隐藏 | ❌ 未覆盖 |\n| RISK-ALARM-007 | 数据 | 阈值字段传入非数值（如空字符串、字母）导致后端异常 | P1 | 前端数值类型校验 + 后端类型校验 | ❌ 未覆盖 |\n| RISK-ALARM-008 | 数据 | 配置名称含 SQL 注入或 XSS 特殊字符（`<script>`、`' OR 1=1`）被持久化 | P1 | 后端参数化查询 + 前端输出转义 | ❌ 未覆盖 |\n| RISK-ALARM-009 | 数据 | 并发：两个用户同时编辑同一条配置，后保存者静默覆盖前者修改 | P1 | 乐观锁（updatedAt 版本校验）或提示冲突 | ❌ 未覆盖 |\n| RISK-ALARM-010 | 数据 | 报警延迟填写 3601 或负数，前端未拦截直接提交 | P2 | 前端 min/max 校验 + 后端 400 | ❌ 未覆盖 |\n| RISK-ALARM-011 | 接口 | 获取设备列表接口超时，导致新增/编辑弹窗设备下拉永久 loading | P1 | 超时兜底提示 + 重试入口 | ❌ 未覆盖 |\n| RISK-ALARM-012 | 接口 | 切换设备后动态加载参数接口失败，监测参数下拉空白但无提示 | P1 | 接口失败时展示错误提示并清空参数选项 | ❌ 未覆盖 |\n| RISK-ALARM-013 | 接口 | Token 过期后操作（新增/编辑/删除）被 401 拦截，前端无跳转登录处理 | P1 | 全局 axios 拦截器捕获 401 → 跳转登录页 | ❌ 未覆盖 |\n| RISK-ALARM-014 | 接口 | DELETE 接口返回 400（启用状态），前端未区分错误码，展示通用错误提示 | P2 | 前端按错误码展示具体原因 | ❌ 未覆盖 |\n| RISK-ALARM-015 | UI/UX | 删除操作无二次确认弹窗，用户误触直接删除 | P1 | 删除前弹出 el-message-box 确认 | ❌ 未覆盖 |\n| RISK-ALARM-016 | UI/UX | 弹窗提交中未禁用确认按钮，用户重复点击导致重复提交 | P1 | 提交中按钮设置 loading + disabled | ❌ 未覆盖 |\n| RISK-ALARM-017 | UI/UX | 编辑弹窗回显数据不完整（监测参数未回显），用户误以为数据丢失 | P1 | 编辑时先加载设备参数列表再回填 paramId | ❌ 未覆盖 |\n| RISK-ALARM-018 | UI/UX | 小屏幕（1280px）下弹窗表单字段溢出或遮挡 | P2 | 响应式布局或弹窗最小宽度设定 | ❌ 未覆盖 |\n| RISK-ALARM-019 | 性能 | 报警配置条目超过 500 条时，前端表格渲染卡顿 | P2 | 分页限制每页条数（建议 ≤20）；虚拟滚动备选 | ❌ 未覆盖 |\n| RISK-ALARM-020 | 性能 | 搜索框每次键入都触发接口请求，高频请求打满后端 | P2 | 搜索防抖（300ms debounce） | ❌ 未覆盖 |\n\n---\n\n## 1. 业务风险\n\n### RISK-ALARM-001\n- **描述**: 误删已启用的报警配置，导致该设备参数失去报警监测保护\n- **触发场景**: 运维人员点击"删除"按钮，未注意该配置当前为启用状态\n- **影响**: 设备超阈值运行时无报警触发，可能造成安全事故\n- **等级**: P0\n- **缓解措施**:\n  1. 前端：启用状态下删除按钮置灰或隐藏\n  2. 后端：DELETE 接口检查 status=active 时返回 400，阻止删除\n  3. 错误提示：\"请先禁用该报警配置，再执行删除操作\"\n- **自动化覆盖**: ❌ 未覆盖\n\n### RISK-ALARM-002\n- **描述**: 同一设备同一参数存在多条激活报警配置，报警判断逻辑冲突\n- **触发场景**: 新增配置时未感知已存在激活配置；或将禁用配置重新启用时未校验冲突\n- **影响**: 报警可能重复触发或相互抵消，监测结果不可信\n- **等级**: P0\n- **缓解措施**:\n  1. 后端 POST/PUT 返回 409：\"该设备该参数已存在激活的报警配置\"\n  2. PATCH toggle 启用时同样触发唯一性校验\n  3. 前端展示 409 错误信息，弹窗保持打开\n- **自动化覆盖**: ❌ 未覆盖\n\n### RISK-ALARM-003\n- **描述**: 阈值上限 ≤ 下限被成功保存，报警规则在逻辑上无效\n- **触发场景**: 用户先填上限后填下限，或直接修改数值导致上下限倒置\n- **影响**: 报警永不触发（上限<下限区间为空）或始终触发（设计错误），影响生产安全\n- **等级**: P0\n- **缓解措施**:\n  1. 前端表单 validator：thresholdHigh > thresholdLow，提交前阻断\n  2. 后端 400 兜底校验\n  3. 提示文案：\"报警阈值上限必须大于下限\"\n- **自动化覆盖**: ❌ 未覆盖\n\n### RISK-ALARM-004\n- **描述**: equipment 模块中设备被删除后，对应报警配置未自动禁用，前端展示孤立配置\n- **触发场景**: 管理员在设备管理页删除设备，未触发级联禁用\n- **影响**: 孤立配置持续占据\"激活\"槽位，影响同参数新配置创建；页面展示设备名为空\n- **等级**: P1\n- **缓解措施**: 设备删除时后端级联将关联报警配置 status 改为 inactive（BR-006）\n- **自动化覆盖**: ❌ 未覆盖\n\n---\n\n## 2. 权限风险\n\n### RISK-ALARM-005\n- **描述**: 未登录用户或无 dcs 模块权限用户直接访问 `/dcs/alarm-config`，获取配置数据\n- **触发场景**: 用户保存了 URL，会话过期后直接打开；或知道 URL 的无权限用户\n- **影响**: 工业设备报警配置参数（阈值、级别）暴露，存在安全隐患\n- **等级**: P0\n- **缓解措施**:\n  1. 前端路由守卫：未登录 → 跳转 `/login`；无模块权限 → 跳转 403 页面\n  2. 后端 GET `/api/dcs/alarm-configs` 返回 401/403\n- **自动化覆盖**: ❌ 未覆盖\n\n### RISK-ALARM-006\n- **描述**: 只读角色用户绕过前端（隐藏的操作按钮），直接发起 POST/PUT/DELETE 请求\n- **触发场景**: 用户使用 Postman 或浏览器 DevTools