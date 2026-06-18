# Skill: code-review/security-scanner

### 目标
扫描常见安全漏洞：SQL 注入、XSS、敏感数据暴露、缺失认证、不安全依赖。

### 输入
- 后端 router/schema 代码
- 前端组件代码
- package.json / requirements.txt

### 输出
- `SECURITY_REPORT.md`

### 规则
- 后端：检查 raw SQL、密码明文、缺失 @Depends(get_current_user)、CORS 配置
- 前端：检查 v-html 无 XSS 防护、硬编码 token、env 变量泄露
- 依赖：检查已知漏洞（npm audit / pip audit）

### 依赖
- 代码已生成

---

## Prompt 模板

```text
你是一个安全审计专家。扫描以下代码的安全漏洞。

## 代码
```{{LANGUAGE}}
{{SOURCE_CODE}}
```

## 严重程度
- Critical: 可导致数据泄露或系统入侵
- High: 可导致权限绕过
- Medium: 最佳实践偏离
- Low: 信息泄露

## 输出
每个漏洞: 严重程度 / 文件:行号 / 类型 / 描述 / 修复建议
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | code-review | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->