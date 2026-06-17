"""
Run SOP for a single module — thin wrapper over SOPRunner.
用法: python tools/run_sop_module.py <module> [mode] [pages...]
示例: python tools/run_sop_module.py warehouse from-requirement
输出: <workspace>/sop_output_<module>.txt
"""
import sys
import io
from pathlib import Path

WORKSTUDY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSTUDY))

# Fix Windows GBK encoding + tee to file
out_path = WORKSTUDY / f"sop_output_{sys.argv[1] if len(sys.argv) > 1 else 'unknown'}.txt"
_file_out = open(str(out_path), "w", encoding="utf-8")

class TeeWriter:
    def __init__(self, *files):
        self.files = files
    def write(self, s):
        for f in self.files:
            f.write(s)
            f.flush()
    def flush(self):
        for f in self.files:
            f.flush()

sys.stdout = TeeWriter(
    io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace'),
    _file_out,
)

from aitest.graphs.sop_runner import SOPRunner


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/run_sop_module.py <module> [mode] [pages...]")
        print("  mode: full | resume | from-requirement | from-test-design | from-automation")
        sys.exit(1)

    module = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "from-requirement"
    pages = sys.argv[3:] if len(sys.argv) > 3 else []

    print(f"SOP: {module} | mode={mode} | pages={pages or '(auto-discover)'}")
    print("Output: " + str(out_path))
    print("=" * 80)

    runner = SOPRunner(module=module, pages=pages, mode=mode)

    for event in runner.run_interactive():
        etype = event.type
        content = event.content[:500] if event.content else ""

        if etype == "sop_start":
            print(f"\n[START] {content}")
        elif etype == "sop_phase":
            progress = event.progress or {}
            step = progress.get("step", 0)
            total = progress.get("total", 9)
            bar = "[" + "=" * step + " " * (total - step) + "]"
            st = {"running": "[RUN]", "pass": "[PASS]", "fail": "[FAIL]"}.get(event.status, "[?]")
            print(f"  {st} {bar} {content}")
        elif etype == "interaction_required":
            # Read interrupt options and pick the most permissive one
            options = getattr(event, 'interaction_options', []) or []
            if not options:
                options = ["approve"]  # fallback
            # Prefer: approve > force_continue > proceed > first option
            preferred = [o for o in options if o in ("approve", "force_continue", "proceed", "accept")]
            choice = preferred[0] if preferred else options[0]
            print(f"\n[HITL] {content}")
            print(f"  -> auto-response: '{choice}' (options: {options})")
            runner.send_interaction(choice)
        elif etype == "sop_complete":
            status = event.status
            print(f"\n{'='*80}")
            print(f"[DONE] SOP {status.upper()}: {content}")
            if event.error:
                print(f"  Error: {event.error[:500]}")
        elif etype == "agent_message":
            print(f"  [MSG] {content}")
        else:
            if content:
                print(f"  [{etype}] {content}")

    print("\nDone.")
    _file_out.close()


if __name__ == "__main__":
    main()
