# PyPI 发布执行手册

**状态**: ✅ 包已构建，待上传  
**日期**: 2026-07-09  
**执行者**: 需用户提供 PyPI 凭证

---

## 当前状态

三个 SDK 包已成功构建并通过完整性验证:

| 包 | 版本 | Wheel 大小 | Source 大小 | 状态 |
|----|------|-----------|------------|------|
| **alice-discovery** | 0.1.0 | 42 KB | 39 KB | ✅ 已构建 |
| **alice-engine** | 1.0.0 | 238 KB | 196 KB | ✅ 已构建 |
| **alice-governance** | 1.0.0 | 123 KB | 91 KB | ✅ 已构建 |

**产物位置**:
```
packages/alice-discovery/dist/
  alice_discovery-0.1.0-py3-none-any.whl
  alice_discovery-0.1.0.tar.gz

packages/alice-engine/dist/
  alice_engine-1.0.0-py3-none-any.whl
  alice_engine-1.0.0.tar.gz

packages/alice-governance/dist/
  alice_governance-1.0.0-py3-none-any.whl
  alice_governance-1.0.0.tar.gz
```

---

## 前置条件

### 1. PyPI 账号

访问 https://pypi.org/account/register/ 注册账号（如已有则跳过）。

### 2. API Token

登录 PyPI → Account Settings → API tokens → "Add API token"

- **Token name**: `alice-sdk-upload`（或任意名称）
- **Scope**: "Entire account"（首次发布）或 "Project: alice-*"（后续更新）
- **保存 Token**: 形如 `pypi-AgEIcHlwaS5vcmc...`（仅显示一次，务必保存）

### 3. 安装 twine

```bash
pip install twine --break-system-packages
```

---

## 发布流程

### Step 1: TestPyPI 试发布（推荐）

TestPyPI 是 PyPI 的测试环境，可以安全验证发布流程，不影响生产。

#### 1.1 注册 TestPyPI 账号

访问 https://test.pypi.org/account/register/（与 PyPI 独立账号体系）

#### 1.2 创建 TestPyPI API Token

登录 TestPyPI → Account Settings → API tokens → "Add API token"

- **Token name**: `alice-sdk-test`
- **Scope**: "Entire account"
- **保存 Token**: `pypi-AgEIcHlwaS5vcmc...`

#### 1.3 上传到 TestPyPI

```bash
cd packages/alice-discovery
twine upload --repository testpypi dist/*

# 提示输入:
# Username: __token__
# Password: <粘贴 TestPyPI Token>
```

重复操作 `alice-engine` 和 `alice-governance`。

#### 1.4 验证 TestPyPI 安装

```bash
# 从 TestPyPI 安装（需要 Python 3.11+）
pip install --index-url https://test.pypi.org/simple/ alice-discovery

# 验证导入
python3 -c "from alice_discovery import SourceDiscoveryPipeline; print('✅ OK')"
```

**预期结果**: 安装成功，导入无报错。

---

### Step 2: 生产 PyPI 发布

确认 TestPyPI 验证通过后，执行生产发布。

#### 2.1 上传到 PyPI

```bash
cd packages/alice-discovery
twine upload dist/*

# 提示输入:
# Username: __token__
# Password: <粘贴 PyPI Token>
```

**输出示例**:
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading alice_discovery-0.1.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 42.0/42.0 kB • 00:01
Uploading alice_discovery-0.1.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 39.0/39.0 kB • 00:01

View at:
https://pypi.org/project/alice-discovery/0.1.0/
```

重复操作 `alice-engine` 和 `alice-governance`:

```bash
cd ../alice-engine
twine upload dist/*

cd ../alice-governance
twine upload dist/*
```

#### 2.2 验证生产安装

```bash
# 从 PyPI 安装（需要 Python 3.11+）
pip install alice-discovery
pip install alice-engine
pip install alice-governance

# 验证导入
python3 -c "
from alice_discovery import SourceDiscoveryPipeline
from alice_engine import Engine, Project
from alice_governance import get_pack_path
print('✅ All OK')
"
```

---

## 常见问题

### Q1: `403 Forbidden` 错误

**原因**: Token 权限不足或项目已存在。

**解决**:
1. 确认使用 `__token__` 作为用户名（不是你的 PyPI 用户名）
2. 确认 Token Scope 包含该项目（首次发布需 "Entire account"）
3. 如果项目已存在且不是你的，需更换包名（在 `pyproject.toml` 中修改 `name`）

---

### Q2: `Package already exists` 错误

**原因**: 该版本号已发布（PyPI 不允许覆盖已发布版本）。

**解决**:
1. 修改 `pyproject.toml` 中 `version`（如 `0.1.0` → `0.1.1`）
2. 重新构建: `python3 -m build`
3. 上传新版本: `twine upload dist/*`

---

### Q3: TestPyPI 安装失败 `No matching distribution found`

**原因**: TestPyPI 的依赖包可能不完整（它不镜像所有 PyPI 包）。

**解决**:
```bash
# 从 PyPI 获取依赖，从 TestPyPI 获取主包
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  alice-discovery
```

---

### Q4: 如何更新已发布的包？

**流程**:
1. 修改代码
2. 更新 `pyproject.toml` 中 `version`（如 `1.0.0` → `1.0.1`）
3. 更新 `CHANGELOG.md`（记录变更）
4. 重新构建: `python3 -m build`
5. 上传: `twine upload dist/*`

**语义化版本规范**:
- **补丁版本** (`1.0.0` → `1.0.1`): Bug 修复
- **次版本** (`1.0.0` → `1.1.0`): 新功能（向后兼容）
- **主版本** (`1.0.0` → `2.0.0`): 破坏性变更

---

## 安全注意事项

### 1. Token 保护

- ❌ 不要将 Token 提交到 Git 仓库
- ❌ 不要在脚本中硬编码 Token
- ✅ 使用 `.pypirc` 配置文件（添加到 `.gitignore`）:

```ini
[pypi]
username = __token__
password = pypi-AgEI...

[testpypi]
username = __token__
password = pypi-AgEI...
```

配置后可简化上传命令:
```bash
twine upload --repository testpypi dist/*  # 自动读取 .pypirc
twine upload dist/*                         # 自动读取 .pypirc
```

### 2. 双因素认证

启用 PyPI 账号的 2FA（推荐）:
- 登录 PyPI → Account Settings → Two Factor Authentication
- 使用 API Token 上传时无需 2FA 输入

---

## CI/CD 自动化（可选）

### GitHub Actions 示例

创建 `.github/workflows/publish-pypi.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      
      - name: Build packages
        run: |
          cd packages/alice-discovery && python -m build
          cd ../alice-engine && python -m build
          cd ../alice-governance && python -m build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: |
          twine upload packages/*/dist/*
```

**配置**:
1. GitHub repo → Settings → Secrets → New repository secret
2. Name: `PYPI_API_TOKEN`
3. Value: 粘贴 PyPI Token

**触发**: 每次在 GitHub 发布新 Release 时自动发布到 PyPI。

---

## 发布后验证清单

### ✅ PyPI 页面

- [ ] 访问 https://pypi.org/project/alice-discovery/ 确认页面显示正常
- [ ] 访问 https://pypi.org/project/alice-engine/ 确认页面显示正常
- [ ] 访问 https://pypi.org/project/alice-governance/ 确认页面显示正常
- [ ] README 渲染正确（PyPI 自动渲染 `README.md`）
- [ ] 版本号、作者、许可证信息正确

### ✅ 安装验证

```bash
# 创建干净虚拟环境
python3 -m venv /tmp/test-pypi
source /tmp/test-pypi/bin/activate

# 安装三个包
pip install alice-discovery alice-engine alice-governance

# 验证导入
python -c "
from alice_discovery import SourceDiscoveryPipeline
from alice_engine import Engine, Project
from alice_engine.extensions import KnowledgeExtension, MemoryExtension
from alice_governance import get_pack_path
print('✅ All imports successful')
"

# 清理
deactivate
rm -rf /tmp/test-pypi
```

### ✅ 文档更新

- [ ] 更新主 README.md 添加 PyPI 安装说明
- [ ] 更新 `docs/architecture/sdk-migration-final-summary.md` 标记 PyPI 发布完成
- [ ] 在项目文档中添加 PyPI 徽章:

```markdown
[![PyPI - alice-discovery](https://img.shields.io/pypi/v/alice-discovery)](https://pypi.org/project/alice-discovery/)
[![PyPI - alice-engine](https://img.shields.io/pypi/v/alice-engine)](https://pypi.org/project/alice-engine/)
[![PyPI - alice-governance](https://img.shields.io/pypi/v/alice-governance)](https://pypi.org/project/alice-governance/)
```

---

## 下次发布

当需要发布新版本时:

```bash
# 1. 更新版本号
vim packages/alice-discovery/pyproject.toml  # version = "0.1.1"

# 2. 更新 CHANGELOG
vim packages/alice-discovery/CHANGELOG.md

# 3. 提交变更
git add packages/alice-discovery/
git commit -m "Bump alice-discovery to 0.1.1"

# 4. 重新构建
cd packages/alice-discovery
rm -rf dist/ build/ *.egg-info
python3 -m build

# 5. 上传
twine upload dist/*
```

---

## 联系与支持

- **PyPI 支持**: https://pypi.org/help/
- **Twine 文档**: https://twine.readthedocs.io/
- **问题反馈**: 项目 GitHub Issues

---

**发布完成标志**: 当三个包在 PyPI 页面可见且 `pip install` 成功时，Task 2 (PyPI 发布) 完成 ✅
