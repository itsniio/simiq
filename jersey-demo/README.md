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
- `scripts/` – skripty, ktorými to vzniklo (cesty v nich ukazujú do dočasného pracovného priečinka)

## Dôležité pri čítaní čísel

- V projekte CLO má látka nastavené zrážanie útku 72 %. Strih (DXF) má hrudník asi 120 cm, CLO dres zobrazuje akoby mal asi 86 cm. Ukážkový dres používa rozmery podľa CLO (× 0,72).
- Látka (`fabric-knit`) a hranice tesné / akurát / voľné sú ukážkové, nie z merania ani zo skúšok na ľuďoch.
- Dres v CLO nemá uvedený materiál (fyzikálne vlastnosti „Unknown“).
