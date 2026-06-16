"""全量测试 — 实时输出，杜绝死锁"""
import subprocess, sys, os, time
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
log_file = os.path.join(os.getcwd(), 'overnight_results.txt')

def cleanup():
    os.system('taskkill /F /IM chromedriver.exe >nul 2>&1')
    os.system('taskkill /F /IM chrome.exe >nul 2>&1')
    time.sleep(5)

cleanup()

modules = [
    ('equipment+lab', 'script/equipment/ script/lab/'),
    ('personnel',     'script/personnel/'),
    ('system',        'script/system/'),
    ('sales',         'script/sales/'),
]

with open(log_file, 'w', encoding='utf-8') as f:
    f.write(f'=== FULL TEST {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ===\n')
    f.write(f'URL: https://aiwechatminidemo.cimc-digital.com/\n\n')

all_results = []

for name, paths in modules:
    stamp = datetime.now().strftime('%H:%M:%S')
    print(f'[{stamp}] {name} START')

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f'\n--- [{stamp}] {name} START ---\n')

    cmd = [sys.executable, '-m', 'pytest'] + paths.split() + [
        '-q', '--tb=line', '-o', 'addopts=', '--reruns', '0'
    ]

    try:
        # 用 Popen + communicate 避免 capture_output 死锁
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1
        )

        collected_lines = []
        try:
            stdout, _ = proc.communicate(timeout=5400)
            output = stdout
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, _ = proc.communicate()
            output = stdout + '\n[TIMEOUT after 90min]'

        # 边跑边写
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(output)

        # 提取汇总行
        summary_line = ''
        for line in output.split('\n'):
            line = line.strip()
            if '=' in line and 'passed' in line and 'failed' in line:
                summary_line = line
                break

        stamp2 = datetime.now().strftime('%H:%M:%S')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f'\n--- [{stamp2}] {name} DONE: {summary_line} ---\n')

        print(f'  {summary_line}')
        all_results.append((name, summary_line, proc.returncode))

    except Exception as e:
        stamp2 = datetime.now().strftime('%H:%M:%S')
        err_msg = f'ERROR: {e}'
        print(f'  [{stamp2}] {name} {err_msg}')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f'\n--- [{stamp2}] {name} {err_msg} ---\n')
        all_results.append((name, err_msg, -1))

    cleanup()

# 最终汇总
summary = f'\n{"="*60}\nALL DONE [{datetime.now().strftime("%H:%M:%S")}]\n{"="*60}\n'
for name, line, code in all_results:
    summary += f'  {name}: {line}\n'

print(summary)
with open(log_file, 'a', encoding='utf-8') as f:
    f.write(summary)

print(f'Results: {log_file}')
