[CmdletBinding()]
param(
    [switch]$SkipLocalLinks
)

$ErrorActionPreference = "Stop"
$root_path = $PSScriptRoot
$utf8_strict = [System.Text.UTF8Encoding]::new($false, $true)
$issues = [System.Collections.Generic.List[string]]::new()

$text_files = @(
    ".editorconfig",
    "README.md",
    "luatos-embedded-team-standard-v1.md",
    "luatos_project_profile_template.md",
    "luatos_pr_checklist.md",
    "luatos_rule_source_matrix.md",
    "validate_luatos_standard.ps1"
)

function Read-StrictUtf8 {
    param([Parameter(Mandatory = $true)][string]$Path)

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    if (($bytes.Length -ge 3) -and
        ($bytes[0] -eq 0xEF) -and
        ($bytes[1] -eq 0xBB) -and
        ($bytes[2] -eq 0xBF)) {
        $issues.Add("BOM is not allowed: $Path")
    }

    try {
        return $utf8_strict.GetString($bytes)
    }
    catch {
        $issues.Add("invalid UTF-8: $Path")
        return ""
    }
}

function Expand-RuleReferences {
    param([Parameter(Mandatory = $true)][string]$Text)

    $result = [System.Collections.Generic.List[string]]::new()
    $matches = [regex]::Matches(
        $Text,
        'LUA-([A-Z]+)-(\d{3})(?:~(\d{3}))?'
    )

    foreach ($match in $matches) {
        $group_name = $match.Groups[1].Value
        $first_number = [int]$match.Groups[2].Value
        $last_number = $first_number
        if ($match.Groups[3].Success) {
            $last_number = [int]$match.Groups[3].Value
        }

        if ($last_number -lt $first_number) {
            $issues.Add("invalid rule range: $($match.Value)")
            continue
        }

        for ($number = $first_number; $number -le $last_number; $number++) {
            $result.Add(("LUA-{0}-{1:D3}" -f $group_name, $number))
        }
    }

    return $result.ToArray()
}

function Get-MarkdownAnchor {
    param([Parameter(Mandatory = $true)][string]$Heading)

    $anchor = $Heading.ToLowerInvariant()
    $anchor = [regex]::Replace($anchor, '`([^`]*)`', '$1')
    $anchor = [regex]::Replace($anchor, '\[[^\]]+\]\([^\)]+\)', '')
    $anchor = [regex]::Replace($anchor, '[^\p{L}\p{Nd}\s-]', '')
    $anchor = [regex]::Replace($anchor.Trim(), '\s+', '-')
    $anchor = [regex]::Replace($anchor, '-+', '-')
    return $anchor
}

foreach ($relative_path in $text_files) {
    $full_path = Join-Path $root_path $relative_path
    if (-not (Test-Path -LiteralPath $full_path -PathType Leaf)) {
        $issues.Add("missing package file: $relative_path")
        continue
    }

    $text = Read-StrictUtf8 -Path $full_path
    if ($text.Contains("`r")) {
        $issues.Add("CR/CRLF is not allowed: $relative_path")
    }
    if (-not $text.EndsWith("`n")) {
        $issues.Add("missing final LF: $relative_path")
    }
    if ([regex]::IsMatch($text, "(?m)[ `t]+$")) {
        $issues.Add("trailing whitespace: $relative_path")
    }
}

$standard_path = Join-Path $root_path "luatos-embedded-team-standard-v1.md"
$matrix_path = Join-Path $root_path "luatos_rule_source_matrix.md"
$checklist_path = Join-Path $root_path "luatos_pr_checklist.md"

$standard_text = Read-StrictUtf8 -Path $standard_path
$rule_matches = [regex]::Matches(
    $standard_text,
    '\[(LUA-[A-Z]+-\d{3})\]\[(MUST|PROJECT)\]'
)
$standard_rules = @($rule_matches | ForEach-Object { $_.Groups[1].Value })
$duplicate_standard_rules = @(
    $standard_rules |
        Group-Object |
        Where-Object Count -gt 1 |
        ForEach-Object Name
)
if ($duplicate_standard_rules.Count -gt 0) {
    $issues.Add("duplicate standard rules: $($duplicate_standard_rules -join ', ')")
}

$unique_standard_rules = @($standard_rules | Sort-Object -Unique)
$rules_by_group = $unique_standard_rules | Group-Object {
    if ($_ -match '^LUA-([A-Z]+)-(\d{3})$') {
        return $Matches[1]
    }
}
foreach ($group in $rules_by_group) {
    $numbers = @(
        $group.Group |
            ForEach-Object { [int]($_.Substring($_.Length - 3)) } |
            Sort-Object
    )
    if ($numbers.Count -eq 0) {
        continue
    }
    $expected_numbers = @(1..$numbers[-1])
    if (($numbers -join ",") -ne ($expected_numbers -join ",")) {
        $issues.Add("rule numbering gap in LUA-$($group.Name): $($numbers -join ',')")
    }
}

$matrix_text = Read-StrictUtf8 -Path $matrix_path
if ($matrix_text -match '(?s)<!-- RULE-MATRIX-BEGIN -->(.*?)<!-- RULE-MATRIX-END -->') {
    $matrix_rules = @(Expand-RuleReferences -Text $Matches[1])
}
else {
    $issues.Add("cannot locate matrix coverage section")
    $matrix_rules = @()
}

$checklist_text = Read-StrictUtf8 -Path $checklist_path
if ($checklist_text -match '(?s)<!-- RULE-COVERAGE-BEGIN -->(.*?)<!-- RULE-COVERAGE-END -->') {
    $checklist_rules = @(Expand-RuleReferences -Text $Matches[1])
}
else {
    $issues.Add("cannot locate checklist coverage block")
    $checklist_rules = @()
}

foreach ($coverage in @(
    @{ Name = "matrix"; Rules = $matrix_rules },
    @{ Name = "checklist"; Rules = $checklist_rules }
)) {
    $duplicates = @(
        $coverage.Rules |
            Group-Object |
            Where-Object Count -gt 1 |
            ForEach-Object Name
    )
    if ($duplicates.Count -gt 0) {
        $issues.Add("duplicate $($coverage.Name) coverage: $($duplicates -join ', ')")
    }

    $unique_coverage = @($coverage.Rules | Sort-Object -Unique)
    $missing = @($unique_standard_rules | Where-Object { $_ -notin $unique_coverage })
    $extra = @($unique_coverage | Where-Object { $_ -notin $unique_standard_rules })
    if ($missing.Count -gt 0) {
        $issues.Add("missing $($coverage.Name) coverage: $($missing -join ', ')")
    }
    if ($extra.Count -gt 0) {
        $issues.Add("extra $($coverage.Name) coverage: $($extra -join ', ')")
    }
}

$local_link_count = 0
if (-not $SkipLocalLinks) {
    $markdown_files = Get-ChildItem -LiteralPath $root_path -Filter "*.md" -File
    foreach ($markdown_file in $markdown_files) {
        $markdown_text = Read-StrictUtf8 -Path $markdown_file.FullName
        $link_matches = [regex]::Matches($markdown_text, '\[[^\]]+\]\(([^\)]+)\)')
        foreach ($link_match in $link_matches) {
            $target = $link_match.Groups[1].Value.Trim()
            if ($target -match "^(?i:https?://|mailto:)") {
                continue
            }

            $local_link_count++
            $parts = $target -split '#', 2
            $relative_target = [Uri]::UnescapeDataString($parts[0])
            $anchor = ""
            if ($parts.Count -eq 2) {
                $anchor = [Uri]::UnescapeDataString($parts[1]).ToLowerInvariant()
            }

            if ([string]::IsNullOrWhiteSpace($relative_target)) {
                $target_path = $markdown_file.FullName
            }
            else {
                $target_path = [System.IO.Path]::GetFullPath(
                    (Join-Path $markdown_file.DirectoryName $relative_target)
                )
            }

            if (-not (Test-Path -LiteralPath $target_path -PathType Leaf)) {
                $issues.Add("broken local link in $($markdown_file.Name): $target")
                continue
            }

            if ((-not [string]::IsNullOrWhiteSpace($anchor)) -and
                ([System.IO.Path]::GetExtension($target_path) -eq ".md")) {
                $target_text = Read-StrictUtf8 -Path $target_path
                $anchors = @(
                    [regex]::Matches($target_text, '(?m)^#{1,6}\s+(.+?)\s*#*\s*$') |
                        ForEach-Object { Get-MarkdownAnchor -Heading $_.Groups[1].Value }
                )
                if ($anchor -notin $anchors) {
                    $issues.Add("broken local anchor in $($markdown_file.Name): $target")
                }
            }
        }
    }
}

$must_count = @($rule_matches | Where-Object { $_.Groups[2].Value -eq "MUST" }).Count
$project_count = @($rule_matches | Where-Object { $_.Groups[2].Value -eq "PROJECT" }).Count
Write-Host (
    "rules={0} unique={1} must={2} project={3} matrix={4} checklist={5} local_links={6}" -f
        $standard_rules.Count,
        $unique_standard_rules.Count,
        $must_count,
        $project_count,
        (@($matrix_rules | Sort-Object -Unique).Count),
        (@($checklist_rules | Sort-Object -Unique).Count),
        $local_link_count
)

if ($issues.Count -gt 0) {
    foreach ($issue in $issues) {
        Write-Host "ERROR: $issue" -ForegroundColor Red
    }
    exit 1
}

Write-Host "validation_issues=0"
