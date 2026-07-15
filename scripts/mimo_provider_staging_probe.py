"""Run a minimal real MiMo provider contract probe.

Only fixed public health-check text is sent.  This script deliberately does
not load project files, governance prompts, skills, or workspace context.
"""

from __future__ import annotations

import json

from alice_engine.providers.mimo import MiMoProvider


def main() -> None:
    response = MiMoProvider().complete(
        "You are a staging health probe.",
        "Reply with exactly: staging-ok",
        temperature=0,
        max_tokens=16,
    )
    print(json.dumps({
        "status": "ok" if response.finish_reason != "error" else "error",
        "model": response.model,
        "finish_reason": response.finish_reason,
        "token_usage": response.token_usage,
        "content_length": len(response.content),
    }, ensure_ascii=False))
    if response.finish_reason == "error":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
