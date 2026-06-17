"""Step 1.2: MiMo tool calling 专项测试

验证 MiMo-V2.5 (via ChatOpenAI) 在 browser-use 中的 tool calling / structured output 可靠性。

用法: python tech-research/experiments/test_mimo_tool_calling.py
"""
import asyncio, logging, sys, time, json
from pathlib import Path

_PROJECT = Path(__file__).resolve().parent.parent.parent / "ZJSN_Test-master526"
sys.path.insert(0, str(_PROJECT))

from base.bu_driver import BrowserUseDriver

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mimo-test")


async def test_structured_output_json():
    """测试: MiMo 能否输出有效的 JSON 结构化数据"""
    logger.info("=" * 50)
    logger.info("Test 1: Structured JSON output")
    logger.info("=" * 50)

    async with BrowserUseDriver(headless=True, use_vision=False, max_steps=10) as bu:
        await bu.login()

        t0 = time.perf_counter()
        result = await bu.run_task("""
Navigate to #/warehouse/hazard/item (hazard item management page).
Wait for the search form and table to render.

Output ONLY a valid JSON object (no markdown, no extra text) with this exact structure:
{"page_title":"...","search_fields_count":0,"button_count":0,"table_columns_count":0}
""")
        elapsed = time.perf_counter() - t0
        output = str(result)

        # Try to parse JSON
        parsed = None
        for marker in ["```json", "```"]:
            if marker in output:
                try:
                    parsed = json.loads(output.split(marker)[1].split("```")[0])
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

        logger.info("Elapsed: %.1fs", elapsed)
        logger.info("Parsed JSON: %s", parsed is not None)
        if parsed:
            logger.info("Content: %s", json.dumps(parsed, ensure_ascii=False))

        return {"name": "test-json-output", "elapsed_s": elapsed,
                "json_parsed": parsed is not None, "content": parsed}


async def test_multi_step_navigation():
    """测试: MiMo 能否完成多步导航 + 搜索操作"""
    logger.info("=" * 50)
    logger.info("Test 2: Multi-step navigation + search")
    logger.info("=" * 50)

    async with BrowserUseDriver(headless=True, use_vision=False, max_steps=12) as bu:
        await bu.login()

        t0 = time.perf_counter()
        result = await bu.run_task("""
Navigate to #/warehouse/hazard/item.
On the page:
1. Find the search input field (look for input near label with "危废品" or similar)
2. Type "test_mimo" into it
3. Find and click the "查询" (Query) button
4. Wait for table to update
5. Report: How many rows in the table now? Done with success=True.
""")
        elapsed = time.perf_counter() - t0
        output = str(result)

        success = "success" in output.lower() or "row" in output.lower()
        logger.info("Elapsed: %.1fs | Success indication: %s", elapsed, success)
        logger.info("Output preview: %s", output[:300])

        return {"name": "test-multi-step", "elapsed_s": elapsed,
                "success_indication": success}


async def test_element_discovery():
    """测试: MiMo 能否发现页面上的所有可交互元素"""
    logger.info("=" * 50)
    logger.info("Test 3: Element discovery")
    logger.info("=" * 50)

    async with BrowserUseDriver(headless=True, use_vision=False, max_steps=8) as bu:
        await bu.login()

        t0 = time.perf_counter()
        result = await bu.run_task("""
Navigate to #/warehouse/hazard/item.
Count ALL interactive elements visible on the page:
- input fields
- select/dropdown triggers
- buttons (all types)
- links

Output JSON: {"inputs": N, "selects": N, "buttons": N, "total": N}
""")
        elapsed = time.perf_counter() - t0
        output = str(result)

        parsed = None
        try:
            for marker in ["```json", "```"]:
                if marker in output:
                    parsed = json.loads(output.split(marker)[1].split("```")[0])
                    break
            if not parsed and "{" in output:
                parsed = json.loads(output[output.index("{"):output.rindex("}")+1])
        except Exception:
            pass

        logger.info("Elapsed: %.1fs | Parsed: %s", elapsed, parsed is not None)
        if parsed:
            logger.info("Elements: %s", json.dumps(parsed, ensure_ascii=False))

        return {"name": "test-element-discovery", "elapsed_s": elapsed,
                "parsed": parsed is not None, "elements": parsed}


async def main():
    logger.info("╔══════════════════════════════════════════╗")
    logger.info("║  MiMo Tool Calling Validation            ║")
    logger.info("╚══════════════════════════════════════════╝")

    results = []
    total_start = time.perf_counter()

    for test_func in [test_structured_output_json, test_multi_step_navigation, test_element_discovery]:
        try:
            r = await test_func()
            results.append(r)
        except Exception as e:
            logger.error("Test failed: %s", e, exc_info=True)
            results.append({"name": test_func.__name__, "error": str(e)})

    total_elapsed = time.perf_counter() - total_start

    # Summary
    logger.info("=" * 50)
    logger.info("MIMO VALIDATION SUMMARY (%.1fs total)", total_elapsed)
    logger.info("=" * 50)

    pass_count = 0
    fail_count = 0
    for r in results:
        name = r.get("name", "unknown")
        if "error" in r:
            logger.info("❌ %s: %s", name, r["error"])
            fail_count += 1
        elif "json_parsed" in r:
            status = "✅" if r["json_parsed"] else "⚠️"
            logger.info("%s %s: %.1fs json=%s", status, name, r.get("elapsed_s", 0), r["json_parsed"])
            pass_count += 1 if r["json_parsed"] else 0
        elif "success_indication" in r:
            status = "✅" if r["success_indication"] else "⚠️"
            logger.info("%s %s: %.1fs", status, name, r.get("elapsed_s", 0))
            pass_count += 1 if r["success_indication"] else 0
        else:
            logger.info("⚠️ %s: %.1fs", name, r.get("elapsed_s", 0))

    logger.info("──")
    logger.info("MiMo ready for production: %s (%d/%d passed)",
                 "✅ YES" if pass_count >= 2 else "❌ NO — use Gemini or Claude instead",
                 pass_count, len(results))


if __name__ == "__main__":
    asyncio.run(main())
