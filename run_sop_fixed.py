#!/usr/bin/env python3
"""库管 SOP 全量运行 + 修复验证"""

import subprocess
import sys
from pathlib import Path

WORKSTUDY = Path("D:/Desktop/WorkStudy")
OUTPUT_FILE = WORKSTUDY / "sop_output_warehouse_fixed.txt"

def run_sop():
    """运行 SOP"""
    cmd = [
        sys.executable, "-m", "aitest.graphs.sop_runner",
        "--module", "warehouse",
        "--mode", "from-requirement",
        "--output", str(OUTPUT_FILE),
    ]

    print(f"\n{'='*80}")
    print("启动库管 SOP（修复版）")
    print(f"{'='*80}\n")

    result = subprocess.run(cmd, cwd=str(WORKSTUDY))

    if result.returncode == 0:
        print(f"\n✓ SOP 完成，输出: {OUTPUT_FILE}")
        return True
    else:
        print(f"\n✗ SOP 失败 (code {result.returncode})")
        return False

if __name__ == "__main__":
    success = run_sop()
    sys.exit(0 if success else 1)
