"""设备报警配置页面测试数据

包含新增、编辑、搜索、边界值等场景的测试数据常量。
"""
from datetime import datetime


# ── 时间戳 —— 用于生成唯一的测试数据 ─────────────────────────────
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# ── 新增规则测试数据 ────────────────────────────────────────────────

ADD_REQUIRED_ONLY = {
    "alarm_name": f"autotest_required_{TIMESTAMP}",
    "alarm_type": "设备报警",
    "alarm_level": "一般",
    # device 为设备名称，需动态获取（取第一个可用设备）
}

ADD_ALL_FIELDS = {
    "alarm_name": f"autotest_all_{TIMESTAMP}",
    "device": None,  # 选第一个可用设备
    "alarm_type": "设备报警",
    "alarm_level": "紧急",
    "threshold_low": 10,
    "threshold_high": 100,
    "notify_mode": "短信通知",
    "enabled": True,
    "remark": "自动化测试-全部字段新增",
}

ADD_CANCEL = {
    "alarm_name": f"autotest_cancel_{TIMESTAMP}",
    "alarm_type": "设备报警",
    "alarm_level": "一般",
}

# ── 编辑规则测试数据 ────────────────────────────────────────────────

EDIT_DATA = {
    "alarm_name": f"autotest_edited_{TIMESTAMP}",
    "threshold_low": 5,
    "threshold_high": 50,
    "notify_mode": "邮件通知",
}

# ── 搜索测试数据 ────────────────────────────────────────────────────

SEARCH_KEYWORD_FOUND = "autotest"
SEARCH_KEYWORD_NOT_FOUND = f"zzz_no_such_alarm_{TIMESTAMP}"

# ── 边界值测试数据 ────────────────────────────────────────────────

BOUNDARY_THRESHOLD_EQUAL = {
    "alarm_name": f"autotest_bound_equal_{TIMESTAMP}",
    "device": None,
    "alarm_type": "设备报警",
    "alarm_level": "一般",
    "threshold_low": 50,
    "threshold_high": 50,
}

BOUNDARY_THRESHOLD_LOW_GT_HIGH = {
    "threshold_low": 100,
    "threshold_high": 10,
}

BOUNDARY_LONG_NAME = "测" * 100

# ── 异常测试数据 ────────────────────────────────────────────────────

EXCEPTION_DUPLICATE_NAME = "出差"  # 假设测试环境中存在此名称的规则

EXCEPTION_EMPTY_REQUIRED = {
    "alarm_type": "",   # 不填
    "alarm_level": "",  # 不填
}

# ── 重复提交测试数据 ────────────────────────────────────────────────

DUP_SUBMIT_DATA = {
    "alarm_name": f"autotest_dup_{TIMESTAMP}",
    "device": None,
    "alarm_type": "设备报警",
    "alarm_level": "一般",
}

# ── 预期提示文本 ────────────────────────────────────────────────────

EXPECTED_TOAST_ADD_SUCCESS = "新增成功"
EXPECTED_TOAST_EDIT_SUCCESS = "修改成功"
EXPECTED_TOAST_DELETE_SUCCESS = "删除成功"

EXPECTED_TABLE_HEADERS = [
    "报警名称", "关联设备", "报警类型", "报警级别",
    "阈值条件", "通知方式", "状态", "创建时间", "操作",
]

EXPECTED_TABLE_HEADER_SET = set(EXPECTED_TABLE_HEADERS)

EXPECTED_STAT_CARD_LABELS = [
    "报警规则总数", "已启用", "今日报警", "已禁用",
]
