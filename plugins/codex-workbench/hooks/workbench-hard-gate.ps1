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
  return (Test-ContainsAny -Text $Text -Needles $needles)
}

function Test-SearchOrReadOnlyCommand {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  $trimmed = $Text.TrimStart()
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
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  $normalized = $Text.Replace("/", "\").ToLowerInvariant()
  $allowedFragments = @(
    "\skills\codex-workbench\assets\assets\",
    "\skills\codex-workbench\references\references\",
    "\skills\codex-workbench\scripts\scripts\"
  )

  if (Test-IsPatchText -Text $Text) {
    $deleteLines = [regex]::Matches($Text, "(?m)^\*\*\* Delete File: (.+)$")
    if ($deleteLines.Count -eq 0) { return $false }
    foreach ($match in $deleteLines) {
      $path = $match.Groups[1].Value.Replace("/", "\").ToLowerInvariant()
      $allowed = $false
      foreach ($fragment in $allowedFragments) {
        if ($path.Contains($fragment)) {
          $allowed = $true
          break
        }
      }
      if (-not $allowed) { return $false }
    }
    return $true
  }

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

function Test-QualityGateFresh {
  param([string]$RepoRoot)
  $gate = Join-Path $RepoRoot "workbench\quality\quality-gate.ps1"
  if (-not (Test-Path $gate)) { return $true }
  $marker = Join-Path $RepoRoot ".workbench-validation\quality-gate-ok.json"
  if (-not (Test-Path $marker)) { return $false }
  $latestChange = Get-LatestChangedFileTime -RepoRoot $RepoRoot
  if ($latestChange -eq [DateTime]::MinValue) { return $true }
  $markerTime = (Get-Item $marker).LastWriteTimeUtc
  return ($markerTime -ge $latestChange)
}

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
    $toolHasForbiddenBypass = (-not $toolIsPatch) -and (-not (Test-SearchOrReadOnlyCommand -Text $toolText)) -and (Test-ForbiddenBypass -Text $toolText)
    $toolIsDestructive = (-not $toolIsPatch) -and (Test-DestructiveCommand -Text $toolText -Cwd ([string]$hook.cwd))
    $toolBypassesGitHooks = Test-GitHookBypassCommand -Text $toolText
    $toolDeletesWorkbenchRules = Test-DeletingWorkbenchRules -Text $toolText
    $invalidWorkbenchDirs = @(Get-InvalidWorkbenchDirsFromPatch -Text $toolText)
    $toolWritesInvalidWorkbenchDir = ($invalidWorkbenchDirs.Count -gt 0)
    if ($toolBypassMode -or $toolHasForbiddenBypass -or $toolIsDestructive -or $toolBypassesGitHooks -or $toolDeletesWorkbenchRules -or $toolWritesInvalidWorkbenchDir) {
      $reason = "工作台硬门禁阻止了 bypassPermissions、绕过审批/沙盒、绕过 Git hooks、破坏性命令或删除工作台规则文件的操作。"
      if ($toolWritesInvalidWorkbenchDir) {
        $reason = "工作台目录契约阻止写入未声明的 workbench 顶层目录：$($invalidWorkbenchDirs -join ', ')。允许的顶层目录是：$(Get-WorkbenchDirectoryContractText)。根目录 docs\ 可以存在，但 workbench\docs\ 不是有效工作台阶段。"
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
      $repoRoot = Get-RepoRoot -Cwd ([string]$hook.cwd)
      if ($repoRoot) {
        Add-TouchedRepo -HookInput $hook -RepoRoot $repoRoot
      }
    }
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
    $repoRoot = Get-RepoRoot -Cwd ([string]$hook.cwd)
    if ($repoRoot) {
      $repoHasChanges = Test-RepoHasChanges -RepoRoot $repoRoot
      $qualityGateFresh = Test-QualityGateFresh -RepoRoot $repoRoot
      $sessionStart = Get-SessionStartTime -HookInput $hook
      $latestChange = Get-LatestChangedFileTime -RepoRoot $repoRoot
      $changedAfterSessionStart = ($sessionStart -ne [DateTime]::MinValue -and $latestChange -ge $sessionStart)
      $repoTouchedThisSession = Test-RepoTouched -HookInput $hook -RepoRoot $repoRoot
      $directoryViolations = @(Get-WorkbenchDirectoryContractViolations -RepoRoot $repoRoot)
      if ($directoryViolations.Count -gt 0 -and ($changedAfterSessionStart -or $repoTouchedThisSession)) {
        Out-HookJson -Payload @{
          decision = "block"
          reason = "检测到本轮触碰过的项目存在未声明的 workbench 顶层目录：$($directoryViolations -join ', ')。允许的顶层目录是：$(Get-WorkbenchDirectoryContractText)。请移动到正确目录、更新模板并跑工作台 validate/audit；根目录 docs\ 可以作为普通项目文档，但不能作为 workbench 阶段。"
        }
        exit 0
      }
      if ($repoHasChanges -and -not $qualityGateFresh -and ($changedAfterSessionStart -or $repoTouchedThisSession)) {
        Out-HookJson -Payload @{
          decision = "block"
          reason = "检测到本轮触碰过的项目存在未验证改动，但没有新鲜的质量门通过记录。请先运行 .\workbench\quality\quality-gate.ps1；如果无法运行，必须在最终回复中说明原因和剩余风险。"
        }
        exit 0
      }
    }
    Out-HookJson -Payload @{}
    exit 0
  }
}

exit 0
