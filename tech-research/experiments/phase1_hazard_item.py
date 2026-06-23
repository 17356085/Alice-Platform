"""Phase 1 实验: Browser-Use 驱动 hazard_item 页面

验证:
1. BrowserUseDriver 能否正常登录
2. 能否导航到 hazard_item 页面
3. NL 驱动的页面观察质量（→ 用于 PO 生成）
4. NL 驱动的搜索操作
5. Token 消耗 & 成本

用法:
    cd d:/Desktop/Alice
    python tech-research/experiments/phase1_hazard_item.py
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# 确保项目在 sys.path
_PROJECT = Path(__file__).resolve().parent.parent.parent / "ZJSN_Test-master526"
sys.path.insert(0, str(_PROJECT))

from base.bu_driver import BrowserUseDriver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("phase1")

# ═══════════════════════════════════════════════════════════════════
#  Experiment Config
# ═══════════════════════════════════════════════════════════════════

MODULE = "hazard_item"
HASH_ROUTE = "#/warehouse/hazard/item"
MENU_PATH = "库管管理 → 环保危废管理 → 物品管理"
PAGE_NAME = "环保物品管理"


async def experiment_1_login():
    """实验 1: 验证登录流程"""
    logger.info("=" * 60)
    logger.info("E1: 登录流程验证")
    logger.info("=" * 60)

    async with BrowserUseDriver(headless=False) as bu:
        t0 = time.perf_counter()
        result = await bu.login()
        elapsed = time.perf_counter() - t0

        logger.info("登录耗时: %.1fs", elapsed)
        logger.info("Token 消耗: %d (~$%.4f)", bu.total_tokens, bu.estimated_cost)

    return {"name": "E1-login", "elapsed_s": elapsed, "tokens": bu.total_tokens, "cost": bu.estimated_cost}


async def experiment_2_page_observe():
    """实验 2: 页面结构观察 → 用于 PO 生成"""
    logger.info("=" * 60)
    logger.info("E2: 页面观察 (%s)", PAGE_NAME)
    logger.info("=" * 60)

    async with BrowserUseDriver(headless=False) as bu:
        # 登录 + 导航
        await bu.login()

        t0 = time.perf_counter()

        # 用侧边栏导航到目标页面
        task = f"""
通过侧边栏菜单导航到: {MENU_PATH}

步骤:
1. 在左侧侧边栏找到"库管管理"菜单（可能需要展开），点击
2. 找到"环保危废管理"子菜单，点击
3. 找到"物品管理"子菜单，点击
4. 等待页面加载完成（表格出现）

然后详细观察页面，输出 JSON 格式：

```json
{{
  "page_title": "面包屑或页面标题",
  "search_fields": [
    {{"label": "字段名", "type": "input|select|date", "placeholder": "placeholder文本", "css_selector": "推荐CSS", "xpath": "推荐XPath"}}
  ],
  "action_buttons": [
    {{"label": "按钮文字", "type": "primary|default|danger", "css_selector": "推荐CSS", "xpath": "推荐XPath"}}
  ],
  "table_columns": ["列名1", "列名2", ...],
  "has_pagination": true/false,
  "dialog_fields": ["如果点新增按钮会弹出弹窗，列出弹窗中的表单字段"]
}}
```

注意:
- 这是 Element Plus 2.x 应用，表格 class 含 el-table__header
- 搜索条件可能在 el-form--inline 中
- 优先用语义化 CSS selector (如 input[placeholder*="..."]) 而非动态 class
"""
        result = await bu.run_task(task, max_steps=25)
        elapsed = time.perf_counter() - t0

        logger.info("观察耗时: %.1fs", elapsed)
        logger.info("Token 消耗: %d (~$%.4f)", bu.total_tokens, bu.estimated_cost)

        # 尝试提取 JSON
        try:
            text = str(result)
            # 找 JSON 块
            json_str = None
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0]
            elif "{" in text:
                json_str = text[text.index("{"):text.rindex("}") + 1]

            if json_str:
                parsed = json.loads(json_str)
                logger.info("页面结构解析成功:\n%s", json.dumps(parsed, ensure_ascii=False, indent=2))
            else:
                parsed = None
                logger.info("未能提取 JSON，原始输出:\n%s", text[:500])
        except Exception as e:
            parsed = None
            logger.warning("JSON 解析失败: %s", e)

    return {
        "name": "E2-page-observe",
        "elapsed_s": elapsed,
        "tokens": bu.total_tokens,
        "cost": bu.estimated_cost,
        "parsed_json": parsed,
    }


async def experiment_3_search():
    """实验 3: NL 驱动的搜索操作"""
    logger.info("=" * 60)
    logger.info("E3: 搜索操作 (%s)", PAGE_NAME)
    logger.info("=" * 60)

    async with BrowserUseDriver(headless=False) as bu:
        await bu.login()

        t0 = time.perf_counter()

        task = f"""
导航到: {MENU_PATH}

然后在搜索区域:
1. 找到"危废品名称"输入框，输入"测试"
2. 点击"查询"按钮
3. 等待表格刷新
4. 观察表格结果（可能为空或有数据），报告当前表格行数
5. 如果有分页，报告总条数
"""
        result = await bu.run_task(task, max_steps=20)
        elapsed = time.perf_counter() - t0

        logger.info("搜索耗时: %.1fs", elapsed)
        logger.info("Token 消耗: %d (~$%.4f)", bu.total_tokens, bu.estimated_cost)
        logger.info("搜索结果:\n%s", str(result)[:300])

    return {
        "name": "E3-search",
        "elapsed_s": elapsed,
        "tokens": bu.total_tokens,
        "cost": bu.estimated_cost,
    }


async def experiment_4_crud():
    """实验 4: 完整 CRUD 链路 — 新增 + 验证 + 删除"""
    logger.info("=" * 60)
    logger.info("E4: 完整 CRUD (%s)", PAGE_NAME)
    logger.info("=" * 60)

    test_name = "BU测试物品"

    async with BrowserUseDriver(headless=False) as bu:
        await bu.login()

        t0 = time.perf_counter()

        task = f"""
导航到: {MENU_PATH}

完成以下完整 CRUD 操作:

**新建**:
1. 找到并点击"新增"按钮
2. 在弹出的对话框中，填写表单：
   - 找到危废品名称输入框，填入"{test_name}"
   - 其他必填字段根据实际表单填写合理值（如编号/类别下拉框选择第一个可用选项）
3. 点击"确定"或"保存"按钮
4. 等待弹窗关闭，观察是否有成功提示（toast）

**验证**:
5. 在搜索区域输入"{test_name}"
6. 点击查询
7. 确认表格中出现了刚创建的数据

**清理**:
8. 在表格中找到"{test_name}"所在行
9. 点击该行的"删除"按钮
10. 在弹出的确认框中点击"确定"
11. 确认数据已从表格中消失

如果任何步骤失败，记录具体原因。
"""
        result = await bu.run_task(task, max_steps=30)
        elapsed = time.perf_counter() - t0

        logger.info("CRUD 耗时: %.1fs", elapsed)
        logger.info("Token 消耗: %d (~$%.4f)", bu.total_tokens, bu.estimated_cost)
        logger.info("CRUD 结果:\n%s", str(result)[:500])

    return {
        "name": "E4-CRUD",
        "elapsed_s": elapsed,
        "tokens": bu.total_tokens,
        "cost": bu.estimated_cost,
    }


async def main():
    """运行所有 Phase 1 实验"""
    logger.info("╔══════════════════════════════════════════╗")
    logger.info("║  Phase 1: Browser-Use 实验验证           ║")
    logger.info("║  模块: %s                     ║", PAGE_NAME)
    logger.info("╚══════════════════════════════════════════╝")

    results = []

    # E1: 登录
    try:
        r = await experiment_1_login()
        results.append(r)
    except Exception as e:
        logger.error("E1 失败: %s", e)
        results.append({"name": "E1-login", "error": str(e)})

    # E2: 页面观察
    try:
        r = await experiment_2_page_observe()
        results.append(r)
    except Exception as e:
        logger.error("E2 失败: %s", e)
        results.append({"name": "E2-page-observe", "error": str(e)})

    # E3: 搜索
    try:
        r = await experiment_3_search()
        results.append(r)
    except Exception as e:
        logger.error("E3 失败: %s", e)
        results.append({"name": "E3-search", "error": str(e)})

    # E4: CRUD
    try:
        r = await experiment_4_crud()
        results.append(r)
    except Exception as e:
        logger.error("E4 失败: %s", e)
        results.append({"name": "E4-CRUD", "error": str(e)})

    # ═══════════════════════════════════════════════════════════════
    #  Summary
    # ═══════════════════════════════════════════════════════════════
    logger.info("=" * 60)
    logger.info("实验汇总")
    logger.info("=" * 60)

    total_tokens = 0
    total_cost = 0.0
    total_elapsed = 0.0

    for r in results:
        status = "❌" if "error" in r else "✅"
        logger.info(
            "%s %s: %.1fs | tokens=%s | cost=$%.4f",
            status,
            r["name"],
            r.get("elapsed_s", 0),
            r.get("tokens", "N/A"),
            r.get("cost", 0),
        )
        if "error" in r:
            logger.info("   Error: %s", r["error"])
        total_tokens += r.get("tokens", 0)
        total_cost += r.get("cost", 0)
        total_elapsed += r.get("elapsed_s", 0)

    logger.info("──")
    logger.info("总计: %.1fs | tokens=%d | cost=$%.4f", total_elapsed, total_tokens, total_cost)

    # 保存结果到文件
    report_file = Path(__file__).parent / "phase1_results.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "summary": {
                    "total_elapsed_s": total_elapsed,
                    "total_tokens": total_tokens,
                    "total_cost_usd": total_cost,
                },
                "experiments": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    logger.info("结果已保存: %s", report_file)


if __name__ == "__main__":
    asyncio.run(main())
