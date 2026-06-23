# TEST_DESIGN — system-management / api-management (接口管理)

> Phase 2 | 2026-06-13 | 输入: PAGE_CONTEXT + ApiManagePage.py
> Swagger UI iframe 嵌入页，测试结果: 3P/0F/1S
> 已有测试: test_api_management.py (4 cases)

## 基本信息

| 字段 | 值 |
|------|-----|
| 页面 | 接口管理 `#/system/api` |
| 页面类型 | Swagger UI iframe 嵌入（只读展示） |
| 无 CRUD | 页面展示后端 API 文档，纯查看 |

## 场景设计

### 一、页面加载

| 场景ID | 描述 | P | 步骤 | 预期 |
|--------|------|:--:|------|------|
| TD-API-001 | 页面正常加载 | P0 | 导航到 `#/system/api` | Swagger UI iframe 加载成功（4级检测: .swagger-ui → el-table → TableRows → 容器文本） |
| TD-API-002 | API分组可见 | P1 | 页面加载后检查 | 至少1个 tag-based API分组可见 |
| TD-API-003 | 空载状态(iframe未渲染) | P1 | 全量回归中网络慢 | 降级检测到el-table或文本即可 |

### 二、页面内容

| 场景ID | 描述 | P | 步骤 | 预期 |
|--------|------|:--:|------|------|
| TD-API-010 | Swagger topbar可见 | P1 | 检查iframe内 | API标题+版本信息 |
| TD-API-011 | API分组展开 | P1 | 点击分组→展开 | 显示该分组的接口列表(GET/POST/PUT/DELETE) |
| TD-API-012 | 获取API总数 | P1 | 统计接口数量 | 返回值 > 0 |

### 三、异常场景

| 场景ID | 描述 | P | 步骤 | 预期 |
|--------|------|:--:|------|------|
| TD-API-020 | iframe渲染超时 | P2 | 全量回归/网络慢 | 4级检测降级到文本匹配，不崩溃 |
| TD-API-021 | Swagger返回0个API | P2 | 后端服务异常 | 页面不崩溃，合理展示 |

## 已知坑位

| # | 坑位 | 影响 |
|---|------|------|
| 1 | iframe渲染时机不稳定 | 全量回归时 get_api_count=0 |
| 2 | 跨域限制 | iframe内元素可能受同源策略限制 |
| 3 | 非纯Swagger UI | 混合Element Plus表格 |

## 已有自动化覆盖

| 文件 | 状态 |
|------|:--:|
| PO | `page/system_page/ApiManagePage.py` ✅ (~140行) |
| 测试 | `script/system/test_api_management.py` ✅ (4 cases, 3P/0F/1S) |
