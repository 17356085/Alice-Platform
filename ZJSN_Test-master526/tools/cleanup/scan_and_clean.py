"""离线扫描并清理测试残留数据

用于 CI 流水线或手工恢复场景，扫描后端所有模块中名称含 test_ 前缀的数据。

用法:
    python tools/cleanup/scan_and_clean.py                # 扫描+交互确认后清理
    python tools/cleanup/scan_and_clean.py --force         # 扫描+强制清理
    python tools/cleanup/scan_and_clean.py --modules dict,course  # 只清理指定模块
"""
import sys
import os
import logging

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BASE_URL, DEFAULT_USERNAME, DEFAULT_PASSWORD
from config.cleanup import CLEANUP_CONFIG

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# {模块名: (列表API路径, 名称字段, 匹配前缀)}
SCAN_QUERIES = {
    "dict":      ("/api/system/dict/type/list",       "dictName",     "test_"),
    "user":      ("/api/system/user/list",             "userName",     "test_"),
    "role":      ("/api/system/role/list",             "roleName",     "test_"),
    "course":    ("/api/personnel/training/course/list","courseName",  "test_"),
    "contract":  ("/api/sales/contract/page",          "contractName", "test_|分页-"),
    "equipment": ("/api/equipment/device/list",        "deviceName",   "test_"),
}


def login() -> requests.Session:
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"username": DEFAULT_USERNAME, "password": DEFAULT_PASSWORD},
               timeout=10)
    r.raise_for_status()
    s.headers.update({"Authorization": f"Bearer {r.json()['data']['accessToken']}"})
    return s


def scan_all(session, modules=None) -> dict:
    """扫描所有模块，返回 {模块名: [(id, 名称), ...]}"""
    found = {}
    for mod, (url, name_field, prefix) in SCAN_QUERIES.items():
        if modules and mod not in modules:
            continue
        r = session.get(f"{BASE_URL}{url}", params={"pageNum": 1, "pageSize": 500}, timeout=30)
        try:
            records = r.json().get("data", {}).get("records", [])
        except Exception:
            logger.warning("  ⚠ %s: 解析响应失败 (HTTP %s)", mod, r.status_code)
            continue
        patterns = prefix.split("|")
        matches = [
            (rec.get("id"), rec.get(name_field, ""))
            for rec in records
            if any(p in str(rec.get(name_field, "")) for p in patterns)
        ]
        if matches:
            found[mod] = matches
    return found


def delete_entities(session, module, entities):
    """批量删除指定模块的实体"""
    delete_url = CLEANUP_CONFIG["batch_clean_urls"].get(module)
    if not delete_url:
        logger.warning("  ❌ %s: 无删除端点配置", module)
        return 0
    count = 0
    for eid, name in entities:
        url = f"{BASE_URL}{delete_url.format(id=eid)}"
        r = session.delete(url, timeout=10)
        if r.ok:
            count += 1
            logger.info("  ✅ %s: %s (%s)", module, name, eid)
        else:
            logger.warning("  ❌ %s: %s (id=%s) — HTTP %s", module, name, eid, r.status_code)
    return count


def main():
    import argparse
    parser = argparse.ArgumentParser(description="扫描/清理测试残留数据")
    parser.add_argument("--force", action="store_true", help="强制清理（不交互确认）")
    parser.add_argument("--modules", default="", help="指定模块，逗号分隔（默认全部）")
    args = parser.parse_args()

    modules = args.modules.split(",") if args.modules else None
    session = login()

    logger.info("正在扫描残留数据...")
    found = scan_all(session, modules)

    if not found:
        logger.info("\n✅ 未发现残留的测试数据")
        return

    logger.info("\n=== 残留数据扫描结果 ===")
    total = 0
    for mod, entities in found.items():
        logger.info("  %s: %d 条", mod, len(entities))
        for eid, name in entities[:3]:
            logger.info("    - %s (%s)", name, eid)
        if len(entities) > 3:
            logger.info("    ... 共 %d 条", len(entities))
        total += len(entities)

    logger.info("\n总计: %d 条残留数据", total)
    threshold = CLEANUP_CONFIG.get("max_residual_allowed", 50)
    if total > threshold:
        logger.warning("⚠ 残留数据超过阈值 (%d)", threshold)

    if not args.force:
        try:
            resp = input(f"\n是否清理这 {total} 条数据？(y/N): ")
        except (EOFError, KeyboardInterrupt):
            resp = "n"
        if resp.lower() != "y":
            logger.info("已取消")
            return

    cleaned = 0
    for mod, entities in found.items():
        cleaned += delete_entities(session, mod, entities)
    logger.info("\n✅ 共清理 %d 条数据", cleaned)


if __name__ == "__main__":
    main()
