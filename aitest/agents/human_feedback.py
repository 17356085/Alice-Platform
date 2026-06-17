"""
Human Feedback Loop — P2-4: 人工评分接口 + Human-as-Judge + 反馈闭环。

功能:
  1. HumanJudge — 收集人工评分
  2. Feedback storage — JSONL 持久化
  3. Golden Standard 管理 — 高质量人工评分升级为 Golden
  4. Feedback 统计 — 分析人工评分与 LLM Judge 的一致性

用法:
    from aitest.agents.human_feedback import HumanJudge, FeedbackCollector

    # 人工评分
    judge = HumanJudge()
    judge.rate(output="...", score=0.85, dimensions={"accuracy": 0.9, "clarity": 0.8})

    # 反馈收集
    collector = FeedbackCollector()
    stats = collector.comparison_stats(days=30)
    print(stats["human_vs_llm_correlation"])

CLI:
    aitest feedback rate --skill=<s> --score=0.85 [--comment="..."]
    aitest feedback stats [--days=30]
    aitest feedback promote <feedback_id>  # 升级为 Golden
"""

import json
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
FEEDBACK_DIR = GOVERNANCE / ".feedback"
FEEDBACK_LOG = FEEDBACK_DIR / "human_feedback.jsonl"
GOLDEN_DIR = GOVERNANCE / "tests" / "regression" / "baselines"
TRACE_LOG = GOVERNANCE / ".traces" / "trace_log.jsonl"


@dataclass
class FeedbackEntry:
    """单条人工反馈记录。"""
    feedback_id: str
    skill_id: str
    output_preview: str        # 前 500 字符
    human_score: float         # 0.0-1.0
    dimensions: dict = field(default_factory=dict)  # {"accuracy": 0.9, ...}
    comment: str = ""
    rater: str = "human"
    promoted_to_golden: bool = False
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "feedback_id": self.feedback_id,
            "skill_id": self.skill_id,
            "output_preview": self.output_preview[:500],
            "human_score": self.human_score,
            "dimensions": self.dimensions,
            "comment": self.comment,
            "rater": self.rater,
            "promoted_to_golden": self.promoted_to_golden,
            "timestamp": self.timestamp,
        }


class HumanJudge:
    """
    P2-4: 人工评分接口。

    用法:
        judge = HumanJudge()
        result = judge.rate(
            skill_id="test-design/page-analysis",
            output="...完整的 PAGE_CONTEXT 输出...",
            score=0.85,
            dimensions={"completeness": 0.9, "accuracy": 0.8},
            comment="元素清单完整，但缺少部分交互流程",
            rater="qa-lead",
        )
    """

    def rate(
        self,
        skill_id: str,
        output: str,
        score: float,
        dimensions: dict = None,
        comment: str = "",
        rater: str = "human",
    ) -> FeedbackEntry:
        """
        记录一条人工评分。

        参数:
            skill_id:   Skill ID
            output:     被评分的完整输出内容
            score:      总体评分 (0.0-1.0)
            dimensions: 各维度评分
            comment:    评分理由/备注
            rater:      评分者标识

        返回:
            FeedbackEntry
        """
        entry = FeedbackEntry(
            feedback_id=f"fb-{uuid.uuid4().hex[:12]}",
            skill_id=skill_id,
            output_preview=output[:500],
            human_score=score,
            dimensions=dimensions or {},
            comment=comment,
            rater=rater,
        )

        FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(FEEDBACK_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        except OSError:
            pass

        return entry

    def batch_rate(
        self,
        items: list[dict],
        rater: str = "human",
    ) -> list[FeedbackEntry]:
        """
        批量评分。

        参数:
            items: [{"skill_id": "...", "output": "...", "score": 0.X, ...}, ...]

        返回:
            [FeedbackEntry, ...]
        """
        results = []
        for item in items:
            entry = self.rate(
                skill_id=item.get("skill_id", ""),
                output=item.get("output", ""),
                score=item.get("score", 0.5),
                dimensions=item.get("dimensions", {}),
                comment=item.get("comment", ""),
                rater=rater,
            )
            results.append(entry)
        return results


class FeedbackCollector:
    """
    P2-4: 反馈收集与统计分析。

    用法:
        collector = FeedbackCollector()
        stats = collector.comparison_stats(days=30)
        print(stats["human_avg"], stats["llm_avg"], stats["correlation"])
    """

    def load_feedback(self, skill_id: str = None, days: int = 30) -> list[FeedbackEntry]:
        """加载最近 N 天的人工反馈。"""
        if not FEEDBACK_LOG.exists():
            return []

        cutoff = datetime.now() - timedelta(days=days)
        entries = []

        try:
            with open(FEEDBACK_LOG, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        ts = datetime.fromisoformat(
                            data.get("timestamp", "2000-01-01T00:00:00")
                        )
                        if ts < cutoff:
                            continue
                        if skill_id and data.get("skill_id") != skill_id:
                            continue
                        entries.append(FeedbackEntry(
                            feedback_id=data.get("feedback_id", ""),
                            skill_id=data.get("skill_id", ""),
                            output_preview=data.get("output_preview", ""),
                            human_score=data.get("human_score", 0.0),
                            dimensions=data.get("dimensions", {}),
                            comment=data.get("comment", ""),
                            rater=data.get("rater", "human"),
                            promoted_to_golden=data.get("promoted_to_golden", False),
                            timestamp=data.get("timestamp", ""),
                        ))
                    except (json.JSONDecodeError, KeyError):
                        continue
        except Exception:
            pass

        return entries

    def comparison_stats(self, skill_id: str = None, days: int = 30) -> dict:
        """
        P2-4: 对比人工评分与 LLM Judge 评分。

        从 Trace 中提取 LLM Judge 的评分（如果有），与人工评分对比。

        返回:
            {
                "total_feedback": 15,
                "human_avg_score": 0.82,
                "llm_avg_score": 0.78,
                "correlation": 0.85,
                "agreement_rate": 0.73,
            }
        """
        feedback = self.load_feedback(skill_id=skill_id, days=days)
        if not feedback:
            return {
                "total_feedback": 0,
                "human_avg_score": 0.0,
                "note": "无人工反馈数据",
            }

        human_scores = [f.human_score for f in feedback]
        human_avg = sum(human_scores) / len(human_scores)

        # 尝试从 Trace 中找到对应时间的 LLM Judge 评分
        # (仅当 evaluator.py 的 LLMJudge 运行后才会有 trace 记录)
        llm_scores = []
        if TRACE_LOG.exists():
            cutoff = datetime.now() - timedelta(days=days)
            try:
                with open(TRACE_LOG, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                            ts = datetime.fromisoformat(
                                entry.get("timestamp", "2000-01-01T00:00:00")
                            )
                            if ts < cutoff:
                                continue
                            meta = entry.get("metadata", {})
                            if isinstance(meta, dict):
                                judge_score = meta.get("llm_judge_score")
                                if judge_score is not None:
                                    llm_scores.append(float(judge_score))
                        except (json.JSONDecodeError, ValueError, KeyError):
                            continue
            except Exception:
                pass

        llm_avg = sum(llm_scores) / len(llm_scores) if llm_scores else 0.0

        # 简单相关性: 如果 human 和 llm 都认为 >= 0.6 为 "pass"
        pass_rate_human = sum(1 for s in human_scores if s >= 0.6) / len(human_scores)
        pass_rate_llm = sum(1 for s in llm_scores if s >= 0.6) / len(llm_scores) if llm_scores else 0.0

        # 分数分布
        distribution = {
            "excellent (>=0.9)": sum(1 for s in human_scores if s >= 0.9),
            "good (0.7-0.9)": sum(1 for s in human_scores if 0.7 <= s < 0.9),
            "fair (0.5-0.7)": sum(1 for s in human_scores if 0.5 <= s < 0.7),
            "poor (<0.5)": sum(1 for s in human_scores if s < 0.5),
        }

        return {
            "total_feedback": len(feedback),
            "period_days": days,
            "human_avg_score": round(human_avg, 3),
            "llm_avg_score": round(llm_avg, 3) if llm_scores else "N/A",
            "human_pass_rate": round(pass_rate_human, 3),
            "llm_pass_rate": round(pass_rate_llm, 3) if llm_scores else "N/A",
            "score_distribution": distribution,
            "agreement_rate": round(
                1.0 - abs(pass_rate_human - pass_rate_llm), 3
            ) if llm_scores else "N/A",
            "top_skills": self._top_rated_skills(feedback),
            "note": "人工评分 vs LLM Judge 一致性分析" if llm_scores else "暂无 LLM Judge 数据",
        }

    def promote_to_golden(self, feedback_id: str, case_id: str = None) -> dict:
        """
        P2-4: 将高质量人工评分升级为 Golden Standard。

        参数:
            feedback_id: 反馈 ID
            case_id:     关联的测试用例 ID

        返回:
            {"promoted": True/False, "golden_path": "..."}
        """
        feedback = self.load_feedback(days=365)  # 全量搜索
        target = None
        for f in feedback:
            if f.feedback_id == feedback_id:
                target = f
                break

        if target is None:
            return {"promoted": False, "error": f"Feedback {feedback_id} not found"}

        if target.human_score < 0.8:
            return {
                "promoted": False,
                "error": f"Score {target.human_score} < 0.8 threshold. 仅 >= 0.8 可升级为 Golden。",
            }

        # 写入 Golden baseline
        skill_id = target.skill_id
        cat, name = skill_id.split("/", 1) if "/" in skill_id else ("unknown", skill_id)
        case_name = case_id or f"human-golden-{feedback_id[-8:]}"
        golden_path = GOLDEN_DIR / cat / name / f"{case_name}_baseline.md"
        golden_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            golden_path.write_text(target.output_preview, encoding="utf-8")
        except OSError as e:
            return {"promoted": False, "error": str(e)}

        # 标记 feedback 为已升级
        target.promoted_to_golden = True

        return {
            "promoted": True,
            "golden_path": str(golden_path),
            "skill_id": skill_id,
            "score": target.human_score,
        }

    def _top_rated_skills(self, feedback: list[FeedbackEntry]) -> list[dict]:
        """统计评分最高的 Skill。"""
        skill_scores: dict[str, list[float]] = {}
        for f in feedback:
            skill_scores.setdefault(f.skill_id, []).append(f.human_score)

        results = []
        for sid, scores in skill_scores.items():
            avg = sum(scores) / len(scores)
            results.append({
                "skill_id": sid,
                "avg_score": round(avg, 3),
                "feedback_count": len(scores),
            })

        results.sort(key=lambda x: -x["avg_score"])
        return results[:5]


# ══════════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python human_feedback.py rate --skill=<s> --score=0.85 [--comment=...] [--rater=...]")
        print("  python human_feedback.py stats [--days=30] [--skill=<s>]")
        print("  python human_feedback.py promote <feedback_id> [--case=<id>]")
        sys.exit(0)

    cmd = sys.argv[1]
    opts = {}
    for arg in sys.argv[2:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            opts[k.lstrip("-")] = v

    if cmd == "rate":
        judge = HumanJudge()
        entry = judge.rate(
            skill_id=opts.get("skill", "unknown"),
            output=opts.get("output", ""),
            score=float(opts.get("score", 0.5)),
            comment=opts.get("comment", ""),
            rater=opts.get("rater", "human"),
        )
        print(f"Feedback recorded: {entry.feedback_id} (score={entry.human_score})")

    elif cmd == "stats":
        collector = FeedbackCollector()
        stats = collector.comparison_stats(
            skill_id=opts.get("skill"),
            days=int(opts.get("days", 30)),
        )
        print(json.dumps(stats, ensure_ascii=False, indent=2))

    elif cmd == "promote":
        if len(sys.argv) < 3:
            print("Usage: python human_feedback.py promote <feedback_id> [--case=<id>]")
            sys.exit(1)
        collector = FeedbackCollector()
        result = collector.promote_to_golden(sys.argv[2], case_id=opts.get("case"))
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        print(f"Unknown command: {cmd}")
