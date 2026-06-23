"""
Multi-Provider Verification — 跨模型 Skill 执行对比。

用法:
    python -m aitest.provider_verify                     # 测试所有可用 Provider
    python -m aitest.provider_verify --skill simple       # 仅测试简单 Skill
    python -m aitest.provider_verify --providers claude,deepseek  # 指定 Provider
    python -m aitest.provider_verify --compare            # 对比模式（同 Skill 跨 Provider）

设计:
    1. 每个 Provider 执行 2-3 个不同复杂度的 Skill
    2. 测量延迟 + Token 消耗 + 成本估算
    3. 输出结构化 JSON 结果（可被 CI 消费）
    4. Provider 不可用时跳过而非失败
"""
import sys
import json
import time
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

WORKSTUDY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSTUDY))

# Windows: fix Unicode output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ══════════════════════════════════════════════════════════════════════════
#  Test Skill Matrix — 按复杂度分级
# ══════════════════════════════════════════════════════════════════════════

SKILL_MATRIX = {
    "simple": {
        "skill_id": "knowledge/completeness-check",
        "input": "检查 equipment 模块的文档完整性。列出所有缺失的关键文档。",
        "expected_tokens": 500,
        "tier": "low",
    },
    "medium": {
        "skill_id": "architecture/project-scanner",
        "input": "扫描 aitest/llm/ 目录，分析模块结构、依赖关系和职责划分。列出所有 .py 文件及其功能摘要。",
        "expected_tokens": 1200,
        "tier": "medium",
    },
    "complex": {
        "skill_id": "test-design/page-analysis",
        "input": "分析 equipment/alarm-config 页面的交互模式。模块: equipment, 页面: alarm-config。识别所有可交互元素及其定位策略。",
        "expected_tokens": 2500,
        "tier": "high",
    },
}


@dataclass
class ProviderResult:
    """单个 Provider + Skill 的执行结果。"""
    provider: str
    model: str
    skill_id: str
    skill_tier: str
    success: bool
    content_length: int
    content_preview: str = ""
    token_usage: dict = field(default_factory=dict)
    elapsed_seconds: float = 0.0
    cost_estimate: float = 0.0
    finish_reason: str = ""
    error_message: str = ""


def check_provider_available(provider_name: str) -> tuple[bool, str]:
    """检查 Provider 是否可用（API Key 已配置）。"""
    from aitest.config import config

    if provider_name == "ollama":
        # 检查本地服务可达性
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            base_url = config.ollama_base_url
            host = base_url.replace("http://", "").replace("https://", "").split(":")[0]
            port = int(base_url.split(":")[-1].rstrip("/"))
            s.connect((host, port))
            s.close()
            return True, f"Ollama reachable at {base_url}"
        except Exception:
            s.close()
            return False, "Ollama service not reachable"

    provider_cfg = config.get_provider_config(provider_name)
    if not provider_cfg["api_key"]:
        return False, f"{provider_name} API key not set in environment"
    return True, f"{provider_name} configured"


def estimate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    """估算 LLM 调用成本（美元）。"""
    try:
        from aitest.infra.trace import MODEL_PRICING
    except ImportError:
        return 0.0

    # 按模型名匹配，再降级按 provider
    price = MODEL_PRICING.get(model)
    if not price:
        # 模糊匹配
        for m, p in MODEL_PRICING.items():
            if m in model or model in m:
                price = p
                break
    if not price:
        return 0.0

    input_price, output_price = price
    return (input_tokens / 1_000_000) * input_price + (output_tokens / 1_000_000) * output_price


def run_skill_on_provider(
    skill_id: str,
    user_input: str,
    provider_name: str,
    model: str = "",
) -> ProviderResult:
    """在指定 Provider 上执行一个 Skill。"""
    from aitest.llm.provider import get_provider
    from aitest.llm.skill_loader import load_skill
    from aitest.llm.skill_registry import get_skill_requirements
    from aitest.llm.prompt_adapter import PromptAdapter
    from aitest.llm.context_injector import ContextInjector

    req = get_skill_requirements(skill_id)
    tier = req.get("min_tier", "unknown")

    provider_kwargs = {}
    if model:
        provider_kwargs["model"] = model

    try:
        llm = get_provider(provider_name, **provider_kwargs)
    except Exception as e:
        return ProviderResult(
            provider=provider_name,
            model=model or "default",
            skill_id=skill_id,
            skill_tier=tier,
            success=False,
            content_length=0,
            error_message=f"Provider init failed: {e}",
        )

    # 加载 + 适配 Prompt
    try:
        raw_prompt = load_skill(skill_id)
    except FileNotFoundError as e:
        return ProviderResult(
            provider=provider_name,
            model=llm.model,
            skill_id=skill_id,
            skill_tier=tier,
            success=False,
            content_length=0,
            error_message=f"Skill not found: {e}",
        )

    adapter = PromptAdapter()
    adapted = adapter.adapt(raw_prompt, provider_type=provider_name)

    # 注入上下文
    injector = ContextInjector()
    adapted = injector.inject(skill_id, adapted, variables={
        "module": "equipment",
        "page": "alarm-config",
    })

    # 执行
    t0 = time.perf_counter()
    try:
        response = llm.complete(
            system_prompt=adapted,
            user_prompt=user_input,
            max_tokens=2048,
        )
    except Exception as e:
        return ProviderResult(
            provider=provider_name,
            model=llm.model,
            skill_id=skill_id,
            skill_tier=tier,
            success=False,
            content_length=0,
            elapsed_seconds=time.perf_counter() - t0,
            error_message=str(e),
        )

    elapsed = time.perf_counter() - t0
    input_tokens = response.token_usage.get("input", 0)
    output_tokens = response.token_usage.get("output", 0)
    cost = estimate_cost(provider_name, response.model, input_tokens, output_tokens)

    return ProviderResult(
        provider=provider_name,
        model=response.model,
        skill_id=skill_id,
        skill_tier=tier,
        success=response.finish_reason != "error",
        content_length=len(response.content),
        content_preview=response.content[:200] + ("..." if len(response.content) > 200 else ""),
        token_usage=response.token_usage,
        elapsed_seconds=round(elapsed, 2),
        cost_estimate=round(cost, 6),
        finish_reason=response.finish_reason,
    )


def print_result(result: ProviderResult, index: int = 0):
    """格式化打印单个结果。"""
    icon = "[PASS]" if result.success else "[FAIL]"
    print(f"\n  [{icon}] {result.provider}/{result.model}")
    print(f"      Skill: {result.skill_id} ({result.skill_tier})")
    print(f"      Tokens: {result.token_usage}")
    print(f"      Time: {result.elapsed_seconds}s")
    print(f"      Cost: ${result.cost_estimate:.6f}")
    if result.content_preview:
        preview = result.content_preview[:120].replace("\n", " ")
        print(f"      Output: {preview}...")
    if not result.success:
        print(f"      Error: {result.error_message[:200]}")


def run_verification(
    providers: list[str] = None,
    skills: list[str] = None,
    compare_mode: bool = False,
) -> list[ProviderResult]:
    """主验证逻辑。"""
    if providers is None:
        providers = ["claude", "openai", "deepseek", "ollama"]
    if skills is None:
        skills = ["simple", "medium", "complex"]

    results: list[ProviderResult] = []

    print("=" * 64)
    print("  Multi-Provider Verification")
    print("=" * 64)
    print(f"\n  Providers: {providers}")
    print(f"  Skills: {skills}")
    if compare_mode:
        print(f"  Mode: COMPARE (同 Skill 跨 Provider)")

    # 检查 Provider 可用性
    print("\n─ Provider Availability ─")
    available = []
    for p in providers:
        ok, msg = check_provider_available(p)
        icon = "[OK]" if ok else "[XX]"
        print(f"  {icon} {p}: {msg}")
        if ok:
            available.append(p)

    if not available:
        print("\n⚠️  No providers available. Set API keys in .env and retry.")
        return results

    # 执行测试
    if compare_mode:
        # 对比模式: 同 Skill 跨 Provider
        print("\n─ Compare Mode ─")
        for skill_key in skills:
            skill_info = SKILL_MATRIX.get(skill_key)
            if not skill_info:
                continue
            print(f"\n  ▶ Skill: {skill_info['skill_id']} ({skill_key})")
            for provider_name in available:
                result = run_skill_on_provider(
                    skill_info["skill_id"],
                    skill_info["input"],
                    provider_name,
                )
                results.append(result)
                print_result(result)
    else:
        # 默认模式: 每个 Provider 执行所有 Skill
        print("\n─ Results ─")
        for provider_name in available:
            print(f"\n  ▸ Provider: {provider_name}")
            for skill_key in skills:
                skill_info = SKILL_MATRIX.get(skill_key)
                if not skill_info:
                    continue
                result = run_skill_on_provider(
                    skill_info["skill_id"],
                    skill_info["input"],
                    provider_name,
                )
                results.append(result)
                print_result(result)

    # 摘要
    print(f"\n{'=' * 64}")
    print(f"  Summary: {sum(1 for r in results if r.success)}/{len(results)} succeeded")
    if results:
        successes = [r for r in results if r.success]
        if successes:
            avg_latency = sum(r.elapsed_seconds for r in successes) / len(successes)
            total_cost = sum(r.cost_estimate for r in results)
            print(f"  Avg Latency: {avg_latency:.1f}s")
            print(f"  Total Cost: ${total_cost:.6f}")
    print(f"{'=' * 64}\n")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Provider LLM Verification — 跨模型 Skill 执行对比",
    )
    parser.add_argument(
        "--providers", "-p",
        default="",
        help="Comma-separated providers to test (default: all available). e.g. claude,deepseek",
    )
    parser.add_argument(
        "--skill", "-s",
        default="",
        help="Skill tier to test: simple|medium|complex|all (default: all)",
    )
    parser.add_argument(
        "--compare", "-c",
        action="store_true",
        help="Compare mode: same skill across all providers",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results as JSON (for CI consumption)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check provider availability only, no LLM calls",
    )

    args = parser.parse_args()

    providers = [p.strip() for p in args.providers.split(",") if p.strip()] if args.providers else None
    skills = [args.skill] if args.skill and args.skill != "all" else None

    if args.dry_run:
        print("Provider availability check (dry-run):")
        for p in (providers or ["claude", "openai", "deepseek", "ollama"]):
            ok, msg = check_provider_available(p)
            icon = "[OK]" if ok else "[XX]"
            print(f"  {icon} {p}: {msg}")
        return

    results = run_verification(
        providers=providers,
        skills=skills,
        compare_mode=args.compare,
    )

    if args.json:
        output = [{
            "provider": r.provider,
            "model": r.model,
            "skill_id": r.skill_id,
            "skill_tier": r.skill_tier,
            "success": r.success,
            "content_length": r.content_length,
            "token_usage": r.token_usage,
            "elapsed_seconds": r.elapsed_seconds,
            "cost_estimate": r.cost_estimate,
            "finish_reason": r.finish_reason,
            "error_message": r.error_message,
        } for r in results]
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
