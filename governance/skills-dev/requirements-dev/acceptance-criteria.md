# Skill: requirements-dev/acceptance-criteria

### 目标
将用户故事的验收标准细化为可测试的 Given/When/Then 场景，覆盖边界和异常。

### 输入
- `USER_STORIES.md`

### 输出
- `ACCEPTANCE_CRITERIA.md`

### 规则
- 每条标准独立可测试
- 覆盖: happy path, error, empty, boundary, permission denied

---

## Prompt 模板

```text
细化以下用户故事的验收标准，使其可测试。

## 用户故事
{{USER_STORIES}}

## 输出
每个故事的详细 Given/When/Then 场景（含边界和异常）。
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | requirements-dev | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->