"""Context Builder — dynamic context discovery.

Task 3a (P1) — APERANT_MIGRATION_PLAN.md
Port of Aperant context/builder.ts 6-step pipeline, adapted for aitest
test-execution domain (not code generation).

Architecture:
  Steps 1-5: pure filesystem — glob + grep + read. No vector DB / LLM.
  Step 6:   optional Memory query via rag_engine (degraded gracefully).

Usage:
    from pathlib import Path
    from aitest.llm.context_builder import build_context

    ctx = build_context(
        module="equipment",
        project_root=Path("/path/to/ZJSN_Test-master526"),
        page="alarm-config",
        task_description="设备报警配置页面 CRUD 测试",
    )
    # → SubtaskContext with discovered files, patterns, keywords
    # Pass ctx to ContextInjector via variables["builder_context"]
"""

import re
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

# Max files to return (avoid context bloat)
MAX_DISCOVERED_FILES = 15

# Max snippet length per file (characters)
MAX_SNIPPET_CHARS = 500

# Keywords always present in test-execution context
FIXED_KEYWORDS = [
    "conftest", "fixture", "BasePage", "locator", "cleanup",
    "pytest", "mark", "parametrize",
]

# Patterns we care about discovering in test project files
INTERESTING_PATTERNS = [
    (r"class\s+\w+\(BasePage\)", "BasePage inheritance"),
    (r"@pytest\.fixture", "pytest fixture"),
    (r"@pytest\.mark\.\w+", "pytest marker"),
    (r"cleanup_tracker", "cleanup tracker"),
    (r"el-table", "Element Plus table"),
    (r"el-dialog", "Element Plus dialog"),
    (r"el-cascader", "Element Plus cascader"),
    (r"By\.CSS_SELECTOR", "CSS Selector locator"),
    (r"By\.XPATH", "XPath locator"),
    (r"wait_vue_stable", "Vue stability wait"),
    (r"def test_", "test function"),
    (r"yield\s+driver", "driver fixture (yield)"),
]


# ── Data classes ───────────────────────────────────────────────────────────

@dataclass
class DiscoveredFile:
    """A file discovered by context builder."""
    path: str           # Relative path from project_root
    role: str           # "modify" | "reference"
    relevance: float    # 0.0–1.0
    snippet: str        # First MAX_SNIPPET_CHARS of content


@dataclass
class SubtaskContext:
    """Result of the 6-step context discovery pipeline."""
    files: list[DiscoveredFile] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)
    memory_hints: str = ""
    source_count: int = 0


# ═══════════════════════════════════════════════════════════════════════════
#  Step 1–2: Keyword extraction
# ═══════════════════════════════════════════════════════════════════════════

def extract_keywords(task_description: str) -> list[str]:
    """Extract search keywords from task description.

    Pure string processing — no LLM, no vector DB.
    Uses Chinese/English delimiters and domain-specific stop-word filtering.
    """
    if not task_description or not task_description.strip():
        return list(FIXED_KEYWORDS)

    # Split on common delimiters (Chinese + English)
    tokens = re.split(r"[，,、\s\n；;。\.：:]+", task_description.strip())

    # Keep tokens with ≥2 characters, filter noise
    stop_words = {
        "的", "了", "是", "在", "和", "与", "或", "the", "a", "an", "is",
        "to", "of", "in", "for", "and", "or", "with", "测试", "页面",
    }
    keywords = []
    for t in tokens:
        t = t.strip()
        if len(t) >= 2 and t.lower() not in stop_words:
            keywords.append(t)

    # Deduplicate preserving order, then append fixed keywords
    seen = set()
    unique = []
    for kw in keywords:
        if kw.lower() not in seen:
            seen.add(kw.lower())
            unique.append(kw)

    # Append fixed keywords not already present
    for fk in FIXED_KEYWORDS:
        if fk.lower() not in seen:
            unique.append(fk)

    return unique


# ═══════════════════════════════════════════════════════════════════════════
#  Step 3: File search (pure filesystem)
# ═══════════════════════════════════════════════════════════════════════════

def search_test_files(
    module: str,
    project_root: Path,
    page: str = "",
    keywords: list[str] = None,
) -> list[DiscoveredFile]:
    """Search project files matching module/page/keywords.

    Search paths (derived from project_root, zero hardcoding):
      - project_root/page/{module}_page/     → Page Objects (.py)
      - project_root/script/{module}/         → Test scripts (.py)
      - project_root/.tlo/knowledge/modules/{module}/  → Module context (.md)

    Pure glob + read. No vector DB / ChromaDB dependency.
    """
    keywords = keywords or []
    project_root = Path(project_root)

    # Define search paths relative to project_root
    search_paths: list[Path] = []
    po_dir = project_root / "page" / f"{module}_page"
    script_dir = project_root / "script" / module
    tlo_module_dir = project_root / ".tlo" / "knowledge" / "modules" / module

    for p in (po_dir, script_dir, tlo_module_dir):
        if p.exists():
            search_paths.append(p)

    if not search_paths:
        logger.debug("No search paths found for module=%s in %s", module, project_root)
        return []

    # Collect file candidates
    candidates: list[tuple[Path, str]] = []  # (full_path, relative_path)

    for sp in search_paths:
        # .py files (recursive for page/ dir, flat for script/)
        if sp == po_dir:
            for py_file in sp.rglob("*.py"):
                rel = py_file.relative_to(project_root)
                candidates.append((py_file, str(rel)))
        elif sp == script_dir:
            for py_file in sp.glob("*.py"):
                rel = py_file.relative_to(project_root)
                candidates.append((py_file, str(rel)))
            for py_file in sp.glob("test_*.py"):
                rel = py_file.relative_to(project_root)
                candidates.append((py_file, str(rel)))
        elif sp == tlo_module_dir:
            for md_file in sp.rglob("*.md"):
                rel = md_file.relative_to(project_root)
                candidates.append((md_file, str(rel)))

    # Deduplicate by relative path
    seen_paths: set[str] = set()
    unique_candidates: list[tuple[Path, str]] = []
    for full, rel in candidates:
        if rel not in seen_paths:
            seen_paths.add(rel)
            unique_candidates.append((full, rel))

    # Score relevance against keywords
    kw_lower = [k.lower() for k in keywords] if keywords else []
    results: list[DiscoveredFile] = []

    for full_path, rel_path in unique_candidates:
        relevance = _score_relevance(rel_path, module, page, kw_lower)

        # Read snippet (first MAX_SNIPPET_CHARS)
        snippet = ""
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            snippet = content[:MAX_SNIPPET_CHARS]
        except (OSError, UnicodeDecodeError):
            pass

        results.append(DiscoveredFile(
            path=rel_path,
            role="",  # Assigned later by categorize_files()
            relevance=relevance,
            snippet=snippet,
        ))

    # Sort by relevance descending, cap at MAX_DISCOVERED_FILES
    results.sort(key=lambda f: f.relevance, reverse=True)
    return results[:MAX_DISCOVERED_FILES]


def _score_relevance(
    rel_path: str,
    module: str,
    page: str = "",
    keywords_lower: list[str] = None,
) -> float:
    """Score file relevance to the task (0.0–1.0)."""
    path_lower = rel_path.lower()
    score = 0.3  # Base score for being in a search path

    if module and module.lower() in path_lower:
        score += 0.3
    if page and page.lower() in path_lower:
        score += 0.2

    if keywords_lower:
        kw_hits = sum(1 for kw in keywords_lower if kw in path_lower)
        score += min(kw_hits * 0.1, 0.3)

    return min(score, 1.0)


# ═══════════════════════════════════════════════════════════════════════════
#  Step 4: File classification (modify vs reference)
# ═══════════════════════════════════════════════════════════════════════════

def categorize_files(
    files: list[DiscoveredFile],
    task_description: str = "",
) -> tuple[list[DiscoveredFile], list[DiscoveredFile]]:
    """Classify files as modify (test targets) vs reference (read-only).

    Heuristics:
      - conftest.py → reference (fixture definitions, don't auto-modify)
      - __init__.py → reference (package markers)
      - .py → modify (Page Objects, test scripts — may need regeneration)
      - .md  → reference (governance docs, read-only knowledge)
    """
    modify: list[DiscoveredFile] = []
    reference: list[DiscoveredFile] = []

    for f in files:
        basename = Path(f.path).name.lower()

        # conftest.py and __init__.py are always reference
        if basename in ("conftest.py", "__init__.py"):
            f.role = "reference"
            reference.append(f)
        elif f.path.endswith(".py"):
            f.role = "modify"
            modify.append(f)
        else:
            f.role = "reference"
            reference.append(f)

    return modify, reference


# ═══════════════════════════════════════════════════════════════════════════
#  Step 5: Pattern discovery (grep-based, no LLM)
# ═══════════════════════════════════════════════════════════════════════════

def discover_patterns(
    project_root: Path,
    reference_files: list[DiscoveredFile],
    keywords: list[str] = None,
) -> list[str]:
    """Discover code/test patterns from reference files using grep.

    Pure regex-based. No LLM / vector DB dependency.
    """
    project_root = Path(project_root)
    found_patterns: set[str] = set()

    for f in reference_files:
        full_path = project_root / f.path
        if not full_path.exists():
            continue
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            continue

        for pattern_re, label in INTERESTING_PATTERNS:
            if re.search(pattern_re, content):
                found_patterns.add(label)

    # Also check modify files for patterns (they contain the real code)
    return sorted(found_patterns)


# ═══════════════════════════════════════════════════════════════════════════
#  Step 6: Memory hints (optional, gracefully degraded)
# ═══════════════════════════════════════════════════════════════════════════

def _query_memory(
    module: str,
    task_description: str,
) -> str:
    """Query project memory for relevant hints.

    Task 3b: Delegates to rag_engine.build_planner_memory_context()
    which queries 5 memory types with graceful cold-start degradation.
    """
    try:
        from aitest.knowledge.rag_engine import build_planner_memory_context
        return build_planner_memory_context(
            module=module,
            task_description=task_description,
        )
    except Exception:
        # Memory DB not initialized / connection failed → silent fallback
        return ""


# ═══════════════════════════════════════════════════════════════════════════
#  Main entry point
# ═══════════════════════════════════════════════════════════════════════════

def build_context(
    module: str,
    project_root: Path,
    page: str = "",
    task_description: str = "",
    include_memory: bool = True,
) -> SubtaskContext:
    """6-step context discovery pipeline.

    Steps 1-5 are pure filesystem (no vector DB / LLM dependency).
    Step 6 is optional Memory query, degraded gracefully on failure.

    Args:
        module: Business module name (e.g. "equipment", "personnel").
        project_root: REQUIRED — absolute path to test project root
                      (e.g. Path("/path/to/ZJSN_Test-master526")).
        page: Optional page name within module (e.g. "alarm-config").
        task_description: Human-readable goal (used for keyword extraction).
        include_memory: Whether to query Memory in step 6 (default True).

    Returns:
        SubtaskContext with files, keywords, patterns, memory_hints.
        Empty results (no files found) are valid — caller handles gracefully.
    """
    project_root = Path(project_root)

    # Steps 1–2: Extract keywords
    keywords = extract_keywords(task_description)
    logger.debug("Keywords extracted: %s", keywords[:10])

    # Step 3: Search files (pure filesystem)
    files = search_test_files(module, project_root, page, keywords)
    logger.debug("Files discovered: %d", len(files))

    # Step 4: Categorize
    modify, reference = categorize_files(files, task_description)
    logger.debug("Categorized: %d modify, %d reference", len(modify), len(reference))

    # Step 5: Discover patterns (grep-based)
    patterns = discover_patterns(project_root, reference, keywords)
    logger.debug("Patterns found: %s", patterns)

    # Step 6: Memory hints (optional, gracefully degraded)
    memory_hints = ""
    if include_memory:
        memory_hints = _query_memory(module, task_description)

    # Combine: modify first (actionable), then reference (informational)
    all_files = modify + reference

    return SubtaskContext(
        files=all_files,
        keywords=keywords,
        patterns=patterns,
        memory_hints=memory_hints,
        source_count=len(all_files),
    )
