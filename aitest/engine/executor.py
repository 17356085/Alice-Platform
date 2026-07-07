"""Compatibility alias to the canonical executor module."""

import sys
from alice_engine.core import executor as _impl

sys.modules[__name__] = _impl
