"""Quality Loop Resources — Dataset/Evaluation/Experiment (P5-1)

数据库表定义：支持质量闭环
- Dataset: 测试样本集合
- Evaluation: 评估任务（在 Dataset 上运行 Agent）
- Experiment: A/B 对比实验
"""

from sqlalchemy import Column, String, Text, Integer, DateTime
from sqlalchemy.sql import func
from aitest.infra.db import Base


class DatasetModel(Base):
    """Dataset 表 — 测试样本集合"""
    __tablename__ = "datasets"

    dataset_id = Column(String(64), primary_key=True)
    name = Column(String(256), nullable=False)
    type = Column(String(32), nullable=False)  # "test_cases" | "conversations" | "prompts"
    project_id = Column(String(64), default="")
    org_id = Column(String(64), default="", index=True)
    created_by = Column(String(64), default="")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # JSONB 字段（存储为 JSON string）
    examples = Column(Text, default="[]")  # List[Example]
    metadata = Column(Text, default="{}")  # Optional metadata


class EvaluationModel(Base):
    """Evaluation 表 — 评估任务"""
    __tablename__ = "evaluations"

    evaluation_id = Column(String(64), primary_key=True)
    name = Column(String(256), nullable=False)
    dataset_id = Column(String(64), nullable=False, index=True)
    agent_id = Column(String(64), nullable=False)
    agent_version = Column(String(64), default="latest")

    org_id = Column(String(64), default="", index=True)
    created_by = Column(String(64), default="")
    status = Column(String(32), default="pending", index=True)  # pending/running/completed/failed

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # JSONB 字段
    evaluator_config = Column(Text, default="{}")  # EvaluatorConfig (judge model, metrics)
    results = Column(Text, default="{}")  # EvaluationResult (pass_rate, metrics)
    error_message = Column(Text, default="")


class ExperimentModel(Base):
    """Experiment 表 — A/B 对比实验"""
    __tablename__ = "experiments"

    experiment_id = Column(String(64), primary_key=True)
    name = Column(String(256), nullable=False)
    baseline_eval_id = Column(String(64), nullable=False, index=True)
    candidate_eval_id = Column(String(64), nullable=False, index=True)

    org_id = Column(String(64), default="", index=True)
    created_by = Column(String(64), default="")
    status = Column(String(32), default="pending")  # pending/analyzing/completed
    decision = Column(String(32), default="pending")  # "promote" | "reject" | "pending"

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime)

    # JSONB 字段
    comparison = Column(Text, default="{}")  # ComparisonResult (diff, winner)
    metadata = Column(Text, default="{}")
