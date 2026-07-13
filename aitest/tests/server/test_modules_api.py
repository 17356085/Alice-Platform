from pathlib import Path

import pytest

import aitest.server.api.modules_v1 as modules_api


class FakeArtifactStore:
    def __init__(self, project_id: str):
        self.primary = Path(FakeArtifactStore.root) / "tlo" / "knowledge" / "modules"
        self._modules_dir = Path(FakeArtifactStore.root) / "legacy" / "modules"

    def path(self, name: str) -> Path:
        return self.primary / name

    def _get_module_search_dirs(self):
        return [self.primary, self._modules_dir]

    def list_modules(self):
        return sorted({p.name for root in self._get_module_search_dirs() if root.exists() for p in root.iterdir() if p.is_dir()})

    def list_pages(self, name: str):
        pages = set()
        for root in self._get_module_search_dirs():
            pages_dir = root / name / "pages"
            if pages_dir.exists():
                pages.update(p.name for p in pages_dir.iterdir() if p.is_dir())
        return sorted(pages)


@pytest.mark.asyncio
async def test_module_crud_is_persistent_and_dual_path(monkeypatch, tmp_path):
    FakeArtifactStore.root = tmp_path
    monkeypatch.setattr(modules_api, "ArtifactStore", FakeArtifactStore)

    created = await modules_api.create_module(modules_api.ModuleCreateRequest(name="billing", description="Billing"), "demo")
    assert created["status"] == "created"
    assert created["module"]["name"] == "billing"
    assert (tmp_path / "tlo/knowledge/modules/billing/pages").is_dir()
    assert (tmp_path / "legacy/modules/billing/pages").is_dir()

    listed = await modules_api.list_modules("demo")
    assert [item["name"] for item in listed["modules"]] == ["billing"]

    updated = await modules_api.update_module("billing", modules_api.ModuleUpdateRequest(name="invoices", description="Invoices"), "demo")
    assert updated["module"]["name"] == "invoices"
    assert (tmp_path / "tlo/knowledge/modules/invoices/module.json").read_text(encoding="utf-8").find("Invoices") >= 0

    deleted = await modules_api.delete_module("invoices", "demo")
    assert deleted["status"] == "deleted"
    assert not (tmp_path / "tlo/knowledge/modules/invoices").exists()
    assert not (tmp_path / "legacy/modules/invoices").exists()


@pytest.mark.asyncio
async def test_module_name_rejects_path_traversal(monkeypatch, tmp_path):
    FakeArtifactStore.root = tmp_path
    monkeypatch.setattr(modules_api, "ArtifactStore", FakeArtifactStore)

    with pytest.raises(Exception) as error:
        await modules_api.create_module(modules_api.ModuleCreateRequest(name="../escape"), "demo")
    assert getattr(error.value, "status_code", None) == 422


@pytest.mark.asyncio
async def test_page_config_crud_is_persistent_and_dual_path(monkeypatch, tmp_path):
    FakeArtifactStore.root = tmp_path
    monkeypatch.setattr(modules_api, "ArtifactStore", FakeArtifactStore)

    await modules_api.create_module(modules_api.ModuleCreateRequest(name="catalog"), "demo")
    created = await modules_api.create_module_page(
        "catalog",
        modules_api.PageCreateRequest(
            name="product-list",
            description="Product list",
            url="https://example.test/products",
            config={"requires_auth": True},
            locators={"search": "[data-testid=search]"},
            execution={"wait_for": ["search"], "actions": [{"action": "click", "target": "search"}]},
            enabled=True,
        ),
        "demo",
    )
    assert created["status"] == "created"
    assert created["page"]["description"] == "Product list"
    assert created["page"]["url"] == "https://example.test/products"
    assert created["page"]["config"] == {"requires_auth": True}
    assert created["page"]["locators"] == {"search": "[data-testid=search]"}
    assert created["page"]["execution"]["wait_for"] == ["search"]
    assert (tmp_path / "tlo/knowledge/modules/catalog/pages/product-list/page.json").exists()
    assert (tmp_path / "legacy/modules/catalog/pages/product-list/page.json").exists()

    listed = await modules_api.list_module_pages("catalog", "demo")
    assert [page["name"] for page in listed["pages"]] == ["product-list"]

    updated = await modules_api.update_module_page(
        "catalog",
        "product-list",
        modules_api.PageUpdateRequest(
            name="products",
            description="Products",
            url="https://example.test/products-v2",
            config={"requires_auth": False},
            locators={"search": "#search"},
            execution={"actions": [{"action": "fill", "target": "search", "value": "blue"}]},
            enabled=False,
        ),
        "demo",
    )
    assert updated["page"]["name"] == "products"
    assert updated["page"]["description"] == "Products"
    assert updated["page"]["url"] == "https://example.test/products-v2"
    assert updated["page"]["config"] == {"requires_auth": False}
    assert updated["page"]["locators"] == {"search": "#search"}
    assert updated["page"]["execution"]["actions"][0]["action"] == "fill"
    assert updated["page"]["enabled"] is False

    deleted = await modules_api.delete_module_page("catalog", "products", "demo")
    assert deleted["status"] == "deleted"
    assert not (tmp_path / "tlo/knowledge/modules/catalog/pages/products").exists()
    assert not (tmp_path / "legacy/modules/catalog/pages/products").exists()


def test_page_config_rejects_unsupported_locator_strategy():
    with pytest.raises(ValueError, match="unsupported strategy"):
        modules_api.PageCreateRequest(
            name="products",
            locators={"submit": {"strategy": "regex", "value": "button"}},
        )

    with pytest.raises(ValueError, match="requires a non-empty value"):
        modules_api.PageUpdateRequest(
            locators={"submit": {"strategy": "role", "value": ""}},
        )

    with pytest.raises(ValueError, match="requires target"):
        modules_api.PageCreateRequest(
            name="products",
            execution={"actions": [{"action": "click"}]},
        )
