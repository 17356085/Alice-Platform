"""GitHub/GitLab Integration API — bidirectional issue-testcase linking.

POST   /api/integrations/github/issue   Create GitHub issue from test failure
POST   /api/integrations/gitlab/issue   Create GitLab issue from test failure
GET    /api/integrations/status           Check integration status (token validity)
"""
import json as _json
import logging
from fastapi import APIRouter, Request, HTTPException

logger = logging.getLogger(__name__)

integrations_router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@integrations_router.get("/status")
async def integration_status():
    """返回集成状态（检查token是否已配置）。"""
    return {
        "github": {"configured": False, "note": "Set token in Project Settings → Integrations"},
        "gitlab": {"configured": False, "note": "Set token in Project Settings → Integrations"},
    }


@integrations_router.post("/github/issue")
async def create_github_issue(request: Request):
    """从测试失败创建 GitHub Issue。

    Body: {
        "title": "Test failure: equipment/alarm-config",
        "body": "## Failure details\n...",
        "labels": ["test-failure", "bug"],
        "token": "ghp_...",
        "repo": "owner/repo"
    }
    """
    body = await request.json() if await request.body() else {}
    token = body.get("token", "")
    repo = body.get("repo", "")
    title = body.get("title", "Test Failure")
    issue_body = body.get("body", "")
    labels = body.get("labels", ["test-failure"])

    if not token or not repo:
        raise HTTPException(status_code=400, detail="GitHub token and repo are required")

    try:
        import urllib.request
        import urllib.error

        url = f"https://api.github.com/repos/{repo}/issues"
        data = _json.dumps({
            "title": title,
            "body": issue_body,
            "labels": labels,
        }).encode()

        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("User-Agent", "AITest-Platform/1.0")

        with urllib.request.urlopen(req, timeout=15) as resp:
            result = _json.loads(resp.read())
            return {
                "status": "created",
                "issue_url": result.get("html_url", ""),
                "issue_number": result.get("number", 0),
                "title": result.get("title", ""),
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        raise HTTPException(status_code=e.code, detail=f"GitHub API error: {error_body[:300]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitHub request failed: {e}")


@integrations_router.post("/gitlab/issue")
async def create_gitlab_issue(request: Request):
    """从测试失败创建 GitLab Issue。

    Body: {
        "title": "Test failure: equipment/alarm-config",
        "description": "## Failure details\n...",
        "labels": ["test-failure"],
        "token": "glpat-...",
        "project_id": "12345"
    }
    """
    body = await request.json() if await request.body() else {}
    token = body.get("token", "")
    project_id = body.get("project_id", "")
    title = body.get("title", "Test Failure")
    description = body.get("description", "")

    if not token or not project_id:
        raise HTTPException(status_code=400, detail="GitLab token and project_id are required")

    try:
        import urllib.request
        import urllib.error

        url = f"https://gitlab.com/api/v4/projects/{project_id}/issues"
        data = _json.dumps({
            "title": title,
            "description": description,
            "labels": body.get("labels", "test-failure"),
        }).encode()

        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("PRIVATE-TOKEN", token)
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "AITest-Platform/1.0")

        with urllib.request.urlopen(req, timeout=15) as resp:
            result = _json.loads(resp.read())
            return {
                "status": "created",
                "issue_url": result.get("web_url", ""),
                "issue_iid": result.get("iid", 0),
                "title": result.get("title", ""),
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        raise HTTPException(status_code=e.code, detail=f"GitLab API error: {error_body[:300]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitLab request failed: {e}")
