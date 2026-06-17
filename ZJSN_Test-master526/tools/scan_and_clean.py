#!/usr/bin/env python
"""测试数据扫描与清理工具 (Data Sanitization Phase)

用法:
    python tools/scan_and_clean.py --scan              # 仅扫描，列出残留测试数据
    python tools/scan_and_clean.py --clean             # 扫描+清理
    python tools/scan_and_clean.py --scan --module=equipment  # 按模块扫描
    python tools/scan_and_clean.py --dry-run           # 模拟清理（不实际删除）

设计:
    - 读取 config/cleanup.py CLEANUP_CONFIG 获取 API 端点映射
    - 按 test_prefix_rules 匹配测试数据命名 (TC- / TEST / [AUTO])
    - 通过 API 扫描 → DELETE 清理
    - 只读实体自动跳过
"""
import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime
from urllib.parse import urljoin

import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.cleanup import CLEANUP_CONFIG
from config import BASE_URL, DEFAULT_USERNAME, DEFAULT_PASSWORD

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("scan_and_clean")


# ═══════════════════════════════════════════════════════════════
#  核心
# ═══════════════════════════════════════════════════════════════

class ScanAndClean:
    """测试数据扫描与清理器"""

    def __init__(self, base_url=None, username=None, password=None, dry_run=False):
        self.base_url = (base_url or BASE_URL).rstrip("/")
        self.username = username or DEFAULT_USERNAME
        self.password = password or DEFAULT_PASSWORD
        self.dry_run = dry_run
        self.session = requests.Session()
        self.token = None
        self.results = {"scanned": 0, "found": 0, "cleaned": 0, "errors": 0, "details": []}

    # ── 认证 ─────────────────────────────────────────────────

    def login(self):
        """API 登录获取 Bearer token"""
        try:
            r = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": self.username, "password": self.password},
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                self.token = data.get("data", {}).get("accessToken", "")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                logger.info("API 登录成功")
                return True
            logger.error("登录失败: HTTP %s — %s", r.status_code, r.text[:200])
            return False
        except requests.RequestException as e:
            logger.error("登录请求异常: %s", e)
            return False

    # ── 扫描 ─────────────────────────────────────────────────

    def scan_entity(self, entity_type, api_url, prefix_patterns):
        """扫描指定实体类型，返回匹配测试前缀的记录 ID 列表

        Args:
            entity_type: 实体类型标识
            api_url: 列表查询 API (不含 {id})
            prefix_patterns: 测试数据命名前缀规则

        Returns:
            list[dict]: [{"id": ..., "name": ..., "code": ...}, ...]
        """
        found = []
        page = 1
        page_size = 100

        # 从删除 URL 推导列表 URL
        list_url = self._delete_to_list_url(api_url)

        while True:
            try:
                r = self.session.get(
                    f"{self.base_url}{list_url}",
                    params={"pageNum": page, "pageSize": page_size},
                    timeout=CLEANUP_CONFIG.get("api_timeout", 10),
                )
                if r.status_code != 200:
                    logger.debug("  %s: HTTP %s", entity_type, r.status_code)
                    break

                data = r.json()
                records = data.get("data", {}).get("records", [])
                if not records:
                    break

                for rec in records:
                    rec_id = rec.get("id")
                    rec_name = str(rec.get("name", rec.get("entityName", "")))
                    rec_code = str(rec.get("code", rec.get("entityCode", "")))
                    rec_remark = str(rec.get("remark", ""))

                    # 匹配测试前缀
                    is_test = False
                    matched_rule = None
                    for rule_key, rule_val in prefix_patterns.items():
                        if rule_key == "name" and rec_name.startswith(rule_val):
                            is_test = True
                            matched_rule = f"name→{rule_val}"
                            break
                        if rule_key == "code" and rec_code.upper().startswith(rule_val.upper()):
                            is_test = True
                            matched_rule = f"code→{rule_val}"
                            break
                        if rule_key == "remark" and rule_val in rec_remark:
                            is_test = True
                            matched_rule = f"remark→{rule_val}"
                            break

                    if is_test:
                        found.append({
                            "id": rec_id,
                            "name": rec_name or rec_code or f"id={rec_id}",
                            "matched_rule": matched_rule,
                        })

                if len(records) < page_size:
                    break
                page += 1

            except requests.RequestException as e:
                logger.debug("  %s: 请求异常 %s", entity_type, e)
                break

        return found

    def _delete_to_list_url(self, delete_url):
        """从 DELETE /api/x/{id} 推导 LIST /api/x/list 或 /api/x

        常见模式:
          /api/system/dict/type/{id} → /api/system/dict/type/list
          /api/equipment/device/{id} → /api/equipment/device/list
        """
        base = delete_url.rsplit("/{id}", 1)[0]
        return f"{base}/list"

    def delete_entity(self, entity_type, api_url, entity_id):
        """通过 API 删除单个实体"""
        url = api_url.replace("{id}", str(entity_id))
        try:
            r = self.session.delete(
                f"{self.base_url}{url}",
                timeout=CLEANUP_CONFIG.get("api_timeout", 10),
            )
            if r.status_code in (200, 204):
                return True
            logger.debug("  删除 %s id=%s: HTTP %s", entity_type, entity_id, r.status_code)
            return False
        except requests.RequestException as e:
            logger.debug("  删除 %s id=%s: %s", entity_type, entity_id, e)
            return False

    # ── 主流程 ───────────────────────────────────────────────

    def run(self, module_filter=None, mode="scan"):
        """执行扫描/清理

        Args:
            module_filter: 模块名过滤 (None = 全部)
            mode: "scan" | "clean"
        """
        if not self.login():
            return self.results

        prefix_patterns = CLEANUP_CONFIG.get("test_prefix_rules", {})
        batch_urls = CLEANUP_CONFIG.get("batch_clean_urls", {})
        readonly = set(CLEANUP_CONFIG.get("readonly_entities", []))
        skip_patterns = CLEANUP_CONFIG.get("skip_patterns", [])

        # 模块→实体类型映射 (用于 --module 过滤)
        module_entity_map = {
            "system": ["dict", "dict_data", "user", "role", "menu", "dept", "org", "post", "notice", "params"],
            "equipment": ["unit", "device", "equipment", "alarm_config", "maintenance", "sensor"],
            "personnel": ["employee", "course", "question", "paper", "exam", "train_plan",
                         "certificate", "contractor_unit", "contractor_personnel"],
            "sales": ["customer", "contract", "sales_order"],
            "lab": ["lab_report"],
            "production": ["business_type", "shift_team"],
            "tank": ["tank_alarm"],
            "warehouse": ["hazard_item", "hazard_in_order", "hazard_out_order",
                         "spare_item", "spare_in_order", "spare_out_order",
                         "spare_requisition", "reagent_item", "reagent_fill"],
        }

        logger.info("=" * 50)
        logger.info("测试数据%s", "扫描" if mode == "scan" else "清理")
        if module_filter:
            logger.info("  模块: %s", module_filter)
        if self.dry_run:
            logger.info("  [DRY-RUN] 不实际删除")
        logger.info("=" * 50)

        for entity_type, api_url in batch_urls.items():
            # 过滤
            if entity_type in readonly:
                continue
            if any(entity_type.startswith(p) for p in skip_patterns):
                continue
            if module_filter:
                allowed = module_entity_map.get(module_filter, [])
                if entity_type not in allowed:
                    continue

            self.results["scanned"] += 1
            logger.info("扫描: %s", entity_type)

            found = self.scan_entity(entity_type, api_url, prefix_patterns)
            if not found:
                continue

            self.results["found"] += len(found)
            logger.info("  发现 %d 条测试残留:", len(found))
            for item in found:
                logger.info("    id=%s  name=%s  [%s]",
                           item["id"], item["name"][:50], item["matched_rule"])
                self.results["details"].append({
                    "entity_type": entity_type,
                    **item,
                })

            if mode == "clean" and not self.dry_run:
                for item in found:
                    if self.delete_entity(entity_type, api_url, item["id"]):
                        self.results["cleaned"] += 1
                        logger.info("    ✓ 已删除 id=%s", item["id"])
                    else:
                        self.results["errors"] += 1
                        logger.warning("    ✗ 删除失败 id=%s", item["id"])
                    time.sleep(0.3)  # 避免请求过快

        # ── 汇总 ──
        logger.info("=" * 50)
        logger.info("扫描: %d 实体类型 | 发现: %d 条残留 | 清理: %d 条 | 错误: %d",
                   self.results["scanned"], self.results["found"],
                   self.results["cleaned"], self.results["errors"])

        # 保存报告
        report_path = os.path.join(
            PROJECT_ROOT, "governance", "artifacts", "data-sanitization",
            f"clean-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json",
        )
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        logger.info("报告: %s", report_path)

        return self.results


# ═══════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="测试数据扫描与清理")
    parser.add_argument("--scan", action="store_true", default=True,
                       help="扫描残留测试数据 (默认)")
    parser.add_argument("--clean", action="store_true",
                       help="扫描并清理残留")
    parser.add_argument("--dry-run", action="store_true",
                       help="模拟运行，不实际删除")
    parser.add_argument("--module", "-m", type=str, default=None,
                       help="按模块过滤 (system/equipment/personnel/sales/lab/production/tank/warehouse)")
    parser.add_argument("--base-url", type=str, default=None,
                       help=f"覆盖 BASE_URL (默认: {BASE_URL})")
    parser.add_argument("--username", type=str, default=None,
                       help="API 用户名")
    parser.add_argument("--password", type=str, default=None,
                       help="API 密码")
    args = parser.parse_args()

    mode = "clean" if args.clean else "scan"
    if args.dry_run:
        mode = "scan"

    tool = ScanAndClean(
        base_url=args.base_url,
        username=args.username,
        password=args.password,
        dry_run=args.dry_run,
    )
    results = tool.run(module_filter=args.module, mode=mode)

    # 如果有残留未清理，退出码 1
    if results["found"] > 0 and mode == "scan" and not args.dry_run:
        logger.warning("发现 %d 条未清理的测试残留", results["found"])


if __name__ == "__main__":
    main()
