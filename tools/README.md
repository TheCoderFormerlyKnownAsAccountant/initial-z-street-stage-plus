# Tools

These are the project-specific tools, published as a record of how Initial Z was built. The general format tools (ISO, XBB, GIM, GMO, @ANA, UCL, MIPS helpers) are in [`../plugin/scripts/`](../plugin/scripts/).

Paths are relative to a workspace:
- `game/`: files extracted from **your own** disc images.
- `work/`: intermediate output.
- `plugin/scripts`: the plugin's core tools.

Several scripts belong to one specific build step and import helpers from that step's folder, so treat them as readable references rather than a one-command build. No game data is included; anything a script needs comes from your own extracted copy.

| Folder | Contents |
|---|---|
| `course/` | `hwline.py` builds the Wangan centre, edge and AI lines from WMP's lane ribbons. `chain.py` and `hkline.py` turn OpenStreetMap ways plus DEM elevation into the Hakone line. `bend.py` maps stock scenery onto a new road. `colli_hw.py` builds collision. `camdata_hk.py` places replay cameras. `build_lod.py` builds the mid-distance LODs. `progress_sim.py`, `streamer_sim.py` and `game_sim.py` model the engine's progress, streaming and wrong-way logic, to prove a course drives before it is run. |
| `movie/` | `make_intro.py` and `chase.py` render the opening movie (cars, portraits, auras, camera moves with motion blur). `mux_psmf.py` writes a PSMF/PMF. `silent_at3p.py` makes a silent ATRAC3plus track. `build48.py` encodes the song and muxes it into the movie (it uses atracdenc, LGPL, built separately). |
| `audio/` | `at3enc.py` is an ATRAC3 encoder for race BGM. |
| `talk/` | `talkgrammar45.py` validates talk tables against the game's script grammar. `m46_talk_boot.py` fixes English lines being run as script commands. |
| `boot/` | Examples of the chainable executable patch scripts and their verifiers: cards screen, Hakone course bank, Wangan rivals and progression, minimap, auras and Akio tuning. Each one asserts the input md5, writes new code only inside its reserved region, adds relocation entries, and is checked by relocation simulation and Unicorn runs. |
