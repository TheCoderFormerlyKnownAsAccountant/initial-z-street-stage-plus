---
name: psp-car-porting
description: Step-by-step method to port a car from one PSP racing game into another so it looks and drives native — locating source model/textures/specs, converting GMO geometry and textures to the target's layout, restyling to the target art direction, synthesizing tuning stages and physics, and wiring it into a car slot. Use for requests like "add the Devil Z from Wangan Midnight Portable to Initial D".
---

# Car porting

## 1. Inventory both sides
- **Source** (e.g. WMP): body GMO + texture set, spec record (name, chassis code, specs), parts variants, engine sound bank.
- **Target** (e.g. Initial D): `data/car/race/<code>_race.bin(.gz)` (in-race model set), `data/car/select/<code>_sel.bin(.gz)` (showroom model), car code table in BOOT.BIN, tuning/physics tables, engine sound `data/sound/se/engine/<id>.bin`, car name text, card art.
- Decompile one target car fully first; choose the **donor**: closest target car by drivetrain, size and layout (S30 Devil Z: front-engine RWD Nissan → donor `nissan_s15` or `nissan_bnr32`-class body proportions; engine sound donor: `s13`/`gtr` banks).

## 2. Geometry
- Export source GMO → OBJ (`gmo.py obj`), apply 0x8015 offset/scale, fix axis order to the target's (compare bboxes of a target car).
- Separate into the target's part structure (body, glass, lights, wheels ×4, brake lights, shadow) and match bone pivots (wheel centers from target `0x8048` translations scaled to the new wheelbase/track).
- Poly budget: stay within ±15% of the donor per LOD. Build LODs by decimation if the target uses more LODs than the source provides.
- If the source only has a low-poly rival model (WMP Devil Z = ~2.5k tris), either accept it, or rebuild/subdivide the body in Blender using the source as reference and the donor for detail level.

## 3. Textures & art style
- Re-map to the target's texture layout and formats (same GIM sizes and palette depths as the donor).
- Target style for Initial D Street Stage: clean anime-toned bodies, strong flat shading, saturated paint, crisp black trim, light baked AO; WMP is grittier/greyscale-shaded. Restyle: remove photographic noise, raise contrast, re-tint to target paint colors, redraw decals (keep Devil Z's dark midnight-blue paint and S30 badges, redraw at target resolution).
- Provide paint variants exactly as the donor does (count and slot order).

## 4. Gameplay data
- Read the donor's tuning stages (Initial D: card-based steps, e.g. `stp1 intake/exhaust`, `stp2 cooling`, ECU resetting, body parts like rear spoiler, intercooler scoop, carbon trunk).
- Build the new car's table: scale power/torque/weight/gearing from real L28-based S30 specs tuned per the Devil Z story (very high power, light, twitchy at the limit), then map onto the donor's stage curve so progression feels like the rest of the roster.
- Visual tuning parts: map source variants (`bd_a/b/c`, `bn_*`, `rs_*`) to target part slots where they exist; disable stages with no visual counterpart rather than inventing mismatched art.

## 5. Wiring
- **Phase A (slot replace)**: write the converted files under the donor's names in a build copy; boot; verify.
- **Phase B (new slot)**: psp-code-patcher extends the car code table (35 entries in Initial D) + every parallel table (names, specs, tuning, sound, unlock flags), adds relocations, checks save data.
- Text: car name/maker strings and card text through psp-translator.

## 6. QA
Car select preview, garage tuning screens, race (day/night/rain), replay, mirrors, shadows, collision box, AI using the car as a rival.

## Worked example: Devil Z → Initial D (build 2)
`remix_build/build2/src/build_devilz.py`: WMP 744/745/746 → nissan_s15 slot. Axis map WMP→IDSS `(x,y,z) → (−z, y − 0.217, x)` (rotation, keeps winding), wheels to ±0.713 / ±1.153, body paint = styled line texture × runtime paint colour (`--plain` for untextured), trim textures written over S15 texture names the stock body kit no longer uses, all body-kit slots collapsed to a degenerate triangle so tuning stages keep working. Preview with `preview_car.py`.

## Adding a new car slot (checklist from Initial D car #36, m26/car36)
- Map every per-car table: code/name table, engine index, physics (stride), engine records (3 sets), 6-speed flags, top-speed rows per course, tuning records, sound index, model-list/sel/race file codes, rival car data, CAR DATA rows, paint colour tables (one per paint × car — an empty entry = black car + crash on buy), paint/parts pointer tables (keep their relocations!).
- Scan the BOOT for the car count (35/0x23) and count±1 in comparisons; confirm each is car-related before changing.
- Name/texture slots: a stock overlay may point at an "empty" slot on purpose (slot 73) — don't put the new name there.
- Maker list: order/count per maker, the per-maker page size, and the 'hidden last car' rule; maker-select grid cells are separate textures (add a cell pair).
- Garage: car-id bits in the packed entry must fit the new id; pack/unpack functions.
- Records: give the new car its own record slots or share an unused car's — never let it index past the table (it overwrote the next course's AE86 record once).
- Save migration: one-time convert with a marker byte in a verified-spare save area; keep owned entries.
- Unlock rule: gate the New Car list entry and any related mode with explicit save checks.
