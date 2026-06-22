# Skill: frontend/frontend-lint-checker

### 目标
机械化检查（不调 LLM）：对生成的 Vue 3 前端代码执行 ESLint + TypeScript 编译 + 代码红线 grep 检查。

### 输入
- 生成的 `.vue` / `.ts` 文件路径列表

### 输出
- Lint 检查报告：错误数、警告数、文件级问题清单

### 规则
- 此 Skill 是 **mechanical**（不调 LLM）——直接执行 ESLint 和 tsc 命令
- 红线 grep 检查（类似测试 code-consistency-checker）

### 代码红线（前端 8 条）

| # | ❌ 禁止 | ✅ 必须 | grep 模式 |
|---|---------|--------|-----------|
| 1 | Options API | `<script setup lang="ts">` | `<script setup lang="ts">` |
| 2 | any 类型 | 完整类型注解 | `: any` (禁止) |
| 3 | 无 scoped 样式 | `<style scoped>` | `<style scoped>` |
| 4 | console.log | logger | `console\.(log|warn)\(` (禁止) |
| 5 | Options API defineComponent | `<script setup>` | `defineComponent` (禁止) |
| 6 | 内联 interface | types/ 目录导入 | `interface \w+\s*\{` (模板中禁止) |
| 7 | 硬编码 API URL | 环境变量 | `fetch\(['\"]https?://` (禁止) |
| 8 | sync 数据处理 | async/await | `async\s+\w+\s*\(` (强制) |

### 依赖
- 无前置 LLM Skill

### 边界
- 不修改代码（只报告问题）
- 如果 ESLint 未安装，报告为 [WARNING] 而非失败

### 检查清单
- [ ] ESLint 执行结果已汇总
- [ ] TypeScript 编译结果已汇总
- [ ] 8 条红线逐一 grep 检查
- [ ] 问题清单按文件分组
- [ ] 最终结论: 通过 / 有 N 个问题

---

## Prompt 模板（无 LLM — 纯脚本）

> 此 Skill 不需要 LLM。直接执行以下检查脚本：

```bash
# 1. ESLint
npx eslint {{TARGET_FILES}} --format json 2>&1

# 2. TypeScript
npx vue-tsc --noEmit 2>&1

# 3. 红线 grep
echo "=== 红线检查 ==="
for f in {{TARGET_FILES}}; do
  echo "--- $f ---"
  # 红线1: 必须有 <script setup lang="ts">
  grep -q '<script setup lang="ts">' "$f" || echo "  ❌ 缺失 <script setup lang=\"ts\">"
  # 红线2: 禁止 : any
  grep -n ': any' "$f" && echo "  ❌ 禁止 any 类型"
  # 红线3: 必须有 scoped style
  grep -q '<style scoped>' "$f" || echo "  ❌ 缺失 scoped 样式"
  # 红线4: 禁止 console.log
  grep -n 'console\.\(log\|warn\)(' "$f" && echo "  ❌ 禁止 console.log"
  # 红线5: 禁止 defineComponent
  grep -n 'defineComponent' "$f" && echo "  ❌ 禁止 Options API (defineComponent)"
  # 红线7: 禁止硬编码 URL
  grep -n "fetch(['\"].*https\?://" "$f" && echo "  ❌ 禁止硬编码 API URL"
done
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | frontend | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->