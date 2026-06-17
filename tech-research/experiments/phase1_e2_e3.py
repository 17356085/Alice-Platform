"""Phase 1 E2+E3: Page observe + search via Browser-Use.
Usage: python tech-research/experiments/phase1_e2_e3.py
"""
import asyncio, logging, sys, time, json
from pathlib import Path

_PROJECT = Path(__file__).resolve().parent.parent.parent / "ZJSN_Test-master526"
sys.path.insert(0, str(_PROJECT))

from base.bu_driver import BrowserUseDriver

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("phase1.e2e3")


async def e2_page_observe():
    """E2: Page structure observation for PO generation."""
    async with BrowserUseDriver(headless=False) as bu:
        await bu.login()

        t0 = time.perf_counter()
        task = """
You are now logged in. Navigate to the "Hazard Item Management" page via sidebar:
- Expand "库管管理" (Warehouse Management) in the left sidebar
- Click "环保危废管理" (Hazard Waste Management)
- Click "物品管理" (Item Management)
- Wait for the table to render.

Then observe the page and output a JSON structure:
{
  "page_title": "breadcrumb or page title text",
  "search_fields": [
    {"label": "field name", "type": "input|select|date", "html_hint": "placeholder or class"}
  ],
  "action_buttons": [
    {"label": "button text", "css_hint": "class or text content"}
  ],
  "table_columns": ["col1", "col2", ...],
  "has_pagination": true/false
}
"""
        result = await bu.run_task(task, max_steps=20)
        elapsed = time.perf_counter() - t0

        logger.info("E2 done: %.1fs | tokens=%d | cost~$%.4f",
                     elapsed, bu.total_tokens, bu.estimated_cost)

        # Extract JSON
        text = str(result)
        parsed = None
        try:
            for marker in ["```json", "```"]:
                if marker in text:
                    js = text.split(marker)[1].split("```")[0].strip()
                    parsed = json.loads(js)
                    break
            if not parsed and "{" in text:
                parsed = json.loads(text[text.index("{"):text.rindex("}")+1])
        except Exception:
            pass

        if parsed:
            logger.info("Parsed page structure:\n%s", json.dumps(parsed, ensure_ascii=False, indent=2))
        else:
            logger.info("Raw output (first 400 chars):\n%s", text[:400])

        return {"name": "E2-observe", "elapsed_s": elapsed, "parsed": parsed,
                "tokens": bu.total_tokens, "cost": bu.estimated_cost}


async def e3_search():
    """E3: NL-driven search operation."""
    async with BrowserUseDriver(headless=False) as bu:
        await bu.login()

        t0 = time.perf_counter()
        task = """
Navigate to 库管管理 → 环保危废管理 → 物品管理 via sidebar.
On the page:
1. Find the search input for item name (placeholder "危废品名称" or similar)
2. Type "test" into it
3. Click the "查询" (Search) button
4. Wait for table to refresh
5. Report: number of rows in the table, and whether pagination shows any total.
"""
        result = await bu.run_task(task, max_steps=15)
        elapsed = time.perf_counter() - t0

        logger.info("E3 done: %.1fs | tokens=%d | cost~$%.4f",
                     elapsed, bu.total_tokens, bu.estimated_cost)
        logger.info("Search result:\n%s", str(result)[:300])

        return {"name": "E3-search", "elapsed_s": elapsed,
                "tokens": bu.total_tokens, "cost": bu.estimated_cost}


async def main():
    results = []

    logger.info("=" * 50)
    logger.info("E2: Page Structure Observation")
    logger.info("=" * 50)
    try:
        results.append(await e2_page_observe())
    except Exception as e:
        logger.error("E2 failed: %s", e)
        results.append({"name": "E2-observe", "error": str(e)})

    logger.info("=" * 50)
    logger.info("E3: Search Operation")
    logger.info("=" * 50)
    try:
        results.append(await e3_search())
    except Exception as e:
        logger.error("E3 failed: %s", e)
        results.append({"name": "E3-search", "error": str(e)})

    # Summary
    logger.info("=" * 50)
    for r in results:
        status = "❌" if "error" in r else "✅"
        logger.info("%s %s: %.1fs tokens=%s cost=$%.4f",
                     status, r["name"], r.get("elapsed_s", 0),
                     r.get("tokens", "N/A"), r.get("cost", 0))
        if "error" in r:
            logger.info("   Error: %s", r["error"])


if __name__ == "__main__":
    asyncio.run(main())
