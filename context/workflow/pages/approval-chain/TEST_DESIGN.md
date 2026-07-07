```json
{
  "testDataSeed": {
    "metadata": {
      "moduleName": "workflow",
      "pageName": "approval-chain",
      "creationTimestamp": "2024-05-23T10:00:00Z",
      "description": "用于 workflow/approval-chain 页面的自动化测试数据种子。包含 P0 功能验证的有效数据与边界条件的无效数据。",
      "usageInstructions": "测试数据对象中的 `id`、`name`、`code` 等字段可作为测试脚本中的定位器、输入值或断言依据。"
    },
    "datasets": {
      "coreApprovalChains": [
        {
          "id": "AC-P0-001",
          "name": "采购审批链",
          "code": "PROCUREMENT-001",
          "status": "enabled",
          "nodeCount": 3,
          "description": "标准采购审批流程，用于核心流程验证。",
          "createdTime": "2024-01-10 09:00:00",
          "updatedTime": "2024-04-20 14:30:00"
        },
        {
          "id": "AC-P0-002",
          "name": "HR-Approval",
          "code": "HR-APPROVAL-ENG",
          "status": "disabled",
          "nodeCount": 2,
          "description": "人力资源审批链（英文命名）。",
          "createdTime": "2024-02-05 11:15:00",
          "updatedTime": "2024-05-01 16:45:00"
        },
        {
          "id": "AC-P0-003",
          "name": "IT-审批_v1.0",
          "code": "IT-APPROVAL-V1",
          "status": "enabled",
          "nodeCount": 4,
          "description": "包含特殊字符和版本号的IT审批链，用于验证特殊字符搜索与显示。",
          "createdTime": "2024-03-12 13:20:00",
          "updatedTime": "2024-05-10 08:10:00"
        },
        {
          "id": "AC-P0-004",
          "name": "财务 审批",
          "code": "FINANCE-WITH-SPACE",
          "status": "enabled",
          "nodeCount": 2,
          "description": "名称中包含空格的审批链，用于验证边界条件。",
          "createdTime": "2024-04-01 10:00:00",
          "updatedTime": "2024-05-15 09:30:00"
        },
        {
          "id": "AC-P0-005",
          "name": "审批链A",
          "code": "CHAIN-A",
          "status": "enabled",
          "nodeCount": 1,
          "description": "用于测试删除操作和状态切换的专用数据（启用状态）。",
          "createdTime": "2024-05-01 08:00:00",
          "updatedTime": "2024-05-18 17:00:00"
        },
        {
          "id": "AC-P0-006",
          "name": "审批链B",
          "code": "CHAIN-B",
          "status": "disabled",
          "nodeCount": 1,
          "description": "用于测试删除操作和状态切换的专用数据（禁用状态）。",
          "createdTime": "2024-05-01 08:05:00",
          "updatedTime": "2024-05-18 17:05:00"
        }
      ],
      "paginationTestData": {
        "description": "用于生成足够数据以测试分页功能。以下为前几条示例，实际需批量生成（如50条）。",
        "sampleRecords": [
          {
            "id": "AC-PAGE-001",
            "name": "分页测试审批链-001",
            "code": "PAGE-TEST-001",
            "status": "enabled",
            "nodeCount": 2,
            "createdTime": "2024-05-20 08:00:00",
            "updatedTime": "2024-05-20 08:00:00"
          },
          {
            "id": "AC-PAGE-002",
            "name": "分页测试审批链-002",
            "code": "PAGE-TEST-002",
            "status": "disabled",
            "nodeCount": 2,
            "createdTime": "2024-05-20 08:01:00",
            "updatedTime": "2024-05-20 08:01:00"
          }
        ]
      },
      "searchTestData": {
        "validKeywords": [
          { "keyword": "采购", "expectedMatchIds": ["AC-P0-001"], "scenario": "TC-SEARCH-01: 有效中文关键词" },
          { "keyword": "HR", "expectedMatchIds": ["AC-P0-002"], "scenario": "TC-SEARCH-01: 有效英文关键词" },
          { "keyword": "IT", "expectedMatchIds": ["AC-P0-003"], "scenario": "TC-FILTER-01: 组合查询中的关键词" }
        ],
        "invalidKeywords": [
          { "keyword": "test123xyz", "scenario": "TC-SEARCH-002: 无匹配结果" },
          { "keyword": "!@#$%^&*()", "scenario": "TC-SEARCH-005: 搜索特殊字符" },
          { "keyword": "ThisIsAVeryLongKeywordForTestingPurposesAndShouldExceedTypicalInputLimits", "scenario": "TC-SEARCH-006: 搜索超长字符串" }
        ]
      },
      "filterTestData": {
        "validStatuses": ["全部", "启用", "禁用"],
        "invalidStatuses": ["未知状态", ""]
      },
      "newEditFormData": {
        "valid": {
          "name": "新建测试审批链",
          "code": "NEW-TEST-CHAIN",
          "nodeCount": 2,
          "description": "这是通过自动化测试新建的审批链。"
        },
        "invalid": {
          "name": "这是一个测试新建功能时使用的超长名称字符串，旨在验证输入框对字符长度的限制处理能力，确保在超过预定长度时系统能够优雅地处理或给出明确提示。此名称已远超常规审批链命名规范。",
          "code": "INVALID-CODE-!@#$",
          "nodeCount": -1,
          "description": "包含特殊字符 & <script>alert('XSS')</script> 的描述，用于安全与输入过滤测试。"
        }
      },
      "paginationBoundaryTestData": {
        "validJumpPageNumbers": [
          { "targetPage": 2, "scenario": "TC-PAGINATE-003: 有效页码跳转" },
          { "targetPage": 1, "scenario": "TC-PAGINATE-005: 单页数据下的页码" }
        ],
        "invalidJumpPageNumbers": [
          { "targetPage": 0, "scenario": "TC-PAGINATE-004: 无效页码0" },
          { "targetPage": -1, "scenario": "TC-PAGINATE-004: 无效页码负数" },
          { "targetPage": 999, "scenario": "TC-PAGINATE-004: 无效页码超出总数" },
          { "targetPage": "abc", "scenario": "TC-PAGINATE-004: 无效页码非数字" }
        ]
      }
    }
  }
}
```