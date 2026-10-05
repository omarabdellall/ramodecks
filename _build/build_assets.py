"""Subset fonts to what the page uses, inline the wordmark sprite + hero blur placeholder, make the grain tile.
Run from the repo root after editing any Japanese text:   python _build/build_assets.py
"""
import re
import sys
from pathlib import Path

import numpy as np
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import wordmark as wm  # noqa: E402

FONTS_IN = HERE / "fonts"
FONTS_OUT = ROOT / "assets" / "fonts"
FONTS_OUT.mkdir(parents=True, exist_ok=True)

html = (ROOT / "index.html").read_text(encoding="utf-8")
js = (ROOT / "assets" / "js" / "main.js").read_text(encoding="utf-8")
page_chars = set(html + js)

LATIN = set(range(0x20, 0x7F)) | {0xA0, 0xB7, 0xD7, 0xE9, 0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026, 0x2192}
JP_EXTRA = set(range(0x3000, 0x3040)) | set(range(0x3040, 0x30FF)) | set(range(0xFF00, 0xFFEF))


def subset_font(font: TTFont, unicodes, out: Path):
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt", "locl", "ccmp", "mark", "mkmk", "vert", "palt"]
    opts.name_IDs = [1, 2]
    opts.notdef_outline = True
    opts.drop_tables += ["DSIG"]
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=sorted(unicodes))
    sub.subset(font)
    font.flavor = "woff2"
    font.save(out)
    print(f"{out.name:28s} {out.stat().st_size/1024:6.1f} KB")


def main():
    # Archivo: variable, limited to the ranges the CSS uses
    f = TTFont(FONTS_IN / "Archivo.ttf")
    f = instancer.instantiateVariableFont(f, {"wght": (400, 900), "wdth": (100, 125)})
    subset_font(f, LATIN | {c for c in map(ord, page_chars) if c < 0x250}, FONTS_OUT / "archivo-sub.woff2")

    for w, name in ((400, "DMMono-Regular"), (500, "DMMono-Medium")):
        subset_font(TTFont(FONTS_IN / f"{name}.ttf"), LATIN | {c for c in map(ord, page_chars) if c < 0x250}, FONTS_OUT / f"dmmono-{w}-sub.woff2")

    jp = {ord(c) for c in page_chars if ord(c) >= 0x2E00} | JP_EXTRA | LATIN
    for w, name in ((400, "Regular"), (700, "Bold"), (900, "Black")):
        subset_font(TTFont(FONTS_IN / f"ZenKaku-{name}.ttf"), jp, FONTS_OUT / f"zenkaku-{w}-sub.woff2")

    # wordmark sprite + hero placeholder inlined into index.html
    d, w, h = wm.svg_path()
    sym = f'<symbol id="w" viewBox="0 0 {w:.0f} {h:.0f}"><path d="{d}"/></symbol>'
    txt = html.replace("assets/img/wordmark.svg#w", "#w")
    txt = re.sub(r'<symbol id="w".*?</symbol>\s*', "", txt, flags=re.S)
    txt = txt.replace('<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">\n',
                      '<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">\n  ' + sym + "\n", 1)
    lqip = (ROOT / "assets" / "img" / "hero-lqip.txt").read_text().strip()
    txt = re.sub(r"--lqip:url\('[^']*'\)", f"--lqip:url('{lqip}')", txt)
    (ROOT / "index.html").write_text(txt, encoding="utf-8")

    # film grain tile (kept tiny; shown at 7% opacity)
    rng = np.random.default_rng(11)
    g = np.clip(rng.normal(128, 46, (112, 112)), 0, 255).astype(np.uint8)
    Image.fromarray(g, "L").save(ROOT / "assets" / "img" / "grain.png", optimize=True)
    print("index.html patched, grain.png written")


if __name__ == "__main__":
    main()
