"""
Bug History — PostgreSQL 历史 Bug 库 + 趋势分析. v3.1

v3.1: Uses parameterized queries via aitest.infra.sql (no more f-string SQL).
"""

import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path
from aitest.infra.sql import safe_exec, safe_query


def add_bug(module: str, page: str = "", test_name: str = "", error_type: str = "",
            error_message: str = "", root_cause: str = "", severity: str = "medium",
            status: str = "open", matched_issue: str = "", fix_description: str = "",
            fix_files: str = "", regression_risk: str = "low", tags: list[str] = None) -> str:
    bug_id = f"BUG-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
    now = time.time()
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_exec(
        "INSERT INTO bugs (id, date, module, page, test_name, error_type, error_message, "
        "root_cause, severity, status, matched_issue, fix_description, fix_files, "
        "regression_risk, tags, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [bug_id, date_str, module, page, test_name, error_type, error_message,
         root_cause, severity, status, matched_issue, fix_description, fix_files,
         regression_risk, ', '.join(tags or []), now, now],
    )
    return bug_id


def update_bug(bug_id: str, **kwargs) -> bool:
    if not kwargs:
        return False
    allowed = {"status", "severity", "matched_issue", "fix_description",
               "fix_files", "regression_risk", "root_cause", "tags"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    updates["updated_at"] = time.time()

    set_parts = []
    params = []
    for k, v in updates.items():
        set_parts.append(f"{k}=?")
        params.append(v)
    params.append(bug_id)

    safe_exec(f"UPDATE bugs SET {', '.join(set_parts)} WHERE id=?", params)
    return True


def list_bugs(module: str = "", severity: str = "", status: str = "",
              limit: int = 20, offset: int = 0) -> list[dict]:
    sql = "SELECT * FROM bugs WHERE 1=1"
    params: list = []
    if module:
        sql += " AND module=?"
        params.append(module)
    if severity:
        sql += " AND severity=?"
        params.append(severity)
    if status:
        sql += " AND status=?"
        params.append(status)
    sql += " ORDER BY date DESC, created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    return safe_query(sql, params)


def get_bug(bug_id: str) -> dict:
    rows = safe_query("SELECT * FROM bugs WHERE id=?", [bug_id])
    return rows[0] if rows else {}


def get_trends(module: str = "", months: int = 6) -> list[dict]:
    since = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
    if module:
        return safe_query(
            "SELECT substr(date, 1, 7) as period, COUNT(*) as total, "
            "COUNT(*) FILTER (WHERE status='fixed') as fixed, "
            "COUNT(*) FILTER (WHERE status='open') as open, "
            "COUNT(*) FILTER (WHERE severity='high') as high_severity "
            "FROM bugs WHERE date >= ? AND module = ? GROUP BY period ORDER BY period",
            [since, module],
        )
    return safe_query(
        "SELECT substr(date, 1, 7) as period, COUNT(*) as total, "
        "COUNT(*) FILTER (WHERE status='fixed') as fixed, "
        "COUNT(*) FILTER (WHERE status='open') as open, "
        "COUNT(*) FILTER (WHERE severity='high') as high_severity "
        "FROM bugs WHERE date >= ? GROUP BY period ORDER BY period",
        [since],
    )


def get_top_errors(limit: int = 10) -> list[dict]:
    return safe_query(
        "SELECT error_type, COUNT(*) as count FROM bugs GROUP BY error_type ORDER BY count DESC LIMIT ?",
        [limit],
    )


def import_from_bug_analysis(artifacts_dir: Path = None) -> int:
    from aitest.runtime.paths import get_workstudy
    if artifacts_dir is None:
        artifacts_dir = get_workstudy() / "governance" / "artifacts"
    if not artifacts_dir.exists():
        return 0
    imported = 0
    for f in sorted(artifacts_dir.glob("BUG_ANALYSIS_*.md")):
        text = f.read_text(encoding="utf-8")
        name = f.stem
        parts = name.replace("BUG_ANALYSIS_", "").split("_")
        module = parts[1] if len(parts) > 1 else ""
        root_cause = ""
        for line in text.split("\n"):
            if "根因" in line or "root cause" in line.lower():
                root_cause = line.strip()
                break
        add_bug(module=module, error_type="imported", root_cause=root_cause[:200], status="closed")
        imported += 1
    return imported


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python bug_history.py add|list|trends|import|top-errors")
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "add":
        add_bug(module=sys.argv[2] if len(sys.argv) > 2 else "unknown",
                error_type=sys.argv[3] if len(sys.argv) > 3 else "",
                root_cause=sys.argv[4] if len(sys.argv) > 4 else "")
        print("Bug added")
    elif cmd == "list":
        bugs = list_bugs(module=sys.argv[2] if len(sys.argv) > 2 else "", limit=20)
        for b in bugs:
            print(f"  [{b['id']}] {b['date']} | {b['module']} | {b['error_type']} | {b['severity']} | {b['status']}")
    elif cmd == "trends":
        trends = get_trends(sys.argv[2] if len(sys.argv) > 2 else "")
        for t in trends:
            print(f"  {t['period']}: {t['total']} bugs (open={t['open']}, fixed={t['fixed']}, high={t['high_severity']})")
    elif cmd == "top-errors":
        errors = get_top_errors()
        for e in errors:
            print(f"  {e['error_type']}: {e['count']} occurrences")
    elif cmd == "import":
        count = import_from_bug_analysis()
        print(f"Imported {count} bugs from artifacts/")
