#!/usr/bin/env python
"""CI 残留测试数据检测脚本

用途:
    - 按 test_prefix_rules 扫描各模块列表 API，检测残留测试数据
    - CI 中运行：超过 max_residual_allowed 阈值时返回非零退出码
    - 手工运行：python tools/check_residual_data.py [--clean] [--module <m>]

用法:
    python tools/check_residual_data.py                        # 检测残留
    python tools/check_residual_data.py --clean                # 检测 + 自动清理
    python tools/check_residual_data.py --module equipment      # 只检测指定模块
    python tools/check_residual_data.py --json                 # JSON 输出 (CI 用)

退出码:
    0 — 残留量在阈值以内
    1 — 超过阈值
    2 — 脚本执行错误
"""

import argparse
import json
import logging
import sys
from typing import Optional

import requests

# 项目根目录
sys.path.insert(0, ".")
from config import BASE_URL, DEFAULT_USERNAME, DEFAULT_PASSWORD
from config.cleanup import CLEANUP_CONFIG

logger = logging.getLogger(__name__)


# ── 扫描配置：entity_type → 列表 API + 名称字段 ─────────────────
SCAN_TARGETS = {
    # 系统管理
    "user":       ("/api/system/user/list",        "userName"),
    "role":       ("/api/system/role/list",        "roleName"),
    "menu":       ("/api/system/menu/list",        "name"),
    "dept":       ("/api/system/dept/list",        "deptName"),
    "post":       ("/api/system/post/list",        "postName"),
    "dict":       ("/api/system/dict/type/list",   "dictName"),
    "notice":     ("/api/system/notice/list",      "noticeTitle"),
    "params":     ("/api/system/params/list",      "paramName"),
    # 设备管理
    "unit":       ("/api/equipment/unit/list",     "unitName"),
    "device":     ("/api/equipment/device/list",   "deviceName"),
    "alarm_config":("/api/equipment/alarm-config/list", "alarmName"),
    "maintenance":("/api/equipment/maintenance/list",   "planName"),
    "sensor":     ("/api/equipment/sensor/list",   "sensorName"),
    # 人员管理
    "employee":   ("/api/personnel/employee/list",        "realName"),
    "course":     ("/api/personnel/training/course/list", "courseName"),
    "question":   ("/api/personnel/training/question/list", "questionTitle"),
    "paper":      ("/api/personnel/training/paper/list",  "paperName"),
    "exam":       ("/api/personnel/training/exam/list",   "examName"),
    "train_plan": ("/api/personnel/training/plan/list",   "planName"),
    # 销售管理
    "customer":   ("/api/sales/customer/list",    "customerName"),
    "contract":   ("/api/sales/contract/list",    "contractName"),
    "sales_order":("/api/sales/sales-order/list", "orderName"),
    # 化验管理
    "lab_report": ("/api/lab/report/list",        "reportName"),
}


def _login() -> requests.Session:
    session = requests.Session()
    r = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": DEFAULT_USERNAME, "password": DEFAULT_PASSWORD},
        timeout=10,
    )
    r.raise_for_status()
    token = r.json()["data"]["accessToken"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


def _fetch_list(session: requests.Session, url: str, page_size: int = 500) -> list:
    """获取列表全量数据"""
    full_url = BASE_URL.rstrip("/") + url
    try:
        r = session.get(full_url, params={"pageNum": 1, "pageSize": page_size}, timeout=30)
        r.raise_for_status()
        data = r.json()
        # 兼容多种分页格式
        records = (
            data.get("data", {}).get("records")
            or data.get("data", {}).get("rows")
            or data.get("rows")
            or data.get("records")
            or []
        )
        if isinstance(data.get("data"), list):
            records = data["data"]
        elif isinstance(data, list):
            records = data
        return records or []
    except Exception as e:
        logger.warning("  ⚠ 获取列表失败 %s: %s", url, e)
        return []


def _match_test_prefix(value: str, prefixes: list[str]) -> bool:
    """检查值是否匹配任一测试前缀"""
    if not value:
        return False
    v = str(value).strip()
    for p in prefixes:
        if v.upper().startswith(p.upper()):
            return True
    return False


def scan_residual(
    session: requests.Session,
    module: Optional[str] = None,
) -> dict[str, list[dict]]:
    """扫描残留测试数据

    Returns:
        {entity_type: [{name, id, url}, ...]}
    """
    prefixes = list(CLEANUP_CONFIG.get("test_prefix_rules", {}).values())
    if not prefixes:
        prefixes = ["TC-", "TEST-", "DBG-"]

    logger.info("扫描残留测试数据 (前缀: %s)...", ", ".join(prefixes))

    results: dict[str, list[dict]] = {}
    targets = SCAN_TARGETS

    if module:
        # 过滤出指定模块相关的 entity type
        targets = {k: v for k, v in SCAN_TARGETS.items() if k.startswith(module) or module in k}

    for entity_type, (list_url, name_field) in targets.items():
        records = _fetch_list(session, list_url)
        matched = []
        for row in records:
            name = row.get(name_field, "")
            if _match_test_prefix(name, prefixes):
                row_id = row.get("id") or row.get(f"{entity_type}Id") or row.get("dictCode")
                delete_url = CLEANUP_CONFIG["batch_clean_urls"].get(entity_type, "")
                matched.append({
                    "name": name,
                    "id": row_id,
                    "delete_url": delete_url.format(id=row_id) if delete_url and row_id else "",
                })
        if matched:
            results[entity_type] = matched
            logger.info("  %s: %d 条残留", entity_type, len(matched))
        else:
            logger.debug("  %s: 干净", entity_type)

    return results


def clean_residual(session: requests.Session, findings: dict[str, list[dict]]) -> int:
    """清理扫描到的残留数据"""
    cleaned = 0
    for entity_type, items in findings.items():
        for item in items:
            if not item["delete_url"]:
                logger.warning("  ⚠ 无法清理 %s(%s): 无删除 URL", entity_type, item["name"])
                continue
            try:
                full_url = BASE_URL.rstrip("/") + item["delete_url"]
                r = session.delete(full_url, timeout=10)
                if r.status_code in (200, 204):
                    logger.info("  ✅ 已删除 %s(%s)", entity_type, item["name"])
                    cleaned += 1
                else:
                    logger.warning("  ⚠ 删除失败 %s(%s): HTTP %d", entity_type, item["name"], r.status_code)
            except Exception as e:
                logger.warning("  ⚠ 删除异常 %s(%s): %s", entity_type, item["name"], e)
    return cleaned


def main():
    parser = argparse.ArgumentParser(description="CI 残留测试数据检测")
    parser.add_argument("--clean", action="store_true", help="自动清理残留数据")
    parser.add_argument("--module", type=str, help="只检测指定模块")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出 (CI 用)")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    threshold = CLEANUP_CONFIG.get("max_residual_allowed", 50)

    try:
        session = _login()
    except Exception as e:
        logger.error("登录失败: %s", e)
        if args.json:
            print(json.dumps({"error": f"Login failed: {e}", "exit_code": 2}))
        sys.exit(2)

    findings = scan_residual(session, module=args.module)
    total = sum(len(v) for v in findings.values())

    if args.json:
        output = {
            "total_residual": total,
            "threshold": threshold,
            "exceeded": total > threshold,
            "by_entity": {k: [{"name": i["name"], "id": i["id"]} for i in v] for k, v in findings.items()},
            "exit_code": 1 if total > threshold else 0,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"  残留检测结果: {total} 条 (阈值: {threshold})")
        print(f"{'='*60}")
        if total == 0:
            print("  ✅ 无残留测试数据")
        else:
            for entity_type, items in findings.items():
                print(f"\n  [{entity_type}] {len(items)} 条:")
                for item in items[:10]:  # 最多显示 10 条
                    print(f"    - {item['name']} (id={item['id']})")
                if len(items) > 10:
                    print(f"    ... 及其他 {len(items)-10} 条")

    if args.clean and total > 0:
        cleaned = clean_residual(session, findings)
        print(f"\n  清理完成: {cleaned}/{total} 条")
        if not args.json:
            if cleaned == total:
                print("  ✅ 全部清理完成")
            else:
                print(f"  ⚠  {total - cleaned} 条未能清理")

    if total > threshold:
        if not args.json:
            print(f"\n  🔴 残留量 {total} 超过阈值 {threshold}!")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
