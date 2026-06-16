"""
PAGE_INTERFACE.yaml 自动生成器

从 PAGE_CONTEXT.md + TEST_CASES.md 提取结构化接口数据，
生成 automation-agent 可直接消费的 PAGE_INTERFACE.yaml。

Token 优化: automation-agent 优先消费 YAML (~200 tokens) 而非通读 Markdown (~2000 tokens)。
覆盖率: 每个页面生成一次，全 SOP 节省 ~80,000 tokens (40 pages × 2000)。

用法:
  python tools/generate_page_interface.py --module equipment --page alarm-config
  python tools/generate_page_interface.py --module equipment --page alarm-config --dry-run  # 仅预览
  python tools/generate_page_interface.py --module equipment --all  # 所有页面
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

import yaml

WORKSTUDY = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSTUDY))
GOVERNANCE = WORKSTUDY / "governance"
CONTEXT_MODULES = GOVERNANCE / "context" / "projects" / "web-automation" / "modules"
INTERFACES_DIR = GOVERNANCE / "context" / "interfaces"


def read_page_context(module: str, page: str) -> dict:
    """读取页面的 PAGE_CONTEXT.md，提取关键信息。"""
    page_dir = CONTEXT_MODULES / module / "pages" / page
    context_file = page_dir / "PAGE_CONTEXT.md"
    test_file = page_dir / "TEST_CASES.md"
    risk_file = page_dir / "RISK_MODEL.md"

    result = {
        "module": module,
        "page": page,
        "page_context_exists": context_file.exists(),
        "test_cases_exists": test_file.exists(),
        "risk_model_exists": risk_file.exists(),
        "page_context_content": "",
        "test_cases_content": "",
        "risk_model_content": "",
    }

    if context_file.exists():
        result["page_context_content"] = context_file.read_text(encoding="utf-8")
    if test_file.exists():
        result["test_cases_content"] = test_file.read_text(encoding="utf-8")
    if risk_file.exists():
        result["risk_model_content"] = risk_file.read_text(encoding="utf-8")

    return result


def build_llm_prompt(page_info: dict) -> str:
    """构建 LLM prompt，从 PAGE_CONTEXT.md 中提取结构化接口。"""
    return f"""你是一名 Vue 3 + Element Plus 前端测试专家。

请从以下 PAGE_CONTEXT.md 和 TEST_CASES.md 中提取结构化测试接口数据，
生成 PAGE_INTERFACE.yaml。

## 页面信息
模块: {page_info['module']}
页面 slug: {page_info['page']}

## PAGE_CONTEXT.md
{page_info['page_context_content'][:4000]}

## TEST_CASES.md
{page_info['test_cases_content'][:3000]}

## 提取规则
1. **elements**: 从 PAGE_CONTEXT 中提取所有可交互元素，推断:
   - selector: 使用 CSS Selector 或相对 XPath（禁止绝对 XPath）
   - element_type: input/button/select/table/dialog/cascader/switch/datepicker/upload/tag/dropdown/checkbox/radio/textarea/pagination/tree/other
   - interaction: click/input/select/wait/scroll/hover/upload/clear/toggle
   - wait_strategy: wait_vue_stable / WebDriverWait / wait_loading_gone
   - el_component: Element Plus 组件名 (如 el-table, el-dialog, el-cascader)
   - risk_level: low/medium/high

2. **test_scenarios**: 从 TEST_CASES 中提取测试场景:
   - id: TC-XXX
   - title: 场景名称
   - priority: P0/P1/P2
   - type: positive/negative/boundary/destructive/smoke
   - steps_summary: 1-2行简述
   - expected: 预期结果

3. **page_behaviors**: 推断页面行为特征:
   - behavior: 如"表格行内编辑弹窗"/"批量操作后刷新"
   - triggers: 触发条件
   - wait_required: true/false
   - wait_suggestion: 等待建议

## 输出格式
严格按以下 YAML 格式输出（markdown code block 中）:

```yaml
interface: page-to-automation
version: "1.0"
source_agent: test-design-agent
target_agent: automation-agent
generated_at: "{datetime.now().strftime('%Y-%m-%d %H:%M')}"

meta:
  module: "{page_info['module']}"
  page_name: "PascalCase"
  page_slug: "{page_info['page']}"
  page_url: "/{page_info['module']}/{page_info['page']}"
  vue_components:
    - component: el-table
      count: 1
      risk_flags: []

elements:
  - name: "业务名称"
    selector: ".css-selector"
    selector_type: CSS_SELECTOR
    element_type: input
    el_component: el-input
    interaction: input
    wait_strategy: wait_vue_stable
    locator_notes: ""
    risk_level: low
    risk_reason: ""

test_scenarios:
  - id: TC-001
    title: "场景名称"
    priority: P0
    type: positive
    preconditions: []
    steps_summary: "简述"
    expected: "预期结果"
    relates_to_elements: []

page_behaviors:
  - behavior: "表格加载后渲染"
    triggers: ["页面加载", "搜索后"]
    wait_required: true
    wait_suggestion: "wait_vue_stable"
```"""


def generate_interface(module: str, page: str, dry_run: bool = False) -> dict:
    """为指定页面生成 PAGE_INTERFACE.yaml。

    返回: {"status": "generated"|"skipped"|"error", "path": str, "message": str}
    """
    page_dir = CONTEXT_MODULES / module / "pages" / page
    output_path = page_dir / "PAGE_INTERFACE.yaml"

    # 检查前置条件
    page_info = read_page_context(module, page)
    if not page_info["page_context_exists"]:
        return {
            "status": "error",
            "path": str(output_path),
            "message": f"PAGE_CONTEXT.md 不存在: {page_dir / 'PAGE_CONTEXT.md'}",
        }

    # 检查是否已存在且新鲜
    if output_path.exists():
        context_mtime = (page_dir / "PAGE_CONTEXT.md").stat().st_mtime
        interface_mtime = output_path.stat().st_mtime
        if interface_mtime > context_mtime:
            return {
                "status": "skipped",
                "path": str(output_path),
                "message": "PAGE_INTERFACE.yaml 已存在且比 PAGE_CONTEXT.md 更新，跳过",
            }

    if dry_run:
        return {
            "status": "dry_run",
            "path": str(output_path),
            "message": f"将生成: {output_path} (PAGE_CONTEXT: {len(page_info['page_context_content'])} chars)",
        }

    # 调用 LLM 生成
    prompt = build_llm_prompt(page_info)
    try:
        from aitest.llm.provider import get_provider
        llm = get_provider("claude")
        response = llm.complete(
            system_prompt="你是测试接口结构化专家。严格按 YAML 格式输出。输出直接放入 markdown code block。",
            user_prompt=prompt,
            temperature=0.3,
            max_tokens=4096,
        )
    except Exception as e:
        # 尝试 OpenAI fallback
        try:
            llm = get_provider("openai")
            response = llm.complete(
                system_prompt="你是测试接口结构化专家。严格按 YAML 格式输出。",
                user_prompt=prompt,
                temperature=0.3,
                max_tokens=4096,
            )
        except Exception:
            return {
                "status": "error",
                "path": str(output_path),
                "message": f"LLM 调用失败: {str(e)}",
            }

    # 提取 YAML 内容
    content = response.content
    import re
    yaml_match = re.search(r'```(?:yaml)?\s*\n(.*?)\n```', content, re.DOTALL)
    if yaml_match:
        yaml_content = yaml_match.group(1)
    else:
        # 尝试找 interface: 开头
        if 'interface:' in content:
            yaml_content = content[content.index('interface:'):]
        else:
            return {
                "status": "error",
                "path": str(output_path),
                "message": f"LLM 输出无法解析: {content[:200]}",
            }

    # 写入文件
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml_content, encoding="utf-8")

    return {
        "status": "generated",
        "path": str(output_path),
        "message": f"PAGE_INTERFACE.yaml 生成完成 ({len(yaml_content)} chars)",
    }


def generate_all(module: str = None, dry_run: bool = False) -> list[dict]:
    """为模块下所有页面生成 PAGE_INTERFACE.yaml。"""
    results = []
    modules_to_process = [module] if module else [
        d.name for d in CONTEXT_MODULES.iterdir()
        if d.is_dir() and not d.name.startswith(".") and not d.name.startswith("_")
    ]

    for mod in modules_to_process:
        pages_dir = CONTEXT_MODULES / mod / "pages"
        if not pages_dir.exists():
            continue
        for page_dir in sorted(pages_dir.iterdir()):
            if not page_dir.is_dir():
                continue
            page = page_dir.name
            result = generate_interface(mod, page, dry_run=dry_run)
            results.append(result)

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="PAGE_INTERFACE.yaml 自动生成器")
    parser.add_argument("--module", help="模块名")
    parser.add_argument("--page", help="页面名 (slug)")
    parser.add_argument("--all", action="store_true", help="所有页面")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不实际调用 LLM")
    args = parser.parse_args()

    if args.all:
        results = generate_all(module=args.module, dry_run=args.dry_run)
        generated = sum(1 for r in results if r["status"] == "generated")
        skipped = sum(1 for r in results if r["status"] == "skipped")
        errors = sum(1 for r in results if r["status"] == "error")
        dry = sum(1 for r in results if r["status"] == "dry_run")
        print(f"Total: {len(results)} pages")
        print(f"  Generated: {generated}")
        print(f"  Skipped (fresh): {skipped}")
        print(f"  Errors: {errors}")
        if dry:
            print(f"  Dry-run: {dry}")
        for r in results:
            if r["status"] in ("error", "dry_run"):
                print(f"  [{r['status'].upper()}] {r['path']}: {r['message'][:100]}")
    elif args.module and args.page:
        result = generate_interface(args.module, args.page, dry_run=args.dry_run)
        print(f"[{result['status'].upper()}] {result['path']}")
        print(f"  {result['message']}")
    else:
        parser.print_help()
        print("\n示例:")
        print("  python tools/generate_page_interface.py --module equipment --page alarm-config")
        print("  python tools/generate_page_interface.py --module equipment --all --dry-run")
        print("  python tools/generate_page_interface.py --all --dry-run  # 全项目预览")
