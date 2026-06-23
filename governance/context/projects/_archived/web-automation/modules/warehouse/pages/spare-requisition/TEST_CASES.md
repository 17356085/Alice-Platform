# 测试用例: 备品领用申请 (Spare Requisition)

| 用例编号 | 用例标题 | 所属模块 | 所属页面 | 优先级 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 | 自动化状态 |
|----------|----------|----------|----------|--------|----------|----------|----------|----------|-----------|
| TC-SRQ-001 | 页面正常加载-表格渲染 | warehouse | spare-requisition | P0 | 1. 用户已登录<br>2. 有查看权限 | 1. 导航至备品领用申请页面<br>2. 等待页面稳定 | 无 | 1. 页面成功加载<br>2. 表格行数 >= 0 | ✅ 已自动化 |
| TC-SRQ-002 | 表格列数在合理范围 | warehouse | spare-requisition | P1 | 页面加载完成 | 1. JS 获取表头 th 数量 | 无 | 6 <= headers <= 14 | ✅ 已自动化 |
| TC-SRQ-003 | 新增按钮可见 | warehouse | spare-requisition | P0 | 页面加载完成 | 1. 检查新增按钮 | 无 | 新增按钮存在 | ✅ 已自动化 |
| TC-SRQ-004 | 分页组件可见 | warehouse | spare-requisition | P0 | 页面加载完成 | 1. 检查分页组件 | 无 | 分页器元素存在 | ✅ 已自动化 |
| TC-SRQ-005 | 按申请人搜索 | warehouse | spare-requisition | P0 | 1. 页面加载完成<br>2. 列表中存在申请人包含"test"的记录 | 1. 输入申请人 "test"<br>2. 点击查询 | 申请人: test | 搜索完成，无异常 | ✅ 已自动化 |
| TC-SRQ-006 | 重置搜索条件 | warehouse | spare-requisition | P1 | 已执行过搜索 | 1. 点击重置按钮 | 无 | 重置完成，搜索条件清空 | ✅ 已自动化 |
| TC-SRQ-007 | 新增弹窗打开 | warehouse | spare-requisition | P0 | 页面加载完成 | 1. 点击新增按钮 | 无 | 新增弹窗可见（`is_dialog_visible()` 为 True） | ✅ 已自动化 |
| TC-SRQ-008 | 新增弹窗有保存按钮 | warehouse | spare-requisition | P1 | 新增弹窗已打开 | 1. 检查弹窗内保存按钮 | 无 | `DIALOG_SAVE` 元素存在 | ✅ 已自动化 |
| TC-SRQ-009 | 查看第一行记录 | warehouse | spare-requisition | P1 | 1. 表格存在数据行 | 1. 点击第一行查看按钮 | 无 | 查看弹窗可见 | ✅ 已自动化 |
| TC-SRQ-010 | 第一行至少有一个操作按钮 | warehouse | spare-requisition | P0 | 1. 表格存在数据行 | 1. 检查查看/编辑/提交/删除按钮存在性 | 无 | 至少一个按钮存在 | ✅ 已自动化 |
| TC-SRQ-011 | 编辑按钮打开编辑弹窗 | warehouse | spare-requisition | P1 | 1. 表格存在可编辑行 | 1. 检查有编辑按钮<br>2. 点击编辑 | 无 | 编辑弹窗可见 | ✅ 已自动化 |
| TC-SRQ-012 | 第一行流程状态可读取 | warehouse | spare-requisition | P1 | 1. 表格存在数据行 | 1. 读取第一行 el-tag 文本 | 无 | 返回字符串类型的状态文本 | ✅ 已自动化 |
| TC-SRQ-013 | 提交按钮触发 Toast 提示 | warehouse | spare-requisition | P1 | 1. 表格存在可提交行 | 1. 检查有提交按钮<br>2. 点击提交 | 无 | Toast 提示出现（`wait_for_toast_text` 无异常） | ✅ 已自动化 |
| TC-SRQ-014 | 新增领用申请-正常填写并保存 | warehouse | spare-requisition | P0 | 1. 页面加载完成 | 1. 记录当前总数<br>2. 点击新增<br>3. 填写申请人<br>4. 点击保存<br>5. 搜索新建记录 | 申请人: AUTO_REQ_{ts} | 1. 创建成功<br>2. 新建记录可搜索到<br>3. 总数 >= 原先 + 1 | ✅ 已自动化 |
| TC-SRQ-015 | 删除刚创建的领用申请 | warehouse | spare-requisition | P0 | 1. 前置 TC-SRQ-014 已执行<br>2. 创建的申请记录存在 | 1. 搜索目标记录<br>2. 尝试删除<br>3. 确认删除<br>4. 再次搜索 | 申请人: AUTO_REQ_{ts}（从 TC-SRQ-014 获取） | 1. 删除成功<br>2. 记录不存在（`is_row_present` 返回 False） | ✅ 已自动化 |
| TC-SRQ-016 | 新增领用申请-取消操作 | warehouse | spare-requisition | P1 | 页面加载完成 | 1. 点击新增<br>2. 填写申请人<br>3. 点击取消<br>4. 搜索该申请人 | 申请人: AUTO_CANCEL_{ts} | 取消后记录不存在 | ✅ 已自动化 |
| TC-SRQ-017 | 新增领用申请-必填校验 | warehouse | spare-requisition | P1 | 页面加载完成 | 1. 点击新增<br>2. 不填写表单直接保存 | 无 | 1. 前端校验错误提示（若有）<br>2. 弹窗可能关闭或保持打开 | ✅ 已自动化 |
| TC-SRQ-018 | 按流程状态筛选 | warehouse | spare-requisition | P1 | 1. 列表中存在不同状态的记录 | 1. 选择流程状态下拉<br>2. 选择特定状态<br>3. 点击查询 | 状态: 待提交/审批中/已通过/已驳回 | 搜索结果符合状态筛选条件 | ⚠️ 待开发 |
| TC-SRQ-019 | 按日期范围搜索 | warehouse | spare-requisition | P1 | 1. 列表中存在日期范围内的记录 | 1. 选择日期范围<br>2. 点击查询 | 日期: 选择具体日期范围 | 搜索结果符合日期筛选 | ⚠️ 待开发 |
| TC-SRQ-020 | 空数据状态显示 | warehouse | spare-requisition | P2 | 1. 当前搜索条件下无记录 | 1. 输入不存在的申请人<br>2. 点击查询 | 申请人: __NON_EXISTENT__ | 表格显示空数据占位 | ⚠️ 待开发 |
| TC-SRQ-021 | 分页翻页操作 | warehouse | spare-requisition | P1 | 1. 列表数据超过一页 | 1. 点击下一页<br>2. 点击上一页 | 无 | 页面正常切换 | ⚠️ 待开发 |
| TC-SRQ-022 | 提交后流程状态变更验证 | warehouse | spare-requisition | P1 | 1. 存在可提交的草稿记录 | 1. 点击提交<br>2. 等待 Toast<br>3. 读取第一行新状态 | 无 | 提交后状态从草稿变更为审批中 | ⚠️ 待开发 |

**测试数据说明**:
- `AUTO_REQ_{ts}`: 时间戳后 6 位，用于新增测试的唯一申请人标识
- `AUTO_CANCEL_{ts}`: 时间戳后 5 位，用于取消测试的唯一申请人标识
- 时间戳格式: `str(int(time.time()))[-6:]` 和 `str(int(time.time()))[-5:]`

**清理策略**:
- 测试 `test_delete_created_requisition` 通过 `delete_by_name` 移除创建的记录
- 删除失败时通过 `CleanupTracker` 注册回调兜底清理
- 已审批记录的删除被 try/except 捕获，仅记录 warning

**按钮可见性规则**:
- 草稿/待提交: 查看/编辑/提交/删除 四按钮均可见
- 审批中: 仅查看按钮可见
- 已通过: 仅查看按钮可见
- 已驳回: 查看 + 编辑按钮可见（中置信度，从工作流一般规律推断）
