"""Club visuals pack: wordmark SVG/PNG (white + black), favicon set, LED banner, square + story
flyer art, OG image, QR codes.   Run from repo root:  python _build/make_visuals.py [site_url]"""
import sys
from pathlib import Path

import numpy as np
import qrcode
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import wordmark as wm  # noqa: E402
from grade import grade, to_img  # noqa: E402

OUT = ROOT / "visuals"
OUT.mkdir(exist_ok=True)
SITE_URL = sys.argv[1] if len(sys.argv) > 1 else "https://ramodj.com"

BONE = (242, 238, 231)
INK = (8, 9, 12)
ORANGE = (255, 79, 26)
FONTS = HERE / "fonts"


# ---------------------------------------------------------------- helpers
def mono(size, medium=True):
    return ImageFont.truetype(str(FONTS / ("DMMono-Medium.ttf" if medium else "DMMono-Regular.ttf")), size)


def arrow_font(size):
    f = ImageFont.truetype(str(FONTS / "Archivo.ttf"), size)
    f.set_variation_by_axes([500, 100])  # [wght, wdth]
    return f


def zen(size):
    return ImageFont.truetype(str(FONTS / "ZenKaku-Black.ttf"), size)


def text_width(text, size, track_em, medium=True):
    w = 0
    for ch in text:
        f = arrow_font(size) if ch == "→" else mono(size, medium)
        w += f.getlength(ch) + track_em * size
    return w - track_em * size


def draw_text(im, x, y, text, size, fill=BONE, track_em=0.14, anchor="l", medium=True, accent_arrow=True):
    d = ImageDraw.Draw(im, "RGBA")
    w = text_width(text, size, track_em, medium)
    if anchor == "c":
        x -= w / 2
    elif anchor == "r":
        x -= w
    for ch in text:
        arrow = ch == "→"
        f = arrow_font(size) if arrow else mono(size, medium)
        d.text((x, y), ch, font=f, fill=ORANGE if (arrow and accent_arrow) else fill)
        x += f.getlength(ch) + track_em * size
    return w


def background(w, h, seed=3, cobalt=(0.1, 1.05, 0.7, 0.36), orange=(0.9, -0.08, 0.3, 0.16)):
    """Near-black with a cobalt wash and a small warm bleed, taken from the hero photo's light."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    base = np.zeros((h, w, 3), np.float32) + np.array(INK, np.float32)

    def glow(cx, cy, r, color, amp):
        d2 = ((xx - cx * w) ** 2 + (yy - cy * h) ** 2) / (r * max(w, h)) ** 2
        return (np.exp(-d2 * 2.4) * amp)[..., None] * np.array(color, np.float32)

    base += glow(cobalt[0], cobalt[1], cobalt[2], (18, 52, 255), cobalt[3])
    base += glow(orange[0], orange[1], orange[2], (255, 96, 34), orange[3])
    return base


def finish(arr, grain=5.5, seed=7):
    rng = np.random.default_rng(seed)
    h, w = arr.shape[:2]
    n = rng.normal(0, grain, (h, w, 1)).astype(np.float32)
    return Image.fromarray(np.clip(arr + n, 0, 255).astype(np.uint8), "RGB")


def paste_rgba(base_rgb, layer_rgba, x, y):
    base = base_rgb.convert("RGBA")
    base.alpha_composite(layer_rgba, (int(x), int(y)))
    return base.convert("RGB")


def ticks(im, m, ln, col=(242, 238, 231, 110)):
    d = ImageDraw.Draw(im, "RGBA")
    w, h = im.size
    for (x, y) in [(m, m), (w - m, m), (m, h - m), (w - m, h - m)]:
        d.line([(x - ln, y), (x + ln, y)], fill=col, width=max(1, w // 1400))
        d.line([(x, y - ln), (x, y + ln)], fill=col, width=max(1, w // 1400))


def hero_photo():
    return to_img(grade(HERE / "source" / "p1.jpg", hue=1.0, nr=0, median=0.20, lift=1.3, face=(650, 780, 270, 0.9)))


def photo_layer(photo, height, width_crop=None):
    """Hero photo scaled to `height` px tall, RGBA."""
    r = height / photo.height
    im = photo.resize((round(photo.width * r), height), Image.LANCZOS).convert("RGBA")
    return im


def fade_edge(layer, side="left", frac=0.5, bottom=0.0):
    a = np.ones((layer.height, layer.width), np.float32)
    xs = np.linspace(0, 1, layer.width, dtype=np.float32)
    ramp = np.clip(xs / frac, 0, 1) ** 1.6 if side == "left" else np.clip((1 - xs) / frac, 0, 1) ** 1.6
    a *= ramp[None, :]
    if bottom:
        ys = np.linspace(0, 1, layer.height, dtype=np.float32)
        a *= np.clip((1 - ys) / bottom, 0, 1)[:, None] ** 1.4
    arr = np.asarray(layer).copy()
    arr[..., 3] = (arr[..., 3] * a).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


# ---------------------------------------------------------------- wordmark files
def write_wordmarks():
    d, w, h = wm.svg_path()
    for name, fill in (("white", "#FFFFFF"), ("black", "#000000")):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="RAMO">'
               f'<path fill="{fill}" d="{d}"/></svg>\n')
        (OUT / f"ramo-wordmark-{name}.svg").write_text(svg)
        wm.raster(2400, (255, 255, 255) if name == "white" else (0, 0, 0)).save(OUT / f"ramo-wordmark-{name}.png")
    # orange accent version for dark flyers
    (OUT / "ramo-wordmark-orange.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="RAMO">'
        f'<path fill="#FF4F1A" d="{d}"/></svg>\n')
    # site-inline version
    (ROOT / "assets" / "img" / "wordmark.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}"><path fill="currentColor" d="{d}"/></svg>\n')
    return d, w, h


def write_favicons():
    dR, wR, hR = wm.svg_path("R", 0)
    s = 512
    pad = s * 0.2
    sc = (s - 2 * pad) / max(wR, hR)
    tx, ty = (s - wR * sc) / 2, (s - hR * sc) / 2
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s} {s}">'
           f'<rect width="{s}" height="{s}" rx="{s*0.18:.0f}" fill="#08090C"/>'
           f'<path fill="#FF4F1A" transform="translate({tx:.1f} {ty:.1f}) scale({sc:.5f})" d="{dR}"/></svg>\n')
    (ROOT / "favicon.svg").write_text(svg)

    def icon(px, rounded=True):
        img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        if rounded:
            d.rounded_rectangle([0, 0, px - 1, px - 1], radius=int(px * 0.18), fill=INK + (255,))
        else:
            d.rectangle([0, 0, px, px], fill=INK + (255,))
        g = wm.raster(int(px * 0.5), ORANGE, text="R", track=0)
        img.alpha_composite(g, ((px - g.width) // 2, (px - g.height) // 2))
        return img

    icon(32).save(ROOT / "favicon-32.png")
    icon(180, rounded=False).convert("RGB").save(ROOT / "apple-touch-icon.png")
    icon(192).save(ROOT / "icon-192.png")
    icon(512).save(ROOT / "icon-512.png")
    icon(256).save(ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])


# ---------------------------------------------------------------- banners
def led_banner(W=1920, H=1080, photo=False):
    k = W / 1920
    arr = background(W, H, cobalt=(0.12, 1.05, 0.75, 0.34) if not photo else (0.1, 0.9, 0.7, 0.32))
    im = finish(arr, grain=5.0 * (1 if k <= 1 else 0.9))
    if photo:
        ph = photo_layer(hero_photo(), H)
        layer = fade_edge(ph, "left", frac=0.55)
        im = paste_rgba(im, layer, W - ph.width * 0.98, 0)
        wmk = wm.raster(int(W * 0.50), BONE)
        im = paste_rgba(im, wmk, 110 * k, H * 0.40)
        draw_text(im, 112 * k, H * 0.40 + wmk.height + 52 * k, "NYC → TOKYO", int(36 * k), track_em=0.32)
        draw_text(im, 112 * k, H - 112 * k, "HOUSE  /  TECH HOUSE  /  UK GARAGE  /  AFRO HOUSE", int(21 * k), fill=(242, 238, 231, 190), track_em=0.2, medium=False)
    else:
        wmk = wm.raster(int(W * 0.66), BONE)
        im = paste_rgba(im, wmk, (W - wmk.width) / 2, H * 0.5 - wmk.height / 2 - 30 * k)
        draw_text(im, W / 2, H * 0.5 + wmk.height / 2 + 36 * k, "NYC → TOKYO", int(40 * k), track_em=0.4, anchor="c")
    ticks(im, int(54 * k), int(14 * k))
    d = ImageDraw.Draw(im, "RGBA")
    d.text((int(86 * k), int(80 * k)), "ラモ", font=zen(int(26 * k)), fill=BONE + (210,))
    draw_text(im, W - 86 * k, 80 * k, "@ramo.decks", int(22 * k), fill=(242, 238, 231, 200), track_em=0.12, anchor="r", medium=False)
    return im


def flyer_square(S=1080, photo=True):
    k = S / 1080
    if photo:
        g = to_img(grade(HERE / "source" / "p1.jpg", hue=1.0, nr=0, median=0.20, lift=1.3, face=(650, 780, 270, 0.9)))
        sq = wm_crop = g.crop((0, 450, 1180, 1630)).resize((S, S), Image.LANCZOS)
        arr = np.asarray(sq).astype(np.float32)
        ys = np.linspace(0, 1, S, dtype=np.float32)[:, None, None]
        shade = np.clip((ys - 0.52) / 0.48, 0, 1) ** 1.5
        arr = arr * (1 - 0.92 * shade) + np.array(INK, np.float32) * 0.92 * shade
        im = finish(arr, grain=3.5)
        wmk = wm.raster(int(S * 0.84), BONE)
        im = paste_rgba(im, wmk, (S - wmk.width) / 2, S - wmk.height - 150 * k)
        draw_text(im, S / 2, S - 100 * k, "NYC → TOKYO", int(30 * k), track_em=0.4, anchor="c")
    else:
        arr = background(S, S, cobalt=(0.2, 1.05, 0.85, 0.32))
        im = finish(arr)
        wmk = wm.raster(int(S * 0.84), BONE)
        im = paste_rgba(im, wmk, (S - wmk.width) / 2, S / 2 - wmk.height / 2 - 20 * k)
        draw_text(im, S / 2, S / 2 + wmk.height / 2 + 40 * k, "NYC → TOKYO", int(32 * k), track_em=0.4, anchor="c")
    ticks(im, int(44 * k), int(12 * k))
    ImageDraw.Draw(im, "RGBA").text((int(70 * k), int(66 * k)), "ラモ", font=zen(int(24 * k)), fill=BONE + (220,))
    return im


def flyer_story(W=1080, H=1920):
    k = W / 1080
    g = to_img(grade(HERE / "source" / "p1.jpg", hue=1.0, nr=0, median=0.20, lift=1.3, face=(650, 780, 270, 0.9)))
    r = H / g.height
    ph = g.resize((round(g.width * r), H), Image.LANCZOS)
    x0 = max(0, int((ph.width - W) * 0.5))
    ph = ph.crop((x0, 0, x0 + W, H))
    arr = np.asarray(ph).astype(np.float32)
    ys = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    shade = np.clip((ys - 0.60) / 0.40, 0, 1) ** 1.4
    arr = arr * (1 - 0.94 * shade) + np.array(INK, np.float32) * 0.94 * shade
    im = finish(arr, grain=3.5)
    wmk = wm.raster(int(W * 0.84), BONE)
    y = int(H * 0.755)
    im = paste_rgba(im, wmk, (W - wmk.width) / 2, y)
    draw_text(im, W / 2, y + wmk.height + 44 * k, "NYC → TOKYO", int(32 * k), track_em=0.4, anchor="c")
    draw_text(im, W / 2, y + wmk.height + 104 * k, "HOUSE / TECH HOUSE / UK GARAGE / AFRO HOUSE", int(18 * k), fill=(242, 238, 231, 190), track_em=0.18, anchor="c", medium=False)
    ImageDraw.Draw(im, "RGBA").text((int(70 * k), int(250 * k)), "ラモ", font=zen(int(24 * k)), fill=BONE + (220,))
    return im


def og_image(W=1200, H=630):
    arr = background(W, H, cobalt=(0.05, 0.9, 0.7, 0.45))
    im = finish(arr, grain=4)
    ph = photo_layer(hero_photo(), H)
    layer = fade_edge(ph, "left", frac=0.5)
    im = paste_rgba(im, layer, W - ph.width * 0.97, 0)
    wmk = wm.raster(int(W * 0.56), BONE)
    im = paste_rgba(im, wmk, 64, H * 0.34)
    draw_text(im, 66, H * 0.34 + wmk.height + 34, "NYC → TOKYO", 28, track_em=0.34)
    draw_text(im, 66, H - 70, "HOUSE / TECH HOUSE / UK GARAGE / AFRO HOUSE", 15, fill=(242, 238, 231, 190), track_em=0.16, medium=False)
    ticks(im, 30, 9)
    return im


# ---------------------------------------------------------------- QR
def qr_files(url):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, box_size=24, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").convert("RGB").save(OUT / "ramo-qr.png")
    inv = qr.make_image(fill_color="white", back_color=(8, 9, 12)).convert("RGB")
    inv.save(OUT / "ramo-qr-dark.png")


def main():
    write_wordmarks()
    write_favicons()
    led_banner(1920, 1080, photo=False).save(OUT / "ramo-led-banner-1920x1080.jpg", quality=92)
    led_banner(3840, 2160, photo=False).save(OUT / "ramo-led-banner-3840x2160.jpg", quality=90)
    led_banner(1920, 1080, photo=True).save(OUT / "ramo-led-banner-photo-1920x1080.jpg", quality=92)
    flyer_square(1080, photo=False).save(OUT / "ramo-square-1080.jpg", quality=92)
    flyer_square(1080, photo=True).save(OUT / "ramo-square-photo-1080.jpg", quality=92)
    flyer_story().save(OUT / "ramo-story-1080x1920.jpg", quality=92)
    og = og_image()
    og.save(ROOT / "assets" / "img" / "og.jpg", quality=88)
    qr_files(SITE_URL)
    print("visuals ok ->", OUT, " QR ->", SITE_URL)


if __name__ == "__main__":
    main()
