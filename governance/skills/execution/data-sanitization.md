# Skill: data-sanitization

> 离线扫描并清理测试残留数据。对应 test-data-policy.md 兜底策略。

## 目标
在测试执行完成后，扫描后端所有模块中名称含测试前缀（`test_` / `TC-` / `分页-`）的残留数据，并通过 API 批量清理。不依赖 CleanupTracker 注册——覆盖测试异常中断、注册遗漏等场景。

## 输入
- `module` — 模块名（可选，不传则扫描全部模块）
- `--force` — 强制模式（SOP 内始终使用）
- `CLEANUP_CONFIG` from `ZJSN_Test-master526/config/cleanup.py`

## 输出
```json
{
  "residual_count": 0,
  "cleaned_count": 0,
  "threshold_exceeded": false,
  "modules_scanned": ["dict", "user", "role", "course", "contract", "equipment"],
  "details": {"module_name": "N 条残留数据"}
}
```

## 执行

```bash
cd ZJSN_Test-master526
python tools/cleanup/scan_and_clean.py --force [--modules=<module>]
```

## 规则
1. `--force` 模式：不交互确认，直接清理
2. 阈值检查: `max_residual_allowed: 50`（超过 → 告警但不阻塞流水线）
3. 清理范围: dict / user / role / course / contract / equipment（共 6 个模块）
4. 匹配前缀: `test_` (通用) / `分页-` (合同模块专属)
5. 清理失败不抛异常，记录 warning

## 依赖
- `ZJSN_Test-master526/tools/cleanup/scan_and_clean.py`
- `ZJSN_Test-master526/config/cleanup.py`（CLEANUP_CONFIG）
- `governance/context/projects/web-automation/test-data-policy.md`（数据清理规范）

## 边界
- 只清理 API 可删除的数据（batch_clean_urls 中注册的实体类型）
- 不清理 UI 创建的数据（需通过 CleanupTracker UI 模式清理）
- 不修改测试代码
- 不分析清理失败原因（那是 bug-analysis 的职责）
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | execution | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->