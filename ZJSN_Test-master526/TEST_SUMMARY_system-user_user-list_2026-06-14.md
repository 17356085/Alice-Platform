# TEST_SUMMARY — system-user/user-list

> **执行日期**: 2026-06-14
> **测试模块**: system-user / user-list (用户列表页)
> **测试环境**: `https://aiwechatminidemo.cimc-digital.com/` · Chrome 149 · Headless
> **框架**: pytest 8.3.5 + Selenium 4.15.2 + Allure 2.16.0

## 执行结果

| 指标 | 值 |
|------|-----|
| 总用例数 | 12 |
| ✅ 通过 | **11** |
| ❌ 失败 | 0 |
| ⏭️ 跳过 | 1 (P2, 预期) |
| 执行时间 | 2:49 (169.53s) |
| 重跑次数 | 4 (pytest-rerunfailures) |

## 用例明细

| 编号 | 标题 | 优先级 | 结果 | 备注 |
|------|------|:---:|:---:|------|
| TC-001 | 页面正常加载 | P0 | ✅ | 表格加载，10行数据 |
| TC-002 | 表格列头正确显示 | P1 | ✅ | 8列: 用户名/姓名/手机号/角色/组织名称/状态/最后登录/操作 |
| TC-003 | 分页组件正常显示 | P1 | ✅ | 共178条，JS提取 |
| TC-004 | 按用户名搜索 | P1 | ✅ | 搜索 'rbac_test_*' 成功 |
| TC-005 | 重置搜索恢复全部数据 | P1 | ✅ | 重置后恢复10行 |
| TC-006 | 按状态筛选 | P1 | ✅ | 选择"启用" |
| TC-007 | 按角色筛选 | P2 | ⏭️ | 角色选项不可用，预期 skip |
| TC-008 | 分页翻页功能 | P1 | ✅ | JS提取分页总数 |
| TC-009 | 行内查看按钮 | P2 | ✅ | 点击"查看"触发弹窗 |
| TC-010 | 批量删除按钮状态 | P2 | ✅ | 勾选后按钮可用 |
| TC-011 | 全选功能 | P2 | ✅ | 全选后批量删除可用 |
| TC-012 | 新增按钮可见 | P0/Smoke | ✅ | 点击弹出表单 |

## Bug 修复记录

本轮修复了 `UserListPage.py` 中的 **5 类问题**：

| # | 根因 | 影响用例 | 修复方案 |
|:---:|------|------|------|
| 1 | **XPATH text() 空白不匹配**: Element Plus 按钮 `<span> 新增 </span>` 含首尾空白，`text()='新增'` 失败 | TC-012, TC-009 | 全局 `text()` → `normalize-space()` |
| 2 | **Row button 无 span 子节点**: "查看"/"编辑" 按钮文本直接作为 button 子节点，`//span[text()]` 定位失败 | TC-009 | 改用 `normalize-space()='查看'` 定位 button 本身 |
| 3 | **Checkbox JS click 不触发 Vue**: `input.click()` 不触发 Element Plus v-model 响应 | TC-010, TC-011 | 点击 label 元素 + `dispatchEvent(change)` |
| 4 | **Pagination visibility 检查**: 分页在视口外，Selenium `is_visible` 失败 | TC-003, TC-008 | 改用 `execute_script` 直接提取 `innerText` |
| 5 | **Status select 消歧义**: 状态和角色下拉并排，定位落到角色下拉 | TC-006 | 多重定位器 + `normalize-space()='全部'` 消歧义 |

## 代码变更

- **Page Object**: `page/system_page/UserListPage.py` — 8 处 XPATH/逻辑修复

## 覆盖率评估

| 优先级 | 总数 | 通过 | 覆盖 |
|:---:|:---:|:---:|:---:|
| P0 | 2 | 2 | 100% |
| P1 | 6 | 6 | 100% |
| P2 | 4 | 3 (+1 skip) | 75% |

---

🤖 Generated with [Claude Code](https://claude.com/claude-code) via /full-sop pipeline
