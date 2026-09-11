#requires -Version 7.0
[CmdletBinding()]
param(
    [switch]$Check
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$utf8_strict = New-Object System.Text.UTF8Encoding($false, $true)
$utf8_no_bom = New-Object System.Text.UTF8Encoding($false)
$body_marker = '<!-- bundle-body-start -->'

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

function Get-FragmentBody {
    param([Parameter(Mandatory = $true)][string]$Path)

    $content = Read-Utf8Text -Path $Path
    $marker_index = $content.IndexOf($body_marker, [System.StringComparison]::Ordinal)
    if ($marker_index -lt 0) {
        throw "$Path 缺少 $body_marker。"
    }

    return $content.Substring($marker_index + $body_marker.Length).Trim()
}

function Convert-ToBundleLinks {
    param([Parameter(Mandatory = $true)][string]$Content)

    $result = $Content.Replace('](../../共享/', '](../共享/')
    $result = $result.Replace('](../../规范依据/', '](../规范依据/')
    $result = $result.Replace('](../pr_checklist.md)', '](pr_checklist.md)')
    $result = $result.Replace('](../project_profile_template.md)', '](project_profile_template.md)')
    $result = $result.Replace('](../rule_source_matrix.md)', '](rule_source_matrix.md)')
    $result = $result.Replace('](../error.h)', '](error.h)')
    $result = $result.Replace('](../check_error_header_usage.ps1)', '](check_error_header_usage.ps1)')
    return $result
}

$c_root = $PSScriptRoot
$rules_root = Join-Path $c_root 'rules'
$examples_root = Join-Path $c_root 'examples'
$bundle_path = Join-Path $c_root 'embedded-c-team-standard-v1.md'

$error_placeholder = @'
> 按需读取 [error.h 裁剪示例](../examples/error-h-cropping.md)。

<!-- BUNDLE_INCLUDE_ERROR_CROPPING -->
'@.Trim()

$comment_placeholder = @'
> 需要注释或类型模板时，按需读取 [注释示例](../examples/comment-templates.md)。

<!-- BUNDLE_INCLUDE_COMMENT_TEMPLATES -->
'@.Trim()

$api_body = Get-FragmentBody -Path (Join-Path $rules_root '10-language-api.md')
$error_body = Get-FragmentBody -Path (Join-Path $examples_root 'error-h-cropping.md')
if (-not $api_body.Contains($error_placeholder)) {
    throw '10-language-api.md 缺少 error.h 示例占位符。'
}
$api_body = $api_body.Replace($error_placeholder, $error_body)

$comment_body = Get-FragmentBody -Path (Join-Path $rules_root '05-comments.md')
$comment_example_body = Get-FragmentBody -Path (Join-Path $examples_root 'comment-templates.md')
if (-not $comment_body.Contains($comment_placeholder)) {
    throw '05-comments.md 缺少注释示例占位符。'
}
$comment_body = $comment_body.Replace($comment_placeholder, $comment_example_body)

$ordered_bodies = @(
    Get-FragmentBody -Path (Join-Path $rules_root '00-core.md')
    $api_body
    Get-FragmentBody -Path (Join-Path $rules_root '20-hardware-concurrency.md')
    Get-FragmentBody -Path (Join-Path $rules_root '30-state-protocol-time.md')
    $comment_body
    Get-FragmentBody -Path (Join-Path $rules_root '40-storage-ota-boot.md')
    Get-FragmentBody -Path (Join-Path $rules_root '50-build-review.md')
    Get-FragmentBody -Path (Join-Path $examples_root 'module-template.md')
    Get-FragmentBody -Path (Join-Path $rules_root '90-reference.md')
)

$bundle_bodies = foreach ($body in $ordered_bodies) {
    Convert-ToBundleLinks -Content $body
}

$generated_note = @'
> **生成文件**：本合订版由 `build_standard.ps1` 根据 `rules/` 和 `examples/` 生成，请勿直接维护正文。人工阅读可使用本文件；AI 按 `AGENTS.md` 只读取任务命中的权威分片。
'@.Trim()

$bundle = "# 嵌入式 C 团队代码规范（V2.1 试运行候选版）`n`n"
$bundle += "$generated_note`n`n"
$bundle += (($bundle_bodies | ForEach-Object { $_.Trim() }) -join "`n`n")
$bundle += "`n"

if ($Check) {
    $current_bundle = Read-Utf8Text -Path $bundle_path
    if ($current_bundle -ne $bundle) {
        throw '合订版与权威分片不一致；请运行 build_standard.ps1 重新生成。'
    }

    Write-Output 'PASS: 合订版与权威分片一致。'
    return
}

[System.IO.File]::WriteAllText($bundle_path, $bundle, $utf8_no_bom)
Write-Output "PASS: 已生成 $bundle_path"
