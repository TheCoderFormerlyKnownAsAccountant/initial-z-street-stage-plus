# Release patch tools

v1.0.1 is distributed as an xdelta patch against the player's own two discs, concatenated
(Initial D Street Stage ISO followed by Wangan Midnight Portable ISO).

- `makepub.py` builds the public ISO from the development build: the build 60 executable, the opening movie with a
  Wangan Midnight Portable track instead of the development song, Wangan Midnight Portable tracks in the 30 custom
  race-music slots, and neutral song names in the BGM selector and Project D Web. It zeroes the old extents of every
  replaced file, runs `cleanslack.py`, verifies every changed file and lba.dat, then encodes and test-decodes the patch.
- `cleanslack.py` rewrites every byte of the image that no file, directory, path table or lba.dat record uses with the
  stock disc's byte at that offset (zero past its end), so nothing left over from earlier builds stays in the image.
- `Patch Initial Z.bat` / `patch.sh` are the player-side patchers shipped in the release zip with xdelta 3.1.0.
- `intro_song.ps1` / `intro_song.py` encode the player's song with atracdenc and write it over the opening movie's ATRAC3plus frames in place (`data/intro_segments.txt` lists the audio payload ranges inside opening.pmf; only those bytes change).
