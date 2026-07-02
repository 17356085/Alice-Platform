"""Audit 单元测试。"""

import pytest
from alice_engine.audit import (
    check_output_safety,
    attribute_failure,
    OnlineMonitor,
    CostAuditor,
    KPICollector,
    QALoop,
    StepEfficiencyAnalyzer,
    ReviewTrigger,
)


class TestSafetyAuditor:
    """SafetyAuditor 测试。"""

    def test_check_output_safety_clean(self):
        """测试安全内容。"""
        flags = check_output_safety("def hello(): print('world')")
        assert len(flags) == 0

    def test_check_output_safety_password(self):
        """测试硬编码密码。"""
        flags = check_output_safety('password = "secret123"')
        assert len(flags) > 0
        assert any(f.severity == "high" for f in flags)

    def test_check_output_safety_eval(self):
        """测试 eval() 调用。"""
        flags = check_output_safety("eval('print(1)')")
        assert len(flags) > 0
        assert any(f.severity == "critical" for f in flags)


class TestFailureAttributor:
    """FailureAttributor 测试。"""

    def test_attribute_failure_unknown(self):
        """测试未知失败。"""
        class MockObs:
            raw_output_full = "some error"

        category = attribute_failure(MockObs(), "some generic error message")
        assert category.category == "unknown"

    def test_attribute_failure_prompt(self):
        """测试 prompt 相关失败。"""
        class MockObs:
            raw_output_full = ""

        category = attribute_failure(MockObs(), "context exceeded token limit")
        assert category.category == "prompt"


class TestOnlineMonitor:
    """OnlineMonitor 测试。"""

    def test_online_monitor_init(self, tmp_path):
        """测试 OnlineMonitor 初始化。"""
        monitor = OnlineMonitor(data_dir=tmp_path)
        assert monitor.data_dir == tmp_path


class TestCostAuditor:
    """CostAuditor 测试。"""

    def test_cost_auditor_init(self, tmp_path):
        """测试 CostAuditor 初始化。"""
        auditor = CostAuditor(data_dir=tmp_path)
        assert len(auditor.records) == 0

    def test_cost_auditor_record(self, tmp_path):
        """测试记录成本。"""
        auditor = CostAuditor(data_dir=tmp_path)
        auditor.record_cost("test-agent", 1000, 500, "claude-sonnet-4-6")
        assert len(auditor.records) == 1
        assert auditor.total_cost() > 0
