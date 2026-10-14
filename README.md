# simiq

> Virtuálne skúšanie športového oblečenia v polohe, v ktorej sa šport robí. Začíname cyklistickými dresmi a bibkami.

**Fáza:** príprava na demo day akcelerátora · **Demo day: piatok 20. 11. 2026** · README aktualizované 14. 10. 2026

## Čo robíme

simiq je B2B služba pre značky športového oblečenia:

- **Značka** nám dodá rozmery produktu a informácie o látke. My produkt zdigitalizujeme.
- **Zákazník e-shopu** zadá výšku, váhu, vek a pohlavie (obvody voliteľne). Dostane odporúčanú veľkosť a 3D postavu v jazdnej polohe, na ktorej vidí, kde mu dres bude tesný alebo voľný.
- **Cieľ:** správna veľkosť na prvý pokus, vyššia konverzia a menej vratiek.

Prečo a ako sme sa rozhodli, je v [simiq-prehlad.md](simiq-prehlad.md) (výskum, konkurencia, architektúra, biznis model, GDPR).

## Kde čo nájdeš

| Čo | Kde |
|---|---|
| Tento prehľad, roadmapa, rozhodnutia | `README.md` |
| Výskum a zdôvodnenie (SK) | [simiq-prehlad.md](simiq-prehlad.md), audio zhrnutie [simiq-prehlad-audio.m4a](simiq-prehlad-audio.m4a) |
| Špecifikácie a úlohy (EN) | [`openspec/changes/`](openspec/changes/): každá zmena má `proposal.md`, `design.md`, `specs/`, `tasks.md` |
| Kód (zatiaľ neexistuje) | `engine/` (Python), `api/` (Python), `web/` (TypeScript), `adapters/` (neskôr) |
| Dáta odevov a látok | `data/` (verejné), `data/private/` (osobné, **nikdy do gitu**) |

Repozitár: [github.com/itsniio/simiq](https://github.com/itsniio/simiq). Pôvodná špecifikácia (zmeny `body-model-spike`, `fit-lab-protocol`, `garment-sim-spike`) zostáva v histórii gitu v commite `5abe63d`.

## Špecifikácie (OpenSpec zmeny)

| # | Zmena | Čo prináša | Fáza | Úlohy |
|---|---|---|---|---|
| 1 | [`fit-engine-poc`](openspec/changes/fit-engine-poc/) | Telo z mier (Anny), merania v jazdnej polohe, model odevu a látky, výpočet natiahnutia, odporúčanie veľkosti s istotou, kalibrácia na fit štúdii | do demo day | 39 |
| 2 | [`tryon-viewer-mvp`](openspec/changes/tryon-viewer-mvp/) | Rýchle API (surogátny model), 3D prehliadač s farebnou mapou, odkaz pre kluby aj vloženie do e-shopu | do demo day | 29 |
| 3 | [`shop-embed-mvp`](openspec/changes/shop-embed-mvp/) | `loader.js` ≤ 10 KB, tlačidlo, modal, odovzdanie veľkosti e-shopu, návod na integráciu, demo e-shop | do demo day | 16 |
| 4 | [`platform-adapters`](openspec/changes/platform-adapters/) | Shopify app, Shoptet doplnok, WooCommerce plugin (najprv len platforma pilotnej značky) | pilot | 22 |
| 5 | [`pilot-analytics`](openspec/changes/pilot-analytics/) | Udalosti, kontrolná skupina (A/B), objednávky a vratky, report pre značku | pilot | 10 |
| 6 | [`brand-onboarding`](openspec/changes/brand-onboarding/) | Portál pre značky, príjem podkladov, synchronizácia katalógu, automatické manifesty | po pilote | 20 |

Postup technických úloh ukáže kedykoľvek príkaz `openspec list`.

## Tím a stopy

| Stopa | Náplň | Kto |
|---|---|---|
| **F** Fit engine (Python) | Anny, merania, fit engine, kalibrácia, API | _doplniť_ |
| **W** Web a 3D (TypeScript) | Prehliadač, widget, demo e-shop, technika landing page | _doplniť_ |
| **B** Biznis | Mentor, značky, rozhovory, LOI, cenník, pitch | _doplniť_ |
| **S** Štúdia a merania | Nákup kusov, meranie rozmerov a látky, fit štúdia | _doplniť_ (pri 3 ľuďoch spolu s B) |

## Roadmapa do demo day

```
            T1        T2         T3         T4         T5         T6
          14.10.    19.10.     26.10.      2.11.      9.11.     16.-20.11.
 F  [repo+Anny]--[telo+merania]--[fit+API]--[kalibracia]--[vysledky]
 W  [web zaklad]-[formular]------[3D]-------[embed]-------[deploy+video]--[freeze 18.11.]
 B  [mentor+znacky]-[rozhovory]--[A/B + landing]--[LOI]---[pitch]--------[DEMO DAY 20.11.]
 S  [nakup kusov]-[meranie kusov+latky]-[skuska]--[studia 1]--[studia 2]
```

### T1 · st 14. 10. – ne 18. 10. · Rozbeh

- [ ] **B** Poslať odpovede mentorovi (hotový text v [simiq-prehlad.md §11](simiq-prehlad.md#11-akcelerátor-fit-štúdia-a-odpovede-mentorovi))
- [ ] **B** Spísať 5–10 značiek oboch typov (D2C e-shop aj výrobcovia tímových dresov) a ku komu máme kontakt; dohodnúť prvé rozhovory
- [ ] **S** Kúpiť alebo požičať 1 dres a 1 bibky v 3–4 veľkostiach, plus 1 kus navyše alebo vzorku látky na rozstrihanie (testy natiahnutia)
- [ ] **F** `fit-engine-poc` 1 (repo, git, pre-commit) a začať 2 (test Anny)
- [ ] **W** `tryon-viewer-mvp` 3.1 (web workspace), náčrt landing page
- [ ] **Všetci** Doplniť mená do tabuľky Tím a stopy

### T2 · po 19. 10. – ne 25. 10. · Merania a jadro

- [ ] **F** Rozhodnutie áno/nie o Anny (`fit-engine-poc` 2.3) **do st 21. 10.**
- [ ] **F** `fit-engine-poc` 3 (telo z mier) a 4 (merania v polohe)
- [ ] **S** `fit-engine-poc` 5.3–5.6: návod na meranie, zmerať všetky veľkosti, krivky látky, tabuľka veľkostí značky
- [ ] **S** Protokol fit štúdie, súhlas účastníka (GDPR), partner: bike-fitting štúdio alebo klub
- [ ] **B** Aspoň 5 rozhovorov so značkami (otázky nižšie)
- [ ] **W** `tryon-viewer-mvp` 3.2–3.3 a 4 (jazyky, rozpočet veľkosti, formulár, súhlas) proti vzorovým dátam

### T3 · po 26. 10. – ne 1. 11. · Prvá predpoveď

- [ ] **F** `fit-engine-poc` 5.1–5.2, 6, 7: výpočet, odporúčanie, CLI, prvé predpovede na členoch tímu (7.4)
- [ ] **F** `tryon-viewer-mvp` 1 (surogát, sieť 3D postáv) a 2.1–2.3 (API)
- [ ] **W** `tryon-viewer-mvp` 5 (výsledok, 3D, farebné zóny) proti vzorovým dátam
- [ ] **S** Skúšobné meranie podľa protokolu na 3–5 ľuďoch
- [ ] **B** **Rozhodnutie o prvej značke: D2C e-shop (A) alebo tímové dresy (B), do ne 1. 11.**
- [ ] **B + W** Landing page s tlačidlom „chcem demo" je online

### T4 · po 2. 11. – ne 8. 11. · Štúdia a embed

- [ ] **S** Fit štúdia, kolo 1 (aspoň 10 jazdcov)
- [ ] **F** `fit-engine-poc` 8 (kalibrácia a vyhodnotenie kola 1); `tryon-viewer-mvp` 2.4–2.7 (API na staging)
- [ ] **W** `tryon-viewer-mvp` 6 (samostatný odkaz a vloženie) a `shop-embed-mvp` 1–4
- [ ] **B** Rozhovory o LOI s 2–3 najzaujímavejšími značkami; cenové hypotézy

### T5 · po 9. 11. – ne 15. 11. · Výsledky a video

- [ ] **S** Fit štúdia, kolo 2 (spolu 20–30 jazdcov)
- [ ] **F** Finálne vyhodnotenie (`fit-engine-poc` 8.5): číslo do pitchu
- [ ] **W** `shop-embed-mvp` 5–6, `tryon-viewer-mvp` 7.1–7.2 (nasadenie, offline demo, demo video)
- [ ] **B** Pitch deck, podpísané LOI (cieľ)

### T6 · po 16. 11. – pi 20. 11. · Demo day

- [ ] po 16. 11. Generálka 1
- [ ] **st 18. 11. Zmrazenie produkcie** (už žiadne nasadenia)
- [ ] `tryon-viewer-mvp` 7.3 a `shop-embed-mvp` 6.3: kontrola celého toku na telefónoch, scenár dema
- [ ] št 19. 11. Generálka 2 na produkcii, pripravená záloha (offline demo, video)
- [ ] **pi 20. 11. Demo day**

### Hotové na demo day znamená

- [ ] Živé demo: demo e-shop → tlačidlo → zadanie postavy → veľkosť + 3D v jazdnej polohe
- [ ] Zdieľateľný odkaz pre kluby (bez e-shopu)
- [ ] Výsledky fit štúdie (N ≥ 20): presnosť oproti tabuľke veľkostí, s intervalmi spoľahlivosti
- [ ] Aspoň 1 LOI alebo dohoda o pilote vrátane dát (tech packy, látky, vratky)
- [ ] Demo video (1–2 min) a landing page
- [ ] Pitch deck

<details>
<summary><b>Otázky na rozhovory so značkami</b></summary>

1. Koľko percent online objednávok vám vracajú a koľko z toho kvôli veľkosti? Máte to vôbec merané?
2. Ktoré produkty sa vracajú najviac (dres, bibky, bunda)?
3. Čo k produktom máte: tech pack s tabuľkou rozmerov, DXF strihy, technické listy látok? Má ich u seba značka, alebo továreň?
4. Na akej platforme beží e-shop a kto ho spravuje?
5. Čo ste už skúšali (tabuľka veľkostí, Fit Analytics a pod.) a prečo to fungovalo alebo nefungovalo?
6. Kto by o takom nástroji rozhodol a z akého rozpočtu?
7. Výrobcovia tímových dresov: koľko sád veľkostí ročne posielate klubom, koľko to stojí a koľko objednávok sa prerába kvôli zlej veľkosti?

Cenu netestovať v prvom rozhovore, až keď značka videla demo.
</details>

## Po demo day: pilot

1. `platform-adapters` (len platforma pilotnej značky) + `pilot-analytics` → pilot s kontrolnou skupinou a dohodnutou dĺžkou
2. `brand-onboarding` → keď príde druhá značka

## Architektúra

```
 VOPRED (nasa linka)                               ONLINE (zakaznik e-shopu)
 +------------------+                              +-----------------------------+
 | podklady znacky  | rozmery, latka, DXF          | produktova stranka e-shopu  |
 | / nase merania   |                              |  loader.js (<10 KB, async)  |
 +--------+---------+                              |  [ Ako mi bude sediet? ]    |
          v                                        +--------------+--------------+
 +------------------+                                             | klik
 | engine (Python)  | telo Anny, merania v polohe,                v
 | fit engine       | natiahnutie, odporucanie     +-----------------------------+
 +--------+---------+                              | viewer (iframe / odkaz)     |
          v                                        | formular -> velkost -> 3D   |
 +------------------+   modely, 3D postavy,        +--------------+--------------+
 | precompute       |   balik odevov                              |
 +--------+---------+------------> CDN <--------------------------+ staticke subory
                                                                  v
                                                   +-----------------------------+
                                                   | fit API (FastAPI)           |
                                                   | nic neuklada, < 300 ms      |
                                                   +-----------------------------+
```

## Kľúčové rozhodnutia

| # | Rozhodnutie | Prečo | Detail |
|---|---|---|---|
| R1 | Fit engine počíta natiahnutie látky a kalibruje sa na ľuďoch, nie simuláciou látky | Simulácia tlaku v štúdiách nekorelovala s realitou | `fit-engine-poc/design.md` D6 |
| R2 | Model tela **Anny** (Apache 2.0), nie SMPL | SMPL je len na nekomerčné použitie (potvrdí test v T2) | D2, D3 |
| R3 | Stack: Python (FastAPI) + TypeScript | Anny beží na PyTorch, web v TS | |
| R4 | Online časť = statické súbory na CDN + malé API bez ťažkých výpočtov | Rýchlosť a spoľahlivosť pre veľké e-shopy | `tryon-viewer-mvp/design.md` D1–D3 |
| R5 | Embed: malé tlačidlo + iframe modal až po kliku | Nerozbije e-shop, žiadny vplyv na výkon | `shop-embed-mvp/design.md` D1 |
| R6 | Digitalizácia je služba, nie samoobsluha | DXF nemá šité spoje, látku treba zmerať | `brand-onboarding` |
| R7 | Profil tela len na zariadení zákazníka; API nič neukladá ani neloguje | GDPR (miery môžu byť zdravotné údaje) | `fit-api` spec |
| R8 | Styling, fotka a sken postavy sú mimo rozsah | Komodita alebo trenie; nerieši sedenie | `simiq-prehlad.md` §4 |
| R9 | README po slovensky, špecifikácie po anglicky | Tím a mentori vs. vývoj a AI nástroje | |

## Otvorené otázky

| Otázka | Kto | Do kedy |
|---|---|---|
| Prvá značka: D2C e-shop (A) alebo tímové dresy (B)? | B | ne 1. 11. |
| Ktorý strih (pánsky/dámsky) a ktoré konkrétne kusy kúpiť? | S | pi 16. 10. |
| Anny áno/nie (deformácia bokov v predklone) | F | st 21. 10. |
| Uhly póz `hoods` a `drops` | F | T2 |
| Partner pre fit štúdiu | S | T2 |
| Kde hostovať API | F + W | T3 |

## Ako pracovať so špecifikáciami

| Chcem | Príkaz |
|---|---|
| Vidieť postup všetkých zmien | `openspec list` |
| Prečítať zmenu | `openspec show <zmena>` alebo súbory v `openspec/changes/<zmena>/` |
| Implementovať úlohy zmeny (Claude Code) | `/opsx:apply <zmena>` |
| Upraviť plán zmeny | `/opsx:update <zmena>` |
| Premyslieť nový nápad, potom ho naplánovať | `/opsx:explore` → `/opsx:propose` |
| Uzavrieť hotovú zmenu (špecifikácie prejdú do `openspec/specs/`) | `/opsx:archive <zmena>` |

Technické úlohy odškrtávame v `tasks.md` príslušnej zmeny. Biznisové úlohy a fit štúdiu odškrtávame tu v README.
