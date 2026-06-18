"""
设备管理模块 — API 测试用例

SOP: 与 UI 用例并行
  - UI: page/equipment_page/EquipmentPage.py (UI 操作)
  - API: script/equipment/test_api_equipment.py (接口验证)

覆盖: CRUD + 列表筛选 + 批量操作

Fixture:
  api_client（来自 conftest.py，module 级）：已认证 API 客户端
  created_equipment（function 级）：创建测试设备 + 自动清理
"""
import os
import sys
import time
import pytest
import allure
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base.api_base import AJSystemAPI


@pytest.fixture(scope="function")
def created_equipment(api_client):
    """创建测试设备（测试后清理）。"""
    equipment = api_client.create_equipment(
        name="Test Equipment",
        code="TEST-001",
        type="machinery",
    )
    yield equipment
    # 清理
    try:
        api_client.delete_equipment(equipment.get("id"))
    except Exception:
        pass


class TestEquipmentAPI:
    """设备管理 API 用例。"""

    @pytest.mark.smoke
    @allure.epic("设备管理")
    @allure.feature("设备列表")
    @allure.story("查询接口")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_equipment_list(self, api_client):
        """获取设备列表 — 接口可用性验证。"""
        with allure.step("调用 GET /api/equipment"):
            resp = api_client.get_equipment_list(page=1, page_size=20)

        with allure.step("验证响应状态"):
            assert resp.code == 200, f"Expected 200, got {resp.code}: {resp.message}"
            assert isinstance(resp.data, dict), "Response data should be dict"

        with allure.step("验证列表结构"):
            assert "items" in resp.data, "Missing 'items' in response"
            assert "total" in resp.data, "Missing 'total' in response"

    @pytest.mark.smoke
    @allure.epic("设备管理")
    @allure.feature("设备列表")
    @allure.story("分页功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_equipment_list_pagination(self, api_client):
        """分页参数生效验证。"""
        with allure.step("第 1 页，每页 5 条"):
            resp1 = api_client.get_equipment_list(page=1, page_size=5)
            assert len(resp1.data.get("items", [])) <= 5

        with allure.step("第 2 页，每页 5 条"):
            resp2 = api_client.get_equipment_list(page=2, page_size=5)

        with allure.step("验证分页数据不重复"):
            items1 = [item.get("id") for item in resp1.data.get("items", [])]
            items2 = [item.get("id") for item in resp2.data.get("items", [])]
            assert len(set(items1) & set(items2)) == 0, "Pagination data overlaps"

    @pytest.mark.smoke
    @allure.epic("设备管理")
    @allure.feature("设备新增")
    @allure.story("创建设备")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_equipment_success(self, api_client):
        """新增设备 — 成功用例。"""
        payload = {
            "name": "New Equipment",
            "code": f"TEST-{int(time.time())}",
            "type": "machinery",
            "status": "active",
        }

        with allure.step(f"创建设备: {payload['name']}"):
            equipment = api_client.create_equipment(**payload)

        with allure.step("验证返回字段"):
            assert equipment.get("id"), "Missing equipment id"
            assert equipment.get("name") == payload["name"]
            assert equipment.get("code") == payload["code"]

        with allure.step("清理"):
            api_client.delete_equipment(equipment["id"])

    @pytest.mark.smoke
    @allure.epic("设备管理")
    @allure.feature("设备新增")
    @allure.story("校验规则")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_equipment_missing_name(self, api_client):
        """新增设备 — 缺少必填字段。"""
        payload = {
            "code": "TEST-002",
            "type": "machinery",
        }

        with allure.step("创建设备（缺 name）"):
            with pytest.raises(Exception) as exc:
                api_client.create_equipment(**payload)

        with allure.step("验证错误信息"):
            assert "name" in str(exc.value).lower() or "required" in str(exc.value).lower()

    @pytest.mark.smoke
    @allure.epic("设备管理")
    @allure.feature("设备编辑")
    @allure.story("更新设备")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_equipment(self, api_client, created_equipment):
        """编辑设备。"""
        equipment_id = created_equipment["id"]
        update_data = {
            "name": "Updated Equipment",
            "status": "inactive",
        }

        with allure.step(f"更新设备 {equipment_id}"):
            updated = api_client.update_equipment(equipment_id, **update_data)

        with allure.step("验证字段已更新"):
            assert updated.get("name") == update_data["name"]
            assert updated.get("status") == update_data["status"]

    @pytest.mark.smoke
    @allure.epic("设备管理")
    @allure.feature("设备删除")
    @allure.story("删除设备")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_equipment(self, api_client):
        """删除设备。"""
        # 先创建
        equipment = api_client.create_equipment(
            name="To Delete",
            code="TEST-DELETE",
            type="machinery",
        )
        equipment_id = equipment["id"]

        with allure.step(f"删除设备 {equipment_id}"):
            api_client.delete_equipment(equipment_id)

        with allure.step("验证已删除"):
            with pytest.raises(Exception):  # 404 或业务异常
                api_client.get_equipment(equipment_id)

    @pytest.mark.smoke
    @allure.epic("设备管理")
    @allure.feature("设备查询")
    @allure.story("按名称搜索")
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_equipment_by_name(self, api_client, created_equipment):
        """按名称搜索设备。"""
        search_key = created_equipment["name"][:3]  # 前 3 个字

        with allure.step(f"搜索: '{search_key}'"):
            resp = api_client.get_equipment_list(search=search_key)

        with allure.step("验证搜索结果"):
            items = resp.data.get("items", [])
            assert len(items) > 0, "Search returned no results"
            # 至少有一个包含搜索词的结果
            assert any(search_key in item.get("name", "") for item in items)


if __name__ == "__main__":
    import time
    pytest.main(["-v", "-s", __file__, "--alluredir=allure-results"])
