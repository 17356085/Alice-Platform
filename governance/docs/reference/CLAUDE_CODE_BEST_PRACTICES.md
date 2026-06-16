# Claude Code 省钱最佳实践

> 目标: 日消耗从 ~¥6 降至 ~¥3 以下，不影响产出质量。

---

## 红线 (绝对遵守)

| 规则 | 做法 |
|------|------|
| 30 轮封顶 | 感觉到 25+ 轮 → 立即收尾，新开会话 |
| 一次一件事 | 分析→设计→编码→执行→修Bug，每个阶段独立会话 |
| 别让 AI 猜 | 直接告诉它模块名、页面名、要做什么 |

---

## 会话模板

### 开头 (30 字以内把状态说清)

```
模块: equipment, 页面: alarm-config
进度: PAGE_CONTEXT + TEST_CASES 已完成，PageObject 写了一半
目标: 完成 PageObject 定位器 + test_*.py
```

### 结尾 (让下个会话能接上)

```
>> 先到这。状态: alarm-config 的 PageObject 已完成，test_alarm_config.py 生成但还没跑。
>> 下一个会话继续: "equipment/alarm-config，跑 test_alarm_config.py 并修复失败"
```

---

## 工具使用省 Token

| 场景 | ❌ 浪费 | ✅ 节省 | 省多少 |
|------|---------|---------|--------|
| 查定位器 | `Read page/xxxPage.py` (500行) | `Grep "search_input" page/xxxPage.py -C 2` | ~1,800 tok |
| 查测试用例 | `Read TEST_CASES.md` (全文件) | `Grep "P0" TEST_CASES.md -A 3` | ~1,500 tok |
| 看有哪些文件 | 让 AI `ls` 然后逐个 `Read` | 让 AI `Glob "**/test_*.py"` → 只看文件名 | ~5,000 tok |
| 查配置 | `Read .env` (全部) | `Grep "URL\|PASSWORD" .env` | ~500 tok |
| 看错误 | `Read` 整个 allure 报告 | `Grep "status.*failed" allure-results/` | ~3,000 tok |
| 理解代码结构 | `Read` 整个 BasePage | `Read base_page.py:1-50` (只看方法签名) | ~2,000 tok |

---

## 会话拆分节奏

```
周一上午:
  Session 1 (20轮): requirement-agent — 分析模块 + 建模
  Session 2 (20轮): test-design-agent — 2 个页面的分析+用例

周一下午:
  Session 3 (25轮): automation-agent — page 1 的 PageObject + test
  Session 4 (25轮): automation-agent — page 2 的 PageObject + test
  Session 5 (15轮): execution-agent — 跑所有 + 看结果

周二:
  Session 6 (20轮): bug-analysis — 修昨天失败用例
  Session 7 (15轮): report-agent + knowledge-agent — 收尾
```

> 原来 1 个 150 轮会话 ≈ ¥15，拆 7 个 ≈ ¥5

---

## Memory 管理

每两周检查一次 `MEMORY.md`:

```
删: 已完成、已归档、已过时的记录
留: 坑位提醒 (tank 自定义框架)、模式规则 (workflow 工厂代码)
```

---

## 快速参考卡

```
┌─────────────────────────────────────────────┐
│  CLAUDE CODE 省钱口诀                        │
├─────────────────────────────────────────────┤
│  30 轮红线不越界                              │
│  一件事一个会话                               │
│  Grep 代替 Read                              │
│  开头报进度，结尾留状态                         │
│  两周清一次 Memory                            │
└─────────────────────────────────────────────┘
```
