"""Quality Store — Dataset/Evaluation/Experiment 数据访问层 (P5-1)"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from aitest.infra.db import get_db_session
from aitest.platform.quality_models import DatasetModel, EvaluationModel, ExperimentModel
from aitest.platform.quality import (
    Dataset, Evaluation, Experiment,
    Example, EvaluatorConfig, EvaluationResult, ComparisonResult
)


class QualityStore:
    """统一的质量资源存储"""

    def __init__(self):
        self.session = get_db_session()
        self._ensure_quality_tables()

    def _ensure_quality_tables(self):
        """确保质量表存在（自动迁移）"""
        try:
            if self.session.get_bind().dialect.name != "sqlite":
                return
            from sqlalchemy import text
            # 检查 datasets 表是否存在
            result = self.session.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='datasets'"
            )).fetchone()
            
            if not result:
                # 执行迁移脚本
                from pathlib import Path
                migration_file = Path(__file__).parent.parent.parent / "migrations" / "add_quality_tables_sqlite.sql"
                if migration_file.exists():
                    with open(migration_file, 'r', encoding='utf-8') as f:
                        sql = f.read()
                    # 分割并执行每条 SQL
                    for statement in sql.split(';'):
                        statement = statement.strip()
                        if statement and not statement.startswith('--'):
                            self.session.execute(text(statement))
                    self.session.commit()
        except Exception as e:
            # 迁移失败不阻塞启动
            print(f"[WARN] Quality tables migration failed: {e}")

    # ── Dataset ─────────────────────────────────────────────────────────

    def create_dataset(
        self,
        name: str,
        type: str,
        project_id: str = "",
        org_id: str = "",
        created_by: str = "",
        examples: List[Example] = None,
        metadata: dict = None,
    ) -> Dataset:
        """创建 Dataset"""
        dataset_id = f"ds_{uuid.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc).isoformat()

        model = DatasetModel(
            dataset_id=dataset_id,
            name=name,
            type=type,
            project_id=project_id,
            org_id=org_id,
            created_by=created_by,
            examples=json.dumps([
                {
                    "input": ex.input,
                    "expected_output": ex.expected_output,
                    "metadata": ex.metadata,
                }
                for ex in (examples or [])
            ]),
            metadata_json=json.dumps(metadata or {}),
        )

        self.session.add(model)
        self.session.commit()

        return self._row_to_dataset(model)

    def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """获取 Dataset"""
        model = self.session.query(DatasetModel).filter_by(dataset_id=dataset_id).first()
        if not model:
            return None
        return self._row_to_dataset(model)

    def list_datasets(
        self,
        project_id: Optional[str] = None,
        org_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dataset]:
        """列出 Datasets"""
        query = self.session.query(DatasetModel)

        if project_id:
            query = query.filter_by(project_id=project_id)
        if org_id:
            query = query.filter_by(org_id=org_id)

        models = query.order_by(DatasetModel.created_at.desc()).limit(limit).all()
        return [self._row_to_dataset(m) for m in models]

    def add_examples(self, dataset_id: str, examples: List[Example]) -> bool:
        """向 Dataset 添加样本"""
        model = self.session.query(DatasetModel).filter_by(dataset_id=dataset_id).first()
        if not model:
            return False

        existing = json.loads(model.examples or "[]")
        new_examples = [
            {
                "input": ex.input,
                "expected_output": ex.expected_output,
                "metadata": ex.metadata,
            }
            for ex in examples
        ]
        existing.extend(new_examples)

        model.examples = json.dumps(existing)
        self.session.commit()
        return True

    def _row_to_dataset(self, row: DatasetModel) -> Dataset:
        """DB row → Dataset dataclass"""
        examples_data = json.loads(row.examples or "[]")
        examples = [
            Example(
                input=ex.get("input", {}),
                expected_output=ex.get("expected_output"),
                metadata=ex.get("metadata", {}),
            )
            for ex in examples_data
        ]

        return Dataset(
            dataset_id=row.dataset_id,
            name=row.name,
            type=row.type,
            project_id=row.project_id,
            org_id=row.org_id,
            created_by=row.created_by,
            created_at=row.created_at.isoformat() if row.created_at else "",
            updated_at=row.updated_at.isoformat() if row.updated_at else "",
            examples=examples,
            metadata=json.loads(row.metadata_json or "{}"),
        )

    # ── Evaluation ──────────────────────────────────────────────────────

    def create_evaluation(
        self,
        name: str,
        dataset_id: str,
        agent_id: str,
        agent_version: str = "latest",
        org_id: str = "",
        created_by: str = "",
        evaluator_config: Optional[EvaluatorConfig] = None,
    ) -> Evaluation:
        """创建 Evaluation"""
        evaluation_id = f"eval_{uuid.uuid4().hex[:16]}"
        config = evaluator_config or EvaluatorConfig()

        model = EvaluationModel(
            evaluation_id=evaluation_id,
            name=name,
            dataset_id=dataset_id,
            agent_id=agent_id,
            agent_version=agent_version,
            org_id=org_id,
            created_by=created_by,
            status="pending",
            evaluator_config=json.dumps({
                "judge_model": config.judge_model,
                "metrics": config.metrics,
                "custom_rubric": config.custom_rubric,
            }),
        )

        self.session.add(model)
        self.session.commit()

        return self._row_to_evaluation(model)

    def get_evaluation(self, evaluation_id: str) -> Optional[Evaluation]:
        """获取 Evaluation"""
        model = self.session.query(EvaluationModel).filter_by(evaluation_id=evaluation_id).first()
        if not model:
            return None
        return self._row_to_evaluation(model)

    def list_evaluations(
        self,
        *,
        org_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Evaluation]:
        """列出 Evaluation，支持全局质量工作台的只读查询。"""
        query = self.session.query(EvaluationModel)
        if org_id:
            query = query.filter_by(org_id=org_id)
        if status:
            query = query.filter_by(status=status)
        models = query.order_by(EvaluationModel.created_at.desc()).limit(limit).all()
        return [self._row_to_evaluation(model) for model in models]

    def update_evaluation_status(
        self,
        evaluation_id: str,
        status: str,
        results: Optional[EvaluationResult] = None,
        error_message: str = "",
    ) -> bool:
        """更新 Evaluation 状态"""
        model = self.session.query(EvaluationModel).filter_by(evaluation_id=evaluation_id).first()
        if not model:
            return False

        model.status = status
        if status == "running" and not model.started_at:
            model.started_at = datetime.now(timezone.utc)
        if status in ("completed", "failed"):
            model.completed_at = datetime.now(timezone.utc)

        if results:
            model.results = json.dumps({
                "pass_rate": results.pass_rate,
                "total_examples": results.total_examples,
                "passed_examples": results.passed_examples,
                "failed_examples": results.failed_examples,
                "metrics": results.metrics,
                "details": results.details,
            })

        if error_message:
            model.error_message = error_message

        self.session.commit()
        return True

    def _row_to_evaluation(self, row: EvaluationModel) -> Evaluation:
        """DB row → Evaluation dataclass"""
        config_data = json.loads(row.evaluator_config or "{}")
        config = EvaluatorConfig(
            judge_model=config_data.get("judge_model", "claude-3-5-sonnet-20241022"),
            metrics=config_data.get("metrics", ["correctness"]),
            custom_rubric=config_data.get("custom_rubric"),
        )

        results = None
        if row.results:
            results_data = json.loads(row.results)
            results = EvaluationResult(
                pass_rate=results_data.get("pass_rate", 0.0),
                total_examples=results_data.get("total_examples", 0),
                passed_examples=results_data.get("passed_examples", 0),
                failed_examples=results_data.get("failed_examples", 0),
                metrics=results_data.get("metrics", {}),
                details=results_data.get("details", []),
            )

        return Evaluation(
            evaluation_id=row.evaluation_id,
            name=row.name,
            dataset_id=row.dataset_id,
            agent_id=row.agent_id,
            agent_version=row.agent_version,
            org_id=row.org_id,
            created_by=row.created_by,
            status=row.status,
            created_at=row.created_at.isoformat() if row.created_at else "",
            started_at=row.started_at.isoformat() if row.started_at else None,
            completed_at=row.completed_at.isoformat() if row.completed_at else None,
            evaluator_config=config,
            results=results,
            error_message=row.error_message,
        )

    # ── Experiment ──────────────────────────────────────────────────────

    def create_experiment(
        self,
        name: str,
        baseline_eval_id: str,
        candidate_eval_id: str,
        org_id: str = "",
        created_by: str = "",
        metadata: dict = None,
    ) -> Experiment:
        """创建 Experiment"""
        experiment_id = f"exp_{uuid.uuid4().hex[:16]}"

        model = ExperimentModel(
            experiment_id=experiment_id,
            name=name,
            baseline_eval_id=baseline_eval_id,
            candidate_eval_id=candidate_eval_id,
            org_id=org_id,
            created_by=created_by,
            status="pending",
            decision="pending",
            metadata_json=json.dumps(metadata or {}),
        )

        self.session.add(model)
        self.session.commit()

        return self._row_to_experiment(model)

    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """获取 Experiment"""
        model = self.session.query(ExperimentModel).filter_by(experiment_id=experiment_id).first()
        if not model:
            return None
        return self._row_to_experiment(model)

    def update_experiment_result(
        self,
        experiment_id: str,
        comparison: ComparisonResult,
        decision: str = "pending",
    ) -> bool:
        """更新 Experiment 结果"""
        model = self.session.query(ExperimentModel).filter_by(experiment_id=experiment_id).first()
        if not model:
            return False

        model.status = "completed"
        model.decision = decision
        model.completed_at = datetime.now(timezone.utc)
        model.comparison = json.dumps({
            "winner": comparison.winner,
            "baseline_score": comparison.baseline_score,
            "candidate_score": comparison.candidate_score,
            "improvement_pct": comparison.improvement_pct,
            "metrics_diff": comparison.metrics_diff,
            "details": comparison.details,
        })

        self.session.commit()
        return True

    def _row_to_experiment(self, row: ExperimentModel) -> Experiment:
        """DB row → Experiment dataclass"""
        comparison = None
        if row.comparison:
            comp_data = json.loads(row.comparison)
            comparison = ComparisonResult(
                winner=comp_data.get("winner", "tie"),
                baseline_score=comp_data.get("baseline_score", 0.0),
                candidate_score=comp_data.get("candidate_score", 0.0),
                improvement_pct=comp_data.get("improvement_pct", 0.0),
                metrics_diff=comp_data.get("metrics_diff", {}),
                details=comp_data.get("details", {}),
            )

        return Experiment(
            experiment_id=row.experiment_id,
            name=row.name,
            baseline_eval_id=row.baseline_eval_id,
            candidate_eval_id=row.candidate_eval_id,
            org_id=row.org_id,
            created_by=row.created_by,
            status=row.status,
            decision=row.decision,
            created_at=row.created_at.isoformat() if row.created_at else "",
            completed_at=row.completed_at.isoformat() if row.completed_at else None,
            comparison=comparison,
            metadata=json.loads(row.metadata_json or "{}"),
        )


# Singleton instance
_store: Optional[QualityStore] = None


def get_quality_store() -> QualityStore:
    """获取 QualityStore 单例"""
    global _store
    if _store is None:
        _store = QualityStore()
    return _store
