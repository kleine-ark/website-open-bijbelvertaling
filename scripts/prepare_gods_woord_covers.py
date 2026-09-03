"""Kopieer en splits de gegenereerde omslagen voor Gods Woord.

Van elk ontwerp staat de volledige omslag in de repository; de losse achterkant,
rug en voorkant worden hier uit gesneden en niet meegecommit -- drie afgeleide
bestanden per variant wegen samen ruim dertig megabyte en zijn in een seconde
opnieuw te maken.

Is de map met de oorspronkelijk gegenereerde beelden er nog, dan wordt daaruit
gekopieerd; anders dient de al aanwezige volledige-omslag.png als bron. Zo blijft
het script werken op een machine die de generatiemap niet heeft.

Vereist Pillow. Uitvoeren vanuit de repositoryroot:
    python scripts/prepare_gods_woord_covers.py
"""

from pathlib import Path
from shutil import copy2

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SOURCE = Path(
    r"C:\Users\rickd\.codex\generated_images"
    r"\019ff74d-645e-70a3-9425-53e277d4e05f"
)
DESTINATION = REPO / "images" / "covers" / "gods-woord"

# (bestandsnaam, bronbestand, x-einde achterkant, x-begin voorkant)
# De ruimte tussen de twee x-coordinaten is de rug.
COVERS = (
    ("01-klassiek-met-tekst", "exec-b8aba590-df3b-457e-bef4-ea05904beba0.png", 694, 828),
    ("01-klassiek-zonder-tekst", "exec-b51cbbe4-e6e1-43f7-b482-54c0e17fe1f6.png", 675, 846),
    ("02-paradijstuin-met-tekst", "exec-9e74c17b-4892-41ea-b15d-d75a73978150.png", 694, 841),
    ("02-paradijstuin-zonder-tekst", "exec-c5c46870-7da9-4954-953e-086384353c77.png", 704, 823),
    ("03-bergen-regenboog-met-tekst", "exec-5f187160-d0c7-4fad-9592-27713d57ba2f.png", 682, 835),
    ("03-bergen-regenboog-zonder-tekst", "exec-c283fc66-f4c1-4623-9a05-d73332373e61.png", 707, 836),
    ("04-rivier-zonsopkomst-met-tekst", "exec-2283de74-fba0-400b-9b59-92443879bacc.png", 671, 838),
    ("04-rivier-zonsopkomst-zonder-tekst", "exec-28f7c685-a07b-40ce-8198-0b37158c266a.png", 690, 833),
    ("05-bloemenweide-met-tekst", "exec-229451fe-ae24-4c94-b917-ad54919d02bd.png", 685, 842),
    ("05-bloemenweide-zonder-tekst", "exec-ef779087-db16-4282-9637-53bdb0158780.png", 703, 837),
    ("06-sober-nachtblauw-met-tekst", "exec-9ac6ddc5-b2c3-424d-8886-30aac2d4f5ad.png", 717, 835),
    ("06-sober-nachtblauw-zonder-tekst", "exec-99378a63-5a4f-40dc-801e-c37c3dc13665.png", 717, 835),
)


def main() -> None:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    missing: list[Path] = []

    for name, source_name, back_end, front_start in COVERS:
        cover_dir = DESTINATION / name
        source = SOURCE / source_name
        if source.exists():
            cover_dir.mkdir(parents=True, exist_ok=True)
            copy2(source, cover_dir / "volledige-omslag.png")
        else:
            source = cover_dir / "volledige-omslag.png"
            if not source.exists():
                missing.append(source)
                continue

        with Image.open(source) as image:
            width, height = image.size
            if width != 1536 or height != 1024:
                raise ValueError(f"Onverwacht formaat voor {source}: {image.size}")
            image.crop((0, 0, back_end, height)).save(cover_dir / "achterkant.png")
            image.crop((back_end, 0, front_start, height)).save(cover_dir / "rug.png")
            image.crop((front_start, 0, width, height)).save(cover_dir / "voorkant.png")

    if missing:
        paths = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Ontbrekende bronbestanden:\n{paths}")

    print(f"Gereed: {len(COVERS)} omslagen in {DESTINATION}")


if __name__ == "__main__":
    main()
