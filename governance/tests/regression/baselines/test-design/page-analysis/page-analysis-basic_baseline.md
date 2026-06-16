# 页面分析请求 — 缺少必要输入

## ⚠️ 当前无法完成完整分析

根据 `page-analysis` 技能规范，分析需要以下输入之一：

1. **页面截图**（1-3张关键区域截图）
2. **HTML 源码**（页面核心区域的 DOM 结构）
3. **已存在的 PAGE_CONTEXT.md**（如有）用于定位器增强

当前仅提供了 `equipment/alarm-config` 页面路径，**缺少上述三种输入中的任何一种**。

---

## 请提供以下信息之一

| 优先级 | 提供内容 | 格式要求 |
|--------|----------|----------|
| P0 | **页面截图** | 搜索区 + 表格区 + 弹窗（如有）各一张截图的URL或附件 |
| P1 | **HTML 源码** | 页面关键区域（搜索表单、表格列、弹窗）的 HTML 片段 |
| P2 | **页面URL** \+ 截图 | 运行中页面的 URL + 整页截图，可远程查看 |

---

## 参考占位（基于页面名称推测）

> 📌 以下为基于典型 Element Plus 后台管理页面的**推测结构**，**不构成正式输出**，仅作为沟通参考。

### 推测元素清单

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| search_deviceCode | 设备编码查询 | el-input | 搜索区 | 模糊搜索 |
| search_alarmType | 报警类型筛选 | el-select | 搜索区 | 下拉单选 |
| btn_search | 查询按钮 | el-button | 搜索区 | `@click` 触发表格刷新 |
| btn_reset | 重置按钮 | el-button | 搜索区 | 清空搜索条件 |
| btn_add | 新增配置 | el-button | 表格右上 | 弹窗创建 |
| table_alarmConfig | 报警配置列表 | el-table | 主内容区 | 需确认列数 |
| col_deviceCode | 设备编码列 | — | 表格列 | 文本类型 |
| col_alarmType | 报警类型列 | — | 表格列 | 文本/Tag |
| col_enable | 启用状态列 | — | 表格列 | el-tag / el-switch |
| col_actions | 操作列 | — | 表格列 | 编辑/删除/切换状态 |
| pagination | 分页组件 | el-pagination | 表格底部 | 含每页条数切换 |
| dialog_config | 配置弹窗 | el-dialog | Teleport 渲染 | 新增/编辑共用 |
| dialog_form_code | 设备编码字段 | el-input | 弹窗内 | 必填 |
| dialog_form_type | 报警类型字段 | el-select | 弹窗内 | 必选 |
| dialog_form_enable | 启用开关 | el-switch | 弹窗内 | 默认开 |
| dialog_save | 保存按钮 | el-button (primary) | 弹窗底部 | 确认提交 |
| dialog_cancel | 取消按钮 | el-button | 弹窗底部 | 关闭弹窗 |

---

## 下一步

请提供 **截图或 HTML 源码**，我将立即完成：

1. ✅ 精确到每个控件的 **PAGE_CONTEXT.md**
2. ✅ 含 A/B/C 三级定位器的 **PAGE_ELEMENT_POSITION.md**
3. ✅ 自动生成 **PAGE_INTERFACE.yaml**（供 automation-agent 消费）