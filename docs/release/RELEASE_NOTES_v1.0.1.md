# Initial Z: Street Stage+ v1.0.1

**Download `InitialZ_v1.0.1_patch.zip` below.** You need your own ISOs of *Initial D Street Stage* (ULJM05093) and *Wangan Midnight Portable* (ULJM05264). No game is included.

A free, unofficial fan remix of *Initial D Street Stage* (PSP) fused with *Wangan Midnight Portable* (PSP). v1.0.1 is the full game exactly as it was developed, distributed as a patch you apply to your own two discs.

## What's new in v1.0.1
- **The full build.** The new Initial Z opening movie, the Akio title screen, the new car pictures, the Wangan and Hakone course photos, the area-clear screens and all the card art are now in the public release.
- **Street Legends Akio** now drives his own record line. He no longer matches your speed, so a faster run beats him.
- Street Legends Akio is slower on **Wangan** (about 1'29"5) and **Hakone** (about 2'13" up / 2'10" down), where he was out of reach. On those two courses he also no longer gets the 8% catch-up boost when he falls behind.
- The Devil Z Challenge is unchanged.
- New cheat codes: aura km/h per step = 5 (with a caution), Easier Akio and Harder Akio. See docs/CHEATS.md.

## Features
- **The Devil Z and Akio Asakura:**
  - The Devil Z is its own car, with its own HUD, tachometer, sound and tuning.
  - The new **Devil Z Challenge** mode runs on every course, and Akio joins Street Legends.
- **Two new courses:**
  - **Wangan**: a night run on the Shuto expressway, converted from Wangan Midnight Portable's own route data.
  - **Hakone**: the Hakone Turnpike, built from OpenStreetMap and Copernicus elevation data, uphill and downhill.
- **15 Wangan Midnight drivers** in Street Legends, each with their own dialogue and progression. They unlock after you beat Takumi on Akina.
- **7 Wangan Midnight cars**: R33 GT-R, Supra, Z32, Z31, the 964 "Blackbird", Celsior and Mark II. They're on the new INITIAL Z maker page and the Toyota page.
- **The aura system:** AURA TUNE, new game plus star auras, legend auras in races, aura cards from aura drivers, and a Rainbow Aura card for beating Akio on every Devil Z Challenge course.
- **Presentation:** the new Initial Z opening movie, the Akio title screen, a rewritten card reward screen, and a complete English translation with dialogue rewritten for every scene.
- **Snow on every course.**
- **Music:** Wangan Midnight race music. The 30 extra race-music slots (songs 28-57) play Wangan Midnight tracks from your disc. The opening movie plays a Wangan Midnight track, or any song you put in the `music` folder before patching.
- **Cheats:** a PPSSPP cheat file (docs/CHEATS.md in the repository).

## Requirements
- Your own ISO of *Initial D Street Stage* (Japan, ULJM05093), MD5 `225f1f56c37097c7a11ecaddd52abbf1`.
- Your own ISO of *Wangan Midnight Portable* (Japan, ULJM05264), MD5 `85c3abab28df6509911461de9d58b9e9`.
- About 4 GB of free disk space.
- **To play:** PPSSPP (Windows, Android and others) or a PSP that can run ISOs.

## Install
1. Unzip `InitialZ_v1.0.1_patch.zip`. You get a folder called `InitialZ_v1.0.1`.
2. Copy both ISOs into `put your games here` (any file names; they are found by checksum).
3. Optional: copy one song (`.mp3`, `.m4a`, `.wav`, `.wma`, `.aac` or `.flac`) into `music`. It becomes the opening movie's song; the first 108 seconds are used.
4. **Windows:** double-click `Patch Initial Z.bat`. **Linux/macOS:** install xdelta3 (`apt install xdelta3` or `brew install xdelta`) and run `sh patch.sh` (a custom intro song also needs python3, ffmpeg and atracdenc).
5. Wait a few minutes until it says Done. The ISO is checked against its MD5 before the intro song is added.
6. Load `InitialZ_StreetStagePlus_v1.0.1.iso` in PPSSPP.
7. Optional: copy the cheat file (docs/cheats/ULJM05093.ini in the repository) to `PSP/Cheats`.

Your saves from v1.0 carry over. Multiplayer: both players need v1.0.1.

## Credits
- Built by Daniel.
- *Initial D Street Stage* © SEGA. *Initial D* © Shuichi Shigeno / Kodansha.
- *Wangan Midnight Portable* © Genki / Namco Bandai. *Wangan Midnight* © Michiharu Kusunoki / Kodansha.
- Bundled tools: xdelta 3.1.0 by Joshua MacDonald (GPL-2.0, https://github.com/jmacd/xdelta-gpl) and atracdenc 0.2.3 by Daniil Cherednik (LGPL-2.1, https://github.com/dcherednik/atracdenc).

This is a non-commercial fan project. It isn't affiliated with or endorsed by any of these companies or creators. You must own the games you patch.
