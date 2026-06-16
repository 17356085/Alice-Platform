# Skill: excel-exporter

## 目标
将 TEST_CASES.md 中的测试用例与 Allure JSON 执行结果**合并**，生成一份综合的带格式中文 Excel 文件（.xlsx）。这是 SOP 最终交付物。

## 输入
- **主场景 — 场景 C（综合 Excel）⭐**：`TEST_CASES.md` + `allure-results/*-result.json`，合并输出一份 Excel
- 场景 A（仅用例表）：`TEST_CASES.md` — 执行前的用例清单，中间过程用
- 场景 B（仅执行结果）：`allure-results/*-result.json` — 仅结果统计，参考用
- 模块名称、页面名称

## 输出
- **场景 C**：`测试报告-{模块}-{日期}.xlsx` — ★ 最终交付物，含用例设计+执行结果合并
- 场景 A：`测试用例-{模块}-{页面}.xlsx`
- 场景 B：`执行结果-{模块}-{时间}.xlsx`
- 所有 .xlsx 输出到 `reports/` 目录

## 规则
- 复用项目中已验证的 Excel 样式（来自 `tools/report/generate_*.py`）
- 微软雅黑字体、蓝色表头(#4472C4)、冻结首行、自适应列宽
- 优先级配色：P0=红色(#FFC7CE) / P1=黄色(#FFEB9C) / P2=绿色(#C6EFCE)
- 执行结果配色：PASS=绿色(#C6EFCE) / FAIL=红色(#FFC7CE) / SKIP=黄色(#FFEB9C) / XPASS=蓝色(#D9E2F3)
- 文件名含模块名+日期，中文命名

## 依赖
- Python `openpyxl` 库（已在 `requirements.txt` 中）
- 现有 Excel 样式参考：
  - `ZJSN_Test-master526/tools/report/generate_customer_testcase_excel.py`
  - `ZJSN_Test-master526/tools/report/generate_excel.py`
  - `ZJSN_Test-master526/reports/generate_excel.py`

## 边界
- 本 Skill 只生成 Excel 文件，不修改 TEST_CASES.md 或 Allure 源文件
- 不处理图片附件
- 不生成 Allure HTML 报告（那是 pytest-allure 的职责）

---

## Prompt 模板

### 场景 A：TEST_CASES.md → 测试用例 Excel

```text
将以下 TEST_CASES.md 中的测试用例表格转换为格式化的 Excel 文件。

## 输入
- 模块名称：{{设备管理}}
- 页面名称：{{设备报警配置}}
- TEST_CASES.md：
{{粘贴 TEST_CASES.md 中的用例表格（含所有行）}}

## 任务
生成 Python 脚本 `reports/generate_{{module}}_testcase_excel.py`：

```python
"""生成 {{模块}}-{{页面}} 测试用例 Excel"""
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

# ── 输出路径 ──
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'reports')
os.makedirs(OUT_DIR, exist_ok=True)

# ── 样式（复用项目已验证配色） ──
HDR_FONT = Font(name='微软雅黑', size=11, bold=True, color='FFFFFF')
HDR_FILL = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
TITLE_FONT = Font(name='微软雅黑', size=14, bold=True, color='1F4E79')
BODY_FONT = Font(name='微软雅黑', size=10)
WRAP = Alignment(wrap_text=True, vertical='center', horizontal='left')
CENTER = Alignment(wrap_text=True, vertical='center', horizontal='center')
BORDER = Border(
    left=Side('thin'), right=Side('thin'),
    top=Side('thin'), bottom=Side('thin'),
)
P0_FILL = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
P1_FILL = PatternFill(start_color='FFEB9C', end_color='FFEB9C', fill_type='solid')
P2_FILL = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
P_FILLS = {'P0': P0_FILL, 'P1': P1_FILL, 'P2': P2_FILL}
AUTO_FILL = PatternFill(start_color='D9E2F3', end_color='D9E2F3', fill_type='solid')
MANUAL_FILL = PatternFill(start_color='F2F2F2', end_color='F2F2F2', fill_type='solid')

wb = openpyxl.Workbook()
ws = wb.active
ws.title = '{{页面}}-测试用例'

# ── 标题行 ──
ws.merge_cells('A1:J1')
ws['A1'].value = '{{模块}} — {{页面}} 测试用例表'
ws['A1'].font = TITLE_FONT
ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
ws.row_dimensions[1].height = 30

# ── 信息行 ──
ws.merge_cells('A2:J2')
ws['A2'].value = f'生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")} | 来源: TEST_CASES.md'
ws['A2'].font = Font(name='微软雅黑', size=9, color='666666')
ws['A2'].alignment = Alignment(horizontal='center')

# ── 表头 ──
HEADERS = ['用例编号', '用例标题', '所属模块', '优先级', '前置条件', '测试步骤', '测试数据', '预期结果', '自动化', '备注']
for c, h in enumerate(HEADERS, 1):
    cell = ws.cell(row=4, column=c, value=h)
    cell.font = HDR_FONT
    cell.fill = HDR_FILL
    cell.alignment = CENTER
    cell.border = BORDER
ws.row_dimensions[4].height = 22

# ── 数据行 ──
CASES = [
    {{从 TEST_CASES.md 逐行提取的数据，格式为 list of dicts 或 list of lists}}
]

for i, case in enumerate(CASES):
    row = 5 + i
    for c, val in enumerate(case, 1):
        cell = ws.cell(row=row, column=c, value=val)
        cell.font = BODY_FONT
        cell.alignment = WRAP if c in (5, 6, 8) else CENTER
        cell.border = BORDER
        # 优先级配色
        if c == 4:  # 优先级列
            cell.fill = P_FILLS.get(str(val).strip(), None)
        # 自动化状态配色
        if c == 9:  # 自动化列
            v = str(val).strip()
            if v in ('✅', '已自动化'):
                cell.fill = AUTO_FILL
            elif v in ('❌', '不适合'):
                cell.fill = MANUAL_FILL
    ws.row_dimensions[row].height = max(40, 15 * str(case).count('\\n'))

# ── 列宽 ──
COL_WIDTHS = [18, 30, 12, 8, 24, 40, 20, 36, 10, 16]
for i, w in enumerate(COL_WIDTHS, 1):
    ws.column_dimensions[get_column_letter(i)].width = w

# ── 冻结首行 ──
ws.freeze_panes = 'A5'

# ── 保存 ──
filename = f'测试用例-{{module}}-{{page}}-{datetime.now().strftime("%Y%m%d")}.xlsx'
path = os.path.join(OUT_DIR, filename)
wb.save(path)
print(f'✅ 已生成: {path}')
```

## 注意
- 从 TEST_CASES.md 的 Markdown 表格中逐行提取数据填入 `CASES` 列表
- 测试步骤和预期结果中的换行符 `\n` 会触发 Excel 自动换行
- 实际结果列（场景B）留空，执行后手动填入
```

### 场景 B：Allure JSON → 执行结果 Excel

```text
将 Allure 执行结果 JSON 转换为带 PASS/FAIL 配色的 Excel 报告。

## 输入
- allure-results/ 目录下的 *-result.json 文件
- {{粘贴 3-5 个典型 result.json 内容}}

## 任务
生成 Python 脚本 `reports/generate_execution_report.py`：

```python
"""生成自动化执行结果 Excel 报告"""
import os, json, glob
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ── 样式 ──
HDR_FONT = Font(name='微软雅黑', size=11, bold=True, color='FFFFFF')
HDR_FILL = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
BODY_FONT = Font(name='微软雅黑', size=10)
WRAP = Alignment(wrap_text=True, vertical='center', horizontal='left')
CENTER = Alignment(wrap_text=True, vertical='center', horizontal='center')
BORDER = Border(left=Side('thin'), right=Side('thin'), top=Side('thin'), bottom=Side('thin'))
PASS_FILL = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
FAIL_FILL = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
SKIP_FILL = PatternFill(start_color='FFEB9C', end_color='FFEB9C', fill_type='solid')
BROKEN_FILL = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')

STATUS_FILLS = {
    'passed': PASS_FILL,
    'failed': FAIL_FILL,
    'skipped': SKIP_FILL,
    'broken': BROKEN_FILL,
}
STATUS_LABELS = {
    'passed': 'PASS',
    'failed': 'FAIL',
    'skipped': 'SKIP',
    'broken': 'BROKEN',
}

wb = openpyxl.Workbook()

# ── 汇总 Sheet ──
ws_summary = wb.active
ws_summary.title = '执行摘要'
SUMMARY_HEADERS = ['指标', '数值']
for c, h in enumerate(SUMMARY_HEADERS, 1):
    cell = ws_summary.cell(row=1, column=c, value=h)
    cell.font = HDR_FONT; cell.fill = HDR_FILL; cell.alignment = CENTER; cell.border = BORDER

summary_data = [
    ['执行时间', datetime.now().strftime('%Y-%m-%d %H:%M')],
    ['总用例数', {{N}}],
    ['通过', {{N}}],
    ['失败', {{N}}],
    ['跳过', {{N}}],
    ['通过率', '{{XX}}%'],
    ['总耗时', '{{X}} min'],
]
for i, (k, v) in enumerate(summary_data, 2):
    ws_summary.cell(row=i, column=1, value=k).font = BODY_FONT
    ws_summary.cell(row=i, column=1).border = BORDER
    ws_summary.cell(row=i, column=2, value=v).font = Font(name='微软雅黑', size=10, bold=True)
    ws_summary.cell(row=i, column=2).border = BORDER
    ws_summary.cell(row=i, column=2).alignment = CENTER

# ── 按模块分 Sheet ──
for module_name in ['{{equipment}}', '{{system}}', '{{sales}}']:
    ws = wb.create_sheet(title=module_name)
    HEADERS = ['用例名称', '状态', '耗时(s)', '错误信息', '模块', 'Allure标签']
    for c, h in enumerate(HEADERS, 1):
        cell = ws.cell(row=1, column=c, value=h)
        cell.font = HDR_FONT; cell.fill = HDR_FILL; cell.alignment = CENTER; cell.border = BORDER
    ws.row_dimensions[1].height = 22

    # 数据行
    row = 2
    for result in {{该模块的 result JSON 列表}}:
        status = result.get('status', 'unknown')
        cells_data = [
            result.get('name', ''),
            STATUS_LABELS.get(status, status.upper()),
            round((result.get('stop', 0) - result.get('start', 0)) / 1000, 1) if result.get('stop') and result.get('start') else '',
            result.get('statusDetails', {}).get('message', '')[:200],
            module_name,
            ', '.join([l['value'] for l in result.get('labels', []) if l.get('name') in ('epic', 'feature', 'story', 'severity')]),
        ]
        for c, val in enumerate(cells_data, 1):
            cell = ws.cell(row=row, column=c, value=val)
            cell.font = BODY_FONT
            cell.alignment = WRAP if c in (1, 4) else CENTER
            cell.border = BORDER
        # 状态配色
        status_cell = ws.cell(row=row, column=2)
        status_cell.fill = STATUS_FILLS.get(status)
        ws.row_dimensions[row].height = 28
        row += 1

    # 列宽
    widths = [36, 8, 10, 50, 14, 30]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = 'A2'

# ── 保存 ──
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'reports')
os.makedirs(OUT_DIR, exist_ok=True)
filename = f'执行结果-{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
path = os.path.join(OUT_DIR, filename)
wb.save(path)
print(f'✅ 已生成: {path}')
```

## 注意
- 从 Allure result JSON 中提取 status/name/start/stop/statusDetails.message/labels 字段
- 按 epic/feature label 自动分组到不同 Sheet
- 汇总 Sheet 含通过率百分比和总耗时
```

---

### 场景 C：TEST_CASES.md + Allure JSON → 综合测试报告 Excel ★ 主场景

```text
将 TEST_CASES.md 中的测试用例与 Allure 执行结果合并为一份综合 Excel。这是 SOP 最终交付物。

## 输入
- 模块名称：{{设备管理}}
- 页面名称：{{设备报警配置}}
- TEST_CASES.md 路径：{{governance/context/projects/web-automation/modules/equipment/pages/alarm-config/TEST_CASES.md}}
- allure-results/ 目录：{{ZJSN_Test-master526/allure-results/}}

## 任务
生成 Python 脚本 `reports/generate_{{module}}_report.py`，执行后输出综合 Excel。

### 数据来源
1. 读取 TEST_CASES.md 中的 Markdown 表格，逐行提取所有用例
2. 读取 allure-results/*-result.json，按 name 匹配用例
3. 匹对逻辑：用例名称模糊匹配（含括号/编号差异容忍）

### Excel 结构（单模块一个 Sheet）

```
Sheet: {{模块名}}

行1: 标题行（合并单元格）— "{{模块}} 测试报告"
行2: 信息行 — "生成时间: YYYY-MM-DD HH:MM | 模块: {{module}} | 总用例: N | 通过: N | 失败: N | 跳过: N | 通过率: XX%"
行3: 空行
行4: 表头

表头列:
| A: 用例编号 | B: 用例标题 | C: 优先级 | D: 前置条件 | E: 测试步骤 | F: 测试数据 | G: 预期结果 | H: 实际状态 | I: 耗时(s) | J: 错误信息 | K: 自动化标记 |

数据行（从行5开始）:
- A~G 列 ← 来自 TEST_CASES.md 的用例行
- H 列 ← 来自 Allure JSON 的 status (PASS/FAIL/SKIP/BROKEN)，未匹配到填 "未执行"
- I 列 ← Allure stop - start (秒)
- J 列 ← Allure statusDetails.message（截断200字），PASS 留空
- K 列 ← TEST_CASES.md 原始 自动化 列（✅/🔄/❌）
```

### Excel 格式
```python
"""生成 {{模块}} 综合测试报告 Excel — SOP 最终交付物"""
import os, json, glob, re
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ── 路径 ──
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO_ROOT, 'reports')
os.makedirs(OUT_DIR, exist_ok=True)

# ── 样式（复用项目已验证配色） ──
HDR_FONT = Font(name='微软雅黑', size=11, bold=True, color='FFFFFF')
HDR_FILL = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
TITLE_FONT = Font(name='微软雅黑', size=14, bold=True, color='1F4E79')
INFO_FONT = Font(name='微软雅黑', size=9, color='666666')
BODY_FONT = Font(name='微软雅黑', size=10)
BOLD_FONT = Font(name='微软雅黑', size=10, bold=True)
WRAP = Alignment(wrap_text=True, vertical='top', horizontal='left')
CENTER = Alignment(wrap_text=True, vertical='center', horizontal='center')
BORDER = Border(left=Side('thin'), right=Side('thin'), top=Side('thin'), bottom=Side('thin'))

# 优先级配色
P0_FILL = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
P1_FILL = PatternFill(start_color='FFEB9C', end_color='FFEB9C', fill_type='solid')
P2_FILL = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
P_FILLS = {'P0': P0_FILL, 'P1': P1_FILL, 'P2': P2_FILL}

# 执行状态配色
PASS_FILL = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
FAIL_FILL = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
SKIP_FILL = PatternFill(start_color='FFEB9C', end_color='FFEB9C', fill_type='solid')
UNEXEC_FILL = PatternFill(start_color='F2F2F2', end_color='F2F2F2', fill_type='solid')
STATUS_FILLS = {'PASS': PASS_FILL, 'FAIL': FAIL_FILL, 'SKIP': SKIP_FILL, 'BROKEN': PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')}

# 自动化标记配色
AUTO_FILL = PatternFill(start_color='D9E2F3', end_color='D9E2F3', fill_type='solid')    # ✅ 已自动化
MANUAL_FILL = PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid')  # ❌ 不适合

# ── 数据加载 ──
# 从 TEST_CASES.md 解析用例（Markdown 表格 → list of dicts）
def parse_test_cases_md(md_path):
    """解析 TEST_CASES.md 中的 Markdown 表格，返回用例列表"""
    # Read file, find markdown table, parse rows
    cases = []
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # ... parse logic: find | 开头的行，跳过表头分隔线
    # 返回 [{id, title, priority, precondition, steps, data, expected, auto}]
    return cases

# 从 Allure JSON 提取执行结果（name → {status, duration, message}）
def parse_allure_results(allure_dir):
    """解析 allure-results/*-result.json，返回 {case_name: {status, duration, message}}"""
    results = {}
    for f in glob.glob(os.path.join(allure_dir, '*-result.json')):
        with open(f, 'r', encoding='utf-8') as fh:
            r = json.load(fh)
            name = r.get('name', '')
            # 清理括号后缀便于匹配： "验证搜索(TC-EQ-AC-001)" → "验证搜索"
            clean_name = re.sub(r'\([^)]*\)', '', name).strip()
            duration = round((r.get('stop', 0) - r.get('start', 0)) / 1000, 1) if r.get('stop') and r.get('start') else ''
            results[name] = {
                'status': r.get('status', 'unknown').upper(),
                'duration': duration,
                'message': (r.get('statusDetails', {}) or {}).get('message', '')[:200],
            }
    return results

# 匹配逻辑：TEST_CASES 中的用例标题与 Allure 中的 name 做模糊匹配
def match_case_to_result(case, allure_results):
    title = case['title'].strip()
    # 精确匹配
    if title in allure_results:
        return allure_results[title]
    # 模糊匹配：忽略括号后缀
    clean = re.sub(r'\([^)]*\)', '', title).strip()
    for name, result in allure_results.items():
        if re.sub(r'\([^)]*\)', '', name).strip() == clean:
            return result
    # 子串匹配
    for name, result in allure_results.items():
        if clean in name or name in clean:
            return result
    return None

# ── 生成 Excel ──
wb = openpyxl.Workbook()
ws = wb.active
ws.title = '{{模块名}}'

# 标题行
ws.merge_cells('A1:K1')
ws['A1'].value = '{{模块}} — 测试报告'
ws['A1'].font = TITLE_FONT
ws['A1'].alignment = Alignment(horizontal='center', vertical='center')

# 信息行
# 先计算统计
cases = parse_test_cases_md('{{TEST_CASES_PATH}}')
allure_results = parse_allure_results('{{ALLURE_DIR}}')
total = len(cases)
passed = sum(1 for c in cases if match_case_to_result(c, allure_results) and match_case_to_result(c, allure_results)['status'] == 'PASSED')
failed = sum(1 for c in cases if match_case_to_result(c, allure_results) and match_case_to_result(c, allure_results)['status'] == 'FAILED')
skipped = sum(1 for c in cases if match_case_to_result(c, allure_results) and match_case_to_result(c, allure_results)['status'] == 'SKIPPED')
unexec = total - passed - failed - skipped
pass_rate = f'{passed/(total-skipped)*100:.1f}%' if (total-skipped) > 0 else 'N/A'

ws.merge_cells('A2:K2')
ws['A2'].value = f'生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")} | 模块: {{模块}} | 总用例: {total} | 通过: {passed} | 失败: {failed} | 跳过: {skipped} | 未执行: {unexec} | 通过率: {pass_rate}'
ws['A2'].font = INFO_FONT
ws['A2'].alignment = Alignment(horizontal='center')

# 表头
HEADERS = ['用例编号', '用例标题', '优先级', '前置条件', '测试步骤', '测试数据', '预期结果', '实际状态', '耗时(s)', '错误信息', '自动化']
for c, h in enumerate(HEADERS, 1):
    cell = ws.cell(row=4, column=c, value=h)
    cell.font = HDR_FONT
    cell.fill = HDR_FILL
    cell.alignment = CENTER
    cell.border = BORDER
ws.row_dimensions[4].height = 22

# 数据行
for i, case in enumerate(cases):
    row = 5 + i
    result = match_case_to_result(case, allure_results)
    status = result['status'] if result else '未执行'
    
    # A~G: 来自 TEST_CASES
    values = [
        case.get('id', ''),
        case.get('title', ''),
        case.get('priority', ''),
        case.get('precondition', ''),
        case.get('steps', ''),
        case.get('data', ''),
        case.get('expected', ''),
        status,                                    # H: 来自 Allure
        result['duration'] if result else '',       # I: 耗时
        result['message'] if result and status == 'FAILED' else '',  # J: 仅失败时填入
        case.get('auto', ''),                       # K: 自动化标记
    ]
    
    for c, val in enumerate(values, 1):
        cell = ws.cell(row=row, column=c, value=val)
        cell.font = BODY_FONT
        cell.alignment = WRAP if c in (4, 5, 6, 7, 10) else CENTER
        cell.border = BORDER
    
    # 优先级列(C)配色
    priority_cell = ws.cell(row=row, column=3)
    priority_cell.fill = P_FILLS.get(str(values[2]).strip(), None)
    
    # 状态列(H)配色
    status_cell = ws.cell(row=row, column=8)
    status_cell.fill = STATUS_FILLS.get(status, UNEXEC_FILL)
    status_cell.font = BOLD_FONT if status == 'FAILED' else BODY_FONT
    
    # 自动化列(K)配色
    auto_cell = ws.cell(row=row, column=11)
    auto_val = str(values[10]).strip()
    if auto_val in ('✅', '已自动化'):
        auto_cell.fill = AUTO_FILL
    elif auto_val in ('❌', '不适合'):
        auto_cell.fill = MANUAL_FILL
    
    ws.row_dimensions[row].height = max(32, 15 * str(case.get('steps', '')).count('\n'))

# 列宽
COL_WIDTHS = {'A': 18, 'B': 28, 'C': 8, 'D': 20, 'E': 38, 'F': 16, 'G': 32, 'H': 10, 'I': 10, 'J': 36, 'K': 10}
for col_letter, width in COL_WIDTHS.items():
    ws.column_dimensions[col_letter].width = width

# 冻结
ws.freeze_panes = 'A5'

# ── 保存 ──
filename = f'测试报告-{{module}}-{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
path = os.path.join(OUT_DIR, filename)
wb.save(path)
print(f'[DONE] 综合测试报告已生成: {path}')
print(f'[STATS] 总={total} 通过={passed} 失败={failed} 跳过={skipped} 未执行={unexec} 通过率={pass_rate}')
```

## 注意
- **这是 SOP 最终交付物**。SOP 跑完后必须生成此 Excel。
- 用例与结果匹配时，名称模糊匹配容忍括号后缀差异（如"验证搜索" vs "验证搜索(TC-EQ-AC-001)"）
- 未匹配到的用例状态显示"未执行"（灰底），便于识别未覆盖用例
- 错误信息截断至 200 字符
- 文件名格式：`测试报告-{模块}-YYYYMMDD_HHMM.xlsx`

---

## 检查清单

### 场景 C（主场景 — SOP 必用）⭐
- [ ] TEST_CASES.md 所有行已完整提取
- [ ] Allure JSON 所有文件已读取
- [ ] 每条用例按名称模糊匹配到了执行结果（或标记为"未执行"）
- [ ] 实际状态列：PASS=绿 / FAIL=红 / SKIP=黄 / 未执行=灰
- [ ] 优先级列：P0=红 / P1=黄 / P2=绿
- [ ] 信息行含完整统计（总/通过/失败/跳过/未执行/通过率）
- [ ] 冻结首行(A5) + 列宽合适
- [ ] 文件名：`测试报告-{模块}-YYYYMMDD_HHMM.xlsx`
- [ ] 脚本保存为 `reports/generate_{module}_report.py`（可复用）

### 场景 A（仅用例表 — 执行前用）
- [ ] TEST_CASES.md 的所有行已完整提取
- [ ] P0/P1/P2 配色正确
- [ ] 自动化状态列有区分颜色
- [ ] 冻结首行 + 列宽自适应
- [ ] 文件名含模块名和日期

### 场景 B（仅执行结果 — 参考用）
- [ ] 汇总 Sheet 的通过率计算正确
- [ ] 每个模块独立 Sheet
- [ ] PASS=绿 / FAIL=红 / SKIP=黄 配色正确
- [ ] 错误信息截断至 200 字符
- [ ] 冻结首行

## 产出物
→ `reports/测试报告-{模块}-YYYYMMDD_HHMM.xlsx` ★ SOP 最终交付物
→ `reports/测试用例-{模块}-{页面}-{日期}.xlsx`（中间过程，场景 A）
→ `reports/执行结果-{日期}_{时间}.xlsx`（中间过程，场景 B）
→ 参考实现：
  - `ZJSN_Test-master526/tools/report/generate_customer_testcase_excel.py`
  - `ZJSN_Test-master526/tools/report/generate_excel.py`
