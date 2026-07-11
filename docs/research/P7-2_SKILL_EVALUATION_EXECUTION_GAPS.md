# P7-2 Skill/Evaluation 深度执行 — 研究报告

> **日期**: 2026-07-11  
> **目标**: 调研 `execute_skill()` 和 `execute_evaluation()` 占位实现，明确真实执行引擎的实现路径

---

## 1. 当前占位实现

### 1.1 `execute_skill()` — `aitest/server/api/run_executor.py:163-210`

**当前行为**:
```python
@staticmethod
async def execute_skill(...) -> Dict[str, Any]:
    """执行单个 Skill（占位实现）"""
    # 1. 创建 Run 记录
    run_id = f"run_{uuid.uuid4().hex[:16]}"
    run_store.create_run(
        run_id=run_id,
        workspace_id=ctx.workspace_id,
        org_id=ctx.org_id,
        triggered_by=ctx.user_id,
        agent=target_id,  # skill_id
        module="skill",
        pages=[],
        mode=execution.get("mode", "full"),
        provider=runtime.get("provider", "claude"),
        metadata={
            "target_type": "skill",
            "target_id": target_id,
            "target_version": target_version,
            "prompt": params.get("prompt", ""),
            "context": params.get("context", {}),
        },
    )

    # 2. TODO: 实现 Skill 独立执行逻辑
    run_store.update_run_status(run_id, "pending", error_message="Skill execution not implemented yet")

    return {
        "run_id": run_id,
        "status": "pending",
        "error_message": "Skill execution not implemented yet",
        ...
    }
```

**问题**: 仅创建 Run 记录，但不执行任何实际逻辑。

---

### 1.2 `execute_evaluation()` — `aitest/server/api/run_executor.py:213-292`

**当前行为**:
```python
@staticmethod
async def execute_evaluation(...) -> Dict[str, Any]:
    """执行 Evaluation（P5-1）"""
    # 1. 创建 Evaluation 记录
    evaluation = quality_store.create_evaluation(
        name=f"Eval {target_id} on {dataset_id}",
        dataset_id=dataset_id,
        agent_id=target_id,
        agent_version=target_version,
        org_id=ctx.org_id,
        created_by=ctx.user_id,
        evaluator_config=evaluator_config,
    )

    # 2. 创建 Run 记录
    run_id = f"run_{uuid.uuid4().hex[:16]}"
    run_store.create_run(
        run_id=run_id,
        workspace_id=ctx.workspace_id,
        ...
        metadata={
            "target_type": "evaluation",
            "target_id": target_id,
            "evaluation_id": evaluation.evaluation_id,
            "dataset_id": dataset_id,
        },
    )

    # 3. 启动 Evaluation 执行（TODO: 异步执行）
    run_store.update_run_status(
        run_id,
        "pending",
        error_message="Evaluation execution engine not implemented yet (P5-1 follow-up)",
    )

    return {
        "run_id": run_id,
        "status": "pending",
        "error_message": "Evaluation execution engine not implemented yet",
        "evaluation_id": evaluation.evaluation_id,
    }
```

**问题**: 创建了 Evaluation 和 Run 记录，但不运行评估引擎。

---

## 2. 已有 Skill 执行机制

### 2.1 `alice_engine.core.skill_executor.run_skill()` — SDK 层

**文件**: `packages/alice-engine/alice_engine/core/skill_executor.py:124-134`

```python
def run_skill(
    skill_id: str,
    user_input: str,
    provider=None,
    context_vars=None,
    **kwargs,
):
    loader = SkillLoader(governance_path=_get_governance_root())
    llm = get_provider(provider or "mock")
    executor = SkillExecutorImpl(skill_loader=loader, provider=llm)
    return executor.execute(skill_id, user_input, context_vars=context_vars, **kwargs)
```

**特点**:
- SDK 层轻量函数式接口
- 需要传入 `skill_id`, `user_input`, `provider`
- 返回 `LLMResponse` 对象（包含 `content`, `token_usage`）
- **不创建 Run 记录**，仅执行 Skill 逻辑

**依赖**:
- `SkillLoader`: 从 `governance/skills/` 加载 Skill 提示词
- `SkillExecutorImpl`: 实际执行器（替换模板变量 + 调用 LLM）
- `get_provider()`: LLM Provider（Claude/Gemini/DeepSeek/MiMo）

---

### 2.2 `aitest.testing.evaluator.EvalRunner.run()` — 评估层

**文件**: `aitest/testing/evaluator.py:223-305`

```python
class EvalRunner:
    def run(
        self,
        skill_id: str,
        input_text: str,
        criteria: Optional[dict] = None,
        context_vars: Optional[dict] = None,
        variant: str = None,
    ) -> EvalRun:
        """执行单次 Skill 评估"""
        try:
            from alice_engine.core.executor import run_skill
            response = run_skill(
                skill_id=skill_id,
                user_input=input_text,
                provider=self.provider,
                context_vars=context_vars or {},
                variant=variant,
            )
            actual_output = response.content or ""
            token_usage = response.token_usage or {}
        except Exception as e:
            errors.append(f"Skill execution error: {str(e)[:200]}")
            actual_output = ""

        # 确定性评分
        score, crit_errors = _score_response(actual_output, criteria)
        ...
        return EvalRun(...)
```

**特点**:
- 复用 `alice_engine.core.executor.run_skill()`
- 支持确定性评分（`_score_response`）: `min_length`, `contains`, `regex`, `structure`
- 返回 `EvalRun` dataclass（包含 `passed`, `score`, `errors`）

---

## 3. 已有 Evaluation 执行机制

### 3.1 `aitest.testing.evaluator.EvalRunner` — 单 Skill 评估

**功能**:
- `run(skill_id, input, criteria)` — 单次 Skill 评估
- `run_agent(agent_name, module, page)` — 完整 Agent 评估
- `metric_from_traces(skill_id)` — 从 trace JSONL 聚合指标

**评分方式**:
1. **确定性评分** (`_score_response`): 规则评分（无 LLM）
2. **LLM Judge** (`evaluator_judge.py`): `LLMJudge`, `AdversarialJudge`

---

### 3.2 Quality 资源模型 — 数据层已就绪

**已实现**:
- `Dataset`: 测试样本集合 (`aitest/platform/quality.py:8-50`)
- `Evaluation`: 评估任务 (`aitest/platform/quality.py:72-117`)
- `EvaluationResult`: 评估结果 (`aitest/platform/quality.py:60-68`)
- `Experiment`: A/B 对比实验 (`aitest/platform/quality.py:131-167`)
- `QualityStore`: CRUD 操作 (`aitest/platform/quality_store.py`)

**数据库表**:
- `datasets`: 样本集合
- `evaluations`: 评估任务（status: pending/running/completed/failed）
- `experiments`: A/B 对比实验

**REST API** (`aitest/server/api/quality.py`):
- `POST /api/v1/evaluations` — 创建 Evaluation（已实现）
- `GET /api/v1/evaluations/:id` — 获取 Evaluation 状态（已实现）
- ⚠️ **缺失**: `POST /api/v1/evaluations/:id/run` — 触发评估执行

---

## 4. Run 资源模型

### 4.1 Run Dataclass — `aitest/platform/run.py:34-100`

**关键字段**:
```python
@dataclass
class Run:
    run_id: str
    workspace_id: str
    org_id: str
    triggered_by: str
    
    # 新资源模型字段（P7-2 Phase 2）
    target_type: str = "agent"          # agent|workflow|skill|evaluation
    target_id: str = ""                 # 执行目标唯一标识
    target_version: str = "latest"      # 版本号
    
    # 状态
    status: str = "running"             # running|completed|failed|cancelled|timed_out
    error_message: str = ""
    
    # 汇总（完成后填充）
    total_tokens: int = 0
    total_cost: float = 0.0
    artifacts: list[str] = field(default_factory=list)
```

**状态管理**:
- `RunStore.update_run_status(run_id, status, error_message)`
- Terminal states: `completed`, `failed`, `cancelled`, `timed_out`

---

## 5. 设计文档分析

### 5.1 `docs/api/POST_api_v1_runs.md`

**存在性**: 需要确认（未读取到完整内容）

**Phase 4 描述** (MASTER_ROADMAP.md:50-79):
- `RunExecutor.execute_agent()`: 复用现有 ExecutionService（完整实现）✅
- `RunExecutor.execute_workflow()`: WorkflowExecutor 执行引擎（完整实现）✅
- `RunExecutor.execute_skill()`: **占位：Skill 独立执行待实现** ⚠️
- `RunExecutor.execute_evaluation()`: **占位：评估引擎待实现** ⚠️

---

## 6. REST API 现状

### 6.1 Quality API — `aitest/server/api/quality.py`

**已实现**:
- `POST /api/v1/datasets` ✅
- `GET /api/v1/datasets/:id` ✅
- `POST /api/v1/datasets/:id/examples` ✅
- `POST /api/v1/evaluations` ✅（创建 Evaluation 记录）
- `GET /api/v1/evaluations/:id` ✅
- `POST /api/v1/experiments` ✅
- `POST /api/v1/experiments/:id/promote` ✅

**缺失**:
- ⚠️ `POST /api/v1/evaluations/:id/run` — 触发评估执行（当前通过 `POST /api/v1/runs` 间接触发）

---

## 7. 实现路径建议

### 7.1 `execute_skill()` 实现方案

**目标**: 使 `POST /api/v1/runs` 支持 `target_type=skill` 真实执行

**实现步骤**:
1. **加载 Skill 提示词**:
   ```python
   from alice_engine.core.skill_loader import SkillLoader
   loader = SkillLoader(governance_path=Path("governance"))
   skill_prompt = loader.load_skill(target_id)
   ```

2. **替换模板变量**:
   ```python
   from alice_engine.core.skill_executor import SkillExecutorImpl
   executor = SkillExecutorImpl(skill_loader=loader, provider=llm)
   response = executor.execute(
       skill_id=target_id,
       user_input=params.get("prompt", ""),
       context_vars=params.get("context", {}),
   )
   ```

3. **更新 Run 状态**:
   ```python
   run_store.update_run_status(run_id, "completed")
   run_store.update_run_summary(
       run_id,
       total_tokens=response.token_usage.get("total", 0),
       artifacts=[],  # 如果 Skill 生成文件，提取路径
   )
   ```

4. **错误处理**:
   ```python
   try:
       response = executor.execute(...)
   except Exception as e:
       run_store.update_run_status(run_id, "failed", error_message=str(e))
   ```

**依赖**:
- `alice_engine.core.skill_loader.SkillLoader`
- `alice_engine.core.skill_executor.SkillExecutorImpl`
- `alice_engine.providers.get_provider()`

---

### 7.2 `execute_evaluation()` 实现方案

**目标**: 运行 Dataset 中的所有样本，聚合评分

**实现步骤**:
1. **加载 Dataset**:
   ```python
   dataset = quality_store.get_dataset(dataset_id)
   if not dataset:
       raise ValueError(f"Dataset not found: {dataset_id}")
   ```

2. **遍历样本执行 Agent**:
   ```python
   from aitest.testing.evaluator import EvalRunner
   runner = EvalRunner(provider=runtime.get("provider", "claude"))
   
   results = []
   for example in dataset.examples:
       eval_run = runner.run(
           skill_id=target_id,  # 或 agent_id
           input_text=example.input.get("prompt", ""),
           criteria=example.expected_output or {},
           context_vars=example.input,
       )
       results.append(eval_run)
   ```

3. **聚合结果**:
   ```python
   from aitest.platform.quality import EvaluationResult
   passed = sum(1 for r in results if r.passed)
   total = len(results)
   
   eval_result = EvaluationResult(
       pass_rate=passed / total if total > 0 else 0.0,
       total_examples=total,
       passed_examples=passed,
       failed_examples=total - passed,
       metrics={"avg_score": sum(r.score for r in results) / total},
       details=[r.to_dict() for r in results],
   )
   ```

4. **更新 Evaluation 状态**:
   ```python
   quality_store.update_evaluation_status(
       evaluation_id=evaluation.evaluation_id,
       status="completed",
       results=eval_result,
   )
   run_store.update_run_status(run_id, "completed")
   ```

**LLM Judge 集成** (可选):
```python
from aitest.testing.evaluator_judge import LLMJudge
judge = LLMJudge(provider="claude", rubric="...")
for example in dataset.examples:
    # 1. 执行 Agent
    response = run_skill(target_id, example.input["prompt"])
    # 2. LLM Judge 评分
    judge_result = judge.judge(
        input=example.input["prompt"],
        output=response.content,
        expected=example.expected_output,
    )
    results.append(judge_result)
```

---

## 8. 缺失组件清单

### 8.1 Skill 执行

- ✅ Skill 提示词加载器 (`SkillLoader`)
- ✅ Skill 执行器 (`SkillExecutorImpl`)
- ✅ LLM Provider 抽象 (`get_provider`)
- ⚠️ **缺失**: `RunExecutor.execute_skill()` 真实实现

---

### 8.2 Evaluation 执行

- ✅ Dataset CRUD (`QualityStore`)
- ✅ Evaluation CRUD (`QualityStore`)
- ✅ EvalRunner 单 Skill 评估
- ✅ LLM Judge (`LLMJudge`, `AdversarialJudge`)
- ⚠️ **缺失**: `RunExecutor.execute_evaluation()` 真实实现（遍历 Dataset + 聚合结果）
- ⚠️ **缺失**: 异步执行机制（长时间运行的 Evaluation 应该后台执行）

---

## 9. 代码量估算

### 9.1 `execute_skill()` 实现

**预估**: ~80 行代码

**主要逻辑**:
1. 加载 Skill (10 行)
2. 执行 Skill (20 行)
3. 提取 artifacts (15 行)
4. 更新 Run 状态 (20 行)
5. 错误处理 (15 行)

---

### 9.2 `execute_evaluation()` 实现

**预估**: ~150 行代码

**主要逻辑**:
1. 加载 Dataset (15 行)
2. 遍历样本 (30 行)
3. 执行 Agent/Skill (40 行)
4. LLM Judge 评分 (30 行)
5. 聚合结果 (25 行)
6. 更新 Evaluation + Run (10 行)

---

## 10. 实现优先级建议

### 10.1 阶段 1: `execute_skill()` 实现（高优先级）

**理由**:
- Skill 是 Agent 的最小执行单元
- 已有完整的 SDK 层实现（`run_skill`）
- 仅需桥接到 RunExecutor
- 工作量小（~80 行）

**交付**:
- `POST /api/v1/runs` 支持 `target_type=skill` 真实执行
- Run 状态正确更新（completed/failed）
- Token 使用统计

---

### 10.2 阶段 2: `execute_evaluation()` 基础实现（中优先级）

**理由**:
- Dataset/Evaluation 资源模型已就绪
- EvalRunner 已实现单 Skill 评估
- 仅需聚合多个 Example 的结果

**交付**:
- `POST /api/v1/runs` 支持 `target_type=evaluation` 执行
- 遍历 Dataset 中的所有 Example
- 聚合 pass_rate, metrics
- 更新 Evaluation 状态

---

### 10.3 阶段 3: 异步执行 + LLM Judge（低优先级）

**理由**:
- Evaluation 可能耗时很长（100+ 样本）
- 需要后台任务队列（Celery/RQ）

**交付**:
- 异步执行引擎（`POST /api/v1/evaluations/:id/run`）
- WebSocket 实时进度通知
- LLM Judge 集成（可选）

---

## 11. 测试策略

### 11.1 Skill 执行测试

```python
# tests/test_skill_execution.py
def test_execute_skill_via_run_api():
    response = client.post("/api/v1/runs", json={
        "target": {
            "type": "skill",
            "id": "automation/page-observe",
            "version": "latest"
        },
        "params": {
            "prompt": "分析 alarm-config 页面",
            "context": {"module": "equipment", "page": "alarm-config"}
        },
        "runtime": {"provider": "claude"}
    })
    
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    
    # 轮询 Run 状态
    run = get_run_store().get_run(run_id)
    assert run.status in ("completed", "running")
```

---

### 11.2 Evaluation 执行测试

```python
# tests/test_evaluation_execution.py
def test_execute_evaluation_via_run_api():
    # 1. 创建 Dataset
    dataset = quality_store.create_dataset(
        name="test-suite",
        type="test_cases",
        examples=[
            Example(input={"prompt": "Test 1"}, expected_output={"score": 0.8}),
            Example(input={"prompt": "Test 2"}, expected_output={"score": 0.9}),
        ]
    )
    
    # 2. 触发 Evaluation
    response = client.post("/api/v1/runs", json={
        "target": {
            "type": "evaluation",
            "id": "automation-agent",
            "version": "2.5.0"
        },
        "params": {
            "dataset_id": dataset.dataset_id,
            "eval_config": {"judge_model": "claude-3-5-sonnet-20241022"}
        }
    })
    
    run_id = response.json()["run_id"]
    evaluation_id = response.json()["evaluation_id"]
    
    # 3. 等待完成
    evaluation = quality_store.get_evaluation(evaluation_id)
    assert evaluation.status in ("completed", "running")
    if evaluation.results:
        assert evaluation.results.pass_rate >= 0.0
```

---

## 12. 向后兼容性

**问题**: 现有代码是否依赖占位实现？

**分析**:
- `execute_skill()` 和 `execute_evaluation()` 目前仅返回 `status="pending"`
- 没有其他代码依赖这两个方法的返回值
- **向后兼容**: 完全替换为真实实现，不会破坏现有功能

---

## 13. 总结

### 13.1 关键发现

1. **Skill 执行机制完整**: SDK 层已有 `run_skill()` + `SkillExecutorImpl`，仅需桥接到 RunExecutor
2. **Evaluation 数据层就绪**: Dataset/Evaluation CRUD 完整，缺执行引擎
3. **EvalRunner 可复用**: 单 Skill 评估逻辑已实现，需要聚合多样本
4. **Run 资源模型支持**: `target_type=skill|evaluation` 字段已预留

---

### 13.2 实现路径

**阶段 1** (1-2 天):
- 实现 `execute_skill()` 真实执行（~80 行）
- 测试 `POST /api/v1/runs` + `target_type=skill`

**阶段 2** (2-3 天):
- 实现 `execute_evaluation()` 基础版（~150 行）
- 遍历 Dataset + 聚合结果
- 测试 `POST /api/v1/runs` + `target_type=evaluation`

**阶段 3** (可选):
- 异步执行 + WebSocket 进度
- LLM Judge 集成

---

### 13.3 风险

1. **Provider 选择**: Skill 执行时需要传入 `runtime.provider`，需要从 `ModelProviderStore` 加载
2. **Artifacts 提取**: Skill 输出可能包含 YAML/JSON，需要解析并保存到 `Run.artifacts`
3. **长时间运行**: Evaluation 可能耗时 10+ 分钟（100 样本 × 6s/样本），需要异步执行

---

## 附录

### A. 关键文件清单

| 文件 | 用途 |
|------|------|
| `aitest/server/api/run_executor.py` | 待实现：execute_skill/execute_evaluation |
| `aitest/platform/quality_store.py` | Dataset/Evaluation CRUD |
| `aitest/testing/evaluator.py` | EvalRunner 单 Skill 评估 |
| `packages/alice-engine/alice_engine/core/skill_executor.py` | run_skill() SDK 接口 |
| `packages/alice-engine/alice_engine/core/skill_executor_impl.py` | SkillExecutorImpl 实现 |
| `aitest/server/api/quality.py` | Quality REST API |

---

**下一步**: 根据此报告编写实现计划（Implementation Plan）
