param(
  [string]$JudgeRoot = "$env:LOCALAPPDATA\InterviewEcho\judge0-v1.13.1",
  [string]$ProjectName = "interviewecho-judge0"
)

$ErrorActionPreference = "Stop"

function Set-ConfValue {
  param(
    [string]$Path,
    [string]$Key,
    [string]$Value
  )

  $content = Get-Content -Raw -LiteralPath $Path
  $pattern = "(?m)^$([regex]::Escape($Key))=.*$"
  if ($content -match $pattern) {
    $content = [regex]::Replace($content, $pattern, "$Key=$Value")
  } else {
    $content = $content.TrimEnd() + "`n$Key=$Value`n"
  }
  Set-Content -LiteralPath $Path -Value $content -Encoding UTF8
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "Docker CLI not found. Please install and start Docker Desktop first."
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
  throw "Docker Desktop is not running. Start Docker Desktop and retry."
}

$composeFile = Join-Path $JudgeRoot "docker-compose.yml"
$confFile = Join-Path $JudgeRoot "judge0.conf"
$releaseUrl = "https://github.com/judge0/judge0/releases/download/v1.13.1/judge0-v1.13.1.zip"

if (-not (Test-Path -LiteralPath $composeFile) -or -not (Test-Path -LiteralPath $confFile)) {
  New-Item -ItemType Directory -Force -Path $JudgeRoot | Out-Null
  $zip = Join-Path $env:TEMP "judge0-v1.13.1.zip"
  $tmp = Join-Path $env:TEMP ("judge0_extract_" + [guid]::NewGuid().ToString("N"))

  if (-not (Test-Path -LiteralPath $zip)) {
    Invoke-WebRequest -Uri $releaseUrl -OutFile $zip
  }

  New-Item -ItemType Directory -Force -Path $tmp | Out-Null
  Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force
  Copy-Item -Path (Join-Path $tmp "judge0-v1.13.1\*") -Destination $JudgeRoot -Recurse -Force
  Remove-Item -LiteralPath $tmp -Recurse -Force
}

$composeContent = Get-Content -Raw -LiteralPath $composeFile
$composeContent = $composeContent.Replace('"2358:2358"', '"127.0.0.1:2358:2358"')
$composeContent = $composeContent.Replace("'2358:2358'", "'127.0.0.1:2358:2358'")
Set-Content -LiteralPath $composeFile -Value $composeContent -Encoding UTF8

Set-ConfValue $confFile "REDIS_PASSWORD" "interviewecho_redis_local"
Set-ConfValue $confFile "POSTGRES_PASSWORD" "interviewecho_postgres_local"
Set-ConfValue $confFile "ALLOW_IP" ""
Set-ConfValue $confFile "COUNT" "4"
Set-ConfValue $confFile "MAX_QUEUE_SIZE" "128"
Set-ConfValue $confFile "CPU_TIME_LIMIT" "2"
Set-ConfValue $confFile "MAX_CPU_TIME_LIMIT" "64"
Set-ConfValue $confFile "WALL_TIME_LIMIT" "6"
Set-ConfValue $confFile "MAX_WALL_TIME_LIMIT" "160"
Set-ConfValue $confFile "MEMORY_LIMIT" "128000"
Set-ConfValue $confFile "MAX_MEMORY_LIMIT" "1024000"
Set-ConfValue $confFile "MAX_PROCESSES_AND_OR_THREADS" "64"
Set-ConfValue $confFile "MAX_MAX_PROCESSES_AND_OR_THREADS" "96"
Set-ConfValue $confFile "ENABLE_PER_PROCESS_AND_THREAD_TIME_LIMIT" "true"
Set-ConfValue $confFile "ALLOW_ENABLE_PER_PROCESS_AND_THREAD_TIME_LIMIT" "true"
Set-ConfValue $confFile "ENABLE_PER_PROCESS_AND_THREAD_MEMORY_LIMIT" "true"
Set-ConfValue $confFile "ALLOW_ENABLE_PER_PROCESS_AND_THREAD_MEMORY_LIMIT" "true"
Set-ConfValue $confFile "ENABLE_NETWORK" "false"
Set-ConfValue $confFile "ALLOW_ENABLE_NETWORK" "false"
Set-ConfValue $confFile "USE_DOCS_AS_HOMEPAGE" "false"

docker compose -p $ProjectName -f $composeFile up -d db redis
Start-Sleep -Seconds 10
docker compose -p $ProjectName -f $composeFile up -d --force-recreate server workers

$healthy = $false
for ($i = 0; $i -lt 45; $i++) {
  try {
    Invoke-RestMethod -Uri "http://127.0.0.1:2358/system_info" -TimeoutSec 3 | Out-Null
    $healthy = $true
    break
  } catch {
    Start-Sleep -Seconds 2
  }
}

if (-not $healthy) {
  docker compose -p $ProjectName -f $composeFile ps
  throw "Judge0 did not become healthy on http://127.0.0.1:2358."
}

Write-Host "Judge0 is ready: http://127.0.0.1:2358"
