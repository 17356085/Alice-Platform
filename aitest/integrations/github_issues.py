"""
GitHub Issue → TLO Test Case Integration.

用法:
    # CLI: 从 GitHub Issue 生成测试用例
    python -m aitest.integrations.github_issues generate --repo=owner/repo --issue=123

    # API: Webhook 监听
    python -m aitest.integrations.github_issues webhook --port=8001

流程:
    GitHub Issue (label: "test-needed")
        ↓
    Issue → Requirement Analyst (理解需求)
        ↓
    Test Strategy Agent (生成测试策略)
        ↓
    Test Designer (Spec Pipeline → TEST_SPEC.md)
        ↓
    → 测试用例写入 governance/artifacts/
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

_WORKSTUDY = Path(__file__).resolve().parent.parent.parent


@dataclass
class GitHubIssue:
    """GitHub Issue 数据结构。"""
    number: int
    title: str
    body: str
    labels: list[str] = field(default_factory=list)
    repo: str = ""
    state: str = "open"
    url: str = ""

    @property
    def module_hint(self) -> Optional[str]:
        """从 title/body/labels 中提取模块名提示。"""
        text = f"{self.title} {self.body} {' '.join(self.labels)}"
        # Match module names
        known_modules = [
            "equipment", "personnel", "sales", "lab", "production",
            "warehouse", "workflow", "tank", "system", "system-user",
            "system-role", "system-management", "dcs",
        ]
        for mod in known_modules:
            if mod.lower() in text.lower():
                return mod
        return None

    @property
    def priority_hint(self) -> str:
        """从 labels 推断测试优先级。"""
        if any("critical" in l.lower() or "p0" in l.lower() for l in self.labels):
            return "P0"
        if any("high" in l.lower() or "p1" in l.lower() for l in self.labels):
            return "P1"
        return "P2"

    def to_test_requirement(self) -> str:
        """将 Issue 转换为测试需求描述。"""
        return f"""## 测试需求 (来自 GitHub Issue #{self.number})

### 标题
{self.title}

### 描述
{self.body}

### 优先级
{self.priority_hint}

### 模块
{self.module_hint or '需从描述中推断'}

### 来源
{self.url}
"""


class GitHubIssueClient:
    """GitHub Issue API 客户端。"""

    def __init__(self, token: str = None, repo: str = None):
        from aitest.config import config
        self.token = token or config.github_token
        self.repo = repo or config.github_repository
        self._api_base = "https://api.github.com"

    def fetch_issue(self, issue_number: int) -> Optional[GitHubIssue]:
        """获取单个 Issue。"""
        url = f"{self._api_base}/repos/{self.repo}/issues/{issue_number}"
        req = Request(url)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("User-Agent", "TLO-Platform")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")

        try:
            with urlopen(req) as resp:
                data = json.loads(resp.read())
            return GitHubIssue(
                number=data["number"],
                title=data["title"],
                body=data.get("body", ""),
                labels=[l["name"] for l in data.get("labels", [])],
                repo=self.repo,
                state=data["state"],
                url=data["html_url"],
            )
        except URLError as e:
            print(f"[GitHubIssue] Fetch error: {e}")
            return None

    def list_issues(self, label: str = "test-needed", state: str = "open") -> list[GitHubIssue]:
        """列出需要测试的 Issues。"""
        url = f"{self._api_base}/repos/{self.repo}/issues"
        params = f"?labels={label}&state={state}&per_page=20"
        req = Request(url + params)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("User-Agent", "TLO-Platform")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")

        try:
            with urlopen(req) as resp:
                data = json.loads(resp.read())
            return [
                GitHubIssue(
                    number=d["number"],
                    title=d["title"],
                    body=d.get("body", ""),
                    labels=[l["name"] for l in d.get("labels", [])],
                    repo=self.repo,
                    state=d["state"],
                    url=d["html_url"],
                )
                for d in data
            ]
        except URLError as e:
            print(f"[GitHubIssue] List error: {e}")
            return []

    def add_comment(self, issue_number: int, body: str):
        """在 Issue 上添加评论。"""
        url = f"{self._api_base}/repos/{self.repo}/issues/{issue_number}/comments"
        data = json.dumps({"body": body}).encode("utf-8")
        req = Request(url, data=data, method="POST")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "TLO-Platform")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")

        try:
            with urlopen(req) as resp:
                print(f"[GitHubIssue] Comment posted on #{issue_number}")
        except URLError as e:
            print(f"[GitHubIssue] Comment error: {e}")

    def add_label(self, issue_number: int, label: str):
        """给 Issue 添加标签。"""
        url = f"{self._api_base}/repos/{self.repo}/issues/{issue_number}/labels"
        data = json.dumps({"labels": [label]}).encode("utf-8")
        req = Request(url, data=data, method="POST")  # POST = append
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "TLO-Platform")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")

        try:
            with urlopen(req) as resp:
                print(f"[GitHubIssue] Label '{label}' added to #{issue_number}")
        except URLError as e:
            print(f"[GitHubIssue] Label error: {e}")


# ═══════════════════════════════════════════════════════
#  Integration: Issue → Test Case
# ═══════════════════════════════════════════════════════

def generate_testcase_from_issue(
    issue: GitHubIssue,
    output_dir: Path = None,
) -> Path:
    """
    从 GitHub Issue 生成测试用例。

    流程:
      1. Issue → Requirement Analyst → 测试需求文档
      2. Test Strategy Agent → 测试策略
      3. Test Designer → TEST_SPEC.md
    """
    if output_dir is None:
        module = issue.module_hint or "unknown"
        output_dir = _WORKSTUDY / "governance" / "artifacts" / "issue-generated" / module

    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: 生成测试需求文档
    req_doc = output_dir / f"REQ_ISSUE_{issue.number}.md"
    req_doc.write_text(issue.to_test_requirement(), encoding="utf-8")

    # Step 2: 生成元信息
    meta = {
        "source": "github_issue",
        "issue_number": issue.number,
        "issue_url": issue.url,
        "title": issue.title,
        "module_hint": issue.module_hint,
        "priority": issue.priority_hint,
        "labels": issue.labels,
        "generated_at": datetime.now().isoformat(),
    }
    meta_path = output_dir / f"META_ISSUE_{issue.number}.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[GitHubIssue] Test requirement generated: {req_doc}")

    return req_doc


def process_test_needed_issues(
    repo: str = None,
    token: str = None,
    auto_label: bool = True,
) -> list[Path]:
    """
    批量处理所有带 'test-needed' 标签的 Issues。

    返回生成的测试需求文件路径列表。
    """
    client = GitHubIssueClient(token=token, repo=repo)
    issues = client.list_issues(label="test-needed")

    generated = []
    for issue in issues:
        print(f"[GitHubIssue] Processing #{issue.number}: {issue.title[:60]}...")
        try:
            path = generate_testcase_from_issue(issue)
            generated.append(path)

            # 添加评论告知已生成测试用例
            client.add_comment(
                issue.number,
                f"🤖 **TLO Platform** 已自动生成测试需求:\n\n"
                f"- 模块: {issue.module_hint or '需人工确认'}\n"
                f"- 优先级: {issue.priority_hint}\n"
                f"- 测试需求: `{path.relative_to(_WORKSTUDY)}`\n\n"
                f"下一步: TLO Spec Pipeline 将生成完整测试用例。",
            )

            # 替换标签: test-needed → test-generated
            if auto_label:
                client.add_label(issue.number, "test-generated")

        except Exception as e:
            print(f"[GitHubIssue] Error processing #{issue.number}: {e}")

    return generated


# ── CLI ──

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TLO GitHub Issue Integration")
    sub = parser.add_subparsers(dest="command")

    gen = sub.add_parser("generate", help="Generate test case from issue")
    gen.add_argument("--repo", required=True)
    gen.add_argument("--issue", type=int, required=True)
    gen.add_argument("--token", default=None)

    batch = sub.add_parser("batch", help="Batch process test-needed issues")
    batch.add_argument("--repo", required=True)
    batch.add_argument("--token", default=None)

    args = parser.parse_args()

    if args.command == "generate":
        client = GitHubIssueClient(token=args.token, repo=args.repo)
        issue = client.fetch_issue(args.issue)
        if issue:
            path = generate_testcase_from_issue(issue)
            print(f"Generated: {path}")

    elif args.command == "batch":
        paths = process_test_needed_issues(repo=args.repo, token=args.token)
        print(f"\nGenerated {len(paths)} test requirements")
        for p in paths:
            print(f"  {p}")

    else:
        parser.print_help()
