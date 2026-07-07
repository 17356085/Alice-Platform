根据提供的 `PAGE_CONTEXT.md` 和测试设计文档，我将为 `workflow` 模块的 `approval-chain` 页面生成配对测试数据种子。数据设计遵循目标：为每个 P0（高优先级）用例生成有效数据，为每个边界条件生成无效数据，并确保数据格式与表单字段匹配。

以下是生成的测试数据种子文件 `TEST_DATA_SEED.json`：

```json
{
  "module": "workflow",
  "page": "approval-chain",
  "version": "1.0",
  "generatedAt": "2024-10-27T10:00:00Z",
  "description": "为 approval-chain 页面生成的配对测试数据种子，覆盖 P0 用例和边界条件。",
  "data": [
    {
      "testCaseId": "TC-SEARCH-01",
      "description": "使用有效关键词搜索（P0）",
      "type": "positive",
      "preconditions": [
        "数据库中已存在至少一条审批链记录"
      ],
      "testData": {
        "keyword": "采购审批"
      },
      "assertions": [
        "列表仅显示名称或编码包含'采购审批'的记录"
      ]
    },
    {
      "testCaseId": "TC-SEARCH-02",
      "description": "搜索无匹配结果",
      "type": "negative",
      "testData": {
        "keyword": "test123xyz_not_exist"
      },
      "assertions": [
        "列表显示'无数据'或为空",
        "无报错"
      ]
    },
    {
      "testCaseId": "TC-SEARCH-05",
      "description": "搜索特殊字符（边界条件）",
      "type": "boundary",
      "testData": {
        "keyword": "!@#$%^&*"
      },
      "assertions": [
        "系统不报错，界面正常响应",
        "列表因无匹配而显示为空或'无数据'"
      ]
    },
    {
      "testCaseId": "TC-SEARCH-06",
      "description": "搜索超长字符串（边界条件）",
      "type": "boundary",
      "testData": {
        "keyword": "长字符串超过输入框最大长度限制的字符串重复多次_长字符串超过输入框最大长度限制的字符串重复多次_长字符串超过输入框最大长度限制的字符串重复多次"
      },
      "assertions": [
        "输入框能正常处理（截断或滚动显示）",
        "搜索功能正常执行，无页面崩溃"
      ]
    },
    {
      "testCaseId": "TC-SEARCH-04",
      "description": "按状态筛选列表（P0）",
      "type": "positive",
      "preconditions": [
        "数据库中存在至少一条'启用'和一条'禁用'状态的审批链记录"
      ],
      "testData": {
        "status": "启用"
      },
      "assertions": [
        "列表仅显示状态为'启用'的数据"
      ]
    },
    {
      "testCaseId": "TC-FILTER-01",
      "description": "组合查询（搜索+状态）（P0）",
      "type": "positive",
      "preconditions": [
        "数据库中存在名称包含'财务'且状态为'禁用'的审批链记录"
      ],
      "testData": {
        "keyword": "财务",
        "status": "禁用"
      },
      "assertions": [
        "列表仅显示名称包含'财务'且状态为'禁用'的数据"
      ]
    },
    {
      "testCaseId": "TC-LIST-ADD-01",
      "description": "新建审批链（P0）",
      "type": "positive",
      "testData": {
        "name": "自动化测试新建审批链",
        "code": "AUTO-NEW-001",
        "status": "启用",
        "nodeCount": 3,
        "description": "用于测试新建功能的审批链数据"
      },
      "assertions": [
        "成功创建新审批链",
        "列表自动刷新并显示新建的数据"
      ]
    },
    {
      "testCaseId": "TC-LIST-EDIT-01",
      "description": "编辑已有审批链（P0）",
      "type": "positive",
      "preconditions": [
        "数据库中已存在一条用于编辑的测试数据（ID或唯一标识）"
      ],
      "testData": {
        "targetRecordId": "PREPARED_FOR_EDIT_001",
        "updatedFields": {
          "name": "自动化测试编辑后的审批链",
          "nodeCount": 4
        }
      },
      "assertions": [
        "编辑页面正确预填充现有信息",
        "保存后列表显示更新后的数据"
      ]
    },
    {
      "testCaseId": "TC-LIST-DELETE-02",
      "description": "确认删除（P0）",
      "type": "positive",
      "preconditions": [
        "数据库中已存在一条专门用于删除的测试数据（ID或唯一标识）"
      ],
      "testData": {
        "targetRecordId": "PREPARED_FOR_DELETE_001",
        "confirmAction": "confirm"
      },
      "assertions": [
        "显示'删除成功'提示",
        "该数据从列表中移除"
      ]
    },
    {
      "testCaseId": "TC-LIST-TOGGLE-01",
      "description": "停用启用状态的审批链（P0）",
      "type": "positive",
      "preconditions": [
        "数据库中已存在一条状态为'启用'的审批链记录"
      ],
      "testData": {
        "targetRecordId": "ENABLED_RECORD_001",
        "action": "disable"
      },
      "assertions": [
        "操作成功提示",
        "数据状态变为'禁用'",
        "操作按钮文字变为'启用'"
      ]
    },
    {
      "testCaseId": "TC-LIST-TOGGLE-02",
      "description": "启用禁用状态的审批链（P0）",
      "type": "positive",
      "preconditions": [
        "数据库中已存在一条状态为'禁用'的审批链记录"
      ],
      "testData": {
        "targetRecordId": "DISABLED_RECORD_001",
        "action": "enable"
      },
      "assertions": [
        "操作成功提示",
        "数据状态变为'启用'",
        "操作按钮文字变为'停用'"
      ]
    },
    {
      "testCaseId": "TC-PAGINATE-01",
      "description": "翻页（P0）",
      "type": "positive",
      "preconditions": [
        "数据库中存在超过10条（默认每页条数）审批链记录"
      ],
      "testData": {
        "action": "nextPage"
      },
      "assertions": [
        "列表数据刷新为下一页数据",
        "分页信息更新（如'2/2页'）"
      ]
    },
    {
      "testCaseId": "TC-PAGINATE-02",
      "description": "切换每页显示条数（P0）",
      "type": "positive",
      "preconditions": [
        "数据库中存在超过10条审批链记录"
      ],
      "testData": {
        "newPageSize": 20
      },
      "assertions": [
        "列表立即刷新，每页显示20条数据",
        "总页数相应减少"
      ]
    },
    {
      "testCaseId": "TC-PAGINATE-03",
      "description": "页码跳转（P0）",
      "type": "positive",
      "preconditions": [
        "数据库中存在至少20条审批链记录（确保至少2页）"
      ],
      "testData": {
        "targetPage": 2
      },
      "assertions": [
        "列表跳转到第2页",
        "显示第2页对应数据"
      ]
    },
    {
      "testCaseId": "TC-PAGINATE-04",
      "description": "无效页码跳转（边界条件）",
      "type": "boundary",
      "testData": {
        "targetPage": "abc"
      },
      "assertions": [
        "系统阻止跳转",
        "输入框恢复原值或清空，或给出提示"
      ]
    },
    {
      "testCaseId": "TC-LIST-DELETE-05",
      "description": "删除后分页更新",
      "type": "positive",
      "preconditions": [
        "当前有3页数据，目标在第二页"
      ],
      "testData": {
        "currentPage": 2,
        "targetRecordId": "RECORD_ON_PAGE2_001",
        "confirmAction": "confirm"
      },
      "assertions": [
        "数据从列表移除",
        "总记录数减1，总页数可能减1",
        "分页信息实时更新"
      ]
    },
    {
      "testCaseId": "TC-PAGINATE-05",
      "description": "单页数据分页状态",
      "type": "boundary",
      "testData": {
        "setup": {
          "recordCount": 3
        },
        "expected": {
          "paginationText": "共3条，1/1页",
          "prevButtonDisabled": true,
          "nextButtonDisabled": true
        }
      },
      "assertions": [
        "分页组件显示'共3条，1/1页'",
        "'上一页'、'下一页'按钮为禁用状态"
      ]
    },
    {
      "testCaseId": "NEW_DATA_BASE",
      "description": "基础审批链数据（支持多项测试）",
      "type": "seed",
      "testData": [
        {
          "id": "BASE_001",
          "name": "采购审批链",
          "code": "PROC-001",
          "status": "启用",
          "nodeCount": 5,
          "updatedAt": "2024-10-26"
        },
        {
          "id": "BASE_002",
          "name": "HR-Approval",
          "code": "HR-APV-002",
          "status": "启用",
          "nodeCount": 3,
          "updatedAt": "2024-10-25"
        },
        {
          "id": "BASE_003",
          "name": "财务 审批",
          "code": "FIN-003",
          "status": "禁用",
          "nodeCount": 4,
          "updatedAt": "2024-10-24"
        },
        {
          "id": "BASE_004",
          "name": "IT-审批_v1.0",
          "code": "IT-APV-004",
          "status": "启用",
          "nodeCount": 2,
          "updatedAt": "2024-10-23"
        },
        {
          "id": "BASE_005",
          "name": "长字符串超过输入框最大长度限制的字符串重复多次_长字符串超过输入框最大长度限制的字符串重复多次_长字符串超过输入框最大长度限制的字符串重复多次",
          "code": "LONG-005",
          "status": "禁用",
          "nodeCount": 6,
          "updatedAt": "2024-10-22"
        }
      ]
    }
  ],
  "executionNotes": {
    "dependencies": [
      "数据库中需要预先存在一些基础记录（参考 NEW_DATA_BASE 种子数据）",
      "部分用例（如编辑、删除、状态切换）的 'targetRecordId' 需要在测试执行前替换为实际存在的记录ID"
    ],
    "usageGuide": [
      "自动化脚本可以遍历 'data' 数组，根据 'testCaseId' 和 'type' 选择对应的测试数据。",
      "对于 'seed' 类型的数据，通常用于测试环境初始化或作为测试操作的基础数据集。",
      "测试前请根据实际环境ID调整 'targetRecordId' 等值。"
    ]
  }
}
```

**使用说明**：
1.  **P0 用例覆盖**：为每个标记为 P0 的核心功能（如有效搜索、新建、编辑、删除确认、状态切换、翻页等）提供了有效的测试数据。
2.  **边界条件覆盖**：为搜索特殊字符、搜索超长字符串、无效页码跳转、单页分页状态等边界场景提供了无效或特殊的测试数据。
3.  **数据初始化**：`NEW_DATA_BASE` 提供了5条具有代表性的基础审批链记录，用于确保测试环境有合适的数据分布（不同名称格式、不同状态）。
4.  **自动化友好**：数据以结构化 JSON 格式提供，每个测试数据对象都关联了测试用例ID、类型和断言，自动化脚本可以直接解析并驱动测试。
5.  **环境适配**：部分数据（如 `targetRecordId`）需要在实际测试环境中替换为真实的记录ID，这是自动化脚本执行前的常规配置步骤。