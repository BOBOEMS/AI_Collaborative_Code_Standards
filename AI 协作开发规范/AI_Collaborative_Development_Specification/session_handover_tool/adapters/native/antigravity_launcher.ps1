#Requires -Version 7.0
$ErrorActionPreference='Stop'
[Console]::InputEncoding=[System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false)
$OutputEncoding=[System.Text.UTF8Encoding]::new($false)
try {
    $request=[Console]::In.ReadToEnd()|ConvertFrom-Json
    $target=$request.target
    $servers=@(Get-CimInstance Win32_Process|Where-Object{$_.Name -eq 'language_server.exe' -and $_.CommandLine -match 'override_ide_name antigravity'})
    if($target.driver.process_id){$servers=@($servers|Where-Object{$_.ProcessId -eq $target.driver.process_id})}
    if($servers.Count -ne 1){throw 'Select a unique authenticated Antigravity language server'}
    $server=$servers[0]
    $csrf=[regex]::Match($server.CommandLine,'--csrf_token\s+(\S+)').Groups[1].Value
    $port=Select-String -LiteralPath $target.driver.log -Pattern 'listening on random port at (\d+) for HTTP'|Select-Object -Last 1
    if(-not $csrf -or -not $port){throw 'Authenticated Antigravity endpoint unavailable'}
    $env:ANTIGRAVITY_LS_ADDRESS='http://127.0.0.1:'+$port.Matches[0].Groups[1].Value
    $env:ANTIGRAVITY_CSRF_TOKEN=$csrf
    $env:PYTHONIOENCODING='utf-8'
    $env:PYTHONUTF8='1'
    $python=if($target.driver.python){$target.driver.python}else{'python'}
    $request|ConvertTo-Json -Depth 30 -Compress|& $python -B (Join-Path $PSScriptRoot 'antigravity_rpc.py')
    exit $LASTEXITCODE
} catch {
    @{ok=$false;code='backend_unavailable';message='Antigravity host discovery failed; check authenticated host/log configuration';uncertain=$false}|ConvertTo-Json -Compress
    exit 1
}
