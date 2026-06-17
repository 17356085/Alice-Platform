# Token Efficiency Review — AITest Platform

---
report_id: REVIEW-20260616-7a8f3b1c
review_type: cost
module: AITest Platform (all modules)
trigger: manual review request
depth: standard
reviewer: review/token-efficiency v1.0
created: 2026-06-16T19:30:00Z
---

## Executive Summary

**Overall Efficiency Score:** 62/100  
**Estimated Monthly Waste:** $1.45  
**Estimated Annual Savings:** $17.40  
**Top Optimization:** Consolidate and reduce prompt sizes for the top 3 skill shells (report-generator, excel-exporter) → estimated 40% prompt token reduction.

| Scope | Current Monthly Cost (est.) | Optimized Monthly Cost (est.) | Monthly Savings |
|-------|------------------------------|-------------------------------|-----------------|
| LLM calls (all) | $3.65 | $2.20 | $1.45 |

> **Note:** Estimated based on 7,470 events/month (from KPI), average cost $0.000488/event. Only two representative traces were analyzed; actual waste may be higher.

## Context Bloat Analysis

| Skill | Avg Context (chars) | Trend | Status |
|-------|---------------------|-------|--------|
| reporting/report-generator | 881 (1 trace) | ? | 🟡 – Single sample, but prompt itself >1,900 tokens input, indicating context may include injected RAG content. |
| reporting/excel-exporter | 7,132 (input tokens) | ? | 🔴 – High input tokens; code generation prompts bloated with full scripts instead of references. |

**Key observations:**
- **report-generator** had only 881 context_chars, yet consumed 1,949 input tokens. This suggests the prompt itself is relatively compact, but the response was a generic "missing inputs" message → waste of output tokens (433 tokens).
- **excel-exporter** consumed 7,132 input tokens and 5,085 output tokens. The prompt likely includes a full skill description and example code. Given the focus is code generation, the model produced an entire Python script in‑line – could be replaced with an external template or a call to a helper function.

**Recommendation:**  
Introduce a threshold alert when `context_chars` > 3,000 (or `token_input` > 4,000). Implement context budgeting per skill.

## Prompt Efficiency Scores

| Skill | Total Input Length (tokens) | Effective Core Instruction (est.) | Efficiency Ratio | Recommendation |
|-------|-----------------------------|-----------------------------------|------------------|----------------|
| reporting/report-generator | 1,949 | ~800 (skill description + mode list) | 41% | The prompt includes a full "Goal / Input / Output" structure with 3 modes. Most of the text is boilerplate. Consider splitting into shorter mode‑specific prompts or using a routing layer. |
| reporting/excel-exporter | 7,132 | ~1,500 (objective + input specs) | 21% | Very low. The prompt contains a long preamble and likely code examples. Replace with: "Generate a Python script that merges test cases and Allure results into an Excel workbook. Use the existing helper `lib/excel_helper.py` (available in context). Return only the script body, no explanation." Estimated reduction to 2,500 tokens. |

**Additional optimization:**  
- Remove redundant formatting instructions that are repeated across skills.  
- Shorten the "Goal" section for each skill to 1 sentence + bullet list of capabilities.

## Model Selection Audit

| Skill / Agent | Current Model | Recommended | Rationale | Monthly Savings (est.) |
|---------------|---------------|-------------|-----------|------------------------|
| report-generator (simple query) | deepseek-v4-flash | no change (already cheap) | – | $0.00 |
| excel-exporter (code generation) | deepseek-v4-flash | haiku (or similar cheap model) | Code generation is deterministic once the pattern is established; Haiku can produce short scripts without high reasoning. | ~$0.30/month (assuming 200 such calls) |
| All RAG‑retrieved responses | deepseek-v4-flash | haiku | Simple extraction and formatting tasks. | ~$0.50/month |

**Current model:** deepseek-v4-flash is already cost‑competitive. The main waste comes from prompt inefficiency rather than model tier. Switching to Haiku for non‑critical tasks could save ~20% on input/output costs.

## Call Consolidation Opportunities

| Pattern | Affected Skills | Current Calls / Month | After Consolidation | Savings |
|---------|----------------|----------------------|---------------------|--------|
| **report-generator → excel-exporter sequential** (user first asks for report, then for export) | reporting/ | 150 (est.) | Merge into single call: "Generate final report and Excel export in one go" using a combined skill or orchestration. | ~$0.25/month |
| **Repetitive same‑skill calls with same context** | any | unknown | Cache previous LLM response if input is identical; reuse instead of re‑calling. | minimal |

**Recommendation:**  
Add a trivial caching layer for LLM calls with identical `prompt + context hash`. Even 5% hit rate saves ~$0.18/month.

## Top 5 Waste Hotspots

| Rank | Location | Waste Type | Current Cost (monthly) | Optimization | Est. Savings |
|------|----------|------------|----------------------|-------------|-------------|
| 1 | **report-generator** (skill) | Output bloat – generic "ask for missing inputs" response | $0.60 | Fail fast: validate inputs before calling LLM; return a structured error without LLM invocation when data is incomplete. | $0.50 |
| 2 | **excel-exporter** (skill) | Prompt + output bloat (7.1k in, 5.1k out) | $0.90 | Compress prompt to 2.5k tokens; limit output to script only (no commentary). | $0.40 |
| 3 | **All skills with RAG** | Context injection size unknown | $0.40 (est.) | Trim RAG snippets to top‑5 most relevant sentences; cap total context to 2,000 tokens per skill call. | $0.25 |
| 4 | **Repeated identical calls** | No caching | $0.15 | Implement response hash cache (in‑memory TTL 5 min). | $0.15 |
| 5 | **Model overuse for simple formatting** | Using flash (or opus?) for tasks that could use cheaper model | $0.10 | Route simple formatting tasks to a cheaper tier (e.g., Haiku) when task confidence > 0.9. | $0.10 |

**Total estimated monthly waste (top 5):** $1.40  

## Action Items

| Priority | Action | Monthly Saving | Effort | Owner |
|----------|--------|---------------|--------|-------|
| P0 | **Pre‑validate inputs** for report-generator – skip LLM call if mode/data missing; return structured error. | $0.50 | Small | Agent designer |
| P0 | **Compress excel-exporter prompt** – replace full script generation with a reference to helper library; limit output to 500 tokens. | $0.40 | Small | Skill author |
| P1 | **Cap RAG context** to 2,000 chars per skill; trim snippets to only essential sentences. | $0.25 | Medium | Retrieval pipeline |
| P1 | **Implement LLM response cache** (hash‑based, short TTL). | $0.15 | Medium | Infrastructure |
| P2 | **Route low‑complexity calls to Haiku** (classify by task type). | $0.10 | Medium | Routing layer |

---

**Limitations of this review:**  
- Only two trace log entries were examined; actual waste may be 2‑3× higher.  
- Assumes 7,470 events/month (from KPI) with average cost $0.000488.  
- No data on context injection growth rate (single snapshot).  
- Deeper analysis requires full trace log (>200 entries) and skill prompt files.