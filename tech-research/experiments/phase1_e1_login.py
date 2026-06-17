"""Phase 1 E1: Login verification.
Usage:
    python tech-research/experiments/phase1_e1_login.py
"""
import asyncio
import logging
import sys
import time
from pathlib import Path

_PROJECT = Path(__file__).resolve().parent.parent.parent / "ZJSN_Test-master526"
sys.path.insert(0, str(_PROJECT))

from base.bu_driver import BrowserUseDriver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("phase1.e1")


async def main():
    logger.info("=" * 50)
    logger.info("E1: Login flow verification")
    logger.info("=" * 50)

    async with BrowserUseDriver(headless=False) as bu:
        t0 = time.perf_counter()
        result = await bu.login()
        elapsed = time.perf_counter() - t0

        logger.info("Login done: %.1fs", elapsed)
        logger.info("Tokens: %d (~$%.4f)", bu.total_tokens, bu.estimated_cost)
        logger.info("Result preview: %s", str(result)[:200])


if __name__ == "__main__":
    asyncio.run(main())
