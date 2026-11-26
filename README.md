# Red Signal - Watch Face (Wear OS 5, Watch Face Format v2)
Watchface personale per Xiaomi Watch 2 Pro: HUD rosso/verde su grigio antracite, con bande a strisce, cifre squadrate a contorno e onde da oscilloscopio.

Dati in tempo reale:
- ora HH:MM (cifre grafiche) e secondi
- data: giorno della settimana, giorno, mese
- batteria: barra a strisce + percentuale
- passi: numero + barra (piena a 10.000), con onde rosse animate che scorrono sullo sfondo
- modalità always-on: ora e data, colori attenuati

Grafica rigenerabile con `python3 tools/gen.py app/src/main/res/drawable tools/roboto_cond_semibold.ttf`
Font: Roboto Condensed (licenza OFL).

L'APK compilato da GitHub Actions viene pubblicato sul ramo `apk` (`redsignal.apk`); si installa con `adb install -r redsignal.apk`.
