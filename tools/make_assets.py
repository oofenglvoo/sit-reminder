"""生成内置资源：assets/icon.ico 与 assets/remind.wav。

用法：python tools/make_assets.py
依赖：Pillow（生成图标）；wave/math 为标准库（生成音频）。
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

SAMPLE_RATE = 44100


def _tone(freq: float, duration: float, volume: float = 0.5) -> list[float]:
    count = int(SAMPLE_RATE * duration)
    samples: list[float] = []
    for i in range(count):
        t = i / SAMPLE_RATE
        # 简单淡入淡出包络，避免爆音
        attack = min(1.0, i / (0.02 * SAMPLE_RATE))
        release = min(1.0, (count - i) / (0.05 * SAMPLE_RATE))
        env = attack * release
        samples.append(volume * env * math.sin(2 * math.pi * freq * t))
    return samples


def make_wav(path: Path) -> None:
    """合成一段柔和的“叮咚”双音提示音。"""
    first = _tone(659.25, 0.22, 0.45)   # E5
    gap = [0.0] * int(SAMPLE_RATE * 0.03)
    second = _tone(987.77, 0.32, 0.45)  # B5
    samples = first + gap + second

    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        frames = b"".join(
            struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples
        )
        wav.writeframes(frames)


def _draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    scale = 4
    large_size = size * scale
    shape = Image.new("L", (large_size, large_size), 0)
    shape_draw = ImageDraw.Draw(shape)
    pad = large_size * 0.055
    radius = large_size * 0.25
    shape_draw.rounded_rectangle(
        [pad, pad, large_size - pad, large_size - pad],
        radius=radius,
        fill=255,
    )

    # 深青绿到明亮青绿的背景渐变，配合清晰、简练的时钟轮廓。
    gradient = Image.new("RGBA", (large_size, large_size), (0, 0, 0, 0))
    pixels = gradient.load()
    start = (15, 105, 91)
    end = (39, 178, 133)
    for y in range(large_size):
        t = y / max(1, large_size - 1)
        color = tuple(round(a + (b - a) * t) for a, b in zip(start, end))
        for x in range(large_size):
            pixels[x, y] = (*color, 255)
    gradient.putalpha(shape)

    detail = Image.new("RGBA", (large_size, large_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(detail)
    cx = cy = large_size / 2
    radius = large_size * 0.305
    white = (246, 255, 251, 255)
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=white,
        width=max(5, int(large_size * 0.035)),
    )

    # 四个短刻度，避免小尺寸下细节拥挤。
    tick_outer = radius * 0.82
    tick_inner = radius * 0.68
    tick_width = max(4, int(large_size * 0.027))
    for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        draw.line(
            [
                (cx + dx * tick_inner, cy + dy * tick_inner),
                (cx + dx * tick_outer, cy + dy * tick_outer),
            ],
            fill=white,
            width=tick_width,
        )

    draw.line(
        [(cx, cy), (cx, cy - radius * 0.49)],
        fill=white,
        width=max(6, int(large_size * 0.043)),
    )
    draw.line(
        [(cx, cy), (cx + radius * 0.40, cy + radius * 0.22)],
        fill=white,
        width=max(6, int(large_size * 0.043)),
    )
    hub = large_size * 0.045
    draw.ellipse([cx - hub, cy - hub, cx + hub, cy + hub], fill=white)

    gradient.alpha_composite(detail)
    img = gradient.resize((size, size), Image.Resampling.LANCZOS)
    return img


def make_ico(path: Path) -> None:
    sizes = [16, 24, 32, 48, 64, 128, 256]
    base = _draw_icon(256)
    path.parent.mkdir(parents=True, exist_ok=True)
    base.save(path, format="ICO", sizes=[(s, s) for s in sizes])


def main() -> None:
    make_ico(ASSETS / "icon.ico")
    make_wav(ASSETS / "remind.wav")
    print(f"已生成: {ASSETS / 'icon.ico'}")
    print(f"已生成: {ASSETS / 'remind.wav'}")


if __name__ == "__main__":
    main()
