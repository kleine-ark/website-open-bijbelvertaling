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
    """Laat alleen een heel zachte lichttrilling over de liersnaren lopen."""
    image = base.convert("RGBA")
    glans = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glans)

    for index, x in enumerate((276, 283, 290, 297, 304, 311, 318, 325)):
        golf = (math.sin(phase - index * 0.7) + 1) / 2
        alpha = round(4 + 25 * golf)
        draw.line((x, 74, x, 205), fill=(214, 176, 80, alpha), width=1)
        if golf > 0.82:
            y = round(90 + 96 * ((index + phase / (2 * math.pi)) % 8) / 8)
            draw.ellipse((x - 2, y - 3, x + 2, y + 3), fill=(239, 211, 133, 16))

    glans = glans.filter(ImageFilter.GaussianBlur(0.45))
    return Image.alpha_composite(image, glans).convert("RGB")


def smoke_line(
    x: float,
    bottom: float,
    top: float,
    phase: float,
    offset: float,
    amplitude: float,
) -> list[tuple[float, float]]:
    points = []
    for step in range(45):
        ratio = step / 44
        y = bottom + (top - bottom) * ratio
        drift = amplitude * math.sin(ratio * math.pi * 2.7 + phase + offset)
        points.append((x + drift * (0.35 + ratio * 0.65), y))
    return points


def draw_gebeden(base: Image.Image, phase: float) -> Image.Image:
    """Laat de rook bijna onmerkbaar drijven en de kolen zacht ademen."""
    image = base.convert("RGBA")

    gloed = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(gloed)
    pulse = (math.sin(phase) + 1) / 2
    for x in (293, 302, 311):
        radius = 4.5 + pulse
        glow_draw.ellipse(
            (x - radius, 170 - radius, x + radius, 170 + radius),
            fill=(214, 157, 54, round(8 + 15 * pulse)),
        )
    gloed = gloed.filter(ImageFilter.GaussianBlur(4.2))
    image = Image.alpha_composite(image, gloed)

    rook = Image.new("RGBA", image.size, (0, 0, 0, 0))
    smoke_draw = ImageDraw.Draw(rook)
    specs = (
        (286, 164, 55, 0.0, 4.0, 17),
        (304, 164, 45, 1.9, 3.4, 14),
        (320, 163, 70, 3.7, 3.1, 12),
    )
    for x, bottom, top, offset, amplitude, alpha in specs:
        smoke_draw.line(
            smoke_line(x, bottom, top, phase, offset, amplitude),
            fill=(89, 117, 116, alpha),
            width=2,
            joint="curve",
        )
    rook = rook.filter(ImageFilter.GaussianBlur(1.1))
    return Image.alpha_composite(image, rook).convert("RGB")


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
