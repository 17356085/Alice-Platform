# alice-engine SDK PyPI 发布指南

## 前置条件

1. **Python 3.11+** 环境
2. **PyPI 账号** (https://pypi.org/account/register/)
3. **API Token** (https://pypi.org/manage/account/token/)
4. **构建工具**:
   ```bash
   pip install build twine
   ```

---

## 发布流程

### 1. 版本号更新

编辑 `packages/alice-engine/pyproject.toml`:

```toml
[project]
name = "alice-engine"
version = "0.1.0"  # 修改为目标版本
```

版本规则（Semantic Versioning）:
- **0.1.0** - 首次发布
- **0.1.1** - 补丁（bug 修复）
- **0.2.0** - 小版本（新功能）
- **1.0.0** - 大版本（稳定 API）

---

### 2. 构建分发包

```bash
cd packages/alice-engine

# 清理旧构建
rm -rf dist/ build/ *.egg-info

# 构建源码分发 + wheel
python -m build

# 验证构建产物
ls -lh dist/
# 预期输出:
#   alice_engine-0.1.0-py3-none-any.whl
#   alice_engine-0.1.0.tar.gz
```

---

### 3. 本地验证

```bash
# 创建虚拟环境
python3.11 -m venv /tmp/alice-test
source /tmp/alice-test/bin/activate

# 安装本地构建
pip install dist/alice_engine-0.1.0-py3-none-any.whl

# 验证导入
python -c "
from alice_engine import Engine, Project
from alice_engine.extensions import KnowledgeExtension, MemoryExtension
from alice_engine.providers import get_provider
print('✅ SDK 导入成功')
"

# 运行测试（如果有）
pytest tests/

deactivate
```

---

### 4. 上传到 TestPyPI（推荐首次）

TestPyPI 是测试环境，允许反复试验。

```bash
# 配置 TestPyPI API token
# 创建 ~/.pypirc:
cat > ~/.pypirc << 'EOF'
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PRODUCTION_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TEST_TOKEN_HERE
EOF

chmod 600 ~/.pypirc

# 上传到 TestPyPI
python -m twine upload --repository testpypi dist/*

# 验证
pip install --index-url https://test.pypi.org/simple/ alice-engine==0.1.0
```

---

### 5. 上传到生产 PyPI

**⚠️ 警告**: PyPI 不允许覆盖已发布版本，确认无误后再执行。

```bash
# 上传到 PyPI
python -m twine upload dist/*

# 输入提示:
#   Enter your username: __token__
#   Enter your password: [paste API token]

# 验证
pip install alice-engine==0.1.0
```

---

## 发布检查清单

### 发布前

- [ ] 所有测试通过 (`pytest`)
- [ ] 零平台依赖 (`python standalone_sdk_test.py`)
- [ ] `pyproject.toml` 版本号正确
- [ ] `README.md` 更新（安装、快速开始）
- [ ] `CHANGELOG.md` 更新（本版本变更）
- [ ] Git tag 创建: `git tag v0.1.0 && git push --tags`

### 发布后

- [ ] PyPI 页面正常: https://pypi.org/project/alice-engine/
- [ ] 文档链接有效
- [ ] 依赖声明正确（安装不报错）
- [ ] GitHub Release 创建
- [ ] 通知用户/团队

---

## pyproject.toml 配置检查

确保以下字段完整：

```toml
[project]
name = "alice-engine"
version = "0.1.0"
description = "测试自动化 Agent Native 执行引擎"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [
    { name = "Alice Team", email = "dev@example.com" }
]
keywords = ["testing", "automation", "agent", "llm"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Testing",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "langgraph>=0.2.0",
    "langchain-core>=0.3.0",
    "anthropic>=0.40.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "black>=24.0.0",
    "ruff>=0.6.0",
]

[project.urls]
Homepage = "https://github.com/your-org/alice-engine"
Documentation = "https://docs.example.com"
Repository = "https://github.com/your-org/alice-engine"
"Bug Tracker" = "https://github.com/your-org/alice-engine/issues"

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]
include = ["alice_engine*"]
exclude = ["tests*", "*.pyc", "__pycache__"]
```

---

## 常见问题

### Q1: 上传失败 "403 Forbidden"

**原因**: API token 无效或权限不足。

**解决**:
1. 重新生成 PyPI API token
2. 确认 token 有 "Upload packages" 权限
3. 检查 `~/.pypirc` 配置格式

---

### Q2: 导入失败 "No module named 'alice_engine'"

**原因**: 包结构或 `pyproject.toml` 配置错误。

**解决**:
```bash
# 检查构建产物
unzip -l dist/alice_engine-0.1.0-py3-none-any.whl
# 应该看到 alice_engine/ 目录

# 检查 MANIFEST.in（如需）
cat MANIFEST.in
```

---

### Q3: 依赖冲突

**原因**: 依赖版本范围过严格。

**解决**: 放宽版本约束
```toml
# 过严格
dependencies = ["langgraph==0.2.0"]

# 推荐
dependencies = ["langgraph>=0.2.0,<0.3"]
```

---

### Q4: TestPyPI 依赖解析失败

**原因**: TestPyPI 不包含所有 PyPI 包。

**解决**: 混合安装
```bash
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    alice-engine
```

---

## 版本发布记录模板

创建 `CHANGELOG.md`:

```markdown
# Changelog

## [0.1.0] - 2026-07-09

### Added
- 初始发布
- Engine 核心执行引擎
- 4 个 Extensions: Audit, Complexity, Knowledge, Memory
- 5 个 LLM Providers: Claude, OpenAI, DeepSeek, MiMo, Mock
- Runtime Capabilities: KnowledgeStore, MemoryStore
- 零平台依赖架构

### Changed
- N/A

### Fixed
- N/A

### Security
- N/A
```

---

## 自动化发布（可选）

使用 GitHub Actions:

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install build tools
        run: pip install build twine
      
      - name: Build package
        run: |
          cd packages/alice-engine
          python -m build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: |
          cd packages/alice-engine
          python -m twine upload dist/*
```

---

## 下一步

发布后：
1. 更新主项目文档，指向 PyPI 安装方式
2. 创建使用示例项目
3. 编写 API 参考文档
4. 建立社区反馈渠道

---

**最后检查**: 在全新环境测试安装

```bash
docker run -it python:3.11-slim bash
pip install alice-engine
python -c "from alice_engine import Engine; print('✅ OK')"
```
