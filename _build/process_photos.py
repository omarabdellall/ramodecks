"""Grade the keeper photos and export: press crops (landscape/portrait/square JPG),
web thumbs (WebP), hero (AVIF + WebP), video poster frames, and a tiny blur placeholder.

Run from the repo root:  python _build/process_photos.py
Source photos live in _build/source/. EXIF (incl. GPS) is dropped on export.
"""
import base64
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

try:
    import pillow_avif  # noqa: F401
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from grade import grade, to_img  # noqa: E402

SRC = HERE / "source"
PRESS = ROOT / "press"
IMG = ROOT / "assets" / "img"
PRESS.mkdir(exist_ok=True)
IMG.mkdir(parents=True, exist_ok=True)

# name -> (source, hue strength, denoise, target median, crops{kind: (cx, cy, width)})
# crop centers are in source pixels; width is the crop width in source pixels.
PHOTOS = {
    "ramo-01-hero": dict(src="p1.jpg", hue=1.0, nr=0, med=0.20, lift=1.3, face=(650, 780, 270, 0.9), crops=dict(
        portrait=(590, 1030, 1180), square=(590, 1110, 1180), landscape=(600, 880, 1180))),
    "ramo-02-booth": dict(src="p7.jpg", hue=1.0, nr=3, med=0.2, crops=dict(
        portrait=(930, 750, 1200), square=(950, 750, 1500), landscape=(1000, 840, 2000))),
    "ramo-03-mixer": dict(src="p9.jpg", hue=1.0, nr=3, med=0.2, crops=dict(
        portrait=(750, 1000, 1500), square=(750, 1100, 1500), landscape=(750, 870, 1500))),
    "ramo-04-floor": dict(src="p11.jpg", hue=1.0, nr=3, med=0.2, crops=dict(
        portrait=(1400, 800, 1000), square=(1400, 800, 1100), landscape=(1280, 700, 1440))),
    "ramo-05-room": dict(src="p19.jpg", hue=0.75, nr=3, med=0.15, crops=dict(
        portrait=(750, 1060, 1500), square=(750, 1250, 1500), landscape=(750, 1250, 1500))),
}
ASPECT = dict(portrait=4 / 5, square=1.0, landscape=16 / 9)


def crop(img, cx, cy, w, aspect):
    h = w / aspect
    x0 = int(round(min(max(cx - w / 2, 0), img.width - w)))
    y0 = int(round(min(max(cy - h / 2, 0), img.height - h)))
    return img.crop((x0, y0, x0 + int(w), y0 + int(round(h))))


def save_webp(im, path, q=78, maxw=None):
    if maxw and im.width > maxw:
        im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    im.save(path, "WEBP", quality=q, method=6)


def main():
    graded = {}
    for name, p in PHOTOS.items():
        g = to_img(grade(SRC / p["src"], hue=p["hue"], nr=p["nr"], median=p["med"], face=p.get("face"), lift=p.get("lift", 1.0)))
        graded[name] = g
        for kind, (cx, cy, w) in p["crops"].items():
            c = crop(g, cx, cy, w, ASPECT[kind])
            out = PRESS / f"{name}-{kind}.jpg"
            c.save(out, "JPEG", quality=92, optimize=True, subsampling=0)
            print(f"{out.name:36s} {c.width}x{c.height}  {out.stat().st_size/1e6:.2f} MB")

    # --- web hero (portrait, full frame) ---
    hero = graded["ramo-01-hero"]
    for w in (640, 900, 1180):
        im = hero.resize((w, round(hero.height * w / hero.width)), Image.LANCZOS)
        im.save(IMG / f"hero-{w}.webp", "WEBP", quality=74, method=6)
        try:
            im.save(IMG / f"hero-{w}.avif", "AVIF", quality=52, speed=5)
        except Exception as e:  # avif plugin missing
            print("avif skipped:", e)

    # --- tiny blur placeholder for the hero (inlined by index.html) ---
    tiny = hero.resize((24, round(24 * hero.height / hero.width)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1))
    buf = io.BytesIO()
    tiny.save(buf, "WEBP", quality=40)
    (IMG / "hero-lqip.txt").write_text("data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode())

    # --- press-grid thumbs (4:5) + bio portrait + room backdrop ---
    for name in PHOTOS:
        c = Image.open(PRESS / f"{name}-portrait.jpg")
        save_webp(c, IMG / f"{name}-thumb.webp", q=76, maxw=720)
    save_webp(Image.open(PRESS / "ramo-02-booth-portrait.jpg"), IMG / "bio.webp", q=78, maxw=800)
    save_webp(Image.open(PRESS / "ramo-03-mixer-landscape.jpg"), IMG / "mixer-wide.webp", q=70, maxw=1400)

    # --- 9:16 poster frames (placeholders until real clips are cut; make-clips.sh replaces them) ---
    posters = dict(clip1=("ramo-03-mixer", 700, 1000), clip2=("ramo-04-floor", 1400, 750), clip3=("ramo-05-room", 750, 1000))
    for k, (n, cx, cy) in posters.items():
        g = graded[n]
        w = int(g.height * 9 / 16) if g.height * 9 / 16 <= g.width else g.width
        c = crop(g, cx, cy, min(w, g.width), 9 / 16)
        c = c.resize((540, 960), Image.LANCZOS) if c.width != 540 else c
        c.save(IMG / f"poster-{k}.jpg", "JPEG", quality=80, optimize=True)
    print("done")


if __name__ == "__main__":
    main()
