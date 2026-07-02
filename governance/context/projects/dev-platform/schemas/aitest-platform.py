根据领域术语和 AITest Platform 的业务模型，我推导出以下核心实体并生成 Pydantic v2 Schema。

---

## 1. `schemas/skill.py`

```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal


class SkillCreate(BaseModel):
    """Schema for registering a new Skill."""
    name: str = Field(..., min_length=3, max_length=100, description="Unique skill name (slug)")
    display_name: str = Field(..., min_length=1, max_length=200, description="Human-readable name")
    version: str = Field(..., min_length=1, max_length=20, description="Semantic version, e.g. 1.0.0")
    category: Literal["backend", "frontend", "architecture", "testing", "governance"] = Field(
        ..., description="Skill category"
    )
    description: str | None = Field(None, max_length=1000)
    dependencies: list[str] = Field(default_factory=list, description="List of dependent skill names")

    @field_validator("version")
    @classmethod
    def version_must_be_semver(cls, v: str) -> str:
        parts = v.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError("version must be semantic (e.g. 1.0.0)")
        return v


class SkillUpdate(BaseModel):
    """Schema for updating an existing Skill. All fields optional."""
    display_name: str | None = Field(None, min_length=1, max_length=200)
    version: str | None = Field(None, min_length=1, max_length=20)
    category: Literal["backend", "frontend", "architecture", "testing", "governance"] | None = None
    description: str | None = Field(None, max_length=1000)
    dependencies: list[str] | None = None
    is_active: bool | None = None

    @field_validator("version")
    @classmethod
    def version_must_be_semver(cls, v: str | None) -> str | None:
        if v is None:
            return v
        parts = v.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError("version must be semantic (e.g. 1.0.0)")
        return v


class SkillResponse(BaseModel):
    """Schema for Skill API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    display_name: str
    version: str
    category: str
    description: str | None
    dependencies: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

## 2. `schemas/agent.py`

```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentCreate(BaseModel):
    """Schema for creating a new Agent."""
    name: str = Field(..., min_length=3, max_length=100, description="Unique agent name (slug)")
    display_name: str = Field(..., min_length=1, max_length=200, description="Human-readable agent name")
    primary_skill_name: str = Field(..., min_length=1, max_length=100, description="Primary skill bound to this agent")
    secondary_skill_names: list[str] = Field(
        default_factory=list, description="Secondary skills bound to this agent"
    )
    description: str | None = Field(None, max_length=1000)


class AgentUpdate(BaseModel):
    """Schema for updating an existing Agent. All fields optional."""
    display_name: str | None = Field(None, min_length=1, max_length=200)
    primary_skill_name: str | None = Field(None, min_length=1, max_length=100)
    secondary_skill_names: list[str] | None = None
    description: str | None = Field(None, max_length=1000)
    is_active: bool | None = None


class AgentResponse(BaseModel):
    """Schema for Agent API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    display_name: str
    primary_skill_name: str
    secondary_skill_names: list[str]
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

## 3. `schemas/module.py`

```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ModuleCreate(BaseModel):
    """Schema for creating a new business Module."""
    name: str = Field(..., min_length=2, max_length=100, description="Unique module slug (e.g. equipment, warehouse)")
    display_name: str = Field(..., min_length=1, max_length=200, description="Human-readable module name")
    description: str | None = Field(None, max_length=1000)
    page_names: list[str] = Field(default_factory=list, description="Pages belonging to this module")


class ModuleUpdate(BaseModel):
    """Schema for updating an existing Module. All fields optional."""
    display_name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    page_names: list[str] | None = None
    is_active: bool | None = None


class ModuleResponse(BaseModel):
    """Schema for Module API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    display_name: str
    description: str | None
    page_names: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

## 4. `schemas/phase.py`

```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PhaseCreate(BaseModel):
    """Schema for creating a new SOP Phase."""
    phase_number: int = Field(..., ge=0, le=9, description="Canonical phase number (0-9)")
    name: str = Field(..., min_length=3, max_length=200, description="Phase name")
    description: str | None = Field(None, max_length=1000)
    output_artifact_type: str = Field(
        ..., min_length=1, max_length=100, description="Document type produced by this phase"
    )
    required_skills: list[str] = Field(default_factory=list, description="Skills required to execute this phase")
    gate_condition: str | None = Field(None, max_length=500, description="SOP gate condition expression")


class PhaseUpdate(BaseModel):
    """Schema for updating an existing Phase. All fields optional."""
    name: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, max_length=1000)
    output_artifact_type: str | None = Field(None, min_length=1, max_length=100)
    required_skills: list[str] | None = None
    gate_condition: str | None = Field(None, max_length=500)
    is_active: bool | None = None


class PhaseResponse(BaseModel):
    """Schema for Phase API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phase_number: int
    name: str
    description: str | None
    output_artifact_type: str
    required_skills: list[str]
    gate_condition: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

## 5. `schemas/test_run.py`

```python
from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class TestRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class TestRunCreate(BaseModel):
    """Schema for creating a new Test Run."""
    module_name: str = Field(..., min_length=2, max_length=100, description="Target module name")
    test_file: str | None = Field(None, max_length=255, description="Specific test file path")
    marker: str | None = Field(None, max_length=100, description="Pytest marker filter")
    triggered_by: str | None = Field(None, max_length=100, description="Trigger source (manual/schedule/agent)")


class TestRunUpdate(BaseModel):
    """Schema for updating a Test Run. Typically for status transitions."""
    status: TestRunStatus | None = None
    passed_count: int | None = Field(None, ge=0)
    failed_count: int | None = Field(None, ge=0)
    error_count: int | None = Field(None, ge=0)
    skipped_count: int | None = Field(None, ge=0)
    duration_seconds: float | None = Field(None, ge=0)
    log_summary: str | None = Field(None, max_length=5000)


class TestRunResponse(BaseModel):
    """Schema for Test Run API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module_name: str
    test_file: str | None
    marker: str | None
    triggered_by: str | None
    status: TestRunStatus
    passed_count: int
    failed_count: int
    error_count: int
    skipped_count: int
    duration_seconds: float | None
    log_summary: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime
```

## 6. `schemas/sop.py`

```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class SOPCreate(BaseModel):
    """Schema for creating a new SOP definition."""
    name: str = Field(..., min_length=3, max_length=200, description="SOP name")
    description: str | None = Field(None, max_length=1000)
    phase_ids: list[UUID] = Field(..., min_length=1, description="Ordered list of phase IDs")
    module_name: str = Field(..., min_length=2, max_length=100, description="Target module this SOP belongs to")


class SOPUpdate(BaseModel):
    """Schema for updating an SOP definition."""
    name: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, max_length=1000)
    phase_ids: list[UUID] | None = None
    is_active: bool | None = None


class SOPResponse(BaseModel):
    """Schema for SOP API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    phase_ids: list[UUID]
    module_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

---

每个 Schema 文件都遵循 Pydantic v2 规范：Request/Response 分离、`ConfigDict(from_attributes=True)` 用于 ORM 模式、必填/可选字段明确标注、String 字段指定长度约束。