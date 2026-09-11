#requires -Version 7.0
[CmdletBinding()]
param([string]$ClangFormatPath = 'clang-format')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$c_root = $PSScriptRoot
$utf8_strict = New-Object System.Text.UTF8Encoding($false, $true)

function Read-Utf8Text {
    param([Parameter(Mandatory = $true)][string]$Path)

    $resolved_path = (Resolve-Path -LiteralPath $Path).Path
    $bytes = [System.IO.File]::ReadAllBytes($resolved_path)
    if (($bytes.Length -ge 3) -and
        ($bytes[0] -eq 0xEF) -and
        ($bytes[1] -eq 0xBB) -and
        ($bytes[2] -eq 0xBF)) {
        throw "$Path 含有 UTF-8 BOM。"
    }
    return $utf8_strict.GetString($bytes).Replace("`r`n", "`n")
}

& (Join-Path $c_root 'build_standard.ps1') -Check

$formatter = (Get-Command $ClangFormatPath -CommandType Application -ErrorAction Stop).Source
$formatter_version = (& $formatter --version) -join "`n"
if ($LASTEXITCODE -ne 0 -or $formatter_version -notmatch '\bclang-format version 19\.1\.7(?:\s|$)') {
    throw "要求 clang-format 19.1.7，实际为：$formatter_version"
}
$example_count = 0

$text_files = Get-ChildItem -LiteralPath $c_root -Recurse -File | Where-Object {
    $_.Extension -in @('.md', '.ps1', '.h', '.json') -or $_.Name -eq '.clang-format'
}
foreach ($file in $text_files) {
    $content = Read-Utf8Text -Path $file.FullName
    $fence_count = ([regex]::Matches($content, '(?m)^```')).Count
    if (($fence_count % 2) -ne 0) {
        throw "$($file.FullName) 的 Markdown 代码围栏不成对。"
    }

    if ($file.Extension -eq '.md') {
        foreach ($block in [regex]::Matches($content, '(?ms)^```c\n(.*?)^```')) {
            $code = $block.Groups[1].Value.TrimEnd()
            $formatted = ($code | & $formatter --style=file `
                "--assume-filename=$(Join-Path $c_root 'standard_example.c')") -join "`n"
            if ($LASTEXITCODE -ne 0) { throw "$($file.FullName) 的示例格式器执行失败。" }
            if ($code -cne $formatted.TrimEnd()) {
                $block_line = ($content.Substring(0, $block.Index) -split "`n").Count
                throw "$($file.FullName):$block_line 的 C 示例不符合 clang-format 19.1.7。"
            }
            $example_count++
        }
        foreach ($link in [regex]::Matches($content, '\]\(([^)]+)\)')) {
            $target = $link.Groups[1].Value
            if ($target -match '^(https?://|#)') { continue }
            $relative_path = [uri]::UnescapeDataString(($target -split '#', 2)[0])
            if ($relative_path -and -not (Test-Path -LiteralPath (Join-Path $file.DirectoryName $relative_path))) {
                throw "$($file.FullName) 的相对链接不存在：$target"
            }
        }
        $inside_c = $false
        $line_number = 0
        foreach ($line in ($content -split "`n")) {
            $line_number++
            if ($line -eq '```c') {
                $inside_c = $true
                continue
            }
            if ($inside_c -and $line -eq '```') {
                $inside_c = $false
                continue
            }
            if ($inside_c -and $line.Length -gt 100) {
                throw "$($file.FullName):$line_number 的 C 示例超过 100 字符。"
            }
            if ($inside_c -and $line -match '^\s+\*[^/]') {
                throw "$($file.FullName):$line_number 存在装饰性行首星号。"
            }
        }
    }
}

$agents_path = Join-Path $c_root 'AGENTS.md'
if ((Get-Item -LiteralPath $agents_path).Length -gt 8192) {
    throw 'AGENTS.md 超过 8 KiB，不再是轻量路由入口。'
}
$agents_text = Read-Utf8Text -Path $agents_path

$route_targets = @(
    'rules\00-core.md',
    'rules\05-comments.md',
    'rules\10-language-api.md',
    'rules\20-hardware-concurrency.md',
    'rules\30-state-protocol-time.md',
    'rules\40-storage-ota-boot.md',
    'rules\50-build-review.md',
    'rules\90-reference.md',
    'examples\comment-templates.md',
    'examples\error-h-cropping.md',
    'examples\module-template.md',
    'pr_checklist.md',
    'project_profile_template.md',
    'rule_source_matrix.md'
)
foreach ($relative_path in $route_targets) {
    $target_path = Join-Path $c_root $relative_path
    if (-not (Test-Path -LiteralPath $target_path)) {
        throw "AI 路由目标不存在：$relative_path"
    }
    $route_text = $relative_path.Replace('\', '/')
    if (-not $agents_text.Contains($route_text)) {
        throw "AGENTS.md 未引用路由目标：$route_text"
    }
}

$rule_files = Get-ChildItem -LiteralPath (Join-Path $c_root 'rules') -Filter '*.md' -File
$rule_text = ($rule_files | ForEach-Object { Read-Utf8Text -Path $_.FullName }) -join "`n"
$pattern = '\*\*\[([A-Z]+-[0-9]{3})\]\[(AUTO-BLOCK|REVIEW-BLOCK|ADVISORY)\]\*\*'
$definitions = [regex]::Matches($rule_text, $pattern)
$duplicates = $definitions | Group-Object { $_.Groups[1].Value } | Where-Object { $_.Count -ne 1 }
if ($duplicates) {
    throw ('权威分片中的规则 ID 重复：' + (($duplicates.Name) -join ', '))
}

$expected_rule_counts = @{
    API = 8; ARC = 3; BLD = 9; DIA = 4; DOC = 10; ERR = 5; EXC = 4
    FMT = 11; GOV = 2; HOT = 4; IRQ = 7; MEM = 8; NAM = 9; NVM = 5
    OTA = 5; PRE = 4; REV = 6; RTOS = 9; SRC = 4; TIM = 6; TYP = 9
}
$actual_rule_groups = $definitions | Group-Object { $_.Groups[1].Value.Split('-')[0] }
foreach ($prefix in $expected_rule_counts.Keys) {
    $actual_group = $actual_rule_groups | Where-Object { $_.Name -eq $prefix }
    $actual_count = if ($actual_group) { $actual_group.Count } else { 0 }
    if ($actual_count -ne $expected_rule_counts[$prefix]) {
        throw "$prefix 规则数量异常：期望 $($expected_rule_counts[$prefix])，实际 $actual_count。"
    }
}
if ($actual_rule_groups.Count -ne $expected_rule_counts.Count) {
    throw '权威分片出现未登记的规则前缀。'
}

foreach ($prefix_group in ($definitions | Group-Object { $_.Groups[1].Value.Split('-')[0] })) {
    $numbers = @($prefix_group.Group | ForEach-Object {
        [int]$_.Groups[1].Value.Split('-')[1]
    } | Sort-Object)
    for ($index = 0; $index -lt $numbers.Count; $index++) {
        $expected = $index + 1
        if ($numbers[$index] -ne $expected) {
            throw "$($prefix_group.Name) 规则序号不连续。"
        }
    }
}

$bundle_text = Read-Utf8Text -Path (Join-Path $c_root 'embedded-c-team-standard-v1.md')
if (-not $bundle_text.Contains('> **生成文件**')) {
    throw '合订版缺少生成文件警示。'
}
$bundle_ids = [regex]::Matches($bundle_text, $pattern) | ForEach-Object { $_.Groups[1].Value }
$fragment_ids = $definitions | ForEach-Object { $_.Groups[1].Value }
if (Compare-Object -ReferenceObject $fragment_ids -DifferenceObject $bundle_ids) {
    throw '合订版与权威分片的规则 ID 集合不一致。'
}

$matrix_text = Read-Utf8Text -Path (Join-Path $c_root 'rule_source_matrix.md')
$mapped_ids = [System.Collections.Generic.HashSet[string]]::new()
foreach ($cell in [regex]::Matches($matrix_text, '(?m)^\|\s*`([^`]+)`\s*\|')) {
    foreach ($range in [regex]::Matches($cell.Groups[1].Value, '([A-Z]+)-(\d{3})(?:~(\d{3}))?')) {
        $first = [int]$range.Groups[2].Value
        $last = if ($range.Groups[3].Success) { [int]$range.Groups[3].Value } else { $first }
        foreach ($number in $first..$last) {
            [void]$mapped_ids.Add(('{0}-{1:D3}' -f $range.Groups[1].Value, $number))
        }
    }
}
if (Compare-Object -ReferenceObject @($fragment_ids) -DifferenceObject @($mapped_ids)) {
    throw '来源矩阵的规则覆盖与权威分片不一致。'
}
$checklist = Read-Utf8Text -Path (Join-Path $c_root 'pr_checklist.md')
$gates = [regex]::Matches($checklist, '(?m)^- \[ \] \*\*GATE-(\d{2}) ')
if ($gates.Count -ne 19 -or (@($gates | ForEach-Object { [int]$_.Groups[1].Value }) -join ',') -ne
    ((1..19) -join ',')) { throw '合并检查表须保持 19 项有序核心门禁。' }

$error_example = Read-Utf8Text -Path (Join-Path $c_root 'examples\error-h-cropping.md')
if ($error_example -match 'typedef\s+enum') {
    throw 'error.h 裁剪示例不得使用枚举。'
}
foreach ($required_text in @(
    '#define ERROR_OK 0',
    '#define EPERM -1',
    '`error.h` 裁剪只能删除未使用项'
)) {
    if (-not $error_example.Contains($required_text)) {
        throw "error.h 裁剪示例缺少：$required_text"
    }
}

$contract = Read-Utf8Text -Path (Join-Path $c_root 'checks/error_macro_contract.json') |
    ConvertFrom-Json -AsHashtable
$actual_macros = [System.Collections.Generic.Dictionary[string,string]]::new([StringComparer]::Ordinal)
foreach ($line in (Get-Content -LiteralPath (Join-Path $c_root 'error.h') -Encoding utf8)) {
    if ($line -match '^\s*#\s*define\s+(\w+)(.*)$') {
        $name = $Matches[1]
        $body = ($Matches[2] -split '/\*', 2)[0].Trim()
        if ($name -eq '__ERROR_H' -and $body -eq '') { continue }
        if ($actual_macros.ContainsKey($name) -or $contract.Keys -cnotcontains $name -or
            $body -cne $contract[$name]) { throw "error.h 宏 $name 偏离冻结契约。" }
        $actual_macros[$name] = $body
    }
}
if ($contract.Count -ne 134 -or $actual_macros.Count -ne $contract.Count) {
    throw 'error.h 完整目录或冻结契约缺少条目。'
}

Write-Output "PASS: 分片、路由、合订版、规则/矩阵、链接、UTF-8、示例格式和 error.h 契约通过；规则数=$($definitions.Count)，C 示例块数=$example_count（含合订版重复展示）。"
