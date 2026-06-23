# TEST_DESIGN — workflow（工作流管理 5 页面）

> 基于 3 轮测试执行反馈 | 2026-06-15
> 从 system/TEST_DESIGN.md 提取工作流相关用例

## 一、测试范围

| 页面 | 路由 | 用例数 | 覆盖策略 |
| --- | --- |:---:| --- |
| 待我审批 | `#/system/workflow/todo` | 8 | 页面展示 + 搜索(工厂/日期) + 重置 + 分页 + 详情 + 审批操作 |
| 我已审批 | `#/system/workflow/history` | 7 | 页面展示 + 搜索(状态/工厂/日期) + 重置 + 分页 + 详情 |
| 我发起的 | `#/system/workflow/my-applications` | 8 | 页面展示 + 搜索(工厂/日期) + 重置 + 分页 + 详情 + 撤回 |
| 审批链配置 | `#/system/workflow/approval-chain` | 6 | 页面展示 + 搜索(已有数据) + 编辑描述 + 重置 + 分页 + 表单验证 |
| SAP推送日志 | `#/system/workflow/sap-push-log` | 6 | 页面展示 + 搜索(状态/日期) + 重置 + 分页 + 详情 |
| **合计** | | **35** | |

## 二、测试策略

### 分层策略

| 层级 | 内容 | 当前状态 |
|:---:| --- |:---:|
| **L1 — 冒烟** | 页面加载 + 基本元素展示 | ✅ 5/5 页面通过 |
| **L2 — 功能** | 搜索/筛选/新增/编辑/删除/审批 | ✅ 5/5 文件零失败 |
| **L3 — 边界** | 空值提交/分页边界/特殊字符 | ✅ 审批链表单验证通过 |
| **L4 — 异常** | 网络超时/接口错误/并发冲突 | ⚪ 未覆盖（需 Mock） |

### 数据策略

| 策略 | 说明 |
| --- | --- |
| **先创建后搜索** | 测试依赖自己创建的数据（`unique_name()`），测试间通过 click_reset 恢复 |
| **数据不存在则 skip** | 搜索前检查数据是否存在，不存在 → `pytest.skip()` |
| **独立运行 > 全量回归** | 全量回归时数据竞态（前序删除影响后续），优先关注单文件结果 |
| **状态筛选项** | 仅测试页面实际存在的选项（如"已通过""已驳回"），不假设全量选项 |

## 三、测试用例速查

### 审批链配置（6 cases — 仅操作已有数据）

> ⚠️ 不新增不删除：审批链为生产预配置数据，自动化仅验证已有数据的展示/搜索/编辑描述/表单校验

| ID | 用例 | 类型 | 结果 |
|:---|------|:---:|:---:|
| SY-APCHAIN-01 | 页面展示+表头校验 | smoke | ✅ |
| SY-APCHAIN-04 | 按名称搜索（已有数据第一行名称） | functional | ✅ |
| SY-APCHAIN-05 | 编辑审批链描述 | functional | ✅ |
| SY-APCHAIN-07 | 重置按钮 | functional | ✅ |
| SY-APCHAIN-08 | 分页跳转 | boundary | ✅ |
| SY-APCHAIN-09 | 空名称提交→表单验证（弹窗不实际创建） | validation | ✅ |

### 待我审批（8 cases）

| ID | 用例 | 类型 | 结果 |
|:---|------|:---:|:---:|
| SY-TODO-01 | 页面展示+表头校验 | smoke | ✅ |
| SY-TODO-02 | 按工厂代码搜索 | functional | ✅ |
| SY-TODO-03 | 按审批状态筛选 | functional | ⏭️ skip |
| SY-TODO-04 | 按日期范围搜索 | functional | ✅ |
| SY-TODO-05 | 重置按钮 | functional | ✅ |
| SY-TODO-06 | 分页跳转 | boundary | ⏭️ skip |
| SY-TODO-07 | 查看详情弹窗 | functional | ✅ |
| SY-TODO-08 | 审批通过+填写意见 | functional | ✅ |

### 我已审批（7 cases）

| ID | 用例 | 类型 | 结果 |
|:---|------|:---:|:---:|
| SY-HIST-01 | 页面展示+表头校验 | smoke | ✅ |
| SY-HIST-02 | 按工厂代码搜索 | functional | ✅ |
| SY-HIST-03 | 按审批状态筛选 | functional | ✅ |
| SY-HIST-04 | 按日期范围搜索 | functional | ✅ |
| SY-HIST-05 | 重置按钮 | functional | ✅ |
| SY-HIST-06 | 分页跳转 | boundary | ⏭️ skip |
| SY-HIST-07 | 查看详情弹窗 | functional | ✅ |

### 我发起的（8 cases）

| ID | 用例 | 类型 | 结果 |
|:---|------|:---:|:---:|
| SY-MYAPP-01 | 页面展示+表头校验 | smoke | ✅ |
| SY-MYAPP-02 | 按工厂代码搜索 | functional | ✅ |
| SY-MYAPP-03 | 按审批状态筛选 | functional | ⏭️ skip |
| SY-MYAPP-04 | 按日期范围搜索 | functional | ✅ |
| SY-MYAPP-05 | 重置按钮 | functional | ✅ |
| SY-MYAPP-06 | 分页跳转 | boundary | ⏭️ skip |
| SY-MYAPP-07 | 查看详情弹窗 | functional | ✅ |
| SY-MYAPP-08 | 撤回申请 | functional | ⏭️ skip |

### SAP推送日志（6 cases）

| ID | 用例 | 类型 | 结果 |
|:---|------|:---:|:---:|
| SY-SAPLOG-01 | 页面展示+表头校验 | smoke | ✅ |
| SY-SAPLOG-02 | 按推送状态筛选 | functional | ⏭️ skip |
| SY-SAPLOG-03 | 按日期范围搜索 | functional | 🔴 全量回归fail |
| SY-SAPLOG-04 | 重置按钮 | functional | 🔴 全量回归fail |
| SY-SAPLOG-05 | 分页跳转 | boundary | ✅ |
| SY-SAPLOG-06 | 查看详情弹窗 | functional | ✅ |

### 端到端（4 cases — 跨模块: workflow + warehouse）

| ID | 用例 | 类型 | 结果 |
|:---|------|:---:|:---:|
| TC-WF-001 | 备品领用申请→审批通过→状态验证 | e2e | ✅ |
| TC-WF-002 | 备品领用申请→审批驳回→状态验证 | e2e | ✅ |
| TC-WF-004 | 端到端：提交→审批→历史记录验证 | e2e | ✅ |
| TC-WF-005 | 端到端：提交→我发起的→状态联动 | e2e | ✅ |

## 四、分组运行建议

```bash
# 冒烟（快速反馈，≤3min）
pytest script/workflow/ -m smoke -v

# 功能回归（全量，~10min）
pytest script/workflow/test_approval_chain.py -v --tb=short     # 核心：审批链CRUD
pytest script/workflow/test_approval_todo.py test_approval_history.py \
       test_my_application.py -v --tb=short                      # 工作流页面

# SAP（单独跑，避免 interceptor 干扰）
pytest script/workflow/test_sap_push_log.py -v

# 端到端（双浏览器）
pytest script/workflow/test_workflow_e2e.py -v
```

## 五、已知局限

1. **L4 异常测试未覆盖**：网络超时/接口错误/并发冲突需 Mock 框架支持
2. **跨页面数据流测试**：完整的"创建审批链→提交申请→审批→查看历史"流程仅部分串联
3. **SAP集成测试**：SAP推送需要SAP环境配合，当前仅验证日志展示
4. **全量回归数据竞态**：5个文件串行跑时存在数据竞争（RM-WF-020），建议分组运行
