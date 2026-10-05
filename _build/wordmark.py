"""RAMO wordmark: Archivo (wght 900, wdth 125) outlines, tightened tracking.
One source of truth for the SVG files, PNG exports, favicon and every banner."""
from pathlib import Path

import cv2
import numpy as np
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image

HERE = Path(__file__).resolve().parent
FONT_SRC = HERE / "fonts" / "Archivo.ttf"
TRACK = -0.012  # em; tight, poster-style


def _font():
    f = TTFont(FONT_SRC)
    return instancer.instantiateVariableFont(f, {"wght": 900, "wdth": 125})


_F = None


def font():
    global _F
    if _F is None:
        _F = _font()
    return _F


class FlattenPen(BasePen):
    """Flatten quadratic/cubic outlines into polylines (list of contours)."""

    def __init__(self, gs, steps=14):
        super().__init__(gs)
        self.contours, self.cur, self.steps = [], [], steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            self.cur.append((
                mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0],
                mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1],
            ))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            self.cur.append((
                mt**2 * p0[0] + 2 * mt * t * p1[0] + t**2 * p2[0],
                mt**2 * p0[1] + 2 * mt * t * p1[1] + t**2 * p2[1],
            ))

    def _closePath(self):
        if self.cur:
            self.contours.append(self.cur)
        self.cur = []

    _endPath = _closePath


def layout(text="RAMO", track=TRACK):
    """Return [(glyphname, x_offset)] in font units, total advance, and ink bounds."""
    f = font()
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    upm = f["head"].unitsPerEm
    x, items = 0, []
    for ch in text:
        gn = cmap[ord(ch)]
        items.append((gn, x))
        x += gs[gn].width + track * upm
    # ink bounds
    xmin = ymin = 1e9
    xmax = ymax = -1e9
    for gn, ox in items:
        bp = BoundsPen(gs)
        gs[gn].draw(bp)
        b = bp.bounds
        xmin, xmax = min(xmin, b[0] + ox), max(xmax, b[2] + ox)
        ymin, ymax = min(ymin, b[1]), max(ymax, b[3])
    return items, (xmin, ymin, xmax, ymax)


def svg_path(text="RAMO", track=TRACK):
    """Return (path_d, width, height) with y flipped and origin at the ink box's top-left."""
    f = font()
    gs = f.getGlyphSet()
    items, (x0, y0, x1, y1) = layout(text, track)
    pen = SVGPathPen(gs, ntos=lambda v: ("%.1f" % v).rstrip("0").rstrip("."))
    for gn, ox in items:
        tp = TransformPen(pen, (1, 0, 0, -1, ox - x0, y1))
        gs[gn].draw(tp)
    return pen.getCommands(), x1 - x0, y1 - y0


def raster(width_px, rgb=(255, 255, 255), text="RAMO", track=TRACK, ss=2):
    """Anti-aliased RGBA wordmark, `width_px` wide, transparent background."""
    f = font()
    gs = f.getGlyphSet()
    items, (x0, y0, x1, y1) = layout(text, track)
    w_units, h_units = x1 - x0, y1 - y0
    scale = width_px * ss / w_units
    W, H = int(round(w_units * scale)), int(round(h_units * scale))
    mask = np.zeros((H, W), np.uint8)
    for gn, ox in items:
        fp = FlattenPen(gs)
        gs[gn].draw(fp)
        polys = [
            np.array([[(px + ox - x0) * scale, (y1 - py) * scale] for px, py in c], np.float32).round().astype(np.int32)
            for c in fp.contours
        ]
        cv2.fillPoly(mask, polys, 255)  # even-odd handles the counters of R, A, O
    mask = cv2.resize(mask, (W // ss, H // ss), interpolation=cv2.INTER_AREA)
    out = np.zeros(mask.shape + (4,), np.uint8)
    out[..., 0], out[..., 1], out[..., 2], out[..., 3] = rgb[0], rgb[1], rgb[2], mask
    return Image.fromarray(out, "RGBA")


def glyph_raster(ch, size_px, rgb):
    """Single-letter raster (used for the favicon monogram)."""
    return raster(size_px, rgb, text=ch, track=0)
