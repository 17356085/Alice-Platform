"""Worker mTLS configuration validation tests."""

import os

import pytest

from aitest.platform.worker_mtls import WorkerMTLSError, load_worker_tls_config


def test_optional_worker_mtls_is_disabled_without_paths(monkeypatch):
    for name in ("AITEST_WORKER_TLS_CA", "AITEST_WORKER_TLS_CERT", "AITEST_WORKER_TLS_KEY"):
        monkeypatch.delenv(name, raising=False)
    assert load_worker_tls_config(required=False) is None


def test_required_worker_mtls_requires_all_files(monkeypatch):
    monkeypatch.delenv("AITEST_WORKER_TLS_CA", raising=False)
    monkeypatch.delenv("AITEST_WORKER_TLS_CERT", raising=False)
    monkeypatch.delenv("AITEST_WORKER_TLS_KEY", raising=False)
    with pytest.raises(WorkerMTLSError, match="required"):
        load_worker_tls_config(required=True)


def test_worker_mtls_validates_private_key_permissions(monkeypatch, tmp_path):
    paths = [tmp_path / name for name in ("ca.pem", "cert.pem", "key.pem")]
    for path in paths:
        path.write_text("test", encoding="utf-8")
    for name, path in zip(("AITEST_WORKER_TLS_CA", "AITEST_WORKER_TLS_CERT", "AITEST_WORKER_TLS_KEY"), paths):
        monkeypatch.setenv(name, os.fspath(path))
    if os.name != "nt":
        paths[2].chmod(0o644)
        with pytest.raises(WorkerMTLSError, match="private key"):
            load_worker_tls_config(required=True)
        paths[2].chmod(0o600)
    assert load_worker_tls_config(required=True).key_file == paths[2]
