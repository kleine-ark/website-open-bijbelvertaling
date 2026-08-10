#!/usr/bin/env python3
"""Bouw vier onderwerp-tags uit expliciet beoordeelde Schriftpassages.

De woordenschat rond zegen, vloek, belofte en feest is contextgevoelig. Daarom
publiceert deze bouwer geen regex-treffers. De onderstaande passages vormen de
gereviewde bronlijst; een kleine wachtrij bewaart twijfelgevallen apart.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
from typing import Any

try:
    from scripts.build_corpus_naslag import load_books, load_corpus
except ModuleNotFoundError:  # Direct uitgevoerd als `python scripts/...`.
    from build_corpus_naslag import load_books, load_corpus


ROOT = Path(__file__).resolve().parents[1]


def p(book: str, chapter: int, first: int, last: int | None = None,
      category: str = "kernpassage", rank: int = 2) -> tuple[str, int, int, int, str, int]:
    """Definieer één beoordeelde passage zonder tekstherkenning."""
    return book, chapter, first, first if last is None else last, category, rank


# Formele zegenwoorden: door God toegezegd, door een gezagsdrager uitgesproken
# of als zaligspreking/benedictie aan de hoorder meegegeven.
BLESSING_PASSAGES = [
    p("genesis", 1, 22, category="scheppingszegen", rank=1),
    p("genesis", 1, 28, category="scheppingszegen", rank=1),
    p("genesis", 5, 2, category="scheppingszegen"), p("genesis", 9, 1, category="verbondszegen"),
    p("genesis", 9, 26, 27, "uitgesproken-zegen"), p("genesis", 12, 2, 3, "verbondszegen", 1),
    p("genesis", 14, 19, 20, "uitgesproken-zegen", 1), p("genesis", 17, 16, category="verbondszegen"),
    p("genesis", 17, 20, category="verbondszegen"), p("genesis", 22, 16, 18, "verbondszegen", 1),
    p("genesis", 24, 60, category="familiezegen"), p("genesis", 26, 3, 4, "verbondszegen"),
    p("genesis", 25, 11, category="goddelijke-zegen"),
    p("genesis", 26, 12, category="goddelijke-zegen"), p("genesis", 26, 24, category="goddelijke-zegen"),
    p("genesis", 26, 29, category="uitgesproken-zegen"), p("genesis", 27, 27, 29, "vaderlijke-zegen", 1),
    p("genesis", 27, 39, 40, "vaderlijke-zegen"), p("genesis", 28, 3, 4, "vaderlijke-zegen"),
    p("genesis", 28, 13, 15, "verbondszegen", 1), p("genesis", 32, 27, 30, "persoonlijke-zegen"),
    p("genesis", 35, 9, 12, "verbondszegen"), p("genesis", 47, 7, category="persoonlijke-zegen"),
    p("genesis", 47, 10, category="persoonlijke-zegen"), p("genesis", 48, 3, 4, "verbondszegen"),
    p("genesis", 48, 9, category="vaderlijke-zegen"), p("genesis", 48, 15, 20, "vaderlijke-zegen", 1),
    p("genesis", 49, 1, 28, "stammenzegen", 1), p("exodus", 39, 43, category="leiderszegen"),
    p("leviticus", 9, 22, 24, "priesterlijke-zegen", 1), p("numeri", 6, 22, 27, "priesterlijke-zegen", 1),
    p("numeri", 23, 7, 10, "profetische-zegen"), p("numeri", 23, 18, 24, "profetische-zegen"),
    p("numeri", 24, 3, 9, "profetische-zegen"), p("deuteronomium", 1, 11, category="leiderszegen"),
    p("deuteronomium", 7, 12, 14, "verbondszegen"), p("deuteronomium", 28, 1, 14, "verbondszegen", 1),
    p("deuteronomium", 33, 1, 29, "stammenzegen", 1), p("jozua", 14, 13, category="leiderszegen"),
    p("jozua", 22, 6, 8, "leiderszegen"), p("ruth", 2, 4, category="dagelijkse-zegen"),
    p("ruth", 2, 12, category="persoonlijke-zegen"), p("ruth", 3, 10, category="persoonlijke-zegen"),
    p("ruth", 4, 11, 12, "familiezegen"), p("ruth", 4, 14, 15, "familiezegen"),
    p("1samuel", 2, 20, category="priesterlijke-zegen"), p("2samuel", 6, 18, category="koninklijke-zegen"),
    p("2samuel", 6, 20, category="koninklijke-zegen"), p("2samuel", 7, 28, 29, "gebed-om-zegen", 1),
    p("1koningen", 8, 14, category="koninklijke-zegen"), p("1koningen", 8, 55, 61, "koninklijke-zegen", 1),
    p("1kronieken", 16, 2, category="koninklijke-zegen"), p("1kronieken", 29, 20, category="gemeentezegen"),
    p("2kronieken", 6, 3, category="koninklijke-zegen"), p("2kronieken", 30, 27, category="priesterlijke-zegen"),
    p("nehemia", 8, 6, category="gemeentezegen"), p("psalmen", 1, 1, 3, "zaligspreking", 1),
    p("psalmen", 32, 1, 2, "zaligspreking"), p("psalmen", 41, 2, 4, "zaligspreking"),
    p("psalmen", 67, 2, 8, "gebed-om-zegen"), p("psalmen", 112, 1, 3, "zaligspreking"),
    p("psalmen", 115, 12, 15, "gemeentezegen"), p("psalmen", 128, 1, 6, "zaligspreking"),
    p("psalmen", 133, 3, category="goddelijke-zegen"), p("spreuken", 3, 13, 18, "zaligspreking"),
    p("jeremia", 17, 7, 8, "zaligspreking"), p("mattheus", 5, 3, 12, "zaligspreking", 1),
    p("mattheus", 11, 6, category="zaligspreking"), p("mattheus", 16, 17, category="zaligspreking"),
    p("lukas", 1, 42, 45, "uitgesproken-zegen"), p("lukas", 6, 20, 23, "zaligspreking", 1),
    p("lukas", 11, 28, category="zaligspreking"), p("lukas", 24, 50, 51, "messiaanse-zegen", 1),
    p("markus", 10, 16, category="messiaanse-zegen", rank=1),
    p("johannes", 20, 29, category="zaligspreking"), p("handelingen", 3, 25, 26, "verbondszegen"),
    p("romeinen", 15, 5, 6, "apostolische-zegen"), p("romeinen", 15, 13, category="apostolische-zegen"),
    p("romeinen", 12, 14, category="geroepen-tot-zegen", rank=1),
    p("romeinen", 15, 33, category="apostolische-zegen"), p("romeinen", 16, 20, category="apostolische-zegen"),
    p("2korinthiers", 13, 13, category="apostolische-zegen", rank=1),
    p("galaten", 6, 18, category="apostolische-zegen"), p("efeziers", 1, 3, category="geestelijke-zegen", rank=1),
    p("efeziers", 6, 23, 24, "apostolische-zegen"), p("filippenzen", 4, 23, category="apostolische-zegen"),
    p("1tessalonicensen", 5, 23, 24, "apostolische-zegen"), p("2tessalonicensen", 3, 16, category="apostolische-zegen"),
    p("hebreeen", 13, 20, 21, "apostolische-zegen"), p("1petrus", 3, 9, category="geroepen-tot-zegen"),
    p("2petrus", 1, 2, category="apostolische-zegen"), p("openbaring", 1, 3, category="zaligspreking"),
    p("openbaring", 22, 7, category="zaligspreking"), p("openbaring", 22, 14, category="zaligspreking"),
]


# Werkelijk uitgesproken vloeken en als vloek geformuleerde verbondssancties.
CURSE_PASSAGES = [
    p("genesis", 3, 14, category="goddelijke-vloek", rank=1), p("genesis", 3, 17, 19, "goddelijke-vloek", 1),
    p("genesis", 4, 11, 12, "goddelijke-vloek"), p("genesis", 9, 25, 27, "vaderlijke-vloek", 1),
    p("genesis", 12, 3, category="verbondsvloek"), p("genesis", 27, 29, category="verbondsvloek"),
    p("genesis", 49, 5, 7, "vaderlijke-vloek"), p("exodus", 21, 17, category="wetsvloek"),
    p("leviticus", 20, 9, category="wetsvloek"), p("leviticus", 26, 14, 39, "verbondsvloek", 1),
    p("numeri", 5, 18, 22, "vloekeed"), p("numeri", 24, 9, category="verbondsvloek"),
    p("deuteronomium", 11, 26, 29, "verbondsvloek"), p("deuteronomium", 27, 12, 26, "verbondsvloek", 1),
    p("deuteronomium", 28, 15, 68, "verbondsvloek", 1), p("deuteronomium", 29, 18, 28, "verbondsvloek"),
    p("deuteronomium", 30, 7, category="verbondsvloek"), p("jozua", 6, 26, category="profetische-vloek", rank=1),
    p("jozua", 9, 23, category="uitgesproken-vloek"), p("richteren", 5, 23, category="uitgesproken-vloek"),
    p("richteren", 9, 20, category="profetische-vloek"), p("richteren", 9, 56, 57, "vervulde-vloek"),
    p("1samuel", 14, 24, category="vloekeed"), p("1samuel", 14, 28, category="vloekeed"),
    p("1samuel", 14, 44, category="vloekeed"), p("1samuel", 17, 43, category="uitgesproken-vloek"),
    p("2samuel", 16, 5, 13, "uitgesproken-vloek"), p("1koningen", 16, 34, category="vervulde-vloek"),
    p("2koningen", 2, 24, category="profetische-vloek"), p("2koningen", 5, 27, category="profetische-vloek"),
    p("nehemia", 13, 25, category="uitgesproken-vloek"), p("job", 3, 1, 10, "zelfvervloeking"),
    p("psalmen", 109, 6, 20, "vloekgebed", 1), p("psalmen", 137, 7, 9, "vloekgebed"),
    p("jeremia", 11, 3, category="verbondsvloek"), p("jeremia", 17, 5, 6, "profetische-vloek", 1),
    p("jeremia", 20, 14, 18, "zelfvervloeking"), p("jeremia", 48, 10, category="profetische-vloek"),
    p("maleachi", 1, 14, category="profetische-vloek"), p("maleachi", 2, 2, 3, "profetische-vloek"),
    p("maleachi", 3, 9, category="verbondsvloek"), p("maleachi", 4, 6, category="profetische-vloek"),
    p("mattheus", 21, 18, 20, "messiaanse-vloek"), p("mattheus", 25, 41, category="eindoordeel-vloek", rank=1),
    p("markus", 11, 12, 14, "messiaanse-vloek"), p("markus", 11, 20, 21, "messiaanse-vloek"),
    p("markus", 14, 71, category="zelfvervloeking"),
    p("galaten", 1, 8, 9, "apostolische-vloek", 1), p("galaten", 3, 10, 13, "wetsvloek", 1),
    p("1korinthiers", 16, 22, category="apostolische-vloek"),
]


# Goddelijke toezeggingen. Verzen die alleen achteraf het woord "belofte"
# noemen, worden niet als de belofte zelf gepubliceerd.
PROMISE_PASSAGES = [
    p("genesis", 3, 15, category="messiaanse-belofte", rank=1), p("genesis", 6, 18, category="verbondsbelofte"),
    p("genesis", 8, 21, 22, "verbondsbelofte"), p("genesis", 9, 8, 17, "verbondsbelofte", 1),
    p("genesis", 12, 1, 3, "abrahamitische-belofte", 1), p("genesis", 13, 14, 17, "abrahamitische-belofte"),
    p("genesis", 15, 1, 6, "abrahamitische-belofte"), p("genesis", 15, 13, 21, "abrahamitische-belofte"),
    p("genesis", 17, 1, 8, "abrahamitische-belofte"), p("genesis", 17, 15, 21, "abrahamitische-belofte"),
    p("genesis", 22, 15, 18, "abrahamitische-belofte", 1), p("genesis", 26, 2, 5, "verbondsbelofte"),
    p("genesis", 28, 12, 15, "verbondsbelofte"), p("genesis", 35, 9, 12, "verbondsbelofte"),
    p("genesis", 46, 2, 4, "persoonlijke-belofte"), p("genesis", 49, 10, category="messiaanse-belofte", rank=1),
    p("exodus", 3, 7, 10, "bevrijdingsbelofte"), p("exodus", 6, 2, 8, "verbondsbelofte", 1),
    p("exodus", 19, 5, 6, "verbondsbelofte"), p("exodus", 23, 20, 31, "landsbelofte"),
    p("leviticus", 26, 3, 13, "verbondsbelofte"), p("numeri", 14, 20, 24, "persoonlijke-belofte"),
    p("numeri", 24, 17, 19, "messiaanse-belofte", 1), p("deuteronomium", 18, 15, 19, "messiaanse-belofte", 1),
    p("deuteronomium", 30, 1, 10, "herstelbelofte"), p("deuteronomium", 31, 6, 8, "nabijheidsbelofte"),
    p("jozua", 1, 1, 9, "landsbelofte"), p("richteren", 6, 14, 16, "persoonlijke-belofte"),
    p("1samuel", 2, 35, category="priesterbelofte"), p("2samuel", 7, 8, 16, "davidische-belofte", 1),
    p("1koningen", 8, 25, 26, "davidische-belofte"), p("1koningen", 9, 3, 5, "davidische-belofte"),
    p("1kronieken", 17, 10, 14, "davidische-belofte"), p("2kronieken", 7, 12, 18, "verbondsbelofte"),
    p("psalmen", 2, 7, 9, "messiaanse-belofte"), p("psalmen", 16, 10, 11, "messiaanse-belofte"),
    p("psalmen", 32, 8, category="leidingsbelofte"), p("psalmen", 34, 19, category="nabijheidsbelofte"),
    p("psalmen", 37, 3, 6, "zorgbelofte"), p("psalmen", 46, 2, 4, "nabijheidsbelofte"),
    p("psalmen", 89, 4, 5, "davidische-belofte"), p("psalmen", 89, 29, 38, "davidische-belofte"),
    p("psalmen", 91, 14, 16, "beschermingsbelofte"), p("psalmen", 110, 1, 4, "messiaanse-belofte", 1),
    p("spreuken", 3, 5, 6, "leidingsbelofte"), p("jesaja", 7, 14, category="messiaanse-belofte", rank=1),
    p("jesaja", 9, 5, 6, "messiaanse-belofte", 1), p("jesaja", 11, 1, 10, "messiaanse-belofte"),
    p("jesaja", 25, 6, 9, "heilsbelofte"), p("jesaja", 35, 1, 10, "herstelbelofte"),
    p("jesaja", 40, 29, 31, "krachtbelofte"), p("jesaja", 41, 10, 14, "nabijheidsbelofte", 1),
    p("jesaja", 42, 1, 7, "messiaanse-belofte"), p("jesaja", 43, 1, 7, "nabijheidsbelofte"),
    p("jesaja", 49, 5, 13, "messiaanse-belofte"), p("jesaja", 52, 13, 15, "messiaanse-belofte"),
    p("jesaja", 53, 1, 12, "messiaanse-belofte", 1), p("jesaja", 54, 10, 17, "verbondsbelofte"),
    p("jesaja", 55, 1, 3, "heilsbelofte"), p("jesaja", 55, 10, 11, "woordbelofte"),
    p("jesaja", 61, 1, 3, "messiaanse-belofte"), p("jesaja", 65, 17, 25, "nieuwe-schepping-belofte"),
    p("jeremia", 23, 5, 6, "messiaanse-belofte", 1), p("jeremia", 29, 10, 14, "herstelbelofte"),
    p("jeremia", 31, 3, 14, "herstelbelofte"), p("jeremia", 31, 31, 34, "nieuw-verbond-belofte", 1),
    p("jeremia", 32, 37, 41, "herstelbelofte"), p("jeremia", 33, 14, 17, "davidische-belofte"),
    p("ezechiel", 11, 17, 20, "herstelbelofte"), p("ezechiel", 18, 21, 23, "vergevingsbelofte"),
    p("ezechiel", 34, 23, 31, "messiaanse-belofte"), p("ezechiel", 36, 22, 28, "nieuw-hart-belofte", 1),
    p("ezechiel", 37, 12, 14, "opstandingsbelofte"), p("ezechiel", 37, 21, 28, "herstelbelofte"),
    p("daniel", 7, 13, 14, "messiaanse-belofte", 1), p("daniel", 12, 2, 3, "opstandingsbelofte"),
    p("hosea", 2, 19, 22, "verbondsbelofte"), p("joel", 2, 28, 32, "geestbelofte", 1),
    p("amos", 9, 11, 15, "herstelbelofte"), p("micha", 5, 1, 4, "messiaanse-belofte"),
    p("zacharia", 9, 9, 10, "messiaanse-belofte"), p("zacharia", 12, 10, category="geestbelofte"),
    p("zacharia", 13, 1, category="reinigingsbelofte"), p("maleachi", 3, 1, category="messiaanse-belofte"),
    p("maleachi", 4, 2, category="messiaanse-belofte"), p("mattheus", 11, 28, 30, "rustbelofte", 1),
    p("mattheus", 16, 18, category="gemeentebelofte"), p("mattheus", 18, 20, category="nabijheidsbelofte"),
    p("mattheus", 28, 18, 20, "nabijheidsbelofte", 1), p("johannes", 3, 16, 18, "heilsbelofte", 1),
    p("johannes", 5, 24, category="heilsbelofte"), p("johannes", 6, 37, 40, "heilsbelofte"),
    p("johannes", 10, 27, 29, "bewaringsbelofte"), p("johannes", 11, 25, 26, "opstandingsbelofte", 1),
    p("johannes", 14, 1, 3, "wederkomstbelofte"), p("johannes", 14, 16, 18, "geestbelofte"),
    p("johannes", 14, 26, 27, "geestbelofte"), p("johannes", 16, 7, 15, "geestbelofte"),
    p("handelingen", 1, 4, 8, "geestbelofte"), p("handelingen", 2, 38, 39, "geestbelofte", 1),
    p("romeinen", 8, 28, 30, "heilsbelofte"), p("romeinen", 8, 32, 39, "bewaringsbelofte"),
    p("romeinen", 10, 9, 13, "heilsbelofte"), p("1korinthiers", 10, 13, category="uitkomstbelofte"),
    p("1korinthiers", 15, 51, 57, "opstandingsbelofte"), p("2korinthiers", 1, 20, category="vervulling-in-christus"),
    p("2korinthiers", 5, 1, category="opstandingsbelofte"), p("2korinthiers", 12, 9, category="genadebelofte"),
    p("galaten", 3, 13, 14, "geestbelofte"), p("galaten", 3, 26, 29, "abrahamitische-belofte"),
    p("filippenzen", 1, 6, category="voltooiingsbelofte"), p("filippenzen", 3, 20, 21, "opstandingsbelofte"),
    p("filippenzen", 4, 19, category="zorgbelofte"), p("1tessalonicensen", 4, 13, 18, "wederkomstbelofte"),
    p("2timotheus", 2, 11, 13, "heilsbelofte"), p("titus", 1, 2, category="eeuwig-leven-belofte"),
    p("hebreeen", 4, 14, 16, "toegang-belofte"), p("hebreeen", 8, 8, 12, "nieuw-verbond-belofte"),
    p("hebreeen", 13, 5, 6, "nabijheidsbelofte"), p("jakobus", 1, 5, category="wijsheidsbelofte"),
    p("jakobus", 1, 12, category="levenskroon-belofte"), p("1petrus", 1, 3, 5, "erfenisbelofte"),
    p("1johannes", 1, 9, category="vergevingsbelofte"), p("1johannes", 2, 25, category="eeuwig-leven-belofte"),
    p("openbaring", 2, 7, category="overwinningsbelofte"), p("openbaring", 2, 10, category="levenskroon-belofte"),
    p("openbaring", 3, 20, 21, "overwinningsbelofte"), p("openbaring", 21, 1, 7, "nieuwe-schepping-belofte", 1),
    p("openbaring", 22, 12, 14, "wederkomstbelofte"), p("openbaring", 22, 20, category="wederkomstbelofte"),
]


# Instelling, kalender en concrete viering van de Bijbelse hoogtijden.
FEAST_PASSAGES = [
    p("exodus", 12, 1, 28, "pascha-ongezuurde-broden", 1), p("exodus", 12, 43, 51, "pascha"),
    p("exodus", 13, 3, 10, "ongezuurde-broden"), p("exodus", 23, 14, 19, "drie-pelgrimsfeesten", 1),
    p("exodus", 34, 18, 26, "feestkalender"), p("leviticus", 23, 1, 44, "feestkalender", 1),
    p("numeri", 9, 1, 14, "pascha"), p("numeri", 10, 10, category="feestoffers"),
    p("numeri", 28, 9, 31, "feestoffers"), p("numeri", 29, 1, 40, "feestoffers", 1),
    p("deuteronomium", 16, 1, 17, "drie-pelgrimsfeesten", 1), p("jozua", 5, 10, 12, "pascha"),
    p("deuteronomium", 31, 10, 13, "loofhuttenfeest"),
    p("richteren", 21, 19, 21, "feest-van-jahweh"), p("1samuel", 1, 3, 7, "jaarlijks-feest"),
    p("1koningen", 8, 2, category="loofhuttenfeest"), p("1koningen", 8, 65, 66, "loofhuttenfeest"),
    p("2koningen", 23, 21, 23, "pascha"), p("2kronieken", 8, 12, 13, "feestkalender"),
    p("2kronieken", 30, 1, 27, "pascha"), p("2kronieken", 35, 1, 19, "pascha"),
    p("ezra", 3, 4, 6, "loofhuttenfeest"), p("ezra", 6, 19, 22, "pascha-ongezuurde-broden"),
    p("nehemia", 8, 14, 18, "loofhuttenfeest"), p("esther", 9, 17, 32, "purim", 1),
    p("psalmen", 81, 4, 5, "feestkalender"), p("2kronieken", 7, 8, 10, "loofhuttenfeest"),
    p("ezechiel", 45, 18, 25, "feestkalender"), p("zacharia", 14, 16, 19, "loofhuttenfeest"),
    p("mattheus", 26, 2, 30, "pascha"), p("markus", 14, 1, 26, "pascha"),
    p("lukas", 2, 41, 43, "pascha"), p("lukas", 22, 1, 20, "pascha"),
    p("johannes", 2, 13, 23, "pascha"), p("johannes", 5, 1, category="naamloos-feest"),
    p("johannes", 6, 4, category="pascha"), p("johannes", 7, 2, 39, "loofhuttenfeest", 1),
    p("johannes", 10, 22, 23, "tempelwijding", 1), p("johannes", 11, 55, 57, "pascha"),
    p("johannes", 12, 1, category="pascha"), p("johannes", 12, 12, category="pascha"),
    p("johannes", 12, 20, category="pascha"), p("johannes", 13, 1, category="pascha"),
    p("johannes", 18, 28, category="pascha"), p("johannes", 19, 14, category="pascha"),
    p("handelingen", 2, 1, 4, "wekenfeest-pinksteren", 1), p("handelingen", 12, 3, 4, "ongezuurde-broden-pascha"),
    p("handelingen", 18, 21, category="feestverwijzing"), p("handelingen", 20, 6, category="ongezuurde-broden"),
    p("handelingen", 20, 16, category="wekenfeest-pinksteren"), p("handelingen", 27, 9, category="verzoendag"),
    p("1korinthiers", 5, 7, 8, "pascha-ongezuurde-broden"), p("1korinthiers", 16, 8, category="wekenfeest-pinksteren"),
    p("kolossenzen", 2, 16, 17, "onderwijs-over-feesten"),
    p("3ezra", 1, 1, 22, "pascha-ongezuurde-broden"),
    p("tobit", 1, 6, category="pelgrimsfeesten"), p("tobit", 2, 2, category="wekenfeest-pinksteren"),
    p("1makkabeeen", 4, 52, 59, "tempelwijding"), p("2makkabeeen", 10, 1, 8, "tempelwijding"),
]


TOPICS = {
    "zegeningen": {
        "naam": "Zegeningen",
        "beschrijving": "Uitgesproken zegeningen, zaligsprekingen en zegenbeden in de Bijbel.",
        "kleur": "#b68a2e",
        "passages": BLESSING_PASSAGES,
    },
    "vervloekingen": {
        "naam": "Vervloekingen",
        "beschrijving": "Uitgesproken vloeken en de als vloek geformuleerde sancties van het verbond.",
        "kleur": "#8b4545",
        "passages": CURSE_PASSAGES,
    },
    "beloften": {
        "naam": "Beloften",
        "beschrijving": "Goddelijke toezeggingen van het eerste verbond tot de nieuwe schepping.",
        "kleur": "#547c78",
        "passages": PROMISE_PASSAGES,
    },
    "bijbelse-feesten": {
        "naam": "Bijbelse feesten",
        "beschrijving": "De instelling, kalender en viering van de feesten die in de Bijbel worden genoemd.",
        "kleur": "#9a6b3d",
        "passages": FEAST_PASSAGES,
    },
}


REVIEW_CASES = [
    ("genesis 27:12", "vervloekingen", "Jakob vreest een vloek; hier wordt geen vloek uitgesproken."),
    ("spreuken 26:2", "vervloekingen", "Onderwijs over een onverdiende vloek, niet een uitgesproken vloek."),
    ("handelingen 7:5", "beloften", "Verwijst terug naar een belofte zonder de toezegging zelf opnieuw uit te spreken."),
    ("hebreeen 11:13", "beloften", "Vat eerdere beloften samen, maar is niet zelf de goddelijke toezegging."),
    ("galaten 3:9", "zegeningen", "Samenvatting van Abrahams zegen; de oorspronkelijke zegen staat al bij Genesis 12."),
    ("hosea 9:5", "bijbelse-feesten", "Retorische verwijzing naar een feest zonder duidelijke identificatie van het feest."),
]


AUDIT_PATTERNS = {
    "zegeningen": re.compile(r"\b(?:zegen\w*|zalig\w*)\b", re.I),
    "vervloekingen": re.compile(r"\b(?:vloek\w*|vervloek\w*|verdoem\w*)\b", re.I),
    "beloften": re.compile(r"\b(?:belof\w*|beloof\w*|toezeg\w*)\b", re.I),
    "bijbelse-feesten": re.compile(
        r"\b(?:feest\w*|pascha|pinkster\w*|ongezuurde\w*|loofhut\w*|purim|verzoendag|tempelwijd\w*)\b",
        re.I,
    ),
}


def _passage_label(book: str, chapter: int, first: int, last: int) -> str:
    return f"{book} {chapter}:{first}" if first == last else f"{book} {chapter}:{first}-{last}"


def _json_dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def build_onderwerpen(root: Path = ROOT, write: bool = True) -> dict[str, Any]:
    books = [book for book in load_books(root) if book.get("chaptersIncluded")]
    corpus = load_corpus(root, include_ethiopic=True)
    valid = {verse.ref for verse in corpus}
    position = {verse.ref: index for index, verse in enumerate(corpus)}
    tags: list[dict[str, Any]] = []

    for topic_id, definition in TOPICS.items():
        mentions: dict[str, dict[str, Any]] = {}
        for book, chapter, first, last, category, rank in definition["passages"]:
            passage = _passage_label(book, chapter, first, last)
            for verse in range(first, last + 1):
                ref = f"{book} {chapter}:{verse}"
                if ref not in valid:
                    raise ValueError(f"Onbekende Bijbelverwijzing in {topic_id}: {ref} ({passage})")
                candidate = {
                    "ref": ref,
                    "rang": rank,
                    "passage": passage,
                    "subcategorie": category,
                    "zekerheid": "zeker",
                    "reviewStatus": "agent-reviewed",
                    "humanReviewed": False,
                }
                if ref not in mentions or rank < mentions[ref]["rang"]:
                    mentions[ref] = candidate
        ordered = [mentions[ref] for ref in sorted(mentions, key=position.__getitem__)]
        tags.append({
            "id": topic_id,
            "naam": definition["naam"],
            "beschrijving": definition["beschrijving"],
            "kleur": definition["kleur"],
            "selectiemethode": "expliciet-beoordeelde-passages",
            "reviewStatus": "agent-reviewed",
            "humanReviewed": False,
            "verzen": ordered,
        })

    reviewqueue = [
        {
            "ref": ref,
            "onderwerp": topic,
            "notitie": note,
            "reviewStatus": "agent-reviewed-needs-human-review",
            "humanReviewed": False,
        }
        for ref, topic, note in REVIEW_CASES
    ]
    if not {item["ref"] for item in reviewqueue} <= valid:
        raise ValueError("De reviewwachtrij bevat een onbekende Bijbelverwijzing")

    # Deze audit bewijst dat ieder boek werkelijk is doorzocht, maar houdt
    # woordtreffers bewust buiten de publicatie totdat hun context is beoordeeld.
    published_anywhere = {item["ref"] for tag in tags for item in tag["verzen"]}
    audit_candidates = []
    for topic_id, pattern in AUDIT_PATTERNS.items():
        for verse in corpus:
            match = pattern.search(verse.text)
            if match and verse.ref not in published_anywhere:
                audit_candidates.append({
                    "ref": verse.ref,
                    "onderwerp": topic_id,
                    "treffer": match.group(0),
                    "status": "lexicale-treffer-niet-gepubliceerd",
                    "humanReviewed": False,
                })

    per_book = []
    for book in books:
        prefix = book["id"] + " "
        counts = {
            tag["id"]: sum(item["ref"].startswith(prefix) for item in tag["verzen"])
            for tag in tags
        }
        per_book.append({
            "boek": book["id"],
            "naam": book["nameDutch"],
            "gescand": True,
            "verzenGetagd": sum(counts.values()),
            "perOnderwerp": counts,
            "twijfelgevallen": sum(item["ref"].startswith(prefix) for item in reviewqueue),
        })

    report = {
        "onderwerpen": [tag["id"] for tag in tags],
        "selectiemethode": "expliciet-beoordeelde-passages; geen automatische woordtreffers gepubliceerd",
        "boekenGescand": len(books),
        "verzenGescand": len(corpus),
        "perOnderwerp": {
            tag["id"]: {
                "verzenGetagd": len(tag["verzen"]),
                "passages": len({item["passage"] for item in tag["verzen"]}),
                "boekenMetTreffers": len({item["ref"].split(" ", 1)[0] for item in tag["verzen"]}),
                "subcategorieen": dict(sorted(Counter(item["subcategorie"] for item in tag["verzen"]).items())),
            }
            for tag in tags
        },
        "twijfelgevallen": len(reviewqueue),
        "lexicaleAudit": {
            "nietGepubliceerdeTreffers": len(audit_candidates),
            "perOnderwerp": dict(sorted(Counter(item["onderwerp"] for item in audit_candidates).items())),
            "uitleg": "Woordtreffers zijn niet automatisch tags; zij blijven apart totdat de context is beoordeeld.",
        },
        "reviewStatus": "agent-reviewed",
        "humanReviewed": False,
        "perBoek": per_book,
    }
    result = {
        "tags": tags,
        "reviewqueue": reviewqueue,
        "auditCandidates": audit_candidates,
        "report": report,
    }

    if write:
        data_dir = root / "data"
        _json_dump(data_dir / "onderwerpen-zegen-vloek-belofte-feest.json", {"tags": tags})
        _json_dump(data_dir / "onderwerpen-zegen-vloek-belofte-feest-reviewqueue.json", {"reviewqueue": reviewqueue})
        _json_dump(data_dir / "onderwerpen-zegen-vloek-belofte-feest-auditkandidaten.json", {"kandidaten": audit_candidates})
        _json_dump(data_dir / "onderwerpen-zegen-vloek-belofte-feest-dekking.json", report)
        tags_path = data_dir / "tags.json"
        document = json.loads(tags_path.read_text(encoding="utf-8"))
        replacement_ids = {tag["id"] for tag in tags}
        document["tags"] = [tag for tag in document.get("tags", []) if tag.get("id") not in replacement_ids] + tags
        _json_dump(tags_path, document)

    return result


if __name__ == "__main__":
    built = build_onderwerpen()
    print(json.dumps(built["report"], ensure_ascii=False, indent=2))
