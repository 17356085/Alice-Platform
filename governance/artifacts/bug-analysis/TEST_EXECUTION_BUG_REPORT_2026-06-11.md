# 全模块测试执行 Bug 报告

> 执行时间：2026-06-11 16:02 ~ 17:04（约 2 小时）
> 执行范围：5 个模块 (lab / equipment / personnel / system / sales)，共 49 个测试文件
> 目标环境：https://aiwechatminidemo.cimc-digital.com/（admin / test 环境）
> 执行工具：pytest 8.3.5 + Selenium 4.44.0 + headless Chrome

---

## 一、总体概况

| 模块 | 测试文件数 | 通过 | 失败 | 跳过 | 错误 | 重跑次数 | 状态 |
|------|-----------|------|------|------|------|----------|------|
| **lab** | 1 | 8 | 2 | 0 | 0 | 5 | 基本健康 |
| **equipment** | 7 | 30 | 43 | 32 | 0 | 87 | 严重 |
| **personnel** | 7 | 22 | 30 | 1 | 12 | 84 | 严重 |
| **system** | 15 | 0 | 0 | 0 | 0 | 0 | 阻塞 |
| **sales** | 19 | ~部分 | ~大部分 | ~部分 | ~0 | ~大量 | 严重（未完成） |
| **合计** | **49** | **~60+** | **~75+** | **~33+** | **12** | **~176+** | — |

---

## 二、Bug 清单与路由建议

### P0 — 阻塞级（整个模块无法运行）

| ID | 位置 | 描述 | 路由建议 |
|----|------|------|----------|
| **BUG-001** | [MenuManagePage.py:736](ZJSN_Test-master526/page/system_page/MenuManagePage.py#L736) | f-string 嵌套双引号导致语法错误 — system 模块 15 个测试文件全部阻塞 | `code-consistency-checker` Skill |

### P1 — 严重级（整个页面/功能模块不可用）

| ID | 文件 | 现象 | 路由建议 |
|----|------|------|----------|
| **BUG-002** | test_maintenance_management | URL 落在 `#/equipment/camera` 而非 `#/equipment/maintenance` | `page-object-generator` + `tech-analysis` |
| **BUG-003** | test_equipment_management | 表头 `[]`、表格 0 行（TimeoutException） | 同上 |
| **BUG-004** | test_sensor_management | 表格头全缺失、统计卡片 `{}` | 同上 |
| **BUG-005** | test_unit_management | 表头 `[]`、搜索/新增按钮不可见 | 同上 |
| **BUG-006** | test_key_param | 统计卡片 `{}`、表头 `[]` | 同上 |
| **BUG-007** | test_question_bank (12 ERROR) | `'QuestionBankPage' has no attribute 'wait_for_loading_mask'` | `page-object-generator` Skill |
| **BUG-008** | test_employee_management | 页面加载 3 次 rerun 全挂 | `bug-analysis` Skill（分析截图） |
| **BUG-009** | test_exam_management | test_001~012 多数挂 | 同上 |
| **BUG-010** | test_paper_management | 关键字段 0/9 缺失 | 同上 |
| **BUG-011** | test_post_management (6 FAILED) | 新增/搜索/编辑/删除全 Timeout | `page-object-generator` Skill |
| **BUG-012** | test_exam_management | 新增/删除 Timeout + 搜索找不到 | `test-script-generator` Skill |
| **BUG-013** | test_train_plan_management (8 FAILED) | 表头缺失 + 全部操作 Timeout | `page-object-generator` + `test-script-generator` Skill |
| **BUG-014** | test_paper_management | `NameError: name 'By' is not defined` | `test-script-generator` Skill |
| **BUG-015** | test_contract (test_002~010) | 新增弹窗不弹出 + 操作全 Timeout | `page-object-generator` Skill |
| **BUG-016** | test_alarm_config | 9 个 CRUD 用例全部 SKIP | `test-script-generator` Skill |
| **BUG-017** | test_sensor_management | `.el-button--success` 找不到 | `page-object-generator` Skill |

### P2 — 中等级

| ID | 位置 | 现象 | 路由建议 |
|----|------|------|----------|
| **BUG-018** | test_gas_analysis_report:140 | 日期字符串比较错误 | `test-script-generator` Skill |
| **BUG-019** | test_gas_analysis_report:92 | 表头定位器失效 | `tech-analysis` Skill |
| **BUG-020** | test_customer | `element click intercepted` | `page-object-generator` Skill |

### P3 — 代码质量

| ID | 类型 | 现象 | 路由建议 |
|----|------|------|----------|
| **BUG-021** | 技术债 | 日志中文乱码 | `code-consistency-checker` Skill |
| **BUG-022** | 规范 | `time.sleep(0.5)` 硬编码 | 同上 |
| **BUG-023** | 体验 | 首次页面加载超时率高 | `tech-analysis` Skill |

---

## 三、推荐处理路线图

```
第1步（立即）: 【新对话 -> code-consistency-checker Skill】
  修复 BUG-001 (MenuManagePage SyntaxError)，解放 system 模块

第2步（立即）: 【新对话 -> page-object-generator Skill】
  修复 BUG-007 (QuestionBankPage 缺失 wait_for_loading_mask)

第3步（立即）: 【新对话 -> test-script-generator Skill】
  修复 BUG-014 (paper_management 缺少 By import)

第4步（本周）: 【新对话 -> page-object-generator + tech-analysis Skill】
  修复 BUG-002~006 (Equipment 导航全挂，5 个子页面)

第5步（本周）: 【新对话 -> page-object-generator Skill】
  修复 BUG-011/013/015/017 (personnel+sales CRUD 按钮定位)

第6步（本周）: 【新对话 -> test-script-generator Skill】
  修复 BUG-012/016/018 (日期比较 + SKIP + 等待策略)

第7步（迭代）: 【新对话 -> code-consistency-checker + tech-analysis Skill】
  修复 BUG-021~023 (编码/规范/超时优化)
```

---

## 四、Artifacts 指针

- 失败截图 & HTML: `ZJSN_Test-master526/artifacts/failures/`
- Allure 原始数据: `ZJSN_Test-master526/allure-results/`
- Allure 报告生成: `allure generate allure-results -o allure-report --clean`

---

*报告由 Claude Code 生成，基于 2026-06-11 全量测试执行。*
