"""
P3-3: SOP Gate Checker → MCP Tool
封装 check_sop_gate.py，Agent 启动前自动检查门禁。
"""
import json
import subprocess

from aitest.mcp.config import SOP_GATE_SCRIPT, ZJSN_TEST
from aitest.mcp.error_taxonomy import ErrorCode, error_response


def check_sop_gate(module: str = "", agent: str = "") -> dict:
    """运行 SOP 门禁检查，返回 gate pass/blocked 状态。"""
    if not SOP_GATE_SCRIPT.exists():
        # 脚本不存在时，做基础的文档存在性检查
        return _fallback_gate_check(module, agent)

    cmd = ["python", str(SOP_GATE_SCRIPT), "--json"]
    if module:
        cmd.extend(["--module", module])
    if agent:
        cmd.extend(["--agent", agent])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                                cwd=str(ZJSN_TEST), encoding='utf-8', errors='replace')
        if result.returncode == 0 and result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                data["status"] = "ok"
                return data
            except json.JSONDecodeError:
                pass

        # 非零退出码或无效 JSON——尝试解析 stdout 作为结果
        output = (result.stdout or "").strip() or (result.stderr or "").strip()
        return {
            "status": "ok",
            "gate": "unknown",
            "message": f"Gate script exited with code {result.returncode}",
            "raw_output": output[:500],
            "suggestion": "检查门禁脚本输出以确定具体阻塞项。",
        }
    except subprocess.TimeoutExpired:
        return error_response(ErrorCode.EXECUTION_TIMEOUT, "SOP gate check timed out",
                              "基础门禁检查应在 30s 内完成。", retryable=True)
    except Exception as e:
        return error_response(ErrorCode.INTERNAL_ERROR, f"Gate check error: {str(e)}",
                              "回退到基础文档存在性检查。", retryable=False)


def _fallback_gate_check(module: str, agent: str) -> dict:
    """当 check_sop_gate.py 不存在时的回退门禁检查。"""
    from aitest.mcp.config import CONTEXT_MODULES
    missing = []
    module_dir = CONTEXT_MODULES / module if module else None

    if module and module_dir and module_dir.exists():
        if not (module_dir / "MODULE_CONTEXT.md").exists():
            missing.append("MODULE_CONTEXT.md")
        if agent == "automation-agent":
            pages_dir = module_dir / "pages"
            if pages_dir.exists():
                for page_dir in sorted(pages_dir.iterdir()):
                    if page_dir.is_dir():
                        if not (page_dir / "PAGE_CONTEXT.md").exists():
                            missing.append(f"pages/{page_dir.name}/PAGE_CONTEXT.md")
                        if not (page_dir / "TEST_CASES.md").exists():
                            missing.append(f"pages/{page_dir.name}/TEST_CASES.md")

    if missing:
        return {
            "status": "ok", "gate": "blocked",
            "missing": missing,
            "suggestion": f"缺失 {len(missing)} 个前置文档。使用 run_sop module={module} 从头编排。",
            "fallback": True,
        }
    return {
        "status": "ok", "gate": "pass",
        "message": f"基础门禁通过 (module={module}, agent={agent})",
        "fallback": True,
    }
