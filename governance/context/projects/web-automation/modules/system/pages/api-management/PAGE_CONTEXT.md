# PAGE_CONTEXT — system-management / api-management

> 最后诊断：2026-06-12

## 页面信息

| 属性 | 值 |
| --- | --- |
| 页面名称 | 接口管理 |
| 路由 | `#/system/api` |
| 所属模块 | 系统管理 |
| 页面类型 | Swagger UI 嵌入页（iframe） |
| Page Object | [ApiManagePage.py](ZJSN_Test-master526/page/system_page/ApiManagePage.py) (~140行) |
| 测试脚本 | [test_api_management.py](ZJSN_Test-master526/script/system/test_api_management.py) (4 cases) |
| 测试结果 | 3P/0F/1S standalone; 1P/1F/2S full-regression |
| 自动化状态 | ⚠️ 基本完成，Swagger iframe 渲染时机不稳定 |

## 页面定位

接口管理页面嵌入 **Swagger UI** 用于展示和测试后端 API。页面通过 iframe 加载 Swagger，显示所有 API 分组和接口详情。

## 页面关键功能

### 页面加载检测

| 级别 | 检测方式 | 说明 |
| :---: | --- | --- |
| 1 | Swagger 标志元素 | `.swagger-ui`, `.topbar` |
| 2 | el-table | Element Plus 表格 |
| 3 | Table Rows | 通用表格行检测 |
| 4 | 容器文本 > 20字符 | 最终降级 |

### Swagger UI 结构（iframe 内）

| 区域 | 内容 | 说明 |
| --- | --- | --- |
| 顶部栏 | API 标题 + 版本 | Swagger topbar |
| API 分组 | tag-based 分组列表 | 如 system-controller |
| 接口列表 | 每个分组的 HTTP 接口 | GET/POST/PUT/DELETE |
| 接口详情 | 展开后的参数/响应 | Try it out 功能 |

## 关键定位策略

| 操作 | 方法 | 策略 |
| --- | --- | --- |
| 页面加载检测 | `is_page_loaded()` | 4级检测（Swagger→el-table→TableRows→容器文本） |
| 获取API分组 | `get_api_groups()` | iframe内查找 Swagger tag 元素 |
| API搜索 | `search_api(keyword)` | Swagger 内置搜索或 filter |

## 已知坑位

1. **非 Swagger UI 页面**：最初假设为 Swagger UI，实际页面可能混合 Element Plus 表格 + Swagger iframe
2. **iframe 渲染时机**：全量回归时 Swagger 可能未加载完成，`get_api_count=0`
3. **跨域限制**：iframe 内元素可能受同源策略限制
4. **页面重写**：PO 已从 Swagger 专属重写为 4 级检测的通用页面加载检测

## 与其他页面的关系

- API 接口 → 被前端各页面调用
- Swagger 分组 → 对应后端 Controller 层
