# simiq

> Virtuálne skúšanie športového oblečenia v polohe, v ktorej sa šport robí. Začíname cyklistickými dresmi a bibkami.

**Fáza:** príprava na demo day akcelerátora · **Demo day: piatok 20. 11. 2026** · **Pilotná značka: Isadore** · README aktualizované 14. 10. 2026

## Čo robíme

simiq je B2B služba pre značky športového oblečenia:

- **Značka** nám dodá rozmery produktu a informácie o látke. My produkt zdigitalizujeme.
- **Zákazník e-shopu** prejde onboardingom navrhnutým vo Figme: pohlavie, hmotnosť, výška a typ postavy; typy rúk, torza, nôh a presné miery sú voliteľné. V katalógu si vyberie dres alebo bibky, dostane odporúčanú veľkosť a 3D postavu, aj na bicykli, na ktorej vidí, kde mu oblečenie bude tesné alebo voľné.
- **Cieľ:** správna veľkosť na prvý pokus, vyššia konverzia a menej vratiek.

Prečo a ako sme sa rozhodli, je v [simiq-prehlad.md](simiq-prehlad.md) (výskum, konkurencia, architektúra, biznis model, GDPR).

## Kde čo nájdeš

| Čo | Kde |
|---|---|
| Tento prehľad, roadmapa, rozhodnutia | `README.md` |
| Pracovná dohoda: workflow, pravidlá, obmedzenia (EN) | [CLAUDE.md](CLAUDE.md) |
| Výskum a zdôvodnenie (SK) | [simiq-prehlad.md](simiq-prehlad.md), audio zhrnutie [simiq-prehlad-audio.m4a](simiq-prehlad-audio.m4a) |
| Špecifikácie a úlohy (EN) | [`openspec/changes/`](openspec/changes/): každá zmena má `proposal.md`, `design.md`, `specs/`, `tasks.md` |
| Rozhodnutia zakladateľov z plánovania | [`fit-engine-poc/grill.md`](openspec/changes/fit-engine-poc/grill.md) |
| Dizajn: onboarding, štúdio, katalóg | [Figma NIIO, stránka `simik`](https://www.figma.com/design/nmFcu26FyE2mqlIGnJJ9Vh/NIIO?node-id=211-1083); mapa rámcov v `tryon-viewer-mvp/design.md` D4b |
| Úlohy (issues), 1:1 s `tasks.md` | [GitHub issues](https://github.com/itsniio/simiq/issues) so štítkami `part:1` až `part:3` |
| Triedy rizika ciest a kontroly pre factory | [`.niio.yml`](.niio.yml) |
| Šablóny issues a PR, CI | [`.github/`](.github/) |
| Kód (zatiaľ neexistuje) | `engine/` (Python), `api/` (Python), `web/` (TypeScript), `adapters/` (neskôr) |
| Dáta odevov a látok | `data/` (verejné), `data/private/` (osobné, **nikdy do gitu**) |

Repozitár: [github.com/itsniio/simiq](https://github.com/itsniio/simiq), **verejný**. Pôvodná špecifikácia (zmeny `body-model-spike`, `fit-lab-protocol`, `garment-sim-spike`) zostáva v histórii gitu v commite `5abe63d`. Prototyp z októbra (`body/`, `garment/`) sa nepreberá, staviame od nuly (R12).

## Ako staviame

Pravidlá niio factory z [os.niio.sk](https://github.com/itsniio/os.niio.sk), upravené pre Python a TypeScript. Plné znenie je v [CLAUDE.md](CLAUDE.md), tu je skratka:

```
 issue (sablona, Estimate: Nd, hitl/afk, part:n)
   -> spec-ready (OpenSpec zmena prejde validaciou)
   -> clovek prida implement-ready
   -> vetva -> najprv padajuci test -> implementacia
   -> PR s pevnym telom (What, Why, Evidence, Door, Blast radius,
      Left undone, Decisions made on my own, Disclosure)
   -> clovek PR precita -> merge
```

- **Jeden PR = jedno správanie**, najviac ~400 zmenených riadkov bez testov.
- **Rozumieť je podmienka.** Autor vie vysvetliť každý riadok. Čomu nerozumie, uvedie v Disclosure. PR do `core` ciest (fit engine, dáta, API, loader) sa zlúči len s Disclosure „None“.
- **Každý vzorec** (natiahnutie, napätie, tlak, rezerva dĺžky, penalizácia, istota) má odvodenie v `engine/docs/formulas.md` a test s ručne vypočítanými číslami.
- **Dôkaz** pochádza z CI alebo zo zaznamenaného behu, nikdy z toho, že agent napíše „testy prešli“. Kontrola, ktorá nebežala, je `unverified`, nikdy zelená.
- **Konštanta pred nastavením.** Čísla, ktoré rozhodujú o veľkosti, sa menia len vlastným PR s číslami pred a po.
- **Oprava** sa zadá ako komentár `/rule: ...` v PR a stane sa z nej lint, test alebo pravidlo. Rovnakú pripomienku nikto nedáva dvakrát.
- Žiadne `git add -A` (hook ho zablokuje) a žiadne AI podpisy v commitoch.

## Špecifikácie (OpenSpec zmeny)

| # | Zmena | Čo prináša | Kedy | Úlohy |
|---|---|---|---|---|
| 1 | [`fit-engine-poc`](openspec/changes/fit-engine-poc/) | Telo z onboardingu (Anny), merania v jazdnej polohe, model odevu a látky, výpočet natiahnutia, odporúčanie veľkosti s istotou, kalibrácia na fit štúdii | do demo day | 42 |
| 2 | [`tryon-viewer-mvp`](openspec/changes/tryon-viewer-mvp/) | Rýchle API a štúdio podľa Figmy: onboarding v 3 krokoch, katalóg a detail produktu, 3D s farebnou mapou aj na bicykli, odkaz aj vloženie do e-shopu | do demo day | 37 |
| 3 | [`shop-embed-mvp`](openspec/changes/shop-embed-mvp/) | `loader.js` ≤ 10 KB, tlačidlo, modal, odovzdanie veľkosti e-shopu, návod, demo e-shop, umiestnenie na isadore.com | do demo day | 17 |
| 4 | [`pilot-analytics`](openspec/changes/pilot-analytics/) | Udalosti, kontrolná skupina (A/B), objednávky a vratky z Isadore (CSV), report | pilot s Isadore | 11 |
| 5 | [`platform-adapters`](openspec/changes/platform-adapters/) | Shopify app, Shoptet doplnok, WooCommerce plugin | prvý zákazník na týchto platformách | 22 |
| 6 | [`brand-onboarding`](openspec/changes/brand-onboarding/) | Portál pre značky, príjem podkladov, synchronizácia katalógu, automatické manifesty | druhá značka | 20 |

Postup technických úloh ukáže kedykoľvek `openspec list`. Štítky `part:1` až `part:6` zodpovedajú poradiu v tejto tabuľke.

## Tím a stopy

| Stopa | Náplň | Kto |
|---|---|---|
| **F** Fit engine (Python) | Anny, merania, fit engine, kalibrácia, API | _doplniť_ |
| **W** Web a 3D (TypeScript) | Prehliadač podľa Figmy, widget, demo e-shop, technika landing page | _doplniť_ |
| **B** Biznis | Mentor, Isadore, ďalšie značky, LOI, cenník, pitch | _doplniť_ |
| **S** Štúdia a merania | Nákup kusov, meranie rozmerov a látky, bodková mriežka, fit štúdia | _doplniť_ (pri 3 ľuďoch spolu s B) |

## Roadmapa do demo day

```
            T1        T2         T3         T4         T5         T6
          14.10.    19.10.     26.10.      2.11.      9.11.     16.-20.11.
 F  [repo+Anny]--[telo+merania]--[fit+API]--[kalibracia]--[vysledky]
 W  [Figma+web]--[formular]------[3D]-------[embed]-------[deploy+video]--[freeze 18.11.]
 B  [mentor+Isadore]-[podklady]--[pilot+landing]--[LOI]---[pitch]--------[DEMO DAY 20.11.]
 S  [nakup kusov]-[meranie+mriezka+latka]-[skuska]--[studia 1]--[studia 2]
```

### T1 · st 14. 10. – ne 18. 10. · Rozbeh

- [ ] **Všetci** Prečítať a zlúčiť PR #1; doplniť mená do tabuľky Tím a stopy; dať `implement-ready` prvým issues a doplniť im `Estimate`
- [ ] **B** Poslať odpovede mentorovi (hotový text v [simiq-prehlad.md §11](simiq-prehlad.md#11-akcelerátor-fit-štúdia-a-odpovede-mentorovi))
- [ ] **B** **Isadore:** dohodnúť stretnutie a požiadať o tech packy (tabuľky rozmerov), informácie o látkach (dodávateľ, technické listy), export vratiek s dôvodmi a kontakt na vývojárov e-shopu
- [ ] **B** Spísať 5–10 ďalších značiek pre rozhovory (záloha a ďalší zákazníci)
- [ ] **S** Kúpiť Isadore dres a bibky v 3–4 veľkostiach a jeden dres navyše (na bodkovú mriežku a potom na rozstrihanie pre testy látky)
- [ ] **F** `fit-engine-poc` 1.2–1.3 (engine, CI, pre-commit) a začať 2 (test Anny)
- [ ] **W** `fit-engine-poc` 3.1 (s dizajnom ujasniť, ako sa meria každá miera z kroku 3), `tryon-viewer-mvp` 3.1 (web, CI)

### T2 · po 19. 10. – ne 25. 10. · Merania a jadro

- [ ] **F** Rozhodnutie áno/nie o Anny (`fit-engine-poc` 2.3) **do st 21. 10.**
- [ ] **F** `fit-engine-poc` 3.2–3.7 (telo z onboardingu) a 4 (merania v polohe)
- [ ] **S** `fit-engine-poc` 8.5 (voliteľne: bodková mriežka na vlastnom drese), potom 5.3–5.6 (zmerať kusy, krivky látky, tabuľka veľkostí Isadore)
- [ ] **S** Protokol fit štúdie, súhlas účastníka (GDPR), partner: bike-fitting štúdio alebo klub
- [ ] **B** Stretnutie s Isadore; aspoň 3 rozhovory s ďalšími značkami (otázky nižšie)
- [ ] **W** `tryon-viewer-mvp` 3.2–3.5 a 4 (jazyky, rozpočty, tokeny, štúdio a onboarding presne podľa Figmy, súhlas)

### T3 · po 26. 10. – ne 1. 11. · Prvá predpoveď

- [ ] **F** `fit-engine-poc` 5.1–5.2, 6, 7: výpočet, odporúčanie, CLI, prvé predpovede na členoch tímu (7.4)
- [ ] **F** `tryon-viewer-mvp` 1 (surogát, sieť 3D postáv) a 2.1–2.3 (API)
- [ ] **W** `tryon-viewer-mvp` 5 (katalóg, detail, odporúčanie, 3D s bicyklom, farebné zóny) proti vzorovým dátam
- [ ] **S** Skúšobné meranie podľa protokolu na 3–5 ľuďoch
- [ ] **B** Návrh pilotu pre Isadore: čo dodajú, čo meriame, ako dlho, kontrolná skupina
- [ ] **B + W** Landing page s tlačidlom „chcem demo“ je online

### T4 · po 2. 11. – ne 8. 11. · Štúdia a embed

- [ ] **S** Fit štúdia, kolo 1 (aspoň 10 jazdcov)
- [ ] **F** `fit-engine-poc` 8.1–8.4, 8.6 (kalibrácia a vyhodnotenie kola 1); `tryon-viewer-mvp` 2.4–2.7 (API na staging)
- [ ] **W** `tryon-viewer-mvp` 6 (samostatný odkaz a vloženie) a `shop-embed-mvp` 1–4
- [ ] **B** LOI s Isadore; cenové hypotézy

### T5 · po 9. 11. – ne 15. 11. · Výsledky a video

- [ ] **S** Fit štúdia, kolo 2 (spolu 20–30 jazdcov)
- [ ] **F** Finálne vyhodnotenie (`fit-engine-poc` 8.6): číslo do pitchu
- [ ] **W** `shop-embed-mvp` 5–6 (vrátane 6.4 umiestnenie na isadore.com, ak je LOI), `tryon-viewer-mvp` 7.1–7.2 (nasadenie, offline demo, demo video)
- [ ] **B** Pitch deck, podpísané LOI (cieľ)

### T6 · po 16. 11. – pi 20. 11. · Demo day

- [ ] po 16. 11. Generálka 1
- [ ] **st 18. 11. Zmrazenie produkcie** (už žiadne nasadenia)
- [ ] `tryon-viewer-mvp` 7.3 a `shop-embed-mvp` 6.3: kontrola celého toku na telefónoch, scenár dema
- [ ] št 19. 11. Generálka 2 na produkcii, pripravená záloha (offline demo, video)
- [ ] **pi 20. 11. Demo day**

### Hotové na demo day znamená

- [ ] Živé demo: demo e-shop → tlačidlo → onboarding podľa Figmy → veľkosť + 3D v jazdnej polohe, na Isadore dresoch
- [ ] Zdieľateľný odkaz (bez e-shopu)
- [ ] Výsledky fit štúdie (N ≥ 20): presnosť oproti tabuľke veľkostí Isadore, s intervalmi spoľahlivosti
- [ ] LOI alebo dohoda o pilote s Isadore vrátane dát (tech packy, látky, export vratiek)
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

## Po demo day

1. `pilot-analytics` + umiestnenie snippetu na isadore.com s ich vývojármi → pilot s kontrolnou skupinou a dohodnutou dĺžkou
2. `platform-adapters` až s prvým zákazníkom na Shopify, Shoptete alebo WooCommerce (Isadore má vlastný e-shop na Nette)
3. `brand-onboarding` pri druhej značke; stack portálu sa rozhodne pred začiatkom (Rails je kandidát)

## Validácia: vlastný nápad

Podľa pravidiel factory (os.niio.sk R7) má vlastný nápad od začiatku kill criterion a dátum revízie.

> **Potvrdené zakladateľmi 14. 10. 2026** („asi okej“, `grill.md` #11):
> - **Revízie:** pi 4. 12. 2026 (dva týždne po demo day) a pi 29. 1. 2027.
> - **Ukončiť alebo zásadne zmeniť smer**, ak k 29. 1. 2027 platí aspoň jedno:
>   1. fit štúdia (N ≥ 20) neukáže, že trafíme veľkosť častejšie ako tabuľka veľkostí Isadore;
>   2. Isadore ani iná značka nepodpísala pilot s dátami (tech packy a export vratiek).

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
          v                                        | onboarding -> velkost -> 3D |
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
| R3 | Stack: Python (FastAPI) + TypeScript | Anny beží na PyTorch, web v TS. Odchýlka od niio štandardu Rails (os R1), zdôvodnená tu a v `grill.md` #1 | |
| R4 | Online časť = statické súbory na CDN + malé API bez ťažkých výpočtov | Rýchlosť a spoľahlivosť pre veľké e-shopy | `tryon-viewer-mvp/design.md` D1–D3 |
| R5 | Embed: malé tlačidlo + iframe modal až po kliku | Nerozbije e-shop, žiadny vplyv na výkon | `shop-embed-mvp/design.md` D1 |
| R6 | Digitalizácia je služba, nie samoobsluha | DXF nemá šité spoje, látku treba zmerať | `brand-onboarding` |
| R7 | Profil tela len na zariadení zákazníka; API nič neukladá ani neloguje | GDPR (miery môžu byť zdravotné údaje) | `fit-api` spec |
| R8 | Styling, fotka a sken postavy sú mimo rozsah | Komodita alebo trenie; nerieši sedenie | `simiq-prehlad.md` §4 |
| R9 | README po slovensky, špecifikácie a kód po anglicky | Tím a mentori vs. vývoj a AI nástroje | `grill.md` #3 |
| R10 | **Pilotná značka Isadore** (D2C e-shop) | Rozhodnutie zakladateľa 14. 10.; e-shop beží na Nette, takže pilot ide cez snippet, nie platformový adaptér | `grill.md` #5 |
| R11 | **Figma je zmluva pre UI**: onboarding v 3 krokoch (pohlavie, hmotnosť, výška, typ postavy; typy rúk, torza, nôh; miery), štúdio s katalógom a bicyklom | Dobre navrhnutý flow; štúdia zmeria, či typy postavy pomáhajú | `grill.md` #6, #12; `body-profile` a `tryon-viewer` spec |
| R12 | **Nový prototyp od nuly**; októbrový `body/`, `garment/` sa nekopíruje | Rozhodnutie zakladateľa 14. 10. | `grill.md` #9 |
| R13 | **Pravidlá niio factory** (CLAUDE.md), „rozumieť je podmienka“ | Žiadny vibecoding: všetko kontrolujeme a rozumieme tomu | `grill.md` #10 |

## Otvorené otázky

| Otázka | Kto | Do kedy |
|---|---|---|
| Pohlavie „Iné“: stavať mužské telo, ako píše poznámka vo Figme, alebo inak? | zakladatelia | ne 18. 10. |
| Ako sa meria každá miera z kroku 3 (texty „i“: ramená, dĺžka rúk…) a ich rozsahy | W + dizajn | T2 (`fit-engine-poc` 3.1) |
| Pridať do kroku 3 boky? Bibky ich potrebujú, dnes sa odhadujú | dizajn | T2 |
| Rámce pre mobil a pre vloženie do e-shopu (dovtedy dočasné riešenie v `tryon-viewer-mvp/design.md` D4b) | dizajn | T3 |
| Anny áno/nie (deformácia bokov v predklone) | F | st 21. 10. |
| Uhly póz `hoods` a `drops` | F | T2 |
| Partner pre fit štúdiu; dá sa nájsť 20–30 jazdcov v novembri (trenažéry, klub)? | S | T2 |
| Kde hostovať API | F + W | T3 |
| Čo z biznisu smie byť vo verejnom repozitári (ceny, výsledky rozhovorov) | zakladatelia | T1 |

## Ako pracovať so špecifikáciami

| Chcem | Príkaz |
|---|---|
| Vidieť postup všetkých zmien | `openspec list` |
| Prečítať zmenu | `openspec show <zmena>` alebo súbory v `openspec/changes/<zmena>/` |
| Založiť úlohu | GitHub issue zo šablóny (Feature, Bug, Research, Idea), so štítkom `part:n` |
| Implementovať úlohy zmeny (Claude Code) | `/opsx:apply <zmena>`, až keď má issue `implement-ready` |
| Upraviť plán zmeny | `/opsx:update <zmena>` |
| Premyslieť nový nápad, potom ho naplánovať | `/opsx:explore` → `/opsx:propose` |
| Uzavrieť hotovú zmenu (špecifikácie prejdú do `openspec/specs/`) | `/opsx:archive <zmena>` |

Technické úlohy odškrtávame v `tasks.md` príslušnej zmeny v tom istom PR. Biznisové úlohy a fit štúdiu odškrtávame tu v README.
