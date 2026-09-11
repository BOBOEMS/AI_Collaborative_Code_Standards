#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$CompilerPath,
    [Parameter(Mandatory = $true)][string]$ErrorHeaderPath,
    [Parameter(Mandatory = $true)][string[]]$SourcePath,
    [string[]]$CompilerArgument = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# 仅支持 GCC 预处理。调用方在项目构建目录运行并传入实际预处理配置。
# 拒绝会写入文件或隐含其他参数的常用选项；脚本强制输出到标准输出。
foreach ($argument in $CompilerArgument) {
    if ($argument -match '^@|^-o|^-M|^-(c|S|E|P)$|^-d[DMNU]|^-f(preprocessed|directives-only)|^-save-temps|^-Wp,|^-Xpreprocessor') {
        throw "不支持参数 $argument；只传入实际构建的包含目录、宏、CPU/ABI 等预处理配置。"
    }
}
$compiler = (Get-Command $CompilerPath -CommandType Application -ErrorAction Stop).Source
$authoritative_header = (Resolve-Path -LiteralPath $ErrorHeaderPath).Path
$contract = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'checks/error_macro_contract.json') `
    -Raw -Encoding utf8 | ConvertFrom-Json -AsHashtable

# 裁剪只允许删除未使用项，所有保留项及别名目标必须仍与完整目录一致。
$retained = [System.Collections.Generic.Dictionary[string,string]]::new([StringComparer]::Ordinal)
foreach ($line in (Get-Content -LiteralPath $authoritative_header -Encoding utf8)) {
    if ($line -match '^\s*#\s*define\s+(\w+)(.*)$') {
        $name = $Matches[1]
        $body = ($Matches[2] -split '/\*', 2)[0].Trim()
        if ($name -eq '__ERROR_H' -and $body -eq '') { continue }
        if ($retained.ContainsKey($name) -or $contract.Keys -cnotcontains $name -or
            $body -cne $contract[$name]) {
            throw "错误码头文件的宏 $name 不符合冻结契约。"
        }
        $retained[$name] = $body
    }
}
if (-not $retained.ContainsKey('ERROR_OK')) { throw '错误码头文件缺少 ERROR_OK。' }
foreach ($name in $retained.Keys) {
    $body = $retained[$name]
    if ($body -match '^[A-Z][A-Z0-9_]*$' -and -not $retained.ContainsKey($body)) {
        throw "保留别名 $name 时必须同时保留 $body。"
    }
}

foreach ($source in $SourcePath) {
    $resolved_source = (Resolve-Path -LiteralPath $source).Path
    $arguments = @($CompilerArgument) + @('-x', 'c', '-E', '-dD', '-Werror', '-o', '-', $resolved_source)
    $output = @(& $compiler @arguments 2>&1 | ForEach-Object { $_.ToString() })
    $compiler_exit = $LASTEXITCODE
    if ($compiler_exit -ne 0) {
        $details = ($output | Where-Object { $_ -match 'error:|warning:|fatal error:' } |
            Select-Object -First 8) -join "`n"
        throw "预处理失败：$source（退出码 $compiler_exit）。`n$details"
    }

    $includes = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $final_macros = [System.Collections.Generic.Dictionary[string,string]]::new([StringComparer]::Ordinal)
    $macro_conflicts = [System.Collections.Generic.List[string]]::new()
    $current_file = ''
    foreach ($line in $output) {
        if ($line -match '^#\s+\d+\s+"([^"]+)"') {
            $include_path = $Matches[1].Replace('\\', '\')
            $current_file = $include_path
            if (Test-Path -LiteralPath $include_path -PathType Leaf) {
                $current_file = (Resolve-Path -LiteralPath $include_path).Path
                [void]$includes.Add($current_file)
            }
        }
        elseif ($line -match '^#define\s+(\w+)\s+(.+)$') {
            $name = $Matches[1]
            $final_macros[$name] = $Matches[2].Trim()
            if ($retained.ContainsKey($name) -and $current_file -ine $authoritative_header) {
                $macro_conflicts.Add("$name 在 $current_file 中另有定义")
            }
        }
        elseif ($line -match '^#undef\s+(\w+)') {
            $name = $Matches[1]
            [void]$final_macros.Remove($name)
            if ($retained.ContainsKey($name)) { $macro_conflicts.Add("$name 在 $current_file 中被取消定义") }
        }
    }
    if (-not $includes.Contains($authoritative_header)) {
        Write-Output "SKIP: $source 未使用指定的 error.h；不计入该目录的检查覆盖。"
        continue
    }
    if ($macro_conflicts.Count -gt 0) {
        $preview = ($macro_conflicts | Select-Object -First 8) -join '；'
        throw "错误码定义冲突：$source，共 $($macro_conflicts.Count) 项，最多展示 8 项。$preview"
    }
    foreach ($include_path in $includes) {
        $leaf = [System.IO.Path]::GetFileName($include_path)
        if ($leaf -ieq 'errno.h' -or
            ($leaf -ieq 'error.h' -and $include_path -ine $authoritative_header)) {
            throw "错误码包含冲突：$source 同时使用权威 error.h 和 $include_path。"
        }
    }
    foreach ($name in $retained.Keys) {
        if (-not $final_macros.ContainsKey($name) -or $final_macros[$name] -cne $retained[$name]) {
            throw "最终宏值漂移：$source 中 $name 与权威 error.h 不一致。"
        }
    }
    Write-Output "PASS: $source 的错误码包含链和 $($retained.Count) 个保留宏一致。"
}
