"""Write press/ramo-bios.txt and build the two downloadable ZIPs.   Run from repo root:  python _build/make_zips.py"""
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRESS = ROOT / "press"
EMAIL = "enygmabiz@gmail.com"  # keep in sync with index.html and assets/js/main.js

ONE_EN = ("RAMO is an NYC house and afro house DJ, now based in Tokyo. "
          "Opened at Circus Tokyo for Insomniac Records presents Riordan.")
ONE_JA = ("RAMO。ニューヨークで活動し、現在は東京を拠点とするハウス/アフロハウスDJ。"
          "Circus Tokyo「Insomniac Records presents Riordan」でオープニングを務めた。")

SHORT_EN = ("RAMO is a New York DJ now based in Tokyo. He has played house and afro house for two years, "
            "mainly at Casa Cecé's in NYC, plus bars, college parties and private events. "
            "On October 1, 2026 he opened at Circus Tokyo for Insomniac Records presents Riordan. "
            "He plays house, tech house, UK garage, techno and afro house.")
SHORT_JA = ("RAMO（ラモ）は、ニューヨークで活動し、現在は東京を拠点とするDJ。NYCで2年間ハウスとアフロハウスをプレイし、"
            "Casa Cecé’sを中心に、バーや大学のパーティー、プライベートイベントにも出演してきた。"
            "2026年10月1日、Circus Tokyo「Insomniac Records presents Riordan」でオープニングを担当。"
            "ハウス、テックハウス、UKガラージ、テクノ、アフロハウスをプレイする。")

LONG_EN = ("RAMO is a New York DJ now based in Tokyo. He has played house and afro house in NYC for two years. "
           "His main room there was Casa Cecé's. He has also played bars, college parties and private events.\n\n"
           "On October 1, 2026 he opened at Circus Tokyo for Insomniac Records presents Riordan.\n\n"
           "He plays house, tech house, UK garage, techno and afro house, and can go open format when a night needs it. "
           "He plays on CDJ-3000s, prepares his sets in rekordbox and plays from USB. He also makes afro house edits in Ableton, Drake edits among them.")
LONG_JA = ("RAMOはニューヨークで活動し、現在は東京を拠点とするDJ。NYCで2年間、ハウスとアフロハウスをプレイしてきた。"
           "メインの現場はCasa Cecé’s。バー、大学のパーティー、プライベートイベントにも出演している。\n\n"
           "2026年10月1日、Circus Tokyo「Insomniac Records presents Riordan」でオープニングを担当。\n\n"
           "ハウス、テックハウス、UKガラージ、テクノ、アフロハウスをプレイし、イベントに合わせてオープンフォーマットにも対応する。"
           "機材はCDJ-3000。セットはrekordboxで準備し、USBでプレイする。Abletonでアフロハウスのエディットも制作しており、Drakeのエディットもある。")


def words(s):
    return len(re.findall(r"[A-Za-z0-9’'\-]+", s))


def main():
    ws, wl = words(SHORT_EN), words(LONG_EN)
    assert 40 <= ws <= 70, f"short bio is {ws} words"
    if not 120 <= wl <= 180:
        print(f"note: long bio is {wl} words (target was 120 to 180)")
    print(f"short bio {ws} words, long bio {wl} words")

    txt = f"""RAMO  |  NYC > Tokyo  |  DJ
=====================================

BOOKING   {EMAIL}
INSTAGRAM @ramo.decks   https://www.instagram.com/ramo.decks/
SOUNDCLOUD https://soundcloud.com/ramo-the-dj

PLAYS     House, tech house, UK garage, afro house, techno.
RIDER     2-3x CDJ-3000, DJM-900NXS2 / DJM-A9 / DJM-V10, booth monitor, rekordbox USB


ONE-LINER (EN)
{ONE_EN}

ONE-LINER (JP)
{ONE_JA}


SHORT BIO (EN)
{SHORT_EN}

SHORT BIO (JP)
{SHORT_JA}


LONG BIO (EN)
{LONG_EN}

LONG BIO (JP)
{LONG_JA}
"""
    (PRESS / "ramo-bios.txt").write_text(txt, encoding="utf-8")

    photos = sorted(PRESS.glob("ramo-0*.jpg"))
    readme = (f"RAMO press photos\n\nEach photo comes as landscape (16:9), portrait (4:5) and square (1:1).\n"
              f"Free to use to promote RAMO's shows.\n\nBooking: {EMAIL}\nInstagram: @ramo.decks\n")
    with zipfile.ZipFile(PRESS / "ramo-press-photos.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in photos:
            z.write(p, f"ramo-press-photos/{p.name}")
        z.write(PRESS / "ramo-bios.txt", "ramo-press-photos/ramo-bios.txt")
        z.writestr("ramo-press-photos/README.txt", readme)

    with zipfile.ZipFile(PRESS / "ramo-logos-and-banners.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted((ROOT / "visuals").iterdir()):
            if p.is_file():
                z.write(p, f"ramo-logos-and-banners/{p.name}")
        z.writestr("ramo-logos-and-banners/README.txt",
                   "RAMO wordmark: -white is for dark backgrounds, -black for light, -orange for dark flyers.\n"
                   "Banners: 16:9 for LED screens (1920x1080 and 3840x2160). Square 1080 and story 1080x1920 for flyers and socials.\n"
                   "Do not stretch, recolor or add effects to the wordmark.\n")
    for z in ("ramo-press-photos.zip", "ramo-logos-and-banners.zip"):
        print(z, f"{(PRESS / z).stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
