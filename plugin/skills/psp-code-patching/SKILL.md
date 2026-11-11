---
name: psp-code-patching
description: How to analyze and patch PSP game code (Allegrex MIPS) — reading BOOT.BIN/decrypted EBOOT, finding tables and functions, relocation-safe edits, free space, armips patches, CWCheat test patches, PPSSPP debugging. Use when adding car/course slots, new menus or game modes, extending music tables, or changing how text is drawn.
---

# PSP code patching

## Getting code
- `PSP_GAME/SYSDIR/BOOT.BIN` is frequently a plain ELF identical in code to EBOOT.BIN — check `\x7fELF`. Initial D (ULJM05093) and Wangan Midnight Portable (ULJM05264) both ship plain BOOT.BINs.
- Else: PPSSPP → Settings → Tools → Developer tools → "Dump decrypted EBOOT.BIN on game boot" (lands in `memstick/PSP/SYSTEM/DUMP/`).
- `mips_tool.py info` lists sections; keep `.rel.text` / `.rel.data` — they mark every absolute address.

## Addressing
- `e_type 0xFFA0` = relocatable executable: first PT_LOAD vaddr 0, file offset `p_offset` (0x54 typical). `vaddr = file_off − p_offset`.
- PPSSPP base for the main module is usually 0x08804000 → runtime = 0x08804000 + vaddr (confirm in the PPSSPP debugger module list).
- Pointers in `.data` are stored as vaddrs and fixed up at load via relocations. A new pointer you write needs a new relocation entry (type R_MIPS_32) or it will point into low memory.

## Finding things
1. `mips_tool.py str BOOT.BIN <text>` → file offset/vaddr of a string or path.
2. `mips_tool.py ptr` / `xref` → tables holding that vaddr, then `lui/addiu` builders in code.
3. `dis` around the consumer; table stride shows as `sll` by 2/3/4 and `addu`.
4. At runtime: PPSSPP debugger breakpoint on the function, or memory breakpoint on the table; IO log (Debug level) shows file open order.

## Patch styles (prefer top to bottom)
1. **Data edit in place**: change a string, a table value, a pointer to an existing string.
2. **Slot replacement**: point an existing slot (car/course/song) at new files.
3. **Table relocation**: copy table to free space with extra entries, retarget every reference (code `lui/addiu` and data words), update count constants, add relocations.
4. **Hook**: `j` to a code cave, run new logic, return. Use when menus/modes need new behaviour. Keep delay slots in mind (instruction after a branch/jump executes first).
5. **PRX plugin**: for large additions (custom music browser), load a small module from `USRDIR` that hooks functions at runtime — keeps the EBOOT nearly untouched.

## Deliver patches as
- `work/<game>/patches/NNN-name.asm` for armips (`.open "BOOT.BIN",0x0` with `.orga` file offsets) or `NNN-name.json` `[{"file_offset":..,"old":"hex","new":"hex","why":".."}]`.
- Optional `ULJMxxxxx.ini` CWCheat lines `_L 0x2XXXXXXX 0xVVVVVVVV` (address = runtime − 0x08800000) for quick in-emulator tests.

## Checklist before handing to the recompiler
- Old bytes verified before writing new ones.
- No relocation entry left pointing at a moved/removed word.
- Free space claimed in `SPACE.md` and not reused by two patches.
- Save data: adding cars/courses/songs can change save-structure sizes — check save load on an existing memory-card save.

## Remix region & heap safety (learned on Initial D, builds 28–32)
- **Check where the heap goes before appending code.** Find the game's sbrk/heap creation (newlib `_sbrk`, sceKernelAllocPartitionMemory, Create*Fpl/Vpl). In PPSSPP the heap block can land *inside* code you appended past the original ELF end: everything works until a big scene allocates over your hooks. Look at PPSSPP's memory-allocation view (block names like `UserSbrk`).
- **Reserve your region at module start**: hook early (before the heap is made) and AllocAt the free part of [code start, ceiling) as its own block; shrink the heap size word only by verified headroom. Expose a status word for QA.
- **Ceiling discipline**: keep all new code/data below the reserved ceiling; record each fork's range in a region table (NOTES) before writing.
- **Chained, re-runnable patch scripts**: one script per feature, input BOOT → output BOOT, refuses to run twice, checks old bytes, allocates only inside its assigned range, adds its own relocations. Build = run the chain in a fixed order; re-run all verifiers on the final output.
- **Verify pattern**: (1) relocation simulation — load the ELF at 0x08804000, apply .rel, disassemble hook sites and targets; (2) unicorn-engine runs of each hook with realistic register/memory state (per mode/course/car) checking outputs and preserved registers.
- **Double-relocation pitfall**: if the instruction you redirect already has a relocation (e.g. an existing `jal`), do NOT add a second one — the base is added twice (crash "jump to 0x0155xxxx").
- When widening a fixed-count table, scan for the count, count−1 and count+1 as immediates (`slti/sltiu/addiu`) and for every reference to the table base via relocations; also check tables that sit right after it (moving a neighbour's references by accident broke race-start names once).
