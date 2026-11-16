# run-p104.ps1 -- run one payload on the phone, doing the loader dance correctly.
#
#   .\run-p104.ps1 -Payload p-p104.bin -Tag p104
#
# What the phone must be doing when this starts: sitting in the *ABL* fastboot
# (the one that answers `fastboot devices` with a real serial).  The script
# boots the loader itself, waits for xnuloader to actually answer, and only
# then stages anything.  Every step is checked; nothing is swallowed.
#
# Every fastboot call goes through FB below, which captures stdout and stderr
# into plain text:  PowerShell 5.1 turns a native command's stderr into error
# records, and `-match "error"` then tripped over "NativeCommandError".

param(
  [string]$Payload = "p-p104.bin",
  [string]$Tag     = "p104",
  [int]   $RunSeconds = 110,
  [switch]$SkipSystem
)

$ErrorActionPreference = "Continue"
$env:Path = "C:\platform-tools;$env:Path"
$RECON = "C:\Users\Administrator\Documents\deepseek-harness\default-workspace\venus-recon"
$FBEXE = "C:\platform-tools\fastboot.exe"

function Fail($what) { Write-Host "      FAILED: $what" -ForegroundColor Red; exit 1 }
function Note($what) { Write-Host "      $what" }

function FB {
  param([string[]]$fbargs)
  $o = [IO.Path]::GetTempFileName()
  $e = [IO.Path]::GetTempFileName()
  $p = Start-Process -FilePath $FBEXE -ArgumentList $fbargs -NoNewWindow -Wait -PassThru `
        -RedirectStandardOutput $o -RedirectStandardError $e
  $text = ""
  if (Test-Path $o) { $text += (Get-Content $o -Raw -ErrorAction SilentlyContinue) }
  if (Test-Path $e) { $text += (Get-Content $e -Raw -ErrorAction SilentlyContinue) }
  Remove-Item $o, $e -Force -ErrorAction SilentlyContinue
  if ($null -eq $text) { $text = "" }
  return [pscustomobject]@{ Code = $p.ExitCode; Text = ($text -replace "`r", "").Trim() }
}

function Devices { return ((FB @("devices")).Text) }

function Wait-Device([string]$want, [int]$seconds) {
  $t0 = Get-Date
  while (((Get-Date) - $t0).TotalSeconds -lt $seconds) {
    $d = Devices
    if ($d -match $want) { return $d }
    Start-Sleep -Seconds 2
  }
  return $null
}

Write-Host "== 1. is the phone in fastboot at all?" -ForegroundColor Cyan
$d = Wait-Device "fastboot" 120
if (-not $d) { Fail "no fastboot device after 120 s -- power-cycle the phone and try again" }
Note $d

if ($d -notmatch "xnuloader") {
  Write-Host "== 2. booting the loader (img-wr2.bin)" -ForegroundColor Cyan
  $fb = FB @("boot", "$RECON\img-wr2.bin")
  Note $fb.Text
  if ($fb.Code -ne 0 -or $fb.Text -match "FAILED") { Fail "fastboot boot refused" }

  Write-Host "== 3. waiting for xnuloader to answer" -ForegroundColor Cyan
  $d = Wait-Device "xnuloader" 150
  if (-not $d) { Fail "the loader never answered as xnuloader" }
  Note $d
} else {
  Write-Host "== 2/3. already in the loader" -ForegroundColor Cyan
}

Write-Host "== 4. stopping any kernel that is still running" -ForegroundColor Cyan
for ($i = 0; $i -lt 2; $i++) {
  $fb = FB @("oem", "stop")
  Note ("stop " + $(if ($fb.Text) { $fb.Text } else { "ok" }))
  Start-Sleep -Seconds 1
}

if (-not $SkipSystem) {
  Write-Host "== 5. oem ramdisk" -ForegroundColor Cyan
  $fb = FB @("oem", "ramdisk")
  if ($fb.Text -match "FAILED|unknown") { Fail "oem ramdisk: $($fb.Text)" }
  Note "ok"

  Write-Host "== 6. staging system-hello.apfs (about 65 s)" -ForegroundColor Cyan
  $t0 = Get-Date
  $fb = FB @("stage", "$RECON\system-hello.apfs")
  Note ("done in {0:N0} s: {1}" -f ((Get-Date) - $t0).TotalSeconds, $fb.Text)
  if ($fb.Code -ne 0 -or $fb.Text -match "FAILED|error|max allowed") { Fail "stage system: $($fb.Text)" }
} else {
  Write-Host "== 5/6. system not staged (-SkipSystem)" -ForegroundColor Yellow
}

Write-Host "== 7. staging $Payload" -ForegroundColor Cyan
$fb = FB @("stage", "$RECON\$Payload")
Note $fb.Text
if ($fb.Code -ne 0 -or $fb.Text -match "FAILED|error") { Fail "stage payload: $($fb.Text)" }

Write-Host "== 8. oem run" -ForegroundColor Cyan
$fb = FB @("oem", "run")
if ($fb.Text -match "FAILED|unknown") { Fail "oem run: $($fb.Text)" }
Note "kicked off"

Write-Host "== 9. waiting for the kernel to hand back to the loader (max $RunSeconds s)" -ForegroundColor Cyan
$t0 = Get-Date
$back = $null
$left = $false
while (((Get-Date) - $t0).TotalSeconds -lt $RunSeconds) {
  $d = Devices
  $elapsed = ((Get-Date) - $t0).TotalSeconds
  if (-not $left) {
    # 内核接管后 USB 会重新枚举，设备名不再是 xnuloader
    if ($d -notmatch "xnuloader") { $left = $true; Note ("kernel took over after {0:N0} s" -f $elapsed) }
    elseif ($elapsed -gt 25) { $left = $true; Note "giving up on seeing the loader go away" }
  } else {
    if ($d -match "xnuloader") { $back = $d; Note ("back in the loader after {0:N0} s" -f $elapsed); break }
  }
  Start-Sleep -Seconds 2
}

Write-Host "== 10. back in the loader? reading the dump" -ForegroundColor Cyan
$d = $back
if (-not $d) { $d = Wait-Device "xnuloader" 90 }
if (-not $d) {
  Write-Host "      the loader is not answering -- the kernel is probably still up or the machine is frozen" -ForegroundColor Yellow
} else {
  $fb = FB @("oem", "dump", "logdump", "0", "100000")
  Note $fb.Text
  Start-Sleep -Seconds 2
  $ld = "$RECON\ld-$Tag.bin"
  $fb = FB @("get_staged", $ld)
  Note $fb.Text
  if (Test-Path $ld) {
    $len = (Get-Item $ld).Length
    Write-Host "      ld-$Tag.bin: $len bytes" -ForegroundColor Green
    $b = [IO.File]::ReadAllBytes($ld)
    $s = [Text.Encoding]::ASCII.GetString($b)
    Write-Host "== 11. the interesting lines ==" -ForegroundColor Cyan
    ($s -split "`n") | Where-Object { $_ -match "pcie: (4|5):|panic|sid|256|watch 1 of|xnuloader|hakios" } | Select-Object -Last 40 | ForEach-Object { Note $_.TrimEnd() }
  }
}

