"""Tool: check_consistency (P1-2) — Zero-LLM 跨层一致性检查。"""
from aitest.mcp.error_taxonomy import ErrorCode, error_response
from aitest.consistency_checker import run_all_checks as _consistency_run_all_checks


def run_consistency_check() -> dict:
    """运行跨层一致性检查 (Zero-LLM Tool — 纯脚本，无 LLM 调用)。"""
    try:
        results = _consistency_run_all_checks()
    except Exception as e:
        return error_response(
            ErrorCode.EXECUTION_FAILED,
            f"Consistency check failed: {str(e)}",
            "检查 Python 环境和治理文档完整性。",
            retryable=False,
        )

    checks = []
    all_ok = True
    total_issues = 0
    for r in results:
        checks.append({
            "name": r.check,
            "ok": r.ok,
            "message": r.message,
            "details": r.details[:10],
        })
        if not r.ok:
            all_ok = False
            total_issues += len(r.details)

    return {
        "status": "pass" if all_ok else "fail",
        "total_checks": len(results),
        "passed_checks": sum(1 for r in results if r.ok),
        "failed_checks": sum(1 for r in results if not r.ok),
        "total_issues": total_issues,
        "checks": checks,
        "suggestion": (
            "所有跨层一致性检查通过" if all_ok
            else f"{total_issues} 个不一致项待修复。使用 'aitest check --consistency' CLI 命令查看完整报告。"
        ),
    }
