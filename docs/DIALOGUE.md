# Dialogue: how it was done

## Translation (builds 12–14)
- All 826 stock rival talk scripts were translated to English: 4,891 lines, with speaker names and inserted car names.
- Talk now uses a half-width 8×16 font, added through a code hook so English fits the boxes.
- About 530 system messages and the Card Collection text were translated alongside.

## The "blank talk" bug (build 46)
After races, many talks showed only the speaker's name. The cause is that the talk interpreter reads the **first character of each line** as a command if it is a letter:
- "Not tonight." ran `N` (end of page).
- "Even an old GT-R…" ran `E` (end of talk).

Japanese lines never start with ASCII letters, so the original game never hit this. The fix marks every dialogue line with an invisible prefix at load time and strips it before drawing. Running the game's own talk code on all 1,210 tables showed **5,791** dialogue lines reaching the screen, up from **1,107**.

## Original writing for Akio and the Wangan drivers (build 56)
An audit mapped every reachable scene (first meeting, meet again, win, loss, retire or time-up, rematch yes/no) and found:
- Akio's 72 lines were built from about 25 sentences, so scenes repeated each other.
- The Wangan drivers had 10 texts spread over 24 scenes.
- 42 stock tables repeated a line back to back.

Akio and all 15 Wangan drivers were rewritten with **original lines**, none quoted from the manga or anime:
- **Akio's arc** runs from the cursed Devil Z, to growing respect for Bunta and Takumi, to a hint at the Devil Z Challenge once he is beaten.
- **The Wangan drivers** keep their personalities (the tuner, the GT-R driver, the doctor in the black 964, the RGO crew) and react to the player's record: first loss, losing again, finally winning.
- **Stock characters** keep their translations; only the repeated lines were replaced.

## Validation
- `tools/talk/talkgrammar45.py` walks every generated table against the stock command grammar: tokens, token pairs, page ends, lines per page, line length, speaker and window order, and pose range. It reported 0 failures.
- Samples of every character were then loaded through the game's own talk runner in emulation, and checked in PPSSPP.

The scripts themselves are not reproduced here, because the stock lines are translations of the original game's text.
