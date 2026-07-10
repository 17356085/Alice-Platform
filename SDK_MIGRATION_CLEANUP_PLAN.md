# SDK Migration Cleanup Plan

**Status**: 70% Complete → Target: 85%  
**Effort**: 2-3 weeks  
**Risk**: Low (mostly cleanup)

---

## Quick Summary

The SDK extraction is **well-executed**. Most core logic is already in `alice-engine`. What remains is:

1. **Delete** deprecated/duplicate code
2. **Clarify** ownership of 3-4 directories
3. **Verify** SDK can run standalone

---

## Phase 1: Audit (3 days)

Run these commands and document results:

```bash
# 1. Check SDK has no platform dependencies
cd packages/alice-engine
grep -r "from aitest\." alice_engine/ | grep -v "test" | grep -v "__pycache__"
# Expected: Empty (or only test imports)

# 2. Check CLI uses SDK public API
cd ../..
grep -r "from aitest\.engine\." aitest/cli/
grep -r "from aitest\.graphs\." aitest/cli/
grep -r "from aitest\.llm\." aitest/cli/
# Expected: Empty (should use "from alice_engine import ...")

# 3. Check for discovery duplication
grep -r "from aitest\.discovery" . | grep -v "__pycache__"
# If any results → need migration

# 4. Check for deprecated provider usage
grep -r "from aitest\.llm\.providers" . | grep -v "__pycache__"
# If empty → can delete aitest/llm/providers/

# 5. Check aitest/runtime/ dependencies
cd aitest/runtime
grep -r "^from aitest\." *.py | grep -v "from aitest.runtime"
grep -r "^from alice_engine" *.py
# Determine: Is this SDK-level or Platform-level?
```

**Deliverable**: `docs/architecture/cleanup-audit-YYYY-MM-DD.md` with findings.

---

## Phase 2: Cleanup (1 week)

### Task 1: Delete Duplicates

If audit confirms these are unused:

```bash
# Delete deprecated providers (if grep found no usages)
rm -rf aitest/llm/providers/
git commit -m "chore: remove deprecated llm providers (now in alice-engine)"

# Delete duplicate discovery (if alice-discovery is used everywhere)
rm -rf aitest/discovery/
git commit -m "chore: remove duplicate discovery module (use alice-discovery package)"
```

### Task 2: Resolve `aitest/runtime/` Ownership

Based on audit findings:

**Option A**: Move to SDK (if used by SDK)
```bash
mv aitest/runtime/* packages/alice-engine/alice_engine/runtime/utils/
# Update imports throughout codebase
git commit -m "refactor: move runtime utilities to SDK"
```

**Option B**: Move to Platform (if used only by Platform)
```bash
mv aitest/runtime/* aitest/infra/runtime/
# Update imports
git commit -m "refactor: move runtime utilities to platform infra"
```

**Option C**: Split (if mixed usage)
- SDK-level utils → `alice-engine/runtime/utils/`
- Platform-level utils → `aitest/infra/runtime/`

### Task 3: Clarify `aitest/graphs/` vs SDK workflow

Compare files:
```bash
diff aitest/graphs/state.py packages/alice-engine/alice_engine/workflow/state.py
```

**If duplicated** → consolidate into SDK  
**If platform-specific** → rename to `aitest/platform/workflow_utils/` for clarity

---

## Phase 3: Refactor CLI (3-4 days)

Replace internal imports with SDK public API:

```python
# Before (BAD)
from aitest.graphs.sop_graph import build_graph
from aitest.engine.executor import AgentLoop

# After (GOOD)
from alice_engine import Engine
from alice_engine.workflow import WorkflowBuilder
```

**Strategy**: One CLI command at a time. Test after each change.

---

## Phase 4: Verify (2 days)

### Standalone SDK Test

```bash
# Create clean test environment
mkdir /tmp/sdk-standalone-test
cd /tmp/sdk-standalone-test
python -m venv .venv
source .venv/bin/activate

# Install only SDK (not platform)
pip install /path/to/packages/alice-engine
pip install /path/to/packages/alice-governance

# Write test script
cat > test_sdk.py << 'EOF'
from alice_engine import Engine, Project

project = Project("./test-project")
engine = Engine(project=project)
result = engine.run("equipment", pages=["alarm-config"])
print(f"Status: {result['status']}")
EOF

# Run test
python test_sdk.py
```

**Success criteria**: Script runs without importing `aitest.*` anywhere.

---

## Phase 5: Document (2 days)

Update documentation:

1. **ADR**: Update `docs/adr/ADR_002_SDK_ARCHITECTURE.md` with final structure
2. **README**: Add SDK usage examples to `packages/alice-engine/README.md`
3. **Migration Guide**: Create `docs/guides/platform-to-sdk-migration.md`

---

## Verification Checklist

Before considering migration complete:

- [ ] `grep -r "from aitest\." packages/alice-engine/` returns no results (except tests)
- [ ] `grep -r "from aitest\.engine\." aitest/cli/` returns no results
- [ ] `grep -r "from aitest\.graphs\." aitest/cli/` returns no results
- [ ] No duplicate modules (discovery, providers)
- [ ] `aitest/runtime/` ownership documented
- [ ] Standalone SDK test passes
- [ ] CI/CD passes all tests

---

## Risk Mitigation

**Low Risk Items** (safe to do):
- Deleting deprecated `aitest/llm/providers/` (after grep confirms unused)
- Deleting duplicate `aitest/discovery/` (after migration)

**Medium Risk Items** (test thoroughly):
- Moving `aitest/runtime/` files
- Refactoring CLI imports

**Strategy**: Make small commits. Test after each change. Can roll back easily.

---

## Timeline

| Week | Focus | Deliverable |
|------|-------|-------------|
| Week 1 | Audit + Easy Deletions | Audit report, delete duplicates |
| Week 2 | Runtime ownership + CLI refactor | Code moved/refactored, tests pass |
| Week 3 | Verification + Documentation | Standalone test, docs updated |

---

## Success Metrics

**Before**: 70% complete, 4-5 unclear ownership areas  
**After**: 85%+ complete, all ownership documented  
**SDK Status**: Can be published to PyPI and used standalone

---

## Questions to Resolve During Audit

1. **aitest/runtime/**: SDK or Platform? Check imports.
2. **aitest/graphs/**: Duplicate or platform-specific? Compare with SDK.
3. **aitest/agents/**: Overlap with SDK agents? Check for duplication.
4. **aitest/adapters/**: Implements SDK interfaces or duplicates SDK? Clarify.
5. **aitest/audit_engine/**: Contains validation logic that belongs in Governance?
6. **aitest/knowledge/**: Generic RAG (SDK) or platform-specific (Platform)?

---

## Contact

Questions? Discuss in `#architecture` channel or comment on this document.
