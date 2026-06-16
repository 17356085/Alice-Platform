"""测试数据随机化工具 — 避免并行/重复执行时的数据冲突。

用法:
    from base.test_data_utils import unique_name, unique_phone, unique_code

    # 每次调用生成唯一值
    name = unique_name("用户")        # → "用户_0608_143022_a3f2"
    phone = unique_phone()            # → "13806081430"
    code  = unique_code("CUST")       # → "CUST_0608_a3f2"
"""

import random
import string
import time
from datetime import datetime

# ── 全局计数器（进程内递增，避免同秒内重复） ────────────────────
_COUNTER = 0


def _seq():
    global _COUNTER
    _COUNTER += 1
    return _COUNTER


def _stamp():
    """短时间戳: MMDD_HHMMSS"""
    return datetime.now().strftime("%m%d_%H%M%S")


def _rand4():
    """4位随机字母数字"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))


# ═════════════════════════════════════════════════════════════════
# 对外 API
# ═════════════════════════════════════════════════════════════════

def unique_name(prefix="测试"):
    """生成唯一名称，如 '测试用户_0608_143022_a3f2'"""
    return f"{prefix}_{_stamp()}_{_rand4()}"


def unique_username(prefix="testuser"):
    """生成唯一用户名，如 'testuser_0608_a3f2'（纯字母数字，适合登录用）"""
    day = datetime.now().strftime("%m%d")
    return f"{prefix}_{day}_{_rand4()}"


def unique_phone():
    """生成唯一手机号，如 '13806081430'（前缀138 + 日期 + 序号）"""
    now = datetime.now()
    base = f"1{random.choice('3456789')}{now.strftime('%m%d')}"
    suffix = f"{_seq():03d}"
    # 补到11位
    result = base + suffix
    while len(result) < 11:
        result += str(random.randint(0, 9))
    return result[:11]


def unique_code(prefix="TEST"):
    """生成唯一编码，如 'TEST_0608_a3f2'"""
    day = datetime.now().strftime("%m%d")
    return f"{prefix}_{day}_{_rand4()}"


def unique_email(prefix="test"):
    """生成唯一邮箱"""
    return f"{prefix}_{_stamp()}_{_rand4()}@test.local"


def unique_id_no():
    """生成唯一身份证号格式（18位，仅用于测试占位）"""
    area = str(random.randint(110000, 659000))
    birth = datetime.now().strftime("%Y%m%d")
    suffix = f"{_seq():04d}"
    result = area + birth + suffix
    while len(result) < 18:
        result += str(random.randint(0, 9))
    return result[:18]


def now_tag():
    """当前时间标签，如 '2026-06-08 14:30:22'"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def short_tag():
    """短标签，如 '0608_1430'"""
    return datetime.now().strftime("%m%d_%H%M")
