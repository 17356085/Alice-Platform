#!/usr/bin/env python3
"""Verify API route migration to /api/v1/ prefix."""
import re
from pathlib import Path

# Target routers to verify
ROUTERS = {
    "agents_router": "agents.py",
    "workspace_router": "workspace.py",
    "workflows_router": "workflows.py",
    "bugs_router": "bugs.py",
    "audit_router": "audit.py",
    "kpi_router": "kpi.py",
    "kanban_router": "kanban.py",
    "terminal_router": "terminal.py",
    "obs_router": "observability.py",
    "chat_router": "chat.py",
    "router": "sessions_api.py",  # sessions uses 'router' instead of 'sessions_router'
    "onboarding_router": "onboarding.py",
    "integrations_router": "integrations.py",
}

api_dir = Path("aitest/server/api")

print("=" * 80)
print("API Route Migration Verification")
print("=" * 80)

errors = []
warnings = []

for router_name, filename in ROUTERS.items():
    filepath = api_dir / filename
    if not filepath.exists():
        errors.append(f"❌ {filename}: File not found")
        continue

    content = filepath.read_text(encoding="utf-8")

    # Check router prefix
    pattern = rf'{router_name}\s*=\s*APIRouter\(prefix="([^"]+)"'
    match = re.search(pattern, content)

    if not match:
        errors.append(f"❌ {filename}: Could not find {router_name} definition")
        continue

    prefix = match.group(1)

    # Expected prefix mapping
    expected = {
        "agents_router": "/api/v1/agents",
        "workspace_router": "/api/v1/workspaces",
        "workflows_router": "/api/v1/workflows",
        "bugs_router": "/api/v1/bugs",
        "audit_router": "/api/v1/audit",
        "kpi_router": "/api/v1/kpi",
        "kanban_router": "/api/v1/kanban",
        "terminal_router": "/api/v1/terminal",
        "obs_router": "/api/v1/observability",
        "chat_router": "/api/v1/chat",
        "router": "/api/v1/sessions",
        "onboarding_router": "/api/v1/onboarding",
        "integrations_router": "/api/v1/integrations",
    }

    expected_prefix = expected[router_name]

    if prefix == expected_prefix:
        print(f"✅ {filename:25s} → {prefix}")
    else:
        errors.append(f"❌ {filename}: Expected '{expected_prefix}', got '{prefix}'")

print("\n" + "=" * 80)
print("Frontend Endpoints Verification")
print("=" * 80)

# Check frontend endpoints.ts
endpoints_file = Path("aitest/web/src/api/endpoints.ts")
if endpoints_file.exists():
    content = endpoints_file.read_text(encoding="utf-8")

    # Key endpoints to check
    checks = [
        ("CHAT_SESSIONS", "/api/v1/chat/sessions"),
        ("ONBOARDING_START", "/api/v1/onboarding/start"),
        ("WS_KANBAN", "/api/v1/kanban/ws"),
        ("KPI_SUMMARY", "/api/v1/kpi/summary"),
    ]

    for const_name, expected_path in checks:
        pattern = rf'{const_name}:\s*[\'"]([^\'"]+)[\'"]'
        match = re.search(pattern, content)
        if match:
            actual = match.group(1)
            if actual == expected_path:
                print(f"✅ {const_name:20s} → {actual}")
            else:
                errors.append(f"❌ endpoints.ts {const_name}: Expected '{expected_path}', got '{actual}'")
        else:
            warnings.append(f"⚠️  endpoints.ts: Could not find {const_name}")
else:
    errors.append("❌ endpoints.ts not found")

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)

if errors:
    print(f"\n❌ {len(errors)} error(s) found:")
    for err in errors:
        print(f"   {err}")

if warnings:
    print(f"\n⚠️  {len(warnings)} warning(s):")
    for warn in warnings:
        print(f"   {warn}")

if not errors and not warnings:
    print("\n✅ All checks passed! API routes successfully migrated to /api/v1/")
    exit(0)
elif not errors:
    print("\n⚠️  Migration complete with warnings")
    exit(0)
else:
    print("\n❌ Migration incomplete, please fix errors above")
    exit(1)
