"""Quality Loop Dataclasses — Dataset/Evaluation/Experiment (P5-1)"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class Example:
    """单个测试样本"""
    input: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Dataset:
    """测试样本集合"""
    dataset_id: str
    name: str
    type: str  # "test_cases" | "conversations" | "prompts"
    project_id: str = ""
    org_id: str = ""
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""
    examples: List[Example] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "type": self.type,
            "project_id": self.project_id,
            "org_id": self.org_id,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "examples": [
                {
                    "input": ex.input,
                    "expected_output": ex.expected_output,
                    "metadata": ex.metadata,
                }
                for ex in self.examples
            ],
            "metadata": self.metadata,
        }


@dataclass
class EvaluatorConfig:
    """评估器配置"""
    judge_model: str = "claude-3-5-sonnet-20241022"
    metrics: List[str] = field(default_factory=lambda: ["correctness", "completeness"])
    custom_rubric: Optional[str] = None


@dataclass
class EvaluationResult:
    """评估结果"""
    pass_rate: float = 0.0
    total_examples: int = 0
    passed_examples: int = 0
    failed_examples: int = 0
    metrics: Dict[str, float] = field(default_factory=dict)
    details: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Evaluation:
    """评估任务"""
    evaluation_id: str
    name: str
    dataset_id: str
    agent_id: str
    agent_version: str = "latest"
    org_id: str = ""
    created_by: str = ""
    status: str = "pending"  # pending/running/completed/failed
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    evaluator_config: EvaluatorConfig = field(default_factory=EvaluatorConfig)
    results: Optional[EvaluationResult] = None
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "name": self.name,
            "dataset_id": self.dataset_id,
            "agent_id": self.agent_id,
            "agent_version": self.agent_version,
            "org_id": self.org_id,
            "created_by": self.created_by,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "evaluator_config": {
                "judge_model": self.evaluator_config.judge_model,
                "metrics": self.evaluator_config.metrics,
                "custom_rubric": self.evaluator_config.custom_rubric,
            },
            "results": {
                "pass_rate": self.results.pass_rate,
                "total_examples": self.results.total_examples,
                "passed_examples": self.results.passed_examples,
                "failed_examples": self.results.failed_examples,
                "metrics": self.results.metrics,
                "details": self.results.details,
            } if self.results else None,
            "error_message": self.error_message,
        }


@dataclass
class ComparisonResult:
    """A/B 对比结果"""
    winner: str  # "baseline" | "candidate" | "tie"
    baseline_score: float = 0.0
    candidate_score: float = 0.0
    improvement_pct: float = 0.0
    metrics_diff: Dict[str, float] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Experiment:
    """A/B 对比实验"""
    experiment_id: str
    name: str
    baseline_eval_id: str
    candidate_eval_id: str
    org_id: str = ""
    created_by: str = ""
    status: str = "pending"  # pending/analyzing/completed
    decision: str = "pending"  # "promote" | "reject" | "pending"
    created_at: str = ""
    completed_at: Optional[str] = None
    comparison: Optional[ComparisonResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "baseline_eval_id": self.baseline_eval_id,
            "candidate_eval_id": self.candidate_eval_id,
            "org_id": self.org_id,
            "created_by": self.created_by,
            "status": self.status,
            "decision": self.decision,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "comparison": {
                "winner": self.comparison.winner,
                "baseline_score": self.comparison.baseline_score,
                "candidate_score": self.comparison.candidate_score,
                "improvement_pct": self.comparison.improvement_pct,
                "metrics_diff": self.comparison.metrics_diff,
                "details": self.comparison.details,
            } if self.comparison else None,
            "metadata": self.metadata,
        }
