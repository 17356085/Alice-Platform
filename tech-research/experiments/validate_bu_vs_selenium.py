"""Browser-Use vs Selenium 成效验证

三个维度:
  V1: PO 生成速度 — BrowserUse 观察页面 → 生成 PO 骨架 vs 现有人工 PO
  V2: 失败自愈 — 故意改错选择器 → BrowserUse 兜底恢复
  V3: Tank 非标准 UI — BrowserUse NL 驱动 vs Selenium 定制 PO

用法: python tech-research/experiments/validate_bu_vs_selenium.py
"""
import asyncio, logging, sys, time, json
from pathlib import Path

_PROJECT = Path(__file__).resolve().parent.parent.parent / "ZJSN_Test-master526"
sys.path.insert(0, str(_PROJECT))

from base.bu_driver import BrowserUseDriver

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("validate")

# ═══════════════════════════════════════════════════════════════════
#  V1: PO 生成 vs 现有人工 PO
# ═══════════════════════════════════════════════════════════════════

MANUAL_PO_FILE = _PROJECT / "page" / "warehouse_page" / "HazardItemPage.py"


async def v1_po_generation():
    """V1: BrowserUse 自动观察页面结构，对比现有人工 PO"""
    logger.info("=" * 60)
    logger.info("V1: PO Generation Speed")
    logger.info("=" * 60)

    # Read existing manual PO for comparison
    manual_lines = 0
    manual_locators = 0
    if MANUAL_PO_FILE.exists():
        content = MANUAL_PO_FILE.read_text(encoding="utf-8")
        manual_lines = len(content.splitlines())
        manual_locators = content.count("(By.")
        logger.info("Existing manual PO: %d lines, %d locators", manual_lines, manual_locators)

    async with BrowserUseDriver(headless=False, use_vision=True, max_steps=15) as bu:
        await bu.login()

        t0 = time.perf_counter()
        result = await bu.run_task("""
Navigate to #/warehouse/hazard/item (hazard item management page).
Wait for table + search form to render fully.

Output JSON:
{
  "search_fields": [{"label":"...","type":"input|select","locator_hint":"CSS or placeholder"}],
  "action_buttons": [{"label":"...","locator_hint":"CSS class or text"}],
  "table_columns": ["col1","col2",...],
  "has_pagination": true|false,
  "has_checkbox_column": true|false
}
""")
        elapsed = time.perf_counter() - t0
        output = str(result)

        # Parse JSON
        parsed = None
        for marker in ["```json", "```"]:
            if marker in output:
                try:
                    js = output.split(marker)[1].split("```")[0].strip()
                    parsed = json.loads(js)
                    break
                except Exception:
                    continue
        if not parsed:
            try:
                start = output.index("{")
                end = output.rindex("}") + 1
                parsed = json.loads(output[start:end])
            except Exception:
                pass

        logger.info("V1 elapsed: %.1fs", elapsed)
        if parsed:
            logger.info("V1 page structure:\n%s", json.dumps(parsed, ensure_ascii=False, indent=2))
            bu_fields = len(parsed.get("search_fields", []))
            bu_buttons = len(parsed.get("action_buttons", []))
            bu_columns = len(parsed.get("table_columns", []))
            logger.info("V1 BU output: %d fields, %d buttons, %d columns",
                        bu_fields, bu_buttons, bu_columns)
        else:
            logger.warning("V1: failed to parse JSON from output")
            logger.info("Raw output: %s", output[:500])

        return {
            "name": "V1-PO-Generation",
            "elapsed_s": elapsed,
            "manual_po_lines": manual_lines,
            "manual_locators": manual_locators,
            "bu_parsed": parsed is not None,
            "bu_fields": parsed.get("search_fields", []) if parsed else [],
            "bu_buttons": parsed.get("action_buttons", []) if parsed else [],
            "bu_columns": parsed.get("table_columns", []) if parsed else [],
        }


# ═══════════════════════════════════════════════════════════════════
#  V2: Self-Healing (broken selector recovery)
# ═══════════════════════════════════════════════════════════════════

async def v2_self_healing():
    """V2: 模拟选择器失效 → BrowserUse 兜底重试"""
    logger.info("=" * 60)
    logger.info("V2: Self-Healing Fallback")
    logger.info("=" * 60)

    async with BrowserUseDriver(headless=False, use_vision=True, max_steps=12) as bu:
        await bu.login()

        t0 = time.perf_counter()

        # Simulate: navigate to page, but "forgot" the correct locator
        # BrowserUse should use vision/NL to find elements
        result = await bu.run_task("""
Navigate to #/warehouse/hazard/item (hazard item management page).

IMPORTANT: The CSS selectors you normally use are broken. You must use vision
and natural language to find elements:

1. Find the input field near the label "危废品名称" (hazard item name).
   Click it and type "test_bu_heal".
2. Find the button labeled "查询" (search/query). Click it.
3. Wait for table refresh. Count the rows shown.
4. Find the button labeled "重置" (reset). Click it.

Report: Were you able to complete all steps without CSS selectors?
""")
        elapsed = time.perf_counter() - t0

        output = str(result)
        success = "test_bu_heal" in output.lower() or "query" in output.lower()
        logger.info("V2 elapsed: %.1fs | NL-driven interaction: %s", elapsed,
                     "SUCCESS" if success else "FAIL")
        logger.info("V2 output preview: %s", output[:400])

        return {
            "name": "V2-Self-Healing",
            "elapsed_s": elapsed,
            "nl_interaction_success": success,
        }


# ═══════════════════════════════════════════════════════════════════
#  V3: Tank 非标准 UI (custom UI framework)
# ═══════════════════════════════════════════════════════════════════

async def v3_tank_custom_ui():
    """V3: Tank 自定义 UI — BrowserUse NL vs Selenium 定制 PO"""
    logger.info("=" * 60)
    logger.info("V3: Tank Custom UI (non-Element Plus)")
    logger.info("=" * 60)

    # Read tank Selenium PO for comparison
    tank_po = _PROJECT / "page" / "tank_page" / "TankMonitorPage.py"
    tank_po_lines = 0
    if tank_po.exists():
        tank_po_lines = len(tank_po.read_text(encoding="utf-8").splitlines())

    async with BrowserUseDriver(headless=False, use_vision=True, max_steps=12) as bu:
        await bu.login()

        t0 = time.perf_counter()
        result = await bu.run_task("""
Navigate to #/tank/monitor (tank monitoring page).
This page uses a CUSTOM UI framework (NOT Element Plus).

Wait for the page to fully load. Using vision, report:
1. How many stat cards at the top? What values do they show?
2. How many columns in the table? List the column headers.
3. How many data rows?
4. What action buttons are visible (e.g. add/edit/export/import)?
""")
        elapsed = time.perf_counter() - t0

        output = str(result)
        logger.info("V3 elapsed: %.1fs | Tank PO lines: %d", elapsed, tank_po_lines)
        logger.info("V3 output preview: %s", output[:500])

        # Check for expected content
        has_stats = any(w in output.lower() for w in ["stat", "card", "tank", "total", "储罐", "统计"])
        has_table = any(w in output.lower() for w in ["column", "header", "row", "table", "列", "行"])

        return {
            "name": "V3-Tank-CustomUI",
            "elapsed_s": elapsed,
            "tank_selenium_po_lines": tank_po_lines,
            "bu_detected_stats": has_stats,
            "bu_detected_table": has_table,
        }


# ═══════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════

async def main():
    logger.info("╔══════════════════════════════════════════╗")
    logger.info("║  Browser-Use vs Selenium Validation      ║")
    logger.info("╚══════════════════════════════════════════╝")

    results = []

    # V1
    try:
        results.append(await v1_po_generation())
    except Exception as e:
        logger.error("V1 failed: %s", e, exc_info=True)
        results.append({"name": "V1", "error": str(e)})

    # V2
    try:
        results.append(await v2_self_healing())
    except Exception as e:
        logger.error("V2 failed: %s", e, exc_info=True)
        results.append({"name": "V2", "error": str(e)})

    # V3
    try:
        results.append(await v3_tank_custom_ui())
    except Exception as e:
        logger.error("V3 failed: %s", e, exc_info=True)
        results.append({"name": "V3", "error": str(e)})

    # ── Summary ──
    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)

    for r in results:
        status = "❌" if "error" in r else "✅"
        logger.info("%s %s | %.1fs", status, r["name"], r.get("elapsed_s", 0))
        if "error" in r:
            logger.info("   Error: %s", r["error"])

    # Save results
    out = Path(__file__).parent / "validation_results.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    logger.info("Results saved: %s", out)


if __name__ == "__main__":
    asyncio.run(main())
