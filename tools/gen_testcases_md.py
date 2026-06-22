"""Generate .md test case files per page to governance/kpi/testcases/equipment/.
Does NOT touch Excel files."""
import os
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MD_OUT = REPO / 'governance' / 'kpi' / 'testcases' / 'equipment'
os.makedirs(MD_OUT, exist_ok=True)
today_str = datetime.now().strftime('%Y-%m-%d')

PAGE_NAMES = {
    'alarm-config': ('设备报警配置', '设备管理'),
    'camera': ('摄像头管理', '设备管理'),
    'key-param': ('关键参数监控', '设备管理'),
    'maintenance': ('设备维保管理', '设备管理'),
}

def mc(cid, title, pri, pre, steps, data, expected, status, dur='', err='', auto=''):
    return (cid, title, pri, pre, steps, data, expected, status, dur, err, auto)

# ═══════════════════════════════════════════════════════
# Data (same as gen_equipment_report.py)
# ═══════════════════════════════════════════════════════
PAGES = {}

# alarm-config
ac = [
    ('功能测试 (5条)', [
        mc('AC-01','页面正常加载','P0','admin登录','导航至报警配置→等待渲染','—','统计卡片≥4张;统计非空','PASS'),
        mc('AC-02','表格表头正确显示','P0','AC-01已通过','获取表头→校验9列','EXPECTED_TABLE_HEADER_SET','表头9列完整','PASS'),
        mc('AC-03','搜索输入框可见','P0','页面已加载','检查搜索输入框','—','可见','PASS'),
        mc('AC-04','新增按钮可见','P0','页面已加载','检查新增配置按钮','—','可见','PASS'),
        mc('AC-05','统计卡片数据一致性','P0','页面已加载','获取4项统计','—','全部≥0','PASS'),
    ]),
    ('搜索筛选测试 (3条)', [
        mc('AC-06','按关键词搜索','P1','有数据','输入关键词→查询','测试报警下-1#','仅匹配记录','PASS'),
        mc('AC-07','搜索无匹配结果','P1','已加载','输入不存在关键词→查询','zzzz_nonexistent','不崩溃','PASS'),
        mc('AC-08','重置搜索条件','P1','已设条件','输入+搜索→重置','—','恢复全量','PASS'),
    ]),
    ('分页测试 (2条) [新]', [
        mc('AC-18','分页组件可见','P1','已加载','检查.el-pagination','—','分页存在','PASS'),
        mc('AC-19','pageSize默认值','P1','已加载','获取pageSize','—','pageSize=10','PASS'),
    ]),
    ('权限测试 (2条) [新]', [
        mc('AC-20','新增按钮权限','P1','admin登录','检查新增按钮','—','可见','PASS'),
        mc('AC-21','行操作按钮权限','P1','表格有数据','检查编辑/删除','—','≥1个','SKIP'),
    ]),
    ('边界值测试 (2条) [新]', [
        mc('AC-22','搜索特殊字符','P1','已加载','输入!@#$%→查询','!@#$%^&*()_+...','不崩溃','PASS'),
        mc('AC-23','搜索超长关键词','P1','已加载','输入256字符→查询','a×256','不崩溃','PASS'),
    ]),
    ('批量操作测试 (1条) [新]', [
        mc('AC-24','批量复选框','P2','已加载','检查checkbox','—','批量检测','PASS'),
    ]),
    ('增删改弹窗测试 (7条)', [
        mc('AC-09','新增-必填字段','P0','admin+权限','新增→填必填→保存','autotest_req_XXXXXX','新增成功','FAIL'),
        mc('AC-10','新增-全部字段','P1','AC-09条件','填全部→保存','name+type+level...','保存成功','FAIL'),
        mc('AC-11','新增-取消','P1','AC-09条件','新增→填后取消','—','不入库','FAIL'),
        mc('AC-12','编辑规则','P1','表格有数据','编辑→修改→保存','—','更新成功','FAIL'),
        mc('AC-13','删除确认弹窗','P1','表格有数据','删除→确认弹窗','—','删除成功','FAIL'),
        mc('AC-16','阈值相等边界','P1','AC-09条件','上下限相等→保存','upper=lower','系统校验','FAIL'),
        mc('AC-17','双击防重复提交','P2','AC-09条件','快速双击保存','—','仅提交一次','FAIL'),
    ]),
    ('其他测试 (2条)', [
        mc('AC-14','查看详情','P1','表格有数据','查看→详情弹窗','—','弹窗显示','SKIP'),
        mc('AC-15','状态切换','P1','表格有数据','切换el-switch','—','切换成功','SKIP'),
    ]),
    ('接口测试 (2条)', [
        mc('AC-API-01','设备列表API','P1','有token','GET /api/equipment/device/list','—','code=200,records>0','PASS'),
        mc('AC-API-02','用户列表API','P1','有token','GET /api/system/user/list','—','code=200,records>0','PASS'),
    ]),
]
PAGES['alarm-config'] = ac

# camera
cm = [
    ('功能测试 (4条)', [
        mc('CAM-01','页面正常加载','P0','admin登录','导航→检查卡片+网格','—','卡片≥4;统计非空','PASS'),
        mc('CAM-02','统计卡片数据','P0','CAM-01通过','获取总数/在线/离线/故障','—','4项≥0','PASS'),
        mc('CAM-03','监控卡片网格','P0','CAM-01通过','检查monitor-cell','—','≥0','PASS'),
        mc('CAM-04','统计标签校验','P0','CAM-01通过','校验4标签','—','标签完整','PASS'),
    ]),
    ('搜索筛选测试 (2条)', [
        mc('CAM-05','关键词搜索','P1','已加载','输入关键词→搜索','罐区','≥0','PASS'),
        mc('CAM-06','搜索无结果','P1','已加载','输入不存在关键词→搜索','zzzz_nonexistent','不崩溃','PASS'),
    ]),
    ('分页测试 (2条)', [
        mc('CAM-07','分页组件','P1','已加载','检查分页','—','total≥0','PASS'),
        mc('CAM-08','翻页测试','P1','数据>1页','下一页→查卡片','—','翻页正常','SKIP'),
    ]),
    ('数据一致性测试 (2条)', [
        mc('CAM-11','统计与分页一致','P1','已加载','对比stat vs page total','—','stat≥page','PASS'),
        mc('CAM-12','搜索后分页重置','P1','数据>1页','翻页→搜索→查页码','—','重置到1','SKIP'),
    ]),
    ('卡片状态测试 (2条)', [
        mc('CAM-09','卡片状态标签','P1','有卡片','获取状态','—','在线/离线/故障','SKIP'),
        mc('CAM-10','卡片操作按钮','P1','有卡片','检查操作区','—','≥1个','SKIP'),
    ]),
    ('弹窗测试 (1条)', [
        mc('CAM-13','查看/预览弹窗','P2','有卡片','点击查看→弹窗','—','弹窗正常','SKIP'),
    ]),
    ('权限测试 (2条) [新]', [
        mc('CAM-14','搜索框权限','P1','admin登录','检查搜索框','—','可见','PASS'),
        mc('CAM-15','卡片操作按钮权限','P1','有卡片','检查按钮区','—','存在','SKIP'),
    ]),
    ('边界值测试 (3条) [新]', [
        mc('CAM-16','搜索特殊字符','P1','已加载','输入!@#$%→搜索','!@#$%^&*()','不崩溃','PASS'),
        mc('CAM-17','搜索超长关键词','P1','已加载','输入256字符→搜索','x×256','不崩溃','PASS'),
        mc('CAM-18','空搜索关键词','P1','已加载','清空→搜索','(空)','正常返回','PASS'),
    ]),
    ('可靠性测试 (1条) [新]', [
        mc('CAM-19','重复搜索稳定性','P2','已加载','3次不同关键词搜索','罐区,消防,(空)','3次正常','PASS'),
    ]),
]
PAGES['camera'] = cm

# key-param
kp = [
    ('功能测试 (3条)', [
        mc('KP-01','页面正常加载','P0','admin登录','导航→查卡片+表格+分页','—','卡片≥2;表格;分页','PASS'),
        mc('KP-02','统计卡片数据','P0','KP-01通过','获取4项统计','—','4项≥0','PASS'),
        mc('KP-03','表头校验','P0','KP-01通过','获取表头','—','≥5列','PASS'),
    ]),
    ('搜索筛选测试 (3条)', [
        mc('KP-04','关键词自动过滤','P0','已加载','输入关键词→刷新','温度/压力/传感器','行数变化','PASS'),
        mc('KP-05','搜索无匹配','P1','已加载','输入不存在关键词','zzzz_nonexistent','行数变化','PASS'),
        mc('KP-06','重置恢复全量','P1','已设搜索','输入→重置','—','total=全量','PASS'),
    ]),
    ('数据校验测试 (1条)', [
        mc('KP-10','状态逻辑一致性','P0','表格有数据','前5条→校验状态vs阈值','—','状态与阈值一致','SKIP'),
    ]),
    ('弹窗测试 (1条)', [
        mc('KP-11','查看参数详情','P1','表格有数据','查看→弹窗','—','弹窗显示','SKIP'),
    ]),
    ('分页测试 (2条) [新]', [
        mc('KP-12','分页组件+总数','P1','已加载','检查分页','—','total≥0','PASS'),
        mc('KP-13','pageSize默认','P1','已加载','获取pageSize','—','=10','PASS'),
    ]),
    ('权限测试 (1条) [新]', [
        mc('KP-14','行操作按钮权限','P1','表格有数据','检查第一行按钮','—','≥1个','PASS'),
    ]),
    ('边界值测试 (2条) [新]', [
        mc('KP-15','搜索特殊字符','P1','已加载','输入!@#$%→刷新','!@#$%^&*()','不崩溃','PASS'),
        mc('KP-16','搜索超长关键词','P1','已加载','输入256字符→刷新','x×256','不崩溃','PASS'),
    ]),
    ('可靠性测试 (1条) [新]', [
        mc('KP-17','重复搜索稳定性','P2','已加载','3次:重置→输入→刷新','温度×3','3次正常','PASS'),
    ]),
]
PAGES['key-param'] = kp

# maintenance
mt = [
    ('功能测试 (4条)', [
        mc('MT-01','页面正常加载','P0','admin登录','导航→检查URL+标题+表头','—','URL含maintenance','PASS'),
        mc('MT-02','表头正确','P0','MT-01通过','检查表头','—','≥9列','PASS'),
        mc('MT-03','表格有数据','P0','有维保计划','获取行数','—','>0','FAIL'),
        mc('MT-04','分页组件','P0','已加载','检查分页','—','total>0','PASS'),
    ]),
    ('搜索筛选测试 (3条)', [
        mc('MT-05','按类型搜索','P1','已加载','选择日检→搜索','日检','正常','PASS'),
        mc('MT-06','按状态搜索','P1','已加载','选择待执行→搜索','待执行','正常','PASS'),
        mc('MT-07','重置恢复全量','P1','已设搜索','选类型+搜索→重置','—','total≥原','PASS'),
    ]),
    ('分页测试 (2条)', [
        mc('MT-08','分页下一页','P1','数据>1页','下一页→查行数','—','有数据','PASS'),
        mc('MT-09','切换每页条数','P1','数据>10','切换20→检查→恢复10','—','行数≤20','PASS'),
    ]),
    ('新增编辑测试 (5条)', [
        mc('MT-10','新增计划-保存','P0','admin+权限','新增→填写→保存','AUTO_测试计划','Toast成功','PASS'),
        mc('MT-11','新增-取消','P0','MT-10条件','新增→填写→取消','—','不入库','PASS'),
        mc('MT-12','新增-必填校验','P1','MT-10条件','新增→直接保存','—','校验提示','PASS'),
        mc('MT-13','编辑-改名称','P0','有数据','编辑→改名→保存→还原','原→原_改→原','更新+还原','PASS'),
        mc('MT-14','编辑-取消','P1','有数据','编辑→改名→取消','—','名称不变','PASS'),
    ]),
    ('生成任务测试 (1条)', [
        mc('MT-15','生成维保任务','P1','有数据','生成任务→Toast','—','有反馈','PASS'),
    ]),
    ('权限测试 (2条)', [
        mc('MT-16','新增按钮(admin)','P1','admin登录','检查新增','—','可见','PASS'),
        mc('MT-17','编辑按钮可见','P1','有编码','检查编辑','—','可见','PASS'),
    ]),
    ('边界值测试 (2条) [新]', [
        mc('MT-18','下拉类型组合','P1','已加载','遍历日检/周检/月检','日检,周检,月检','每种正常','PASS'),
        mc('MT-19','计划名称标识','P1','MT-10条件','新增→timestamp名','AUTOTEST_{ts}','成功','PASS'),
    ]),
    ('批量操作测试 (1条) [新]', [
        mc('MT-20','批量复选框','P1','已加载','检查checkbox','—','检测','PASS'),
    ]),
    ('可靠性测试 (1条) [新]', [
        mc('MT-21','重复搜索稳定性','P2','已加载','3次:重置→选类型→搜索','日检,待执行','3次正常','PASS'),
    ]),
]
PAGES['maintenance'] = mt

# ═══════════════════════════════════════════════════════
# Generate .md files
# ═══════════════════════════════════════════════════════
STATUS_MAP = {'PASS': '✅ PASS', 'FAIL': '❌ FAIL', 'SKIP': '⏭ SKIP'}

for page_slug, sections in PAGES.items():
    page_name, module_name = PAGE_NAMES[page_slug]
    lines = []
    lines.append(f'# {module_name} — {page_name} 测试用例')
    lines.append('')
    lines.append(f'> 模块: equipment | 页面: {page_slug} | 生成日期: {today_str} | SOP Phase 3 产出')
    lines.append('')

    all_cases = []
    for _, cases in sections:
        all_cases.extend(cases)
    total = len(all_cases)
    n_pass = sum(1 for t in all_cases if t[7]=='PASS')
    n_fail = sum(1 for t in all_cases if t[7]=='FAIL')
    n_skip = sum(1 for t in all_cases if t[7]=='SKIP')
    p0 = sum(1 for t in all_cases if t[2]=='P0')
    p1 = sum(1 for t in all_cases if t[2]=='P1')
    p2 = sum(1 for t in all_cases if t[2]=='P2')

    lines.append(f'| 指标 | 数值 |')
    lines.append(f'|------|:---:|')
    lines.append(f'| 用例总数 | {total} |')
    lines.append(f'| P0 / P1 / P2 | {p0} / {p1} / {p2} |')
    lines.append(f'| 通过 | {n_pass} |')
    lines.append(f'| 失败 | {n_fail} |')
    lines.append(f'| 跳过 | {n_skip} |')
    lines.append(f'| 通过率 | {n_pass/max(total,1)*100:.1f}% |')
    lines.append('')

    for sec_label, cases in sections:
        count = len(cases)
        lines.append(f'## {sec_label}')
        lines.append('')
        lines.append(f'| 用例编号 | 用例标题 | 优先级 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 | 实际状态 |')
        lines.append(f'|---------|---------|--------|---------|---------|---------|---------|---------|')
        for t in cases:
            cid, title, pri, pre, steps, data, expected, status, dur, err, auto = t
            pre_s = (pre or '—')[:40].replace('\n',' ')
            steps_s = (steps or '—')[:50].replace('\n',' ')
            expected_s = (expected or '—')[:40]
            data_s = (data or '—')[:25]
            status_disp = STATUS_MAP.get(status, status)
            lines.append(f'| {cid} | {title} | {pri} | {pre_s} | {steps_s} | {data_s} | {expected_s} | {status_disp} |')
        lines.append('')

    lines.append('---')
    lines.append(f'*Generated by SOP Phase 3 — {today_str}*')
    lines.append('')

    fname = f'testcases-equipment-{page_slug}.md'
    with open(MD_OUT / fname, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'{fname}: {total} cases, {len(sections)} sections')

print(f'Done → {MD_OUT}')
