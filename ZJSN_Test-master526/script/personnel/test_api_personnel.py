"""
人事管理模块 — API 测试用例

SOP: 与 UI 用例并行
  - UI: script/personnel/test_employee*.py (UI 操作)
  - API: script/personnel/test_api_personnel.py (接口验证)

覆盖: 员工 CRUD + 岗位 CRUD
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
def created_post(api_client):
    """创建测试岗位（测试后清理）。"""
    post = api_client.create_post(
        name="Test Post",
        description="Test post for API testing",
    )
    yield post
    try:
        api_client.delete_post(post.get("id"))
    except Exception:
        pass


@pytest.fixture(scope="function")
def created_employee(api_client, created_post):
    """创建测试员工（测试后清理）。"""
    employee = api_client.create_employee(
        name="Test Employee",
        post_id=created_post.get("id"),
    )
    yield employee
    try:
        api_client.delete_employee(employee.get("id"))
    except Exception:
        pass


class TestPersonnelAPI:
    """人事管理 API 用例。"""

    @pytest.mark.smoke
    @allure.epic("人事管理")
    @allure.feature("岗位管理")
    @allure.story("查询接口")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_posts_list(self, api_client):
        """获取岗位列表 — 接口可用性验证。"""
        with allure.step("调用 GET /api/v1/posts"):
            resp = api_client.get_posts(page=1, page_size=20)

        with allure.step("验证响应状态"):
            assert resp.code == 200, f"Expected 200, got {resp.code}: {resp.message}"
            assert isinstance(resp.data, dict), "Response data should be dict"

        with allure.step("验证列表结构"):
            assert "items" in resp.data, "Missing 'items' in response"
            assert "total" in resp.data, "Missing 'total' in response"

    @pytest.mark.smoke
    @allure.epic("人事管理")
    @allure.feature("岗位管理")
    @allure.story("新增岗位")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_post_success(self, api_client, test_data_cleanup):
        """创建岗位 — 成功用例。"""
        payload = {
            "name": f"Test Post {int(time.time())}",
            "description": "Auto-generated test post",
        }

        with allure.step(f"创建岗位: {payload['name']}"):
            post = api_client.create_post(**payload)

        with allure.step("验证返回字段"):
            assert post.get("id"), "Missing post id"
            assert post.get("name") == payload["name"]

        with allure.step("清理"):
            test_data_cleanup.add("post", post["id"])

    @pytest.mark.smoke
    @allure.epic("人事管理")
    @allure.feature("岗位管理")
    @allure.story("编辑岗位")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_post(self, api_client, created_post):
        """编辑岗位。"""
        post_id = created_post["id"]
        update_data = {"description": "Updated description"}

        with allure.step(f"更新岗位 {post_id}"):
            updated = api_client.update_post(post_id, **update_data)

        with allure.step("验证字段已更新"):
            assert updated.get("description") == update_data["description"]

    @pytest.mark.smoke
    @allure.epic("人事管理")
    @allure.feature("岗位管理")
    @allure.story("删除岗位")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_post(self, api_client):
        """删除岗位。"""
        post = api_client.create_post(
            name="To Delete",
            description="Will be deleted",
        )
        post_id = post["id"]

        with allure.step(f"删除岗位 {post_id}"):
            api_client.delete_post(post_id)

        with allure.step("验证已删除"):
            with pytest.raises(Exception):
                api_client.get_post(post_id)

    @pytest.mark.smoke
    @allure.epic("人事管理")
    @allure.feature("员工管理")
    @allure.story("查询接口")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_employees_list(self, api_client):
        """获取员工列表 — 接口可用性验证。"""
        with allure.step("调用 GET /api/v1/employees"):
            resp = api_client.get_employees(page=1, page_size=20)

        with allure.step("验证响应状态"):
            assert resp.code == 200, f"Expected 200, got {resp.code}: {resp.message}"
            assert isinstance(resp.data, dict), "Response data should be dict"

        with allure.step("验证列表结构"):
            assert "items" in resp.data, "Missing 'items' in response"
            assert "total" in resp.data, "Missing 'total' in response"

    @pytest.mark.smoke
    @allure.epic("人事管理")
    @allure.feature("员工管理")
    @allure.story("新增员工")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_employee_success(self, api_client, created_post, test_data_cleanup):
        """创建员工 — 成功用例。"""
        payload = {
            "name": f"Test Employee {int(time.time())}",
            "post_id": created_post["id"],
        }

        with allure.step(f"创建员工: {payload['name']}"):
            employee = api_client.create_employee(**payload)

        with allure.step("验证返回字段"):
            assert employee.get("id"), "Missing employee id"
            assert employee.get("name") == payload["name"]

        with allure.step("清理"):
            test_data_cleanup.add("employee", employee["id"])

    @pytest.mark.smoke
    @allure.epic("人事管理")
    @allure.feature("员工管理")
    @allure.story("编辑员工")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_employee(self, api_client, created_employee):
        """编辑员工。"""
        employee_id = created_employee["id"]
        update_data = {"name": "Updated Employee Name"}

        with allure.step(f"更新员工 {employee_id}"):
            updated = api_client.update_employee(employee_id, **update_data)

        with allure.step("验证字段已更新"):
            assert updated.get("name") == update_data["name"]

    @pytest.mark.smoke
    @allure.epic("人事管理")
    @allure.feature("员工管理")
    @allure.story("删除员工")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_employee(self, api_client, created_post):
        """删除员工。"""
        employee = api_client.create_employee(
            name="To Delete",
            post_id=created_post["id"],
        )
        employee_id = employee["id"]

        with allure.step(f"删除员工 {employee_id}"):
            api_client.delete_employee(employee_id)

        with allure.step("验证已删除"):
            with pytest.raises(Exception):
                api_client.get_employee(employee_id)


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__, "--alluredir=allure-results"])
