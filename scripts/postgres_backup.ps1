param(
    [string]$Container = "aitest-postgres-1",
    [string]$Output = "artifacts/postgres/aitest-$(Get-Date -Format yyyyMMdd-HHmmss).dump"
)

$target = [IO.Path]::GetFullPath($Output)
$parent = Split-Path -Parent $target
New-Item -ItemType Directory -Force -Path $parent | Out-Null
docker exec $Container pg_dump -U aitest -d aitest -Fc | Set-Content -Encoding Byte -Path $target
if ($LASTEXITCODE -ne 0) { throw "pg_dump failed" }
Get-FileHash -Algorithm SHA256 -LiteralPath $target | Set-Content -Path "$target.sha256"
Write-Output "Backup written: $target"
