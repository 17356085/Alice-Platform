"""Step 1.3: BrowserUseSkillAdapter smoke test.

Tests all 3 adapter methods against the hazard_item page.

Usage: python tech-research/experiments/smoke_test_adapter.py
"""
import asyncio, logging, sys, json, time
from pathlib import Path

_PROJECT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT))
sys.path.insert(0, str(_PROJECT / "ZJSN_Test-master526"))

from aitest.bu_adapter import BrowserUseSkillAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("smoke")

HASH = "#/warehouse/hazard/item"


async def main():
    adapter = BrowserUseSkillAdapter(headless=True, use_vision=True, max_steps=12)
    results = {}

    # ── Test 1: observe_page_structure ──
    logger.info("=" * 50)
    logger.info("SMOKE 1: observe_page_structure(%s)", HASH)
    logger.info("=" * 50)
    t0 = time.perf_counter()
    try:
        r = await adapter.observe_page_structure(HASH)
        elapsed = time.perf_counter() - t0
        ok = "error" not in r
        logger.info("%s (%.1fs)", "PASS" if ok else "FAIL", elapsed)
        if ok:
            logger.info("  fields: %d, buttons: %d, columns: %d, pagination: %s",
                         len(r.get("search_fields", [])),
                         len(r.get("action_buttons", [])),
                         len(r.get("table_columns", [])),
                         r.get("has_pagination"))
        else:
            logger.info("  error: %s", r.get("error", "")[:200])
        results["observe"] = {"ok": ok, "elapsed": elapsed, "data": r}
    except Exception as e:
        logger.error("observe crashed: %s", e)
        results["observe"] = {"ok": False, "error": str(e)}

    # ── Test 2: generate_po_suggestions ──
    logger.info("=" * 50)
    logger.info("SMOKE 2: generate_po_suggestions(%s)", HASH)
    logger.info("=" * 50)
    t0 = time.perf_counter()
    try:
        r = await adapter.generate_po_suggestions(HASH)
        elapsed = time.perf_counter() - t0
        ok = "error" not in r
        logger.info("%s (%.1fs)", "PASS" if ok else "FAIL", elapsed)
        if ok:
            logger.info("  class: %s, total: %d, high_confidence: %d",
                         r.get("class_name"),
                         r.get("total_found", 0),
                         r.get("high_confidence", 0))
            for loc in r.get("locators", [])[:3]:
                logger.info("  %s: css=%s", loc.get("element_name"), loc.get("css", "")[:60])
        else:
            logger.info("  error: %s", r.get("error", "")[:200])
        results["po"] = {"ok": ok, "elapsed": elapsed, "data": r}
    except Exception as e:
        logger.error("po crashed: %s", e)
        results["po"] = {"ok": False, "error": str(e)}

    # ── Test 3: heal_locator ──
    logger.info("=" * 50)
    logger.info("SMOKE 3: heal_locator('search button', %s)", HASH)
    logger.info("=" * 50)
    t0 = time.perf_counter()
    try:
        r = await adapter.heal_locator("the query/search button", HASH)
        elapsed = time.perf_counter() - t0
        ok = r.get("found", False)
        logger.info("%s (%.1fs) | found=%s confidence=%.2f",
                     "PASS" if ok else "WARN", elapsed, ok, r.get("confidence", 0))
        if r.get("css_selector"):
            logger.info("  css: %s", r["css_selector"])
        if r.get("note"):
            logger.info("  note: %s", r["note"])
        results["heal"] = {"ok": ok, "elapsed": elapsed, "data": r}
    except Exception as e:
        logger.error("heal crashed: %s", e)
        results["heal"] = {"ok": False, "error": str(e)}

    # ── Summary ──
    logger.info("=" * 50)
    passed = sum(1 for r in results.values() if r["ok"])
    total = len(results)
    total_time = sum(r.get("elapsed", 0) for r in results.values())
    logger.info("ADAPTER SMOKE: %d/%d passed (%.1fs total)", passed, total, total_time)
    for name, r in results.items():
        status = "✅" if r["ok"] else "❌"
        logger.info("  %s %s: %.1fs", status, name, r.get("elapsed", 0))

    # Save
    out = Path(__file__).parent / "adapter_smoke_results.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    logger.info("Saved: %s", out)


if __name__ == "__main__":
    asyncio.run(main())
