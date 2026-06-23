# 测试用例: 备品出库 (Spare Out Order)

| 用例编号 | 用例标题 | 所属模块 | 所属页面 | 优先级 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 | 自动化状态 |
|----------|----------|----------|----------|--------|----------|----------|----------|----------|-----------|
| TC-SOO-001 | 页面正常加载-表格渲染 | warehouse | spare-out-order | P0 | 1. 用户已登录<br>2. 有查看权限 | 1. 导航至备品出库页面<br>2. 等待页面稳定 | 无 | 1. 页面成功加载<br>2. 表格行数 >= 0 | ✅ 已自动化 |
| TC-SOO-002 | 表格列数在合理范围 | warehouse | spare-out-order | P1 | 页面加载完成 | 1. JS 获取表头 th 数量 | 无 | 8 <= headers <= 28 | ✅ 已自动化 |
| TC-SOO-003 | 分页组件可见 | warehouse | spare-out-order | P0 | 页面加载完成 | 1. 检查分页组件 | 无 | 分页器元素存在 | ✅ 已自动化 |
| TC-SOO-004 | 新增按钮可见 | warehouse | spare-out-order | P0 | 页面加载完成 | 1. 检查新增按钮 | 无 | 新增按钮存在 | ✅ 已自动化 |
| TC-SOO-005 | 备件查询按钮可见 | warehouse | spare-out-order | P1 | 页面加载完成 | 1. 检查备件查询按钮 | 无 | 备件查询按钮存在 | ✅ 已自动化 |
| TC-SOO-006 | 按经办人搜索 | warehouse | spare-out-order | P0 | 1. 页面加载完成<br>2. 列表中存在经办人包含"test"的记录 | 1. 输入经办人 "test"<br>2. 点击查询 | 经办人: test | 搜索完成，无异常 | ✅ 已自动化 |
| TC-SOO-007 | 重置搜索条件 | warehouse | spare-out-order | P1 | 已执行过搜索 | 1. 点击重置按钮 | 无 | 重置完成，搜索条件清空 | ✅ 已自动化 |
| TC-SOO-008 | 新增弹窗打开 | warehouse | spare-out-order | P0 | 页面加载完成 | 1. 点击新增按钮 | 无 | 新增弹窗可见（`is_dialog_visible()` 为 True） | ✅ 已自动化 |
| TC-SOO-009 | 新增弹窗有表单输入项 | warehouse | spare-out-order | P1 | 新增弹窗已打开 | 1. JS 统计弹窗内 input/textarea 数量 | 无 | input/textarea 数量 >= 1 | ✅ 已自动化 |
| TC-SOO-010 | LY 单号链接可点击 | warehouse | spare-out-order | P1 | 1. 页面加载完成<br>2. 存在 LY 单号链接 | 1. 查找 `.el-button--primary.is-link` 文本以 LY 开头的按钮<br>2. 点击第一个 LY 链接 | 动态获取 LY 单号 | 点击无异常，页面稳定 | ✅ 已自动化 |
| TC-SOO-011 | 备件查询按钮导航 | warehouse | spare-out-order | P1 | 页面加载完成 | 1. 点击备件查询按钮 | 无 | 页面导航到备件查询页面 | ✅ 已自动化 |
| TC-SOO-012 | 查看第一行记录 | warehouse | spare-out-order | P1 | 1. 表格存在数据行 | 1. 点击第一行查看按钮 | 无 | 查看弹窗可见 | ✅ 已自动化 |
| TC-SOO-013 | 新增出库-正常填写并保存 | warehouse | spare-out-order | P0 | 1. 页面加载完成 | 1. 记录当前总数<br>2. 点击新增<br>3. 填写经办人<br>4. 点击保存<br>5. 搜索新建记录 | 经办人: AUTO_OUT_{ts} | 1. 创建成功<br>2. 新建记录可搜索到<br>3. 总数 >= 原先 + 1 | ✅ 已自动化 |
| TC-SOO-014 | 删除刚创建的出库记录 | warehouse | spare-out-order | P0 | 1. 前置 TC-SOO-013 已执行<br>2. 创建的出库记录存在 | 1. 搜索目标记录<br>2. 点击行内删除<br>3. 确认删除<br>4. 再次搜索 | 经办人: AUTO_OUT_{ts}（从 TC-SOO-013 获取） | 1. 删除成功<br>2. 记录不存在（`is_row_present` 返回 False） | ✅ 已自动化 |
| TC-SOO-015 | 新增出库-取消操作 | warehouse | spare-out-order | P1 | 页面加载完成 | 1. 点击新增<br>2. 填写经办人<br>3. 点击取消<br>4. 搜索该经办人 | 经办人: AUTO_CANCEL_{ts} | 取消后记录不存在 | ✅ 已自动化 |
| TC-SOO-016 | 新增出库-必填校验 | warehouse | spare-out-order | P1 | 页面加载完成 | 1. 点击新增<br>2. 不填写表单直接保存 | 无 | 1. 前端校验错误提示（若有）<br>2. 弹窗可能关闭或保持打开 | ✅ 已自动化 |
| TC-SOO-017 | 按日期搜索出库记录 | warehouse | spare-out-order | P1 | 1. 列表中存在日期范围内的记录 | 1. 选择日期范围<br>2. 点击查询 | 日期: 选择具体日期 | 搜索结果符合日期筛选条件 | ⚠️ 待开发 |
| TC-SOO-018 | 空数据状态显示 | warehouse | spare-out-order | P2 | 1. 当前搜索条件下无记录 | 1. 输入不存在的经办人<br>2. 点击查询 | 经办人: __NON_EXISTENT__ | 1. 表格显示空数据占位<br>2. 分页显示总数为 0 | ⚠️ 待开发 |
| TC-SOO-019 | 分页翻页操作 | warehouse | spare-out-order | P1 | 1. 列表数据超过一页 | 1. 点击下一页<br>2. 点击上一页 | 无 | 页面正常切换，数据加载正常 | ⚠️ 待开发 |
| TC-SOO-020 | 重置后搜索条件清空验证 | warehouse | spare-out-order | P1 | 1. 已输入搜索条件并执行搜索 | 1. 点击重置<br>2. 检查搜索输入框内容 | 无 | 搜索条件清空，表格恢复默认数据 | ⚠️ 待开发 |

**测试数据说明**:
- `AUTO_OUT_{ts}`: 时间戳后 6 位，用于新增测试的唯一经办人标识
- `AUTO_CANCEL_{ts}`: 时间戳后 5 位，用于取消测试的唯一经办人标识
- 时间戳格式: `str(int(time.time()))[-6:]` 和 `str(int(time.time()))[-5:]`

**清理策略**:
- 测试 `test_delete_created_out_order` 通过 `delete_by_handler` 移除创建的记录
- 删除失败时通过 `CleanupTracker` 注册回调兜底清理
- `cleanup_tracker` 的 `register_entity` 接收实体类型、名称、删除回调
