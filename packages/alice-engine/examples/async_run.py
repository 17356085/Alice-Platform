"""异步用法 — run_async()。"""

import asyncio
from alice_engine import Engine, Project


async def main():
    project = Project("D:/Desktop/TestingProject/ZJSN_Test-master526")
    engine = Engine(project=project, llm_provider="mock")

    result = await engine.run_async("equipment", pages=["alarm-config"])

    print(f"状态: {result.status}")
    print(f"成功: {result.success}")
    print(f"耗时: {result.elapsed_seconds}s")


if __name__ == "__main__":
    asyncio.run(main())
