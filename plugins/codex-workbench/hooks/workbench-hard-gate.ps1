$ErrorActionPreference = "Stop"

function Out-HookJson {
  param([hashtable]$Payload)
  $json = $Payload | ConvertTo-Json -Depth 10 -Compress
  $bytes = [Text.Encoding]::UTF8.GetBytes($json)
  $stdout = [Console]::OpenStandardOutput()
  $stdout.Write($bytes, 0, $bytes.Length)
  $stdout.Flush()
}

function Read-HookInput {
  $raw = [Console]::In.ReadToEnd()
  if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
  try {
    return $raw | ConvertFrom-Json -ErrorAction Stop
  } catch {
    return $null
  }
}

function Get-HookToolName {
  param($HookInput)
  if ($null -eq $HookInput) { return "" }
  foreach ($name in @("tool_name", "tool", "name")) {
    if ($HookInput.PSObject.Properties.Name -contains $name) {
      return [string]$HookInput.$name
    }
  }
  return ""
}

function Get-TextFromToolInput {
  param($HookInput)
  if ($null -eq $HookInput -or $null -eq $HookInput.tool_input) { return "" }
  if ($HookInput.tool_input.PSObject.Properties.Name -contains "command") {
    return [string]$HookInput.tool_input.command
  }
  return ($HookInput.tool_input | ConvertTo-Json -Depth 10 -Compress)
}

function Test-BypassPermissionMode {
  param($HookInput)
  if ($null -eq $HookInput) { return $false }
  if ($HookInput.PSObject.Properties.Name -contains "permission_mode") {
    return ([string]$HookInput.permission_mode -eq "bypassPermissions")
  }
  return $false
}

function Test-ContainsAny {
  param(
    [string]$Text,
    [string[]]$Needles
  )
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  $lower = $Text.ToLowerInvariant()
  foreach ($needle in $Needles) {
    if ($lower.Contains($needle.ToLowerInvariant())) { return $true }
  }
  return $false
}

function Get-HookStateDir {
  $base = $env:PLUGIN_DATA
  if ([string]::IsNullOrWhiteSpace($base)) {
    $base = Join-Path $env:USERPROFILE ".codex\hooks\state\codex-workbench"
  }
  $dir = Join-Path $base "hook-state"
  if (-not (Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
  }
  return $dir
}

function Get-SafeSessionId {
  param($HookInput)
  $id = "unknown"
  if ($null -ne $HookInput -and ($HookInput.PSObject.Properties.Name -contains "session_id") -and -not [string]::IsNullOrWhiteSpace([string]$HookInput.session_id)) {
    $id = [string]$HookInput.session_id
  }
  return ($id -replace "[^A-Za-z0-9_.-]", "_")
}

function Get-SessionStartFile {
  param($HookInput)
  return (Join-Path (Get-HookStateDir) ("{0}.start.txt" -f (Get-SafeSessionId -HookInput $HookInput)))
}

function Get-SessionTouchedFile {
  param($HookInput)
  return (Join-Path (Get-HookStateDir) ("{0}.repos.txt" -f (Get-SafeSessionId -HookInput $HookInput)))
}

function Get-SessionQualityGateFile {
  param($HookInput)
  return (Join-Path (Get-HookStateDir) ("{0}.quality-gates.txt" -f (Get-SafeSessionId -HookInput $HookInput)))
}

function Save-SessionStart {
  param($HookInput)
  $path = Get-SessionStartFile -HookInput $HookInput
  [IO.File]::WriteAllText($path, [DateTime]::UtcNow.ToString("o"), [Text.Encoding]::UTF8)
}

function Get-SessionStartTime {
  param($HookInput)
  $path = Get-SessionStartFile -HookInput $HookInput
  if (-not (Test-Path $path)) { return [DateTime]::MinValue }
  try {
    return [DateTime]::Parse((Get-Content -LiteralPath $path -Encoding UTF8 -Raw)).ToUniversalTime()
  } catch {
    return [DateTime]::MinValue
  }
}

function Add-TouchedRepo {
  param(
    $HookInput,
    [string]$RepoRoot
  )
  if ([string]::IsNullOrWhiteSpace($RepoRoot)) { return }
  $path = Get-SessionTouchedFile -HookInput $HookInput
  $repos = @()
  if (Test-Path $path) {
    $repos = @(Get-Content -LiteralPath $path -Encoding UTF8 | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
  }
  if ($repos -notcontains $RepoRoot) {
    $repos += $RepoRoot
    [IO.File]::WriteAllText($path, (($repos | Sort-Object -Unique) -join [Environment]::NewLine), [Text.Encoding]::UTF8)
  }
}

function Get-TouchedRepos {
  param($HookInput)
  $path = Get-SessionTouchedFile -HookInput $HookInput
  if (-not (Test-Path $path)) { return @() }
  return @(Get-Content -LiteralPath $path -Encoding UTF8 | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Sort-Object -Unique)
}

function Test-RepoTouched {
  param(
    $HookInput,
    [string]$RepoRoot
  )
  if ([string]::IsNullOrWhiteSpace($RepoRoot)) { return $false }
  $path = Get-SessionTouchedFile -HookInput $HookInput
  if (-not (Test-Path $path)) { return $false }
  $repos = @(Get-Content -LiteralPath $path -Encoding UTF8 | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
  return ($repos -contains $RepoRoot)
}

function Add-QualityGateRun {
  param(
    $HookInput,
    [string]$RepoRoot
  )
  if ([string]::IsNullOrWhiteSpace($RepoRoot)) { return }
  $path = Get-SessionQualityGateFile -HookInput $HookInput
  $repos = @()
  if (Test-Path $path) {
    $repos = @(Get-Content -LiteralPath $path -Encoding UTF8 | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
  }
  if ($repos -notcontains $RepoRoot) {
    $repos += $RepoRoot
    [IO.File]::WriteAllText($path, (($repos | Sort-Object -Unique) -join [Environment]::NewLine), [Text.Encoding]::UTF8)
  }
}

function Test-QualityGateRun {
  param(
    $HookInput,
    [string]$RepoRoot
  )
  if ([string]::IsNullOrWhiteSpace($RepoRoot)) { return $false }
  $path = Get-SessionQualityGateFile -HookInput $HookInput
  if (-not (Test-Path $path)) { return $false }
  $repos = @(Get-Content -LiteralPath $path -Encoding UTF8 | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
  return ($repos -contains $RepoRoot)
}

function Get-PatchPaths {
  param([string]$Text)
  $paths = @()
  if (-not (Test-IsPatchText -Text $Text)) { return $paths }
  $pathLines = [regex]::Matches($Text, "(?m)^\*\*\* (?:Add File|Update File|Delete File|Move to):\s+(.+?)\s*$")
  foreach ($match in $pathLines) {
    $value = [string]$match.Groups[1].Value
    if (-not [string]::IsNullOrWhiteSpace($value)) {
      $paths += $value.Trim()
    }
  }
  return @($paths | Sort-Object -Unique)
}

function Get-PatchAddedText {
  param([string]$Text)
  if (-not (Test-IsPatchText -Text $Text)) { return "" }
  $lines = @()
  foreach ($line in ($Text -split "`r?`n")) {
    if ($line.StartsWith("+") -and -not $line.StartsWith("+++")) {
      $lines += $line.Substring(1)
    }
  }
  return ($lines -join [Environment]::NewLine)
}

function Get-CommandPathCandidates {
  param([string]$Text)
  $paths = @()
  $paths += Get-PatchPaths -Text $Text
  $paths += Get-LiteralPathsFromCommandSegment -Text $Text
  $matches = [regex]::Matches($Text, "(?is)(?:Set-Content|Add-Content|Out-File|New-Item|Copy-Item|Move-Item|Remove-Item|git\s+apply)\b.*?(?:\s(?:-Path|-Destination|-ItemType|-Filter)\s+)?(?:""([^""]+)""|'([^']+)'|([A-Za-z]:\\[^\s;|&}]+|\.{1,2}[\\/][^\s;|&}]+|[A-Za-z0-9_.-]+[\\/][^\s;|&}]+))")
  foreach ($match in $matches) {
    foreach ($index in 1..3) {
      $value = [string]$match.Groups[$index].Value
      if (-not [string]::IsNullOrWhiteSpace($value)) {
        $paths += $value
        break
      }
    }
  }
  return @($paths | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Sort-Object -Unique)
}

function Resolve-PathCandidate {
  param(
    [string]$PathText,
    [string]$Cwd
  )
  if ([string]::IsNullOrWhiteSpace($PathText)) { return $null }
  $candidate = $PathText.Trim(" `t`r`n`"'")
  if ([string]::IsNullOrWhiteSpace($candidate)) { return $null }
  if ($candidate -match "^[`$%]") { return $null }
  if ($candidate.IndexOfAny([char[]]"*?[]") -ge 0) { return $null }
  try {
    if ([IO.Path]::IsPathRooted($candidate)) {
      return [IO.Path]::GetFullPath($candidate)
    }
    if (-not [string]::IsNullOrWhiteSpace($Cwd) -and [IO.Path]::IsPathRooted($Cwd)) {
      return [IO.Path]::GetFullPath((Join-Path $Cwd $candidate))
    }
  } catch {
    return $null
  }
  return $null
}

function Get-RepoRootForPath {
  param([string]$PathText)
  if ([string]::IsNullOrWhiteSpace($PathText)) { return $null }
  try {
    $candidate = [IO.Path]::GetFullPath($PathText)
  } catch {
    return $null
  }
  if (Test-Path -LiteralPath $candidate -PathType Leaf) {
    $candidate = Split-Path -Parent $candidate
  }
  if (-not (Test-Path -LiteralPath $candidate)) {
    $candidate = Split-Path -Parent $candidate
  }
  while (-not [string]::IsNullOrWhiteSpace($candidate)) {
    if (Test-Path -LiteralPath (Join-Path $candidate ".git")) {
      return $candidate
    }
    $parent = Split-Path -Parent $candidate
    if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $candidate) { break }
    $candidate = $parent
  }
  return $null
}

function Add-TouchedReposFromToolText {
  param(
    $HookInput,
    [string]$Text
  )
  $repos = @()
  $cwdRepo = Get-RepoRoot -Cwd ([string]$HookInput.cwd)
  if ($cwdRepo) { $repos += $cwdRepo }
  foreach ($path in (Get-CommandPathCandidates -Text $Text)) {
    $resolved = Resolve-PathCandidate -PathText $path -Cwd ([string]$HookInput.cwd)
    if ($resolved) {
      $repo = Get-RepoRootForPath -PathText $resolved
      if ($repo) { $repos += $repo }
    }
  }
  foreach ($repo in ($repos | Sort-Object -Unique)) {
    Add-TouchedRepo -HookInput $HookInput -RepoRoot $repo
  }
}

function Test-QualityGateCommand {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  $normalized = $Text.Replace("/", "\")
  $trimmed = $normalized.Trim()
  if ($trimmed -match "(?i)\b(py|python|python3|powershell|powershell\.exe|pwsh|pwsh\.exe)\b\s+-(c|command|encodedcommand)\b") { return $false }
  if ($trimmed -match "(?i)^cmd(\.exe)?\s+/c\b") { return $false }
  $quotedPs1 = '["''][^"'']*\\workbench\\quality\\quality-gate\.ps1["'']'
  if ($trimmed -match ("(?i)^(?:&\s*)?(?:" + $quotedPs1 + "|(?:\.{1,2}\\|[A-Za-z]:\\|\\)?[^\s;|&<>]*\\workbench\\quality\\quality-gate\.ps1)(?:\s|$)")) { return $true }
  if ($trimmed -match ("(?i)^powershell(?:\.exe)?\b.*\s-file\s+(?:" + $quotedPs1 + "|(?:\.{1,2}\\|[A-Za-z]:\\|\\)?[^\s;|&<>]*\\workbench\\quality\\quality-gate\.ps1)(?:\s|$)")) { return $true }
  if ($trimmed -match ("(?i)^pwsh(?:\.exe)?\b.*\s-file\s+(?:" + $quotedPs1 + "|(?:\.{1,2}\\|[A-Za-z]:\\|\\)?[^\s;|&<>]*\\workbench\\quality\\quality-gate\.ps1)(?:\s|$)")) { return $true }
  if ($trimmed -match "(?i)^(?:py|python|python3)(?:\s+-B)?\s+(?:(?:\.{1,2}\\|[A-Za-z]:\\|\\)?[^\s;|&<>]*\\workbench\\quality\\quality_gate\.py)(?:\s|$)") { return $true }
  return $false
}

function Test-CompositeOrRedirectCommand {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  return ($Text -match "(;|\|\||&&|\||>|<|`n|`r)")
}

function Test-SingleQualityGateCommand {
  param([string]$Text)
  if (-not (Test-QualityGateCommand -Text $Text)) { return $false }
  if (Test-CompositeOrRedirectCommand -Text $Text) { return $false }
  if ($Text -match "(?i)\b(Set-Content|Add-Content|Out-File|New-Item|Copy-Item|Move-Item|Remove-Item)\b") { return $false }
  if ($Text -match "(?i)\.workbench-validation\\quality-gate(?:-smoke)?-ok\.json") { return $false }
  return $true
}

function Add-QualityGateRunFromToolText {
  param(
    $HookInput,
    [string]$Text
  )
  if (-not (Test-SingleQualityGateCommand -Text $Text)) { return }
  $repos = @()
  $cwdRepo = Get-RepoRoot -Cwd ([string]$HookInput.cwd)
  if ($cwdRepo) { $repos += $cwdRepo }
  foreach ($path in (Get-CommandPathCandidates -Text $Text)) {
    $resolved = Resolve-PathCandidate -PathText $path -Cwd ([string]$HookInput.cwd)
    if ($resolved) {
      $repo = Get-RepoRootForPath -PathText $resolved
      if ($repo) { $repos += $repo }
    }
  }
  foreach ($repo in ($repos | Sort-Object -Unique)) {
    Add-QualityGateRun -HookInput $HookInput -RepoRoot $repo
  }
}

function Test-DirectQualityGateMarkerWrite {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  $normalized = $Text.Replace("/", "\")
  $markerPattern = "(?i)\.workbench-validation\\quality-gate(?:-smoke)?-ok\.json"
  $mentionsValidationDir = ($normalized -match "(?i)\.workbench-validation")
  $mentionsMarkerName = ($normalized -match "(?i)quality-gate(?:-smoke)?-ok\.json")
  $mentionsWritePrimitive = ($normalized -match "(?i)\b(write_text|open|Set-Content|Add-Content|Out-File|New-Item|Copy-Item|Move-Item)\b")
  if ($mentionsValidationDir -and $mentionsMarkerName -and $mentionsWritePrimitive) { return $true }
  if ($normalized -match $markerPattern) {
    if (-not (Test-SingleQualityGateCommand -Text $Text)) { return $true }
    if ($mentionsWritePrimitive) { return $true }
  }
  if ($normalized -match ("(?i)\b(Set-Content|Add-Content|Out-File|New-Item|Copy-Item|Move-Item)\b[^\r\n;|&<>]*" + $markerPattern)) { return $true }
  if ($normalized -match ("(?i)(>|>>)[^\r\n;|&<>]*" + $markerPattern)) { return $true }
  if ($normalized -match ("(?i)" + $markerPattern + "[^\r\n;|&<>]*(>|>>)")) { return $true }
  foreach ($path in (Get-CommandPathCandidates -Text $Text)) {
    if ($path.Replace("/", "\") -match "(?i)\.workbench-validation\\quality-gate(?:-smoke)?-ok\.json$" -and $Text -match "(?i)\b(Set-Content|Add-Content|Out-File|New-Item|Copy-Item|Move-Item|write_text|open)\b") { return $true }
  }
  return $false
}

function Test-CommandLikelyWrites {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  if (Test-IsPatchText -Text $Text) { return $true }
  $patterns = @(
    "\bSet-Content\b",
    "\bAdd-Content\b",
    "\bOut-File\b",
    "\bNew-Item\b",
    "\bCopy-Item\b",
    "\bMove-Item\b",
    "\bRemove-Item\b",
    "\bgit\s+apply\b",
    "\bgit\s+add\b",
    "\bgit\s+commit\b",
    "\bnpm\s+install\b",
    "\bpnpm\s+(add|install)\b",
    "\byarn\s+(add|install)\b",
    "\bcomposer\s+install\b",
    "\bpip\s+install\b"
  )
  foreach ($pattern in $patterns) {
    if ($Text -match $pattern) { return $true }
  }
  return $false
}

function Test-ToolLikelyWrites {
  param($HookInput, [string]$Text)
  $toolName = Get-HookToolName -HookInput $HookInput
  if ($toolName -match "^(apply_patch|Edit|Write)$") { return $true }
  if ($toolName -match "^mcp__.*(write|edit|delete|remove|move|rename|create|update|upload|commit|apply).*$") { return $true }
  return (Test-CommandLikelyWrites -Text $Text)
}

function Test-ForbiddenBypass {
  param([string]$Text)
  $needles = @(
    "--dangerously-bypass-approvals-and-sandbox",
    "--yolo",
    "danger-full-access",
    "bypasspermissions",
    "dangerously-skip-permissions",
    "approval_policy = never",
    "approval_policy=`"never`"",
    "approval_policy='never'",
    "sandbox_mode = danger-full-access",
    "sandbox_mode=`"danger-full-access`"",
    "sandbox_mode='danger-full-access'"
  )
  if (Test-ContainsAny -Text $Text -Needles $needles) { return $true }
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  $patterns = @(
    "(?i)\bapproval_policy\s*=\s*['""]?never['""]?",
    "(?i)\bsandbox_mode\s*=\s*['""]?danger-full-access['""]?",
    "(?i)\bpermission_mode\s*=\s*['""]?bypassPermissions['""]?"
  )
  foreach ($pattern in $patterns) {
    if ($Text -match $pattern) { return $true }
  }
  return $false
}

function Test-PatchHasForbiddenBypass {
  param([string]$Text)
  if (-not (Test-IsPatchText -Text $Text)) { return $false }
  $added = Get-PatchAddedText -Text $Text
  return (Test-ForbiddenBypass -Text $added)
}

function Test-PatchTouchesSensitiveConfig {
  param([string]$Text)
  if (-not (Test-IsPatchText -Text $Text)) { return $false }
  foreach ($path in (Get-PatchPaths -Text $Text)) {
    $normalized = $path.Replace("/", "\")
    if ($normalized -match "(?i)(^|\\)\.codex\\config\.toml$") { return $true }
    if ($normalized -match "(?i)(^|\\)hooks\.json$") { return $true }
    if ($normalized -match "(?i)(^|\\)workbench-hard-gate\.ps1$") { return $true }
  }
  return $false
}

function Test-SearchOrReadOnlyCommand {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  $trimmed = $Text.TrimStart()
  if ($trimmed -match "(;|\|\||&&|\||>|<|`n|`r)") { return $false }
  $readOnlyPrefixes = @(
    "rg ",
    "Select-String ",
    "Get-Content ",
    "findstr ",
    "grep "
  )
  foreach ($prefix in $readOnlyPrefixes) {
    if ($trimmed.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
      return $true
    }
  }
  return $false
}

function Test-CommandHasSwitch {
  param(
    [string]$Text,
    [string[]]$Names
  )
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  foreach ($name in $Names) {
    if ($Text -match ("(?i)(^|[\s`"'])-" + [regex]::Escape($name) + "($|[\s:`"'])")) {
      return $true
    }
  }
  return $false
}

function Get-RemoveItemCommandSegments {
  param([string]$Text)
  $segments = @()
  if ([string]::IsNullOrWhiteSpace($Text)) { return $segments }
  $matches = [regex]::Matches($Text, "(?is)\bRemove-Item\b.*?(?=(?:;|\r?\n|$))")
  foreach ($match in $matches) {
    $segments += [string]$match.Value
  }
  return $segments
}

function Get-LiteralPathsFromCommandSegment {
  param([string]$Text)
  $paths = @()
  if ([string]::IsNullOrWhiteSpace($Text)) { return $paths }
  $matches = [regex]::Matches($Text, "(?is)-LiteralPath\s+(?:""([^""]+)""|'([^']+)'|([^\s;|&}]+))")
  foreach ($match in $matches) {
    foreach ($index in 1..3) {
      $value = [string]$match.Groups[$index].Value
      if (-not [string]::IsNullOrWhiteSpace($value)) {
        $paths += $value
        break
      }
    }
  }
  return $paths
}

function Get-NormalizedAbsolutePath {
  param([string]$PathText)
  if ([string]::IsNullOrWhiteSpace($PathText)) { return $null }
  $candidate = $PathText.Trim(" `t`r`n`"'")
  if ([string]::IsNullOrWhiteSpace($candidate)) { return $null }
  if ($candidate -match "^[`$%]") { return $null }
  if ($candidate.IndexOfAny([char[]]"*?[]") -ge 0) { return $null }
  if (-not [IO.Path]::IsPathRooted($candidate)) { return $null }
  try {
    if (Test-Path -LiteralPath $candidate) {
      return (Resolve-Path -LiteralPath $candidate -ErrorAction Stop).Path
    }
    return [IO.Path]::GetFullPath($candidate)
  } catch {
    return $null
  }
}

function Test-PathEqualsOrInside {
  param(
    [string]$PathText,
    [string]$BasePath
  )
  if ([string]::IsNullOrWhiteSpace($PathText) -or [string]::IsNullOrWhiteSpace($BasePath)) { return $false }
  try {
    $full = [IO.Path]::GetFullPath($PathText).TrimEnd("\")
    $base = [IO.Path]::GetFullPath($BasePath).TrimEnd("\")
    return ($full.Equals($base, [StringComparison]::OrdinalIgnoreCase) -or $full.StartsWith($base + "\", [StringComparison]::OrdinalIgnoreCase))
  } catch {
    return $false
  }
}

function Test-ProtectedDeletionPath {
  param(
    [string]$ResolvedPath,
    [string]$Cwd
  )
  if ([string]::IsNullOrWhiteSpace($ResolvedPath)) { return $true }
  $full = [IO.Path]::GetFullPath($ResolvedPath).TrimEnd("\")
  $root = [IO.Path]::GetPathRoot($full).TrimEnd("\")
  if ($full.Equals($root, [StringComparison]::OrdinalIgnoreCase)) { return $true }

  $userProfile = $env:USERPROFILE
  if (-not [string]::IsNullOrWhiteSpace($userProfile)) {
    if (([IO.Path]::GetFullPath($userProfile).TrimEnd("\")).Equals($full, [StringComparison]::OrdinalIgnoreCase)) { return $true }
    if (Test-PathEqualsOrInside -PathText $full -BasePath (Join-Path $userProfile ".codex")) { return $true }
  }

  $pluginRoot = $env:PLUGIN_ROOT
  if (-not [string]::IsNullOrWhiteSpace($pluginRoot) -and (Test-PathEqualsOrInside -PathText $full -BasePath $pluginRoot)) { return $true }

  $repoRoot = Get-RepoRoot -Cwd $Cwd
  if (-not [string]::IsNullOrWhiteSpace($repoRoot) -and ([IO.Path]::GetFullPath($repoRoot).TrimEnd("\")).Equals($full, [StringComparison]::OrdinalIgnoreCase)) { return $true }
  if (-not [string]::IsNullOrWhiteSpace($Cwd) -and [IO.Path]::IsPathRooted($Cwd)) {
    try {
      $cwdFull = [IO.Path]::GetFullPath($Cwd).TrimEnd("\")
      if ($full.Equals($cwdFull, [StringComparison]::OrdinalIgnoreCase)) { return $true }
    } catch {
    }
  }
  if (Test-Path -LiteralPath $full) {
    $projectMarkers = @(".git", "AGENTS.md", "WORKBENCH.md", "package.json", "pom.xml", "pyproject.toml", "Cargo.toml", "go.mod")
    foreach ($marker in $projectMarkers) {
      if (Test-Path -LiteralPath (Join-Path $full $marker)) { return $true }
    }
  }

  if ($full -match "(?i)(^|\\)\.git(\\|$)") { return $true }
  if ($full -match "(?i)\\(AGENTS\.md|REVIEW\.md|WORKBENCH\.md|hooks\.json|workbench-hard-gate\.ps1)$") { return $true }
  if ($full -match "(?i)\\workbench$") { return $true }
  if ($full -match "(?i)\\workbench\\(product|design|architecture|delivery|feature-template|features|quality|runtime|scorecard|review|feedback)(\\|$)") { return $true }
  if ($full -match "(?i)\\workbench\\docs(\\|$)") { return $true }
  return $false
}

function Test-AllowedWorkbenchResidueDeletePath {
  param([string]$ResolvedPath)
  if ([string]::IsNullOrWhiteSpace($ResolvedPath)) { return $false }
  $full = [IO.Path]::GetFullPath($ResolvedPath).TrimEnd("\")
  if ($full -match "(?i)\\__pycache__$") { return $true }
  if ($full -match "(?i)\\scripts\\workbench_lib\\workbench_lib$") { return $true }
  return $false
}

function Test-AllowedExplicitRecursiveDelete {
  param(
    [string]$Text,
    [string]$Cwd
  )
  $segments = @(Get-RemoveItemCommandSegments -Text $Text)
  if ($segments.Count -eq 0) { return $false }
  $checked = 0
  foreach ($segment in $segments) {
    $hasRecurse = Test-CommandHasSwitch -Text $segment -Names @("Recurse", "r")
    $hasForce = Test-CommandHasSwitch -Text $segment -Names @("Force", "fo")
    if (-not ($hasRecurse -and $hasForce)) { continue }
    $checked += 1
    $paths = @(Get-LiteralPathsFromCommandSegment -Text $segment)
    if ($paths.Count -eq 0) { return $false }
    foreach ($path in $paths) {
      $resolved = Get-NormalizedAbsolutePath -PathText $path
      if ([string]::IsNullOrWhiteSpace($resolved)) { return $false }
      if (Test-AllowedWorkbenchResidueDeletePath -ResolvedPath $resolved) { continue }
      if (Test-ProtectedDeletionPath -ResolvedPath $resolved -Cwd $Cwd) { return $false }
    }
  }
  return ($checked -gt 0)
}

function Test-DestructiveCommand {
  param(
    [string]$Text,
    [string]$Cwd = ""
  )
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  if (Test-SearchOrReadOnlyCommand -Text $Text) { return $false }
  $patterns = @(
    "git\s+reset\s+--hard",
    "git\s+clean\s+-[^\s]*f[^\s]*d",
    "git\s+checkout\s+--\s+",
    "rm\s+-[^\s]*r[^\s]*f"
  )
  foreach ($pattern in $patterns) {
    if ($Text -match $pattern) { return $true }
  }
  $removeItemSegments = @(Get-RemoveItemCommandSegments -Text $Text)
  foreach ($segment in $removeItemSegments) {
    $hasRecurse = Test-CommandHasSwitch -Text $segment -Names @("Recurse", "r")
    $hasForce = Test-CommandHasSwitch -Text $segment -Names @("Force", "fo")
    if ($hasRecurse -and $hasForce) {
      return (-not (Test-AllowedExplicitRecursiveDelete -Text $Text -Cwd $Cwd))
    }
  }
  return $false
}

function Test-GitHookBypassCommand {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  $patterns = @(
    "git\s+(commit|push|merge|rebase|cherry-pick|am)\b.*\s--no-verify(\s|$)",
    "git\s+(commit|push|merge|rebase|cherry-pick|am)\b.*\s-n(\s|$)"
  )
  foreach ($pattern in $patterns) {
    if ($Text -match $pattern) { return $true }
  }
  return $false
}

function Test-DeletingWorkbenchRules {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  if (Test-AllowedWorkbenchResidueCleanup -Text $Text) { return $false }
  if ($Text -match "\*\*\* Delete File: .*?(AGENTS\.md|REVIEW\.md|WORKBENCH\.md|hooks\.json|workbench-hard-gate\.ps1)") {
    return $true
  }
  $protectedFiles = @(
    "AGENTS\.md",
    "REVIEW\.md",
    "WORKBENCH\.md",
    "hooks\.json",
    "workbench-hard-gate\.ps1"
  )
  $protectedPattern = ($protectedFiles -join "|")
  $commandPatterns = @(
    "\bRemove-Item\b[^\r\n]*($protectedPattern)",
    "\bMove-Item\b[^\r\n]*($protectedPattern)",
    "\bRename-Item\b[^\r\n]*($protectedPattern)",
    "\bdel\b[^\r\n]*($protectedPattern)",
    "\berase\b[^\r\n]*($protectedPattern)"
  )
  foreach ($pattern in $commandPatterns) {
    if ($Text -match $pattern) { return $true }
  }
  return $false
}

function Get-WorkbenchAllowedTopDirs {
  return @(
    "product",
    "design",
    "architecture",
    "delivery",
    "feature-template",
    "features",
    "quality",
    "runtime",
    "scorecard",
    "review",
    "feedback",
    "archive"
  )
}

function Get-InvalidWorkbenchTopDirFromPath {
  param([string]$PathText)
  if ([string]::IsNullOrWhiteSpace($PathText)) { return $null }
  $normalized = $PathText.Replace("/", "\").Trim(" `t`r`n`"'")
  $parts = @($normalized -split "\\+" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
  if ($parts.Count -lt 2) { return $null }
  $allowed = Get-WorkbenchAllowedTopDirs
  for ($i = 0; $i -lt ($parts.Count - 1); $i++) {
    if ($parts[$i].ToLowerInvariant() -eq "workbench") {
      $top = ($parts[$i + 1] -replace "[^A-Za-z0-9_.-].*$", "").ToLowerInvariant()
      if ([string]::IsNullOrWhiteSpace($top)) { return $null }
      if ($allowed -notcontains $top) { return $top }
      return $null
    }
  }
  return $null
}

function Get-InvalidWorkbenchDirsFromPatch {
  param([string]$Text)
  $invalid = @()
  if (-not (Test-IsPatchText -Text $Text)) { return $invalid }
  $pathLines = [regex]::Matches($Text, "(?m)^\*\*\* (?:Add File|Update File|Delete File|Move to):\s+(.+?)\s*$")
  foreach ($match in $pathLines) {
    $dir = Get-InvalidWorkbenchTopDirFromPath -PathText $match.Groups[1].Value
    if (-not [string]::IsNullOrWhiteSpace($dir)) {
      $invalid += $dir
    }
  }
  return @($invalid | Sort-Object -Unique)
}

function Get-WorkbenchDirectoryContractViolations {
  param([string]$RepoRoot)
  $violations = @()
  if ([string]::IsNullOrWhiteSpace($RepoRoot)) { return $violations }
  $workbenchDir = Join-Path $RepoRoot "workbench"
  if (-not (Test-Path -LiteralPath $workbenchDir)) { return $violations }
  $allowed = Get-WorkbenchAllowedTopDirs
  $dirs = @(Get-ChildItem -LiteralPath $workbenchDir -Directory -Force -ErrorAction SilentlyContinue)
  foreach ($dir in $dirs) {
    $name = $dir.Name.ToLowerInvariant()
    if ($allowed -notcontains $name) {
      $violations += $dir.Name
    }
  }
  return @($violations | Sort-Object -Unique)
}

function Get-WorkbenchDirectoryContractText {
  return ((Get-WorkbenchAllowedTopDirs) -join ", ")
}

function Test-AllowedWorkbenchResidueCleanup {
  param([string]$Text)
  return $false
}

function Test-IsPatchText {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  return $Text.TrimStart().StartsWith("*** Begin Patch", [StringComparison]::Ordinal)
}

function Get-RepoRoot {
  param([string]$Cwd)
  if ([string]::IsNullOrWhiteSpace($Cwd) -or -not (Test-Path $Cwd)) { return $null }
  Push-Location $Cwd
  try {
    $root = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($root)) {
      return $root.Trim()
    }
  } catch {
    return $null
  } finally {
    Pop-Location
  }
  return $null
}

function Test-RepoHasChanges {
  param([string]$RepoRoot)
  if ([string]::IsNullOrWhiteSpace($RepoRoot)) { return $false }
  Push-Location $RepoRoot
  try {
    $status = git status --porcelain 2>$null
    return -not [string]::IsNullOrWhiteSpace(($status -join ""))
  } catch {
    return $false
  } finally {
    Pop-Location
  }
}

function Get-LatestChangedFileTime {
  param([string]$RepoRoot)
  $latest = [DateTime]::MinValue
  Push-Location $RepoRoot
  try {
    $changed = git status --porcelain -z 2>$null
    if ([string]::IsNullOrWhiteSpace($changed)) { return $latest }
    foreach ($entry in ($changed -split "`0")) {
      if ([string]::IsNullOrWhiteSpace($entry)) { continue }
      $path = $entry.Substring([Math]::Min(3, $entry.Length)).Trim()
      if ($path -match " -> ") { $path = ($path -split " -> ")[-1] }
      $full = Join-Path $RepoRoot $path
      if (Test-Path $full) {
        $time = (Get-Item $full).LastWriteTimeUtc
        if ($time -gt $latest) { $latest = $time }
      }
    }
  } catch {
    return $latest
  } finally {
    Pop-Location
  }
  return $latest
}

function Get-GitHead {
  param([string]$RepoRoot)
  if ([string]::IsNullOrWhiteSpace($RepoRoot)) { return "" }
  Push-Location $RepoRoot
  try {
    $head = git rev-parse HEAD 2>$null
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($head)) {
      return $head.Trim()
    }
  } catch {
    return ""
  } finally {
    Pop-Location
  }
  return ""
}

function Get-GitDiffHash {
  param([string]$RepoRoot)
  if ([string]::IsNullOrWhiteSpace($RepoRoot)) { return "" }
  Push-Location $RepoRoot
  try {
    $tmp = New-TemporaryFile
    try {
      git diff --binary HEAD --output=$tmp 2>$null | Out-Null
      $bytes = [IO.File]::ReadAllBytes($tmp)
      $sha = [Security.Cryptography.SHA256]::Create()
      $hash = $sha.ComputeHash($bytes)
      return "sha256:" + ([BitConverter]::ToString($hash).Replace("-", "").ToLowerInvariant())
    } finally {
      Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
    }
  } catch {
    return ""
  } finally {
    Pop-Location
  }
}

function Get-FileSha256 {
  param([string]$PathText)
  if ([string]::IsNullOrWhiteSpace($PathText) -or -not (Test-Path -LiteralPath $PathText)) { return "" }
  try {
    $bytes = [IO.File]::ReadAllBytes($PathText)
    $sha = [Security.Cryptography.SHA256]::Create()
    $hash = $sha.ComputeHash($bytes)
    return "sha256:" + ([BitConverter]::ToString($hash).Replace("-", "").ToLowerInvariant())
  } catch {
    return ""
  }
}

function Get-QualityGateFreshFailure {
  param([string]$RepoRoot)
  $gate = Join-Path $RepoRoot "workbench\quality\quality-gate.ps1"
  if (-not (Test-Path $gate)) { return $null }
  $marker = Join-Path $RepoRoot ".workbench-validation\quality-gate-ok.json"
  if (-not (Test-Path $marker)) { return "missing quality-gate-ok.json" }
  try {
    $data = Get-Content -LiteralPath $marker -Encoding UTF8 -Raw | ConvertFrom-Json -ErrorAction Stop
  } catch {
    return "quality-gate-ok.json is not valid json"
  }
  if ([string]$data.schema -ne "codex-workbench-quality-gate-marker/v2") { return "quality-gate marker schema is invalid" }
  if (@("passed", "passed_with_risk") -notcontains ([string]$data.status)) { return "quality-gate marker status is not passed" }
  $currentHead = Get-GitHead -RepoRoot $RepoRoot
  if (-not [string]::IsNullOrWhiteSpace($currentHead) -and -not [string]::IsNullOrWhiteSpace([string]$data.git_head) -and [string]$data.git_head -ne $currentHead) {
    return "quality-gate marker git_head is stale"
  }
  $currentDiffHash = Get-GitDiffHash -RepoRoot $RepoRoot
  if (-not [string]::IsNullOrWhiteSpace($currentDiffHash) -and -not [string]::IsNullOrWhiteSpace([string]$data.diff_hash) -and [string]$data.diff_hash -ne $currentDiffHash) {
    return "quality-gate marker diff_hash is stale"
  }
  $checks = @($data.checks_run)
  if ($checks.Count -eq 0) { return "quality-gate marker checks_run is empty" }
  if ([string]$data.quality_profile -eq "smoke") {
    return "quality-gate marker is smoke-only and cannot be used as delivery proof"
  }
  if (@("standard", "full") -contains ([string]$data.quality_profile)) {
    if (@($data.skipped_groups).Count -gt 0) { return "quality-gate marker used skipped groups for standard/full" }
    if ($data.allow_empty -eq $true) { return "quality-gate marker used allow_empty for standard/full" }
  }
  $workflowState = [string]$data.workflow_state
  if ([string]::IsNullOrWhiteSpace($workflowState)) { return "quality-gate marker workflow_state is missing" }
  if (-not [IO.Path]::IsPathRooted($workflowState)) {
    $workflowState = Join-Path $RepoRoot $workflowState
  }
  if (-not (Test-Path -LiteralPath $workflowState)) { return "quality-gate workflow state file is missing" }
  if (-not (Test-PathEqualsOrInside -PathText $workflowState -BasePath (Join-Path $RepoRoot ".workbench-validation"))) {
    return "quality-gate workflow state is outside .workbench-validation"
  }
  $expectedWorkflowHash = [string]$data.workflow_state_hash
  $actualWorkflowHash = Get-FileSha256 -PathText $workflowState
  if ([string]::IsNullOrWhiteSpace($expectedWorkflowHash) -or [string]::IsNullOrWhiteSpace($actualWorkflowHash) -or $expectedWorkflowHash -ne $actualWorkflowHash) {
    return "quality-gate workflow_state_hash is invalid"
  }
  if ([string]$data.branch_protection -eq "verified" -and @($data.unverified_paths) -contains "branch_protection") {
    return "quality-gate marker branch_protection is internally inconsistent"
  }
  $latestChange = Get-LatestChangedFileTime -RepoRoot $RepoRoot
  if ($latestChange -ne [DateTime]::MinValue) {
    $markerTime = (Get-Item $marker).LastWriteTimeUtc
    if ($markerTime -lt $latestChange) { return "quality-gate marker is older than changed files" }
  }
  return $null
}

function Test-QualityGateFresh {
  param([string]$RepoRoot)
  return ($null -eq (Get-QualityGateFreshFailure -RepoRoot $RepoRoot))
}

$event = "unknown"

try {
  $hook = Read-HookInput
  if ($null -eq $hook) { exit 0 }
  $event = [string]$hook.hook_event_name

  switch ($event) {
  "SessionStart" {
    Save-SessionStart -HookInput $hook
    Out-HookJson -Payload @{
      hookSpecificOutput = @{
        hookEventName = "SessionStart"
        additionalContext = "工作台硬门禁已加载：危险绕过命令会被拦截；如果当前会话处于 bypassPermissions 会被阻断。项目有 workbench\quality\quality-gate.ps1 且本轮触碰项目改动时，结束前需要运行质量门。执行前还要自检会话职责边界、skill 完整性、搜索路由、阶段状态和 workbench 目录契约。允许的 workbench 顶层目录是：$(Get-WorkbenchDirectoryContractText)。根目录 docs\ 可以作为普通项目文档，但不能发明 workbench\docs\ 作为工作台阶段。"
      }
    }
    exit 0
  }

  "SubagentStart" {
    Out-HookJson -Payload @{
      hookSpecificOutput = @{
        hookEventName = "SubagentStart"
        additionalContext = "子代理也必须遵守工作台边界：工作台配置会话只处理规则、skill、MCP、hook、模板和质量门；匹配 skill 先读 SKILL.md；需要搜索时优先 global-search；涉及项目改动时保留验证和审查证据；不得发明未声明的 workbench 顶层目录。"
      }
    }
    exit 0
  }

  "UserPromptSubmit" {
    if (Test-BypassPermissionMode -HookInput $hook) {
      Out-HookJson -Payload @{
        decision = "block"
        reason = "当前会话处于 bypassPermissions，会绕过工作台审批/沙盒边界。请重启到正常权限模式，或由用户明确重新确认本轮高风险权限。"
      }
      exit 0
    }
    Out-HookJson -Payload @{
      hookSpecificOutput = @{
        hookEventName = "UserPromptSubmit"
        additionalContext = "执行任务时不要只依赖软规则。先确认当前会话职责：如果用户已声明是工作台配置会话，就只处理规则、skill、MCP、hook、模板和质量门，不推进业务项目。匹配 skill 时先读 SKILL.md，并确认其 references/scripts/assets 等必要资源存在；缺失时先修复或说明。用户要求搜索、全网、全球资料、大神/别人怎么做、最新资料时，先用 global-search 并优先 Tavily；失败要说明原因后再降级。涉及代码改动时优先使用项目质量门、测试、lint、CI 或独立审查。进入实现前先检查 PROJECT_INTAKE、product/design/architecture/delivery 和 feature 包状态。真正执行绕过审批/沙盒、绕过 Git hooks、破坏性命令或写入未声明 workbench 顶层目录时必须由工具门禁拦截。"
      }
    }
    exit 0
  }

  "PreToolUse" {
    $toolText = Get-TextFromToolInput -HookInput $hook
    $toolIsPatch = Test-IsPatchText -Text $toolText
    $toolBypassMode = Test-BypassPermissionMode -HookInput $hook
    $toolHasForbiddenBypass = ((-not $toolIsPatch) -and (-not (Test-SearchOrReadOnlyCommand -Text $toolText)) -and (Test-ForbiddenBypass -Text $toolText)) -or (Test-PatchHasForbiddenBypass -Text $toolText)
    $toolIsDestructive = (-not $toolIsPatch) -and (Test-DestructiveCommand -Text $toolText -Cwd ([string]$hook.cwd))
    $toolBypassesGitHooks = Test-GitHookBypassCommand -Text $toolText
    $toolDeletesWorkbenchRules = Test-DeletingWorkbenchRules -Text $toolText
    $toolWeakensSensitiveConfig = (Test-PatchTouchesSensitiveConfig -Text $toolText) -and (Test-PatchHasForbiddenBypass -Text $toolText)
    $toolWritesQualityGateMarker = Test-DirectQualityGateMarkerWrite -Text $toolText
    $invalidWorkbenchDirs = @(Get-InvalidWorkbenchDirsFromPatch -Text $toolText)
    $toolWritesInvalidWorkbenchDir = ($invalidWorkbenchDirs.Count -gt 0)
    if ($toolBypassMode -or $toolHasForbiddenBypass -or $toolIsDestructive -or $toolBypassesGitHooks -or $toolDeletesWorkbenchRules -or $toolWritesInvalidWorkbenchDir -or $toolWeakensSensitiveConfig -or $toolWritesQualityGateMarker) {
      $reason = "工作台硬门禁阻止了 bypassPermissions、绕过审批/沙盒、绕过 Git hooks、破坏性命令或删除工作台规则文件的操作。"
      if ($toolWritesInvalidWorkbenchDir) {
        $reason = "工作台目录契约阻止写入未声明的 workbench 顶层目录：$($invalidWorkbenchDirs -join ', ')。允许的顶层目录是：$(Get-WorkbenchDirectoryContractText)。根目录 docs\ 可以存在，但 workbench\docs\ 不是有效工作台阶段。"
      }
      if ($toolWritesQualityGateMarker) {
        $reason = "工作台硬门禁阻止直接写入 .workbench-validation\quality-gate-ok.json。该 marker 只能由项目质量门生成，不能手写伪造。"
      }
      Out-HookJson -Payload @{
        hookSpecificOutput = @{
          hookEventName = "PreToolUse"
          permissionDecision = "deny"
          permissionDecisionReason = $reason
        }
      }
      exit 0
    }
    if (Test-ToolLikelyWrites -HookInput $hook -Text $toolText) {
      Add-TouchedReposFromToolText -HookInput $hook -Text $toolText
    }
    Add-QualityGateRunFromToolText -HookInput $hook -Text $toolText
    exit 0
  }

  "PermissionRequest" {
    $toolText = Get-TextFromToolInput -HookInput $hook
    $toolBypassMode = Test-BypassPermissionMode -HookInput $hook
    $toolHasForbiddenBypass = Test-ForbiddenBypass -Text $toolText
    $toolIsDestructive = Test-DestructiveCommand -Text $toolText -Cwd ([string]$hook.cwd)
    $toolBypassesGitHooks = Test-GitHookBypassCommand -Text $toolText
    if ($toolBypassMode -or $toolHasForbiddenBypass -or $toolIsDestructive -or $toolBypassesGitHooks) {
      Out-HookJson -Payload @{
        hookSpecificOutput = @{
          hookEventName = "PermissionRequest"
          decision = @{
            behavior = "deny"
            message = "工作台硬门禁拒绝高风险权限申请。"
          }
        }
      }
      exit 0
    }
    exit 0
  }

  "Stop" {
    if ($hook.stop_hook_active -eq $true) {
      Out-HookJson -Payload @{}
      exit 0
    }
    $candidateRepos = @()
    $cwdRepo = Get-RepoRoot -Cwd ([string]$hook.cwd)
    if ($cwdRepo) { $candidateRepos += $cwdRepo }
    $candidateRepos += Get-TouchedRepos -HookInput $hook
    foreach ($repoRoot in ($candidateRepos | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Sort-Object -Unique)) {
      $repoHasChanges = Test-RepoHasChanges -RepoRoot $repoRoot
      $qualityGateFreshFailure = Get-QualityGateFreshFailure -RepoRoot $repoRoot
      $qualityGateFresh = ($null -eq $qualityGateFreshFailure)
      $hasProjectQualityGate = Test-Path -LiteralPath (Join-Path $repoRoot "workbench\quality\quality-gate.ps1")
      $sessionStart = Get-SessionStartTime -HookInput $hook
      $latestChange = Get-LatestChangedFileTime -RepoRoot $repoRoot
      $changedAfterSessionStart = ($sessionStart -ne [DateTime]::MinValue -and $latestChange -ge $sessionStart)
      $repoTouchedThisSession = Test-RepoTouched -HookInput $hook -RepoRoot $repoRoot
      $qualityGateRanThisSession = Test-QualityGateRun -HookInput $hook -RepoRoot $repoRoot
      $directoryViolations = @(Get-WorkbenchDirectoryContractViolations -RepoRoot $repoRoot)
      if ($directoryViolations.Count -gt 0 -and ($changedAfterSessionStart -or $repoTouchedThisSession)) {
        Out-HookJson -Payload @{
          decision = "block"
          reason = "检测到本轮触碰过的项目存在未声明的 workbench 顶层目录：$($directoryViolations -join ', ')。允许的顶层目录是：$(Get-WorkbenchDirectoryContractText)。请移动到正确目录、更新模板并跑工作台 validate/audit；根目录 docs\ 可以作为普通项目文档，但不能作为 workbench 阶段。"
        }
        exit 0
      }
      if ($hasProjectQualityGate -and ($changedAfterSessionStart -or $repoTouchedThisSession) -and (-not $qualityGateFresh -or -not $qualityGateRanThisSession)) {
        $reasonDetail = $qualityGateFreshFailure
        if ([string]::IsNullOrWhiteSpace($reasonDetail)) { $reasonDetail = "本轮没有记录到项目质量门调用" }
        Out-HookJson -Payload @{
          decision = "block"
          reason = "检测到本轮触碰过的项目缺少本轮质量门证明：$reasonDetail。项目：$repoRoot。请先运行 .\workbench\quality\quality-gate.ps1；如果无法运行，必须在最终回复中说明原因和剩余风险。"
        }
        exit 0
      }
    }
    Out-HookJson -Payload @{}
    exit 0
  }
  }

  exit 0
} catch {
  $message = [string]$_.Exception.Message
  if ([string]::IsNullOrWhiteSpace($message)) {
    $message = "unknown hook error"
  }
  try {
    if ($event -eq "PreToolUse") {
      Out-HookJson -Payload @{
        hookSpecificOutput = @{
          hookEventName = "PreToolUse"
          permissionDecision = "deny"
          permissionDecisionReason = "Codex Workbench hook 异常，已按 fail-closed 拒绝工具调用。异常：$message"
        }
      }
    } elseif ($event -eq "PermissionRequest") {
      Out-HookJson -Payload @{
        hookSpecificOutput = @{
          hookEventName = "PermissionRequest"
          decision = @{
            behavior = "deny"
            message = "Codex Workbench hook 异常，已按 fail-closed 拒绝权限申请。异常：$message"
          }
        }
      }
    } elseif ($event -eq "Stop") {
      Out-HookJson -Payload @{
        decision = "block"
        reason = "Codex Workbench hook 异常，已按 fail-closed 阻断结束。异常：$message"
      }
    } else {
      Out-HookJson -Payload @{
        hookSpecificOutput = @{
          hookEventName = $event
          additionalContext = "Codex Workbench hook 自身发生异常；本事件只追加上下文，不作为硬门禁。异常：$message"
        }
      }
    }
  } catch {
    $fallback = '{"hookSpecificOutput":{"hookEventName":"HookError","additionalContext":"Codex Workbench hook failed before structured JSON output; treat this turn as unverified."}}'
    $bytes = [Text.Encoding]::UTF8.GetBytes($fallback)
    $stdout = [Console]::OpenStandardOutput()
    $stdout.Write($bytes, 0, $bytes.Length)
    $stdout.Flush()
  }
  exit 0
}
