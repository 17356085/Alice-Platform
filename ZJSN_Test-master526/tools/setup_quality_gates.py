#!/usr/bin/env python3
"""一键安装"代码质量防护体系"

用法:
  python tools/setup_quality_gates.py install     # 安装 pre-commit 钩子
  python tools/setup_quality_gates.py remove      # 卸载
"""
import os
import sys
import subprocess
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS_DIR = os.path.join(PROJECT_ROOT, ".git", "hooks")
PRE_COMMIT_SRC = os.path.join(PROJECT_ROOT, "tools", "pre-commit.sh")
PRE_COMMIT_DST = os.path.join(HOOKS_DIR, "pre-commit")


def install():
    """安装 pre-commit 钩子"""
    if not os.path.isdir(HOOKS_DIR):
        print(f"[ERR] 未找到 Git hooks 目录: {HOOKS_DIR}")
        print("  请确认该目录已初始化 Git 仓库")
        return False

    if not os.path.isfile(PRE_COMMIT_SRC):
        print(f"[ERR] 未找到 pre-commit 脚本: {PRE_COMMIT_SRC}")
        return False

    # 检查是否已安装
    if os.path.isfile(PRE_COMMIT_DST):
        with open(PRE_COMMIT_DST) as f:
            first_line = f.readline().strip()
        # 如果不是 sample，且包含 check_code_quality，说明是我们安装的
        if ".sample" not in first_line and "check_code_quality" in open(PRE_COMMIT_DST).read():
            print("  [PASS] pre-commit 已安装，跳过")
            return True
        # 备份已存在的自定义钩子
        backup = PRE_COMMIT_DST + ".bak"
        print(f"  [WARN] 发现已有 pre-commit 钩子，备份到 {backup}")
        shutil.copy2(PRE_COMMIT_DST, backup)

    # 复制脚本
    shutil.copy2(PRE_COMMIT_SRC, PRE_COMMIT_DST)

    # 设置执行权限（Unix）
    if os.name != "nt":
        os.chmod(PRE_COMMIT_DST, 0o755)
        print("  [PASS] pre-commit 安装完成 (Unix)")
    else:
        print("  [PASS] pre-commit 安装完成 (Windows)")
        print("  注意: Windows 下需要 Git Bash 执行 git commit 才生效")
        print("  可手动运行: copy tools\\pre-commit.sh .git\\hooks\\pre-commit")

    return True


def remove():
    """卸载 pre-commit 钩子"""
    if os.path.isfile(PRE_COMMIT_DST):
        os.remove(PRE_COMMIT_DST)
        # 恢复备份
        backup = PRE_COMMIT_DST + ".bak"
        if os.path.isfile(backup):
            shutil.move(backup, PRE_COMMIT_DST)
            print(f"  [PASS] 已卸载，并恢复备份钩子")
        else:
            print(f"  [PASS] 已卸载 pre-commit 钩子")
    else:
        print("  [WARN] pre-commit 未安装")
    return True


def check():
    """检查安装状态"""
    print("═══ 防护体系状态检查 ═══")

    # 1. CLAUDE.md 红线（方案1）
    claude_file = os.path.join(PROJECT_ROOT, "..", "..", "CLAUDE.md")
    # 尝试在项目根目录找
    for candidate in [
        os.path.join(PROJECT_ROOT, "..", "CLAUDE.md"),
        os.path.join(PROJECT_ROOT, "..", "..", "CLAUDE.md"),
        os.path.join(PROJECT_ROOT, "CLAUDE.md"),
    ]:
        if os.path.isfile(candidate):
            claude_file = candidate
            break

    if os.path.isfile(claude_file):
        content = open(claude_file, encoding="utf-8", errors="replace").read()
        if "代码红线" in content:
            print("  [PASS] 方案1 (CLAUDE.md 红线) : 已安装")
        else:
            print("  [WARN] 方案1 (CLAUDE.md 红线) : 未安装")
    else:
        print("  [WARN] 方案1 : CLAUDE.md 未找到")

    # 2. Skill 自检（方案2）
    governance_dir = os.path.join(PROJECT_ROOT, "..", "governance")
    skill_dir = os.path.join(governance_dir, "skills", "automation")
    has_self_check = 0
    total_skill = 0
    for fname in ["page-object-generator.md", "test-script-generator.md"]:
        fpath = os.path.join(skill_dir, fname)
        if os.path.isfile(fpath):
            total_skill += 1
            if "生成后自检" in open(fpath, encoding="utf-8", errors="replace").read():
                has_self_check += 1
    print(f"  [PASS] 方案2 (Skill 自检) : {has_self_check}/{total_skill} 已安装")

    # 3. Pre-commit（方案3A）
    if os.path.isfile(PRE_COMMIT_DST):
        print("  [PASS] 方案3A (pre-commit) : 已安装")
    else:
        print("  [WARN] 方案3A (pre-commit) : 未安装 (运行 python tools/setup_quality_gates.py)")

    # 4. AST 扫描器（方案3B）
    scanner_path = os.path.join(PROJECT_ROOT, "tools", "check_code_quality.py")
    if os.path.isfile(scanner_path):
        print("  [PASS] 方案3B (AST 扫描器) : 已安装")
    else:
        print("  [WARN] 方案3B (AST 扫描器) : 未安装")

    print("══════════════════════════════")
    return True


def main():
    """CLI 入口"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python tools/setup_quality_gates.py install   # 安装 pre-commit")
        print("  python tools/setup_quality_gates.py remove    # 卸载 pre-commit")
        print("  python tools/setup_quality_gates.py check     # 检查安装状态")
        print("  python tools/setup_quality_gates.py           # 同上（默认）")
        return 0

    cmd = sys.argv[1]
    if cmd == "install":
        install()
    elif cmd == "remove":
        remove()
    elif cmd == "check":
        check()
    else:
        print(f"未知命令: {cmd}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
