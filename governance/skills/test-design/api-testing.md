# Skill: api-testing

## 目标
从 API 文档或 Network 抓包出发，设计接口测试方案并生成自动化脚本。

## 输入
- API 文档 / 浏览器 Network 抓包
- PAGE_CONTEXT.md（接口依赖关系）
- 已有自动化架构（requests 封装、Token 处理）

## 输出
- API_TEST_DESIGN.md
- 接口测试脚本（可选，pytest + requests）

## 规则
- 覆盖 5 个维度：参数边界、Token 校验、权限校验、异常测试、安全测试
- 参数边界必须包含：必填缺失、类型错误、超长、特殊字符、分页边界
- Token 校验：无 Token / 过期 Token / 伪造 Token
- 权限校验：低权限调用高权限接口、跨租户访问
- 安全测试：SQL 注入、XSS、敏感信息泄露

## 依赖
- workflows/sop-summary.md (§ Phase 6)

## 边界
- 本 Skill 不覆盖 UI 层面自动化
- 不覆盖性能测试

---

## Prompt 模板

```text
基于以下接口信息，设计接口测试方案。

## 接口信息
{{粘贴接口列表（从浏览器Network面板或API文档获取）}}

示例格式：
| 接口 | 方法 | URL | 参数 | 触发时机 |
|------|------|-----|------|---------|
| 获取报警列表 | GET | /api/alarm/list | page, size, keyword | 页面加载/搜索 |
| 新增报警 | POST | /api/alarm/add | {name, type, threshold} | 弹窗确认 |
| 删除报警 | DELETE | /api/alarm/{id} | id | 删除确认 |

## 任务
输出 API_TEST_DESIGN.md，覆盖5个维度：

1. **参数边界测试**：必填缺失、类型错误、超长/特殊字符、分页边界(page=0, size=10000)
2. **Token校验**：无Token→401、过期Token→401、伪造Token→401
3. **权限校验**：低权限调用高权限接口、跨租户数据访问
4. **异常测试**：不存在的资源ID→404、重复提交幂等性、并发请求
5. **安全测试**：SQL注入字符、XSS字符、响应中敏感信息泄露

## 自动化实现（可选）
```python
import requests
import pytest

class TestAlarmAPI:
    BASE_URL = "http://8.136.215.171:8081/api"
    
    def test_get_list_unauthorized(self):
        """无Token请求应返回401"""
        resp = requests.get(f"{self.BASE_URL}/alarm/list")
        assert resp.status_code == 401
```
```

## 检查清单
- [ ] 每个接口至少1个正向用例+1个异常用例
- [ ] 5个维度全覆盖（参数边界/Token/权限/异常/安全）
- [ ] 分页边界覆盖 page=0, page=-1, size=0, size=10000
- [ ] Token校验3种场景（无/过期/伪造）
- [ ] 安全测试含SQL注入和XSS字符
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **0.1-exp** | experimental | test-design | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->