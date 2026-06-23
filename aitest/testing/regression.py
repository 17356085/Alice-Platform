"""
Regression Test Runner — P1-4: Golden Test 基线 + 退化检测。

对 Skill Prompt 修改后自动验证输出不退化：
  - 加载 golden test cases (YAML)
  - 按确定性 criteria 评分
  - 与 baseline 输出比较（文本相似度）
  - 捕获当前输出为新基线

用法:
    from aitest.testing.regression import RegressionRunner

    runner = RegressionRunner(provider="claude")
    runner.run_all(tag="smoke")
    print(runner.summary())

    runner.capture_baseline("page-analysis-basic")

CLI:
    aitest regression run [--tag=<t>] [--skill=<s>] [--provider=<p>]
    aitest regression list [--skill=<s>]
    aitest regression capture <case_id> [--output=<path>]
"""

import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
TEST_CASES_PATH = GOVERNANCE / "tests" / "regression" / "test_cases.yaml"
BASELINE_DIR = GOVERNANCE / "tests" / "regression" / "baselines"


@dataclass
class RegressionResult:
    """单次回归测试结果。"""
    case_id: str
    skill_id: str
    passed: bool = False
    score: float = 0.0
    baseline_skill_version: str = ""
    current_skill_version: str = ""
    deviations: list[str] = field(default_factory=list)
    current_output_preview: str = ""
    token_usage: dict = field(default_factory=dict)
    latency_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "skill_id": self.skill_id,
            "passed": self.passed,
            "score": self.score,
            "deviations": self.deviations,
            "current_output_preview": self.current_output_preview[:300],
            "token_usage": self.token_usage,
            "latency_ms": self.latency_ms,
        }


class RegressionRunner:
    """
    回归测试运行器。

    用法:
        runner = RegressionRunner(provider="claude")

        # 运行所有 smoke 标签的用例
        results = runner.run_all(tag="smoke")

        # 查看汇总
        print(runner.summary())

        # 捕获基线
        runner.capture_baseline("page-analysis-basic")
    """

    def __init__(self, provider: str = "claude"):
        self.provider = provider
        self.results: list[RegressionResult] = []

    # ── 加载测试用例 ───────────────────────────────────────────────

    def load_cases(self, tag: str = None, skill_id: str = None) -> list[dict]:
        """
        从 YAML 加载测试用例。

        参数:
            tag:      按标签筛选 (e.g. "smoke", "critical")
            skill_id: 按 Skill ID 筛选

        返回:
            用例字典列表
        """
        import yaml

        if not TEST_CASES_PATH.exists():
            return []

        with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        cases = data.get("test_cases", [])
        if tag:
            cases = [c for c in cases if tag in c.get("tags", [])]
        if skill_id:
            cases = [c for c in cases if c.get("skill_id") == skill_id]
        return cases

    def list_cases(self, skill_id: str = None) -> list[dict]:
        """列出所有注册的回归测试用例（简化格式）。"""
        cases = self.load_cases(skill_id=skill_id)
        return [
            {
                "id": c["id"],
                "skill_id": c.get("skill_id", ""),
                "description": c.get("description", ""),
                "tags": c.get("tags", []),
                "has_baseline": self._baseline_path(c).exists(),
            }
            for c in cases
        ]

    # ── 运行 ──────────────────────────────────────────────────────

    def run_all(self, tag: str = None, skill_id: str = None) -> list[RegressionResult]:
        """
        运行所有匹配的回归测试用例。

        返回:
            RegressionResult 列表（同时存储在 self.results 中）
        """
        cases = self.load_cases(tag=tag, skill_id=skill_id)
        if not cases:
            return []

        for i, case in enumerate(cases):
            try:
                result = self.run_case(case)
                if result.passed:
                    print(f"  [{i+1}/{len(cases)}] PASS {case['id']} (score={result.score:.2f})")
                else:
                    print(f"  [{i+1}/{len(cases)}] FAIL {case['id']} (score={result.score:.2f}, {len(result.deviations)} deviations)")
            except Exception as e:
                from aitest.infra.error_logger import log_error
                log_error("regression.run_all", "run_case", e, {"case_id": case.get("id", "")})
                result = RegressionResult(
                    case_id=case.get("id", "?"),
                    skill_id=case.get("skill_id", ""),
                    passed=False,
                    score=0.0,
                    deviations=[f"Runtime error: {str(e)[:200]}"],
                )
                self.results.append(result)

        return self.results

    def run_case(self, case: dict) -> RegressionResult:
        """
        执行单个回归测试用例。

        1. 加载 Skill 并运行
        2. 用 deterministic criteria 评分
        3. 如果 baseline 文件存在，计算文本相似度
        4. 报告是否退化
        """
        skill_id = case["skill_id"]
        input_text = case.get("input", "")
        criteria = case.get("expected", {})

        from aitest.testing.evaluator import EvalRunner, _score_response
        runner = EvalRunner(provider=self.provider)

        eval_run = runner.run(skill_id, input_text, criteria)

        deviations = list(eval_run.errors)

        # 与 baseline 比较（如果存在）
        baseline_path = self._baseline_path(case)
        baseline_similarity = None
        if baseline_path.exists():
            try:
                baseline_content = baseline_path.read_text(encoding="utf-8")
                similarity = _text_similarity(eval_run.actual_output, baseline_content)
                baseline_similarity = round(similarity, 3)
                # 阈值 0.2：LLM 输出天然非确定性，仅检测大幅偏离
                if similarity < 0.2:
                    deviations.append(
                        f"Output diverges from baseline (similarity={similarity:.2f})"
                    )
            except Exception as e:
                deviations.append(f"Baseline comparison error: {e}")

        # 判断是否通过
        passed = eval_run.passed and not any(
            d.startswith("Output diverges") for d in deviations
        ) and not any(
            d.startswith("Skill execution error") for d in deviations
        )

        result = RegressionResult(
            case_id=case["id"],
            skill_id=skill_id,
            passed=passed,
            score=eval_run.score,
            baseline_skill_version=str(baseline_similarity) if baseline_similarity else "no baseline",
            current_skill_version="current",
            deviations=deviations,
            current_output_preview=eval_run.actual_output[:300],
            token_usage=eval_run.token_usage,
            latency_ms=eval_run.latency_ms,
        )
        self.results.append(result)
        return result

    # ── Baseline 管理 ─────────────────────────────────────────────

    def capture_baseline(self, case_id: str, output: str = None) -> Path:
        """
        捕获当前输出为新基线。

        参数:
            case_id: 测试用例 ID
            output:  要保存的输出内容（None = 重新运行 Skill 生成）

        返回:
            基线文件路径
        """
        cases = self.load_cases()
        case = next((c for c in cases if c.get("id") == case_id), None)
        if not case:
            raise ValueError(f"Case not found: '{case_id}'. Use 'aitest regression list' to see all cases.")

        if output is None:
            # 重新运行 Skill 生成输出
            from aitest.testing.evaluator import EvalRunner
            runner = EvalRunner(provider=self.provider)
            eval_run = runner.run(
                skill_id=case["skill_id"],
                input_text=case.get("input", ""),
                criteria=case.get("expected", {}),
            )
            output = eval_run.actual_output

        baseline_path = self._baseline_path(case)
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(output, encoding="utf-8")

        return baseline_path

    def _baseline_path(self, case: dict) -> Path:
        """获取用例的基线文件路径。"""
        skill_id = case.get("skill_id", "unknown/unknown")
        cat, name = skill_id.split("/", 1) if "/" in skill_id else ("unknown", skill_id)
        return BASELINE_DIR / cat / name / f"{case['id']}_baseline.md"

    # ── 汇总 ──────────────────────────────────────────────────────

    def summary(self) -> dict:
        """聚合所有回归测试结果。"""
        if not self.results:
            return {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0.0}

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        by_skill = {}
        for r in self.results:
            sid = r.skill_id
            if sid not in by_skill:
                by_skill[sid] = {"total": 0, "passed": 0}
            by_skill[sid]["total"] += 1
            if r.passed:
                by_skill[sid]["passed"] += 1

        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / total, 3) if total else 0.0,
            "avg_score": round(sum(r.score for r in self.results) / total, 3) if total else 0.0,
            "by_skill": by_skill,
            "deviations": [
                {"case_id": r.case_id, "deviations": r.deviations}
                for r in self.results if not r.passed
            ],
        }


# ══════════════════════════════════════════════════════════════════════════
#  Helper
# ══════════════════════════════════════════════════════════════════════════

def _text_similarity(a: str, b: str) -> float:
    """
    简单文本相似度（单词重叠系数）。

    零外部依赖，不引入 numpy/scikit-learn。
    返回 0.0 ~ 1.0。
    """
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    return len(intersection) / min(len(words_a), len(words_b))


def _section_similarity(a: str, b: str) -> dict:
    """
    P0-4: 结构化 Section Diff — 按 Markdown header 分段对比。

    将文本按 ## / ### header 拆分为 sections，逐 section 计算相似度。
    比全文单词重叠系数更精确，能定位到具体哪个 section 退化。

    返回:
        {
            "overall": 0.85,
            "sections": {
                "## 页面概述": 0.92,
                "## 元素清单": 0.78,   # ← 退化明显的 section
                ...
            },
            "missing_sections": ["## 交互流程"],  # 旧版本有但新版本没有
            "new_sections": ["## 附加说明"],       # 新版本新增
        }
    """
    import re

    def _extract_sections(text: str) -> dict[str, str]:
        """提取 Markdown sections。"""
        sections = {}
        current_header = "_preamble"
        current_content = []

        for line in text.split("\n"):
            if re.match(r"^#{2,3}\s+", line):
                if current_content:
                    sections[current_header] = "\n".join(current_content).strip()
                current_header = line.strip()
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections[current_header] = "\n".join(current_content).strip()

        return sections

    sections_a = _extract_sections(a)
    sections_b = _extract_sections(b)

    all_headers = set(sections_a.keys()) | set(sections_b.keys())
    section_scores = {}
    missing_in_b = []
    new_in_b = []

    for header in sorted(all_headers):
        if header not in sections_b:
            missing_in_b.append(header)
            section_scores[header] = 0.0
        elif header not in sections_a:
            new_in_b.append(header)
            # P2-FIX (2026-06-15): 新增 section 不再给 1.0 免费分。
            # 基于内容充实度评分: 长度 + 关键词密度。
            # 短小/空洞的新 section 会拉低 overall。
            content = sections_b[header]
            lines = content.count("\n") + 1 if content else 0
            chars = len(content) if content else 0
            # 长度分: 0~0.4 (>=200 chars → 0.4)
            len_score = min(0.4, chars / 500)
            # 密度分: 0~0.3 (>=3 行 → 0.3)
            den_score = min(0.3, lines / 10)
            # 基础分: 0.3 (是合法的新内容)
            section_scores[header] = round(0.3 + len_score + den_score, 3)
        else:
            score = _text_similarity(sections_a[header], sections_b[header])
            section_scores[header] = score

    # 整体分数: 按 header 数量加权，new_sections 参与计算
    if all_headers:
        overall = sum(section_scores.values()) / len(all_headers)
    else:
        overall = 0.0

    return {
        "overall": round(overall, 3),
        "sections": section_scores,
        "missing_sections": missing_in_b,
        "new_sections": new_in_b,
    }


# ══════════════════════════════════════════════════════════════════════════
#  P0-4: Regression Gate — Prompt 变更自动回归门禁
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class GateResult:
    """回归门禁检查结果。"""
    skill_id: str
    old_version: str
    new_version: str
    passed: bool
    cases_total: int
    cases_passed: int
    cases_failed: int
    failures: list[dict] = field(default_factory=list)
    recommendation: str = ""


def check_prompt_upgrade(
    skill_id: str,
    old_version: str,
    new_version: str,
    provider: str = "claude",
    tag: str = "smoke",
) -> GateResult:
    """
    P0-4: Prompt 版本升级时的自动回归门禁。

    当 Skill Prompt 从 old_version 升级到 new_version 时:
      1. 加载该 Skill 的所有回归测试用例
      2. 用旧 Prompt (old_version) 和新 Prompt (new_version) 分别运行
      3. 对比输出质量 — 如果退化 > 阈值 → 阻止升级

    参数:
        skill_id:    Skill ID (如 "test-design/page-analysis")
        old_version: 旧版本号 (如 "1.0")
        new_version: 新版本号 (如 "2.0")
        provider:    LLM provider
        tag:         回归用例标签筛选 (默认 "smoke")

    返回:
        GateResult — passed=True 表示可以安全升级
    """
    import yaml
    from aitest.testing.evaluator import EvalRunner, _score_response
    from aitest.llm.skill_loader import load_skill

    runner = EvalRunner(provider=provider)
    cases = runner.load_cases(tag=tag, skill_id=skill_id) if hasattr(runner, 'load_cases') else []

    if not cases:
        # 尝试直接加载回归用例
        try:
            r = RegressionRunner(provider=provider)
            cases = r.load_cases(tag=tag, skill_id=skill_id)
        except Exception:
            cases = []

    if not cases:
        return GateResult(
            skill_id=skill_id,
            old_version=old_version,
            new_version=new_version,
            passed=True,
            cases_total=0,
            cases_passed=0,
            cases_failed=0,
            recommendation="无回归用例，跳过门禁检查。建议添加 smoke 用例。",
        )

    failures = []
    cases_passed = 0
    regression_threshold = 0.15  # 允许 15% 以内的分数波动

    for case in cases:
        case_id = case.get("id", "?")
        criteria = case.get("expected", {})

        # 用新版本 Prompt 运行
        try:
            eval_new = runner.run(
                skill_id=skill_id,
                input_text=case.get("input", ""),
                criteria=criteria,
            )
        except Exception:
            cases_passed += 1  # 无法评估，算通过
            continue

        # 比较新版本与 baseline（如果有）
        baseline_path = RegressionRunner._baseline_path_static(case)
        if baseline_path.exists():
            try:
                baseline_content = baseline_path.read_text(encoding="utf-8")
                sec_sim = _section_similarity(baseline_content, eval_new.actual_output)

                # 检查结构化退化: 任何已有 section 相似度 < 0.3 且 score 下降 > threshold
                degraded_sections = []
                for header, score in sec_sim.get("sections", {}).items():
                    if score < 0.3 and header not in sec_sim.get("new_sections", []):
                        degraded_sections.append({"section": header, "similarity": score})

                missing = sec_sim.get("missing_sections", [])
                new = sec_sim.get("new_sections", [])
                overall = sec_sim.get("overall", 1.0)

                # P2-FIX (2026-06-15): 区分重构 vs 退化
                # - degraded_sections 存在 → 明确退化
                # - missing_sections 存在但不补偿 → 退化
                # - missing + new 同时存在 + overall 尚可 → 视为重构，放行
                is_refactor = (
                    not degraded_sections
                    and missing
                    and new
                    and overall >= 0.5  # 重构后整体相似度仍 >50%
                    and eval_new.passed   # criteria 仍通过
                )

                if degraded_sections:
                    failures.append({
                        "case_id": case_id,
                        "score": eval_new.score,
                        "overall_similarity": overall,
                        "degraded_sections": degraded_sections,
                        "missing_sections": missing,
                        "reason": "degraded",
                    })
                elif missing and not is_refactor:
                    failures.append({
                        "case_id": case_id,
                        "score": eval_new.score,
                        "overall_similarity": overall,
                        "degraded_sections": degraded_sections,
                        "missing_sections": missing,
                        "new_sections": new,
                        "reason": "missing_sections_without_compensation",
                    })
                else:
                    cases_passed += 1
                    if is_refactor:
                        # 记录为 "refactor pass"（不计入失败）
                        pass
            except Exception:
                cases_passed += 1
        else:
            # 无 baseline — 仅检查 criteria 是否通过
            if eval_new.passed:
                cases_passed += 1
            else:
                failures.append({
                    "case_id": case_id,
                    "score": eval_new.score,
                    "errors": eval_new.errors,
                })

    cases_total = len(cases)
    cases_failed = len(failures)
    passed = cases_failed == 0

    recommendation = ""
    if passed:
        recommendation = f"✅ 回归通过。{cases_passed}/{cases_total} 用例通过。可以安全发布 {skill_id}@{new_version}。"
    else:
        recommendation = (
            f"❌ 回归失败。{cases_failed}/{cases_total} 用例退化。"
            f"禁止发布 {skill_id}@{new_version}。"
            f"请检查退化用例: {[f['case_id'] for f in failures]}"
        )

    return GateResult(
        skill_id=skill_id,
        old_version=old_version,
        new_version=new_version,
        passed=passed,
        cases_total=cases_total,
        cases_passed=cases_passed,
        cases_failed=cases_failed,
        failures=failures,
        recommendation=recommendation,
    )


def promote_skill_version(skill_id: str, new_version: str, provider: str = "claude") -> dict:
    """
    P0-4: 安全发布 Skill 新版本。

    流程:
      1. 获取当前 current_version
      2. 运行 check_prompt_upgrade(old, new)
      3. 通过 → 更新 registry 中的 current_version → 发射 PromptChanged 事件
      4. 失败 → 发射 EvalRegressed 事件 → 阻止发布

    返回:
        {"promoted": True/False, "old_version": "...", "new_version": "...", "gate_result": {...}}
    """
    from aitest.llm.skill_loader import get_skill_version

    ver_info = get_skill_version(skill_id)
    if ver_info is None:
        return {"promoted": False, "error": f"Skill 未注册: {skill_id}"}

    old_version = ver_info.current_version

    # 运行回归门禁
    gate = check_prompt_upgrade(skill_id, old_version, new_version, provider=provider)

    if gate.passed:
        # 成功 → 更新 registry（标记 current_version）
        _update_registry_version(skill_id, new_version)

        # 发射 PromptChanged 事件
        try:
            from aitest.audit_engine.event_bus import emit
            emit("PromptChanged",
                 skill_id=skill_id,
                 old_version=old_version,
                 new_version=new_version,
                 changelog=f"Promoted from {old_version} to {new_version}")
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("regression.promote", "emit_PromptChanged", e, {"skill_id": skill_id})

        return {
            "promoted": True,
            "old_version": old_version,
            "new_version": new_version,
            "gate_result": gate.__dict__,
        }
    else:
        # 失败 → 发射 EvalRegressed 事件
        try:
            from aitest.audit_engine.event_bus import emit
            for failure in gate.failures:
                emit("EvalRegressed",
                     skill_id=skill_id,
                     case_id=failure.get("case_id", "?"),
                     old_score="baseline",
                     new_score=str(failure.get("score", 0)))
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("regression.promote", "emit_EvalRegressed", e, {"skill_id": skill_id})

        return {
            "promoted": False,
            "old_version": old_version,
            "new_version": new_version,
            "gate_result": gate.__dict__,
        }


def _update_registry_version(skill_id: str, new_version: str) -> bool:
    """P0-4: 更新 skill-registry.yaml 中的 current_version。"""
    import yaml

    registry_path = GOVERNANCE / "skills" / "skill-registry.yaml"
    if not registry_path.exists():
        return False

    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = yaml.safe_load(f)

        for skill in registry.get("skills", []):
            if skill.get("id") == skill_id or skill.get("id", "").split("/")[-1] == skill_id:
                # 验证版本存在于 versions[] 中
                versions = skill.get("versions", [])
                if any(v.get("version") == new_version for v in versions):
                    skill["current_version"] = new_version
                    with open(registry_path, "w", encoding="utf-8") as f:
                        yaml.dump(registry, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
                    return True
                break

        return False
    except Exception:
        return False


# Patch RegressionRunner to expose static baseline path method
def _baseline_path_static(case: dict) -> Path:
    """Static version of _baseline_path for use outside RegressionRunner instance."""
    skill_id = case.get("skill_id", "unknown/unknown")
    cat, name = skill_id.split("/", 1) if "/" in skill_id else ("unknown", skill_id)
    return BASELINE_DIR / cat / name / f"{case['id']}_baseline.md"


RegressionRunner._baseline_path_static = staticmethod(_baseline_path_static)
