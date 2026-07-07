根据提供的 `PAGE_CONTEXT.md` 页面上下文，现为 `approval-history` 页面的配对测试生成测试数据种子。数据设计遵循了上下文中的测试数据设计要点，并严格匹配了每个 P0 用例及关键边界条件的验证需求。

---

### 配对测试数据种子 (`approval-history_test_data_seeds.json`)

```json
{
  "seeds": [
    {
      "id": "SEED-P0-01",
      "description": "P0：页面初始状态与查询加载 (S-01, S-03) - 无筛选条件查询",
      "test_case_ids": ["S-01", "S-03"],
      "priority": "P0",
      "category": "初始状态与基本交互",
      "filter_params": {},
      "expected_result": {
        "total_count_min": 50,
        "first_page_rows": 10,
        "should_show_loading": true,
        "query_btn_disables_during_load": true,
        "status_distribution": {
          "待审批": ">= 20",
          "审批中": ">= 20",
          "已通过": ">= 20",
          "已驳回": ">= 20"
        },
        "time_range_in_data": "记录时间跨度超过6个月"
      },
      "data_setup_notes": "确保数据库中有多于50条审批记录，且四种状态数据分布均匀。"
    },
    {
      "id": "SEED-P0-02",
      "description": "P0：时间范围-快捷选项筛选 - 最近7天 (S-05)",
      "test_case_ids": ["S-05"],
      "priority": "P0",
      "category": "筛选查询",
      "filter_params": {
        "timeRangeType": "quick",
        "quickOption": "last7Days"
      },
      "expected_result": {
        "total_count_min": 10,
        "all_records_within_7_days": true,
        "date_format": "YYYY-MM-DD HH:mm"
      },
      "data_setup_notes": "确保最近7天内有至少10条不同状态、不同类型的记录。"
    },
    {
      "id": "SEED-P0-03",
      "description": "P0：时间范围-快捷选项筛选 - 本月 (S-05)",
      "test_case_ids": ["S-05"],
      "priority": "P0",
      "category": "筛选查询",
      "filter_params": {
        "timeRangeType": "quick",
        "quickOption": "thisMonth"
      },
      "expected_result": {
        "total_count_min": 15,
        "all_records_within_current_month": true
      },
      "data_setup_notes": "确保当前月份内有至少15条记录，包含月初和月末的数据。"
    },
    {
      "id": "SEED-P0-04",
      "description": "P0：时间范围-自定义日期范围 - 有效范围 (S-06)",
      "test_case_ids": ["S-06"],
      "priority": "P0",
      "category": "筛选查询",
      "filter_params": {
        "timeRangeType": "custom",
        "startDate": "2024-01-01",
        "endDate": "2024-01-31"
      },
      "expected_result": {
        "total_count_min": 8,
        "all_records_in_2024_jan": true
      },
      "data_setup_notes": "确保2024年1月有至少8条记录。"
    },
    {
      "id": "SEED-P0-05",
      "description": "P0：时间范围-自定义日期范围 - 跨月范围 (S-06)",
      "test_case_ids": ["S-06"],
      "priority": "P0",
      "category": "筛选查询",
      "filter_params": {
        "timeRangeType": "custom",
        "startDate": "2024-01-15",
        "endDate": "2024-02-15"
      },
      "expected_result": {
        "total_count_min": 5,
        "all_records_in_specified_range": true
      },
      "data_setup_notes": "确保2024年1月15日至2月15日之间有至少5条记录。"
    },
    {
      "id": "SEED-P0-06",
      "description": "P0：时间范围-自定义日期范围 - 跨年范围 (S-06)",
      "test_case_ids": ["S-06"],
      "priority": "P0",
      "category": "筛选查询",
      "filter_params": {
        "timeRangeType": "custom",
        "startDate": "2023-12-15",
        "endDate": "2024-01-15"
      },
      "expected_result": {
        "total_count_min": 3,
        "all_records_in_cross_year_range": true
      },
      "data_setup_notes": "确保跨年时间段有至少3条记录。"
    },
    {
      "id": "SEED-P0-07",
      "description": "P0：状态多选筛选 - 单个状态‘已通过’ (S-08)",
      "test_case_ids": ["S-08"],
      "priority": "P0",
      "category": "筛选查询",
      "filter_params": {
        "status": ["已通过"]
      },
      "expected_result": {
        "total_count_min": 20,
        "all_status_are_passed": true
      },
      "data_setup_notes": "确保‘已通过’状态的数据大于20条。"
    },
    {
      "id": "SEED-P0-08",
      "description": "P0：状态多选筛选 - 多个状态组合‘待审批’和‘已驳回’ (S-08)",
      "test_case_ids": ["S-08"],
      "priority": "P0",
      "category": "筛选查询",
      "filter_params": {
        "status": ["待审批", "已驳回"]
      },
      "expected_result": {
        "total_count_min": 25,
        "all_statuses_match_filter": true
      },
      "data_setup_notes": "确保‘待审批’和‘已驳回’状态的数据总和大于25条。"
    },
    {
      "id": "SEED-P0-09",
      "description": "P0：组合筛选-时间+状态 (S-11)",
      "test_case_ids": ["S-11"],
      "priority": "P0",
      "category": "筛选查询",
      "filter_params": {
        "timeRangeType": "quick",
        "quickOption": "last30Days",
        "status": ["已通过"]
      },
      "expected_result": {
        "total_count_min": 10,
        "all_records_in_last_30_days_and_passed": true
      },
      "data_setup_notes": "确保最近30天内‘已通过’状态的数据大于10条。"
    },
    {
      "id": "SEED-P0-10",
      "description": "P0：组合筛选-时间+类型+发起人 (S-11)",
      "test_case_ids": ["S-11"],
      "priority": "P0",
      "category": "筛选查询",
      "filter_params": {
        "timeRangeType": "custom",
        "startDate": "2024-01-01",
        "endDate": "2024-03-31",
        "type": "报销审批",
        "initiator": "张伟"
      },
      "expected_result": {
        "total_count_min": 3,
        "all_records_match_all_filters": true
      },
      "data_setup_notes": "确保在指定时间范围内，由‘张伟’发起的‘报销审批’记录大于3条。"
    },
    {
      "id": "SEED-P0-11",
      "description": "P0：数据展示与格式验证 (S-13)",
      "test_case_ids": ["S-13"],
      "priority": "P0",
      "category": "数据展示",
      "filter_params": {},
      "expected_result": {
        "table_columns_visible": ["审批ID", "类型", "发起人", "状态", "发起时间", "操作"],
        "time_format_regex": "^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}$",
        "status_labels_styles_present": true,
        "specific_record_check": {
          "initiator": "张伟",
          "type": "报销审批",
          "status": "已通过",
          "time_exact": "2024-01-15 10:30"
        }
      },
      "data_setup_notes": "确保数据库中存在描述中指定的特定记录，并且有多条记录用于验证格式。"
    },
    {
      "id": "SEED-P0-12",
      "description": "P0：分页功能验证-多页数据 (S-15)",
      "test_case_ids": ["S-15"],
      "priority": "P0",
      "category": "分页",
      "filter_params": {},
      "expected_result": {
        "total_count_min": 50,
        "total_pages_calculated": "total_count / 10 (向上取整)",
        "page_navigation_works": true,
        "page_highlight_correct": true,
        "data_not_duplicated_across_pages": true
      },
      "data_setup_notes": "确保总数据量超过50条，以便至少生成5页数据（每页10条）。"
    },
    {
      "id": "SEED-P0-13",
      "description": "P0：行操作-详情跳转 (S-19)",
      "test_case_ids": ["S-19"],
      "priority": "P0",
      "category": "行操作",
      "filter_params": {},
      "expected_result": {
        "target_record_has_detail_btn": true,
        "click_redirects_to_detail_page": true,
        "url_contains_correct_approval_id": true,
        "detail_page_data_matches_list_summary": true
      },
      "data_setup_notes": "确保列表中存在至少一条记录，其‘详情’按钮可正常点击。"
    },
    {
      "id": "SEED-BOUNDARY-01",
      "description": "边界条件：时间范围无效输入-结束日期早于开始日期 (S-07)",
      "test_case_ids": ["S-07"],
      "priority": "P2",
      "category": "边界交互",
      "filter_params": {
        "timeRangeType": "custom",
        "startDate": "2024-03-01",
        "endDate": "2024-02-01"
      },
      "expected_result": {
        "should_prevent_query": true,
        "error_message_shown": true,
        "error_text_contains": "结束日期不能早于开始日期"
      }
    },
    {
      "id": "SEED-BOUNDARY-02",
      "description": "边界条件：时间范围无效输入-遥远未来日期 (S-07)",
      "test_case_ids": ["S-07"],
      "priority": "P2",
      "category": "边界交互",
      "filter_params": {
        "timeRangeType": "custom",
        "startDate": "2099-01-01",
        "endDate": "2099-12-31"
      },
      "expected_result": {
        "total_count": 0,
        "empty_state_visible": true
      }
    },
    {
      "id": "SEED-BOUNDARY-03",
      "description": "边界条件：组合筛选导致‘无结果’ (S-12)",
      "test_case_ids": ["S-12"],
      "priority": "P2",
      "category": "筛选查询",
      "filter_params": {
        "timeRangeType": "custom",
        "startDate": "2099-01-01",
        "endDate": "2099-12-31",
        "status": ["已通过"]
      },
      "expected_result": {
        "total_count": 0,
        "empty_state_visible": true,
        "pagination_shows_zero": true
      }
    },
    {
      "id": "SEED-BOUNDARY-04",
      "description": "边界条件：分页-无效页码输入 (S-16)",
      "test_case_ids": ["S-16"],
      "priority": "P1",
      "category": "分页",
      "filter_params": {
        "page_jump_input": ["abc", "0", "-1", "999999"]
      },
      "expected_result": {
        "invalid_input_rejected": true,
        "page_does_not_change_for_invalid_input": true,
        "page_jumps_to_last_page_for_overflow": true
      }
    },
    {
      "id": "SEED-BOUNDARY-05",
      "description": "边界条件：网络异常模拟 (S-22)",
      "test_case_ids": ["S-22"],
      "priority": "P1",
      "category": "异常与健壮性",
      "filter_params": {
        "simulate_network": "offline_or_timeout"
      },
      "expected_result": {
        "error_prompt_shown": true,
        "error_message_text": "网络异常，请稍后重试",
        "page_does_not_crash": true,
        "retry_action_possible": true
      },
      "data_setup_notes": "此数据种子用于在测试环境中模拟网络请求失败。"
    },
    {
      "id": "SEED-BOUNDARY-06",
      "description": "边界条件：特殊字符/XSS测试输入 (S-23)",
      "test_case_ids": ["S-23"],
      "priority": "P2",
      "category": "异常与健壮性",
      "filter_params": {
        "initiator_search_input": "<script>alert(1)</script>"
      },
      "expected_result": {
        "input_sanitized_or_rejected": true,
        "no_script_execution": true,
        "search_returns_zero_or_safe_error": true
      }
    }
  ]
}
```

### 使用说明

1.  **数据池准备**：执行测试前，需按照 `data_setup_notes` 中的说明在测试环境数据库中预先准备或核实基础数据。
2.  **字段匹配**：`filter_params` 中的字段名（如 `timeRangeType`, `status`, `initiator`）与自动化脚本中操作页面表单元素的ID或Name属性相对应。
3.  **预期结果**：`expected_result` 包含了断言所需的关键信息（如计数、状态、可见性），可直接用于编写自动化测试的断言（assert）部分。
4.  **种子分类**：
    *   `SEED-P0-*`：为P0核心用例生成的有效数据组合。
    *   `SEED-BOUNDARY-*`：为关键边界条件和异常场景生成的无效或特殊数据。