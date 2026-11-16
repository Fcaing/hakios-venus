param([string]$File, [string]$Out)
# 从 262144 B 的 cur-pNNN.bin 里抽出可打印串（日志环原始内容），按行写到一个 txt
$bytes = [System.IO.File]::ReadAllBytes($File)
$sb = New-Object System.Text.StringBuilder
$run = New-Object System.Text.StringBuilder
foreach ($b in $bytes) {
    if ($b -ge 32 -and $b -lt 127) { [void]$run.Append([char]$b) }
    else {
        if ($run.Length -ge 8) { [void]$sb.AppendLine($run.ToString()) }
        [void]$run.Clear()
    }
}
if ($run.Length -ge 8) { [void]$sb.AppendLine($run.ToString()) }
[System.IO.File]::WriteAllText($Out, $sb.ToString())
"lines=$((Get-Content $Out).Count)"
