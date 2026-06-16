# BUG_ANALYSIS — unit_management 页面前3条失败

> 日期: 2026-06-11 | 执行: equipment 全模块 | 模式: 批量(3失败)

## 执行摘要

equipment 全模块测试中，unit_management 页面 UN-01/02/03 连续失败（3条），根因确认为 **L2: Vue 自定义组件渲染等待不足**。alarm_config 10 passed 对比确认此问题仅影响使用自定义 stat-card 组件的页面。

## 失败分类

| 类别 | 数量 | 用例 |
|------|------|------|
| 等待不足(自定义组件) | 3 | UN-01, UN-02, UN-03 |

## 5层递进排查

### [L1] 定位器失效？
结论: ✅排除。STAT_CARD = `(By.CSS_SELECTOR, '.stat-card')` 定位器本身正确——`find_all` 可执行但返回数量不足或文本为空。非 NoSuchElementException。

### [L2] 等待不足？← 根因
结论: ❌确认。3个失败的共同根因。

**证据:**
1. `navigate_to_unit_management()` 调用 `_wait_page_ready()` 仅检查 `document.readyState == 'complete'`
2. 统计卡片为自定义 HTML (`.stat-card` BEM命名)，非 Element Plus el-table
3. `get_stat_card_count()` 直接调用 `find_all()` — **无显式等待卡片渲染**
4. `get_text(STAT_TOTAL)` 在卡片值为空时返回 `""`，导致 `"".isdigit()` → False
5. Vue 渲染时序: DOM ready → Vue mount → data fetch → template render → stat cards appear。`_wait_page_ready()` 在步骤1就返回了，测试在步骤4-5之间执行

**对比:** alarm_config (10 passed) 使用 el-table + BasePage 内置 waiting，无此问题。

### [L3] 数据问题？
结论: ✅排除。测试环境有数据(UN-04 passed, UN-05 passed)。非数据缺失。

### [L4] 环境问题？
结论: ✅排除。同批次其他测试正常通过。非网络/服务器问题。

### [L5] 产品Bug？
结论: ✅排除。手动访问页面正常显示卡片。

## 根因总结

**置信度: 高**

Vue 异步渲染时序导致: `document.readyState complete` (L1等待) 早于 Vue 自定义组件渲染完成 (stat cards出现) → `find_all()` 返回空列表或 `get_text()` 返回空字符串。

## 修复建议

在 `navigate_to_unit_management()` 末尾增加显式等待:

```python
# 修复: navigate_to_unit_management() 末尾增加
def navigate_to_unit_management(self):
    # ... existing navigation code ...
    self._wait_page_ready()
    # 🆕 等待自定义 stat-card 组件渲染完成
    WebDriverWait(self.driver, 10).until(
        EC.presence_of_all_elements_located(self.STAT_CARD)
    )
    self.wait_vue_stable()
```

## 回归范围

| 影响类型 | 范围 | 评估 |
|----------|------|------|
| 直接影响 | UnitManagePage 使用 stat-card 的方法 | 3 个 affected tests |
| 间接影响 | 使用自定义组件的其他页面 (KeyParamPage, CameraManagePage) | 可能同类型问题 |
| 修复后回归 | test_unit_management.py 全部 + 同模式页面 | 建议回归 equipment 全模块 |

## 预防措施

1. **tech-analysis 规则增强**: 识别自定义组件(非el-* 前缀)→强制添加显式等待策略
2. **code-consistency-checker 增强**: 检测 PageObject navigate 方法是否含自定义组件等待
3. **test-patterns 更新**: crud-standard.md 增加"自定义组件等待"陷阱

## 知识沉淀建议

→ 新增 known-issue: `FP-004` (自定义组件渲染时序)  
→ 更新 pitfalls/selenium/stale-element-vue-rerender.md 补充自定义组件场景  
→ 更新 PROJECT_CONTEXT § UI框架差异: 标注 UnitManagePage 的 stat-card 等待要求
