#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""库管模块失败分析 — 分布 + 诊断 + 分类报告"""

import json
import re
import sys
import io
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# 强制 UTF-8 输出
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ALLURE_DIR = Path("D:/Desktop/WorkStudy/allure-results")

def load_results(limit=None):
    """加载所有 result.json（递归）"""
    results = []
    for f in sorted(ALLURE_DIR.rglob("*-result.json"), key=lambda p: -p.stat().st_mtime):
        if limit and len(results) >= limit:
            break
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            results.append(data)
        except:
            pass
    return results

def categorize_failure(result: dict) -> Tuple[str, str]:
    """分类失败原因"""
    status = result.get("status", "")
    if status != "failed":
        return ("PASS/SKIP", "")

    name = result.get("name", "")

    # 获取 statusDetails (Allure v2 标准字段)
    status_details = result.get("statusDetails", {})
    trace = status_details.get("trace", "")
    message = status_details.get("message", "")

    full_text = f"{name} {message} {trace}".lower()

    # 分类规则
    if any(x in full_text for x in ["elementnotfound", "no such element", "stale element", "unable to locate"]):
        return ("定位器失败", "选择器过期/变化或页面延迟")

    if any(x in full_text for x in ["timeout", "wait", "timed out"]):
        return ("超时", "元素未出现或页面加载慢")

    if any(x in full_text for x in ["assertion", "assert", "expected", "actual"]):
        return ("断言失败", "值/状态不符预期")

    if any(x in full_text for x in ["connection", "refused", "unreachable", "network"]):
        return ("网络错误", "服务不可达或连接断开")

    if any(x in full_text for x in ["permission", "forbidden", "401", "403"]):
        return ("权限错误", "用户权限不足")

    if any(x in full_text for x in ["keyerror", "valueerror", "typeerror", "attributeerror"]):
        return ("代码异常", "Python 异常或类型错误")

    if any(x in full_text for x in ["fixture", "setup", "teardown"]):
        return ("Fixture 错误", "测试前后处理失败")

    if message or trace:
        return ("其他错误", message[:100] if message else trace[:100])

    return ("未知", "无错误信息")

def main():
    results = load_results(limit=None)  # 全量

    if not results:
        print("❌ 未找到测试结果")
        return

    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "passed")
    failed = sum(1 for r in results if r.get("status") == "failed")
    skipped = sum(1 for r in results if r.get("status") == "skipped")

    # ══════════════════════════════════════════════════════════════════════════
    # 1. 失败分布统计
    # ══════════════════════════════════════════════════════════════════════════
    category_count = defaultdict(int)
    category_samples = defaultdict(list)

    for result in results:
        cat, reason = categorize_failure(result)
        category_count[cat] += 1
        if cat != "PASS/SKIP" and len(category_samples[cat]) < 3:
            category_samples[cat].append({
                "name": result.get("name", "N/A"),
                "reason": reason,
                "message": result.get("statusDetails", {}).get("message", "")[:150],
            })

    print("=" * 80)
    print("Failure Analysis Report - Warehouse Module")
    print("=" * 80)
    print()

    print(f"Total: {total}")
    print(f"  PASS: {passed} ({100*passed/total:.1f}%)")
    print(f"  FAIL: {failed} ({100*failed/total:.1f}%)")
    print(f"  SKIP: {skipped} ({100*skipped/total:.1f}%)")
    print()

    # ══════════════════════════════════════════════════════════════════════════
    # 2. 失败分类
    # ══════════════════════════════════════════════════════════════════════════
    print("=" * 80)
    print("Failure Distribution (by Type)")
    print("=" * 80)

    sorted_cats = sorted(
        [(cat, count) for cat, count in category_count.items() if cat != "PASS/SKIP"],
        key=lambda x: -x[1]
    )

    for cat, count in sorted_cats:
        pct = 100 * count / total
        print(f"\n[{cat}] {count} cases ({pct:.1f}%)")
        for sample in category_samples[cat]:
            print(f"  - {sample['name'][:60]}")
            if sample['reason']:
                print(f"    Reason: {sample['reason']}")
            if sample['message']:
                print(f"    Error: {sample['message']}")

    # ══════════════════════════════════════════════════════════════════════════
    # 3. 按用例名分组统计
    # ══════════════════════════════════════════════════════════════════════════
    print()
    print("=" * 80)
    print("Top Failed Tests (by count)")
    print("=" * 80)

    test_name_stats = defaultdict(lambda: {"pass": 0, "fail": 0})
    for result in results:
        name = result.get("name", "unknown")
        if result.get("status") == "passed":
            test_name_stats[name]["pass"] += 1
        elif result.get("status") == "failed":
            test_name_stats[name]["fail"] += 1

    # 只显示有失败的
    failed_tests = sorted(
        [(n, s) for n, s in test_name_stats.items() if s["fail"] > 0],
        key=lambda x: -x[1]["fail"]
    )

    for name, stats in failed_tests[:20]:  # top 20
        fail_pct = 100 * stats["fail"] / (stats["pass"] + stats["fail"])
        print(f"\n{name[:70]}")
        print(f"  PASS: {stats['pass']}, FAIL: {stats['fail']} ({fail_pct:.0f}%)")

    # ══════════════════════════════════════════════════════════════════════════
    # 4. 写入诊断报告
    # ══════════════════════════════════════════════════════════════════════════
    report_path = ALLURE_DIR / "failure_analysis.json"

    report_data = {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": f"{100*passed/total:.1f}%",
        },
        "failure_distribution": dict(sorted_cats),
        "top_failed_tests": [
            {
                "name": name,
                "pass_count": stats["pass"],
                "fail_count": stats["fail"],
                "fail_rate": f"{100*stats['fail']/(stats['pass']+stats['fail']):.1f}%",
            }
            for name, stats in failed_tests[:20]
        ],
        "category_samples": {
            cat: samples for cat, samples in category_samples.items()
        }
    }

    report_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding='utf-8')
    print()
    print(f"\nDiagnostic report saved: {report_path}")

if __name__ == "__main__":
    main()
