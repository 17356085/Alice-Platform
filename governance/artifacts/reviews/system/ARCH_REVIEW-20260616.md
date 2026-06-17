# Architecture Review Report — AITest Platform

---
report_id: REVIEW-20260616-8a4f2c3b
review_type: architecture
module: system
trigger: manual
depth: standard
reviewer: review/architecture-assessment v1.0
created: 2026-06-16
---

## Executive Summary

**Overall Score:** 57/100 (C)
**Critical Issues:** 3
**Warnings:** 5
**Recommendations:** 8

架构评估57分，评级C。系统在Agent和SOP编排骨架方面合理，治理层建设也较完整，但存在组件边界一致性、测试与开发SOP模式不对称、以及技术债务积累等问题。tank模块的自定义UI脱离通用定位体系是当前测试基线偏低（62.4%）的架构根因之一。治理层已发现16个真实问题，但架构层面尚未完全收敛到统一模式。开发→评审→修复→复评效率不足。

## Dimension Scores

| Dimension | Score | Assessment |
|-----------|-------|------------|
| Component Boundary | 45/100 | tank模块边界不一致，职责重叠未收敛 |
| Data Flow | 60/100 | 事件驱动链路完整，但多源状态同步机制脆弱 |
| Coupling | 70/100 | 组件间依赖较合理，但SOP硬编码节点耦合度未最小化 |
| Scalability | 50/100 | 新增模块成本高，平均5~8文件，缺乏对称SOP扩展机制 |
| Consistency | 40/100 | Test SOP(8-step) vs Dev SOP(9-step)模式不统一，边界判定不同 |
| Technical Debt | 35/100 | 临时方案固化（tank模块典型），PO-UI适配问题未自动化 |

## Findings

### Critical (must fix)

| ID | Dimension | Finding | Impact | Recommendation | Effort |
|----|-----------|---------|--------|----------------|--------|
| C01 | Component Boundary | **tank模块使用自定义UI框架，BasePage通用定位器不可用**。该模块的DOM访问方式与其他模块不一致，PO编写时需手动诊断DOM。"工厂代码"非"标题"，无法使用通用定位策略。 | 跨模块UI自动化能力不可复用，维护成本极高。测试基线62.4%的主要贡献者（约30%失败案例集中在此模块）。 | 短期：为tank实现适配层，将自定义UI框架的定位接口映射到BasePage通用定位方法。长期：推动tank模块UI标准化为Element Plus。提供适配器封装使自定义元素的定位策略可被通用方法发现。 | L |
| C02 | Consistency | **Test SOP(8 Agent)与Dev SOP(9 Agent)架构模式不对称**。Test SOP以 project→requirement→test-design→automation→execution→bug-analysis→report→knowledge 为主线，Dev SOP为 pm→req→arch→design→frontend/backend→review→test→debug→build。两个SOP对"知识沉淀"的处理位置不同，Dev SOP将"test"和"debug"分开而Test SOP合并为"bug-analysis"。 | Agent定义、Skill注册表管理不统一。跨SOP对比时容易产生认知偏差。治理层写SOPViolation检查逻辑时需分别处理。 | 统一SOP抽象层：定义"共通阶段"枚举（planning, executing, verifying, closing），再将两个SOP映射到该抽象。knowledge沉淀改为跨SOP关注点，而非SOP末位节点。 | L |
| C03 | Scalability | **新增一个业务模块（如dashboard）需同时修改graphs、agent-definitions、skill-registry、State Auditor配置、测试配置等5~8个文件**。当前无"Add-X"脚手架或自动注册机制。 | 团队扩展速度受限，遗漏风险高。已发现16个治理问题中可能有未注册遗漏导致。 | 构建`auto-register`装饰器：agent-definitions中新增Agent时自动更新SOP图和Skill关联表。生成初始占位符。引入模块脚手架命令：`cli.py add-module <name>`一键更新所有必要文件。 | M |

### Warnings (should fix)

| ID | Dimension | Finding | Impact | Recommendation | Effort |
|----|-----------|---------|--------|----------------|--------|
| W01 | Data Flow | **SQLite + JSON + YAML 三源状态存储同步一致性缺乏原子性保证**。当前Agent Loop的状态更新先写SQLite checkpoint再更新JSON/YAML事实源，未实现事务性补偿机制。 | 出现StateDrift事件时难以追溯哪个源先失败。已观测到16个治理问题中约3个难以追溯到同步时序问题。 | 引入写前日志（WAL）模式，将状态变更写入单一权威记录（SQLite），JSON/YAML作为惰性快照通过定时/事件同步生成。 | M |
| W02 | Coupling | **Skill Registry中test-design skill与automation skill存在隐式契约**。test-design的输出格式被automation隐式依赖，修改模板可能意外破坏下游自动化Agent。 | 修改成本不可预知，回归测试容易漏检。 | 为每个Skill定义interface契约（如JSON Schema），通过SOP图在阶段间验证契约。 | M |
| W03 | Component Boundary | **Test SOP的requirement Agent与Dev SOP的req Agent职责高度重叠但实现分离**。两个Agent功能类似，但指向不同事实源（Test从测试视角，Dev从开发视角），缺乏协调机制。 | 需求变更时两个Agent需分别更新，易产生矛盾。知识沉淀时需手动去重。 | 将"需求分析"职责提升为独立Agent，通过上下文字段标记（context_flag: test/dev）切换视角，避免重复维护。 | M |
| W04 | Technical Debt | **workflow-pages搜索字段硬编码为"工厂代码"而非"标题"**。该硬编码值散布在2个Agent的prompt和1个skill指令中。 | UI字段名变更（如改为"工厂编号"）需修改多处代码文件。PO编写前必须人工诊断DOM，违反数据驱动定位原则。 | 将UI元素定位策略集中管理：引入`locators.yaml`每页面模块，用统一命名服务实现元素→定位器映射。 | S |
| W05 | Consistency | **State Auditor(7 checks)与SOP Auditor(7 checks)之间存在重叠规则**（"状态一致性"与"SOP合规性"），但两个Auditor使用不同的规则描述方式。 | 审计维度重叠导致重复工作，合并分析时需要手动对齐。 | 将重叠规则合并到`governance/rules/`统一规则目录下，State Auditor和SOP Auditor共享同一规则通过规则ID引用。 | S |

### Observations (nice to fix)

| ID | Dimension | Finding | Recommendation |
|----|-----------|---------|----------------|
| O01 | Scalability | Agent Runner (2046行) 承担过多职责：执行Perceive/Plan/Act/Observe循环 + checkpoint管理 + 事件发射。 | 拆分：事件发射提取为`EventEmitter`，checkpoint管理提取为`StateManager`。 |
| O02 | Data Flow | Knowledge Agent通过事件订阅消费，但事件粒度较粗（如"test-execution-completed"），Knowledge Agent需额外解析大量数据才能沉淀知识。 | 增加细粒度事件（如"test-case-passed"、"bug-found"），附带预计算的摘要供Knowledge Agent直接使用。 |
| O03 | Technical Debt | chat.html FastAPI测试工作台使用率低，大部分测试通过SOP自动化完成，该工作台成为维护负担。 | 评估chat.html使用频率，若长期低频可转为按需启动，或将其功能迁移到CLI/Web UI。 |
| O04 | Coupling | Skill Registry版本号统一为v1.0，缺乏版本兼容性测试。升级一个skill并改变输出格式时可能破坏下游skill和Agent。 | 引入SemVer语义化版本，skill版本与契约Schema绑定，Agent声明所需skill版本范围。 |

## Cross-Audit Analysis

| 审计发现 | 架构根因 | 修复优先级 |
|---------|----------|-----------|
| 全量SOP 828 tests baseline 62.4% | tank模块架构边界不一致（C01）是最大贡献者（约30%失败），workflow-pages字段硬编码（W04）贡献约10%失败。 | 修复C01可将基线提升至75%+，修复W04可进一步提升至80%+ |
| equipment unit + personnel exam 0 ERROR（已修复） | 这两个模块使用标准Element Plus + BasePage通用定位方法，验证了一致性架构的价值。 | 证明统一UI框架是正确方向 |
| Governance validation sprint发现16个真实问题 | 其中3个与同步一致性（W01）有关，2个与重复Agent职责（W03）有关。架构层面不协调直接导致治理漏洞。 | 优先修复W01、W03 |

## Architecture Decision Records

| ADR ID | Title | Decision | Rationale | Status |
|--------|-------|----------|-----------|--------|
| ADR-001 | 统一SOP抽象层 | 引入共通阶段枚举，将Test SOP和Dev SOP映射到同一骨架 | 解决不对称性导致的Agent/Skill混淆，降低跨SOP认知负担 | Proposed |
| ADR-002 | 确立SQLite权威状态 | 状态存储以SQLite为唯一权威源，JSON/YAML惰性快照 | 解决三源同步一致性问题，简化State Auditor逻辑 | Proposed |
| ADR-003 | tank适配层 | 短期编写tank UI适配层，通过适配器暴露标准定位接口 | 平衡修复成本与收益，长期推动标准化 | Approved (sprint 3) |

## Action Items

| Priority | Action | Effort | Rationale |
|----------|--------|--------|-----------|
| P0 | 修复tank模块架构边界（C01）— 实现BasePage适配层 | L | 直接影响基线，30%失败可恢复 |
| P0 | 统一SOP抽象层（C02）— 定义共通阶段，映射两个SOP | L | 解决架构层不一致，降低长期维护成本 |
| P0 | 状态同步一致性（W01）— 建立SQLite权威记录+惰性快照 | M | 治理层事件溯源可靠性基础 |
| P1 | 新增模块脚手架（C03）— 实现`cli.py add-module` | M | 提升扩展效率，消除注册遗漏 |
| P1 | 硬编码字段抽取（W04）— 引入locators.yaml | S | 解决字段名变更问题，再提升基线约5% |
| P1 | 合并重叠审计规则（W05） | S | 减少重复劳动，降低审计歧义 |
| P2 | Skill版本兼容性测试（O04） | M | 防止级联破坏，保障Agent稳定性 |
| P2 | Agent Runner职责拆分（O01） | L | 提升可测试性和可维护性 |

> **注：** Action Item优先级参考"影响×努力"矩阵。P0为关键路径项，集中在下一个Sprint。若投入40%精力修复C01和C02，预计架构评分可从57提升至70分（B-）。
