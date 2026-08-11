"""Snijd alle vrije-penkrul-SVG's reproduceerbaar bij op hun tekenwerk."""

from pathlib import Path
import re

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
INITIALEN = ROOT / "images" / "initialen" / "vrije-penkrul"
MARGE = 6


def _getekende_grenzen(page, svg_text):
    return page.evaluate(
        """tekst => {
            const bron = new DOMParser().parseFromString(tekst, 'image/svg+xml').documentElement;
            const svg = document.importNode(bron, true);
            svg.style.cssText = 'position:fixed;left:-10000px;top:-10000px;width:400px;height:400px';
            document.body.append(svg);
            const dozen = [...svg.querySelectorAll('[data-role]')].map(el => el.getBBox());
            const grenzen = {
                links: Math.min(...dozen.map(b => b.x)),
                boven: Math.min(...dozen.map(b => b.y)),
                rechts: Math.max(...dozen.map(b => b.x + b.width)),
                onder: Math.max(...dozen.map(b => b.y + b.height)),
            };
            svg.remove();
            return grenzen;
        }""",
        svg_text,
    )


def _getal(waarde):
    return f"{waarde:.3f}".rstrip("0").rstrip(".")


def main():
    bestanden = sorted(INITIALEN.glob("*.svg")) + sorted((INITIALEN / "donker").glob("*.svg"))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content("<!doctype html><body></body>")
        for bestand in bestanden:
            tekst = bestand.read_text(encoding="utf-8")
            vak = _getekende_grenzen(page, tekst)
            x = vak["links"] - MARGE
            y = vak["boven"] - MARGE
            breedte = vak["rechts"] - vak["links"] + 2 * MARGE
            hoogte = vak["onder"] - vak["boven"] + 2 * MARGE
            viewbox = " ".join(_getal(v) for v in (x, y, breedte, hoogte))
            nieuw = re.sub(r'viewBox="[^"]+"', f'viewBox="{viewbox}"', tekst, count=1)
            bestand.write_text(nieuw, encoding="utf-8", newline="\n")
        browser.close()
    print(f"{len(bestanden)} initialen bijgesneden met {MARGE} SVG-eenheden marge.")


if __name__ == "__main__":
    main()
