#!/bin/sh
# Initial Z: Street Stage+ v1.0.1 patcher for Linux/macOS.
# Needs xdelta3 (apt install xdelta3 / brew install xdelta). For an intro song: python3, ffmpeg and atracdenc.
cd "$(dirname "$0")"
command -v xdelta3 >/dev/null 2>&1 || { echo "Please install xdelta3 first."; exit 1; }
md5() { if command -v md5sum >/dev/null 2>&1; then md5sum "$1" | cut -d' ' -f1; else md5 -q "$1"; fi; }
IDSS=""; WMP=""
for f in "put your games here"/*.iso; do
  [ -f "$f" ] || continue
  m=$(md5 "$f")
  [ "$m" = 225f1f56c37097c7a11ecaddd52abbf1 ] && IDSS="$f"
  [ "$m" = 85c3abab28df6509911461de9d58b9e9 ] && WMP="$f"
done
[ -n "$IDSS" ] || { echo "Initial D Street Stage (ULJM05093, MD5 225f1f56c37097c7a11ecaddd52abbf1) not found in 'put your games here'."; exit 1; }
[ -n "$WMP" ] || { echo "Wangan Midnight Portable (ULJM05264, MD5 85c3abab28df6509911461de9d58b9e9) not found in 'put your games here'."; exit 1; }
echo "Joining the two discs into a temporary file..."
cat "$IDSS" "$WMP" > _source.tmp || exit 1
echo "Applying the patch..."
xdelta3 -d -f -B 1073741824 -s _source.tmp InitialZ_v1.0.1.xdelta InitialZ_StreetStagePlus_v1.0.1.iso; e=$?
rm -f _source.tmp
[ $e -eq 0 ] || { echo "Patching failed."; exit 1; }
[ "$(md5 InitialZ_StreetStagePlus_v1.0.1.iso)" = 4b42a4f7cc4620d35d228881eea080cc ] || { echo "WARNING: checksum mismatch; re-download the patch."; exit 1; }
echo "Checksum OK."
SONG=$(ls music/*.mp3 music/*.m4a music/*.wav music/*.flac music/*.aac 2>/dev/null | head -n 1)
if [ -n "$SONG" ]; then
  echo "Adding your intro song: $SONG"
  python3 intro_song.py InitialZ_StreetStagePlus_v1.0.1.iso "$SONG" || echo "Could not add the intro song (needs python3, ffmpeg and atracdenc). The game still works."
fi
echo "Done: InitialZ_StreetStagePlus_v1.0.1.iso is ready. Load it in PPSSPP."
