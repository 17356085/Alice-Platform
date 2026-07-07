"""Project 单元测试。"""

import pytest
from alice_engine import Project, ProjectNotFoundError
from alice_engine.behavior import load_behavior_pack, resolve_governance_pack_path


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

    def test_project_governance_path_prefers_env_pack(self, tmp_path, monkeypatch):
        (tmp_path / ".tlo").mkdir()
        (tmp_path / ".tlo" / "project.yaml").write_text("name: test\nurl: http://test.com")
        env_pack = tmp_path / "env-governance"
        (env_pack / "skills").mkdir(parents=True)

        monkeypatch.setenv("ENGINE_GOVERNANCE_PATH", str(env_pack))

        project = Project(tmp_path)
        assert project.governance_path == env_pack.resolve()


def test_load_behavior_pack_uses_env_when_not_explicitly_overridden(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    project_root.mkdir()
    local_pack = project_root / "governance"
    (local_pack / "skills").mkdir(parents=True)
    env_pack = tmp_path / "env-governance"
    (env_pack / "skills-dev").mkdir(parents=True)

    monkeypatch.setenv("ENGINE_GOVERNANCE_PATH", str(env_pack))

    resolved = resolve_governance_pack_path(project_root=project_root)
    pack = load_behavior_pack(None)

    assert resolved == env_pack.resolve()
    assert pack.root == env_pack.resolve()
