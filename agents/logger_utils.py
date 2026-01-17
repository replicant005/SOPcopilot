from agents.models import PipelineState

from time import time
from typing import Any


def _now_ms() -> int:
    return int(time() * 1000)

def log_event_patch(agent: str, event: str, data: dict | None = None) -> dict[str, Any]:
    """
    Returns a patch that can be merged into PipelineState via the audit_log reducer.
    Use this in workers too (since it doesn't need state).
    """
    return {
        "audit_log": [{
            "ts_ms": _now_ms(),
            "agent": agent,
            "event": event,
            "data": data or {},
        }]
    }

def log_event(state: PipelineState, agent: str, event: str, data: dict | None = None) -> dict[str, Any]:
    """
    Convenience wrapper when you HAVE state.
    (Still returns a patch; don't mutate state in-place.)
    """
    return log_event_patch(agent, event, data)
