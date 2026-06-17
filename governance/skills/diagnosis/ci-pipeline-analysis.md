# Skill: ci-pipeline-analysis

## 目标
分析 Jenkins / CI 流水线的阶段问题、失败模式和改进点。

## 输入
- Jenkinsfile
- 构建日志
- 测试报告
- 环境参数

## 输出
- 阶段问题定位
- 失败归类
- 优化建议
- 可 Skill 化动作建议

## 规则
- 区分环境问题、配置问题、脚本问题、产品问题
- 区分并行安全任务与串行破坏性任务
- 关注产物归档与可追踪性

## 关联资产
- d:\Desktop\WorkStudy\ZJSN_Test-master526\Jenkinsfile

---

## Prompt 模板

```text
分析以下CI构建结果，诊断问题。

## 构建信息
- Jenkins Job：{{ZJSN_Test}}
- 构建编号：{{#123}}
- 构建状态：{{失败}}
- 构建日志：
```
{{粘贴关键日志片段}}
```

## 任务
1. **构建失败原因**：快速定位失败阶段（Sync/Lint/Safe Tests/Destructive Tests/Report）
2. **与上次成功构建的差异**：
   - 代码变更？
   - 环境变更？
   - 数据变更？
3. **失败类型判断**：
   - 编译/依赖问题 → 环境
   - 用例失败 → 测试
   - 超时 → 性能/环境
4. **修复建议**：具体操作步骤
5. **CI配置优化建议**：
   - 是否添加重试？调整超时时间？
   - 是否增加前置检查步骤？
```

## 检查清单
- [ ] 失败阶段定位明确（Sync/Lint/Safe/Destructive/Report）
- [ ] 区分了环境问题/配置问题/脚本问题/产品问题
- [ ] 与上次成功构建有对比分析
- [ ] 修复建议具体可操作
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | diagnosis | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->