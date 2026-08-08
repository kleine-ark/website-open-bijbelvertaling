"""Bouw de subtiele cinemagraphs voor de wiki-tegels Liederen en Gebeden."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "images" / "wiki"
WIDTH = 600
HEIGHT = 300
SCALE = 3
FRAME_COUNT = 50
FRAME_DURATION_MS = 100

NAVY = "#142e42"
GOLD = "#cba449"
TEAL = "#4a7c7a"
PAPER = "#faf7ef"


def point(x: float, y: float) -> tuple[int, int]:
    return round(x * SCALE), round(y * SCALE)


def width(value: float) -> int:
    return max(1, round(value * SCALE))


def cubic(
    start: tuple[float, float],
    control_a: tuple[float, float],
    control_b: tuple[float, float],
    end: tuple[float, float],
    steps: int = 36,
) -> list[tuple[int, int]]:
    result = []
    for index in range(steps + 1):
        t = index / steps
        u = 1 - t
        x = (
            u**3 * start[0]
            + 3 * u**2 * t * control_a[0]
            + 3 * u * t**2 * control_b[0]
            + t**3 * end[0]
        )
        y = (
            u**3 * start[1]
            + 3 * u**2 * t * control_a[1]
            + 3 * u * t**2 * control_b[1]
            + t**3 * end[1]
        )
        result.append(point(x, y))
    return result


def background() -> Image.Image:
    top = (250, 247, 239)
    bottom = (239, 231, 212)
    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), top)
    draw = ImageDraw.Draw(image)
    for y in range(HEIGHT * SCALE):
        ratio = y / (HEIGHT * SCALE - 1)
        color = tuple(round(a + (b - a) * ratio) for a, b in zip(top, bottom))
        draw.line((0, y, WIDTH * SCALE, y), fill=color)
    return image


def draw_rotated_ellipse(
    image: Image.Image,
    center: tuple[float, float],
    radii: tuple[float, float],
    angle: float,
    color: str,
) -> None:
    rx, ry = radii
    margin = 3
    layer = Image.new(
        "RGBA",
        (width((rx + margin) * 2), width((ry + margin) * 2)),
        (0, 0, 0, 0),
    )
    layer_draw = ImageDraw.Draw(layer)
    layer_draw.ellipse(
        (
            width(margin),
            width(margin),
            width(margin + rx * 2),
            width(margin + ry * 2),
        ),
        fill=color,
    )
    layer = layer.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    target = point(center[0], center[1])
    image.alpha_composite(
        layer,
        (target[0] - layer.width // 2, target[1] - layer.height // 2),
    )


def draw_liederen(phase: float) -> Image.Image:
    image = background().convert("RGBA")
    draw = ImageDraw.Draw(image)

    bowl = cubic((248, 160), (248, 216), (352, 216), (352, 160))
    bowl.extend([point(352, 148), point(248, 148)])
    draw.polygon(bowl, fill=PAPER)
    draw.line(bowl + [bowl[0]], fill=NAVY, width=width(5), joint="curve")

    draw.line(
        cubic((252, 150), (238, 118), (236, 94), (246, 72)),
        fill=NAVY,
        width=width(5),
        joint="curve",
    )
    draw.line(
        cubic((348, 150), (362, 118), (364, 94), (354, 72)),
        fill=NAVY,
        width=width(5),
        joint="curve",
    )
    draw.line((point(243, 72), point(357, 72)), fill=GOLD, width=width(6))
    draw.ellipse((point(237, 66), point(249, 78)), fill=GOLD)
    draw.ellipse((point(351, 66), point(363, 78)), fill=GOLD)

    string_ends = ((272, 196), (286, 201), (300, 203), (314, 201), (328, 196))
    for index, (x, bottom_y) in enumerate(string_ends):
        vibration = 1.15 * math.sin(phase + index * 0.62)
        points = []
        for step in range(25):
            ratio = step / 24
            y = 78 + (bottom_y - 78) * ratio
            offset = vibration * math.sin(math.pi * ratio)
            points.append(point(x + offset, y))
        draw.line(points, fill=TEAL, width=width(3.5))

    note_shift = 2.4 * math.sin(phase)
    draw_rotated_ellipse(image, (428, 120 + note_shift), (9, 7), 20, NAVY)
    draw.line(
        (point(435, 119 + note_shift), point(435, 64 + note_shift)),
        fill=NAVY,
        width=width(4),
    )
    draw_rotated_ellipse(image, (465, 112 - note_shift * 0.65), (9, 7), 20, NAVY)
    draw.line(
        (point(472, 111 - note_shift * 0.65), point(472, 56 - note_shift * 0.65)),
        fill=NAVY,
        width=width(4),
    )
    draw.polygon(
        (
            point(435, 64 + note_shift),
            point(472, 56 - note_shift * 0.65),
            point(472, 70 - note_shift * 0.65),
            point(435, 78 + note_shift),
        ),
        fill=NAVY,
    )

    return image.convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def smoke_path(
    phase: float,
    x: float,
    bottom_y: float,
    top_y: float,
    amplitude: float,
    offset: float,
) -> list[tuple[int, int]]:
    points = []
    for step in range(49):
        ratio = step / 48
        y = bottom_y + (top_y - bottom_y) * ratio
        wave = amplitude * math.sin(ratio * math.pi * 3.2 + phase + offset)
        taper = 0.35 + ratio * 0.65
        points.append(point(x + wave * taper, y))
    return points


def draw_gebeden(phase: float) -> Image.Image:
    image = background().convert("RGBA")

    glow_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow = ImageDraw.Draw(glow_layer)
    pulse = (math.sin(phase) + 1) / 2
    for x, y, radius in ((277, 193, 7), (300, 189, 8), (323, 193, 7)):
        outer = radius + 8 + pulse * 2
        glow.ellipse(
            (point(x - outer, y - outer), point(x + outer, y + outer)),
            fill=(203, 164, 73, round(16 + 15 * pulse)),
        )
    image = Image.alpha_composite(image, glow_layer)
    draw = ImageDraw.Draw(image)

    smoke_specs = (
        (300, 172, 44, 16, 0.0, 5, 0.80),
        (258, 176, 120, 9, 1.8, 5, 0.48),
        (342, 176, 120, 9, 3.5, 5, 0.48),
    )
    for x, bottom_y, top_y, amplitude, offset, stroke, opacity in smoke_specs:
        smoke_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        smoke_draw = ImageDraw.Draw(smoke_layer)
        smoke_draw.line(
            smoke_path(phase, x, bottom_y, top_y, amplitude, offset),
            fill=(74, 124, 122, round(255 * opacity)),
            width=width(stroke),
            joint="curve",
        )
        image = Image.alpha_composite(image, smoke_layer)

    draw = ImageDraw.Draw(image)
    draw.ellipse((point(270, 186), point(284, 200)), fill=GOLD)
    draw.ellipse((point(292, 181), point(308, 197)), fill=GOLD)
    draw.ellipse((point(316, 186), point(330, 200)), fill=GOLD)

    bowl = cubic((228, 196), (244, 226), (356, 226), (372, 196))
    bowl.append(point(228, 196))
    draw.polygon(bowl, fill=PAPER)
    draw.line(bowl, fill=NAVY, width=width(5), joint="curve")
    draw.line((point(300, 222), point(300, 238)), fill=NAVY, width=width(5))
    draw.line((point(270, 252), point(330, 252)), fill=NAVY, width=width(5))
    draw.line((point(206, 196), point(394, 196)), fill=NAVY, width=width(5))
    draw.line((point(240, 252), point(254, 252)), fill=GOLD, width=width(5))
    draw.line((point(346, 252), point(360, 252)), fill=GOLD, width=width(5))

    return image.convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def save_animation(name: str, renderer) -> Path:
    frames = [renderer(2 * math.pi * index / FRAME_COUNT) for index in range(FRAME_COUNT)]
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
