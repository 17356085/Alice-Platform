# Phase 1 实验报告

> 日期: 2026-06-17 | 环境: Windows 11, Python 3.12, browser-use 0.13.1, DeepSeek (Anthropic-compatible)

## 实验结果

| 实验 | 状态 | 耗时 | 详情 |
|------|------|------|------|
| **E1: 登录** | ✅ 通过 | ~44s | 4 LLM steps: navigate→wait→fill→click→verify |
| **E2: 页面观察** | ✅ 通过 | ~68s | 成功提取页面结构 JSON（搜索字段/按钮/表格列/分页） |
| **E3: 搜索** | ❌ 失败 | ~77s | 侧边栏导航循环点击，DeepSeek 虚构结果 |
| **E4: CRUD** | ⏭ 跳过 | - | E3 失败后暂停，避免浪费 token |

## 关键发现

### 1. Browser-Use 在本系统上可行

- 成功控制 Playwright Chromium 浏览器
- 成功操作 Vue 3 + Element Plus 登录页面
- 成功通过侧边栏导航到目标页面
- 成功识别 Element Plus 组件（input/select/button/table/pagination）

### 2. DeepSeek 是瓶颈

| 能力 | DeepSeek | 影响 |
|------|----------|------|
| 无视觉支持 (use_vision=False) | ❌ | 无截图验证，judge 无法确认结果 |
| instruction following | ⚠️ | 复杂多步任务容易走偏 |
| 侧边栏导航 | ⚠️ | 偶尔成功，经常循环点击 |
| 虚构输出 (hallucination) | ❌ | 无法完成任务时编造结果 |
| Extended thinking | ❌ | 与 tool_choice 冲突，需显式禁用 |

### 3. 配置要点

```python
# 必须配置（DeepSeek 兼容）
ChatAnthropic(
    model="claude-sonnet-4-6",
    base_url="https://api.deepseek.com/anthropic",
    thinking={"type": "disabled"},  # 关键！否则 400 错误
)

# 推荐配置
Browser(keep_alive=True)  # 多 Agent 共享浏览器会话
Agent(use_vision=False)    # DeepSeek 不支持视觉
```

### 4. 与现有 Selenium 方案对比

| | Selenium (当前) | Browser-Use (本次实验) |
|---|---|---|
| 登录可靠性 | 98% (3次重试) | ~80% (首次) |
| 导航方式 | JS hash 直跳 | 侧边栏逐级点击 |
| 页面观察 | 需手写 PO | NL 驱动，自动提取 |
| 搜索操作 | 稳定 | 不可靠（DeepSeek） |
| 执行速度 | <5s/操作 | 40-80s/任务 |

## 对项目计划的影响

### Phase 2 (PO Generator) — 继续推进 ✅

E2 证明 page observation 质量足够生成 PO 骨架。改进方案：
- 导航改用 `driver.get(BASE_URL + hash_route)` 直接跳转，不走侧边栏
- 页面观察 JSON 可直接驱动代码模板

### Phase 3 (Self-Healing) — 需重新评估 ⚠️

DeepSeek 的可靠性不足以做实时自愈。备选方案：
- 仅在有视觉能力的模型上启用（需切换到真实 Anthropic API）
- 或降级为"离线修复建议"（失败后分析，不实时干预）

### Phase 4 (Explorer Agent) — 延期 ⏸

需更强模型。DeepSeek 的多步推理和指令遵循能力不足以支持自主探索。

## 下一步建议

1. **切换到真实 Anthropic API** (claude-sonnet-4-6 直连) — 成本和可靠性评估
2. **导航优化**: 用 hash-route 直跳替代侧边栏逐级点击
3. **PO Generator MVP**: 基于 E2 成功经验，快速实现原型
