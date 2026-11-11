# Put your own song into the Initial Z opening movie (Windows). Called by "Patch Initial Z.bat".
param([string]$Iso, [string]$Song)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$lba = [int64](Get-Content (Join-Path $here 'data\intro_lba.txt'))
$segs = Get-Content (Join-Path $here 'data\intro_segments.txt') | Where-Object { $_.Trim() } | ForEach-Object { $p = $_.Split(' '); ,@([int64]$p[0], [int]$p[1]) }
$sil = [Convert]::FromBase64String((Get-Content (Join-Path $here 'data\silent_frame.b64') -Raw).Trim())
$tmp = Join-Path $env:TEMP ('initialz_intro_' + [guid]::NewGuid().ToString('N') + '.oma')
& (Join-Path $here 'tools\atracdenc.exe') -e atrac3plus -i $Song -o $tmp | Out-Null
if (-not (Test-Path $tmp)) { throw 'atracdenc could not read the song. Try an .mp3, .m4a or .wav file.' }
$d = [IO.File]::ReadAllBytes($tmp); Remove-Item $tmp
if ($d.Length -lt 96 -or [Text.Encoding]::ASCII.GetString($d, 0, 3) -ne 'EA3') { throw 'unexpected atracdenc output' }
$dataOff = $d[4] * 256 + $d[5]; $dataLen = [int64]($d.Length - $dataOff)
if (($dataLen % 2048) -ne 0) { throw 'unexpected ATRAC3plus frame size' }
$nfr = 2343; $skip = 2; $hdr = [byte[]](0x0f,0xd0,0x28,0xff,0,0,0,0)
$have = [Math]::Floor(($dataLen) / 2048)
$ms = New-Object IO.MemoryStream
for ($k = 0; $k -lt $nfr; $k++) {
  $ms.Write($hdr, 0, 8)
  $src = $k + $skip
  if ($src -lt $have) { $ms.Write($d, [int]($dataOff + $src * 2048), 2048) } else { $ms.Write($sil, 0, 2048) }
}
$stream = $ms.ToArray()
$total = 0; foreach ($s in $segs) { $total += $s[1] }
if ($total -ne $stream.Length) { throw "intro layout mismatch ($total vs $($stream.Length))" }
$f = [IO.File]::Open($Iso, 'Open', 'ReadWrite')
try {
  $pos = 0
  foreach ($s in $segs) { $f.Seek($lba * 2048 + $s[0], 'Begin') | Out-Null; $f.Write($stream, $pos, $s[1]); $pos += $s[1] }
} finally { $f.Close() }
$used = [Math]::Min($have - $skip, $nfr) * 2048 / 44100
Write-Host ('Intro song written: ' + (Split-Path -Leaf $Song) + (' ({0:N1} s used)' -f $used))
