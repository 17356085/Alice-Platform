"""
Context Agent — 为下游 Agent 构建最小精准 Context。

职责:
  1. 诊断当前任务范围 (module / page / phase)
  2. 从 git diff + CURRENT_TASK + checkpoint 精确定位中断点
  3. 只打包"本次任务需要的"文件，扔掉不相关的
  4. Automation Agent 永远不知道整个项目，只知道当前页面

数据流:
  User Input → diagnose_task() → TaskContext
  TaskContext → pack_focused_context() → FocusedContext
  FocusedContext → 注入 automation/page-object-generator 等 Skill

使用:
  ctx_agent = ContextAgent()
  task = ctx_agent.diagnose_task("继续写 equipment")
  ctx = ctx_agent.pack_focused_context(task)
  # ctx.to_skill_variables() → 传给 ContextInjector
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
ZJSN_TEST = WORKSTUDY / "ZJSN_Test-master526"
CONTEXT_MODULES = GOVERNANCE / "context" / "projects" / "web-automation" / "modules"
ARTIFACTS_DIR = GOVERNANCE / "artifacts"
SOP_STATUS_DIR = ARTIFACTS_DIR / "sop-status"

# 已知模块列表（从目录发现 + 常用别名）
_KNOWN_MODULES = [
    "equipment", "personnel", "warehouse", "sales", "tank",
    "lab", "dcs", "system", "workflow", "production",
    "contractor", "system-role",
]

# 用户输入 → 模块别名映射
_MODULE_ALIASES: dict[str, str] = {
    "设备": "equipment", "器材": "equipment",
    "人员": "personnel", "人事": "personnel",
    "仓库": "warehouse", "库房": "warehouse",
    "销售": "sales",
    "罐区": "tank",
    "实验": "lab",
    "dcs": "dcs",
    "系统": "system",
    "工作流": "workflow",
    "承包商": "contractor",
    "角色": "system-role",
}


@dataclass
class TaskContext:
    """诊断结果：当前任务的精确范围。"""
    module: str
    pages: list[str]
    current_phase: str          # Automation / Test Design / Bug Analysis ...
    checkpoint_path: Optional[str] = None
    git_diff_summary: str = ""  # git diff HEAD~1 摘要
    interrupted_page: Optional[str] = None   # 上次中断在哪个页面
    interrupted_phase: Optional[str] = None  # 上次中断在哪个 Phase
    detection_source: str = "unknown"        # how we detected this
    confidence: float = 1.0                  # 0..1

    @property
    def is_resume(self) -> bool:
        return bool(self.interrupted_page or self.interrupted_phase)


@dataclass
class FocusedContext:
    """精准 context 包：只包含本次任务需要的文件。"""
    module: str
    page: str
    phase: str

    # 已加载的上下文内容
    page_interface: str = ""        # PAGE_INTERFACE.yaml (~200 tok)
    page_context: str = ""          # PAGE_CONTEXT.md (~500 tok，仅本页)
    auto_strategy: str = ""         # AUTO_STRATEGY.md (~300 tok)
    checkpoint_summary: str = ""    # 上次进度摘要 (~200 tok)
    git_diff: str = ""              # git diff (仅相关文件, ~100 tok)

    # 省略了什么（可观测性）
    omitted: list[str] = field(default_factory=list)
    total_chars: int = 0

    def to_skill_variables(self) -> dict:
        """转换为 ContextInjector 变量格式。"""
        return {
            "module": self.module,
            "page": self.page,
            "module_dir": str(CONTEXT_MODULES / self.module),
            "po_path": str(
                ZJSN_TEST / "page" / f"{self.module}_page" / f"{self.page.replace('-', '_')}_page.py"
            ),
            "test_path": str(
                ZJSN_TEST / "script" / self.module / f"test_{self.page.replace('-', '_')}.py"
            ),
        }

    def to_inline_context(self) -> str:
        """构建注入 Skill Prompt 的内联 context 字符串。"""
        parts = []

        if self.checkpoint_summary:
            parts.append(f"## 上次进度\n{self.checkpoint_summary}")

        if self.git_diff:
            parts.append(f"## 近期改动 (git diff)\n{self.git_diff}")

        if self.page_interface:
            parts.append(f"## 页面接口 (PAGE_INTERFACE.yaml)\n{self.page_interface}")

        if self.auto_strategy:
            parts.append(f"## 自动化策略\n{self.auto_strategy}")

        if self.page_context:
            parts.append(f"## 页面上下文\n{self.page_context}")

        if self.omitted:
            parts.append(
                f"## 省略内容 (不需要)\n" + "\n".join(f"- {x}" for x in self.omitted)
            )

        return "\n\n".join(parts)


class ContextAgent:
    """
    Context Agent — 诊断任务范围 + 构建最小 Context。

    Automation Agent 只拿 FocusedContext，不知道整个项目。
    """

    def diagnose_task(
        self,
        user_input: str,
        module_hint: Optional[str] = None,
        page_hint: Optional[str] = None,
    ) -> TaskContext:
        """
        从用户输入 + git diff + SOP_STATUS 诊断当前任务范围。

        优先级:
          1. 显式参数 (module_hint, page_hint)
          2. SOP_STATUS JSON 最近未完成模块/页面
          3. git diff 分析改动文件
          4. 用户输入关键词匹配
        """
        # ── Step 1: 模块识别 ──
        module = module_hint or self._detect_module(user_input)

        # ── Step 2: 从 SOP_STATUS 找中断点 ──
        interrupted = self._find_interrupted_task(module)

        # ── Step 3: 页面识别 ──
        pages = []
        if page_hint:
            pages = [page_hint]
        elif interrupted.get("page"):
            pages = [interrupted["page"]]
        else:
            pages = self._detect_pages(user_input, module)

        # ── Step 4: Phase 识别 ──
        phase = interrupted.get("phase") or self._detect_phase(user_input)

        # ── Step 5: git diff 摘要（仅本模块相关文件）──
        diff_summary = self._get_diff_summary(module, pages)

        # ── Step 6: checkpoint 路径 ──
        checkpoint_path = self._find_checkpoint_path(module)

        return TaskContext(
            module=module,
            pages=pages,
            current_phase=phase,
            checkpoint_path=checkpoint_path,
            git_diff_summary=diff_summary,
            interrupted_page=interrupted.get("page"),
            interrupted_phase=interrupted.get("phase"),
            detection_source=interrupted.get("source", "user_input"),
            confidence=interrupted.get("confidence", 0.8),
        )

    def pack_focused_context(
        self,
        task: TaskContext,
        page: Optional[str] = None,
    ) -> FocusedContext:
        """
        为单个页面构建精准 context 包。

        Args:
            task: diagnose_task() 的结果
            page: 目标页面（默认用 task.pages[0]）
        """
        target_page = page or (task.pages[0] if task.pages else "")
        if not target_page:
            return FocusedContext(
                module=task.module,
                page="",
                phase=task.current_phase,
                omitted=["没有检测到目标页面"],
            )

        ctx = FocusedContext(
            module=task.module,
            page=target_page,
            phase=task.current_phase,
        )

        page_dir = CONTEXT_MODULES / task.module / "pages" / target_page
        omitted = []

        # ── 读 PAGE_INTERFACE.yaml (~200 tok，优先) ──
        pi_path = page_dir / "PAGE_INTERFACE.yaml"
        if pi_path.exists():
            ctx.page_interface = self._read_capped(pi_path, 800)
        else:
            omitted.append(f"PAGE_INTERFACE.yaml (not found: {pi_path})")

        # ── 读 AUTO_STRATEGY.md (~300 tok) ──
        as_path = page_dir / "AUTO_STRATEGY.md"
        if as_path.exists():
            ctx.auto_strategy = self._read_capped(as_path, 1200)
        else:
            omitted.append(f"AUTO_STRATEGY.md (not found: {as_path})")

        # ── 读 PAGE_CONTEXT.md（如果 PAGE_INTERFACE 缺失才读）──
        pc_path = page_dir / "PAGE_CONTEXT.md"
        if not ctx.page_interface and pc_path.exists():
            ctx.page_context = self._read_capped(pc_path, 2000)
        elif pc_path.exists():
            omitted.append("PAGE_CONTEXT.md (PAGE_INTERFACE already loaded, skipped)")
        else:
            omitted.append(f"PAGE_CONTEXT.md (not found: {pc_path})")

        # ── checkpoint 摘要 ──
        if task.checkpoint_path:
            ctx.checkpoint_summary = self._extract_checkpoint_summary(
                task.checkpoint_path, task.module, target_page
            )

        # ── git diff（仅本页相关文件）──
        if task.git_diff_summary:
            ctx.git_diff = task.git_diff_summary

        # ── 明确省略清单 ──
        omitted.extend([
            "governance/context/shared-language.md (全局, 不需要)",
            "governance/README.md (不需要)",
            *[
                f"module/{m} (其他模块, 不需要)"
                for m in _KNOWN_MODULES
                if m != task.module
            ],
            *[
                f"page/{p} (其他页面, 不需要)"
                for p in task.pages
                if p != target_page
            ],
        ])

        ctx.omitted = omitted
        ctx.total_chars = (
            len(ctx.page_interface)
            + len(ctx.page_context)
            + len(ctx.auto_strategy)
            + len(ctx.checkpoint_summary)
            + len(ctx.git_diff)
        )

        return ctx

    # ════════════════════════════════════════════════════════════════
    # 内部方法
    # ════════════════════════════════════════════════════════════════

    def _detect_module(self, user_input: str) -> str:
        """从用户输入识别模块名。"""
        text = user_input.lower()

        # 先查别名
        for alias, module in _MODULE_ALIASES.items():
            if alias in text:
                return module

        # 再查英文模块名
        for module in _KNOWN_MODULES:
            if module in text:
                return module

        # 从 SOP_STATUS 找最近活跃模块
        return self._find_most_recent_active_module()

    def _find_most_recent_active_module(self) -> str:
        """扫描 SOP_STATUS 文件，找最近修改的未完成模块。"""
        if not SOP_STATUS_DIR.exists():
            # fallback: 扫 artifacts 根目录的 SOP_STATUS_*.json
            fallback_dir = ARTIFACTS_DIR
            pattern = "SOP_STATUS_*.json"
        else:
            fallback_dir = SOP_STATUS_DIR
            pattern = "SOP_STATUS_*.json"

        latest_mtime = 0.0
        latest_module = "equipment"  # 最终 fallback

        for f in fallback_dir.glob(pattern):
            try:
                mtime = f.stat().st_mtime
                if mtime > latest_mtime:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    # 只取未完成的
                    if data.get("status") not in ("completed", "done"):
                        latest_mtime = mtime
                        # 文件名: SOP_STATUS_equipment.json → equipment
                        latest_module = f.stem.replace("SOP_STATUS_", "")
            except Exception:
                pass

        return latest_module

    def _find_interrupted_task(self, module: str) -> dict:
        """从 SOP_STATUS 找上次中断的任务。"""
        # 优先查 sop-status 子目录
        for status_dir in [SOP_STATUS_DIR, ARTIFACTS_DIR]:
            status_file = status_dir / f"SOP_STATUS_{module}.json"
            if not status_file.exists():
                continue
            try:
                data = json.loads(status_file.read_text(encoding="utf-8"))

                completed = set(data.get("completed_phases", []))
                all_phases = [
                    "Project Init", "Requirement", "Test Design",
                    "Automation", "Execute & Debug", "Bug Analysis",
                    "Report", "Knowledge Update",
                ]
                # 找第一个未完成的 phase
                for phase in all_phases:
                    if phase not in completed:
                        # 当前在哪个页面
                        current_page = data.get("current_page") or data.get("pages", [None])[0]
                        return {
                            "phase": phase,
                            "page": current_page,
                            "source": "sop_status",
                            "confidence": 0.9,
                        }
            except Exception:
                pass

        return {}

    def _detect_pages(self, user_input: str, module: str) -> list[str]:
        """从用户输入 + 模块目录推断目标页面。"""
        text = user_input.lower()

        # 尝试从模块的 pages 目录发现
        module_pages_dir = CONTEXT_MODULES / module / "pages"
        if module_pages_dir.exists():
            candidate_pages = [d.name for d in module_pages_dir.iterdir() if d.is_dir()]
            # 按用户输入关键词过滤
            matched = [p for p in candidate_pages if p.replace("-", " ") in text or p in text]
            if matched:
                return matched[:3]  # 最多 3 个页面
            # 无关键词匹配 → 返回第一个未完成的页面
            return candidate_pages[:1] if candidate_pages else []

        return []

    def _detect_phase(self, user_input: str) -> str:
        """从用户输入识别当前 Phase。"""
        text = user_input.lower()
        phase_keywords = {
            "Automation": ["automation", "自动化", "po", "page object", "写代码", "写 po", "page-object"],
            "Test Design": ["test design", "测试设计", "测试用例", "test case", "风险"],
            "Execute & Debug": ["执行", "跑", "run", "debug", "失败", "fix"],
            "Bug Analysis": ["bug", "错误", "error", "分析"],
            "Requirement": ["需求", "requirement", "模块建模"],
        }
        for phase, keywords in phase_keywords.items():
            if any(kw in text for kw in keywords):
                return phase
        return "Automation"  # 最常见的默认值

    def _get_diff_summary(self, module: str, pages: list[str]) -> str:
        """git diff HEAD~1 — 只要本模块相关文件。"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                cwd=str(WORKSTUDY),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
            )
            if result.returncode != 0:
                return ""

            changed_files = result.stdout.strip().split("\n")

            # 过滤：只保留本模块相关文件
            module_files = [
                f for f in changed_files
                if module in f.lower()
                or any(p.replace("-", "_") in f.lower() for p in pages)
            ]

            if not module_files:
                return ""

            # 获取这些文件的 diff（摘要）
            diff_result = subprocess.run(
                ["git", "diff", "--unified=2", "HEAD~1", "HEAD", "--"] + module_files[:5],
                cwd=str(WORKSTUDY),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )

            if diff_result.returncode != 0:
                return f"Changed files: {', '.join(module_files[:5])}"

            # 截断 diff 到 800 chars
            diff_text = diff_result.stdout
            if len(diff_text) > 800:
                diff_text = diff_text[:800] + "\n... (truncated)"

            return diff_text

        except Exception:
            return ""

    def _find_checkpoint_path(self, module: str) -> Optional[str]:
        """找最近的 checkpoint 文件。"""
        for status_dir in [SOP_STATUS_DIR, ARTIFACTS_DIR]:
            f = status_dir / f"SOP_STATUS_{module}.json"
            if f.exists():
                return str(f)
        return None

    def _extract_checkpoint_summary(
        self, checkpoint_path: str, module: str, page: str
    ) -> str:
        """从 SOP_STATUS JSON 提取本页进度摘要（精简，不加载全文）。"""
        try:
            data = json.loads(Path(checkpoint_path).read_text(encoding="utf-8"))
            completed = data.get("completed_phases", [])
            current_page = data.get("current_page", page)
            pages = data.get("pages", [])
            status = data.get("status", "unknown")

            lines = [
                f"Module: {module} | Status: {status}",
                f"Completed phases: {', '.join(completed) if completed else '(none)'}",
                f"Pages: {', '.join(str(p) for p in pages)}",
                f"Current page: {current_page}",
            ]

            # 页面级 artifact 状态（仅本页）
            artifact_map = data.get("artifact_map", {})
            page_artifacts = {k: v for k, v in artifact_map.items() if page in str(k)}
            if page_artifacts:
                lines.append(f"Artifacts for {page}:")
                for key, paths in list(page_artifacts.items())[:3]:
                    lines.append(f"  - {key}: {paths}")

            return "\n".join(lines)

        except Exception:
            return ""

    @staticmethod
    def _read_capped(path: Path, max_chars: int) -> str:
        """读文件并截断。"""
        try:
            content = path.read_text(encoding="utf-8")
            if len(content) > max_chars:
                return content[:max_chars] + f"\n... (truncated at {max_chars} chars)"
            return content
        except Exception:
            return ""
