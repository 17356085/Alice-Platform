# Skill: data-preparer

## 目标
测试数据准备 — 生成/刷新/清理测试数据，确保每个测试用例有可用的前置数据。

## 输入
- 模块名称 + 页面列表
- TEST_SPEC.md (测试用例的数据依赖)
- test_data_policy.md (数据策略)
- test_accounts.yaml (账号配置)

## 输出
- TEST_DATA_REPORT.md — 数据就绪报告
  - 账号状态 (可用/锁定/过期)
  - 测试数据清单 (每页面所需数据 + 状态)
  - 数据生成脚本 (如需要)
  - 清理脚本 (测试后恢复)

## 操作类型

| 模式 | 操作 | 触发条件 |
|------|------|---------|
| quick | 检查数据是否已存在 | 快速模式 |
| full | 清理旧数据 → 生成新数据 → 验证 | 完整模式 |
| refresh | 仅刷新过期数据 | 增量模式 |

## 数据策略
- 测试数据与生产数据隔离 (test_ 前缀)
- 每次全量执行前清理残留数据
- 账号不硬编码，从 .env / test_accounts.yaml 读取
- 数据生成脚本放在 ZJSN_Test-master526/data/ 目录

## 规则
- 数据生成失败 → 标记 env_ready=false
- 使用工厂模式 (Factory Boy / Faker) 生成随机但合理的数据
- 关键业务数据 (如设备编号) 使用预定义种子数据

## 依赖
- governance/context/config/test_accounts.yaml
- governance/context/projects/web-automation/test-data-policy.md
- ZJSN_Test-master526/data/

## 边界
- 不访问生产数据库
- 不修改被测系统代码
- 仅操作测试专用数据表/账号

---

## Prompt 模板

```text
你是一个测试数据工程师。请为以下模块准备测试数据。

## 模块信息
- 模块名称：{{module_name}}
- 页面列表：{{page_list}}
- 测试用例数：{{test_count}}
- 数据策略：{{data_policy}}

## 任务
1. 从 TEST_SPEC.md 提取数据依赖清单
2. 检查 test_accounts.yaml 账号可用性
3. 生成必需的测试数据 (使用 Faker/预定义种子)
4. 生成清理脚本 (测试后恢复)
5. 输出 TEST_DATA_REPORT.md

## 输出
- 账号状态表
- 每页面数据依赖 + 状态 (✅就绪 / ⚠️需生成 / ❌不可用)
- 数据生成脚本路径
- 清理脚本路径
```
