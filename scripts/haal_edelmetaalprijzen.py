#!/usr/bin/env python3
"""Ververs data/edelmetaalprijzen.json met de actuele goud- en zilverkoers.

De site rekent de metaalwaarde van Bijbelse gewichten en munten om naar euro's.
Die omrekening gebeurt niet live in de browser: dat zou bij elk bezoek een
externe aanroep kosten, de pagina offline onbruikbaar maken en de bezoeker aan
een derde partij blootstellen. In plaats daarvan staan de koersen in een
databestand met datum en bron, en haalt dit script ze op wanneer je ze wilt
bijwerken.

    python scripts/haal_edelmetaalprijzen.py

Let op: dit is de waarde van het métaal, niet de koopkracht van de munt. Een
penning was een dagloon; die verhouding zegt meer dan het zilvergewicht.
"""
import datetime
import json
import os
import urllib.request

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOEL = os.path.join(WORTEL, 'data', 'edelmetaalprijzen.json')
TROY_OUNCE_IN_GRAM = 31.1034768

METAAL = {'goud': 'XAU', 'zilver': 'XAG'}
METAAL_URL = 'https://api.gold-api.com/price/{}'
KOERS_URL = 'https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR'


def _haal(url):
    # Zonder eigen User-Agent antwoordt de wisselkoers-API met 403.
    verzoek = urllib.request.Request(url, headers={'User-Agent': 'open-vertaling/1.0'})
    with urllib.request.urlopen(verzoek, timeout=30) as respons:
        return json.loads(respons.read().decode('utf-8'))


def main():
    spot = {}
    for naam, symbool in METAAL.items():
        gegevens = _haal(METAAL_URL.format(symbool))
        prijs = float(gegevens['price'])
        if prijs <= 0:
            raise SystemExit(f'onbruikbare prijs voor {naam}: {prijs}')
        spot[naam] = prijs

    koers = _haal(KOERS_URL)
    euro_per_dollar = float(koers['rates']['EUR'])
    if not 0.5 < euro_per_dollar < 2:
        raise SystemExit(f'onwaarschijnlijke wisselkoers: {euro_per_dollar}')

    data = {
        'toelichting': (
            'Spotprijzen voor de metaalwaarde-omrekening op maateenheden.html. '
            'Dit is de waarde van het edelmetaal, niet de koopkracht van de munt. '
            'Ververs met scripts/haal_edelmetaalprijzen.py.'
        ),
        'bijgewerkt': koers.get('date') or datetime.date.today().isoformat(),
        'bron': {
            'metaalprijs': 'gold-api.com — spotprijs per troy ounce in USD',
            'wisselkoers': 'Europese Centrale Bank via frankfurter.dev',
        },
        'troyOunceInGram': TROY_OUNCE_IN_GRAM,
        'euroPerDollar': round(euro_per_dollar, 5),
        'spotDollarPerTroyOunce': {n: round(p, 2) for n, p in spot.items()},
        'euroPerGram': {
            n: round(p * euro_per_dollar / TROY_OUNCE_IN_GRAM, 4)
            for n, p in spot.items()
        },
    }

    with open(DOEL, 'w', encoding='utf-8', newline='\n') as bestand:
        bestand.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(f'{DOEL} bijgewerkt ({data["bijgewerkt"]}):')
    print(f'  goud   € {data["euroPerGram"]["goud"]:.2f} per gram')
    print(f'  zilver € {data["euroPerGram"]["zilver"]:.4f} per gram')


if __name__ == '__main__':
    main()
