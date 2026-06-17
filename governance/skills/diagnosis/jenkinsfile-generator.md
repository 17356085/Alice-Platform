# Skill: jenkinsfile-generator

## 目标
根据模块测试脚本自动生成或更新 Jenkinsfile 中的 pytest 执行配置，自动识别安全/破坏性用例并分组。

## 输入
- 现有 Jenkinsfile（如已有）
- 模块测试脚本目录（`script/<module>/test_*.py`）
- pytest marker 信息（从测试脚本中提取的 `@pytest.mark.xxx`）

## 输出
- 更新后的 Jenkinsfile 片段（含正确的 stage 分组）
- 安全/破坏性用例分组清单
- 新增模块的 pytest 命令

## 规则
- 扫描 `@pytest.mark.destructive` 标记 → 归入串行执行组
- 无 destructive 标记的用例 → 归入并行执行组（`-n 3 --dist=loadfile`）
- 每个模块的 pytest 命令格式保持一致
- 保留现有 Jenkinsfile 的非 pytest 阶段（Sync/Lint/Report）
- 新增模块自动追加到对应 stage

## 依赖
- `ZJSN_Test-master526/Jenkinsfile`（参考模板）
- pytest marker 约定（smoke / destructive / skip）

## 边界
- 本 Skill 只生成/更新 Jenkinsfile，不修改 CI 服务器配置
- 不修改 credentials / environment 配置
- 不生成新的 Jenkins Job

---

## Prompt 模板

### 为新模块生成 Jenkinsfile 更新

```text
基于以下信息，更新 Jenkinsfile 的测试执行阶段。

## 当前 Jenkinsfile
```groovy
{{粘贴现有 Jenkinsfile 的 stages 部分}}
```

## 新增模块信息
- 模块名称：{{设备管理（equipment）}}
- 测试脚本路径：script/equipment/
- 测试文件清单：
  - test_alarm_config.py — 无 destructive marker（安全用例）
  - test_camera_management.py — 无 destructive marker（安全用例）
  - test_maintenance_management.py — 含 @pytest.mark.destructive（破坏性用例）
  - test_unit_management.py — 无 destructive marker（安全用例）
- 该模块是否需要独立浏览器：{{是/否}}

## 任务
1. **分析 marker 分布**：
   - 扫描各 test_*.py 中的 @pytest.mark 标记
   - 分类：安全用例（可并行） vs 破坏性用例（需串行）

2. **生成 Safe Tests stage 更新**：
```groovy
stage('Safe Tests (Parallel)') {
    steps {
        echo '=== 安全用例并行执行 ==='
        catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
            sh '''
                python -m pytest \\
                    script/equipment/test_alarm_config.py \\
                    script/equipment/test_camera_management.py \\
                    script/equipment/test_unit_management.py \\
                    script/system/test_user_management.py \\
                    -m "not destructive" \\
                    -n 3 --dist=loadfile \\
                    -q --tb=line \\
                    --alluredir=allure-results \\
                    2>&1 | tail -30
            '''
        }
    }
}
```

3. **生成 Destructive Tests stage 更新**：
```groovy
stage('Destructive Tests (Serial)') {
    steps {
        echo '=== 破坏性用例串行执行 ==='
        catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
            sh '''
                python -m pytest \\
                    script/equipment/test_maintenance_management.py \\
                    script/system/test_role_management.py \\
                    -m destructive \\
                    -q --tb=line \\
                    --alluredir=allure-results \\
                    2>&1 | tail -30
            '''
        }
    }
}
```

4. **约束**：
   - 安全用例全部放在并行 stage，破坏性用例全部放在串行 stage
   - 每个 .py 文件一行，用 \\ 续行
   - 保留 --alluredir=allure-results 参数
   - 不修改 Sync/Lint/Report/post 部分
   - 如果某个模块跨多个环境（dev/test/staging），用 TARGET_ENV 参数区分
```

### 全量 Jenkinsfile 健康检查

```text
检查当前 Jenkinsfile 的配置健康度。

## 输入
- Jenkinsfile：{{粘贴完整 Jenkinsfile}}
- 最近 5 次构建日志摘要：
{{粘贴构建摘要}}

## 任务
1. **测试分组合理性检查**：
   - 是否有 @pytest.mark.destructive 的用例被错误归入并行组？
   - 是否有安全用例被错误归入串行组？
   - 并行 worker 数（-n 3）是否适合当前节点配置？

2. **超时配置检查**：
   - 当前 timeout（3h）是否足够？（对比最近构建耗时）
   - 单个 stage 是否需要独立 timeout？

3. **产物归档检查**：
   - artifacts 路径是否覆盖所有可能的失败产物？
   - allure-results 是否正确归档？

4. **优化建议**：
   - 是否可以利用 pytest-test-groups 按模块自动分组？
   - 是否需要增加 flaky test 重试机制（--reruns）？
   - 是否需要增加构建前环境验证 step？
```

---

## 检查清单

- [ ] 所有 test_*.py 已扫描 marker 标记
- [ ] 安全用例和破坏性用例正确分组
- [ ] pytest 命令格式与现有保持一致
- [ ] --alluredir 参数在所有 stage 中统一
- [ ] 非 pytest stage（Sync/Lint/Report）未被修改
- [ ] 续行符 \\ 格式正确（无多余空格）
- [ ] 新增模块未遗漏任何 test_*.py

## 产出物
→ 更新后的 Jenkinsfile stage 片段或完整 Jenkinsfile。
→ 参考模板：`ZJSN_Test-master526/Jenkinsfile`。
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **0.1-exp** | experimental | diagnosis | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->