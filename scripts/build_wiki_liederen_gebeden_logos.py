"""Bouw subtiele cinemagraphs van de handgetekende wiki-illustraties."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "images" / "wiki"
SOURCE_DIR = OUTPUT_DIR / "bronnen"
WIDTH = 600
HEIGHT = 300
FRAME_COUNT = 50
FRAME_DURATION_MS = 100


def source_image(name: str) -> Image.Image:
    """Open de gegenereerde illustratie en lever het vaste tegelkader."""
    with Image.open(SOURCE_DIR / f"{name}.webp") as source:
        return source.convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def draw_liederen(base: Image.Image, phase: float) -> Image.Image:
    """Laat een heel zachte ochtendgloed en snaarglans door de scène lopen."""
    image = base.convert("RGBA")

    ochtendlicht = Image.new("RGBA", image.size, (0, 0, 0, 0))
    light_draw = ImageDraw.Draw(ochtendlicht)
    pulse = (math.sin(phase) + 1) / 2
    light_draw.ellipse(
        (22, 151, 188, 248),
        fill=(232, 190, 79, round(3 + 7 * pulse)),
    )
    ochtendlicht = ochtendlicht.filter(ImageFilter.GaussianBlur(28))
    image = Image.alpha_composite(image, ochtendlicht)

    glans = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glans)

    for index, x in enumerate((312, 317, 322, 327, 332, 337, 342, 347)):
        golf = (math.sin(phase - index * 0.7) + 1) / 2
        alpha = round(3 + 18 * golf)
        draw.line((x, 82, x, 165), fill=(214, 176, 80, alpha), width=1)
        if golf > 0.82:
            y = round(91 + 60 * ((index + phase / (2 * math.pi)) % 8) / 8)
            draw.ellipse((x - 2, y - 3, x + 2, y + 3), fill=(239, 211, 133, 16))

    glans = glans.filter(ImageFilter.GaussianBlur(0.45))
    return Image.alpha_composite(image, glans).convert("RGB")


def draw_gebeden(base: Image.Image, phase: float) -> Image.Image:
    """Laat alleen het zachte ochtendlicht bijna onmerkbaar ademen."""
    image = base.convert("RGBA")
    gloed = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(gloed)
    pulse = (math.sin(phase) + 1) / 2
    drift = (math.cos(phase) + 1) / 2
    glow_draw.ellipse(
        (18, 122, 236, 254),
        fill=(235, 192, 80, round(2 + 19 * pulse)),
    )
    glow_draw.ellipse(
        (70, 145, 258, 266),
        fill=(224, 173, 63, round(2 + 17 * drift)),
    )
    gloed = gloed.filter(ImageFilter.GaussianBlur(35))
    return Image.alpha_composite(image, gloed).convert("RGB")


def save_animation(name: str, renderer) -> Path:
    base = source_image(name)
    frames = [
        renderer(base, 2 * math.pi * index / FRAME_COUNT)
        for index in range(FRAME_COUNT)
    ]
    output = OUTPUT_DIR / f"{name}.webp"
    frames[0].save(
        output,
        format="WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        lossless=True,
        method=6,
    )
    return output


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, renderer in (("liederen", draw_liederen), ("gebeden", draw_gebeden)):
        output = save_animation(name, renderer)
        with Image.open(output) as animation:
            print(
                f"{output.relative_to(ROOT)}: {animation.size}, "
                f"{animation.n_frames} frames, {FRAME_COUNT * FRAME_DURATION_MS} ms"
            )


if __name__ == "__main__":
    main()
