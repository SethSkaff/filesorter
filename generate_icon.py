#!/usr/bin/env python3
"""
generate_icon.py — Creates app_icon.ico for FileSorter.
Run once before building the installer.
Requires: Pillow  (pip install Pillow)
"""

from pathlib import Path
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Pillow not found. Install it: pip install Pillow")
    raise SystemExit(1)

HERE = Path(__file__).parent

def make_icon():
    sizes = [16, 24, 32, 48, 64, 128, 256]
    frames = []

    for sz in sizes:
        img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background circle
        margin = max(1, sz // 16)
        draw.ellipse(
            [margin, margin, sz - margin, sz - margin],
            fill=(79, 142, 247, 255),   # accent blue #4f8ef7
        )

        # Inner dark circle
        inner_margin = sz // 5
        draw.ellipse(
            [inner_margin, inner_margin, sz - inner_margin, sz - inner_margin],
            fill=(22, 33, 62, 255),     # panel #16213e
        )

        # Two horizontal "file" bars
        bar_h    = max(2, sz // 10)
        bar_w    = int(sz * 0.42)
        cx, cy   = sz // 2, sz // 2
        gap      = max(2, sz // 8)

        for dy in [-gap, gap]:
            x0 = cx - bar_w // 2
            y0 = cy + dy - bar_h // 2
            draw.rounded_rectangle(
                [x0, y0, x0 + bar_w, y0 + bar_h],
                radius=max(1, bar_h // 2),
                fill=(79, 142, 247, 255),
            )

        # Arrow pointing right (sort indicator)
        arrow_x  = cx + bar_w // 2 + max(2, sz // 12)
        arrow_cy = cy
        arrow_sz = max(2, sz // 7)
        pts = [
            (arrow_x,              arrow_cy - arrow_sz),
            (arrow_x + arrow_sz,   arrow_cy),
            (arrow_x,              arrow_cy + arrow_sz),
        ]
        draw.polygon(pts, fill=(76, 175, 125, 255))   # keep-green #4caf7d

        frames.append(img)

    # Save .ico (multi-size)
    ico_path = HERE / "app_icon.ico"
    frames[0].save(
        ico_path,
        format="ICO",
        sizes=[(f.width, f.height) for f in frames],
        append_images=frames[1:],
    )
    print(f"Icon saved: {ico_path}")

    # Also save a 256×256 PNG for reference / Windows Store
    png_path = HERE / "app_icon.png"
    frames[-1].save(png_path)
    print(f"PNG saved:  {png_path}")

if __name__ == "__main__":
    make_icon()
