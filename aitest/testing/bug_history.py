"""
Bug History — SQLite 历史 Bug 库 + 趋势分析

功能:
  1. Bug 记录入库（结构化字段）
  2. 按模块/严重度/状态查询
  3. 趋势分析（按月/周统计）
  4. RAG 已知问题联动

数据库: governance/.data/bugs.db
"""
import sqlite3
import time
import uuid
from pathlib import Path
from datetime import datetime, timedelta

WORKSTUDY = Path(__file__).resolve().parent.parent.parent
DATA_DIR = WORKSTUDY / "governance" / ".data"
BUG_DB = DATA_DIR / "bugs.db"

# ── 数据库初始化 ──────────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(BUG_DB))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bugs (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            module TEXT NOT NULL,
            page TEXT DEFAULT '',
            test_name TEXT DEFAULT '',
            error_type TEXT DEFAULT '',
            error_message TEXT DEFAULT '',
            root_cause TEXT DEFAULT '',
            severity TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            matched_issue TEXT DEFAULT '',
            fix_description TEXT DEFAULT '',
            fix_files TEXT DEFAULT '',
            regression_risk TEXT DEFAULT 'low',
            tags TEXT DEFAULT '',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    """)
    # 索引
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bugs_module ON bugs(module)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bugs_date ON bugs(date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bugs_severity ON bugs(severity)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bugs_status ON bugs(status)")
    conn.commit()
    conn.close()


# ── CRUD ──────────────────────────────────────────────────────────────

def add_bug(
    module: str,
    page: str = "",
    test_name: str = "",
    error_type: str = "",
    error_message: str = "",
    root_cause: str = "",
    severity: str = "medium",
    status: str = "open",
    matched_issue: str = "",
    fix_description: str = "",
    fix_files: str = "",
    regression_risk: str = "low",
    tags: list[str] = None,
) -> str:
    """添加 Bug 记录。返回 bug_id。"""
    init_db()
    conn = get_db()
    bug_id = f"BUG-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
    now = time.time()
    date_str = datetime.now().strftime("%Y-%m-%d")

    conn.execute("""
        INSERT INTO bugs (id, date, module, page, test_name, error_type, error_message,
                          root_cause, severity, status, matched_issue, fix_description,
                          fix_files, regression_risk, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        bug_id, date_str, module, page, test_name, error_type, error_message,
        root_cause, severity, status, matched_issue, fix_description,
        fix_files, regression_risk, ", ".join(tags or []), now, now
    ))
    conn.commit()
    conn.close()
    return bug_id


def update_bug(bug_id: str, **kwargs) -> bool:
    """更新 Bug 字段。"""
    if not kwargs:
        return False
    conn = get_db()
    allowed = {"status", "severity", "matched_issue", "fix_description", "fix_files",
               "regression_risk", "root_cause", "tags"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    updates["updated_at"] = time.time()
    set_clause = ", ".join(f"{k}=?" for k in updates)
    values = list(updates.values()) + [bug_id]
    conn.execute(f"UPDATE bugs SET {set_clause} WHERE id=?", values)
    conn.commit()
    conn.close()
    return True


def list_bugs(module: str = "", severity: str = "", status: str = "",
              limit: int = 20, offset: int = 0) -> list[dict]:
    """查询 Bug 列表。"""
    init_db()
    conn = get_db()
    conditions = []
    params = []

    if module:
        conditions.append("module=?")
        params.append(module)
    if severity:
        conditions.append("severity=?")
        params.append(severity)
    if status:
        conditions.append("status=?")
        params.append(status)

    where = " AND ".join(conditions) if conditions else "1=1"
    rows = conn.execute(
        f"SELECT * FROM bugs WHERE {where} ORDER BY date DESC, created_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset]
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_bug(bug_id: str) -> dict:
    """获取单个 Bug。"""
    conn = get_db()
    row = conn.execute("SELECT * FROM bugs WHERE id=?", [bug_id]).fetchone()
    conn.close()
    return dict(row) if row else {}


def get_trends(module: str = "", months: int = 6) -> list[dict]:
    """获取 Bug 趋势（按月统计）。"""
    init_db()
    conn = get_db()
    since = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")

    if module:
        rows = conn.execute("""
            SELECT substr(date, 1, 7) as period,
                   COUNT(*) as total,
                   SUM(CASE WHEN status='fixed' THEN 1 ELSE 0 END) as fixed,
                   SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) as open,
                   SUM(CASE WHEN severity='high' THEN 1 ELSE 0 END) as high_severity
            FROM bugs WHERE date >= ? AND module = ?
            GROUP BY period ORDER BY period
        """, [since, module]).fetchall()
    else:
        rows = conn.execute("""
            SELECT substr(date, 1, 7) as period,
                   COUNT(*) as total,
                   SUM(CASE WHEN status='fixed' THEN 1 ELSE 0 END) as fixed,
                   SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) as open,
                   SUM(CASE WHEN severity='high' THEN 1 ELSE 0 END) as high_severity
            FROM bugs WHERE date >= ?
            GROUP BY period ORDER BY period
        """, [since]).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_top_errors(limit: int = 10) -> list[dict]:
    """获取最高频的错误类型。"""
    init_db()
    conn = get_db()
    rows = conn.execute("""
        SELECT error_type, COUNT(*) as count
        FROM bugs GROUP BY error_type
        ORDER BY count DESC LIMIT ?
    """, [limit]).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def import_from_bug_analysis(artifacts_dir: Path = None) -> int:
    """从 artifacts/ 中的 BUG_ANALYSIS_*.md 导入历史 Bug。"""
    if artifacts_dir is None:
        artifacts_dir = WORKSTUDY / "governance" / "artifacts"

    if not artifacts_dir.exists():
        print(f"Artifacts dir not found: {artifacts_dir}")
        return 0

    imported = 0
    for f in sorted(artifacts_dir.glob("BUG_ANALYSIS_*.md")):
        text = f.read_text(encoding="utf-8")
        # 简单提取：文件名 → 日期/模块，内容 → 根因
        name = f.stem
        parts = name.replace("BUG_ANALYSIS_", "").split("_")
        date_str = parts[0] if parts else ""
        module = parts[1] if len(parts) > 1 else ""

        # 提取根因行
        root_cause = ""
        for line in text.split("\n"):
            if "根因" in line or "root cause" in line.lower():
                root_cause = line.strip()
                break

        add_bug(
            module=module,
            error_type="imported",
            root_cause=root_cause[:200],
            status="closed",
        )
        imported += 1

    return imported


# CLI
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python bug_history.py add|list|trends|import|top-errors")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "add":
        # Quick add from CLI args
        add_bug(
            module=sys.argv[2] if len(sys.argv) > 2 else "unknown",
            error_type=sys.argv[3] if len(sys.argv) > 3 else "",
            root_cause=sys.argv[4] if len(sys.argv) > 4 else "",
        )
        print("Bug added")

    elif cmd == "list":
        bugs = list_bugs(
            module=sys.argv[2] if len(sys.argv) > 2 else "",
            limit=int(sys.argv[3]) if len(sys.argv) > 3 else 20,
        )
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
