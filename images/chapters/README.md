# Hoofdstuk-illustraties (AI-generated)

Hier komen per-hoofdstuk illustraties (ai-generated, te genereren met
bijvoorbeeld Nano Banana, DALL-E, Midjourney of Stable Diffusion).

## Bestandsnamen

Bestandsnamen volgen het patroon `{bookId}_{chapter}.jpg` — bijvoorbeeld:

- `genesis_1.jpg`
- `markus_5.jpg`
- `psalmen_23.jpg`
- `openbaring_22.jpg`

De `bookId` komt overeen met het `id`-veld in `data/books.json` (kleine
letters, geen spaties, bijvoorbeeld `1korinthiers`, `boekderwijsheid`,
`estherapocrief`).

## Prompts

De prompts die zijn gebruikt om deze afbeeldingen te genereren staan
in `data/chapter-image-prompts.json`. Per hoofdstuk bevat dat bestand:

- `book` — boek-id
- `chapter` — hoofdstuknummer
- `title_nl` — Nederlandse titel ("Genesis 1")
- `subject` — korte beschrijving van het hoofdthema
- `prompt` — visueel prompt voor image-generation
- `style` — stijl-suffix (oude meester / oil painting / etc.)

## Stijl-richtlijnen

- Oude meester schilderkunst (Rembrandt / Caravaggio / Pre-Raphaeliet)
- Warme tonen, dramatisch licht
- Geen tekst in de afbeelding ("no text, no captions")
- Historisch correcte kleding (1e-eeuws / OT-gewaden)
- Semitisch / Midden-Oosters uiterlijk; geen Westerse stereotypes
- Compositie focust op het kern-moment of -beeld van het hoofdstuk
