"""
Worktree Manager — Git Worktree 隔离管理器。

借鉴 Aperant core/worktree.py:
  - 每个 Agent 在独立 worktree 中工作，主分支不受影响
  - 验证通过后才合并回原分支
  - 失败时保留 worktree 供人工检查

用法:
    from aitest.infra.worktree_manager import WorktreeManager

    mgr = WorktreeManager()
    with mgr.isolate("automation-fix-equipment") as wt:
        # 在 wt.path 中安全地修改文件
        wt.write("script/equipment/test_alarm.py", new_content)
        # 验证通过 → 自动合并
        wt.mark_success()
    # 离开 with 块 → 自动清理 worktree
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


_WORKSTUDY = Path(__file__).resolve().parent.parent.parent
_WORKTREE_ROOT = _WORKSTUDY / ".claude" / "worktrees"


@dataclass
class WorktreeContext:
    """单个 worktree 的上下文。"""
    name: str
    path: Path
    base_branch: str
    branch: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    success: bool = False
    merged: bool = False
    _files_changed: list[str] = field(default_factory=list)

    def write(self, rel_path: str, content: str):
        """在 worktree 中写入文件（相对路径）。"""
        target = self.path / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self._files_changed.append(rel_path)

    def read(self, rel_path: str) -> str:
        """从 worktree 中读取文件。"""
        return (self.path / rel_path).read_text(encoding="utf-8")

    def exists(self, rel_path: str) -> bool:
        """检查文件在 worktree 中是否存在。"""
        return (self.path / rel_path).exists()

    def mark_success(self):
        """标记 worktree 修改已验证通过，退出时自动合并。"""
        self.success = True

    @property
    def changed_files(self) -> list[str]:
        return list(self._files_changed)

    @property
    def is_dirty(self) -> bool:
        return len(self._files_changed) > 0


class WorktreeManager:
    """
    Git Worktree 隔离管理器。

    生命周期:
      1. create(name) → 创建 worktree + 分支
      2. Agent 在 worktree.path 中修改文件
      3a. 验证通过 → mark_success() → 退出时 git merge + git branch -d
      3b. 验证失败 → 退出时保留 worktree 供人工检查
      4. cleanup() → git worktree remove + git branch -D (仅成功时)
    """

    def __init__(self, base_ref: str = "HEAD"):
        """
        Args:
            base_ref: worktree 的基准引用。
                      "HEAD" = 当前本地分支
                      "origin/master" = 远程主分支
        """
        self.base_ref = base_ref
        _WORKTREE_ROOT.mkdir(parents=True, exist_ok=True)

    def isolate(self, name: str = None, agent: str = "agent") -> WorktreeContext:
        """
        创建隔离 worktree 上下文管理器。

        用法:
            mgr = WorktreeManager()
            with mgr.isolate("fix-locator-equipment") as wt:
                wt.write("script/equipment/test_alarm.py", fixed_code)
                if verify(wt.path):
                    wt.mark_success()  # ← 验证通过，自动合并
            # 退出 with → 自动清理 (成功时) 或保留 (失败时)
        """
        return _WorktreeSession(self, name or self._make_name(agent))

    def create(self, name: str = None, agent: str = "agent") -> WorktreeContext:
        """创建 worktree（手动管理，需要手动调用 cleanup）。"""
        ctx = self._create_worktree(name or self._make_name(agent))
        return ctx

    def merge_and_cleanup(self, ctx: WorktreeContext):
        """合并 worktree 分支到原分支，然后删除 worktree。"""
        if ctx.success and ctx.is_dirty:
            self._merge_branch(ctx)
        self._remove_worktree(ctx, force=not ctx.success)

    def list_worktrees(self) -> list[dict]:
        """列出所有 TLO 管理的 worktree。"""
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=str(_WORKSTUDY), capture_output=True, text=True
        )
        worktrees = []
        current = {}
        for line in result.stdout.split("\n"):
            if line.startswith("worktree "):
                if current:
                    worktrees.append(current)
                current = {"path": line.split("worktree ", 1)[1]}
            elif line.startswith("HEAD ") and current:
                current["head"] = line.split("HEAD ", 1)[1]
            elif line.startswith("branch ") and current:
                current["branch"] = line.split("branch ", 1)[1].replace("refs/heads/", "")
        if current:
            worktrees.append(current)
        return [
            w for w in worktrees
            if str(_WORKTREE_ROOT) in w.get("path", "")
        ]

    def cleanup_stale(self, max_age_hours: int = 24):
        """清理超过 max_age_hours 的未使用 worktree。"""
        stale = []
        now = time.time()
        for wt_dir in _WORKTREE_ROOT.iterdir():
            if wt_dir.is_dir():
                age_hours = (now - wt_dir.stat().st_mtime) / 3600
                if age_hours > max_age_hours:
                    stale.append(wt_dir)
        for d in stale:
            shutil.rmtree(d, ignore_errors=True)
            print(f"[WorktreeManager] Cleaned stale: {d.name}")
        return len(stale)

    # ── Internal ──

    def _make_name(self, agent: str) -> str:
        ts = datetime.now().strftime("%y%m%d-%H%M%S")
        uid = uuid.uuid4().hex[:6]
        safe_agent = agent.replace(" ", "-").lower()[:20]
        return f"tlo-{safe_agent}-{ts}-{uid}"

    def _create_worktree(self, name: str) -> WorktreeContext:
        wt_path = _WORKTREE_ROOT / name
        branch = f"tlo/{name}"

        # 创建 worktree
        result = subprocess.run(
            ["git", "worktree", "add", str(wt_path), "-b", branch, self.base_ref],
            cwd=str(_WORKSTUDY), capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"git worktree add failed: {result.stderr.strip()}")

        # 获取原分支名
        base_branch = self._current_branch()

        print(f"[WorktreeManager] Created: {name}")
        print(f"  Path:   {wt_path}")
        print(f"  Branch: {branch} (from {base_branch})")

        return WorktreeContext(
            name=name,
            path=wt_path,
            base_branch=base_branch,
            branch=branch,
        )

    def _merge_branch(self, ctx: WorktreeContext):
        """将 worktree 分支合并回原分支，然后删除分支。"""
        try:
            # 切回原分支并合并
            cmds = [
                f"git checkout {ctx.base_branch}",
                f"git merge --no-ff {ctx.branch} -m 'TLO: auto-merge {ctx.name}'",
                f"git branch -d {ctx.branch}",
            ]
            for cmd in cmds:
                result = subprocess.run(
                    cmd.split(), cwd=str(_WORKSTUDY),
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    print(f"[WorktreeManager] Merge warning ({cmd}): {result.stderr.strip()}")
                    ctx.merged = False
                    return
            ctx.merged = True
            print(f"[WorktreeManager] Merged: {ctx.branch} → {ctx.base_branch}")
        except Exception as e:
            print(f"[WorktreeManager] Merge failed: {e}")
            ctx.merged = False

    def _remove_worktree(self, ctx: WorktreeContext, force: bool = False):
        """删除 worktree 目录 + 分支。"""
        wt_path = str(ctx.path)
        try:
            # Remove worktree
            args = ["git", "worktree", "remove", wt_path]
            if force:
                args.append("--force")
            subprocess.run(args, cwd=str(_WORKSTUDY), capture_output=True, text=True)

            # Clean up branch if not merged
            if force and not ctx.merged:
                subprocess.run(
                    ["git", "branch", "-D", ctx.branch],
                    cwd=str(_WORKSTUDY), capture_output=True, text=True
                )

            status = "Removed" if ctx.success else "Force-removed"
            print(f"[WorktreeManager] {status}: {ctx.name}")
        except Exception as e:
            print(f"[WorktreeManager] Remove error: {e}")

    def _current_branch(self) -> str:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(_WORKSTUDY), capture_output=True, text=True
        )
        return result.stdout.strip() or "main"


class _WorktreeSession:
    """上下文管理器 — with mgr.isolate(name) as wt: ..."""

    def __init__(self, mgr: WorktreeManager, name: str):
        self.mgr = mgr
        self.name = name
        self.ctx: Optional[WorktreeContext] = None

    def __enter__(self) -> WorktreeContext:
        self.ctx = self.mgr.create(self.name)
        return self.ctx

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.ctx:
            if exc_type is not None:
                # 异常 → 不合并，强制清理
                self.ctx.success = False
            self.mgr.merge_and_cleanup(self.ctx)
        return False  # 不抑制异常
