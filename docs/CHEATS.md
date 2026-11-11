# Cheats

[`cheats/ULJM05093.ini`](cheats/ULJM05093.ini) is a PPSSPP cheat file. It only works on Initial Z builds; the addresses are for the remix executable, not the stock game.

**Install:** copy it to `PSP/Cheats/ULJM05093.ini` in your PPSSPP memory stick folder, then in game open **Game settings → Cheats**. If you already have a file with that name, merge the entries into it.

**Back up your save first.** Several codes write progress into the save.

**Encoding:** CWCheat addresses are the runtime address − 0x08800000. For example, the executable's vaddr V is written as `V + 0x4000`.

| Code | What it does |
|---|---|
| Tune Up cards ×99 | One of the two community codes that exist for this game, moved to the remix layout. The other ("infinite time") was dropped because it would overwrite remix memory. |
| All cards ×99 / Stock cards / Aura cards / Tuning cards ×99 | Owns every card. Keep these off if you want to earn real NEW cards: with every card at 99, the card screen can only show ×99 repeats. |
| Unlock all extras | Project D Web movies and course guides, music, comms cars and passes. |
| Unlock Challenge Bunta + Subaru | The stock Bunta mode and the Subaru in New Car. |
| Takumi on Akina beaten | Opens the Wangan and Hakone lineups and the Wangan Rivals page. |
| Bunta beaten | Opens Akio in Street Legends. |
| Game cleared | Sets the clear count (one New Game+ star) and the extra rivals. |
| Devil Z buyable | Puts the Devil Z in New Car → Nissan. |
| All Street Legends rivals beaten | Stock rivals, the Wangan lineup and Akio on every course. |
| Page-2 Wangan rivals + Hakone lineup beaten | Marks all the Wangan Rivals pages and Hakone as beaten. |
| Unlock Devil Z Challenge | Records an Akio win on Akina, which is saved. |
| Devil Z Challenge FORCE | Opens the mode while the code is on, without touching the save. |
| All aura colours at HUGE | All 18 aura steps on every garage car. |
| Aura km/h per step = 0/1/2/3/5 | The top-speed bonus per aura step. The default is 2; 0 makes auras purely cosmetic. |
| Legend auras OFF | No glow on the legends (Akio keeps his). |
| Give Rainbow Aura card / Rainbow Aura ×99 | The top-tier aura card. To use it, buy all 18 AURA TUNE steps on the car and select White; the AURA TUNE header then shows RAINBOW and the car races with Akio's rainbow. |
| Aura drops: guaranteed count / % per slot | Tune how many aura cards a win over an aura driver gives. |
| Rainbow Aura reward off | Turns off the card normally earned by clearing every Devil Z Challenge course. |
| Easier Akio: Wangan / Hakone | Slows Street Legends Akio further on the two new courses. Wangan: about 1'32"7 instead of 1'29"5. Hakone: about 2'20" up and 2'17" down instead of 2'13" and 2'10". |
| Harder Akio | Brings back the v1.0 Street Legends Akio: he matches your speed plus 2 km/h, with the faster v1.0 pace on Wangan and Hakone. |

## Caution: aura km/h per step = 5

This code lets a fully tuned car (18 aura steps) gain up to **+90 km/h** of top speed, instead of +36 km/h at the default setting. The courses, collision, AI and cameras were only tested up to about +36 km/h. At these speeds you can expect:

- cars launching over crests, clipping through walls or falling out of the course,
- corners you can't physically make, and rivals that can't keep up at all,
- Time Attack records that are far beyond normal play. **Those records are saved.**

Back up your save first, and turn the code off before racing for real records.
