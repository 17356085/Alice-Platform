#!/bin/bash
# Pre-commit Hook -- P2-2 consistency + code quality
# Install: cp tools/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PASS=0; FAIL=0
echo ""; echo "========================================"; echo "  Pre-commit Check"; echo "========================================"
echo ""; echo "[1/3] Consistency..."
if python -m aitest.consistency_checker --json 2>/dev/null; then
    echo "  -> PASS"; PASS=$((PASS + 1))
else
    echo "  -> FAIL (run: aitest check --consistency)"; FAIL=$((FAIL + 1))
fi
echo ""; echo "[2/3] Code quality (staged)..."
if python tools/check_code_quality.py --staged --json 2>/dev/null; then
    echo "  -> PASS"; PASS=$((PASS + 1))
else
    echo "  -> FAIL (run: aitest check)"; FAIL=$((FAIL + 1))
fi
echo ""; echo "[3/3] Python syntax..."
SYNTAX_OK=0; SYNTAX_ERR=0
for f in $(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | grep '\.py$'); do
    if [ -f "$f" ]; then
        if python -c "import py_compile; py_compile.compile('$f', doraise=True)" 2>/dev/null; then
            SYNTAX_OK=$((SYNTAX_OK + 1))
        else
            echo "  FAIL: $f"; SYNTAX_ERR=$((SYNTAX_ERR + 1))
        fi
    fi
done
[ $SYNTAX_ERR -eq 0 ] && echo "  -> PASS ($SYNTAX_OK files)" && PASS=$((PASS + 1)) || echo "  -> FAIL ($SYNTAX_ERR files)" && FAIL=$((FAIL + 1))
echo ""; echo "========================================"; echo "  Result: $PASS passed, $FAIL failed"; echo "========================================"
[ $FAIL -gt 0 ] && echo "" && echo "Commit blocked. Fix issues or use --no-verify." && exit 1
exit 0
