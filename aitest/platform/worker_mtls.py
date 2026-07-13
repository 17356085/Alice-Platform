"""mTLS configuration and certificate validation for remote Workers.

The module deliberately owns configuration/validation only. TLS termination is
performed by the deployment ingress or uvicorn process using these paths.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class WorkerMTLSError(ValueError):
    """Raised when required Worker mTLS configuration is invalid."""


@dataclass(frozen=True)
class WorkerTLSConfig:
    ca_file: Path
    cert_file: Path
    key_file: Path
    required: bool = True

    def validate(self) -> None:
        for label, path in (("CA", self.ca_file), ("certificate", self.cert_file), ("private key", self.key_file)):
            if not path.is_file():
                raise WorkerMTLSError(f"Worker mTLS {label} file does not exist: {path}")
            if path.stat().st_size == 0:
                raise WorkerMTLSError(f"Worker mTLS {label} file is empty: {path}")
        if os.name != "nt":
            mode = self.key_file.stat().st_mode & 0o077
            if mode:
                raise WorkerMTLSError("Worker mTLS private key must not be group/world readable")


def load_worker_tls_config(*, required: bool | None = None) -> WorkerTLSConfig | None:
    required = required if required is not None else os.environ.get("AITEST_WORKER_MTLS_REQUIRED", "0").lower() in {"1", "true", "yes"}
    values = [os.environ.get(name, "") for name in ("AITEST_WORKER_TLS_CA", "AITEST_WORKER_TLS_CERT", "AITEST_WORKER_TLS_KEY")]
    if not any(values):
        if required:
            raise WorkerMTLSError("Worker mTLS is required but CA/certificate/key are not configured")
        return None
    if not all(values):
        raise WorkerMTLSError("Worker mTLS requires CA, certificate and private key")
    config = WorkerTLSConfig(*(Path(value).expanduser() for value in values), required=required)
    config.validate()
    return config
