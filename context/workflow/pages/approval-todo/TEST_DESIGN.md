好的，这是根据提供的 `approval-todo` 页面上下文生成的配对测试数据种子文件。

该文件为页面的核心交互场景设计了测试数据，旨在与测试用例（`TEST_CASES.md`）配对使用。数据格式匹配页面表单字段。

```json
{
  "module": "workflow",
  "page": "approval-todo",
  "description": "审批待办页面测试数据种子",
  "lastUpdated": "2023-10-27",
  "testDataSeeds": [
    {
      "id": "seed-filter-01",
      "name": "有效筛选查询",
      "category": "P0",
      "preConditions": {
        "description": "确保系统中存在至少5条记录，覆盖多种流程类型和状态",
        "records": [
          { "processType": "请假申请", "status": "待我审批", "title": "张三请假申请", "applicant": "张三", "createdDate": "2023-10-26" },
          { "processType": "请假申请", "status": "已同意", "title": "李四请假申请", "applicant": "李四", "createdDate": "2023-10-25" },
          { "processType": "报销审批", "status": "待我审批", "title": "王五差旅费报销", "applicant": "王五", "createdDate": "2023-10-24" },
          { "processType": "采购申请", "status": "已拒绝", "title": "赵六采购申请", "applicant": "赵六", "createdDate": "2023-10-23" },
          { "processType": "报销审批", "status": "待我审批", "title": "钱七会议费报销", "applicant": "钱七", "createdDate": "2023-10-22" }
        ]
      },
      "actions": [
        {
          "field": "processType",
          "value": "请假申请",
          "selector": "[data-testid=\"filter-processType\"]"
        },
        {
          "field": "status",
          "value": "待我审批",
          "selector": "[data-testid=\"filter-status\"]"
        },
        {
          "field": "query",
          "selector": "button:has-text('查询')"
        }
      ],
      "expectedResult": {
        "filteredRecords": [
          { "title": "张三请假申请", "status": "待我审批" }
        ],
        "totalCount": 1
      }
    },
    {
      "id": "seed-batch-01",
      "name": "批量操作-同意",
      "category": "P0",
      "preConditions": {
        "description": "确保存在3条状态为‘待我审批’的记录",
        "records": [
          { "processType": "请假申请", "status": "待我审批", "id": "batch-p-01" },
          { "processType": "报销审批", "status": "待我审批", "id": "batch-p-02" },
          { "processType": "请假申请", "status": "待我审批", "id": "batch-p-03" }
        ]
      },
      "actions": [
        { "type": "selectRow", "id": "batch-p-01" },
        { "type": "selectRow", "id": "batch-p-02" },
        { "type": "click", "selector": "[data-testid=\"btn-batch-approve\"]" },
        { "type": "confirmDialog", "action": "confirm" }
      ],
      "expectedResult": {
        "successMessage": "批量操作成功",
        "remainingRecords": [
          { "id": "batch-p-03", "status": "待我审批" }
        ]
      }
    },
    {
      "id": "seed-single-01",
      "name": "单条操作-同意",
      "category": "P0",
      "preConditions": {
        "description": "确保存在1条状态为‘待我审批’的记录",
        "records": [
          { "processType": "报销审批", "status": "待我审批", "id": "single-p-01" }
        ]
      },
      "actions": [
        { "type": "clickAction", "rowId": "single-p-01", "action": "同意" }
      ],
      "expectedResult": {
        "successMessage": "操作成功",
        "recordStatusChange": { "id": "single-p-01", "newStatus": "已同意" }
      }
    },
    {
      "id": "seed-page-01",
      "name": "分页导航",
      "category": "P0",
      "preConditions": {
        "description": "确保列表总记录数为15条，每页显示10条",
        "totalRecords": 15,
        "records": "生成15条不同ID的待办记录"
      },
      "actions": [
        { "type": "click", "selector": ".ant-pagination-next" }
      ],
      "expectedResult": {
        "currentPage": 2,
        "totalPages": 2,
        "recordsOnPage2": 5,
        "prevButtonDisabled": false,
        "nextButtonDisabled": true
      }
    },
    {
      "id": "seed-filter-invalid-01",
      "name": "筛选条件-无效关键词输入",
      "category": "边界条件",
      "preConditions": {
        "description": "系统存在多条记录",
        "records": "正常预置数据"
      },
      "actions": [
        {
          "field": "keyword",
          "value": "<script>alert('xss')</script>",
          "selector": "[data-testid=\"filter-keyword\"]"
        },
        {
          "field": "query",
          "selector": "button:has-text('查询')"
        }
      ],
      "expectedResult": {
        "filteredRecords": "无匹配结果或显示警告提示",
        "noXSSExecution": true
      }
    },
    {
      "id": "seed-filter-invalid-02",
      "name": "筛选条件-无效日期范围",
      "category": "边界条件",
      "preConditions": {
        "description": "系统存在多条记录",
        "records": "正常预置数据"
      },
      "actions": [
        {
          "field": "startDate",
          "value": "2023-10-27",
          "selector": "[data-testid=\"filter-startDate\"]"
        },
        {
          "field": "endDate",
          "value": "2023-10-20",
          "selector": "[data-testid=\"filter-endDate\"]"
        },
        {
          "field": "query",
          "selector": "button:has-text('查询')"
        }
      ],
      "expectedResult": {
        "errorMessage": "结束日期不能早于开始日期",
        "queryNotExecuted": true
      }
    },
    {
      "id": "seed-filter-invalid-03",
      "name": "筛选条件-重置所有",
      "category": "边界条件",
      "preConditions": {
        "description": "已设置筛选条件并执行过查询",
        "currentState": {
          "processType": "请假申请",
          "keyword": "测试"
        }
      },
      "actions": [
        { "type": "click", "selector": "button:has-text('重置')" }
      ],
      "expectedResult": {
        "processTypeValue": null,
        "statusValue": null,
        "keywordValue": "",
        "startDateValue": null,
        "endDateValue": null,
        "tableData": "恢复到初始全量数据状态"
      }
    }
  ]
}
```

**使用说明：**

1.  **配对使用**：此文件中的每个 `seed` 对象都应与 `TEST_CASES.md` 中的一个或多个测试用例（P0或边界条件）相关联。使用时，脚本可根据用例ID引用对应的种子ID。
2.  **`preConditions`**：描述了测试开始前需要通过API、数据库操作或UI预置创建的数据环境。自动化脚本应在测试用例的 `beforeEach` 或 `before` 钩子中实现这些前置条件。
3.  **`actions`**：定义了测试数据在页面表单或控件中的具体输入和操作。`selector` 字段基于 `PAGE_CONTEXT.md` 中推断的元素定位器（如 `data-testid`），在实际脚本中需根据最终DOM进行确认和调整。
4.  **`expectedResult`**：提供了用于断言（`assert`）的预期结果数据点，与 `TEST_CASES.md` 中的验证点对应。
5.  **数据管理**：在真实测试中，`preConditions` 中的数据预置和测试后的清理工作，应遵循 `PAGE_CONTEXT.md` 中建议的“测试前初始化”和“测试后清理”策略，以确保用例独立性和环境确定性。