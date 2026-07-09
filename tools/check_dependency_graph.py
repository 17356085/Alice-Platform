"""Dependency graph and SCC baseline checker for Phase 8.

Builds a first-level package dependency graph for the runtime Python packages,
reports strongly connected components, and guards the alice_engine -> aitest
boundary against both static and dynamic imports.
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent.parent
AITEST_ROOT = REPO_ROOT / "aitest"
SDK_ROOT = REPO_ROOT / "packages" / "alice-engine" / "alice_engine"
DEFAULT_BASELINE = REPO_ROOT / "docs" / "architecture" / "dependency_graph_baseline.json"

FORBIDDEN_DYNAMIC_MARKERS = (
    'import_module("aitest',
    "import_module('aitest",
    '__import__("aitest',
    "__import__('aitest",
)


@dataclass(frozen=True)
class PackageRoot:
    name: str
    path: Path


ROOTS = (
    PackageRoot(name="aitest", path=AITEST_ROOT),
    PackageRoot(name="alice_engine", path=SDK_ROOT),
)


def iter_python_files(root: Path) -> Iterable[Path]:
    for file_path in root.rglob("*.py"):
        if "__pycache__" in file_path.parts:
            continue
        yield file_path


def module_name_for_path(file_path: Path) -> str:
    if file_path.is_relative_to(AITEST_ROOT):
        relative = file_path.relative_to(AITEST_ROOT)
        parts = ["aitest", *relative.with_suffix("").parts]
    elif file_path.is_relative_to(SDK_ROOT):
        relative = file_path.relative_to(SDK_ROOT)
        parts = ["alice_engine", *relative.with_suffix("").parts]
    else:
        raise ValueError(f"Unsupported file path: {file_path}")

    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def level1_name(module_name: str) -> str | None:
    parts = module_name.split(".")
    if len(parts) < 2:
        return None
    return ".".join(parts[:2])


def normalize_import_target(import_name: str) -> str | None:
    if import_name == "aitest":
        return "aitest"
    if import_name.startswith("aitest."):
        return level1_name(import_name)
    if import_name == "alice_engine":
        return "alice_engine"
    if import_name.startswith("alice_engine."):
        return level1_name(import_name)
    return None


def extract_imports(file_path: Path) -> set[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level and not node.module:
                continue
            if node.module:
                imports.add(node.module)
    return imports


def first_party_nodes() -> set[str]:
    nodes: set[str] = set()
    for root in ROOTS:
        for file_path in iter_python_files(root.path):
            module_name = module_name_for_path(file_path)
            level1 = level1_name(module_name)
            if level1:
                nodes.add(level1)
    return nodes


def build_dependency_report() -> dict:
    nodes = first_party_nodes()
    edges: dict[str, set[str]] = {node: set() for node in nodes}
    edge_sources: dict[str, set[str]] = {}
    boundary_violations: list[dict[str, str]] = []

    for root in ROOTS:
        for file_path in iter_python_files(root.path):
            source_module = module_name_for_path(file_path)
            source_level1 = level1_name(source_module)
            if source_level1 is None:
                continue

            imports = extract_imports(file_path)
            for import_name in imports:
                target = normalize_import_target(import_name)
                if not target or target == source_level1 or target not in edges:
                    continue
                edges[source_level1].add(target)
                key = f"{source_level1}->{target}"
                edge_sources.setdefault(key, set()).add(source_module)

                if source_level1.startswith("alice_engine") and target.startswith("aitest"):
                    boundary_violations.append(
                        {
                            "type": "static",
                            "source_file": str(file_path.relative_to(REPO_ROOT)).replace("\\", "/"),
                            "source_module": source_module,
                            "target": import_name,
                        }
                    )

            if source_level1.startswith("alice_engine"):
                text = file_path.read_text(encoding="utf-8")
                for marker in FORBIDDEN_DYNAMIC_MARKERS:
                    if marker in text:
                        boundary_violations.append(
                            {
                                "type": "dynamic",
                                "source_file": str(file_path.relative_to(REPO_ROOT)).replace("\\", "/"),
                                "source_module": source_module,
                                "target": marker,
                            }
                        )

    sccs = strongly_connected_components(edges)
    multi_node_sccs = sorted(
        [sorted(component) for component in sccs if len(component) > 1],
        key=lambda component: (-len(component), component),
    )

    return {
        "nodes": sorted(nodes),
        "edges": [
            {
                "source": source,
                "target": target,
                "sources": sorted(edge_sources.get(f"{source}->{target}", set())),
            }
            for source in sorted(edges)
            for target in sorted(edges[source])
        ],
        "sccs": multi_node_sccs,
        "boundary_violations": boundary_violations,
        "summary": {
            "node_count": len(nodes),
            "edge_count": sum(len(targets) for targets in edges.values()),
            "scc_count": len(multi_node_sccs),
            "largest_scc_size": max((len(component) for component in multi_node_sccs), default=0),
        },
    }


def strongly_connected_components(graph: dict[str, set[str]]) -> list[list[str]]:
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    result: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for neighbor in sorted(graph[node]):
            if neighbor not in indices:
                visit(neighbor)
                lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
            elif neighbor in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[neighbor])

        if lowlinks[node] == indices[node]:
            component: list[str] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            result.append(component)

    for node in sorted(graph):
        if node not in indices:
            visit(node)

    return result


def load_baseline(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compare_with_baseline(report: dict, baseline: dict) -> list[str]:
    errors: list[str] = []
    summary = report["summary"]
    baseline_summary = baseline.get("summary", {})

    if report["boundary_violations"]:
        errors.append("alice_engine -> aitest boundary violation detected")

    expected_sccs = {tuple(component) for component in baseline.get("sccs", [])}
    actual_sccs = {tuple(component) for component in report["sccs"]}
    new_sccs = sorted(actual_sccs - expected_sccs)
    if new_sccs:
        errors.append(f"new SCCs introduced: {new_sccs}")

    max_scc_count = baseline_summary.get("scc_count")
    if max_scc_count is not None and summary["scc_count"] > max_scc_count:
        errors.append(
            f"SCC count grew from baseline {max_scc_count} to {summary['scc_count']}"
        )

    max_largest = baseline_summary.get("largest_scc_size")
    if max_largest is not None and summary["largest_scc_size"] > max_largest:
        errors.append(
            f"largest SCC grew from baseline {max_largest} to {summary['largest_scc_size']}"
        )

    return errors


def render_text_report(report: dict) -> str:
    lines = [
        "Dependency graph summary",
        f"  nodes: {report['summary']['node_count']}",
        f"  edges: {report['summary']['edge_count']}",
        f"  sccs:  {report['summary']['scc_count']}",
        f"  max:   {report['summary']['largest_scc_size']}",
    ]
    if report["sccs"]:
        lines.append("SCC baseline:")
        for component in report["sccs"]:
            lines.append(f"  - {' <-> '.join(component)}")
    if report["boundary_violations"]:
        lines.append("Boundary violations:")
        for violation in report["boundary_violations"]:
            lines.append(
                f"  - {violation['type']}: {violation['source_file']} -> {violation['target']}"
            )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check package dependency graph and SCC baseline")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Path to the dependency baseline JSON file",
    )
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Write the current report to the baseline path",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full JSON report instead of the text summary",
    )
    args = parser.parse_args()

    report = build_dependency_report()

    if args.write_baseline:
        args.baseline.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Wrote baseline to {args.baseline}")
        return 0

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))

    if args.baseline.exists():
        errors = compare_with_baseline(report, load_baseline(args.baseline))
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
