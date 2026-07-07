# 配对测试数据种子生成 (approval-todo)

根据提供的 `PAGE_CONTEXT.md` 和对页面结构的分析，已为关键测试场景生成配对测试数据种子。数据设计遵循用户要求，为推断的 P0 场景提供有效数据，并为边界条件提供无效数据，格式与页面表单字段匹配。

---

## 测试数据种子文件 (JSON)

```json
{
  "page": "approval-todo",
  "generatedAt": "2023-10-27T10:00:00Z",
  "description": "测试数据种子用于 approval-todo 页面的自动化测试。包含筛选、操作、分页等场景的有效及无效数据。",
  "testData": {
    "filterValid": {
      "description": "用于筛选功能测试的有效数据组合",
      "cases": [
        {
          "id": "FILTER_V01",
          "name": "按单个流程类型筛选",
          "filterData": {
            "processType": "请假申请",
            "status": "",
            "keyword": "",
            "startDate": null,
            "endDate": null
          },
          "expectedResult": "表格仅显示‘请假申请’类型的待办记录"
        },
        {
          "id": "FILTER_V02",
          "name": "按状态筛选",
          "filterData": {
            "processType": "",
            "status": "待我审批",
            "keyword": "",
            "startDate": null,
            "endDate": null
          },
          "expectedResult": "表格仅显示状态为‘待我审批’的记录"
        },
        {
          "id": "FILTER_V03",
          "name": "按关键词模糊搜索",
          "filterData": {
            "processType": "",
            "status": "",
            "keyword": "项目A",
            "startDate": null,
            "endDate": null
          },
          "expectedResult": "表格仅显示关键词包含‘项目A’的记录"
        },
        {
          "id": "FILTER_V04",
          "name": "按日期范围筛选",
          "filterData": {
            "processType": "",
            "status": "",
            "keyword": "",
            "startDate": "2023-10-01",
            "endDate": "2023-10-31"
          },
          "expectedResult": "表格仅显示创建日期在2023年10月内的记录"
        },
        {
          "id": "FILTER_V05",
          "name": "组合筛选（流程类型+状态）",
          "filterData": {
            "processType": "报销审批",
            "status": "已同意",
            "keyword": "",
            "startDate": null,
            "endDate": null
          },
          "expectedResult": "表格仅显示‘报销审批’类型且状态为‘已同意’的记录"
        }
      ]
    },
    "filterInvalid": {
      "description": "用于测试筛选器边界条件或错误处理的无效数据",
      "cases": [
        {
          "id": "FILTER_I01",
          "name": "无效的关键词（特殊字符/超长）",
          "filterData": {
            "processType": "",
            "status": "",
            "keyword": "!@#$%^&*()_+~`|}{[]:;?><,./-=",
            "startDate": null,
            "endDate": null
          },
          "expectedResult": "查询返回空结果或页面无报错，显示空状态"
        },
        {
          "id": "FILTER_I02",
          "name": "无效的日期范围（开始日期 > 结束日期）",
          "filterData": {
            "processType": "",
            "status": "",
            "keyword": "",
            "startDate": "2023-11-01",
            "endDate": "2023-10-01"
          },
          "expectedResult": "日期选择器可能提示错误，或查询返回空结果"
        }
      ]
    },
    "operationValid": {
      "description": "用于单条记录操作（同意、拒绝、详情）的有效数据（需确保记录状态为‘待我审批’）",
      "cases": [
        {
          "id": "OP_V01",
          "name": "单条记录-同意",
          "targetRecord": {
            "id": "REC-001",
            "processType": "请假申请",
            "applicant": "张三",
            "createTime": "2023-10-25",
            "status": "待我审批"
          },
          "operation": "agree",
          "expectedResult": "操作成功提示，记录状态变为‘已同意’或从待办列表中消失"
        },
        {
          "id": "OP_V02",
          "name": "单条记录-拒绝",
          "targetRecord": {
            "id": "REC-002",
            "processType": "报销审批",
            "applicant": "李四",
            "createTime": "2023-10-24",
            "status": "待我审批"
          },
          "operation": "reject",
          "expectedResult": "操作成功提示，记录状态变为‘已拒绝’或从待办列表中消失"
        },
        {
          "id": "OP_V03",
          "name": "单条记录-查看详情",
          "targetRecord": {
            "id": "REC-003",
            "processType": "出差申请",
            "applicant": "王五",
            "createTime": "2023-10-23",
            "status": "待我审批"
          },
          "operation": "viewDetail",
          "expectedResult": "页面跳转至详情页，URL包含记录ID参数"
        }
      ]
    },
    "batchOperationValid": {
      "description": "用于批量操作测试的有效数据（需多选多条‘待我审批’状态的记录）",
      "cases": [
        {
          "id": "BATCH_V01",
          "name": "批量同意",
          "selectedRecords": [
            {"id": "REC-010", "status": "待我审批"},
            {"id": "REC-011", "status": "待我审批"},
            {"id": "REC-012", "status": "待我审批"}
          ],
          "operation": "batchApprove",
          "expectedResult": "操作成功提示，所有选中记录状态更新或从待办列表消失"
        },
        {
          "id": "BATCH_V02",
          "name": "批量拒绝",
          "selectedRecords": [
            {"id": "REC-020", "status": "待我审批"},
            {"id": "REC-021", "status": "待我审批"}
          ],
          "operation": "batchReject",
          "expectedResult": "操作成功提示，所有选中记录状态更新或从待办列表消失"
        }
      ]
    },
    "batchOperationInvalid": {
      "description": "用于测试批量操作边界条件的无效数据或场景",
      "cases": [
        {
          "id": "BATCH_I01",
          "name": "未选择记录时点击批量操作",
          "selectedRecords": [],
          "operation": "batchApprove",
          "precondition": "无任何记录被选中",
          "expectedResult": "批量操作按钮应为禁用状态（disabled），点击无效"
        },
        {
          "id": "BATCH_I02",
          "name": "选择非‘待我审批’状态的记录进行操作",
          "selectedRecords": [
            {"id": "REC-030", "status": "已同意"},
            {"id": "REC-031", "status": "已拒绝"}
          ],
          "operation": "batchApprove",
          "expectedResult": "操作应失败，给出‘只能操作待审批记录’的提示"
        }
      ]
    },
    "paginationValid": {
      "description": "用于分页功能测试的数据（需确保总条数 > 单页条数，如总数15，每页10）",
      "cases": [
        {
          "id": "PAGE_V01",
          "name": "默认分页状态",
          "dataState": "总记录数 >= 15",
          "expectedResult": "第一页显示10条，分页器显示‘共 15 条’，‘下一页’按钮可用，‘上一页’按钮禁用"
        },
        {
          "id": "PAGE_V02",
          "name": "点击下一页",
          "precondition": "当前在第一页",
          "action": "点击‘下一页’按钮",
          "expectedResult": "表格加载第二页数据（第11-15条），‘上一页’按钮变为可用"
        }
      ]
    }
  }
}
```

---

## 使用说明

1.  **数据对应关系**：
    *   `filterValid.cases`：对应筛选器功能的 P0 测试场景（有效筛选组合）。
    *   `filterInvalid.cases`：对应筛选器输入边界的测试场景。
    *   `operationValid.cases`：对应表格行级操作（同意/拒绝/详情）的 P0 测试场景。
    *   `batchOperationValid.cases`：对应批量操作功能的 P0 测试场景。
    *   `batchOperationInvalid.cases`：对应批量操作前置条件校验的边界测试场景。
    *   `paginationValid.cases`：对应分页功能的 P0 测试场景。

2.  **在自动化脚本中使用**：
    *   **前置数据准备**：在执行需要特定数据的用例（如 `OP_V01`, `BATCH_V01`）前，可通过 API 调用或数据库脚本，根据 `targetRecord` 或 `selectedRecords` 中的 `id` 创建或重置相应状态的数据。
    *   **筛选器测试**：将 `filterData` 对象中的值分别填入页面对应字段的输入框/下拉框中，然后触发查询。
    *   **操作测试**：根据 `operation` 字段，在表格中定位到对应 `id` 的行，执行单击操作按钮。批量操作时，根据 `selectedRecords` 列表中的 `id` 选中对应行的复选框。
    *   **断言**：使用 `expectedResult` 字段作为断言的预期结果。

3.  **数据管理建议**：
    *   **环境隔离**：建议为自动化测试配置独立的测试环境或测试数据集，避免与开发、生产数据混淆。
    *   **数据重置**：在执行会修改数据的测试用例（如同意、拒绝）后，应有机制（如执行特定 API）将数据恢复到初始状态，确保用例可重复执行。
    *   **数据覆盖**：此数据种子覆盖了页面的主要功能点。在实际实施中，可能需要根据详细的 `TEST_CASES.md` 中的具体用例 ID 和步骤进行微调或扩充。