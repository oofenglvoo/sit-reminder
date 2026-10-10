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
    draw = ImageDraw.Draw(img)
    pad = size * 0.06
    # 圆角矩形背景
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=size * 0.22,
        fill=(37, 99, 235, 255),
    )
    # 表盘
    cx = cy = size / 2
    r = size * 0.30
    draw.ellipse(
        [cx - r, cy - r, cx + r, cy + r],
        outline=(255, 255, 255, 255),
        width=max(1, int(size * 0.045)),
    )
    # 指针
    draw.line(
        [cx, cy, cx, cy - r * 0.62],
        fill=(255, 255, 255, 255),
        width=max(1, int(size * 0.05)),
    )
    draw.line(
        [cx, cy, cx + r * 0.5, cy],
        fill=(255, 255, 255, 255),
        width=max(1, int(size * 0.05)),
    )
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
