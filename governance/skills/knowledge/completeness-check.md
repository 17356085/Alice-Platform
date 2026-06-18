# Skill: completeness-check

## 目标
检查模块/页面上下文的文档完整性，识别缺失文档和缺口。

## 输入
- context/projects/<project>/modules/ 目录结构
- 需检查的模块/页面清单

## 输出
- 文档完整性报告
- 缺失文档清单（标注优先级 P0/P1/P2）

## 规则
- 检查标准按 SOP Phase：MODULE_CONTEXT（Phase 0.5）、PAGE_CONTEXT（Phase 1）、RISK_MODEL（Phase 1.5）、TEST_DESIGN（Phase 2）、TEST_CASES（Phase 2.5）、TECH_ANALYSIS（Phase 3）、PAGE_ELEMENT_POSITION（Phase 3）、AUTO_STRATEGY（Phase 3.5）
- P0：阻塞测试执行（缺少 PAGE_CONTEXT / TEST_DESIGN）
- P1：影响质量（缺少 RISK_MODEL / TEST_CASES）
- P2：锦上添花（缺少 AUTO_STRATEGY / TECH_ANALYSIS）
- 给出补充建议（哪些可基于现有信息推断，哪些需要访问实际页面）

## 依赖
- skills/module-modeling.md
- workflows/sop-summary.md

## 边界
- 本 Skill 只检查文档存在性，不验证文档质量
- 不自动补充缺失内容

---

## Prompt 模板

```text
检查 contexts/ 下各模块的文档完整性。

## 检查标准
对每个模块/页面，检查是否具备以下文档：
- [ ] MODULE_CONTEXT.md（Phase 0.5）
- [ ] 每个页面有 PAGE_CONTEXT.md（Phase 1）
- [ ] 每个页面有 RISK_MODEL.md（Phase 1.5）
- [ ] 每个页面有 TEST_DESIGN.md（Phase 2）
- [ ] 每个页面有 TEST_CASES.md（Phase 2.5）
- [ ] 每个页面有 TECH_ANALYSIS.md（Phase 3）
- [ ] 每个页面有 PAGE_ELEMENT_POSITION.md（Phase 3）
- [ ] 每个页面有 AUTO_STRATEGY.md（Phase 3.5）

## 优先级定义
- P0：阻塞测试执行（缺少 PAGE_CONTEXT / TEST_DESIGN）
- P1：影响质量（缺少 RISK_MODEL / TEST_CASES）
- P2：锦上添花（缺少 AUTO_STRATEGY / TECH_ANALYSIS）

## 任务
1. 逐模块输出缺失文档清单
2. 标注每个缺失项的优先级（P0/P1/P2）
3. 给出补充建议：
   - 可基于现有信息推断的 → 标注"可推断"
   - 需要实际访问页面的 → 标注"需浏览器"
```

### 单模块深度检查

```text
对 {{设备管理}} 模块执行深度文档完整性检查。

## 检查范围
1. 对照 MODULE_INDEX.md 确认模块是否已注册
2. 对照 PAGE_CONTEXT 中的子页面清单，确认每个页面是否具备：
   - PAGE_CONTEXT.md（元素清单完整？）
   - PAGE_ELEMENT_POSITION.md（定位器表完整？A/B/C三级覆盖？）
   - RISK_MODEL.md（6维度全覆盖？P0风险有缓解措施？）
   - TEST_DESIGN.md（8维度全覆盖？每个场景有执行方式标注？）
   - TEST_CASES.md（P0覆盖率100%？测试数据具体可执行？）
   - TECH_ANALYSIS.md（Element Plus组件全识别？等待策略覆盖5种场景？）
   - AUTO_STRATEGY.md（覆盖矩阵完整？ROI计算完整？）
3. 对照自动化代码确认 Page Object 和 test_*.py 是否与文档对应

## 输出
| 文档类型 | 状态 | 优先级 | 获取方式 | 备注 |
|----------|------|--------|----------|------|
| PAGE_CONTEXT | ✅ 已有 | — | — | 17个元素，完整 |
| RISK_MODEL | ❌ 缺失 | P1 | 可推断 | 可基于PAGE_CONTEXT和权限矩阵推断 |
| TEST_CASES | ⚠️ 不完整 | P0 | 需补充 | P0覆盖率仅60%，缺权限/异常场景 |
```

---

## 检查清单
- [ ] 所有已注册模块均已检查
- [ ] 缺失文档标注了优先级（P0/P1/P2）
- [ ] 补充建议标注了获取方式（可推断/需浏览器/需实际页面）
- [ ] 自动化代码与文档的对应关系已检查
- [ ] 不完整文档的具体缺口已标注
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | knowledge | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->