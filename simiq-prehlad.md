# simiq: technický a biznisový prehľad

> Výstup z explore session, 14. 10. 2026. Pracovný dokument na diskusiu v tíme, nie finálna špecifikácia.
> Fakty pochádzajú z webovej rešerše k uvedenému dátumu. Zdroje sú na konci, neoverené veci sú označené.

## Obsah

1. [Zhrnutie na jednu minútu](#1-zhrnutie-na-jednu-minútu)
2. [Fit engine namiesto fyzikálneho enginu](#2-fit-engine-namiesto-fyzikálneho-enginu)
3. [Model tela, vstupy od zákazníka, materiál](#3-model-tela-vstupy-od-zákazníka-materiál)
4. [Produkt: čo áno a čo nie](#4-produkt-čo-áno-a-čo-nie)
5. [Konkurencia a poučenia](#5-konkurencia-a-poučenia)
6. [Architektúra](#6-architektúra)
7. [Integrácia do e-shopov](#7-integrácia-do-e-shopov)
8. [Onboarding značky a marketing](#8-onboarding-značky-a-marketing)
9. [Biznis model a validácia](#9-biznis-model-a-validácia)
10. [GDPR a právo](#10-gdpr-a-právo)
11. [Akcelerátor: fit štúdia a odpovede mentorovi](#11-akcelerátor-fit-štúdia-a-odpovede-mentorovi)
12. [Štruktúra špecifikácie (OpenSpec)](#12-štruktúra-špecifikácie-openspec)
13. [Riziká a otvorené otázky](#13-riziká-a-otvorené-otázky)
14. [Zdroje](#14-zdroje)

---

## 1. Zhrnutie na jednu minútu

| Plán dnes | Návrh | Prečo |
|---|---|---|
| Problém č. 1 je 3D fyzikálny engine | Problém č. 1 je dokázať, že predpoveď sedí | Štúdie ukazujú, že 3D simulácia tlaku nekoreluje s realitou ani pri cyklistickom oblečení |
| Dva produkty (digitalizácia + fitting), k tomu styling a vlastný scan | Jeden produkt (fit) + digitalizácia ako onboarding služba. Styling a scan neskôr | Značka platí za menej vratiek a vyššiu konverziu, nie za 3D model. Generatívny styling je komodita |
| Iframe, ktorý robí všetko | Malé jadro na stránke, ťažké veci až po kliku, výpočty vopred na serveri | Rýchlosť, žiadny dopad na e-shop, spoľahlivosť |
| „Znížime vratky" | Zmerať to v pilote cez A/B test | Aj Zalando namerané zníženie vratiek nepotvrdilo, tvrdenia predajcov sú skreslené |

**Vaša medzera na trhu:** sedenie v jazdnej polohe. Castelli, Sportful, Le Col ani Assos ho dnes neriešia, majú len statické tabuľky veľkostí.

**Najbližší krok:** fit štúdia s 20 až 30 jazdcami + prototyp fit enginu na jednom drese a jedných bibkách.

---

## 2. Fit engine namiesto fyzikálneho enginu

### Čo hovorí výskum

- **Cyklistické oblečenie v štyroch jazdných polohách (2024):** tlak, ktorý predpovedala 3D simulácia, nekoreloval s tlakom nameraným na ľuďoch. Autori píšu, že avatary majú hodnotu na porovnanie a vizualizáciu.
- **Kompresné športové oblečenie (Brubacher 2021):** rovnaký výsledok.
- **Plavky v CLO3D (2025):** simulácia nerozlíšila dve rôzne látky (80/20 polyamid/elastan a 80/20 polyester/elastan).
- **Opak:** jednoduchý výpočet podľa Laplaceovho zákona s nameranou krivkou natiahnutia látky mal na testovacích valcoch chybu prevažne pod 5 %.

### Čo z toho vyplýva

Cyklistický dres a bibky sú priliehavé, takže látka kopíruje telo. Nejde o zložitú simuláciu padania a záhybov, ale o geometriu: **o koľko sa látka natiahne na danom obvode a dĺžke v jazdnej polohe.**

Systém preto rozdeľujeme na dve nezávislé časti:

```
        FIT ENGINE  ("pravda")                 VIZUAL  ("presvedcenie")
 +-------------------------------------+  +-------------------------------------+
 | vstup: telo v jazdnej polohe        |  | vstup: 3D model dresu + telo         |
 |        tabulka rozmerov per velkost |  |                                     |
 |        krivka natiahnutia per zona  |  | vystup: 3D model + farebna mapa     |
 | vystup: natiahnutie per zona        |  |         napatia (tesne/volne)       |
 |         -> velkost + istota         |  |                                     |
 | rychlost: ms, deterministicke       |  | rychlost: vypocitane vopred, z CDN  |
 | testovatelne proti realnym ludom    |  | "vyzera to dobre a dava to zmysel"  |
 +-------------------------------------+  +-------------------------------------+
          |                                          |
          +----------> odporucanie + 3D <------------+
```

| | Fit engine | Vizuál |
|---|---|---|
| Úloha | Rozhodnúť veľkosť | Vysvetliť a presvedčiť |
| Musí byť | Presný, overiteľný | Pekný, zrozumiteľný |
| Kedy beží | V reálnom čase (milisekundy) | Vopred na serveri |
| Technológia | Vlastný výpočet natiahnutia + Laplaceov zákon | NVIDIA Warp/Newton (Apache 2.0) alebo Browzwear VStitcher Server |
| Overenie | Fit štúdia, vratky | Spätná väzba používateľov |

### Čo fit engine počíta v jazdnej polohe

| Zóna | Čo meriame na tele v polohe | S čím porovnávame |
|---|---|---|
| Hrudník, pás | Obvod | Obvod dresu v kľude + natiahnutie látky |
| Chrbát | Dĺžka chrbta v predklone | Dĺžka dresu (vyhrnie sa?) |
| Rukáv | Dĺžka ruky natiahnutej k riadidlám | Dĺžka rukáva |
| Traky bibiek | Dĺžka trupu od ramena po rozkrok | Traky + bibky (ťahajú? padajú?) |
| Stehno | Obvod | Obvod nohavičky a gumy (grippera) |

Výsledok je **vysvetliteľný** („v predklone vám chrbát vyjde o 3 cm"), **rýchly** a **overiteľný na ľuďoch**. Tlak ukazujeme len relatívne (tesnejšie alebo voľnejšie ako iná veľkosť), nikdy ako absolútne číslo.

### Kalibrácia

```
 fit studia (20-50 jazdcov na strih) --> rozsahy natiahnutia per znacka a strih
 vratky (SIZE_TOO_SMALL / TOO_LARGE)  --> priebezna korekcia modelu
```

---

## 3. Model tela, vstupy od zákazníka, materiál

### Model tela: Anny, nie SMPL

| Model | Licencia | Komerčne použiteľný? | Poznámka |
|---|---|---|---|
| **Anny** (NAVER LABS Europe, 2025) | Kód Apache 2.0, dáta CC0 (z MakeHuman) | **Áno** | Nepoužívať jeho voliteľnú SMPL-X topológiu, tá je nekomerčná |
| SMPL / SMPL-X / STAR | Nekomerčná | Len s platenou licenciou | Meshcapade kúpil v roku 2026 Epic a zavrel ho. Licencie dnes cez Max Planck Innovation, posledný známy cenník od 5 000 €/rok (neoverené, či platí) |
| MakeHuman / MPFB2 | Dáta CC0, kód GPL/AGPL | Dáta áno, kód len ako offline nástroj | |

**Pozor:** open-source nástroje HOOD a ContourCraft majú licenciu MIT, ale bez SMPL nefungujú, takže licenciu SMPL zdedíte.

**Anny v skratke:** 13 718 vrcholov, postava sa nastavuje čitateľnými parametrami (pohlavie, vek, výška, váha, svalovina, proporcie), má kostru so 104 kosťami a dá sa napózovať. Nemá opravné tvary pre hlboké polohy, takže **v ostrom predklone sa môže deformovať oblasť bokov a rozkroku**, čo je presne miesto bibiek. Toto je prvý technický test, ktorý treba urobiť.

### Vstupy od zákazníka

| Vstup | Typická chyba | Odporúčanie |
|---|---|---|
| Výška + váha (+ vek, pohlavie) | Hrudník ~2,9 cm, pás ~3,8 cm, boky ~2,2 cm | **Verzia 1.** Približne pol veľkosti neistoty, preto odporúčanie s istotou („M, na hranici s L") |
| + vlastné obvody (hrudník, pás, boky) | Nižšia | **Verzia 1, voliteľne** |
| 2 fotky | 1,5–2 cm (interný údaj predajcu, nie nezávislá štúdia) | Neskôr |
| Sken telefónom (LiDAR, fotogrametria) | 1,0–1,6 cm | Nie: nie je presnejší ako dve fotky a pridáva veľa trenia |

Zadanie musí trvať **do 30 sekúnd**, inak ho zákazníci nedokončia.

### Materiál

- Zo zloženia látky (napr. 80 % polyamid, 20 % elastan) sa natiahnutie odhadnúť nedá. Rozhoduje štruktúra pleteniny, hrúbka elastanu a úprava.
- Pre priliehavé oblečenie stačí **jedna krivka: sila v závislosti od natiahnutia** v oboch smeroch pleteniny, od 0 do 60 %. Ohyb látky je pri priliehavých úpletoch takmer nepodstatný.
- Lacné meranie bez laboratória: závažia alebo silomer podľa normy EN 14704-1 (pás látky) alebo ASTM D4964 (slučka).
- Najprv sa spýtať značky na **technické listy od dodávateľa látky**. Niekedy tieto údaje už obsahujú.

### Čo značky reálne majú

| Podklad | Ako často (odhad, neoverené) | Použiteľnosť |
|---|---|---|
| Tech pack s tabuľkou rozmerov per veľkosť (POM) | Takmer vždy | Stačí na veľkosti a obvody |
| DXF strihy (AAMA/ASTM) | Zvyčajne u výrobcu alebo strihára | Presnejší tvar dielov, ale DXF neobsahuje informáciu o tom, ktoré diely sa zošívajú. Treba doplniť ručne |
| CLO .zprj, Browzwear .bw | Len značky, ktoré už robia v 3D | Najlepší vstup, ale zriedkavý |

**Len tabuľka rozmerov, bez strihov:** nasadíme parametrickú šablónu dresu alebo bibiek. Obvody budú sedieť, čo na veľkosti stačí. Stratíme presný tvar dielov a predtvarovaný jazdný strih, takže 3D model nebude vyzerať presne ako reálny kus.

---

## 4. Produkt: čo áno a čo nie

| Časť | Rozhodnutie | Dôvod |
|---|---|---|
| Fit pre zákazníka e-shopu (veľkosť + 3D s mapou tesných a voľných miest) | **Produkt** | Za toto značka platí |
| Digitalizácia produktu | **Platený onboarding, interná výrobná linka** | Ako samostatný produkt by konkurovala CLO3D a Browzwear |
| Simulácia „ako sa dres ohýba a naťahuje" pre dizajnérov značky | Neskôr, možno | Iný zákazník (vývoj produktu, nie e-commerce) |
| Styling (farba, môj bicykel) | **Vyradiť** | Google Try On je zadarmo vo vyhľadávaní (v kontinentálnej EÚ zatiaľ nie, podľa jedného zdroja), aplikácie stoja ~0,10–0,17 $ za skúšku. Nikto z nich nerieši sedenie |
| Vlastný 3D scan postavy | Neskôr | Nie je presnejší ako fotky, pridáva trenie |

---

## 5. Konkurencia a poučenia

### Kto čo robí

| Hráč | Čo robí | Integrácia / cena |
|---|---|---|
| Fit Analytics (Berlín) | Dotazník + ML odporúčanie veľkosti | Loader ~2 kB, tlačidlo len pri namapovanom produkte. Cena na dopyt |
| True Fit | Odporúčanie veľkosti | Shopify app, 1 000 $/mes. do 150 000 objednávok/rok |
| Kiwi Sizing | Tabuľky + jednoduché odporúčanie | 7,99–26,99 $/mes. |
| Sizekick | Typ postavy alebo video | 115–1 150 $/mes. |
| Kleep (FR) | 2 fotky alebo dotazník | 300+ značiek vrátane Lacoste |
| 3DLOOK YourFit | Sken z 2 fotiek + vizuálne skúšanie | 499 $ za 100 skenov |
| PICTOFiT (Graz) | Avatary, 2D/3D skúšanie, digitalizácia | Riadená služba, 500 $/mes. |
| **Zalando (interne)** | **3D avatar z výšky a váhy + mapa tesných miest pre rifle** | Najbližšie k simiq. Pilot 2023: 30 000 používateľov |

### Cyklistika

- Castelli, Sportful, Le Col (Shopify) a Assos (Magento) majú len statické tabuľky veľkostí (overené 14. 10. 2026).
- Rapha má v konfigurácii stránky príznak `truefit-pdp` vypnutý, môže ísť o test True Fit.
- Ryzon používa dotazník, ktorý volá „virtual fitting room". KOSTÜME ukazuje fotky bibiek na rôznych jazdcoch.
- **Nástroj na sedenie v jazdnej polohe sme nenašli nikde.**
- Výrobcovia custom tímových dresov (Kalas CZ, Santini, Bioracer) posielajú klubom **fyzické sady veľkostí** na vyskúšanie.

### Kto to skúšal pred vami

| Firma | Čo sa stalo |
|---|---|
| Fits.me | Kúpil Rakuten, neskôr zavreté |
| Presize | Ukončil B2B v roku 2022 |
| Zyler | Dnes presmeruje na svadobnú aplikáciu |
| Fytted | Presmeruje na čakaciu listinu iného produktu |
| Metail | Pivot zo skúšania na B2B produktové fotky |
| Snap (vlastnil Fit Analytics) | V roku 2023 zavrel AR enterprise divíziu |

**Opakujúce sa príčiny a vaša odpoveď:**

| Príčina | Odpoveď simiq |
|---|---|
| Drahá digitalizácia každého produktu | Šablóna dresu + tabuľka rozmerov, nie ručné modelovanie |
| Trenie pre zákazníka | Zadanie do 30 sekúnd, fotka voliteľná |
| Látka nevyzerá reálne | Nesúťažiť v realizme, súťažiť v presnosti |
| ROI sa nedá dokázať | A/B test v pilote od prvého dňa |

---

## 6. Architektúra

### Čo znamená „100 % spoľahlivé"

1. **E-shop sa nikdy nerozbije.** Skript sa načíta asynchrónne, s rezervovaným miestom na stránke a s časovým limitom. Keď niečo zlyhá, tlačidlo sa nezobrazí alebo sa ukáže pôvodná tabuľka veľkostí obchodu.
2. **Online časť je „hlúpa".** Statické súbory na CDN a malé API. Žiadny ťažký výpočet nebeží počas požiadavky zákazníka.
3. **Odporúčanie má istotu.** Odpoveď „neviem, ste medzi M a L" je platná.

Cieľová dostupnosť API: 99,9 %. Porovnateľní dodávatelia (Bazaarvoice, Algolia) uvádzajú 99,9 až 99,999 %, fit nástroje svoje SLA nezverejňujú.

### Celkový obraz

```
 VOPRED (nasa linka, raz za produkt)              ONLINE (zakaznik e-shopu)
 +-------------------+                            +-----------------------------+
 | Podklady          | tech pack, tabulka         | produktova stranka e-shopu  |
 | (portal / mail)   | rozmerov, latka, DXF       |  [loader < 10 KB, async]    |
 +---------+---------+                            |  [ "Ako mi bude sediet?" ]  |
           v                                      +--------------+--------------+
 +-------------------+                                           | klik
 | Digitalizacia     | sablona + velkosti                        v
 | + materialy       | + zony latky               +-----------------------------+
 +---------+---------+                            | modal (iframe, nasa domena) |
           v                                      | telo -> velkost -> 3D       |
 +-------------------+  3D modely + mapy napatia  +--------------+--------------+
 | Vypocet vopred    |-------------> CDN <--------------------- | staticke subory
 | velkosti x tela   |                                          v
 | x polohy          |                            +-----------------------------+
 +---------+---------+                            | Fit API (male, rychle)      |
           v                                      | profil -> odporucanie       |
 +-------------------+                            +--------------+--------------+
 | Kontrola kvality  |                                           v
 | + schvalenie      |                            udalosti: zobrazenie, odporucanie,
 |   znackou         |                            kosik, objednavka, vratka
 +-------------------+
```

### Kto čo robí

| Časť | Zodpovednosť | Kde beží |
|---|---|---|
| Podklady | Prijať a skontrolovať tech pack, látku, DXF | Portál pre značky |
| Digitalizácia | Z podkladov vytvoriť model odevu per veľkosť a zóny látky | Naša linka (spočiatku polo-ručne) |
| Výpočet vopred | Pre veľkosti × typy tiel × polohy vypočítať 3D a mapy napätia | Server (GPU), dávkovo |
| Kontrola kvality | Overiť výsledok, značka schváli | Portál |
| Loader + tlačidlo | Zobraziť tlačidlo pri namapovanom produkte, nič nerozbiť | Stránka e-shopu |
| Modal | Zadanie tela, odporúčanie, 3D | Iframe na našej doméne |
| Fit API | Profil tela → veľkosť + istota | Server, rýchle |
| Analytika | Udalosti, objednávky, vratky, A/B | Server |

Výpočet vopred: zhruba 200 až 500 typov tiel × veľkosti × 1 až 2 jazdné polohy. Zákazník dostane najbližší vypočítaný výsledok. Prehliadač len zobrazuje 3D model (glTF) s farebnou mapou, nič nesimuluje.

---

## 7. Integrácia do e-shopov

### Jedno jadro, tenké obaly

```
                +------------------------------------------+
                |  JADRO (jeden kod, jedno nasadenie)       |
                |  loader.js -> <simiq-fit> tlacidlo        |
                |  (oddelene CSS) -> po kliku iframe modal  |
                |  s 3D a profilom                          |
                +------------------------------------------+
                   ^           ^            ^            ^
   tenke obaly:    |           |            |            |
              Shopify app   Shoptet     WooCommerce   HTML snippet
              (theme app    doplnok     plugin        (vlastne shopy,
               extension)                              Magento, ...)
```

### Iframe, web component alebo SDK

| Prístup | Na čo | Plusy | Mínusy |
|---|---|---|---|
| **Web component** (Shadow DOM) | Tlačidlo na produktovej stránke | Ľahký, prispôsobí sa téme, vie čítať vybraný variant | Zdieľa JavaScript so stránkou, podlieha jej bezpečnostným pravidlám |
| **Iframe** | Modal s 3D a profilom, až po kliku | Oddelený od kódu e-shopu, nezávislé vydávanie, žiadne konflikty štýlov | Úložisko je oddelené per obchod, takže profil sa medzi e-shopmi nezdieľa. Kamera potrebuje `allow="camera"` a Safari má vlastné obmedzenia |
| **SDK** | Headless / React shopy, mobilné aplikácie | Plná kontrola | Viac práce pre e-shop |

### Platformy

| Platforma | Ako sa napojiť | Na čo dať pozor |
|---|---|---|
| **Shopify** | Theme app extension: app block (obchodník si ho umiestni) | Povinné pre App Store. JS do 10 KB (odporúčané), aplikácia smie zhoršiť Lighthouse skóre najviac o 10 bodov. Billing API povinné (Shopify berie 0 % z prvého 1 mil. $). Tri povinné GDPR webhooky. Objednávky cez Web Pixel `checkout_completed` (staré skripty na ďakovacej stránke skončili 26. 8. 2026). Vratky s dôvodom `SIZE_TOO_SMALL` / `SIZE_TOO_LARGE` |
| **Shoptet** | Partnerské API (schválenie cez api@shoptet.cz) + trh doplnkov | Domáci trh: ~28 600 CZ a ~7 600 SK obchodov. Kód cez `/template-include`, objednávky cez webhooky. OAuth token per inštalácia, API tokeny platia 30 minút |
| **WooCommerce** | WordPress plugin | Webhooky podpísané HMAC-SHA256, vratky cez REST API |
| **Shopware 6** | „App" model (vlastný backend) | Kontrola v obchode s aplikáciami |
| **Magento / Adobe Commerce** | Composer modul | Automatická + ručná kontrola |
| **Vlastné e-shopy** | HTML snippet | Ako Kiwi: ID produktu, SKU, obrázky, CSS selektor na umiestnenie |

### Mapovanie produktov a meranie

- Kľúč produktu: **ID variantu + SKU + GTIN** a zjednotené názvy veľkostí.
- Princíp ako pri Fit Analytics: **produkt bez mapovania = žiadne tlačidlo.**
- Jedno ID relácie od produktovej stránky cez objednávku až po vratku. Bez neho sa ROI nedá zmerať.

### Výkon

Core Web Vitals („dobré" pri 75. percentile): LCP ≤ 2,5 s, INP ≤ 200 ms, CLS ≤ 0,1. Postupy: asynchrónne načítanie, načítať až pri zobrazení alebo kliknutí, preconnect, CDN, rezervované miesto pre tlačidlo, otestovaný výpadok nášho skriptu, náhradná tabuľka veľkostí.

---

## 8. Onboarding značky a marketing

### Kroky pre značku (obsah tutoriálu)

| # | Krok | Kto | Trvanie |
|---|---|---|---|
| 1 | Registrácia, výber platformy | Značka | min. |
| 2 | Inštalácia: Shopify app / Shoptet doplnok / plugin / snippet | Značka (alebo my) | ~5 min |
| 3 | Katalóg sa načíta sám, značka vyberie produkty | Značka | min. |
| 4 | Podklady: tabuľka rozmerov, info o látke, DXF ak je, 1 vzorka | Značka | podľa značky |
| 5 | **Digitalizácia a kalibrácia** | **My** | **X dní** |
| 6 | Kontrola a zapnutie produktov | Značka | min. |
| 7 | Prehľad: použitie, odporúčania, konverzia, vratky (A/B) | Značka | priebežne |

Krok 5 je miesto, kde sa vízia „e-shop nahrá produkty a hotovo" stretne s realitou. DXF strihy neobsahujú informáciu o šitých spojoch a najlepší automatický výsledok, ktorý sme našli, správne spracoval 68 % strihov. **Spočiatku to predávať ako službu („do X dní je to live") a automatizovať postupne**, keď uvidíte, čo sa opakuje.

### Poradie marketingu

1. **Landing page** s tlačidlom „chcem demo" môže ísť von hneď (lacná validácia záujmu).
2. **Demo video** až keď funguje 3D prehliadač na reálnom produkte.
3. **Tutoriál** až keď existuje integrácia.

---

## 9. Biznis model a validácia

### Čo sa dá o vratkách tvrdiť

| Údaj | Hodnota | Zdroj |
|---|---|---|
| Vratky online oblečenia, USA | 24,4 % | Coresight |
| Najčastejší dôvod vratky v DE/AT | Nesedí veľkosť (67–71 %) | Univerzita Bamberg, rakúska štúdia 2026 |
| Fashion e-shopy s vratkami nad 20 % | 67,8 % | EHI 2026 |
| Náklad na jednu vratku | ~5–20 € | EHI 2026 |
| Cyklistika špecificky | **Spoľahlivé číslo neexistuje** | |

### Čo fit nástroje reálne dosahujú

- **Zalando (vlastná publikovaná štúdia):** personalizované odporúčanie veľkosti zvýšilo konverziu o 2,1 %, ale vratky kvôli veľkosti významne neznížilo. Upozornenie „tento kus je menší/väčší" znížilo vratky kvôli veľkosti o 3,8 až 6,6 %, no zvýšilo objednávanie viacerých veľkostí naraz o 11 až 19 %.
- **Štúdia 2025 (496 000 kusov):** používatelia nástroja na veľkosť vracali o 0,65 % viac, ale ich hodnota pre obchod v ďalšom štvrťroku vzrástla o 7,5 %.
- **Tvrdenia predajcov:** −10 % až −50 % vratiek. Porovnávajú používateľov s nepoužívateľmi, takže sú skreslené.

**Záver:** pilot musí mať **kontrolnú skupinu**, ktorá tlačidlo nevidí. Argument pri predaji je „zmeriame to spolu", nie „sľubujeme −30 %".

### Cenové modely na trhu

| Model | Príklady | Cena |
|---|---|---|
| Predplatné podľa počtu objednávok | Kiwi / Sizekick / True Fit | 8–27 $ / 115–1 150 $ / 1 000 $ mesačne |
| Za sken | 3DLOOK | 499 $ za 100, 999 $ za 500 |
| Za skúšku | Genlook, LookSize | od 0,02 $ za skúšku |
| Riadená služba | PICTOFiT / Vue.ai | 500 $ mesačne / ~30 000 $ ročne (odhad) |
| Digitalizácia za kus | odhady trhu | 50–150 $ fotogrametria, 100–500 $ ručne |
| Podiel z ušetrených vratiek | | Verejne nenájdené |

**Návrh na overenie:** jednorazový poplatok za digitalizovaný model + mesačné predplatné podľa počtu objednávok. Pilot zadarmo alebo lacno výmenou za dáta (tech packy, materiály, export vratiek).

### Dve cesty k prvej značke

| | A) D2C značka s e-shopom (napr. Isadore, SK) | B) Výrobca tímových dresov (napr. Kalas, CZ) |
|---|---|---|
| Kto platí | E-commerce manažér | Obchod / výroba |
| Metrika | Vratky + konverzia (pomalé, treba A/B a návštevnosť) | Ušetrené fyzické sady veľkostí pre kluby (priama, rýchla) |
| Integrácia | E-shop widget od začiatku | Stačí odkaz pre členov klubu |
| Dáta o ľuďoch | Anonymní zákazníci | Jazdci s menom, celá tímová objednávka naraz |
| Zhoda s víziou | Úplná | Úvodný krok, widget príde potom |

Cesta B overí fit engine rýchlejšie a lacnejšie, cesta A ide priamo k cieľovému produktu. **Rozhodnutie závisí od toho, ku komu máte reálny prístup.**

---

## 10. GDPR a právo

- **Fotky a miery tela nie sú automaticky biometrické údaje.** GDPR za biometriu považuje spracovanie na jednoznačnú identifikáciu osoby, meranie tela kvôli oblečeniu to zvyčajne nie je.
- **Reálne riziko sú zdravotné údaje.** Tvar tela a váha môžu prezradiť zdravotný stav. Súdny dvor EÚ (C-184/20) považuje za citlivé aj údaje, ktoré citlivú vlastnosť prezrádzajú nepriamo. Právnici preto odporúčajú **výslovný súhlas + posúdenie vplyvu (DPIA)**.
- **Čo robia iní:** 3DLOOK fotky hneď maže a nechá si len miery a 3D model. Kleep si nechá len čísla. Size Stream spracuje sken priamo v telefóne. Najbezpečnejšie je **vôbec nepracovať s tvárou**.
- **Profil medzi obchodmi:** ak by simiq držal jeden profil tela použiteľný vo viacerých e-shopoch, stáva sa prevádzkovateľom údajov, nie len sprostredkovateľom. **Verzia 1: profil per obchod / per zariadenie**, čo je jednoduchšie aj právne.
- **Shopify** vyžaduje tri GDPR webhooky (žiadosť o údaje, vymazanie zákazníka, vymazanie obchodu) s 30-dňovou lehotou.
- **EU AI Act:** virtuálne skúšanie nie je vysoko rizikové (recitál 16 ho považuje za doplnkovú funkciu). Povinnosť označovať AI-generované obrázky (čl. 50 ods. 2) platí od 2. 8. 2026, ale len ak by ste generovali fotorealistické obrázky.
- **USA (pri expanzii):** žaloby podľa zákona štátu Illinois o biometrických údajoch (BIPA) mieria na try-on nástroje, hlavne so skenom tváre (napr. Charlotte Tilbury, vyrovnanie 2,9 mil. $).

---

## 11. Akcelerátor: fit štúdia a odpovede mentorovi

### Fit štúdia: hlavný výstup programu

- 20 až 30 jazdcov, ideálne cez bike-fitting štúdio alebo klub (tam sú ľudia v jazdnej polohe a meranie je samozrejmosť).
- Každý sa zmeria, vyskúša si dve veľkosti na trenažéri v jazdnej polohe a ohodnotí, ako sedia jednotlivé zóny.
- Výsledok je jedno číslo do pitchu: *„trafíme veľkosť, ktorú si jazdec sám vybral, v X % prípadov; tabuľka veľkostí v Y %"*.
- Zároveň tým nakalibrujete fit engine.

### Odpovede pre mentora (na vloženie)

> **1. Stav:** Tvoríme B2B virtual fitting pre športové oblečenie, začíname cyklistikou. Dres a bibky musia sedieť v jazdnej polohe, nie v stoji, no existujúce nástroje pracujú so statickou postavou a ignorujú materiál. Veľké cyklistické značky (Castelli, Sportful, Le Col, Assos) dnes ponúkajú len statické tabuľky veľkostí. Máme market research, UX prototyp, user scenáre a preverené technické možnosti. Funkčný prototyp zatiaľ nemáme.
>
> **2. Najväčšia výzva:** Technicky: dokázať, že vieme predpovedať sedenie v jazdnej polohe presnejšie ako tabuľka veľkostí. Výskum ukazuje, že bežné 3D simulácie tlaku s realitou nekorelujú, preto staviame na meraní natiahnutia materiálu a kalibrácii na reálnych jazdcoch. Biznisovo: kto v značke za to zaplatí a podľa akej metriky (vratky, konverzia, úspora na fit setoch).
>
> **3. Cieľ do konca programu:** Funkčný prototyp na 2 až 3 reálnych produktoch jednej značky. Fit štúdia s 20 až 30 jazdcami, ktorá ukáže presnosť oproti tabuľke veľkostí. Pilot alebo LOI s aspoň jednou značkou vrátane dohody o dátach. Otestovaný cenník a predajná stratégia pre ďalšie B2B značky.
>
> **S čím by ste nám vedeli pomôcť:** kontakty na e-commerce alebo produktových ľudí v športových značkách a spätná väzba na cenotvorbu B2B SaaS.

Posledný bod je dôležitý: mentori reagujú na konkrétnu prosbu, nie na všeobecný stav.

---

## 12. Štruktúra špecifikácie (OpenSpec)

Návrh, zatiaľ nič nezapísané v `openspec/`.

### Schopnosti systému (specs)

| Capability | Čo pokrýva |
|---|---|
| `body-profile` | Vstupy od zákazníka, parametre Anny, súhlas a GDPR |
| `garment-model` | Tabuľka rozmerov, zóny, materiály, veľkosti |
| `garment-intake` | Čo značka dodáva, kontrola podkladov |
| `fit-engine` | Natiahnutie, dĺžky v polohe, odporúčanie, istota |
| `fit-calibration` | Fit štúdia, vratky → korekcie |
| `tryon-viewer` | 3D, mapa napätia, polohy |
| `shop-embed` | Loader, web component, iframe, náhradné riešenie, limity výkonu |
| `platform-adapters` | Shopify, Shoptet, WooCommerce |
| `catalog-sync` | Mapovanie variant / SKU / GTIN |
| `analytics` | Udalosti, objednávky, vratky, A/B |
| `brand-portal` | Onboarding, schválenie, prehľad |

### Poradie zmien (changes)

| # | Zmena | Obsah | Prečo v tomto poradí |
|---|---|---|---|
| 1 | `fit-engine-poc` | Anny + 1 dres + 1 bibky, jazdná poloha, výpočet natiahnutia | Overí jadro hodnoty, dá sa porovnať s fit štúdiou |
| 2 | `tryon-viewer-mvp` | 3D + mapa napätia | Zdroj pre demo video a pitch |
| 3 | `shop-embed-mvp` | Snippet + 1 platforma (podľa prvej značky) | Až keď je čo ukázať |
| 4 | `brand-onboarding` | Portál na podklady, schválenie | Keď príde druhá značka |
| 5 | `analytics-ab` | Udalosti, objednávky, vratky, kontrolná skupina | Pred ostrým pilotom |

---

## 13. Riziká a otvorené otázky

### Technické riziká

| Riziko | Dopad | Čo s tým |
|---|---|---|
| Anny sa v hlbokom predklone deformuje (boky, rozkrok) | Nepresné bibky | Prvý technický test. Prípadne doplniť vlastné opravné tvary |
| Chýbajú krivky natiahnutia látok | Fit engine nemá vstup | Technické listy od dodávateľa látky, inak lacné vlastné meranie |
| Výška + váha = pol veľkosti neistoty | Zlé odporúčanie na hranici | Ukazovať istotu, ponúknuť voliteľné obvody |
| DXF bez informácie o šitých spojoch | Ručná práca pri digitalizácii | Služba, nie samoobsluha. Automatizovať postupne |
| Licencie komerčných simulátorov pre SaaS nie sú verejné | Právne / cenové riziko | Vyjednať, alebo použiť Warp/Newton (Apache 2.0) |

### Biznisové riziká

| Riziko | Čo s tým |
|---|---|
| ROI sa nedá dokázať | A/B v pilote od prvého dňa, jedno ID relácie až po vratku |
| Trenie pre zákazníka | Zadanie do 30 sekúnd |
| Nákladná digitalizácia každého produktu | Šablóny + tabuľka rozmerov, poplatok za onboarding |

### Otvorené otázky pre tím

1. **Prvá značka:** D2C s e-shopom (A) alebo výrobca tímových dresov (B)? Ku komu máte reálny prístup?
2. Akú platformu má prvá značka (Shopify, Shoptet, iné)? Určí, ktorý obal stavať prvý.
3. Kto v tíme vie 3D (CLO, Blender, Python) a kto web?
4. Ktoré jazdné polohy sú kľúčové (na rukovätiach zhora, v spodnom úchope, aero)?
5. Mužské aj ženské strihy od začiatku, alebo najprv jeden?

### Neoverené

- Ceny SMPL licencie po zániku Meshcapade.
- Stav API CLO-SET Fitting, licenčné podmienky Style3D a Browzwear pre server/SaaS.
- Presnosť Bodygram.
- Aký podiel značiek má DXF oproti len tech packu.
- Stav Google Try On v EÚ.
- Či Rapha reálne používa True Fit.
- Webhooky vratiek v Shoptete.

---

## 14. Zdroje

**Model tela a simulácia**
- [Anny demo](https://anny-demo.europe.naverlabs.com/) · [Anny GitHub](https://github.com/naver/anny) · [Anny paper (arXiv 2511.03589)](https://arxiv.org/abs/2511.03589)
- [SMPL](https://smpl.is.tue.mpg.de/) · [SMPL-X](https://smpl-x.is.tue.mpg.de/) · [STAR](https://star.is.tue.mpg.de/) · [Meshcapade](https://meshcapade.com/) · [MPG o akvizícii](https://www.mpg.de/26082348)
- [MPFB / MakeHuman FAQ](https://static.makehumancommunity.org/mpfb/faq/use_in_closed_source.html)
- [Browzwear VStitcher Server](https://help.browzwear.com/en/articles/13065059-open-platform-and-vstitcher-server-engine) · [CLO developer](https://developer.clo3d.com/) · [Marvelous Designer na Linuxe](https://digitalproduction.com/2025/09/30/marvelous-designer-finally-sews-itself-into-linux/)
- [Newton (Warp)](https://pypi.org/project/newton/) · [Codim-IPC](https://github.com/ipc-sim/Codim-IPC) · [GarmentCode](https://github.com/maria-korosteleva/GarmentCode) · [WebGPU cloth benchmark](https://arxiv.org/html/2507.11794v1)

**Presnosť simulácie a materiály**
- [Cyklistické oblečenie, virtuálny vs. nameraný tlak (2024)](https://gcris.ieu.edu.tr/entities/publication/807ba37d-13d3-4dbe-bfcd-3cd56a17c66e)
- [Kompresné oblečenie, Brubacher 2021](https://e-space.mmu.ac.uk/627476)
- [Plavky v CLO (2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12588493/)
- [Laplaceov zákon a tlak](https://pmc.ncbi.nlm.nih.gov/articles/PMC8401858/)
- [Porovnanie meraní látok (2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12349057/) · [Odhad parametrov látky (CGF 2024)](https://diglib.eg.org/handle/10.1111/cgf15027)
- [DXF norma ASTM D6673](https://store.astm.org/d6673-04.html) · [Parsovanie strihov do 3D](https://research.adobe.com/publication/parsing-sewing-patterns-into-3d-garments)

**Telo z mier a fotiek**
- [Presnosť z výšky a váhy (ANSUR)](https://pdfs.semanticscholar.org/a063/833838a473f518b2d20df83f530e8d1d3412.pdf) · [3DLOOK presnosť](https://3dlook.ai/?p=44386) · [Sken telefónom (arXiv 2608.12827)](https://arxiv.org/abs/2608.12827)

**Konkurencia a trh**
- [Fit Analytics docs](https://developers.fitanalytics.com/about-fit-finder/) · [True Fit](https://apps.shopify.com/truefit) · [Kiwi Sizing](https://apps.shopify.com/kiwi-sizing) · [Sizekick](https://apps.shopify.com/sizekick-size-advisor) · [Kleep](https://kleep.ai/blog/how-body-scan-sizing-works) · [3DLOOK pricing](https://3dlook.ai/pricing/) · [PICTOFiT](https://apps.shopify.com/pictofit-1) · [Genlook](https://apps.shopify.com/genlook-virtual-try-on) · [LookSize](https://looksize.com/pricing) · [Virtusize](https://virtusize.com/ja/app-pricing)
- [Zalando 3D pilot](https://www.just-style.com/news/zalando-pilots-virtual-fitting-room-globally/) · [Snap zatvára enterprise](https://techcrunch.com/2023/09/27/snap-shutters-its-enterprise-services-division-after-less-than-a-year/) · [Presize koniec](https://www.hohenstein.com/en/news/presize-discontinued-digital-size-calculator-service) · [Metail](https://metail.com)
- [Custom tímové dresy](https://cyclingweekly.com/group-tests/best-cycling-bespoke-custom-kit-brands-472747) · [Fit sety pre kluby](https://pearlizumi.eu/blogs/news/choosing-the-right-fit-for-your-custom-cycling-kit) · [Isadore](https://www.mtbiker.shop/shop/apparel/isadore-debut-jersey-gleam-p274711.html)

**Vratky a ROI**
- [Zalando štúdia (arXiv 2106.03532)](https://arxiv.org/abs/2106.03532) · [Štúdia 2025, 496k kusov](https://www.elsevier.es/en-revista-journal-innovation-knowledge-376-articulo-fits-like-glove-knowledge-use-S2444569X25001246)
- [Coresight](https://coresight.com/research/the-true-cost-of-apparel-returns/) · [Univerzita Bamberg](https://www.uni-bamberg.de/presse/pm/artikel/massnahmen-retouren-2019/) · [Rakúska štúdia 2026](https://www.leadersnet.at/news/99374,retouren-bleiben-ein-problem-im-onlinehandel.html) · [EHI 2026](https://retail-news.de/ehi-retourenmanagement-2026-fashion-kosten/)
- [Fit Analytics case studies](https://fitanalytics.com/case-studies) · [Bold Metrics](https://www.boldmetrics.com/virtual-sizer)

**Integrácia a výkon**
- [Shopify App Store požiadavky](https://shopify.dev/docs/apps/launch/shopify-app-store/app-store-requirements) · [Theme app extensions](https://shopify.dev/docs/apps/build/online-store/theme-app-extensions/configuration) · [App proxy](https://shopify.dev/docs/apps/build/online-store/app-proxies) · [Kontrolný zoznam](https://shopify.dev/docs/apps/launch/app-requirements-checklist) · [Podiel z príjmov](https://shopify.dev/changelog/update-to-shopifys-app-developer-revenue-share) · [GDPR webhooky](https://shopify.dev/docs/apps/build/compliance/privacy-law-compliance) · [Web Pixels](https://shopify.dev/docs/apps/build/marketing-analytics/build-web-pixels) · [Koniec skriptov na ďakovacej stránke](https://weltpixel.com/blogs/news/shopify-thank-you-page-tracking-the-august-26-2026-deadline) · [ReturnReason](https://shopify.dev/docs/api/admin-graphql/2026-07/enums/ReturnReason)
- [Shoptet šablóny](https://developers.shoptet.cz/uvodni-stranka/api/dokumentace/kody-do-sablon/) · [Shoptet webhooky](https://developers.shoptet.cz/webhooky/) · [Počty obchodov (TASR)](https://www.teraz.sk/ekonomika/rok-2026-je-pre-slovenske-e-shopy-pozit/980905-clanok.html)
- [WooCommerce webhooky](https://developer.woocommerce.com/docs/apis/rest-api/v3/webhooks/) · [Shopware apps](https://developer.shopware.com/docs/v6.6/concepts/extensions/apps-concept.html) · [Adobe Marketplace](https://developer.adobe.com/commerce/marketplace/guides/sellers/submit-for-review) · [Kiwi integrácia](https://developers.kiwisizing.com/docs/product-page-integration)
- [CHIPS (cookies v iframe)](https://developer.chrome.com/docs/privacy-sandbox/chips/) · [Kamera v iframe](https://blog.addpipe.com/camera-and-microphone-access-in-cross-oirigin-iframes-with-feature-policy/) · [Core Web Vitals](https://web.dev/articles/vitals) · [Tretie strany a výkon](https://web.dev/articles/optimizing-content-efficiency-loading-third-party-javascript) · [Rýchlosť a konverzia](https://web.dev/case-studies/milliseconds-make-millions)

**Právo**
- [Súdny dvor EÚ C-184/20](https://www.insideprivacy.com/eu-data-protection/special-category-data-by-inference-cjeu-significantly-expands-the-scope-of-article-9-gdpr/) · [Mishcon: virtual try-on a GDPR](https://www.mishcon.com/news/virtual-try-on-data-protection-compliance-considerations) · [3DLOOK súkromie](https://3dlook.ai/?p=36961) · [AI Act recitál 16](https://artificialintelligenceact.eu/recital/16/) · [AI Act čl. 50](https://www.cooley.com/news/insight/2026/2026-08-03-eu-ai-act-transparency-obligations-take-effect-2-august-2026) · [Charlotte Tilbury BIPA](https://idtechwire.com/charlotte-tilbury-beauty-agrees-to-2-9m-settlement-over-biometric-data-collection)
