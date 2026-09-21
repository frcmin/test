#!/usr/bin/env python3
"""Rasterize the NexoBrowser sci-fi mark into Firefox branding icon slots."""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

SRC = Path("/opt/cursor/artifacts/assets/nexobrowser_icon_1024.png")
BRAND = Path("additions/browser/branding/camoufox")


def resize(img: Image.Image, size: int) -> Image.Image:
    return img.resize((size, size), Image.Resampling.LANCZOS)


def save_png(img: Image.Image, dest: Path, size: int) -> None:
    resize(img, size).save(dest, format="PNG", optimize=True)


def save_ico(img: Image.Image, dest: Path, sizes: list[int]) -> None:
    import io
    import struct

    def png_bytes(size: int) -> bytes:
        buf = io.BytesIO()
        img.resize((size, size), Image.Resampling.LANCZOS).save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    blobs = [png_bytes(s) for s in sizes]
    offset = 6 + 16 * len(sizes)
    parts = [struct.pack("<HHH", 0, 1, len(sizes))]
    for size, data in zip(sizes, blobs):
        w = 0 if size >= 256 else size
        h = 0 if size >= 256 else size
        parts.append(struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(data), offset))
        offset += len(data)
    dest.write_bytes(b"".join(parts) + b"".join(blobs))


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"missing source icon: {SRC}")
    img = Image.open(SRC).convert("RGBA")

    png_sizes = {
        "default16.png": 16,
        "default22.png": 22,
        "default24.png": 24,
        "default32.png": 32,
        "default48.png": 48,
        "default64.png": 64,
        "default128.png": 128,
        "default256.png": 256,
        "logo.png": 256,
        "VisualElements_70.png": 70,
        "VisualElements_150.png": 150,
        "PrivateBrowsing_70.png": 70,
        "PrivateBrowsing_150.png": 150,
        "content/about-logo.png": 256,
        "content/about-logo@2x.png": 512,
        "content/about-logo-private.png": 256,
        "content/about-logo-private@2x.png": 512,
        "content/about.png": 256,
        "msix/Assets/StoreLogo.scale-200.png": 88,
        "msix/Assets/SmallTile.scale-200.png": 142,
        "msix/Assets/Square44x44Logo.scale-200.png": 88,
        "msix/Assets/Square44x44Logo.targetsize-256.png": 256,
        "msix/Assets/Square44x44Logo.altform-lightunplated_targetsize-256.png": 256,
        "msix/Assets/Square44x44Logo.altform-unplated_targetsize-256.png": 256,
        "msix/Assets/Square150x150Logo.scale-200.png": 300,
        "msix/Assets/Document44x44.png": 44,
        "msix/Assets/LargeTile.scale-200.png": 310,
        "msix/Assets/Wide310x150Logo.scale-200.png": 310,
        "Assets.xcassets/AppIcon.appiconset/icon_16x16.png": 16,
        "Assets.xcassets/AppIcon.appiconset/icon_16x16@2x.png": 32,
        "Assets.xcassets/AppIcon.appiconset/icon_32x32.png": 32,
        "Assets.xcassets/AppIcon.appiconset/icon_32x32@2x.png": 64,
        "Assets.xcassets/AppIcon.appiconset/icon_128x128.png": 128,
        "Assets.xcassets/AppIcon.appiconset/icon_128x128@2x.png": 256,
        "Assets.xcassets/AppIcon.appiconset/icon_256x256.png": 256,
        "Assets.xcassets/AppIcon.appiconset/icon_256x256@2x.png": 512,
        "Assets.xcassets/AppIcon.appiconset/icon_512x512.png": 512,
        "Assets.xcassets/AppIcon.appiconset/icon_512x512@2x.png": 1024,
    }

    replaced: list[str] = []
    for rel, size in png_sizes.items():
        dest = BRAND / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith("Wide310x150Logo.scale-200.png"):
            canvas = Image.new("RGBA", (620, 300), (6, 10, 28, 255))
            mark = resize(img, 280)
            canvas.paste(mark, (170, 10), mark)
            canvas.save(dest, format="PNG", optimize=True)
        else:
            save_png(img, dest, size)
        replaced.append(str(dest))

    ico_map = {
        "firefox.ico": [16, 24, 32, 48, 64, 128, 256],
        "firefox64.ico": [16, 32, 48, 64],
        "document.ico": [16, 32, 48, 256],
        "document_pdf.ico": [16, 32, 48, 256],
        "newtab.ico": [16, 32, 48],
        "newwindow.ico": [16, 32, 48],
        "pbmode.ico": [16, 32, 48, 256],
    }
    for name, sizes in ico_map.items():
        dest = BRAND / name
        save_ico(img, dest, sizes)
        replaced.append(str(dest))

    # About-dialog SVG: embed the 256px PNG so chrome shows the same mark.
    png256 = BRAND / "content/about-logo.png"
    svg = BRAND / "content/about-logo.svg"
    b64 = png256.read_bytes()
    import base64

    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        'width="256" height="256" viewBox="0 0 256 256">\n'
        f'  <image width="256" height="256" href="data:image/png;base64,{base64.b64encode(b64).decode()}" />\n'
        "</svg>\n",
        encoding="utf-8",
    )
    replaced.append(str(svg))

    master = Path("nexo-browser/icons/nexobrowser_icon_1024.png")
    master.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC, master)
    replaced.append(str(master))

    print(f"wrote {len(replaced)} branding assets from {SRC}")
    for path in replaced:
        print(path)


if __name__ == "__main__":
    main()
