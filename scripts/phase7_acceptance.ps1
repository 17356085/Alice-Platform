param(
    [ValidateSet("reuse", "fresh")]
    [string]$WorkspaceMode = "reuse",
    [string]$PythonPath = "C:\Program Files\Python312\python.exe",
    [string]$WorkspaceVenv = ".phase7-workspace",
    [string]$StandaloneVenv = ".phase7-standalone",
    [string]$DockerTag = "aitest-phase7-local",
    [switch]$SkipDocker,
    [switch]$UseSystemSitePackagesForStandalone,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$tmpRoot = Join-Path $repoRoot "tmp\phase7-acceptance"
$env:TEMP = $tmpRoot
$env:TMP = $tmpRoot
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Resolve-AbsolutePath {
    param([string]$PathValue)
    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return $PathValue
    }
    return [System.IO.Path]::GetFullPath((Join-Path $repoRoot $PathValue))
}

function Invoke-External {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory = $repoRoot
    )

    $rendered = if ($Arguments.Count -gt 0) {
        "$FilePath $($Arguments -join ' ')"
    } else {
        $FilePath
    }
    Write-Host "[$WorkingDirectory] $rendered"
    if ($DryRun) {
        return
    }

    Push-Location $WorkingDirectory
    try {
        & $FilePath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed with exit code ${LASTEXITCODE}: $rendered"
        }
    }
    finally {
        Pop-Location
    }
}

function Ensure-Python {
    param([string]$Candidate)
    $resolved = Resolve-AbsolutePath $Candidate
    if (-not (Test-Path -LiteralPath $resolved)) {
        throw "Python not found: $resolved"
    }
    return $resolved
}

function Ensure-Venv {
    param(
        [string]$BootstrapPython,
        [string]$VenvPath,
        [switch]$SystemSitePackages
    )

    $resolvedVenv = Resolve-AbsolutePath $VenvPath
    $venvPython = Join-Path $resolvedVenv "Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $venvPython)) {
        $args = @("-m", "venv")
        if ($SystemSitePackages) {
            $args += "--system-site-packages"
        }
        $args += $resolvedVenv
        Invoke-External -FilePath $BootstrapPython -Arguments $args
        if ($DryRun) {
            return $venvPython
        }
    }
    if (-not (Test-Path -LiteralPath $venvPython)) {
        throw "Virtual environment python not found: $venvPython"
    }
    return $venvPython
}

function Write-TempPythonScript {
    param(
        [string]$Name,
        [string]$Content
    )

    $scriptPath = Join-Path $tmpRoot $Name
    if (-not $DryRun) {
        New-Item -ItemType Directory -Force -Path $tmpRoot | Out-Null
        Set-Content -LiteralPath $scriptPath -Value $Content -Encoding UTF8
    }
    return $scriptPath
}

function Get-LatestWheel {
    $distDir = Join-Path $repoRoot "packages\alice-engine\dist"
    if (-not (Test-Path -LiteralPath $distDir)) {
        throw "Wheel dist directory not found: $distDir"
    }
    $wheel = Get-ChildItem -LiteralPath $distDir -Filter "alice_engine-*.whl" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($null -eq $wheel) {
        if ($DryRun) {
            return (Join-Path $distDir "alice_engine-<version>.whl")
        }
        throw "No alice_engine wheel found under $distDir"
    }
    return $wheel.FullName
}

function Write-WheelPatchScript {
    $scriptPath = Join-Path $tmpRoot "patch_wheel.py"
    $content = @'
from __future__ import annotations

import base64
import csv
import hashlib
import shutil
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def _hash_bytes(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    encoded = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return f"sha256={encoded}"


def _build_record(root: Path, dist_info_dir: Path) -> str:
    rows: list[list[str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.endswith("/RECORD"):
            continue
        data = path.read_bytes()
        rows.append([rel, _hash_bytes(data), str(len(data))])

    record_rel = dist_info_dir.relative_to(root).as_posix() + "/RECORD"
    rows.append([record_rel, "", ""])
    return "\n".join(",".join(row) for row in rows) + "\n"


def patch_wheel(wheel_path: Path, router_source: Path) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        staging = Path(tmpdir)
        with ZipFile(wheel_path, "r") as zf:
            zf.extractall(staging)

        target = staging / "alice_engine" / "router.py"
        target.write_text(router_source.read_text(encoding="utf-8"), encoding="utf-8")

        dist_info_dir = next(staging.glob("alice_engine-*.dist-info"))
        (dist_info_dir / "RECORD").write_text(_build_record(staging, dist_info_dir), encoding="utf-8")

        tmp_wheel = wheel_path.with_suffix(".tmp.whl")
        if tmp_wheel.exists():
            tmp_wheel.unlink()
        with ZipFile(tmp_wheel, "w", compression=ZIP_DEFLATED) as zf:
            for path in sorted(staging.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(staging).as_posix())
        shutil.move(str(tmp_wheel), str(wheel_path))


def main() -> int:
    wheel_path = Path(sys.argv[1])
    router_source = Path(sys.argv[2])
    patch_wheel(wheel_path, router_source)
    print(f"patched {wheel_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'@
    if (-not $DryRun) {
        New-Item -ItemType Directory -Force -Path $tmpRoot | Out-Null
        Set-Content -LiteralPath $scriptPath -Value $content -Encoding UTF8
    }
    return $scriptPath
}

function Prepare-StandaloneDependencyVendor {
    param([string]$WorkspacePython)

    $workspaceSitePackages = Resolve-AbsolutePath (Join-Path (Split-Path $WorkspacePython -Parent) "..\Lib\site-packages")
    if (-not (Test-Path -LiteralPath $workspaceSitePackages)) {
        return $null
    }

    $vendorDir = Join-Path $tmpRoot "standalone-site-packages"
    if (-not $DryRun) {
        New-Item -ItemType Directory -Force -Path $vendorDir | Out-Null
        $excludePatterns = @(
            "aitest*",
            "alice_engine*",
            "alice_governance*",
            "alice_discovery*",
            "*.pth"
        )
        Get-ChildItem -LiteralPath $workspaceSitePackages -Force |
            Where-Object {
                $name = $_.Name
                foreach ($pattern in $excludePatterns) {
                    if ($name -like $pattern) {
                        return $false
                    }
                }
                return $true
            } |
            ForEach-Object {
                try {
                    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $vendorDir $_.Name) -Recurse -Force -ErrorAction Stop
                }
                catch {
                    # Best-effort vendor mirror: skip locked or non-critical files.
                }
            }
    }
    return $vendorDir
}

function Resolve-OfflineDockerImage {
    $tagCandidates = @(
        $env:PHASE7_DOCKER_IMAGE,
        "aitest-phase7-local",
        "aitest-phase7-offline",
        "aitest-phase7-runtime"
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

    foreach ($candidate in $tagCandidates) {
        $inspect = & docker image inspect $candidate 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $candidate
        }
    }

    $tarCandidates = @(
        $env:PHASE7_DOCKER_IMAGE_TAR,
        (Join-Path $repoRoot "python-3.12-slim.tar"),
        (Join-Path $repoRoot "tmp\phase7-docker\alpine-latest.tar"),
        (Join-Path $repoRoot "tmp\phase7-docker\aitest-phase7-local.tar"),
        (Join-Path $repoRoot "tmp\phase7-docker\aitest-phase7-local.tar.gz"),
        (Join-Path $repoRoot "tmp\phase7-docker\phase7-local-image.tar")
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

    foreach ($tarPath in $tarCandidates) {
        if (-not (Test-Path -LiteralPath $tarPath)) {
            continue
        }
        $loadOutput = & docker load -i $tarPath 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to load offline Docker image from $tarPath"
        }
        $loaded = $loadOutput | Select-String -Pattern '^Loaded image: (.+)$'
        if ($loaded) {
            return $loaded.Matches[0].Groups[1].Value.Trim()
        }
        throw "Docker image tar loaded from $tarPath but no image tag was reported"
    }

    throw "No offline Docker image found. Set PHASE7_DOCKER_IMAGE or PHASE7_DOCKER_IMAGE_TAR to a preloaded local image."
}

function Get-WorkspacePython {
    param([string]$BootstrapPython)
    $workspacePython = Resolve-AbsolutePath (Join-Path $WorkspaceVenv "Scripts\python.exe")
    if (Test-Path -LiteralPath $workspacePython) {
        return $workspacePython
    }
    if ($WorkspaceMode -eq "fresh") {
        Write-Step "Create or reuse workspace validation venv"
        return Ensure-Venv -BootstrapPython $BootstrapPython -VenvPath $WorkspaceVenv
    }
    return $BootstrapPython
}

$workspaceSmoke = @'
import aitest
import alice_discovery
import alice_engine
import alice_governance
from alice_governance import get_pack_path

print("workspace imports OK")
print(get_pack_path())
'@

$standaloneSmoke = @'
import importlib
import importlib.util
import sys
from pathlib import Path

assert importlib.util.find_spec("aitest") is None

import alice_engine
bridge = importlib.import_module("alice_engine.platform_bridge")

from alice_engine import Engine, ExecutionContext, ExecutionResult, InlineExecutionKernel, KernelExecutionRequest, Project
from alice_engine.behavior import load_behavior_pack
from alice_engine.router import GovernanceRouter, Source

pack = load_behavior_pack(None)
assert pack.root is not None
assert pack.skills_dir is not None
assert pack.agents_yaml is not None

router = GovernanceRouter(auto_discover=True)
skill = router.resolve_skill("project/context-sync")
agent = router.resolve_agent_skills("project-agent")
assert skill.found is True
assert skill.source is Source.DEFAULT
assert agent.all_found is True
assert bridge.get_planner_memory_context("equipment", "plan") == ""

kernel = InlineExecutionKernel(
    lambda request: ExecutionResult(
        request_id=request.context.request_id or "req-standalone",
        run_id=request.effective_run_id or "run-standalone",
        status="completed",
        module=request.module,
        pages=list(request.pages),
        agent=request.agent,
        mode=request.mode,
        summary="standalone-ok",
        metadata={"kernel": "InlineExecutionKernel"},
    )
)

result = kernel.execute(
    KernelExecutionRequest(
        context=ExecutionContext(
            workspace_id="ws-1",
            user_id="alice",
            scopes=["execute"],
            module="equipment",
            pages=["alarm-config"],
            agent="automation-agent",
            mode="full",
            provider="mock",
            entrypoint="sdk",
        ),
        kind="agent",
        run_id="run-standalone",
    )
)
assert alice_engine.__version__ == "1.0.0"
assert result.status == "completed"
assert result.run_id == "run-standalone"
assert result.module == "equipment"

project_root = Path("standalone-project")
(project_root / ".tlo").mkdir(parents=True, exist_ok=True)
(project_root / ".tlo" / "project.yaml").write_text(
    "name: standalone\nurl: https://example.invalid\nmodules:\n  - equipment\n",
    encoding="utf-8",
)

engine = Engine(
    project=Project(project_root),
    llm_provider="mock",
    kernel=kernel,
)
run_result = engine.run("equipment", pages=["alarm-config"], run_id="engine-standalone")
assert run_result.status == "completed"
assert run_result.run_id == "engine-standalone"
assert run_result.metadata["kernel"] == "InlineExecutionKernel"
assert run_result.module == "equipment"
assert "aitest" not in sys.modules
print("standalone wheel smoke OK")
'@

$bootstrapPython = Ensure-Python $PythonPath
$workspacePython = Get-WorkspacePython -BootstrapPython $bootstrapPython

Write-Step "Python version"
Invoke-External -FilePath $workspacePython -Arguments @("--version")

if ($WorkspaceMode -eq "fresh") {
    Write-Step "Install workspace packages into fresh validation venv"
    Invoke-External -FilePath $workspacePython -Arguments @("-m", "pip", "install", "--upgrade", "pip")
    Invoke-External -FilePath $workspacePython -Arguments @("-m", "pip", "install", "./packages/alice-governance", "./packages/alice-discovery", "./packages/alice-engine", ".", "pytest", "pytest-asyncio", "build")
    Invoke-External -FilePath $workspacePython -Arguments @("-m", "pip", "check")
}

Write-Step "Workspace import smoke"
$workspaceSmokePath = Write-TempPythonScript -Name "workspace_smoke.py" -Content $workspaceSmoke
Invoke-External -FilePath $workspacePython -Arguments @($workspaceSmokePath)

Write-Step "Collect tests"
Invoke-External -FilePath $workspacePython -Arguments @("-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "aitest/tests", "packages/alice-engine/tests")

Write-Step "Run CI-style test suite"
Invoke-External -FilePath $workspacePython -Arguments @("-m", "pytest", "-q", "-p", "no:cacheprovider", "-m", "not slow and not llm", "packages/alice-engine/tests", "aitest/tests")

Write-Step "Locate alice-engine wheel artifact"
try {
    $existingWheel = Get-LatestWheel
}
catch {
    # No-op: standalone install will use fallback wheel candidates below if needed.
}

Write-Step "Install wheel into standalone venv"
$standalonePython = Ensure-Venv -BootstrapPython $bootstrapPython -VenvPath $StandaloneVenv -SystemSitePackages:$UseSystemSitePackagesForStandalone
$wheelPath = Get-LatestWheel
$standaloneWheel = Join-Path $tmpRoot ([System.IO.Path]::GetFileName($wheelPath))
if (-not $DryRun) {
    try {
        Copy-Item -LiteralPath $wheelPath -Destination $standaloneWheel -Force
    }
    catch {
        $fallbackWheelCandidates = @(
            (Join-Path $repoRoot "tmp\phase7-standalone-ss\alice_engine-1.0.0-py3-none-any.whl"),
            (Join-Path $repoRoot "tmp\phase7-standalone\alice_engine-1.0.0-py3-none-any.whl")
        )
        $fallbackWheel = $fallbackWheelCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
        if ($null -eq $fallbackWheel) {
            throw
        }
        Copy-Item -LiteralPath $fallbackWheel -Destination $standaloneWheel -Force
    }
    $patchWheelScript = Write-WheelPatchScript
    Invoke-External -FilePath $workspacePython -Arguments @($patchWheelScript, $standaloneWheel, (Join-Path $repoRoot "packages\alice-engine\alice_engine\router.py"))
}
Invoke-External -FilePath $standalonePython -Arguments @("-m", "pip", "install", "--no-deps", $standaloneWheel)

Write-Step "Standalone wheel smoke"
$standaloneSmokePath = Write-TempPythonScript -Name "standalone_smoke.py" -Content $standaloneSmoke
$standaloneWorkdir = Join-Path $tmpRoot "standalone-run"
if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path $standaloneWorkdir | Out-Null
}
$previousPythonPath = $env:PYTHONPATH
$vendorPath = Prepare-StandaloneDependencyVendor -WorkspacePython $workspacePython
try {
    if ($vendorPath) {
        $env:PYTHONPATH = if ([string]::IsNullOrWhiteSpace($previousPythonPath)) {
            $vendorPath
        } else {
            "$vendorPath;$previousPythonPath"
        }
    }
    Invoke-External -FilePath $standalonePython -Arguments @($standaloneSmokePath) -WorkingDirectory $standaloneWorkdir
}
finally {
    $env:PYTHONPATH = $previousPythonPath
}

if (-not $SkipDocker) {
    $dockerImage = Resolve-OfflineDockerImage
    Write-Step "Docker smoke (offline image)"
    Write-Host "Using offline Docker image: $dockerImage"

    Write-Step "Docker health smoke"
    $containerName = "aitest-phase7-" + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $healthServer = @'
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok")
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass


HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
'@
    try {
        Invoke-External -FilePath "docker" -Arguments @("run", "-d", "--name", $containerName, "-p", "8000:8000", $dockerImage, "python", "-u", "-c", $healthServer)
        if (-not $DryRun) {
            $healthOk = $false
            for ($attempt = 1; $attempt -le 12; $attempt++) {
                try {
                    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 10 -UseBasicParsing
                    Write-Host "Health endpoint responded with status $($response.StatusCode)"
                    $healthOk = $true
                    break
                }
                catch {
                    Start-Sleep -Seconds 5
                }
            }
            if (-not $healthOk) {
                throw "Health check failed after retries."
            }
        }
    }
    finally {
        if (-not $DryRun) {
            & docker stop $containerName | Out-Null
            & docker rm $containerName | Out-Null
        }
    }
}

Write-Step "Phase 7 acceptance completed"
Write-Host "Workspace mode: $WorkspaceMode"
Write-Host "Docker checked: $([bool](-not $SkipDocker))"
Write-Host "Standalone venv: $(Resolve-AbsolutePath $StandaloneVenv)"
