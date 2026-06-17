# MODULE_CONTEXT — equipment

## 基本信息
- 模块ID：equipment
- 模块名称：设备管理
- 所属项目：web-automation
- 存量来源：d:\Desktop\WorkStudy\TestIntern_library\02-项目文档\contexts\equipment\
- 关联旧文档：MODULE_CONTEXT.md

## 模块定位
设备管理承接设备相关台账、报警配置、维保、关键参数与摄像头等页面，是典型的设备业务测试模块。

## 当前页面清单
- alarm-config - ✅ 已完成全部 8 治理文档 + PO + test
- camera - ✅ 已完成全部 8 治理文档 + PO + test
- key-param - ✅ 已完成全部 8 治理文档 + PO + test
- maintenance - ✅ 已完成全部 8 治理文档 + PO + test
- unit-manage - ⚠️ 仅 PAGE_CONTEXT，待补齐其余文档
- sensor-manage - ⚠️ 仅代码 PO 存在，待补齐治理文档

## 治理说明
- 本次先按旧 contexts 已存在页面补骨架
- 其他设备子页面后续按实际资产继续补齐

## 映射状态
- alarm-config 已完成 PAGE_CONTEXT、PAGE_ELEMENT_POSITION 映射
- camera 已完成 PAGE_CONTEXT、PAGE_ELEMENT_POSITION 映射
- maintenance 已完成 PAGE_CONTEXT、PAGE_ELEMENT_POSITION 映射


<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-stats -->
<!-- Source: tools/sync_progress.py — regenerated on each SOP run -->
## 自动统计数据 (更新于 2026-06-17 16:53)

| 指标 | 数值 |
|------|:---:|
| 测试文件 | 8 (script/equipment/test_*.py) |
| Page Object | 7 (page/equipment_page/*.py) |
| 治理文档 | 30 .md 文件 |
| TECH_ANALYSIS | 4 |
| AUTO_STRATEGY | 4 |
| RISK_MODEL | 4 |
| PAGE_CONTEXT | 5 |
| SOP 状态 | completed |
| Phase 完成 | Automation, Bug Analysis, Data Sanitization, Execute & Debug, Knowledge, Project Init, Report, Requirement, Test Design |

> 此段由 sync_progress.py 自动更新。手动编辑会被覆盖。
<!-- ⚠️ AUTO-GENERATED SECTION END: module-stats -->