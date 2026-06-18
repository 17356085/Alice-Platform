# Skill: requirements-dev/feature-spec

### 目标
从用户需求到结构化功能规格，生成 FEATURE_SPEC.md。

### 输入
- 用户需求描述
- 现有项目上下文

### 输出
- `FEATURE_SPEC.md`：功能列表、优先级、范围边界

### 规则
- 功能编号 F-001, F-002...
- 优先级: P0(必须) / P1(重要) / P2(可选)
- 明确 MVP vs 后续迭代的边界

---

## Prompt 模板

```text
你是资深产品经理。将以下用户需求转化为功能规格。

## 需求
{{USER_REQUIREMENT}}

## 输出
```markdown
# 功能规格 — {{PROJECT}}

## 功能列表
| ID | 功能 | 优先级 | 描述 | MVP |
|----|------|--------|------|-----|
| F-001 | ... | P0 | ... | ✅ |

## 范围边界
- MVP: {{MVP_SCOPE}}
- 后续: {{FUTURE_SCOPE}}
- 不做: {{OUT_OF_SCOPE}}
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | requirements-dev | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->