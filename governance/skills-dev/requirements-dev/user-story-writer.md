# Skill: requirements-dev/user-story-writer

### 目标
将 FEATURE_SPEC.md 转化为用户故事（As a / I want / So that），每个故事带有可验证的验收标准。

### 输入
- `FEATURE_SPEC.md`

### 输出
- `USER_STORIES.md`

### 规则
- 格式: "As a <role>, I want <action>, so that <benefit>"
- 每故事 3-5 条验收标准（Given/When/Then）
- 覆盖: happy path, error path, empty state

---

## Prompt 模板

```text
你是资深产品经理。将以下功能规格转化为用户故事。

## 功能规格
{{FEATURE_SPEC}}

## 输出
```markdown
# 用户故事

## US-001: {{TITLE}}
**作为** {{ROLE}}
**我想要** {{ACTION}}
**以便** {{BENEFIT}}

### 验收标准
1. Given {{PRECONDITION}}, When {{ACTION}}, Then {{OUTCOME}}
2. ...
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | requirements-dev | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->