# AUTO_STRATEGY — personnel / certificate

> 基于 TECH_ANALYSIS + PAGE_CONTEXT | 2026-06-12
> 页面类型: 标准 CRUD 管理页（表格 + 搜索筛选 + 8字段弹窗表单）

## 覆盖矩阵

| 编号 | 标题 | 优先级 | 自动化 | 理由 |
|------|------|--------|:--:|------|
| CERT-01 | 页面正常加载 | P0 | ✅ | 表格+搜索区渲染检测 |
| CERT-02 | 证书名称搜索 | P1 | ✅ | CSS input[placeholder*=证书名称] |
| CERT-03 | 状态下拉筛选 | P1 | ✅ | el-select 定位 |
| CERT-04 | 重置搜索 | P1 | ✅ | |
| CERT-05 | 分页切换 | P1 | ✅ | el-pagination 点击 |
| CERT-06 | 新增证书-弹窗完整性 | P0 | ✅ | 8字段表单渲染+标题校验 |
| CERT-07 | 新增证书-必填校验 | P1 | ✅ | 空提交→前端拦截 |
| CERT-08 | 新增证书-名称唯一性 | P0 | ✅ | 重复名称→后端错误 |
| CERT-09 | 新增证书-日期校验 | P1 | ✅ | 颁发日期>当前→拦截 |
| CERT-10 | 新增证书-永久有效联动 | P1 | ✅ | switch→日期选择器disable |
| CERT-11 | 新增证书-用户不存在 | P1 | ✅ | 不存在用户→提示 |
| CERT-12 | 编辑证书 | P1 | ✅ | 预填→修改→保存 |
| CERT-13 | 删除证书 | P1 | ✅ | 确认弹窗→记录消失 |
| CERT-14 | 删除-取消 | P2 | ✅ | 弹窗关闭→记录保留 |
| CERT-15 | 空数据状态 | P2 | ✅ | el-empty显示 |

## PageObject 拆分

```
CertificateManagePage
├── 搜索区: search_cert_name / search_status / click_search / click_reset
├── 表格区: get_table_rows / get_row_by_name / click_edit / click_delete
├── 弹窗区: fill_cert_name / fill_user / select_cert_type / fill_issue_org
│          fill_issue_date / fill_valid_start / toggle_permanent / fill_remark
│          click_confirm / click_cancel / get_dialog_title
├── 确认弹窗: confirm_delete / cancel_delete
└── 导航: navigate_to_certificate_management
```

## ROI

| 指标 | 值 |
|------|-----|
| 预计投入 | ~3h (PageObject + test + conftest) |
| 预计维护 | ~0.3h/月 |
| 手工测试 | 15min/次 |
| 目标自动化率 | 100% (15/15) |

## 技术债
- 无

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 -->
