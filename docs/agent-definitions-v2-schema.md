# Agent Definitions Schema v2.0 — Skill 版本绑定（P4-1）

## 变更概述

从 v1.0 的裸 skill ID 升级到 v2.0 的版本化引用。

## Schema 对比

### v1.0（当前）

```yaml
agents:
  project-agent:
    skills:
      - project/project-context-manager
      - project/context-sync
```

**问题**:
- 无法得出 AgentVersion 锁定的 skill 版本
- 无法回溯历史版本的 skill 依赖
- 无法实现 immutable deployment

### v2.0（目标）

```yaml
version: "2.0"  # schema 版本号提升
agents:
  project-agent:
    version: "2.5.0"  # agent 自身版本
    skills:
      - id: project/project-context-manager
        version: "1.2.0"        # 明确 skill 版本
        sha256: "abc123..."     # 可选：内容哈希校验
      - id: project/context-sync
        version: "1.1.0"
```

## 向后兼容策略

支持两种格式混用：

```yaml
agents:
  project-agent:
    skills:
      - project/legacy-skill              # v1.0 格式：解析为 "latest"
      - id: project/versioned-skill       # v2.0 格式
        version: "1.2.0"
```

## 解析逻辑

```python
def parse_skill_ref(skill_entry):
    if isinstance(skill_entry, str):
        # v1.0 format: "project/skill-name"
        return SkillRef(id=skill_entry, version="latest", sha256=None)
    elif isinstance(skill_entry, dict):
        # v2.0 format: {id, version, sha256}
        return SkillRef(
            id=skill_entry["id"],
            version=skill_entry.get("version", "latest"),
            sha256=skill_entry.get("sha256")
        )
```

## 数据模型

```python
@dataclass
class SkillRef:
    """Skill 引用（带版本）"""
    id: str               # "project/context-sync"
    version: str          # "1.2.0" | "latest"
    sha256: Optional[str] # 内容哈希（可选）

@dataclass
class AgentDefinition:
    id: str
    name: str
    version: str          # NEW: agent 自身版本
    phase: str
    description: str
    capabilities: List[str]
    model_tier: str
    skills: List[SkillRef]  # 从 List[str] 改为 List[SkillRef]
```

## API 变更

### 新增端点

```
GET /api/v1/agents/:agent_id/versions/:version
```

返回 Agent 版本快照，包含锁定的 skill 版本：

```json
{
  "agent_id": "project-agent",
  "version": "2.5.0",
  "skills": [
    {
      "id": "project/project-context-manager",
      "version": "1.2.0",
      "sha256": "abc123...",
      "resolved_at": "2026-07-10T12:34:56Z"
    }
  ]
}
```

### 现有端点更新

`GET /api/v1/agents/:id` 返回的 `skills` 字段从 `List[str]` 变为 `List[SkillRef]`。

## 迁移步骤

1. 更新 `agent-definitions.yaml` parser 支持两种格式
2. 更新 `AgentDefinition` dataclass 添加 `version` 字段
3. 更新 `AgentRegistry` 支持版本查询
4. 添加 `GET /api/v1/agents/:id/versions/:version` 端点
5. 文档迁移指南

## 示例：完整的 v2.0 agent-definitions.yaml

```yaml
version: "2.0"
description: "alice-engine default governance pack"

agents:
  project-agent:
    version: "2.5.0"
    name: "Project Agent"
    phase: "Project Init"
    description: "初始化项目上下文"
    capabilities:
      - project
      - knowledge
    model_tier: balanced
    skills:
      - id: project/project-context-manager
        version: "1.2.0"
      - id: project/context-sync
        version: "1.1.0"
      - id: project/hygiene-check
        version: "1.0.0"
      - id: knowledge/completeness-check
        version: "2.0.1"
```

## 实现优先级

**Phase 1（本次）**: 
- 支持解析两种格式
- AgentDefinition 添加 version 字段
- 向后兼容

**Phase 2（未来）**:
- SHA256 校验
- 版本约束表达式（`"^1.2.0"`, `">=1.0.0,<2.0.0"`）
- 自动版本解析（从 skill 文件读取）
