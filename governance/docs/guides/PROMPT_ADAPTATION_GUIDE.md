# Prompt 适配指南 — 跨 LLM Provider 的 Prompt 工程

> 版本：v1.0 | 日期：2026-06-14
> 前提：LLM Provider 抽象层已就绪（`aitest/llm/provider.py`）
> 相关：[[PLATFORM_INDEPENDENCE_ROADMAP]]

---

## 一、为什么需要适配

不同 LLM 对 Prompt 的解析方式差异显著。Claude 优化过的 Skill Prompt 直接给 GPT-4o 或 Qwen3 使用时，效果可能下降 30-50%。本指南记录已验证的差异和适配策略。

---

## 二、各模型 Prompt 特征对比

| 维度 | Claude (Sonnet/Opus) | GPT-4o | DeepSeek-V3 | 本地模型 (Qwen3) |
|------|---------------------|--------|-------------|------------------|
| **System Prompt 最佳长度** | 8K-32K tokens | 2K-8K tokens | 4K-16K tokens | 1K-4K tokens |
| **结构化偏好** | XML tags (`<rules>`) | Markdown (`### 规则`) | Markdown (`### 规则`) | Markdown + 示例 |
| **指令遵循** | 严格 | 灵活（需要更多约束） | 较严格 | 松散（需示例引导） |
| **中文能力** | ★★★★☆ | ★★★★☆ | ★★★★★ | ★★★★☆ (Qwen3) |
| **Tool Calling** | 原生 + 并行 | 原生 + 并行 | 原生 (V3+) | 部分模型支持 |
| **Context 窗口** | 200K | 128K | 128K | 32K (qwen3:8b) |
| **示例需求** | 低（理解力强） | 低 | 中 | 高（少示例=易偏离） |
| **角色设定敏感度** | 高 | 中 | 高 | 中 |

---

## 三、关键适配规则

### 3.1 System Prompt 长度截断

不同模型的 system prompt 处理能力不同。过长的 prompt 在低能力模型上会被截断或忽略尾部。

```
Claude:   ≤ 32K tokens → 无需截断
GPT-4o:  ≤ 8K tokens  → 截断中间，保留首尾
DeepSeek: ≤ 16K tokens → 截断中间，保留首尾
Qwen3:   ≤ 4K tokens  → 截断尾部 1/3
```

**策略**：对长 Skill Prompt（如 `test-design/page-analysis`），`PromptAdapter` 自动根据 Provider 能力截断。

### 3.2 XML Tags vs Markdown

Claude 对 XML tags 理解最好：
```xml
<rules>
  <rule id="1">禁止使用绝对 XPath</rule>
  <rule id="2">必须继承 BasePage</rule>
</rules>
```

GPT-4o / DeepSeek 更偏好 Markdown：
```markdown
### 规则
1. **禁止使用绝对 XPath** — 使用 CSS Selector 或相对路径
2. **必须继承 BasePage** — 所有 Page Object 继承 `base.BasePage`
```

`PromptAdapter._strip_xml_tags()` 自动转换 `<tag>content</tag>` → `**tag**: content`。

### 3.3 示例注入（Few-Shot）

- **Claude / GPT-4o**：不需要额外示例，Skill Prompt 中的规范描述即可
- **本地模型 (Qwen3)**：没有具体输出格式示例时容易偏离，需注入 few-shot 模板

`PromptAdapter._inject_few_shot()` 检测 Skill 中是否已有示例，没有则注入对应类型的格式模板。

### 3.4 中文 Prompt 优化

- **DeepSeek** 对中文理解最佳，无需特殊处理
- **Claude** 中文能力优秀，但复杂嵌套结构偶有误解
- **GPT-4o** 中文流畅，但在代码生成任务中不如英文准确
- **Qwen3** 中文母语级，但复杂推理任务建议简化描述

### 3.5 Tool Calling 格式转换

- **Claude** 使用 Anthropic native tool format（`input_schema` 格式）
- **OpenAI / DeepSeek / Ollama** 使用 OpenAI function calling format
- `ClaudeProvider.complete()` 自动将 OpenAI format → Anthropic format 转换

---

## 四、Skill 编写最佳实践

### 4.1 推荐的 Skill Prompt 结构（跨模型兼容）

```markdown
# 角色
你是一个 [角色描述]。使用中文回复。

## 任务
[一句话描述核心任务]

## 输入格式
[描述输入数据结构]

## 输出规范
### 格式要求
- 使用 Markdown 格式
- 代码块使用 ```python
- 表格使用标准 Markdown 表格

### 内容要求
1. [具体要求1]
2. [具体要求2]

## 约束规则
1. **[规则名]**：[规则描述]
2. ...

## 输出示例  ← 对本地模型至关重要
[具体输出格式的示例]
```

### 4.2 反模式（避免）

| 反模式 | 受影响模型 | 改进 |
|--------|-----------|------|
| 纯 XML tags 做结构 | GPT-4o, Qwen3 | 改用 Markdown 标题 + 列表 |
| 超长单段描述 (>500字) | 全部 | 分段，使用 ### 标题 |
| 无输出格式示例 | 本地模型 | 添加 `### 输出示例` 块 |
| System prompt > 10K tokens | GPT-4o, Qwen3 | 拆分核心/增强两部分 |
| 在 prompt 中混入大量 Context | 全部 | 使用 ContextInjector 按需注入 |

### 4.3 Skill 复杂度分级

| Tier | Context | 示例 Skill | 推荐模型 |
|------|---------|-----------|---------|
| **mechanical** | 0 | code-consistency-checker | 任意 |
| **low** | <4K | knowledge-manager | Claude Haiku / GPT-4o-mini / Qwen3:8b |
| **medium** | <8K | page-analysis | Claude Sonnet / GPT-4o / DeepSeek-V3 |
| **high** | <20K | tech-analysis, bug-analysis | Claude Opus / GPT-4o / DeepSeek-V3 |

---

## 五、使用 PromptAdapter

### 5.1 代码示例

```python
from aitest.llm.prompt_adapter import PromptAdapter
from aitest.llm.skill_loader import load_skill

adapter = PromptAdapter()
raw_prompt = load_skill("automation/tech-analysis")

# 为目标 Provider 适配
adapted = adapter.adapt(
    skill_prompt=raw_prompt,
    provider_type="ollama",  # "claude" | "openai" | "deepseek" | "ollama"
    context="附加上下文...",
)
```

### 5.2 CLI 使用

```bash
# 自动适配（--provider 指定目标模型）
aitest skill run automation/tech-analysis --input "分析 equipment/alarm-config" --provider deepseek
aitest skill run automation/page-object-generator --input "生成 AlarmConfigPage" --provider ollama:qwen3
```

### 5.3 验证适配效果

```bash
# 跨 Provider 对比同一 Skill 的输出质量
python -m aitest.provider_verify --compare --skill medium --providers claude,deepseek
```

---

## 六、已知差异与解决方案

### 6.1 Element Plus 定位器生成

| 模型 | 质量 | 常见问题 |
|------|:----:|---------|
| Claude Sonnet | ★★★★★ | 最优，原生理解 Element Plus |
| GPT-4o | ★★★★☆ | 偶有 CSS selector 不够具体 |
| DeepSeek-V3 | ★★★★☆ | 中文变量名偏好需纠正 |
| Qwen3:8b | ★★★☆☆ | 定位器策略过于简单，需更多示例 |

**解决**：在 `automation/tech-analysis` Skill Prompt 中已内置定位器规范，自动纠正模型偏差。

### 6.2 测试用例生成

| 模型 | 覆盖率 | 常见问题 |
|------|:---:|---------|
| Claude Sonnet | 高 | 偶有过度设计 |
| GPT-4o | 中高 | 边界值覆盖不足 |
| DeepSeek-V3 | 高 | 中文场景覆盖优秀 |
| Qwen3:8b | 中 | 复杂场景遗漏 |

---

## 七、持续改进

- [ ] 在 3 个 Skill 上完成 A/B 测试，量化各模型效果差异
- [ ] 基于测试结果调整 PromptAdapter 的参数
- [ ] 建立自动化回归：同一输入 → 所有 Provider → 质量评分

---

> **下一步**：用 `python -m aitest.provider_verify --compare` 跑一次实际对比，根据输出调整 PromptAdapter 配置。
