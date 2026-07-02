"""Project 单元测试。"""

import pytest
from alice_engine import Project, ProjectNotFoundError


class TestProject:
    """Project 测试。"""

    def test_project_init(self, tmp_path):
        """测试 Project 初始化。"""
        (tmp_path / ".tlo").mkdir()
        (tmp_path / ".tlo" / "project.yaml").write_text("name: test\nurl: http://test.com")

        project = Project(tmp_path)
        assert project.name == "test"
        assert project.config.url == "http://test.com"

    def test_project_not_found(self, tmp_path):
        """测试项目不存在。"""
        with pytest.raises(ProjectNotFoundError):
            Project(tmp_path / "nonexistent")

    def test_project_modules(self, tmp_path):
        """测试模块发现。"""
        (tmp_path / ".tlo").mkdir()
        (tmp_path / ".tlo" / "project.yaml").write_text("name: test\nmodules:\n  - mod1\n  - mod2")

        project = Project(tmp_path)
        modules = project.modules
        assert "mod1" in modules
        assert "mod2" in modules

    def test_project_validate(self, tmp_path):
        """测试项目验证。"""
        (tmp_path / ".tlo").mkdir()
        (tmp_path / ".tlo" / "project.yaml").write_text("name: test\nurl: http://test.com")

        project = Project(tmp_path)
        validation = project.validate()
        assert validation.valid is True
