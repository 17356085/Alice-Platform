# Code Review — equipment

> ⏳ 待执行 — 2026-06-17 governance audit 创建骨架
> 执行: 运行 code-consistency-checker Skill 或手动审查

## 待检查项

- [ ] Page Object 定位器稳定性 (BasePage 4-level fallback 使用正确性)
- [ ] 测试脚本与 Page Object 方法签名一致性
- [ ] conftest.py fixture 覆盖完整性
- [ ] 硬编码等待 (time.sleep) → 替换为 wait_page_ready/wait_table_ready
- [ ] Element Plus 组件交互 (el-select/el-dialog/el-date-picker Teleport 处理)

## 模块概况

  - PO files: 8
  - Test files: 8
