# 会话最佳实践 — 一个模板用到底

> 目标：一个模块 SOP 走完 ≤4 个会话，总花费 ≤$0.25，不乱。

---

## 黄金模板（直接复制用）

以 equipment 模块、2 个页面（alarm-config, device-list）为例。

### 会话 1：分析 (≤40轮)

```
模块: equipment
进度: 未开始
目标: 完成 MODULE_CONTEXT + alarm-config 的 PAGE_CONTEXT + TEST_CASES
```

中间自然推进，不需要拆。AI 读完模块结构直接切到第一个页面做测试设计，上下文连着的。

```
>> equipment MODULE_CONTEXT + alarm-config PAGE_CONTEXT + TEST_CASES 已完成 (P0×3 P1×5)
>> 下一会话: "模块: equipment 进度: alarm-config 测试设计已完成 目标: alarm-config + device-list 的 PO + test"
```

### 会话 2：写代码 (≤45轮)

```
模块: equipment
进度: alarm-config PAGE_CONTEXT + TEST_CASES 已完成
      device-list 的还没做，先跳过
目标: alarm-config PageObject + test_alarm_config.py，然后 device-list 同上
```

```
>> alarm-config + device-list 的 PO 和 test 全部完成
>> 下一会话: "模块: equipment 进度: PO+test全部完成 目标: 跑pytest + 修失败 + 出报告"
```

### 会话 3：执行 + 收尾 (≤40轮)

```
模块: equipment
进度: alarm-config + device-list 的 PO+test 已完成
目标: 跑 pytest → 修失败用例 → 生成报告 → 沉淀经验
```

```
>> equipment 模块 SOP 全闭环。29 passed / 2 failed / 1 skipped
>> 2 个 failed 是已知问题: el-cascader 弹窗不稳定 (已有 RAG 条目 #17)
>> sop_status 已更新到 SOP_STATUS_equipment.json
```

### 如果失败多，加一个会话 4：专项修 Bug (≤30轮)

```
模块: equipment
问题: 6 个用例失败，集中在 el-cascader 和 el-dialog 弹窗
目标: 逐个修复 + 重跑验证
```

---

## 三个铁律

### 1. 开头 3 行（省 5-10 轮探索）

```
模块: <名>  页面: <名>（如果有）
进度: <上一会话产出，一行>
目标: <本次要产出什么，一行>
```

❌ "测 equipment 模块" → AI 要从头探索状态
❌ 贴一大段历史 → 浪费 token
✅ 上面 3 行 → AI 秒懂

### 2. 50 轮收尾（省 70% 费用）

别管 Phase 到哪了，感觉对话变慢就收。SOP_STATUS.json 会记住断点，下次 `resume` 继续。

```
>> 先到这。进度: alarm-config PO 写了 70%，el-cascader 定位还没搞定
>> 下一会话: "equipment/alarm-config el-cascader定位问题 目标: 解决并完成剩余30%"
```

### 3. Grep 先、Read 准（省 60% 单轮 token）

```
❌ Read page/alarmConfigPage.py          → 500 行全进上下文
✅ Grep "def \|class " page/alarmConfigPage.py  → 只看方法名
✅ Read page/alarmConfigPage.py:120-150          → 只看需要的那 30 行

❌ Read 全部 allure 结果 JSON
✅ Grep "status.*failed" allure-results/ -l

❌ Read TEST_CASES.md 全文重温
✅ Grep "P0\|P1" TEST_CASES.md -A 1
```

---

## 一张图总结

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  会话1 (≤40轮)         会话2 (≤45轮)      会话3 (≤40轮)   │
│  ┌──────────────┐    ┌──────────────┐   ┌──────────────┐ │
│  │ 分析+设计    │ →  │ 写代码       │ → │ 执行+修+报告 │ │
│  │              │    │              │   │              │ │
│  │ Preflight    │    │ PageObject   │   │ pytest       │ │
│  │ Requirement  │    │ test_*.py    │   │ Bug Analysis │ │
│  │ Test Design  │    │ (1-2页)      │   │ Report       │ │
│  │              │    │              │   │ Knowledge    │ │
│  └──────────────┘    └──────────────┘   └──────────────┘ │
│                                                          │
│  开头3行    结尾留状态   SOP_STATUS.json 是断点续跑底气    │
│  50轮红线   Grep先Read准   一个会话一个明确产出            │
│                                                          │
│  总花费 ~$0.23  总轮数 ~125  总会话 3-4个                  │
│  对比旧方式: 省 75% 费用                                  │
└──────────────────────────────────────────────────────────┘
```

---

## 什么时候打破 3 会话节奏

| 情况 | 做法 |
|------|------|
| 模块只有 1 个页面 | 2 个会话就够：分析+写代码 / 执行+收尾 |
| 模块有 5+ 个页面 | 会话2 拆成两个：先做 2 页，再做 3 页 |
| 中间遇到顽固 Bug | 收尾当前，新开会话专项修，再切回来 |
| 跨天/跨半天 | 自然收尾，下个时段新会话接上 |
| 纯探索（不知道页面长什么样）| 先用一个 20 轮会话专门探索，再走 SOP |
