#!/usr/bin/env python3
"""Koppel de gepubliceerde materiaalillustraties en korte toelichtingen.

De gegevens vormen de bron voor zowel de overzichtskaarten als de aparte
materiaalpagina's. Dit script houdt die metadata reproduceerbaar bij.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "naslag-materialen.json"

DESCRIPTIONS = {
    "tin": "Tin is een zacht, zilvergrijs metaal dat in de Bijbel onder meer bij handel en metaalbewerking wordt genoemd.",
    "lood": "Lood is een zwaar, buigzaam metaal dat beeldend wordt gebruikt voor gewicht en zinken in diep water.",
    "staal": "Staal is gehard ijzer; het woord duidt in de Bijbel op krachtig metaal voor wapens en werktuigen.",
    "steen": "Steen is bouwmateriaal, grenssteen en beeld voor stevigheid; de Bijbel noemt ook vele kostbare steensoorten.",
    "marmer": "Marmer is hard natuursteen met een glad te polijsten oppervlak, geschikt voor kostbare gebouwen en versiering.",
    "albast": "Albast is een licht, fijnkorrelig gesteente dat vaak tot kostbare kruiken en zalfflessen werd bewerkt.",
    "kristal": "Kristal is helder mineraal of glasachtig gesteente en wordt in de Bijbel gebruikt als beeld van schitterende zuiverheid.",
    "glas": "Glas is een doorzichtig, door verhitting gevormd materiaal; in Openbaring verschijnt het als beeld van glans.",
    "ivoor": "Ivoor is het harde, roomkleurige materiaal uit slagtanden en gold in de oudheid als kostbare luxegrondstof.",
    "parel": "Parels ontstaan in schelpen en behoren in de Bijbel tot de kostbare sieraden en beelden van grote waarde.",
    "saffier": "Saffier is een kostbare blauwe edelsteen die in de Bijbel verbonden wordt met pracht en hemelse luister.",
    "smaragd": "Smaragd is een groene edelsteen die in de Bijbel voorkomt tussen de kostbare stenen van priesterlijk en hemels sieraad.",
    "diamant": "Diamant is een uiterst hard edelgesteente; de bijbelse steennaam kan ook een andere zeer harde steen aanduiden.",
    "robijn": "Robijn is een rode edelsteen die als beeld van uitzonderlijke kostbaarheid wordt gebruikt.",
    "topaas": "Topaas is een heldere edelsteen die in de Bijbel onder de stenen van de borsttas en het nieuwe Jeruzalem staat.",
    "karbonkel": "Karbonkel is een traditionele naam voor een rood glanzende edelsteen, waarschijnlijk verwant aan granaat.",
    "agaat": "Agaat is een gelaagde variëteit van kwarts die in de oudheid voor sieraden en zegelstenen werd gebruikt.",
    "amethist": "Amethist is een paarsgekleurde variëteit van kwarts en behoort tot de kostbare stenen die de Bijbel noemt.",
    "jaspis": "Jaspis is een ondoorzichtige, vaak veelkleurige kwartssteen die in Openbaring de glans van Gods heerlijkheid tekent.",
    "chrysoliet": "Chrysoliet is een geelgroene edelsteennaam uit de oudheid, genoemd onder de sierstenen van het nieuwe Jeruzalem.",
    "chalcedon": "Chalcedon is een fijne, doorschijnende kwartsvariëteit die in Openbaring onder de fundamentstenen wordt genoemd.",
    "sardius": "Sardius is een roodbruine edelsteen, ook wel carneool genoemd, die tot de kostbare priesterlijke stenen behoort.",
    "hyacint": "Hyacint is een traditionele naam voor een blauwviolette of roodachtige edelsteen uit de opsomming van Openbaring.",
    "cederhout": "Cederhout is geurig, duurzaam naaldhout en was geliefd voor paleizen, tempelbouw en kostbare betimmering.",
    "sittimhout": "Sittimhout is acaciahout: hard woestijnhout dat voor de tabernakel en zijn gerei werd gebruikt.",
    "ebbenhout": "Ebbenhout is zeer donker, dicht en hard hout dat in de oudheid als luxe handelswaar werd verhandeld.",
    "wol": "Wol is de vezel van schapen en geiten, gebruikt voor kleding, weefsel en offers.",
    "vlas": "Vlas levert lange vezels voor linnen en was een belangrijk gewas voor kleding en weefwerk.",
    "linnen": "Linnen is geweven vlasvezel en staat in de Bijbel voor fijne kleding, priesterdienst en reinheid.",
    "geitenhaar": "Geitenhaar is een sterke, donkere vezel die voor tentdoek en de bedekking van de tabernakel werd gebruikt.",
    "huiden": "Huiden van dieren werden gelooid of geverfd en dienden onder meer voor tentbedekking en gebruiksvoorwerpen.",
    "leer": "Leer is gelooide dierenhuid, een duurzaam materiaal voor riemen, sandalen, zakken en tentbenodigdheden.",
    "klei": "Klei is kneedbare aarde die voor potten, bakstenen en beelden wordt gebruikt en vaak beeld is van de mens in Gods hand.",
    "kalk": "Kalk is gebrand gesteente dat als witkalk en bindmiddel bij bouw en opschrift werd gebruikt.",
    "perkament": "Perkament is zorgvuldig bereide dierenhuid waarop duurzame rollen, brieven en boeken konden worden geschreven.",
    "inkt": "Inkt is een donkere schrijfstof voor rollen en brieven, in de Bijbel genoemd bij het vastleggen en verbranden van woorden.",
    "wierook": "Wierook is aromatische hars die bij verbranding geur verspreidt en in de eredienst een vaste plaats heeft.",
    "nardus": "Nardus is kostbare, sterk geurende olie uit een plantwortel, gebruikt voor zalving en gastvrijheid.",
    "kaneel": "Kaneel is geurige schors die aan zalfolie en reukwerk werd toegevoegd en als kostbare handelswaar gold.",
    "galbanum": "Galbanum is een sterk geurende hars die volgens Exodus deel uitmaakte van het heilige reukwerk.",
    "purper": "Purper is kostbare roodpaarse kleurstof en stof, verbonden met koninklijke waardigheid en rijkdom.",
    "scharlaken": "Scharlaken is helder rode kleurstof en draad, gebruikt in stoffen, priesterlijke voorwerpen en symbolische reiniging.",
    "karmozijn": "Karmozijn is diepe rode kleurstof, gewonnen uit schildluizen, en werd gebruikt voor kostbare textiel.",
    "zout": "Zout bewaart voedsel, geeft smaak en wordt in de Bijbel ook gebruikt als beeld van verbond en trouw.",
    "zwavel": "Zwavel is een geel mineraal dat brandt met scherpe rook en in de Bijbel vaak met oordeel verbonden is.",
    "kolen": "Kolen zijn gloeiende of brandende stukken hout en worden gebruikt bij vuur, reiniging en beeldspraak.",
    "as": "As is het restant van verbrand materiaal en drukt in de Bijbel rouw, vernedering en vergankelijkheid uit.",
}


def enrich(data: dict) -> dict:
    """Voeg de gepubliceerde beeld- en toelichtingsmetadata toe aan een dataset."""
    for item in data["items"]:
        item_id = item["id"]
        item["afbeelding"] = f"images/wiki/materialen/{item_id}.webp"
        if item_id in DESCRIPTIONS:
            item["beschrijving"] = DESCRIPTIONS[item_id]
    return data


def main() -> None:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    enrich(data)
    SOURCE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
