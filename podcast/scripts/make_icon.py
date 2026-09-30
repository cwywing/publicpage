#!/usr/bin/env python3
"""生成播客页的应用图标：渐变底 + 白色耳机图形。

  python podcast/scripts/make_icon.py   # 输出 icon.png(180) / icon-512.png / favicon.png
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
S = 1024  # 工作尺寸，最后缩小抗锯齿

C1 = (94, 92, 230)    # 靛蓝
C2 = (10, 132, 255)   # 蓝


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient() -> Image.Image:
    img = Image.new("RGB", (S, S))
    dr = ImageDraw.Draw(img)
    for y in range(S):
        dr.line([(0, y), (S, y)], fill=lerp(C1, C2, y / S))
    return img


def main() -> None:
    img = gradient()
    dr = ImageDraw.Draw(img)
    w = S // 20  # 线宽

    # 头带：上半圆弧
    pad = S // 5
    box = (pad, pad + S // 14, S - pad, S - pad + S // 6)
    dr.arc(box, start=180, end=360, fill=(255, 255, 255), width=w)

    # 左右耳罩：圆角竖条
    cup_w, cup_h = S // 5, S // 3
    r = cup_w // 2
    arc_cx = (box[0] + box[2]) / 2
    left_cx = box[0] + r
    right_cx = box[2] - r
    cy = (box[1] + box[3]) / 2 + S // 44
    for cx in (left_cx, right_cx):
        dr.rounded_rectangle(
            (cx - cup_w / 2, cy - cup_h / 2, cx + cup_w / 2, cy + cup_h / 2),
            radius=r, fill=(255, 255, 255),
        )

    icon512 = img.resize((512, 512), Image.LANCZOS)
    icon512.save(ROOT / "icon-512.png")
    img.resize((180, 180), Image.LANCZOS).save(ROOT / "icon.png")
    img.resize((64, 64), Image.LANCZOS).save(ROOT / "favicon.png")
    print("wrote icon-512.png / icon.png / favicon.png")


if __name__ == "__main__":
    main()
