"""Backward-compatible state machine facade for legacy imports/tests."""

from alice_engine.core.state_machine import *  # noqa: F401,F403
from alice_engine.core.state_machine import register_legacy_event_emitter


def emit(event_type: str, data=None, **kwargs):
    return {"type": event_type, "data": data or kwargs}


def _dispatch(event_type: str, data=None, **kwargs):
    return emit(event_type, data, **kwargs)


register_legacy_event_emitter(_dispatch)
