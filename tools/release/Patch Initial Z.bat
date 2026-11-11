@echo off
title Initial Z: Street Stage+ v1.0.1 patcher
cd /d "%~dp0"
echo Initial Z: Street Stage+ v1.0.1 patcher
echo.
set "IDSS="
set "WMP="
echo Looking for your games in "put your games here" (checking each ISO takes a few seconds)...
for %%F in ("put your games here\*.iso") do call :check "%%~fF"
if not defined IDSS (echo Could not find Initial D Street Stage ^(ULJM05093^) in "put your games here". & echo Expected MD5 225f1f56c37097c7a11ecaddd52abbf1 & goto end)
if not defined WMP (echo Could not find Wangan Midnight Portable ^(ULJM05264^) in "put your games here". & echo Expected MD5 85c3abab28df6509911461de9d58b9e9 & goto end)
echo Found: %IDSS%
echo Found: %WMP%
echo.
echo Joining the two discs into a temporary file (about 1.5 GB)...
copy /b "%IDSS%" + "%WMP%" "_source.tmp" >nul || (echo Could not write the temporary file. Check free disk space ^(about 4 GB needed^). & goto end)
echo Applying the patch (a few minutes)...
"tools\xdelta3.exe" -d -f -B 1073741824 -s "_source.tmp" "InitialZ_v1.0.1.xdelta" "InitialZ_StreetStagePlus_v1.0.1.iso"
set ERR=%errorlevel%
del "_source.tmp"
if not "%ERR%"=="0" (echo Patching failed. & goto end)
echo Checking the result...
call :md5 "InitialZ_StreetStagePlus_v1.0.1.iso"
if /i not "%H%"=="4b42a4f7cc4620d35d228881eea080cc" (echo WARNING: the ISO checksum does not match. Re-download the patch and try again. & goto end)
echo Checksum OK.
set "SONG="
for %%S in ("music\*.mp3" "music\*.m4a" "music\*.wav" "music\*.wma" "music\*.aac" "music\*.flac") do if not defined SONG set "SONG=%%~fS"
if defined SONG (
  echo.
  echo Adding your intro song: %SONG%
  powershell -NoProfile -ExecutionPolicy Bypass -File "intro_song.ps1" -Iso "%~dp0InitialZ_StreetStagePlus_v1.0.1.iso" -Song "%SONG%" || echo Could not add the intro song. The game still works, with the default intro song.
) else (
  echo No song in the "music" folder: the intro keeps its default Wangan Midnight track.
)
echo.
echo Done: InitialZ_StreetStagePlus_v1.0.1.iso is ready. Load it in PPSSPP.
:end
echo.
pause
exit /b

:md5
set "H="
for /f "tokens=* delims=" %%L in ('certutil -hashfile "%~1" MD5 ^| findstr /v ":"') do if not defined H set "H=%%L"
if defined H set "H=%H: =%"
goto :eof

:check
call :md5 "%~1"
if /i "%H%"=="225f1f56c37097c7a11ecaddd52abbf1" set "IDSS=%~1"
if /i "%H%"=="85c3abab28df6509911461de9d58b9e9" set "WMP=%~1"
goto :eof
