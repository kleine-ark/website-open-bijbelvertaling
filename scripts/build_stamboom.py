#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genereer data/stamboom.json — de geslachtslijn van Adam tot Jozef en Jezus.

HOE DEZE DATA TOT STAND KOMT
============================
Er bestond geen genealogie-bestand in de repo, dus is de stamboom afgeleid uit
de vertaalde tekst zelf (`text2026` in `data/<boek>/<hoofdstuk>.json`).

Elke relatie in de tabel `BRONNEN` hieronder verwijst naar één vers. Twee
werkwijzen:

  V('genesis 5:6')    Automatisch: het script leest de zin "X verwekte Y" uit
                      het vers en leidt vader en kinderen daaruit af. Alleen
                      gebruikt bij de strak geformuleerde geslachtsregisters.

  K('genesis 46:11', 'levi', ['Gerson', 'Kehath', 'Merari'])
                      Handmatig: de vader wordt met zijn id genoemd, de
                      kinderen met hun naam. Het script CONTROLEERT dat elke
                      naam letterlijk in dat vers staat; staat hij er niet, dan
                      stopt de build met een foutmelding. Zo kan de tabel niet
                      stilletjes uit de pas lopen met de tekst.

  P('genesis 4:19', 'lamech', ['Ada', 'Zilla'])
                      Idem, maar voor echtgenotes/bijvrouwen.

Daarnaast:
  * `EXTRA_VERZEN` — losse verzen die bij een persoon horen maar geen relatie
    uitdrukken (bv. Genesis 1:27 bij Adam).
  * `NAAMKEUZE`    — weergavenaam bij naamsveranderingen (Abram → Abraham).
  * `OPMERKINGEN`  — één regel toelichting bij bekende personen.

BEWUST NIET OPGENOMEN
---------------------
  * Jaartallen en leeftijden. De hoofdstukken noemen ze wel, maar ze staan
    (voorlopig) niet in de stamboom.
  * De Horieten van Genesis 36:20-30 (Seïr, Lotan, Sobal, Zibeon, Ana, Dison,
    Ezer, Disan). De tekst leidt hen niet terug op Adam, dus ze zouden een
    tweede, losse wortel opleveren.
  * 1 Kronieken 3:21b-24 (Refaja, Arnan, Obadja, Sechanja en hun nageslacht).
    De tekst zegt daar alleen "de kinderen van X, de kinderen van Y" zonder
    duidelijk te maken wie van wie afstamt; die keten is niet te reconstrueren
    zonder te gissen.
  * De grote registers van 1 Kronieken 4-9. Die vertakken zo breed en met
    zoveel gelijknamige personen dat ze zonder aparte controleslag meer ruis
    dan stamboom opleveren.

Gebruik:  python scripts/build_stamboom.py
"""
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
UIT = os.path.join(DATA, 'stamboom.json')

# Namen die in een "zonen van"-opsomming een volk aanduiden, geen persoon.
VOLK_SUFFIX = ('ieten', 'iet', 'ijnen', 'ieters')


# ---------------------------------------------------------------- hulpmiddelen

def slug(naam):
    """'Mahalal-el' -> 'mahalal-el', 'Aäron' -> 'aaron', 'Tubal-Kaïn' -> 'tubal-kain'."""
    s = unicodedata.normalize('NFD', naam)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.lower().replace("'", '').replace('’', '')
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s or 'x'


def is_volk(naam):
    return any(naam.endswith(sfx) for sfx in VOLK_SUFFIX)


class Bron(object):
    """Eén regel uit de brontabel."""

    def __init__(self, soort, ref, ouder, namen, opties):
        self.soort = soort          # 'kind' | 'partner' | 'verwekte'
        self.ref = ref              # 'genesis 5:6'
        self.ouder = ouder          # id van vader/persoon (None bij 'verwekte')
        self.namen = namen or []
        self.opties = opties


def K(ref, ouder, namen, **opties):
    """Kinderen van `ouder`, met hun namen letterlijk uit het vers."""
    return Bron('kind', ref, ouder, namen, opties)


def P(ref, persoon, namen, **opties):
    """Echtgenotes/bijvrouwen van `persoon`. '#id' verwijst naar een bestaand persoon."""
    return Bron('partner', ref, persoon, namen, opties)


def V(ref, **opties):
    """Automatisch: alle 'X verwekte Y'-zinnen uit dit vers."""
    return Bron('verwekte', ref, None, None, opties)


# ------------------------------------------------------------------ brontabel
# Volgorde is belangrijk: een ouder moet bestaan voordat zijn kinderen komen.

BRONNEN = [
    # === Genesis 4 — Adam, Kaïn en Seth ===
    P('genesis 4:1', 'adam', ['Eva']),
    K('genesis 4:1', 'adam', ['Kaïn'], moeder='eva'),
    K('genesis 4:2', 'adam', ['Abel'], moeder='eva'),
    K('genesis 4:17', 'kain', ['Henoch']),
    K('genesis 4:18', 'henoch', ['Hirad']),
    V('genesis 4:18'),                                   # Hirad → Mechujael → Methusael → Lamech
    P('genesis 4:19', 'lamech', ['Ada', 'Zilla']),
    K('genesis 4:20', 'lamech', ['Jabal'], moeder='ada'),
    K('genesis 4:21', 'lamech', ['Jubal'], moeder='ada'),
    K('genesis 4:22', 'lamech', ['Tubal-Kaïn', 'Naema'], moeder='zilla', vrouwen=['Naema']),
    K('genesis 4:25', 'adam', ['Seth'], moeder='eva'),
    K('genesis 4:26', 'seth', ['Enos']),

    # === Genesis 5 — van Adam tot Noach ===
    K('genesis 5:3', 'adam', ['Seth'], moeder='eva'),     # zelfde persoon, extra vindplaats
    V('genesis 5:6'),                                     # Seth → Enos
    V('genesis 5:9'),                                     # Enos → Kenan
    V('genesis 5:12'),                                    # Kenan → Mahalal-el
    V('genesis 5:15'),                                    # Mahalal-el → Jered
    K('genesis 5:18', 'jered', ['Henoch'], id={'Henoch': 'henoch-jered'}),
    K('genesis 5:21', 'henoch-jered', ['Methusalach']),
    K('genesis 5:25', 'methusalach', ['Lamech'], id={'Lamech': 'lamech-methusalach'}),
    K('genesis 5:29', 'lamech-methusalach', ['Noach']),
    V('genesis 5:32'),                                    # Noach → Sem, Cham, Jafeth
    K('genesis 9:18', 'noach', ['Sem', 'Cham', 'Jafeth']),

    # === Genesis 10 — de volkerentafel ===
    K('genesis 10:2', 'jafeth', ['Gomer', 'Magog', 'Madai', 'Javan', 'Tubal', 'Mesech', 'Thiras']),
    K('genesis 10:3', 'gomer', ['Askenaz', 'Rifath', 'Togarma']),
    K('genesis 10:4', 'javan', ['Elisa', 'Tarsis', 'Chittieten', 'Dodanieten']),
    K('genesis 10:6', 'cham', ['Cusch', 'Mitsraim', 'Put', 'Kanaän']),
    K('genesis 10:7', 'cusch', ['Seba', 'Havila', 'Sabta', 'Raema', 'Sabtecha']),
    K('genesis 10:7', 'raema', ['Scheba', 'Dedan']),
    K('genesis 10:8', 'cusch', ['Nimrod']),
    K('genesis 10:13', 'mitsraim', ['Ludieten', 'Anamieten', 'Lehabieten', 'Naftuchieten']),
    K('genesis 10:14', 'mitsraim', ['Pathrusieten', 'Casluchieten', 'Caftorieten']),
    K('genesis 10:15', 'kanaan', ['Sidon', 'Heth']),
    K('genesis 10:16', 'kanaan', ['Jebusiet', 'Amoriet', 'Girgasiet']),
    K('genesis 10:17', 'kanaan', ['Hivviet', 'Arkiet', 'Siniet']),
    K('genesis 10:18', 'kanaan', ['Arvadiet', 'Tsemariet', 'Hamathiet']),
    K('genesis 10:22', 'sem', ['Elam', 'Assur', 'Arfachsad', 'Lud', 'Aram']),
    K('genesis 10:23', 'aram', ['Uz', 'Hul', 'Gether', 'Maz']),
    V('genesis 10:24'),                                   # Arfachsad → Selah → Heber
    K('genesis 10:25', 'heber', ['Peleg', 'Joktan']),
    K('genesis 10:26', 'joktan', ['Almodad', 'Selef', 'Hatsarmaveth', 'Jarach']),
    K('genesis 10:27', 'joktan', ['Hadoram', 'Usal', 'Dikla']),
    K('genesis 10:28', 'joktan', ['Obal', 'Abimaël', 'Scheba'], id={'Scheba': 'scheba-joktan'}),
    K('genesis 10:29', 'joktan', ['Ofir', 'Havila', 'Jobab'], id={'Havila': 'havila-joktan'}),

    # === Genesis 11 — van Sem tot Abram ===
    V('genesis 11:10'),                                   # Sem → Arfachsad
    V('genesis 11:12'),                                   # Arfachsad → Selah
    V('genesis 11:14'),                                   # Selah → Heber
    V('genesis 11:16'),                                   # Heber → Peleg
    V('genesis 11:18'),                                   # Peleg → Rehu
    V('genesis 11:20'),                                   # Rehu → Serug
    V('genesis 11:22'),                                   # Serug → Nahor
    V('genesis 11:24'),                                   # Nahor → Terah
    K('genesis 11:26', 'terah', ['Abram', 'Nahor', 'Haran'], id={'Nahor': 'nahor-terah'}),
    K('genesis 11:27', 'haran', ['Lot']),
    K('genesis 11:29', 'haran', ['Milka', 'Jiska'], vrouwen=['Milka', 'Jiska']),
    P('genesis 11:29', 'abram', ['Saraï']),
    P('genesis 11:29', 'nahor-terah', ['#milka']),

    # === Genesis 19 — Lot ===
    K('genesis 19:37', 'lot', ['Moab']),
    K('genesis 19:38', 'lot', ['Ben-ammi']),

    # === Genesis 16, 21, 25 — Abraham ===
    P('genesis 16:15', 'abram', ['Hagar']),
    K('genesis 16:15', 'abram', ['Ismaël'], moeder='hagar'),
    K('genesis 21:3', 'abram', ['Izak'], moeder='sarai'),
    P('genesis 25:1', 'abram', ['Ketura']),
    K('genesis 25:2', 'abram', ['Zimran', 'Joksan', 'Medan', 'Midian', 'Jisbak', 'Suah'], moeder='ketura'),
    K('genesis 25:3', 'joksan', ['Seba', 'Dedan'], id={'Seba': 'seba-joksan', 'Dedan': 'dedan-joksan'}),
    K('genesis 25:3', 'dedan-joksan', ['Assurieten', 'Letusieten', 'Leummieten']),
    K('genesis 25:4', 'midian', ['Efa', 'Efer', 'Henoch', 'Abida', 'Eldaa'], id={'Henoch': 'henoch-midian'}),
    K('genesis 25:13', 'ismael', ['Nabajoth', 'Kedar', 'Adbeel', 'Mibsam'], moeder='hagar'),
    K('genesis 25:14', 'ismael', ['Misma', 'Duma', 'Massa'], moeder='hagar'),
    K('genesis 25:15', 'ismael', ['Hadar', 'Thema', 'Jetur', 'Nafis', 'Kedma'], moeder='hagar'),

    # === Genesis 22, 24 — Nahor, Bethuël, Laban ===
    K('genesis 22:21', 'nahor-terah', ['Uz', 'Buz', 'Kemuël'], moeder='milka', id={'Uz': 'uz-nahor'}),
    K('genesis 22:21', 'kemuel', ['Aram'], id={'Aram': 'aram-kemuel'}),
    K('genesis 22:22', 'nahor-terah', ['Chesed', 'Hazo', 'Pildas', 'Jidlaf', 'Bethuël'], moeder='milka'),
    P('genesis 22:24', 'nahor-terah', ['Reüma']),
    K('genesis 22:24', 'nahor-terah', ['Tebah', 'Gaham', 'Tahas', 'Maächa'], moeder='reuma'),
    K('genesis 22:23', 'bethuel', ['Rebekka'], vrouwen=['Rebekka']),
    K('genesis 24:29', 'bethuel', ['Laban']),

    # === Genesis 25, 29, 30, 35 — Izak, Ezau en Jakob ===
    P('genesis 25:20', 'izak', ['#rebekka']),
    K('genesis 25:25', 'izak', ['Ezau'], moeder='rebekka'),
    K('genesis 25:26', 'izak', ['Jakob'], moeder='rebekka'),
    K('genesis 29:16', 'laban', ['Lea', 'Rachel'], vrouwen=['Lea', 'Rachel']),
    P('genesis 29:23', 'jakob', ['#lea']),
    P('genesis 29:28', 'jakob', ['#rachel']),
    P('genesis 30:4', 'jakob', ['Bilha']),
    P('genesis 30:9', 'jakob', ['Zilpa']),
    K('genesis 29:32', 'jakob', ['Ruben'], moeder='lea'),
    K('genesis 29:33', 'jakob', ['Simeon'], moeder='lea'),
    K('genesis 29:34', 'jakob', ['Levi'], moeder='lea'),
    K('genesis 29:35', 'jakob', ['Juda'], moeder='lea'),
    K('genesis 30:6', 'jakob', ['Dan'], moeder='bilha'),
    K('genesis 30:8', 'jakob', ['Nafthali'], moeder='bilha'),
    K('genesis 30:11', 'jakob', ['Gad'], moeder='zilpa'),
    K('genesis 30:13', 'jakob', ['Aser'], moeder='zilpa'),
    K('genesis 30:18', 'jakob', ['Issaschar'], moeder='lea'),
    K('genesis 30:20', 'jakob', ['Zebulon'], moeder='lea'),
    K('genesis 30:21', 'jakob', ['Dina'], moeder='lea', vrouwen=['Dina']),
    K('genesis 30:24', 'jakob', ['Jozef'], moeder='rachel'),
    K('genesis 35:18', 'jakob', ['Benjamin'], moeder='rachel'),

    # === Genesis 36 — Ezau, vader van de Edomieten ===
    P('genesis 36:2', 'ezau', ['Ada', 'Aholibama'], id={'Ada': 'ada-ezau'}),
    P('genesis 36:3', 'ezau', ['Basmath']),
    K('genesis 36:4', 'ezau', ['Elifaz'], moeder='ada-ezau'),
    K('genesis 36:4', 'ezau', ['Rehuël'], moeder='basmath'),
    K('genesis 36:5', 'ezau', ['Jehus', 'Jaëlam', 'Korah'], moeder='aholibama'),
    K('genesis 36:11', 'elifaz', ['Teman', 'Omar', 'Zefo', 'Gaetam', 'Kenaz']),
    P('genesis 36:12', 'elifaz', ['Timna']),
    K('genesis 36:12', 'elifaz', ['Amalek'], moeder='timna'),
    K('genesis 36:13', 'rehuel', ['Nahath', 'Zerah', 'Samma', 'Mizza'], id={'Zerah': 'zerah-rehuel'}),

    # === Genesis 38 — Juda en Thamar ===
    K('genesis 38:3', 'juda', ['Er']),
    K('genesis 38:4', 'juda', ['Onan']),
    K('genesis 38:5', 'juda', ['Sela']),
    P('genesis 38:6', 'er', ['Thamar']),
    K('genesis 38:29', 'juda', ['Perez'], moeder='thamar'),
    K('genesis 38:30', 'juda', ['Zera'], moeder='thamar', id={'Zera': 'zerah-juda'}),

    # === Genesis 41, 46 — de zeventig zielen die in Egypte kwamen ===
    K('genesis 46:9', 'ruben', ['Hanoch', 'Pallu', 'Hezron', 'Karmi'], id={'Hezron': 'hezron-ruben'}),
    K('genesis 46:10', 'simeon', ['Jemuël', 'Jamin', 'Ohad', 'Jachin', 'Zohar', 'Saul']),
    K('genesis 46:11', 'levi', ['Gerson', 'Kehath', 'Merari']),
    K('genesis 46:12', 'juda', ['Er', 'Onan', 'Sela', 'Perez']),
    K('genesis 46:12', 'juda', ['Zerah'], id={'Zerah': 'zerah-juda'}),
    K('genesis 46:12', 'perez', ['Hezron', 'Hamul'], id={'Hezron': 'hezron-perez'}),
    K('genesis 46:13', 'issaschar', ['Tola', 'Puwa', 'Job', 'Simron']),
    K('genesis 46:14', 'zebulon', ['Sered', 'Elon', 'Jahleel']),
    K('genesis 46:16', 'gad', ['Zifjon', 'Haggi', 'Schuni', 'Ezbon', 'Eri', 'Arodi', 'Areli']),
    K('genesis 46:17', 'aser', ['Jimna', 'Jisva', 'Jisvi', 'Berija', 'Sera'], vrouwen=['Sera']),
    K('genesis 46:17', 'berija', ['Heber', 'Malchiël'], id={'Heber': 'heber-berija'}),
    P('genesis 41:45', 'jozef', ['Asnath']),
    K('genesis 41:51', 'jozef', ['Manasse'], moeder='asnath'),
    K('genesis 41:52', 'jozef', ['Efraïm'], moeder='asnath'),
    K('genesis 46:21', 'benjamin', ['Bela', 'Becher', 'Asbel', 'Gera', 'Naäman',
                                    'Echi', 'Ros', 'Muppim', 'Huppim', 'Ard']),
    K('genesis 46:23', 'dan', ['Chusim']),
    K('genesis 46:24', 'nafthali', ['Jahzeel', 'Guni', 'Jezer', 'Sillem']),

    # === Exodus 6 en Numeri 26 — het huis van Levi ===
    K('exodus 6:16', 'gerson', ['Libni', 'Simeï']),
    K('exodus 6:17', 'kehath', ['Amram', 'Jizhar', 'Hebron', 'Uzziël']),
    K('exodus 6:18', 'merari', ['Machli', 'Musi']),
    K('numeri 26:59', 'levi', ['Jochebed'], vrouwen=['Jochebed']),
    P('exodus 6:19', 'amram', ['#jochebed']),
    K('exodus 6:19', 'amram', ['Aäron', 'Mozes'], moeder='jochebed'),
    K('numeri 26:59', 'amram', ['Mirjam'], moeder='jochebed', vrouwen=['Mirjam']),
    K('exodus 6:20', 'jizhar', ['Korah', 'Nefeg', 'Zichri'], id={'Korah': 'korah-jizhar'}),
    K('exodus 6:21', 'uzziel', ['Misael', 'Elzafan', 'Sithri']),
    P('exodus 6:22', 'aaron', ['Eliseba']),
    K('exodus 6:22', 'aaron', ['Nadab', 'Abihu', 'Eleazar', 'Ithamar'], moeder='eliseba'),
    K('exodus 6:23', 'korah-jizhar', ['Assir', 'Elkana', 'Abiasaf'], id={'Assir': 'assir-korah'}),
    K('exodus 6:24', 'eleazar', ['Pinehas']),

    # === Ruth 4 en 1 Kronieken 2 — van Perez tot David ===
    V('ruth 4:18'),                                       # Perez → Hezron
    V('ruth 4:19', ids={'Hezron': 'hezron-perez'}),       # Hezron → Ram → Amminadab
    V('ruth 4:20'),                                       # Amminadab → Nahesson → Salma
    K('ruth 4:21', 'salma', ['Boaz']),                    # het vers schrijft hier "Salmon"
    P('ruth 4:13', 'boaz', ['Ruth']),
    K('ruth 4:21', 'boaz', ['Obed'], moeder='ruth'),
    V('ruth 4:22'),                                       # Obed → Isaï → David
    K('1kronieken 2:9', 'hezron-perez', ['Jerahmeël', 'Ram', 'Chelubai']),
    K('1kronieken 2:6', 'zerah-juda', ['Zimri', 'Ethan', 'Heman', 'Chalcol', 'Dara']),
    K('1kronieken 2:8', 'ethan', ['Azaria'], id={'Azaria': 'azaria-ethan'}),
    K('1kronieken 2:13', 'isai', ['Eliab', 'Abinadab', 'Simea']),
    K('1kronieken 2:14', 'isai', ['Nethaneël', 'Raddai']),
    K('1kronieken 2:15', 'isai', ['Ozem', 'David']),
    K('1kronieken 2:16', 'isai', ['Zeruja', 'Abigaïl'], vrouwen=['Zeruja', 'Abigaïl']),
    K('1kronieken 2:16', 'zeruja', ['Abisai', 'Joab', 'Asa-El']),
    K('1kronieken 2:17', 'abigail', ['Amasa']),

    # De twaalf stammen nog eens opgesomd — levert extra vindplaatsen op.
    K('1kronieken 2:1', 'jakob', ['Ruben', 'Simeon', 'Levi', 'Juda', 'Issaschar', 'Zebulon']),
    K('1kronieken 2:2', 'jakob', ['Dan', 'Jozef', 'Benjamin', 'Nafthali', 'Gad', 'Aser']),

    # === 1 Kronieken 3 — het huis van David ===
    K('1kronieken 3:1', 'david', ['Amnon', 'Daniël']),
    K('1kronieken 3:2', 'david', ['Absalom', 'Adonia']),
    K('1kronieken 3:3', 'david', ['Sefatja', 'Jithream']),
    K('1kronieken 3:5', 'david', ['Simea', 'Sobab', 'Nathan', 'Salomo'], id={'Simea': 'simea-david'}),
    K('1kronieken 3:6', 'david', ['Jibchar', 'Elisama', 'Elifelet']),
    K('1kronieken 3:7', 'david', ['Nogah', 'Nefeg', 'Jafia'], id={'Nefeg': 'nefeg-david'}),
    K('1kronieken 3:8', 'david', ['Elisama', 'Eljada', 'Elifelet'],
      id={'Elisama': 'elisama-2', 'Elifelet': 'elifelet-2'}),
    K('1kronieken 3:9', 'david', ['Thamar'], vrouwen=['Thamar'], id={'Thamar': 'thamar-david'}),
    K('1kronieken 3:10', 'salomo', ['Rehabeam']),
    K('1kronieken 3:10', 'rehabeam', ['Abia']),
    K('1kronieken 3:10', 'abia', ['Asa']),
    K('1kronieken 3:10', 'asa', ['Josafat']),
    K('1kronieken 3:11', 'josafat', ['Joram']),
    K('1kronieken 3:11', 'joram', ['Ahazia']),
    K('1kronieken 3:11', 'ahazia', ['Joas']),
    K('1kronieken 3:12', 'joas', ['Amazia']),
    K('1kronieken 3:12', 'amazia', ['Azaria'], id={'Azaria': 'azaria-amazia'}),
    K('1kronieken 3:12', 'azaria-amazia', ['Jotham']),
    K('1kronieken 3:13', 'jotham', ['Achaz']),
    K('1kronieken 3:13', 'achaz', ['Hizkia']),
    K('1kronieken 3:13', 'hizkia', ['Manasse'], id={'Manasse': 'manasse-hizkia'}),
    K('1kronieken 3:14', 'manasse-hizkia', ['Amon']),
    K('1kronieken 3:14', 'amon', ['Josia']),
    K('1kronieken 3:15', 'josia', ['Johanan', 'Jojakim', 'Zedekia', 'Sallum']),
    K('1kronieken 3:16', 'jojakim', ['Jechonia', 'Zedekia'], id={'Zedekia': 'zedekia-jojakim'}),
    K('1kronieken 3:17', 'jechonia', ['Assir', 'Sealthiël'], id={'Assir': 'assir-jechonia'}),
    K('1kronieken 3:18', 'jechonia', ['Malchiram', 'Pedaja', 'Senazar', 'Jekamja', 'Hosama', 'Nedabja']),
    K('1kronieken 3:19', 'pedaja', ['Zerubbabel', 'Simeï'], id={'Simeï': 'simei-pedaja'}),
    K('1kronieken 3:19', 'zerubbabel', ['Mesullam', 'Hananja', 'Selomith'], vrouwen=['Selomith']),
    K('1kronieken 3:20', 'zerubbabel', ['Hasuba', 'Ohel', 'Berechja', 'Hasadja', 'Jusabhesed']),
    K('1kronieken 3:21', 'hananja', ['Pelatja', 'Jesaja']),

    # === Mattheüs 1 — van Zerubbabel tot Jozef en Jezus ===
    K('mattheus 1:13', 'zerubbabel', ['Abiud']),
    K('mattheus 1:13', 'abiud', ['Eljakim']),
    K('mattheus 1:13', 'eljakim', ['Azor']),
    K('mattheus 1:14', 'azor', ['Sadok']),
    K('mattheus 1:14', 'sadok', ['Achim']),
    K('mattheus 1:14', 'achim', ['Elihud']),
    K('mattheus 1:15', 'elihud', ['Eleazar'], id={'Eleazar': 'eleazar-elihud'}),
    K('mattheus 1:15', 'eleazar-elihud', ['Matthan']),
    K('mattheus 1:15', 'matthan', ['Jakob'], id={'Jakob': 'jakob-matthan'}),
    K('mattheus 1:16', 'jakob-matthan', ['Jozef'], id={'Jozef': 'jozef-matthan'}),
    P('mattheus 1:16', 'jozef-matthan', ['Maria']),
    K('mattheus 1:16', 'jozef-matthan', ['JEZUS'], moeder='maria', viaMoeder=True,
      id={'JEZUS': 'jezus'}),
]

# Weergavenaam en nevenvormen (naamsverandering of andere spelling in de tekst).
NAAMKEUZE = {
    'abram':               ('Abraham', ['Abram']),
    'sarai':               ('Sara', ['Saraï']),
    'jakob':               ('Jakob', ['Israël']),
    'methusalach':         ('Methusalach', ['Methusalah']),
    'zerah-juda':          ('Zerah', ['Zera']),
    'salma':               ('Salma', ['Salmon']),
    'jezus':               ('Jezus Christus', ['JEZUS']),
    'zerubbabel':          ('Zerubbabel', ['Zorobabel']),
    'izak':                ('Izak', ['Isaak']),
    'nahor-terah':         ('Nahor', []),
    'henoch-jered':        ('Henoch', []),
    'lamech-methusalach':  ('Lamech', []),
}

# Losse vindplaatsen die geen relatie uitdrukken maar wel bij de persoon horen.
EXTRA_VERZEN = {
    'adam':               ['genesis 1:27', 'genesis 2:7', 'genesis 5:5', '1kronieken 1:1'],
    'eva':                ['genesis 3:20'],
    'kain':               ['genesis 4:8', 'genesis 4:16'],
    'abel':               ['genesis 4:4'],
    'seth':               ['genesis 5:8'],
    'henoch-jered':       ['genesis 5:24'],
    'methusalach':        ['genesis 5:27'],
    'noach':              ['genesis 6:9', 'genesis 7:7', 'genesis 9:29'],
    'nimrod':             ['genesis 10:9', 'genesis 10:10'],
    'abram':              ['genesis 12:1', 'genesis 17:5', 'genesis 25:8'],
    'sarai':              ['genesis 17:15', 'genesis 23:2'],
    'lot':                ['genesis 13:11', 'genesis 19:29'],
    'ismael':             ['genesis 16:12', 'genesis 25:17'],
    'izak':               ['genesis 22:2', 'genesis 35:29'],
    'rebekka':            ['genesis 24:67'],
    'ezau':               ['genesis 25:30', 'genesis 36:8'],
    'jakob':              ['genesis 32:28', 'genesis 47:9', 'genesis 49:33'],
    'rachel':             ['genesis 35:19'],
    'jozef':              ['genesis 37:3', 'genesis 41:41', 'genesis 50:26'],
    'juda':               ['genesis 49:10'],
    'levi':               ['exodus 6:15'],
    'mozes':              ['exodus 2:10', 'deuteronomium 34:5'],
    'aaron':              ['exodus 28:1'],
    'mirjam':             ['exodus 15:20'],
    'pinehas':            ['numeri 25:11'],
    'boaz':               ['ruth 2:1'],
    'obed':               ['ruth 4:17'],
    'david':              ['1samuel 16:13', '1kronieken 3:4'],
    'salomo':             ['1koningen 3:12'],
    'zerubbabel':         ['mattheus 1:12'],
    'jozef-matthan':      ['mattheus 1:16'],
    'maria':              ['lukas 1:31'],
    'jezus':              ['mattheus 1:1', 'lukas 3:23'],
}

# Korte toelichting; steeds terug te lezen in de aangehaalde verzen.
OPMERKINGEN = {
    'adam':              'De eerste mens; de stamboom van heel de Bijbel begint bij hem.',
    'eva':               'Zij heet Eva "omdat zij een moeder alle levenden is" (Genesis 3:20).',
    'abel':              'Door zijn broer Kaïn doodgeslagen; hij liet geen nageslacht na.',
    'henoch':            'Zoon van Kaïn — niet te verwarren met Henoch, de zoon van Jered.',
    'henoch-jered':      'Hij wandelde met God en "was niet meer; want God nam hem weg".',
    'methusalach':       'Van hem worden de meeste levensjaren vermeld van alle mensen in de Bijbel.',
    'lamech':            'Zoon van Methusael, uit het geslacht van Kaïn.',
    'lamech-methusalach': 'Vader van Noach, uit het geslacht van Seth.',
    'noach':             'Met hem en zijn drie zonen begint na de vloed het hele mensdom opnieuw.',
    'nimrod':            'De eerste geweldige op de aarde; zijn rijk begon met Babel.',
    'kanaan':            'Stamvader van de Kanaänieten, de bewoners van het beloofde land.',
    'abram':             'Zijn naam werd van Abram in Abraham veranderd (Genesis 17:5).',
    'sarai':             'Haar naam werd van Saraï in Sara veranderd (Genesis 17:15).',
    'lot':               'Neef van Abraham; zijn beide zonen zijn de stamvaders van Moab en Ammon.',
    'ismael':            'Zoon van Hagar; van zijn twaalf zonen stammen twaalf vorsten af.',
    'izak':              'De zoon van de belofte, geboren toen Abraham en Sara oud waren.',
    'jakob':             'Ook Israël genoemd (Genesis 32:28); zijn twaalf zonen worden de twaalf stammen.',
    'ezau':              'Ook Edom genoemd; stamvader van de Edomieten.',
    'juda':              'Uit zijn geslacht komen David en, volgens Mattheüs 1, de Christus.',
    'levi':              'Uit zijn geslacht komen Mozes, Aäron en de priesters.',
    'jozef':             'Onderkoning van Egypte; zijn twee zonen worden zelf tot stammen gerekend.',
    'perez':             'Tweelingzoon van Juda en Thamar; door hem loopt de lijn naar David.',
    'mozes':             'Leidde Israël uit Egypte.',
    'aaron':             'De eerste hogepriester.',
    'david':             'Koning over Israël; met hem begint het koningshuis van Juda.',
    'salomo':            'Zoon van David; bouwer van de tempel.',
    'jechonia':          'Onder hem ging Juda in ballingschap naar Babel.',
    'zerubbabel':        ('1 Kronieken 3:19 noemt hem de zoon van Pedaja; Mattheüs 1:12 leidt hem '
                          'af van Sealthiël. Hier is de lijn van 1 Kronieken aangehouden.'),
    'moab':              'Geboren uit de oudste dochter van Lot (Genesis 19:36-37).',
    'ben-ammi':          'Geboren uit de jongste dochter van Lot (Genesis 19:36,38).',
    'jezus':             ('Mattheüs 1:16 zegt niet dat Jozef Hem verwekte, maar dat Jezus uit Maria '
                          'geboren is; de lijn loopt daarom via Maria.'),
    'thamar':            'Schoondochter van Juda; moeder van Perez en Zerah.',
    'ruth':              'De Moabitische; overgrootmoeder van koning David.',
    'zeruja':            'Haar drie zonen worden in 1 Kronieken 2:16 naar háár genoemd, niet naar hun vader.',
    'amasa':             'Zoon van Abigaïl; zijn vader was Jether, de Ismaëliet (1 Kronieken 2:17).',
    'jesaja':            ('1 Kronieken 3:21-24 gaat verder met Refaja, Arnan, Obadja en Sechanja, '
                          'maar zegt niet wie van wie afstamt; die namen staan hier daarom niet.'),
    'pelatja':           ('1 Kronieken 3:21-24 gaat verder met Refaja, Arnan, Obadja en Sechanja, '
                          'maar zegt niet wie van wie afstamt; die namen staan hier daarom niet.'),
}

MAX_RELATIE_VERZEN = 6     # verzen waaruit de plaats in de boom volgt
MAX_EXTRA_VERZEN = 4       # losse vindplaatsen uit EXTRA_VERZEN

# Ankers op de hoofdlijn: personen die op de stamboompagina altijd een eigen rij
# krijgen. Alles daartussen is een rechte lijn van vader op zoon en wordt tot één
# samengevouwen schakel getekend ("Seth › … › Lamech · 8 generaties"), zodat de
# hele boom in ingeklapte staat op een telefoonscherm past. De keuze is die van
# de scharnierpunten in het verhaal: de eerste mens, de vloed, de aartsvaders,
# de stam waaruit de Christus komt, het koningshuis, de ballingschap en de
# terugkeer.
ANKERS = [
    'adam', 'noach', 'sem', 'abram', 'izak', 'jakob', 'juda', 'david',
    'jechonia', 'zerubbabel', 'jozef-matthan', 'jezus',
]


# ------------------------------------------------------------------- inlezen

_hoofdstuk_cache = {}
_boeknamen = {}


def laad_boeknamen():
    with open(os.path.join(DATA, 'books.json'), encoding='utf-8') as fh:
        for b in json.load(fh)['books']:
            _boeknamen[b['id']] = b['nameDutch']


def laad_hoofdstuk(boek, hoofdstuk):
    sleutel = (boek, hoofdstuk)
    if sleutel not in _hoofdstuk_cache:
        pad = os.path.join(DATA, boek, '%d.json' % hoofdstuk)
        if not os.path.exists(pad):
            _hoofdstuk_cache[sleutel] = {}
        else:
            with open(pad, encoding='utf-8') as fh:
                d = json.load(fh)
            _hoofdstuk_cache[sleutel] = dict(
                (v['number'], v.get('text2026', ''))
                for v in d.get('verses', []) if isinstance(v, dict)
            )
    return _hoofdstuk_cache[sleutel]


def ontleed_ref(ref):
    """'genesis 5:6' -> ('genesis', 5, 6)"""
    boek, rest = ref.rsplit(' ', 1)
    hoofdstuk, vers = rest.split(':')
    return boek.strip(), int(hoofdstuk), int(vers)


def verstekst(ref):
    boek, hoofdstuk, vers = ontleed_ref(ref)
    return laad_hoofdstuk(boek, hoofdstuk).get(vers, '')


# ------------------------------------------------------------------ opbouwen

class Stamboom(object):

    def __init__(self):
        self.personen = {}          # id -> dict
        self.volgorde = []          # ids in aanmaakvolgorde
        self.fouten = []
        self.waarschuwingen = []

    # -- basis

    def nieuw(self, naam, geslacht='m', gedwongen_id=None):
        pid = gedwongen_id or slug(naam)
        if not gedwongen_id:
            n = 2
            while pid in self.personen:
                pid = '%s-%d' % (slug(naam), n)
                n += 1
        p = {
            'id': pid, 'naam': naam, 'ookGenoemd': [], 'geslacht': geslacht,
            'soort': 'volk' if is_volk(naam) else 'persoon',
            'ouder': None, 'vader': None, 'moeder': None, 'partners': [], 'kinderen': [],
            'refs': [], 'extraRefs': [], 'generatie': None, 'opmerking': None, 'viaMoeder': False,
        }
        self.personen[pid] = p
        self.volgorde.append(pid)
        return p

    def ref_toevoegen(self, p, ref):
        if ref and ref not in p['refs']:
            p['refs'].append(ref)

    def naam_toevoegen(self, p, naam):
        if naam != p['naam'] and naam not in p['ookGenoemd']:
            p['ookGenoemd'].append(naam)

    def zoek_op_naam(self, naam):
        treffers = []
        for pid in self.volgorde:
            p = self.personen[pid]
            if p['naam'] == naam or naam in p['ookGenoemd']:
                treffers.append(pid)
        return treffers

    # -- controle

    def controleer_in_vers(self, ref, naam):
        tekst = verstekst(ref)
        if not tekst:
            self.fouten.append('vers bestaat niet: %s' % ref)
            return
        patroon = r'(?<![A-Za-zÀ-ÿ])' + re.escape(naam)
        if not re.search(patroon, tekst):
            self.fouten.append('naam "%s" staat niet in %s: %s' % (naam, ref, tekst[:90]))

    # -- relaties

    def kind_toevoegen(self, ouder_id, naam, ref, opties):
        ouder = self.personen.get(ouder_id)
        if ouder is None:
            self.fouten.append('onbekende ouder "%s" bij %s (%s)' % (ouder_id, naam, ref))
            return None
        self.controleer_in_vers(ref, naam)

        gedwongen = (opties.get('id') or {}).get(naam)
        kind = None
        if gedwongen:
            # Een opgegeven id is bindend: bestaat hij al, dan is het dezelfde
            # persoon; bestaat hij nog niet, dan is het uitdrukkelijk een ander
            # (bv. de twee zonen van David die allebei Elisama heten).
            kind = self.personen.get(gedwongen)
        else:
            for kid in ouder['kinderen']:
                k = self.personen[kid]
                if k['naam'] == naam or naam in k['ookGenoemd']:
                    kind = k
                    break
        if kind is None:
            geslacht = 'v' if naam in (opties.get('vrouwen') or []) else 'm'
            kind = self.nieuw(naam, geslacht, gedwongen)
        else:
            self.naam_toevoegen(kind, naam)

        if kind['id'] == ouder_id:
            self.fouten.append('%s zou zijn eigen ouder zijn (%s)' % (naam, ref))
            return kind
        if kind['ouder'] and kind['ouder'] != ouder_id:
            self.waarschuwingen.append(
                '%s had al ouder %s, nu ook %s (%s)' % (kind['id'], kind['ouder'], ouder_id, ref))
        kind['ouder'] = ouder_id
        if opties.get('viaMoeder'):
            kind['viaMoeder'] = True          # Jezus: Mattheüs 1:16 zegt geen "verwekte"
        elif ouder['geslacht'] == 'v':
            kind['moeder'] = ouder_id         # de tekst noemt hier alleen de moeder
        else:
            kind['vader'] = ouder_id
        if kind['id'] not in ouder['kinderen']:
            ouder['kinderen'].append(kind['id'])

        moeder_id = opties.get('moeder')
        if moeder_id:
            if moeder_id in self.personen:
                kind['moeder'] = moeder_id
            else:
                self.fouten.append('onbekende moeder "%s" bij %s (%s)' % (moeder_id, naam, ref))
        self.ref_toevoegen(kind, ref)
        self.ref_toevoegen(ouder, ref)
        return kind

    def partner_toevoegen(self, persoon_id, naam, ref, opties):
        persoon = self.personen.get(persoon_id)
        if persoon is None:
            self.fouten.append('onbekende persoon "%s" bij partner %s (%s)' % (persoon_id, naam, ref))
            return None
        if naam.startswith('#'):
            partner = self.personen.get(naam[1:])
            if partner is None:
                self.fouten.append('onbekende partner-id "%s" (%s)' % (naam, ref))
                return None
        else:
            self.controleer_in_vers(ref, naam)
            gedwongen = (opties.get('id') or {}).get(naam)
            partner = self.personen.get(gedwongen) if gedwongen else None
            if partner is None:
                partner = self.nieuw(naam, 'v', gedwongen)
        if partner['id'] not in persoon['partners']:
            persoon['partners'].append(partner['id'])
        if persoon_id not in partner['partners']:
            partner['partners'].append(persoon_id)
        self.ref_toevoegen(partner, ref)
        self.ref_toevoegen(persoon, ref)
        return partner

    # -- automatische "X verwekte Y"-ontleding

    NAAM_RE = re.compile(r"[A-ZÉËÏÖÜ][a-zäëïöüéèêáàâç'’]+(?:-[A-ZÉËÏÖÜa-z][a-zäëïöüéèêáàâç'’]*)*")
    VERWEKT_RE = re.compile(r'\bverwekte\b')

    def verwekte_verwerken(self, ref, opties):
        """Leest "X verwekte Y" uit één vers.

        Het onderwerp staat niet altijd vlak voor het werkwoord ("en hij
        verwekte Enos"), dus zoeken we terug naar de laatste eigennaam vóór
        "verwekte". De kinderen staan tussen dit werkwoord en de eigennaam van
        de volgende "verwekte"-zin, of tot het einde van de zin.
        """
        tekst = verstekst(ref)
        if not tekst:
            self.fouten.append('vers bestaat niet: %s' % ref)
            return
        namen = [m for m in self.NAAM_RE.finditer(tekst) if m.group(0) not in NIET_EEN_NAAM]
        treffers = list(self.VERWEKT_RE.finditer(tekst))
        if not treffers:
            self.fouten.append('geen "verwekte" gevonden in %s' % ref)
            return

        def vadernaam_voor(pos):
            kandidaat = None
            for m in namen:
                if m.end() <= pos:
                    kandidaat = m
                else:
                    break
            return kandidaat

        for i, m in enumerate(treffers):
            vm = vadernaam_voor(m.start())
            if vm is None:
                self.fouten.append('geen naam vóór "verwekte" in %s' % ref)
                continue
            volgende = vadernaam_voor(treffers[i + 1].start()) if i + 1 < len(treffers) else None
            eind = volgende.start() if volgende is not None and volgende.start() > m.end() else len(tekst)
            staart = re.split(r'[.;:!?]', tekst[m.end():eind])[0]

            vadernaam = vm.group(0)
            vader_id = (opties.get('ids') or {}).get(vadernaam)
            if not vader_id:
                kandidaten = self.zoek_op_naam(vadernaam)
                if len(kandidaten) == 1:
                    vader_id = kandidaten[0]
                elif not kandidaten:
                    self.fouten.append('vader "%s" onbekend bij %s' % (vadernaam, ref))
                    continue
                else:
                    self.fouten.append('vader "%s" is dubbelzinnig bij %s: %s'
                                       % (vadernaam, ref, kandidaten))
                    continue
            kinderen = []
            for n in self.NAAM_RE.findall(staart):
                if n not in NIET_EEN_NAAM and n not in kinderen:
                    kinderen.append(n)
            if not kinderen:
                self.fouten.append('geen kindnamen gevonden na "verwekte" in %s' % ref)
            for naam in kinderen:
                self.kind_toevoegen(vader_id, naam, ref, opties)

    # -- afronden

    def generaties_bepalen(self, wortel):
        rij = [(wortel, 0)]
        gezien = set()
        while rij:
            pid, g = rij.pop(0)
            if pid in gezien:
                continue
            gezien.add(pid)
            p = self.personen[pid]
            p['generatie'] = g
            for kid in p['kinderen']:
                rij.append((kid, g + 1))
        # Partners krijgen de generatie van hun man.
        for pid in self.volgorde:
            p = self.personen[pid]
            if p['generatie'] is None:
                for q in p['partners']:
                    if self.personen[q]['generatie'] is not None:
                        p['generatie'] = self.personen[q]['generatie']
                        break
        return gezien

    def cycli_zoeken(self):
        kleur = {}

        def loop(pid, pad):
            kleur[pid] = 1
            for kid in self.personen[pid]['kinderen']:
                if kleur.get(kid) == 1:
                    self.fouten.append('kringloop in de stamboom: %s' % ' > '.join(pad + [kid]))
                elif kleur.get(kid) is None:
                    loop(kid, pad + [kid])
            kleur[pid] = 2

        for pid in self.volgorde:
            if kleur.get(pid) is None:
                loop(pid, [pid])


NIET_EEN_NAAM = set(['En', 'De', 'Deze', 'Dit', 'Toen', 'Want', 'Zo', 'Maar', 'Al', 'Alle',
                     'Daarna', 'Verder', 'Hij', 'Zij', 'Ook', 'Nu', 'Van', 'Die', 'Het'])


# ----------------------------------------------------------------------- main

def main():
    laad_boeknamen()
    sb = Stamboom()
    sb.nieuw('Adam', 'm', 'adam')
    sb.personen['adam']['refs'].append('genesis 5:1')

    for bron in BRONNEN:
        if bron.soort == 'kind':
            for naam in bron.namen:
                sb.kind_toevoegen(bron.ouder, naam, bron.ref, bron.opties)
        elif bron.soort == 'partner':
            for naam in bron.namen:
                sb.partner_toevoegen(bron.ouder, naam, bron.ref, bron.opties)
        else:
            sb.verwekte_verwerken(bron.ref, bron.opties)

    # Weergavenamen en nevenvormen
    for pid, (weergave, ook) in NAAMKEUZE.items():
        p = sb.personen.get(pid)
        if p is None:
            sb.fouten.append('NAAMKEUZE verwijst naar onbekende id "%s"' % pid)
            continue
        if p['naam'] != weergave:
            sb.naam_toevoegen(p, p['naam'])
            p['naam'] = weergave
        for naam in ook:
            sb.naam_toevoegen(p, naam)

    for pid, refs in EXTRA_VERZEN.items():
        p = sb.personen.get(pid)
        if p is None:
            sb.fouten.append('EXTRA_VERZEN verwijst naar onbekende id "%s"' % pid)
            continue
        for ref in refs:
            if not verstekst(ref):
                sb.fouten.append('EXTRA_VERZEN: vers bestaat niet (%s bij %s)' % (ref, pid))
                continue
            if ref not in p['refs'] and ref not in p['extraRefs']:
                p['extraRefs'].append(ref)

    for pid, tekst in OPMERKINGEN.items():
        p = sb.personen.get(pid)
        if p is None:
            sb.fouten.append('OPMERKINGEN verwijst naar onbekende id "%s"' % pid)
            continue
        p['opmerking'] = tekst

    sb.cycli_zoeken()
    bereikbaar = sb.generaties_bepalen('adam')

    # Hoofdlijn Adam → Jezus markeren; de pagina toont die bij het openen.
    pid = 'jezus'
    while pid:
        sb.personen[pid]['hoofdlijn'] = True
        pid = sb.personen[pid]['ouder']

    for pid in ANKERS:
        if pid not in sb.personen:
            sb.fouten.append('ANKERS verwijst naar onbekende id "%s"' % pid)
        elif not sb.personen[pid].get('hoofdlijn'):
            sb.fouten.append('anker "%s" ligt niet op de hoofdlijn' % pid)
        else:
            sb.personen[pid]['anker'] = True
    los = [pid for pid in sb.volgorde
           if pid not in bereikbaar and not sb.personen[pid]['partners']]
    for pid in los:
        sb.waarschuwingen.append('niet verbonden met Adam: %s' % pid)

    # Verzen materialiseren
    for pid in sb.volgorde:
        p = sb.personen[pid]
        verzen = []
        alle = p['refs'][:MAX_RELATIE_VERZEN] + p['extraRefs'][:MAX_EXTRA_VERZEN]
        for ref in alle:
            boek, hoofdstuk, vers = ontleed_ref(ref)
            tekst = verstekst(ref)
            if not tekst:
                continue
            verzen.append({
                'boek': boek,
                'boekNaam': _boeknamen.get(boek, boek.capitalize()),
                'hoofdstuk': hoofdstuk,
                'vers': vers,
                'tekst': tekst,
            })
        p['verzen'] = verzen
        del p['refs']
        del p['extraRefs']
        # lege velden weglaten — scheelt een derde van de bestandsgrootte
        p['ookGenoemd'] = [n for n in p['ookGenoemd'] if n != p['naam']]
        for veld in ('ookGenoemd', 'partners', 'kinderen'):
            if not p[veld]:
                del p[veld]
        for veld in ('ouder', 'vader', 'moeder', 'opmerking'):
            if p[veld] is None:
                del p[veld]
        if not p['viaMoeder']:
            del p['viaMoeder']
        if p['soort'] == 'persoon':
            del p['soort']

    if sb.fouten:
        sys.stderr.write('\n== FOUTEN ==\n')
        for f in sb.fouten:
            sys.stderr.write(' - %s\n' % f)
        sys.stderr.write('\nBuild afgebroken: %d fout(en).\n' % len(sb.fouten))
        return 1

    for w in sb.waarschuwingen:
        print('let op: %s' % w)

    generaties = max(p['generatie'] for p in sb.personen.values() if p['generatie'] is not None)
    uitvoer = {
        '_over': ('Stamboom van Adam tot Jozef en Jezus, afgeleid uit de tekst van de Open '
                  'Vertaling (text2026). Elke relatie verwijst naar het vers waaruit hij komt. '
                  'Gegenereerd door scripts/build_stamboom.py — niet met de hand bijwerken.'),
        '_bronnen': ('Genesis 4, 5, 9, 10, 11, 16, 19, 21, 22, 24, 25, 29, 30, 35, 36, 38, 41, 46; '
                     'Exodus 6; Numeri 26; Ruth 4; 1 Kronieken 2, 3; Mattheüs 1.'),
        '_zonderJaartallen': True,
        'wortel': 'adam',
        'aantalPersonen': len(sb.personen),
        'aantalGeneraties': generaties + 1,
        'personen': sb.personen,
    }
    with open(UIT, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(uitvoer, fh, ensure_ascii=False, indent=1, sort_keys=False)
        fh.write('\n')

    print('data/stamboom.json geschreven: %d personen, %d generaties (%.0f kB)'
          % (len(sb.personen), generaties + 1, os.path.getsize(UIT) / 1024.0))
    return 0


if __name__ == '__main__':
    sys.exit(main())
