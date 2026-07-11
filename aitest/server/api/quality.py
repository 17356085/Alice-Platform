"""Quality API — Dataset/Evaluation/Experiment endpoints (P5-1)

质量闭环 REST API:
- POST   /api/v1/datasets             — 创建 Dataset
- GET    /api/v1/datasets/:id         — 获取 Dataset
- GET    /api/v1/datasets             — 列出 Datasets
- POST   /api/v1/datasets/:id/examples — 添加样本

- POST   /api/v1/evaluations          — 创建 Evaluation
- GET    /api/v1/evaluations/:id      — 获取 Evaluation

- POST   /api/v1/experiments          — 创建 Experiment
- GET    /api/v1/experiments/:id      — 获取 Experiment
- POST   /api/v1/experiments/:id/promote — 提升候选版本
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

quality_router = APIRouter(prefix="/api/v1", tags=["Quality Loop"])


# ── Request/Response Schemas ────────────────────────────────────────────

class ExampleSchema(BaseModel):
    input: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreateDatasetRequest(BaseModel):
    name: str
    type: str  # "test_cases" | "conversations" | "prompts"
    project_id: str = ""
    examples: List[ExampleSchema] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AddExamplesRequest(BaseModel):
    examples: List[ExampleSchema]


class CreateEvaluationRequest(BaseModel):
    name: str
    dataset_id: str
    agent_id: str
    agent_version: str = "latest"
    evaluator_config: Optional[Dict[str, Any]] = None


class CreateExperimentRequest(BaseModel):
    name: str
    baseline_eval_id: str
    candidate_eval_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ── Dataset Endpoints ───────────────────────────────────────────────────

@quality_router.post("/datasets")
async def create_dataset(req: CreateDatasetRequest, request: Request):
    """创建 Dataset"""
    from aitest.platform.quality_store import get_quality_store
    from aitest.platform.quality import Example

    user_id = getattr(request.state, "user_id", None) or request.headers.get("X-User-Id", "anonymous")
    org_id = getattr(request.state, "org_id", None) or request.headers.get("X-Org-Id", "")

    examples = [
        Example(
            input=ex.input,
            expected_output=ex.expected_output,
            metadata=ex.metadata,
        )
        for ex in req.examples
    ]

    store = get_quality_store()
    dataset = store.create_dataset(
        name=req.name,
        type=req.type,
        project_id=req.project_id,
        org_id=org_id,
        created_by=user_id,
        examples=examples,
        metadata=req.metadata,
    )

    return dataset.to_dict()


@quality_router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str):
    """获取 Dataset"""
    from aitest.platform.quality_store import get_quality_store

    store = get_quality_store()
    dataset = store.get_dataset(dataset_id)

    if not dataset:
        raise HTTPException(404, f"Dataset '{dataset_id}' not found")

    return dataset.to_dict()


@quality_router.get("/datasets")
async def list_datasets(
    project_id: Optional[str] = None,
    org_id: Optional[str] = None,
    limit: int = 50,
):
    """列出 Datasets"""
    from aitest.platform.quality_store import get_quality_store

    store = get_quality_store()
    datasets = store.list_datasets(
        project_id=project_id,
        org_id=org_id,
        limit=min(limit, 100),
    )

    return {
        "datasets": [ds.to_dict() for ds in datasets],
        "total": len(datasets),
    }


@quality_router.post("/datasets/{dataset_id}/examples")
async def add_examples(dataset_id: str, req: AddExamplesRequest):
    """向 Dataset 添加样本"""
    from aitest.platform.quality_store import get_quality_store
    from aitest.platform.quality import Example

    examples = [
        Example(
            input=ex.input,
            expected_output=ex.expected_output,
            metadata=ex.metadata,
        )
        for ex in req.examples
    ]

    store = get_quality_store()
    success = store.add_examples(dataset_id, examples)

    if not success:
        raise HTTPException(404, f"Dataset '{dataset_id}' not found")

    return {"message": f"Added {len(examples)} examples to dataset '{dataset_id}'"}


# ── Evaluation Endpoints ────────────────────────────────────────────────

@quality_router.get("/evaluations")
async def list_evaluations(
    org_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
):
    """列出 Evaluation，供全局质量工作台查询。"""
    from aitest.platform.quality_store import get_quality_store

    store = get_quality_store()
    evaluations = store.list_evaluations(
        org_id=org_id,
        status=status,
        limit=min(limit, 100),
    )
    return {
        "evaluations": [evaluation.to_dict() for evaluation in evaluations],
        "total": len(evaluations),
    }

@quality_router.post("/evaluations")
async def create_evaluation(req: CreateEvaluationRequest, request: Request):
    """创建 Evaluation（评估任务）"""
    from aitest.platform.quality_store import get_quality_store
    from aitest.platform.quality import EvaluatorConfig

    user_id = getattr(request.state, "user_id", None) or request.headers.get("X-User-Id", "anonymous")
    org_id = getattr(request.state, "org_id", None) or request.headers.get("X-Org-Id", "")

    config = None
    if req.evaluator_config:
        config = EvaluatorConfig(
            judge_model=req.evaluator_config.get("judge_model", "claude-3-5-sonnet-20241022"),
            metrics=req.evaluator_config.get("metrics", ["correctness"]),
            custom_rubric=req.evaluator_config.get("custom_rubric"),
        )

    store = get_quality_store()
    evaluation = store.create_evaluation(
        name=req.name,
        dataset_id=req.dataset_id,
        agent_id=req.agent_id,
        agent_version=req.agent_version,
        org_id=org_id,
        created_by=user_id,
        evaluator_config=config,
    )

    return evaluation.to_dict()


@quality_router.get("/evaluations/{evaluation_id}")
async def get_evaluation(evaluation_id: str):
    """获取 Evaluation 状态"""
    from aitest.platform.quality_store import get_quality_store

    store = get_quality_store()
    evaluation = store.get_evaluation(evaluation_id)

    if not evaluation:
        raise HTTPException(404, f"Evaluation '{evaluation_id}' not found")

    return evaluation.to_dict()


# ── Experiment Endpoints ────────────────────────────────────────────────

@quality_router.post("/experiments")
async def create_experiment(req: CreateExperimentRequest, request: Request):
    """创建 Experiment（A/B 对比实验）"""
    from aitest.platform.quality_store import get_quality_store

    user_id = getattr(request.state, "user_id", None) or request.headers.get("X-User-Id", "anonymous")
    org_id = getattr(request.state, "org_id", None) or request.headers.get("X-Org-Id", "")

    store = get_quality_store()

    # 验证两个 Evaluation 存在
    baseline = store.get_evaluation(req.baseline_eval_id)
    if not baseline:
        raise HTTPException(404, f"Baseline evaluation '{req.baseline_eval_id}' not found")

    candidate = store.get_evaluation(req.candidate_eval_id)
    if not candidate:
        raise HTTPException(404, f"Candidate evaluation '{req.candidate_eval_id}' not found")

    experiment = store.create_experiment(
        name=req.name,
        baseline_eval_id=req.baseline_eval_id,
        candidate_eval_id=req.candidate_eval_id,
        org_id=org_id,
        created_by=user_id,
        metadata=req.metadata,
    )

    # TODO: 触发后台对比分析任务

    return experiment.to_dict()


@quality_router.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    """获取 Experiment 结果"""
    from aitest.platform.quality_store import get_quality_store

    store = get_quality_store()
    experiment = store.get_experiment(experiment_id)

    if not experiment:
        raise HTTPException(404, f"Experiment '{experiment_id}' not found")

    return experiment.to_dict()


@quality_router.post("/experiments/{experiment_id}/promote")
async def promote_experiment(experiment_id: str):
    """提升候选版本（将 candidate Agent 标记为生产版本）"""
    from aitest.platform.quality_store import get_quality_store

    store = get_quality_store()
    experiment = store.get_experiment(experiment_id)

    if not experiment:
        raise HTTPException(404, f"Experiment '{experiment_id}' not found")

    if experiment.status != "completed":
        raise HTTPException(400, f"Experiment must be completed before promotion")

    if not experiment.comparison or experiment.comparison.winner != "candidate":
        raise HTTPException(400, f"Can only promote when candidate is the winner")

    # TODO: 实际的 Agent 版本提升逻辑（需要 Agent 版本管理系统）

    # 更新 decision 为 "promote"
    store.update_experiment_result(
        experiment_id=experiment_id,
        comparison=experiment.comparison,
        decision="promote",
    )

    return {
        "message": f"Candidate from experiment '{experiment_id}' promoted to production",
        "experiment_id": experiment_id,
        "decision": "promote",
    }
