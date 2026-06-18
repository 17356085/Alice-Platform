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
    """创建测试岗位，通过名称搜索获取 ID（API 创建不返回对象）。"""
    post_name = f"TestPost_{int(time.time())}"
    api_client.create_post(postName=post_name)
    # 按名搜索获取创建后的 ID
    resp = api_client.get_posts(page=1, page_size=50)
    records = resp.data.get("records", [])
    post = next((r for r in records if r.get("postName") == post_name), None)
    if not post:
        pytest.skip(f"Created post '{post_name}' not found in list")
    yield post
    try:
        api_client.delete_post(post["id"])
    except Exception:
        pass


@pytest.fixture(scope="function")
def created_employee(api_client, created_post):
    """创建测试员工，通过名称搜索获取 ID。"""
    emp_name = f"TestEmp_{int(time.time())}"
    result = api_client.create_employee(realName=emp_name, postId=created_post["id"])
    # 创建可能返回字符串或对象
    if isinstance(result, str):
        resp = api_client.get_employees(page=1, page_size=100)
        records = resp.data.get("records", [])
        employee = next((r for r in records if r.get("realName") == emp_name), None)
    else:
        employee = result
    if not employee:
        pytest.skip(f"Created employee '{emp_name}' not found in list")
    yield employee
    try:
        api_client.delete_employee(employee["id"])
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
            assert "records" in resp.data, "Missing 'records' in response"
            assert "total" in resp.data, "Missing 'total' in response"

    @pytest.mark.smoke
    @allure.epic("人事管理")
    @allure.feature("岗位管理")
    @allure.story("新增岗位")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_post_success(self, api_client, test_data_cleanup):
        """创建岗位 — 成功用例。"""
        post_name = f"Test Post {int(time.time())}"
        payload = {"postName": post_name}

        with allure.step(f"创建岗位: {post_name}"):
            result = api_client.create_post(**payload)

        with allure.step("验证创建成功"):
            assert result is not None, "Create should return success message"
            # API returns success string, not object

        with allure.step("通过搜索确认已创建"):
            resp = api_client.get_posts(page=1, page_size=50)
            records = resp.data.get("records", [])
            created = next((r for r in records if r.get("postName") == post_name), None)
            assert created is not None, f"Post '{post_name}' should exist after creation"
            assert created.get("postName") == post_name

        with allure.step("清理"):
            if created:
                test_data_cleanup.add("post", created["id"])

    @pytest.mark.smoke
    @allure.epic("人事管理")
    @allure.feature("岗位管理")
    @allure.story("编辑岗位")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_post(self, api_client, created_post):
        """编辑岗位 — 更新成功。"""
        post_id = created_post["id"]
        new_name = f"Updated_{int(time.time())}"
        update_data = {"postName": new_name}

        with allure.step(f"更新岗位 {post_id} 名称→{new_name}"):
            result = api_client.update_post(post_id, **update_data)

        with allure.step("验证更新结果: API 返回成功"):
            assert result is not None, "Update API should return result"

        with allure.step("通过查询确认名称已变更"):
            updated = api_client.get_post(post_id)
            assert updated.get("postName") == new_name, f"Expected {new_name}, got {updated.get('postName')}"

    @pytest.mark.smoke
    @allure.epic("人事管理")
    @allure.feature("岗位管理")
    @allure.story("删除岗位")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_post(self, api_client):
        """删除岗位 — 软删除后查询不到。"""
        post_name = f"ToDelete_{int(time.time())}"
        api_client.create_post(postName=post_name)

        # 搜索获取 ID
        resp = api_client.get_posts(page=1, page_size=50)
        records = resp.data.get("records", [])
        created = next((r for r in records if r.get("postName") == post_name), None)
        assert created, f"Post '{post_name}' not found after creation"
        post_id = created["id"]

        with allure.step(f"删除岗位 {post_id}"):
            api_client.delete_post(post_id)

        with allure.step("验证已删除: GET 返回 null"):
            result = api_client.get_post(post_id)
            assert result is None or result == {}, f"Deleted post should return null/empty, got: {result}"

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
            assert "records" in resp.data, "Missing 'records' in response"
            assert "total" in resp.data, "Missing 'total' in response"

    @pytest.mark.smoke
    @allure.epic("人事管理")
    @allure.feature("员工管理")
    @allure.story("新增员工")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_employee_success(self, api_client, created_post, test_data_cleanup):
        """创建员工 — 成功用例。"""
        emp_name = f"Test Employee {int(time.time())}"
        payload = {"realName": emp_name, "postId": created_post["id"]}

        with allure.step(f"创建员工: {emp_name}"):
            result = api_client.create_employee(**payload)

        with allure.step("验证创建成功"):
            if isinstance(result, str):
                # API returns success message
                assert result, "Create should return result"
            else:
                assert result.get("id"), "Missing employee id"
                assert result.get("realName") == emp_name

        with allure.step("通过搜索确认已创建"):
            resp = api_client.get_employees(page=1, page_size=100)
            records = resp.data.get("records", [])
            created = next((r for r in records if r.get("realName") == emp_name), None)
            assert created is not None, f"Employee '{emp_name}' should exist after creation"

        with allure.step("清理"):
            if created:
                test_data_cleanup.add("employee", created["id"])

    @pytest.mark.smoke
    @allure.epic("人事管理")
    @allure.feature("员工管理")
    @allure.story("编辑员工")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_employee(self, api_client, created_employee):
        """编辑员工 — 更新 realName 并通过查询确认。"""
        employee_id = created_employee["id"]
        new_name = f"UpdatedEmp_{int(time.time())}"
        update_data = {"realName": new_name}

        with allure.step(f"更新员工 {employee_id}"):
            api_client.update_employee(employee_id, **update_data)

        with allure.step("通过查询确认名称已变更"):
            updated = api_client.get_employee(employee_id)
            assert updated.get("realName") == new_name

    @pytest.mark.smoke
    @allure.epic("人事管理")
    @allure.feature("员工管理")
    @allure.story("删除员工")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_employee(self, api_client, created_post):
        """删除员工。"""
        emp_name = f"ToDeleteEmp_{int(time.time())}"
        api_client.create_employee(realName=emp_name, postId=created_post["id"])

        # 搜索获取 ID
        resp = api_client.get_employees(page=1, page_size=100)
        records = resp.data.get("records", [])
        created = next((r for r in records if r.get("realName") == emp_name), None)
        if not created:
            pytest.skip(f"Employee '{emp_name}' not found — API may be unstable")
        employee_id = created["id"]

        with allure.step(f"删除员工 {employee_id}"):
            api_client.delete_employee(employee_id)

        with allure.step("验证已删除: GET 返回 null"):
            result = api_client.get_employee(employee_id)
            assert result is None or result == {}, f"Deleted employee should return null/empty, got: {result}"


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__, "--alluredir=allure-results"])
