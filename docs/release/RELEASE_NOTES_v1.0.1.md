# Initial Z: Street Stage+ v1.0.1 (clean install kit)

## What's new in v1.0.1
- Street Legends Akio now drives his own record line. He no longer matches your speed, so a faster run beats him.
- Street Legends Akio is slower on Wangan (about 1'29"5) and Hakone (about 2'13" up / 2'10" down), where he was out of reach.
- On Wangan and Hakone, Street Legends Akio no longer gets the 8% catch-up boost when he falls behind.
- The Devil Z Challenge is unchanged.

A free, unofficial fan remix of *Initial D Street Stage* (PSP, ULJM05093) fused with *Wangan Midnight Portable*
(PSP, ULJM05264). This kit contains no game data. It rebuilds Initial Z on your computer from your own discs.

## Features
- **The Devil Z and Akio Asakura:**
  - The Devil Z is its own car, with its own HUD, tachometer, sound and tuning.
  - The new **Devil Z Challenge** mode runs on every course, and Akio joins Street Legends.
- **Two new courses:**
  - **Wangan**: a night run on the Shuto expressway, converted from Wangan Midnight Portable's own route data.
  - **Hakone**: the Hakone Turnpike, built from OpenStreetMap and Copernicus elevation data, uphill and downhill.
- **15 Wangan Midnight drivers** in Street Legends, each with their own dialogue and progression. They unlock after you beat Takumi on Akina.
- **7 Wangan Midnight cars**: R33 GT-R, Supra, Z32, Z31, the 964 "Blackbird", Celsior and Mark II. They're on the new INITIAL Z maker page and the Toyota page.
- **The aura system:**
  - AURA TUNE, plus new game plus star auras and legend auras in races.
  - Aura cards drop only from rivals who have an aura.
  - A Rainbow Aura card for beating Akio on every Devil Z Challenge course.
- **Interface and presentation:**
  - A rewritten card reward screen.
  - A complete English translation, with dialogue rewritten for every scene.
  - Snow on every course. (The new Initial Z opening movie arrives in v1.1; v1.0 keeps the original opening.)
- **Music:** Wangan Midnight race music, plus 30 race-music slots you fill with your own songs.
- **Cheats:** a PPSSPP cheat file (see CHEATS.md in the project repository).

## Requirements
- Your own ISO of *Initial D Street Stage* (Japan, ULJM05093).
- Your own ISO of *Wangan Midnight Portable* (Japan, ULJM05264).
- About 4 GB of free disk space.
- **Windows:** nothing to install; a private Python is included.
- **Linux/macOS:** Python 3.10–3.12. `install.sh` fetches the pinned packages.
- **Optional:** your own music for the 30 race-music slots. For .mp3 and similar formats, put ffmpeg.exe into `tools`.
- **To play:** PPSSPP (Windows, Android and others) or a PSP that can run ISOs.

## Install
1. Unzip the kit.
2. Put both ISOs into `put your games here`.
3. Optionally, put your songs into `music`.
4. Run `Install Initial Z.bat` on Windows, or `./install.sh` on Linux or macOS. It takes about 15–30 minutes on a typical PC. It uses all CPU cores; antivirus scanning and slower or battery-powered laptops can make it longer.
5. Load `InitialZ_StreetStagePlus_v1.0.1.iso` in PPSSPP.
6. Optionally, copy the cheat file to `PSP/Cheats`.

Both discs are md5-checked, and every rebuilt file is checked against its expected checksum. The result is the same byte for byte on Windows, Linux and macOS.

Multiplayer: both players need v1.0.1. Song choices are local, and empty song slots are filled with defaults.

## Changes since the first test
- Install is about 3× faster: converters run side by side, the Wangan converter builds its sections in parallel, and texture re-encoding is vectorised. The output is byte-identical.
- The file-select header now reads "SELECT A DRIVER FILE", and SAVE/LOAD headers are clean English. They no longer mix in Japanese text.
- 41 more menu labels on painted backgrounds are rebuilt cleanly.

## Known differences from the private development build
Everything that came from the games' own pictures is rebuilt from your discs or uses your disc's stock equivalent. A few screens therefore look slightly different from the build shown in videos:

| Area | What you'll see |
|---|---|
| Akio's talk portrait | Rebuilt from his Wangan Midnight portrait with matching framing; the colours and edges differ very slightly. |
| Course-select and Wangan talk photos | The Wangan and Hakone photos use the stock Happogahara course photos. |
| New-car pictures (car select, garage, maker page) | Stock pictures of the base car each one is built on. Their names and data are correct. |
| Area-clear screens | Stock artwork behind our English text. |
| Card art and viewer | A few card pictures use the closest stock card art. |
| Some menu labels on painted backgrounds | Background repainted automatically behind our English text; faint smudges are possible. |
| Title screen | Stock title art without Akio. Our Initial Z logo is unchanged. |
| Project D Web song list | Shows your own song names, by design. |
| Loading-screen logo and a few font sheets | Very slightly different edges from re-encoding. |

Gameplay, courses, cars, AI, cards, dialogue and menus work the same as the private build. The opening movie is the original Initial D one in v1.0; the Initial Z intro comes in v1.1.

## Credits
- Built by Daniel.
- *Initial D Street Stage* © SEGA. *Initial D* © Shuichi Shigeno / Kodansha.
- *Wangan Midnight Portable* © Genki / Namco Bandai. *Wangan Midnight* © Michiharu Kusunoki / Kodansha.

This is a non-commercial fan project. It isn't affiliated with or endorsed by any of these companies or creators. You must own the games you install it with.

## Licences
- **Our code, tools and documentation:** MIT.
- **Hakone road data:** © OpenStreetMap contributors, ODbL 1.0.
- **Elevation:** produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA.
- **Bundled components:** Python, numpy, scipy, Pillow, zopfli, pycdlib and the DejaVu and Liberation fonts. Their licences are in `LICENSES/`.
- **Game content:** this kit doesn't cover the games or anything taken from them, which comes only from your own discs.
