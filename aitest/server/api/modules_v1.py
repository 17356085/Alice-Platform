"""Persistent project module CRUD.

Modules are filesystem-backed project resources, matching the existing
ArtifactStore/.tlo dual-path storage contract. A module owns a directory and
can later accumulate pages and generated artifacts.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from aitest.platform.artifacts import ArtifactStore
from aitest.platform.page_config import PageConfig, PageExecutionPlan


modules_router = APIRouter(prefix="/api/v1/modules", tags=["modules"])
_MODULE_NAME = re.compile(r"^[\w-][\w.-]{0,127}$", re.UNICODE)
_PAGE_NAME = _MODULE_NAME


class ModuleCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=2000)


class ModuleUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=128)
    description: Optional[str] = Field(default=None, max_length=2000)


class PageCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=2000)
    url: str = Field(default="", max_length=2000)
    config: dict[str, Any] = Field(default_factory=dict)
    locators: dict[str, Any] = Field(default_factory=dict)
    execution: PageExecutionPlan = Field(default_factory=PageExecutionPlan)
    enabled: bool = True

    @field_validator("locators")
    @classmethod
    def validate_locator_schema(cls, value: dict[str, Any]) -> dict[str, Any]:
        return PageConfig(page_id="page", locators=value).locators


class PageUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=128)
    description: Optional[str] = Field(default=None, max_length=2000)
    url: Optional[str] = Field(default=None, max_length=2000)
    config: Optional[dict[str, Any]] = None
    locators: Optional[dict[str, Any]] = None
    execution: Optional[PageExecutionPlan] = None
    enabled: Optional[bool] = None

    @field_validator("locators")
    @classmethod
    def validate_locator_schema(cls, value: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
        if value is None:
            return None
        return PageConfig(page_id="page", locators=value).locators


def _project_id(project_id: str) -> str:
    return project_id.strip() or "web-automation"


def _validate_name(name: str) -> str:
    value = name.strip()
    if not _MODULE_NAME.fullmatch(value) or value in {".", ".."}:
        raise HTTPException(status_code=422, detail="Invalid module name")
    return value


def _validate_page_name(name: str) -> str:
    value = name.strip()
    if not _PAGE_NAME.fullmatch(value) or value in {".", ".."}:
        raise HTTPException(status_code=422, detail="Invalid page name")
    return value


def _store(project_id: str) -> ArtifactStore:
    return ArtifactStore(_project_id(project_id))


def _roots(store: ArtifactStore, name: str) -> list[Path]:
    """Return primary and legacy module roots, constrained by the store."""
    primary = store.path(name)
    legacy = store._modules_dir / name  # dual-write migration path
    roots = [primary]
    if legacy != primary:
        roots.append(legacy)
    base_paths = [p.resolve() for p in store._get_module_search_dirs()]
    safe: list[Path] = []
    for root in roots:
        resolved = root.resolve()
        if not any(resolved == base or base in resolved.parents for base in base_paths):
            raise HTTPException(status_code=400, detail="Invalid module path")
        safe.append(root)
    return safe


def _meta(store: ArtifactStore, name: str) -> dict:
    for root in _roots(store, name):
        path = root / "module.json"
        if path.exists():
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(value, dict):
                    return value
            except (OSError, json.JSONDecodeError):
                pass
    return {}


def _module_payload(store: ArtifactStore, name: str) -> dict:
    pages = store.list_pages(name)
    meta = _meta(store, name)
    return {
        "id": name,
        "name": name,
        "description": str(meta.get("description", "")),
        "pages": pages,
        "page_count": len(pages),
        "persistent": True,
    }


def _page_roots(store: ArtifactStore, module: str, page: str) -> list[Path]:
    module_roots = _roots(store, module)
    roots = [root / "pages" / page for root in module_roots]
    base_paths = [
        (base / module / "pages").resolve()
        for base in store._get_module_search_dirs()
    ]
    safe: list[Path] = []
    for root in roots:
        resolved = root.resolve()
        if not any(resolved == base or base in resolved.parents for base in base_paths):
            raise HTTPException(status_code=400, detail="Invalid page path")
        if root not in safe:
            safe.append(root)
    return safe


def _page_meta(store: ArtifactStore, module: str, page: str) -> dict:
    for root in _page_roots(store, module, page):
        path = root / "page.json"
        if path.exists():
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(value, dict):
                    return value
            except (OSError, json.JSONDecodeError):
                pass
    return {}


def _page_payload(store: ArtifactStore, module: str, page: str) -> dict:
    meta = _page_meta(store, module, page)
    config = meta.get("config", {})
    locators = meta.get("locators", {})
    execution = meta.get("execution", {})
    return {
        "id": page,
        "name": page,
        "module": module,
        "description": str(meta.get("description", "")),
        "url": str(meta.get("url", "")),
        "config": config if isinstance(config, dict) else {},
        "locators": locators if isinstance(locators, dict) else {},
        "execution": execution if isinstance(execution, dict) else {},
        "enabled": bool(meta.get("enabled", True)),
        "persistent": True,
    }


def _write_page_meta(root: Path, meta: dict) -> None:
    (root / "page.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


@modules_router.get("")
async def list_modules(project_id: str = Query("")):
    store = _store(project_id)
    names = set(store.list_modules())
    for base in store._get_module_search_dirs():
        if base.exists():
            names.update(
                path.name for path in base.iterdir()
                if path.is_dir() and not path.name.startswith((".", "_"))
            )
    modules = [_module_payload(store, name) for name in sorted(names)]
    return {"modules": modules, "total": len(modules), "project_id": _project_id(project_id)}


@modules_router.get("/{module_id}/pages")
async def list_module_pages(module_id: str, project_id: str = Query("")):
    module = _validate_name(module_id)
    store = _store(project_id)
    if not any(root.exists() for root in _roots(store, module)):
        raise HTTPException(status_code=404, detail="Module not found")
    names = set(store.list_pages(module))
    for root in _roots(store, module):
        pages_dir = root / "pages"
        if pages_dir.exists():
            names.update(
                path.name for path in pages_dir.iterdir()
                if path.is_dir() and not path.name.startswith((".", "_"))
            )
    pages = [_page_payload(store, module, name) for name in sorted(names) if name]
    return {"pages": pages, "total": len(pages), "module_id": module, "project_id": _project_id(project_id)}


@modules_router.post("/{module_id}/pages", status_code=201)
async def create_module_page(module_id: str, req: PageCreateRequest, project_id: str = Query("")):
    module = _validate_name(module_id)
    page = _validate_page_name(req.name)
    store = _store(project_id)
    if not any(root.exists() for root in _roots(store, module)):
        raise HTTPException(status_code=404, detail="Module not found")
    roots = _page_roots(store, module, page)
    if any(root.exists() for root in roots):
        raise HTTPException(status_code=409, detail=f"Page '{page}' already exists")
    for root in roots:
        root.mkdir(parents=True, exist_ok=False)
        _write_page_meta(root, {
            "description": req.description.strip(),
            "url": req.url.strip(),
            "config": req.config,
            "locators": req.locators,
            "execution": req.execution.model_dump(mode="json"),
            "enabled": req.enabled,
        })
    return {"status": "created", "page": _page_payload(store, module, page)}


@modules_router.patch("/{module_id}/pages/{page_id}")
async def update_module_page(module_id: str, page_id: str, req: PageUpdateRequest, project_id: str = Query("")):
    module = _validate_name(module_id)
    current = _validate_page_name(page_id)
    store = _store(project_id)
    current_roots = _page_roots(store, module, current)
    existing = [root for root in current_roots if root.exists()]
    if not existing:
        raise HTTPException(status_code=404, detail="Page not found")
    target = _validate_page_name(req.name) if req.name is not None else current
    if target != current:
        target_roots = _page_roots(store, module, target)
        if any(root.exists() for root in target_roots):
            raise HTTPException(status_code=409, detail=f"Page '{target}' already exists")
        for source, destination in zip(existing, target_roots):
            destination.parent.mkdir(parents=True, exist_ok=True)
            source.rename(destination)
        current = target
        current_roots = target_roots
    if any(value is not None for value in (req.description, req.url, req.config, req.locators, req.execution, req.enabled)):
        payload = _page_meta(store, module, current)
        if req.description is not None:
            payload["description"] = req.description.strip()
        if req.url is not None:
            payload["url"] = req.url.strip()
        if req.config is not None:
            payload["config"] = req.config
        if req.locators is not None:
            payload["locators"] = req.locators
        if req.execution is not None:
            payload["execution"] = req.execution.model_dump(mode="json")
        if req.enabled is not None:
            payload["enabled"] = req.enabled
        for root in current_roots:
            if root.exists():
                _write_page_meta(root, payload)
    return {"status": "updated", "page": _page_payload(store, module, current)}


@modules_router.delete("/{module_id}/pages/{page_id}")
async def delete_module_page(module_id: str, page_id: str, project_id: str = Query("")):
    module = _validate_name(module_id)
    page = _validate_page_name(page_id)
    store = _store(project_id)
    roots = _page_roots(store, module, page)
    existing = [root for root in roots if root.exists()]
    if not existing:
        raise HTTPException(status_code=404, detail="Page not found")
    for root in existing:
        shutil.rmtree(root)
    return {"status": "deleted", "module_id": module, "page_id": page}


@modules_router.post("", status_code=201)
async def create_module(req: ModuleCreateRequest, project_id: str = Query("")):
    name = _validate_name(req.name)
    store = _store(project_id)
    roots = _roots(store, name)
    if any(root.exists() for root in roots):
        raise HTTPException(status_code=409, detail=f"Module '{name}' already exists")
    for root in roots:
        root.mkdir(parents=True, exist_ok=False)
        (root / "pages").mkdir()
        (root / "module.json").write_text(
            json.dumps({"description": req.description.strip()}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return {"status": "created", "module": _module_payload(store, name)}


@modules_router.patch("/{module_id}")
async def update_module(module_id: str, req: ModuleUpdateRequest, project_id: str = Query("")):
    current = _validate_name(module_id)
    store = _store(project_id)
    current_roots = _roots(store, current)
    if not any(root.exists() for root in current_roots):
        raise HTTPException(status_code=404, detail="Module not found")
    target = _validate_name(req.name) if req.name is not None else current
    if target != current:
        target_roots = _roots(store, target)
        if any(root.exists() for root in target_roots):
            raise HTTPException(status_code=409, detail=f"Module '{target}' already exists")
        for source, destination in zip(current_roots, target_roots):
            destination.parent.mkdir(parents=True, exist_ok=True)
            source.rename(destination)
        current = target
        current_roots = target_roots
    if req.description is not None:
        payload = {"description": req.description.strip()}
        for root in current_roots:
            (root / "module.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "updated", "module": _module_payload(store, current)}


@modules_router.delete("/{module_id}")
async def delete_module(module_id: str, project_id: str = Query("")):
    name = _validate_name(module_id)
    store = _store(project_id)
    roots = _roots(store, name)
    existing = [root for root in roots if root.exists()]
    if not existing:
        raise HTTPException(status_code=404, detail="Module not found")
    for root in existing:
        shutil.rmtree(root)
    return {"status": "deleted", "module_id": name}
