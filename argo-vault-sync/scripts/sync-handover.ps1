[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string]$Title,
    [Parameter(Mandatory = $true)] [string]$BodyFile,
    [string]$Project = '끄쫀꾸',
    [string]$Date = (Get-Date -Format 'yyyy-MM-dd')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$vault = Join-Path $env:USERPROFILE '.argo\vault'
if (-not (Test-Path -LiteralPath $vault -PathType Container)) {
    throw "Argo vault not found: $vault"
}
if (-not (Test-Path -LiteralPath $BodyFile -PathType Leaf)) {
    throw "Handover body file not found: $BodyFile"
}

$body = Get-Content -LiteralPath $BodyFile -Raw -Encoding UTF8
if ([string]::IsNullOrWhiteSpace($body)) { throw 'Handover body is empty' }

$secretPatterns = @(
    '(?i)\bsk-[A-Za-z0-9_-]{16,}',
    '(?i)\bgh[pousr]_[A-Za-z0-9_]{20,}',
    '(?i)\bBearer\s+[A-Za-z0-9._-]{16,}',
    '(?i)\b(password|passwd|api[_-]?key|access[_-]?token|refresh[_-]?token)\s*[:=]'
)
foreach ($pattern in $secretPatterns) {
    if ($body -match $pattern) { throw 'Potential secret detected; handover was not written' }
}

$conversationDir = Join-Path $vault "conversations\$Project"
$notesDir = Join-Path $vault 'notes'
New-Item -ItemType Directory -Force -Path $conversationDir | Out-Null
New-Item -ItemType Directory -Force -Path $notesDir | Out-Null

$slug = ($Title -replace '[^\p{L}\p{Nd}]+', '-')
$slug = $slug.Trim('-')
if ([string]::IsNullOrWhiteSpace($slug)) { $slug = 'handover' }
$base = "$Date-$slug"
$path = Join-Path $conversationDir "$base.md"
$i = 2
while (Test-Path -LiteralPath $path) {
    $path = Join-Path $conversationDir "$base-$i.md"
    $i++
}

$doc = @"
# $Title

Date: $Date
Project: [[$Project]]

$body
"@
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($path, $doc.Trim() + [Environment]::NewLine, $utf8)

$hub = Join-Path $notesDir "$Project.md"
if (-not (Test-Path -LiteralPath $hub)) {
    [System.IO.File]::WriteAllText($hub, "# $Project`n`n## 최근 핸드오버`n", $utf8)
}
$relative = "../conversations/$Project/$(Split-Path -Leaf $path -Resolve)"
$hubText = Get-Content -LiteralPath $hub -Raw -Encoding UTF8
$entry = "- [$Title]($relative)"
if ($hubText -notmatch [regex]::Escape($entry)) {
    if ($hubText -notmatch '(?m)^## 최근 핸드오버\s*$') {
        $hubText = $hubText.TrimEnd() + "`n`n## 최근 핸드오버`n"
    } else {
        $hubText = $hubText.TrimEnd() + "`n"
    }
    [System.IO.File]::WriteAllText($hub, $hubText + $entry + "`n", $utf8)
}

$index = Join-Path $vault '_index.md'
if (Test-Path -LiteralPath $index) {
    $indexText = Get-Content -LiteralPath $index -Raw -Encoding UTF8
    $wiki = "- [[$Project]]"
    if ($indexText -notmatch [regex]::Escape($wiki)) {
        [System.IO.File]::WriteAllText($index, $indexText.TrimEnd() + "`n$wiki`n", $utf8)
    }
}

[PSCustomObject]@{
    status = 'written'
    project = $Project
    handover = $path
    hub = $hub
    index = $index
} | ConvertTo-Json -Compress
