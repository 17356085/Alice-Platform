param(
    [Parameter(Mandatory=$true)][string]$Dump,
    [string]$Container = "aitest-postgres-1",
    [string]$Database = "aitest_restore_drill"
)

if (-not (Test-Path -LiteralPath $Dump)) { throw "Dump not found: $Dump" }
$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Dump).Hash
if (Test-Path -LiteralPath "$Dump.sha256") {
    $expected = (Get-Content -LiteralPath "$Dump.sha256" -Raw) -replace '.*Hash\s*:\s*','' -replace '\s',''
    if ($expected -and $expected.ToUpperInvariant() -ne $hash.ToUpperInvariant()) { throw "Backup checksum mismatch" }
}
docker exec $Container createdb -U aitest $Database 2>$null
Get-Content -LiteralPath $Dump -AsByteStream | docker exec -i $Container pg_restore -U aitest -d $Database --clean --if-exists
if ($LASTEXITCODE -ne 0) { throw "pg_restore failed" }
$tables = docker exec $Container psql -U aitest -d $Database -Atc "SELECT count(*) FROM pg_tables WHERE schemaname='public'"
if ([int]$tables -lt 1) { throw "Restore drill produced no public tables" }
Write-Output "Restore drill passed: database=$Database tables=$tables sha256=$hash"
