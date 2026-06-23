# full-sop.workflow.js 拆分方案

> 2026-06-12 | Token Cost Audit Phase 3.4 | 预计节省: 10,000→~2,000 tokens/按需加载

## 当前问题

`full-sop.workflow.js` (927 行, ~10,000 tokens) 是单文件巨型编排器。每次 `/full-sop` 调用时全量加载，即使大部分代码路径不执行（如 mode=status 只需 Preflight）。

## 目标架构

```
governance/agents/
├── full-sop.workflow.js          ← 主编排器 (~200 行)
│   ├── 参数解析 + mode 判断
│   ├── 公共函数 (assertGate, requirePageArtifacts, writeStatus)
│   └── Phase 调度逻辑 (条件性按需加载子模块)
│
└── full-sop-phases/
    ├── preflight.js              ← Phase 0: 状态检查 + 断点恢复 (~80 行)
    ├── project-init.js           ← Phase 1: 项目初始化 (~60 行)
    ├── module-modeling.js        ← Phase 2: 模块建模 (~50 行)
    ├── test-design.js            ← Phase 3: 测试设计 pipeline (~70 行)
    ├── automation.js             ← Phase 4: 代码生成 pipeline (~90 行)
    ├── execute-debug.js          ← Phase 5-6: 执行+调试循环 (~150 行)
    ├── report.js                 ← Phase 7: 报告生成 (~60 行)
    └── knowledge.js              ← Phase 8: 知识沉淀 (~80 行)
```

## 加载策略

| mode | 加载模块 | Token |
|------|---------|-------|
| `status` | preflight only | ~800 |
| `resume` | preflight + 断点所在 phase | ~800-1,500 |
| `full` | preflight + 按 Phase 逐步加载 | ~800-3,000 |
| `from-automation` | preflight + automation + execute-debug + report + knowledge | ~1,200 |

> 当前: 每次 10,000 tokens（全量）→ 优化后: 平均 ~1,500 tokens（按需）

## 实施步骤

1. 创建 `full-sop-phases/` 目录
2. 将每个 Phase 的 agent() 调用逻辑提取到独立的 `.js` 文件
3. 主文件保留:
   - `export const meta = {...}`
   - 参数解析 (MODULE, MODE, PROJECT)
   - 公共函数 (assertGate, requirePageArtifacts, writeStatus)
   - `switch(MODE)` 调度逻辑
4. 子模块通过 Workflow API 的 `import()` 或内联引用加载
5. 向后兼容: 确保 `mode=full` 流程完全一致

## 风险

- Workflow API 是否支持模块化加载（需验证）
- 跨文件变量共享（args, STATUS_FILE 等需要通过参数传递）
- 测试成本高（需要覆盖所有 mode 组合）

## 优先级

🟢 **低优先级** — 当前 927 行的单文件已可接受。此优化在模块数量增长到 15+ 时价值更大。
建议在完成 Phase 1-3 全部优化后再实施。
