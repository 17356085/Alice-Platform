"""Child process for :mod:`aitest.platform.plugin_sandbox`."""

from __future__ import annotations

import importlib
import json
import sys


def main() -> int:
    if len(sys.argv) != 2 or ":" not in sys.argv[1]:
        return 2
    module_name, function_name = sys.argv[1].split(":", 1)
    try:
        function = getattr(importlib.import_module(module_name), function_name)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": f"entrypoint import failed: {exc}"}), flush=True)
        return 1
    for line in sys.stdin:
        try:
            message = json.loads(line)
            if message.get("op") == "stop":
                print(json.dumps({"status": "stopped"}), flush=True)
                return 0
            if message.get("op") == "ping":
                print(json.dumps({"status": "ready"}), flush=True)
                continue
            if message.get("op") == "invoke":
                result = function(message.get("payload", {}))
                print(json.dumps({"status": "ok", "result": result}, ensure_ascii=False, default=str), flush=True)
                continue
            print(json.dumps({"status": "error", "error": "unsupported operation"}), flush=True)
        except Exception as exc:
            print(json.dumps({"status": "error", "error": str(exc)}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
