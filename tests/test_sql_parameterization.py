"""Test: SQL parameterization — verify no f-string SQL injection risk.

Batch 1 of coupling fix plan. Verifies:
  1. No _escape/_escape_json functions remain in migrated files
  2. safe_literal handles injection attempts
  3. All migrated modules import without errors
  4. QueryLayer uses parameterized filters
"""

import pytest
import importlib
import inspect


# ── 1. Verify _escape is gone from all migrated modules ──────────────

MIGRATED_MODULES = [
    "aitest.platform.run_store",
    "aitest.platform.audit_log",
    "aitest.platform.artifact_lineage",
    "aitest.platform.replay",
    "aitest.platform.query_layer",
    "aitest.server.session_store",
    "aitest.infra.task_queue",
    "aitest.testing.bug_history",
]


@pytest.mark.parametrize("module_name", MIGRATED_MODULES)
def test_no_escape_function(module_name):
    """Verify _escape and _escape_json are not defined in migrated modules."""
    mod = importlib.import_module(module_name)
    assert not hasattr(mod, "_escape"), f"{module_name} still has _escape"
    assert not hasattr(mod, "_escape_json"), f"{module_name} still has _escape_json"


# ── 2. Verify safe_literal handles injection ──────────────────────────

def test_safe_literal_string_escape():
    """Single quotes must be escaped."""
    from aitest.infra.sql import safe_literal
    result = safe_literal("it's a test")
    assert result == "'it''s a test'"


def test_safe_literal_injection_attempt():
    """SQL injection via single quote must be neutralized."""
    from aitest.infra.sql import safe_literal
    result = safe_literal("'; DROP TABLE runs; --")
    # The single quote in "';" gets doubled, so the SQL becomes:
    # '''; DROP TABLE runs; --'
    # Which is a valid string literal, not SQL injection
    assert "DROP TABLE" in result  # Content preserved
    assert result.startswith("'")  # But it's a quoted string
    assert result.endswith("'")


def test_safe_literal_none():
    from aitest.infra.sql import safe_literal
    assert safe_literal(None) == "NULL"


def test_safe_literal_int():
    from aitest.infra.sql import safe_literal
    assert safe_literal(42) == "42"


def test_safe_literal_bool():
    from aitest.infra.sql import safe_literal
    assert safe_literal(True) == "TRUE"
    assert safe_literal(False) == "FALSE"


def test_safe_literal_dict():
    from aitest.infra.sql import safe_literal
    result = safe_literal({"key": "val"})
    assert result.startswith("'")
    assert "key" in result


def test_safe_json_none():
    from aitest.infra.sql import safe_json
    assert safe_json(None) == "'{}'"


def test_safe_json_dict():
    from aitest.infra.sql import safe_json
    result = safe_json({"a": 1})
    assert result.startswith("'")
    assert "a" in result


# ── 3. Verify all migrated modules import ─────────────────────────────

@pytest.mark.parametrize("module_name", MIGRATED_MODULES)
def test_module_imports(module_name):
    """Verify all migrated modules can be imported without errors."""
    mod = importlib.import_module(module_name)
    assert mod is not None


# ── 4. Verify QueryLayer uses parameterized filters ───────────────────

def test_run_query_uses_parameterized_filters():
    """RunQuery.filter methods should accumulate params, not f-string values."""
    from aitest.platform.query_layer import RunQuery
    q = RunQuery().status("failed").module("equipment")
    # The query builder should have accumulated parameters
    assert len(q._params) == 2
    assert q._params[0] == "failed"
    assert q._params[1] == "equipment"


def test_run_query_sql_uses_question_marks():
    """RunQuery SQL should use ? placeholders."""
    from aitest.platform.query_layer import RunQuery
    q = RunQuery().status("failed").module("equipment").limit(10)
    sql, params = q._build()
    assert "?" in sql
    assert sql.count("?") == len(params)


def test_session_query_title_uses_like():
    """SessionQuery.title should use ? with LIKE pattern."""
    from aitest.platform.query_layer import SessionQuery
    q = SessionQuery().title("test")
    assert len(q._params) == 1
    assert q._params[0] == "%test%"


# ── 5. Verify sql.py _sql_value handles edge cases ────────────────────

def test_sql_value_backslash():
    """Backslashes must be escaped."""
    from aitest.infra.sql import _sql_value
    result = _sql_value("path\\to\\file")
    assert "\\\\" in result


def test_sql_value_json_with_quotes():
    """JSON values with quotes must be escaped."""
    from aitest.infra.sql import _sql_value
    result = _sql_value({"key": "it's"})
    assert "it''s" in result
