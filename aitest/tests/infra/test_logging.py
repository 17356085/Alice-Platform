"""Tests for infra/logging.py — structured JSONL logging.

Tests: Logger creation, bind(), all levels, JSONL output, thread safety,
and crash-safety (logging error must never crash the app).
"""
import json
import threading
from pathlib import Path

import pytest
from aitest.infra.logging import Logger, get_logger, _write_entry, _LOG_FILE


# ══════════════════════════════════════════════════════════════════════════
#  Logger creation + singleton
# ══════════════════════════════════════════════════════════════════════════


class TestGetLogger:
    def test_returns_logger(self):
        log = get_logger("test_component")
        assert isinstance(log, Logger)

    def test_same_component_returns_same_instance(self):
        a = get_logger("test_singleton")
        b = get_logger("test_singleton")
        assert a is b

    def test_different_components_are_different(self):
        a = get_logger("comp_a")
        b = get_logger("comp_b")
        assert a is not b

    def test_default_bindings_empty(self):
        log = get_logger("fresh")
        assert log._bindings == {}


# ══════════════════════════════════════════════════════════════════════════
#  Logger.bind()
# ══════════════════════════════════════════════════════════════════════════


class TestBind:
    def test_bind_adds_context(self):
        log = get_logger("bind_test")
        ctx = log.bind(module="equipment", run_id="abc")
        assert ctx._bindings == {"module": "equipment", "run_id": "abc"}

    def test_bind_does_not_mutate_original(self):
        log = get_logger("bind_immutable")
        ctx = log.bind(page="alarm")
        assert log._bindings == {}
        assert ctx._bindings == {"page": "alarm"}

    def test_bind_chains(self):
        log = get_logger("bind_chain")
        ctx1 = log.bind(a=1)
        ctx2 = ctx1.bind(b=2)
        assert ctx1._bindings == {"a": 1}
        assert ctx2._bindings == {"a": 1, "b": 2}
        assert log._bindings == {}

    def test_bind_overrides_later(self):
        log = get_logger("bind_override")
        ctx = log.bind(module="old").bind(module="new")
        assert ctx._bindings == {"module": "new"}

    def test_bind_preserves_component(self):
        log = get_logger("bind_component")
        ctx = log.bind(x=1)
        assert ctx._component == "bind_component"


# ══════════════════════════════════════════════════════════════════════════
#  Log levels — all four
# ══════════════════════════════════════════════════════════════════════════


class TestLogLevels:
    """Smoke test each level — ensures no exceptions raised."""

    def test_debug(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.logging._LOG_DIR", temp_dir)
        monkeypatch.setattr("aitest.infra.logging._LOG_FILE", temp_dir / "app_log.jsonl")
        log = Logger("level_test")
        log.debug("debug_event", "debug msg", key="val")
        # Must not raise

    def test_info(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.logging._LOG_DIR", temp_dir)
        monkeypatch.setattr("aitest.infra.logging._LOG_FILE", temp_dir / "app_log.jsonl")
        log = Logger("level_test")
        log.info("info_event", "info msg", key="val")

    def test_warning(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.logging._LOG_DIR", temp_dir)
        monkeypatch.setattr("aitest.infra.logging._LOG_FILE", temp_dir / "app_log.jsonl")
        log = Logger("level_test")
        log.warning("warn_event", "warn msg", key="val")

    def test_error(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.logging._LOG_DIR", temp_dir)
        monkeypatch.setattr("aitest.infra.logging._LOG_FILE", temp_dir / "app_log.jsonl")
        log = Logger("level_test")
        log.error("error_event", "error msg", key="val")

    def test_bindings_merged_into_context(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.logging._LOG_DIR", temp_dir)
        monkeypatch.setattr("aitest.infra.logging._LOG_FILE", temp_dir / "app_log.jsonl")
        log = Logger("ctx_test", {"agent": "test-agent"})
        log.info("event_with_ctx", extra="data")
        # Must not raise


# ══════════════════════════════════════════════════════════════════════════
#  JSONL file output
# ══════════════════════════════════════════════════════════════════════════


class TestJsonlOutput:
    def test_writes_valid_jsonl(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.logging._LOG_DIR", temp_dir)
        log_file = temp_dir / "app_log.jsonl"
        monkeypatch.setattr("aitest.infra.logging._LOG_FILE", log_file)

        log = Logger("jsonl_test")
        log.info("event1", "message one", count=1)
        log.info("event2", "message two", count=2)

        assert log_file.exists()
        lines = log_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2

        for line in lines:
            entry = json.loads(line)
            assert "ts" in entry
            assert "level" in entry
            assert "component" in entry
            assert "event" in entry
            assert "msg" in entry

        e1 = json.loads(lines[0])
        assert e1["level"] == "INFO"
        assert e1["component"] == "jsonl_test"
        assert e1["event"] == "event1"
        assert e1["count"] == 1

    def test_context_appears_in_jsonl(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.logging._LOG_DIR", temp_dir)
        log_file = temp_dir / "app_log.jsonl"
        monkeypatch.setattr("aitest.infra.logging._LOG_FILE", log_file)

        log = get_logger("ctx_jsonl").bind(run_id="r123", module="equipment")
        log.info("phase_done", duration_ms=4200)

        entry = json.loads(log_file.read_text(encoding="utf-8").strip())
        assert entry["run_id"] == "r123"
        assert entry["module"] == "equipment"
        assert entry["duration_ms"] == 4200

    def test_error_level_written(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.logging._LOG_DIR", temp_dir)
        log_file = temp_dir / "app_log.jsonl"
        monkeypatch.setattr("aitest.infra.logging._LOG_FILE", log_file)

        log = Logger("err_test")
        log.error("crash", "something broke", error="ValueError")

        entry = json.loads(log_file.read_text(encoding="utf-8").strip())
        assert entry["level"] == "ERROR"
        assert entry["error"] == "ValueError"


# ══════════════════════════════════════════════════════════════════════════
#  Crash safety — logging must never crash the app
# ══════════════════════════════════════════════════════════════════════════


class TestCrashSafety:
    def test_write_to_nonexistent_dir_does_not_crash(self, temp_dir):
        """Logging to a path whose parent doesn't exist should not raise."""
        nonexistent = temp_dir / "nonexistent" / "subdir" / "log.jsonl"
        # _write_entry creates parent dirs via _ensure_dir()
        try:
            _write_entry("INFO", "crash_test", "test_event",
                         message="should not crash", _test_file=nonexistent)
        except Exception as exc:
            pytest.fail(f"_write_entry raised: {exc}")

    def test_write_to_readonly_dir_does_not_crash(self, temp_dir, monkeypatch):
        """Permission errors during file write should be silently ignored."""
        readonly = temp_dir / "readonly"
        readonly.mkdir()
        log_file = readonly / "app_log.jsonl"
        # Create an unwritable file (read-only)
        log_file.write_text("")
        log_file.chmod(0o444)
        readonly.chmod(0o444)  # make dir read-only too

        monkeypatch.setattr("aitest.infra.logging._LOG_FILE", log_file)
        monkeypatch.setattr("aitest.infra.logging._LOG_DIR", readonly)

        # Must not raise despite permission error
        try:
            _write_entry("INFO", "crash_test", "readonly_event",
                         message="this should silently fail")
        except Exception as exc:
            pytest.fail(f"_write_entry raised on readonly dir: {exc}")
        finally:
            readonly.chmod(0o755)
            log_file.chmod(0o644)


# ══════════════════════════════════════════════════════════════════════════
#  Thread safety
# ══════════════════════════════════════════════════════════════════════════


class TestThreadSafety:
    def test_concurrent_writes_do_not_crash(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.logging._LOG_DIR", temp_dir)
        monkeypatch.setattr("aitest.infra.logging._LOG_FILE", temp_dir / "app_log.jsonl")

        log = Logger("thread_test")
        errors = []

        def write_logs(n: int):
            try:
                for i in range(n):
                    log.info("concurrent", f"msg_{i}", thread=threading.get_ident())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write_logs, args=(20,)) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Logging crashed in thread: {errors}"

    def test_concurrent_get_logger_is_safe(self):
        """get_logger with same name across threads returns same instance."""
        instances = []

        def fetch():
            instances.append(get_logger("concurrent_singleton"))

        threads = [threading.Thread(target=fetch) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should be the same instance
        first = instances[0]
        for inst in instances:
            assert inst is first
