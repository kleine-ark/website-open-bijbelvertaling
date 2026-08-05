#!/usr/bin/env python3
"""Leest de veldnummers uit een Google Formulier.

Elk antwoordveld van een formulier heeft een nummer van de vorm entry.1234567,
en dat nummer moet in js/feedback.js staan om er een melding naartoe te kunnen
sturen. Google toont die nummers nergens in de bewerkmodus, maar ze staan in de
openbare pagina van het formulier zelf — inloggen is dus niet nodig.

Gebruik:
    python scripts/formulier_velden.py https://docs.google.com/forms/d/e/…/viewform

De uitvoer is bedoeld om over te nemen in FORMULIER en FORMULIER_VELDEN in
js/feedback.js. Zie docs/opmerkingen-in-google-sheet.md.
"""
import json
import re
import sys
import urllib.request

# Google zet de opbouw van het formulier als JSON in een scriptvariabele. Dat is
# geen gedocumenteerde koppeling, dus als het ooit stopt met werken: open het
# formulier, bekijk de bron en zoek naar entry- of FB_PUBLIC_LOAD_DATA_.
GEGEVENS = re.compile(r"FB_PUBLIC_LOAD_DATA_ = (.*?);\s*</script>", re.S)


def haal_op(adres):
    verzoek = urllib.request.Request(adres, headers={"User-Agent": "openvertaling-veldlezer"})
    with urllib.request.urlopen(verzoek, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def velden(html):
    m = GEGEVENS.search(html)
    if not m:
        return None, []
    d = json.loads(m.group(1))
    titel = d[3] if len(d) > 3 else ""
    uit = []
    for vraag in (d[1][1] or []):
        naam = vraag[1]
        for onderdeel in (vraag[4] or []):
            uit.append((f"entry.{onderdeel[0]}", naam))
    return titel, uit


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    adres = sys.argv[1]
    try:
        html = haal_op(adres)
    except Exception as e:
        print(f"Formulier niet op te halen: {e}", file=sys.stderr)
        return 1

    titel, gevonden = velden(html)
    if gevonden is None or not gevonden:
        print("Geen velden gevonden.", file=sys.stderr)
        print("Klopt het adres, en staat het formulier open voor iedereen?", file=sys.stderr)
        return 1

    print(f"Formulier: {titel or '(zonder titel)'}\n")
    print("Verzendadres:")
    print("  " + re.sub(r"/viewform.*$", "/formResponse", adres) + "\n")
    print("Velden:")
    for nummer, naam in gevonden:
        print(f"  {nummer:<22} {naam}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
