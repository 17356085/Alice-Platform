"""数据清理配置

更新记录:
    2026-06-15: v2.0 — 扩展 batch_clean_urls 14→43，覆盖全模块
"""
CLEANUP_CONFIG = {
    # ── 总开关 ──
    "enabled": True,

    # ── 默认清理方式 ──
    "preferred_method": "api",       # "api" | "ui" | "callback"

    # ── API 超时 ──
    "api_timeout": 10,

    # ── 测试数据命名前缀规则（用于离线扫描识别残留） ──
    "test_prefix_rules": {
        "name": "TC-",
        "code": "TEST",
        "remark": "[AUTO]",
    },

    # ── CI 残留阈值 ──
    "max_residual_allowed": 50,

    # ── 各模块批量删除 API 端点映射 ──
    # 格式: entity_type → DELETE API URL (使用 {id} 占位符)
    "batch_clean_urls": {
        # ── 系统管理 ──
        "dict":             "/api/system/dict/type/{id}",
        "dict_data":        "/api/system/dict/data/{id}",
        "user":             "/api/system/user/{id}",
        "role":             "/api/system/role/{id}",
        "menu":             "/api/system/menu/{id}",
        "dept":             "/api/system/dept/{id}",
        "org":              "/api/system/dept/{id}",       # 别名
        "post":             "/api/system/post/{id}",
        "notice":           "/api/system/notice/{id}",
        "params":           "/api/system/params/{id}",

        # ── 设备管理 ──
        "unit":             "/api/equipment/unit/{id}",
        "device":           "/api/equipment/device/{id}",
        "equipment":        "/api/equipment/device/{id}",  # 别名
        "alarm_config":     "/api/equipment/alarm-config/{id}",
        "maintenance":      "/api/equipment/maintenance/{id}",
        "sensor":           "/api/equipment/sensor/{id}",

        # ── 人员管理 ──
        "employee":         "/api/personnel/employee/{id}",
        "course":           "/api/personnel/training/course/{id}",
        "question":         "/api/personnel/training/question/{id}",
        "paper":            "/api/personnel/training/paper/{id}",
        "exam":             "/api/personnel/training/exam/{id}",
        "train_plan":       "/api/personnel/training/plan/{id}",
        "certificate":      "/api/personnel/certificate/{id}",
        "contractor_unit":  "/api/personnel/contractor/unit/{id}",
        "contractor_personnel": "/api/personnel/contractor/personnel/{id}",

        # ── 销售管理 ──
        "customer":         "/api/sales/customer/{id}",
        "contract":         "/api/sales/contract/{id}",
        "sales_order":      "/api/sales/sales-order/{id}",

        # ── 化验管理 ──
        "lab_report":       "/api/lab/report/{id}",

        # ── 生产管理 ──
        "business_type":    "/api/production/business-type/{id}",
        "shift_team":       "/api/production/shift-team/{id}",

        # ── 储罐管理 ──
        "tank_alarm":       "/api/tank/alarm-config/{id}",

        # ── 库管管理 ──
        "hazard_item":      "/api/warehouse/hazard-item/{id}",
        "hazard_in_order":  "/api/warehouse/hazard-in-order/{id}",
        "hazard_out_order": "/api/warehouse/hazard-out-order/{id}",
        "spare_item":       "/api/warehouse/spare-item/{id}",
        "spare_in_order":   "/api/warehouse/spare-in-order/{id}",
        "spare_out_order":  "/api/warehouse/spare-out-order/{id}",
        "spare_requisition":"/api/warehouse/spare-requisition/{id}",
        "reagent_item":     "/api/warehouse/reagent-item/{id}",
        "reagent_fill":     "/api/warehouse/reagent-fill/{id}",
    },

    # ── 只读实体（不生成清理 URL，走 callback/UI 兜底） ──
    "readonly_entities": [
        "camera", "key_param", "monitor",            # equipment 只读
        "gas_indicator", "water_indicator",           # lab 指标配置
        "gas_compare", "water_compare",               # lab 对比
        "daily_report", "monthly_report",             # 报表
        "tank_monitor", "tank_report",                # tank 监控/报表
        "login_log", "operation_log", "system_log",   # 日志
        "timed_task", "monitor_management",           # 运维
    ],

    # ── 例外规则 ──
    "skip_patterns": ["readonly_", "init_"],
}
