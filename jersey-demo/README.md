# Ukážkový dres na tele z Anny (záloha práce z 15. 10. 2026)

Záloha práce s dresom „Mens Cycling Jersey – Green Printed“ z RenderHubu (kúpený s komerčnou licenciou). Licencia dovoľuje model použiť, nie ho zverejniť, a repozitár je verejný. Preto tu nie je nič, z čoho sa dá dres vytiahnuť: pôvodné súbory modelu (DXF, ZPRJ, GLB, textúry) ani naše exporty s dresom (`anny-jersey-*.glb`, `anny-green-jersey.glb`, textúra potlače). Tie sú len v `SIMIQ/mens cycling jersey-green printed` na Macu.

## Obsah

- `simiq-anny/` – výstupy z CLO a z prenosu dresu na Anny
  - `anny-m178-75-apose.obj`, `anny-m178-75-hoods.obj` – telo z Anny (muž 178 cm / 75 kg) v súradniciach CLO (cm, Y hore)
  - `anny-m178-75-to-hoods.pc2` – animácia z A-pózy do pózy hoods (150 snímok, 30 fps) na import do CLO
  - `*-render.png` – náhľady dresu nasimulovaného v CLO na tele z Anny
  - `strainmap-*.mp4` – videá mapy natiahnutia z CLO (spredu, zboku, zozadu, spolu)
  - `heatmap/` – heatmapa fit enginu a porovnanie s CLO
- `fit/` – rozmery dresu odmerané zo strihu (`poms.json`) a výsledky enginu po zónach (`fit.json`)
- `demo/data/` – ukážkový dres v 6 veľkostiach, ukážková látka a hranice, odporúčania pre 45 mužských postáv
- `demo/site/` – dáta pre budúcu demo stránku (geometria a telá z Anny; textúra `jersey.png` sa sem kopíruje len lokálne)
- `scripts/` – skripty, ktorými to vzniklo (cesty v starších ukazujú do dočasného pracovného priečinka)
- `videos/` – rovnaký dres M na štyroch telách (178/75, 180/64, 176/88, 192/82) v troch polohách, simulácia v CLO (16. 10. 2026)
  - `simiq-{hoods,drops,standing}-sequence.mp4` – telo sa plynule mení, 6 pohľadov (potlač a heatmapa spredu, zozadu, z boku, šikmo)
  - `simiq-{hoods,drops,standing}-comparison.png` – 4 telá × 5 pohľadov
  - `simiq-all-poses.mp4`, `simiq-poses-summary.png` – všetky tri polohy spolu
- `bodies/` – časovanie animácií (ktorá snímka patrí ktorému telu)

## Ako vznikli videá v `videos/`

1. `clo_bodies.py`, `clo_sequence.py`, `clo_poses.py`, `clo_standing.py` (spúšťať v `engine/` cez `uv run python …`) vyrobia z Anny animácie `.pc2` v súradniciach CLO. Každá začína presne tam, kde stojí telo v projekte CLO (odchýlka pod 0,001 mm), a telo sa medzi postavami mení plynule, aby dres nebolo treba nasadzovať nanovo.
2. V CLO: otvoriť projekt s Anny 178/75, v Animation Editore zmazať starú nahrávku dresu a potom starú animáciu tela (v tomto poradí, inak dres ostane v starom tvare), načítať `.pc2` (Import Point Cache, cm), nastaviť End Frame a nahrať tlačidlom Record.
3. `clo_export_views.py` (Edit → Python Script v CLO) vyexportuje videá z pohľadov; pohľad priamo zozadu je klávesa 8 v 3D okne.
4. `compose.py` z nich poskladá videá s popiskami a prehľadové obrázky.

Stoj sa simuluje zvlášť z pôvodného nasadenia dresu v stoji. Po jazde by spodný okraj ostal nakrivo, lebo zdvihnuté ľavé koleno vytlačí dres nahor a látka sa trením sama nestiahne.

`.pc2` animácie (spolu ~400 MB) a projekty `.zprj` (obsahujú kúpený dres) nie sú v gite, sú len na Macu v `simiq-anny/bodies/`.

## Dôležité pri čítaní čísel

- V projekte CLO má látka nastavené zrážanie útku 72 %. Strih (DXF) má hrudník asi 120 cm, CLO dres zobrazuje akoby mal asi 86 cm. Ukážkový dres používa rozmery podľa CLO (× 0,72).
- Látka (`fabric-knit`) a hranice tesné / akurát / voľné sú ukážkové, nie z merania ani zo skúšok na ľuďoch.
- Dres v CLO nemá uvedený materiál (fyzikálne vlastnosti „Unknown“).
