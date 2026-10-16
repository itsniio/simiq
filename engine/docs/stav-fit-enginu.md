# Stav fit enginu (vetva `rp-anny`, 16. 10. 2026)

Prehľad pre tím: ako engine dnes počíta fit, čo je hotové, čo chýba a kam to smeruje. Vzorce s odvodením a ručne spočítanými číslami sú v [formulas.md](formulas.md), definície mier s obrázkami v [measurements.md](measurements.md), plán v [design.md](../../openspec/changes/fit-engine-poc/design.md) (D6, D8), úlohy v [tasks.md](../../openspec/changes/fit-engine-poc/tasks.md).

Nič z toho ešte nie je v `master`: vetva nemá PR, CI na nej nebežalo a nikto ju nečítal. Overené lokálne 16. 10. 2026 na macOS (`uv sync --locked`, `uv run pytest`): 146 passed, `ruff check` čistý; v CI zatiaľ nie.

## Dve rôzne veci: engine a CLO

- **Fit engine** (`engine/`) počíta odporúčanie veľkosti. Látku nesimuluje (rozhodnutie R1): porovnáva obvody a dĺžky tela s rozmermi dresu po zónach. Beží za zlomok milisekundy.
- **CLO** (videá v [`jersey-demo/`](../../jersey-demo/README.md)) je plná fyzikálna simulácia látky na tele z Anny. Dáva mapu natiahnutia po celej ploche dresu, ale odporúčanie z nej nepočítame. Slúži na vizuál do dema a na kontrolu enginu: na tom istom tele sa v hlavných zónach zhodujú, na rukáve nie.

## Ako engine počíta dnes

1. **Telo.** Z pohlavia, výšky a hmotnosti (voliteľne vek a miery z kroku 3) sa postaví telo z Anny: výška na 0,5 cm, hmotnosť na 2 % (hmotnosť = objem × 1,03 kg/l). Podporované BMI: ženy 14–40, muži 16–40. Telo sa dá do polohy `standing`, `hoods` alebo `drops`.
2. **Merania v polohe**, ako krajčírsky meter: obvod hrude, pásu a bokov (boky na krúžku bodov na koži, aby sedeli aj v predklone), profily ramena a stehna po 2 cm, dĺžka chrbta (C7 → boky) a zvislý obvod trupu. Každá miera má neistotu podľa toho, čo zákazník zadal (zdroj: ANSUR II a štúdia o meraní pásu doma).
3. **Dres** je tabuľka rozmerov každej veľkosti a zóny. Dres má päť zón:

   | Zóna | Rozmer dresu | Miera tela | Váha |
   |---|---|---|---|
   | hruď | obvod hrudníka | obvod hrude | 2 |
   | pás | obvod pásu | obvod pásu | 1 |
   | lem | spodný obvod | boky | 1 |
   | rukáv | otvor rukáva | rameno 12 cm pod podpazuším | 1 |
   | dĺžka chrbta | dĺžka chrbta | dĺžka chrbta | 1 |

4. **Každá zóna:**
   - natiahnutie ε = obvod tela / obvod dresu − 1 (hruď 96 cm v drese 84 cm → +14,3 %); záporné = voľnosť v cm;
   - napätie z krivky látky (sila pri danom natiahnutí z pásikového testu) a tlak z Laplaceovho zákona P = T / r, r = obvod / 2π. Tlak sa ukazuje len relatívne medzi veľkosťami („M tlačí viac ako L“), nikdy v kPa;
   - dĺžka: rezerva = dĺžka dresu × (1 + natiahnutie pri komfortnom napätí) − dĺžka tela.
5. **Pásma.** Podľa hraníc zóny dostane zóna stav `too_loose`, `loose`, `ok`, `tight`, `too_tight` (pri dĺžke `too_short`, `short`, `ok`, `long`).
6. **Odporúčanie.** Penalizácia = Σ váha × cena stavu (ok 0; loose, tight, short, long 1; too_* 3). Vyhrá najnižšia, pri zhode veľkosť bližšie k stredu ok pásiem. Istota = podiel zo 64 mierne pozmenených tiel (podľa neistoty mier), pri ktorých vyjde tá istá veľkosť; pod 0,6 sa ponúkne aj druhá veľkosť. Vysvetlenie vymenuje zóny, ktoré sa líšia od susednej veľkosti („L má voľný hrudník“).

## Čo je hotové a čo chýba

| Časť | Stav |
|---|---|
| Telo z výšky a hmotnosti, polohy, determinizmus (3.2, 3.4, 3.6, 3.7) | hotové, otestované |
| Merania a ich neistota (4.1–4.6) | hotové, porovnané s ANSUR II (rozdiel 1–6 cm) |
| Formáty dresu a látky, šablóny zón (5.1, 5.2) | hotové; v `data/examples/` sú len vymyslené ukážky |
| Natiahnutie, napätie, tlak, rýchlosť (6.1, 6.2, 6.5) | hotové |
| Penalizácia, istota, vysvetlenie (7.1, 7.2) | hotové |
| Rezerva dĺžky a načítanie hraníc (6.3, 6.4) | kód hotový, **čísla chýbajú**: komfortné napätie ani hranice pásiem (`data/fit-ranges/`) ešte neexistujú; ukážkové hranice sú len v `jersey-demo/demo/data/ranges.json` |
| Príkaz `simiq-fit recommend` (7.3) | chýba, čaká na 6.3 a 6.4 (`measure` a `export-mesh` fungujú) |
| Tabuľka veľkostí Isadore (5.6) | zapísaná v `data/size-charts/isadore-men.json`, chýbajú záznamy samotných dresov |
| Návod na meranie dresov (5.3) | napísaný, overia ho dvaja z tímu |
| Typy postavy a miery z kroku 3 ako ciele (3.3, 3.5) | čaká na dizajnéra (3.1: ako sa ktorá miera meria) |
| Spike Anny (2.3) | odporúčanie v [anny-spike.md](anny-spike.md), čaká na podpis tímu (termín 21. 10.) |
| Štúdia a kalibrácia (8.x), test celej cesty (9.1) | nezačaté |

## Ako to chceme počítať (plán)

Výpočet zostáva rovnaký, čísla majú prísť z reality:

1. Zmerať dresy a bibky Isadore vo všetkých veľkostiach (5.4) a pásikovým testom krivky látky (5.5).
2. Skúšanie dresov na tíme: z neho komfortné napätie a prvé hranice pásiem (6.3, 6.4), potom porovnanie predpovedí s tým, ako to sedelo (7.4).
3. Fit štúdia (N ≥ 20): kalibrácia hraníc (8.3) a správa, či trafíme veľkosť častejšie ako tabuľka Isadore (8.4). To je zároveň kill criterion z README.
4. Bibky: rozkrok a zadok sa merajú na stojacom tele a zmena v polohe sa doplní z merania metrom na ľuďoch (Anny tam v predklone skresľuje).

Známe zjednodušenia: zóna je jeden obvod, nie mapa po ploche; neistota mier sa zo stoja do polohy prenáša jedna k jednej (kým nebude 3.5); látka má jednu krivku na smer.

Otvorená otázka: fyzikálna simulácia s reálnou látkou namiesto porovnania obvodov. Mení rozhodnutie R1, preto patrí do grill session. Dovtedy CLO slúži na overovanie enginu na rovnakých telách a dresoch.
