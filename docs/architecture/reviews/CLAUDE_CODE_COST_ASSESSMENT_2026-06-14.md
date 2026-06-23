# Claude Code 层 — Token 成本评估

> 评估日期: 2026-06-14  
> 范围: Claude Code 会话级 token 消耗（不含 aitest pipeline）  
> 触发: 用户报告 DeepSeek API 累计消费 ~¥200

---

## 成本结构总览

```
                     ┌──────────────────────────────┐
                     │   每 Turn 输入 Token           │
                     ├──────────────────────────────┤
Layer 1: 系统开销     │ CLAUDE.md        ~2,299 tok │ ← 每会话
                     │ MEMORY.md index  ~  214 tok │
                     │ 7 memory files   ~2,060 tok │
                     │ 小计             ~4,574 tok │
                     ├──────────────────────────────┤
Layer 2: 技能调用     │ SKILL.md (10个)  ~7,975 tok │ ← 按需
                     │ → 每个 Skill 还会链式加载       │
                     │   governance/skills/*.md        │
                     │   最大: excel-exporter 22KB     │
                     │   总 active: 27 文件 128KB     │
                     ├──────────────────────────────┤
Layer 3: 对话累积     │ 历史消息全部保留在上下文         │ ← #1 成本驱动
                     │ 30-turn ≈ 90K tokens history  │
                     ├──────────────────────────────┤
Layer 4: Tool Results │ Bash/Read/Grep 结果注入上下文  │
                     │ 大文件 Read → 2K+ tokens      │
                     └──────────────────────────────┘
```

---

## 识别到的浪费点

### 🔴 P0 — 高影响

| # | 问题 | 数据 | 建议 |
|---|------|------|------|
| 1 | **对话累积** | 30-turn 历史 ≈ 90K tokens/turn | 长任务拆分为多次短会话；使用 `/compact` |
| 2 | **governance/skills/ 巨型文件** | `excel-exporter.md` 22KB (~5,700 tok) 一次性吸入上下文 | 拆分为简短 prompt + 示例文件引用 |

### 🟡 P1 — 中影响

| # | 问题 | 数据 | 建议 |
|---|------|------|------|
| 3 | **CLAUDE.md 路由表冗余** | 口语化路由 12 条规则 ~500 tokens | 保留 3 条最常用，其余移入 `governance/` 引用 |
| 4 | **SKILL.md 重复指令** | 每个含 SOP 门禁说明（~200 tok）+ 边界说明（~150 tok）+ 必读列表（~200 tok） | 提取门禁/边界到共享引用 |
| 5 | **Memory 文件碎片** | 8 个文件 ~2,272 tokens | 未被引用的归档；合并相关记忆 |

### 🟢 P2 — 低影响

| # | 问题 | 数据 |
|---|------|------|
| 6 | `excel-exporter.md` 22KB | 包含大量示例表格，非每次调用都需要 |
| 7 | `knowledge-manager.md` 9.4KB | 两条知识操作合并后未精简 |

---

## 与 aitest Pipeline 成本对比

| 层面 | 消耗 | 占比 |
|------|------|------|
| Claude Code 会话 (~30 turns) | ~$0.09/会话 × 会话数 | **大头** |
| aitest Pipeline (38 events total) | $0.09/累计 | 极小 |

> 结论: 烧掉的 ~¥200 主要来自 Claude Code 对话本身，而非 aitest pipeline。

---

## 优化建议（按 ROI 排序）

1. **拆分长会话** — 50+ turn 的对话拆为多次短会话（最直接省钱）
2. **精简 CLAUDE.md** — 路由表从 12 条减至 3 条高频路由，其余移入 `governance/docs/reference/routing-guide.md`
3. **Memory 瘦身** — 归档超过 30 天未引用的记忆文件
4. **Skill 门禁去重** — 10 个 SKILL.md 各含几乎相同的 SOP 门禁说明，提取到共享模板通过引用加载
5. **巨型 Skill 拆分** — `excel-exporter.md` (22KB) 拆为指令 + 数据，指令部分压缩到 5KB 以内
