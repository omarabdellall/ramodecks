"""Point the whole kit at your final URL (canonical, Open Graph / Twitter tags, JSON-LD, QR codes, CNAME file).

    python _build/set_domain.py https://ramodj.com
    python _build/set_domain.py https://YOUR-GITHUB-USERNAME.github.io/ramo      (project page, no custom domain)

Run from the repo root. Needs the venv with Pillow + qrcode (see README) for the QR step; the HTML step needs nothing.
"""
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent


def main():
    if len(sys.argv) < 2 or not sys.argv[1].startswith("http"):
        sys.exit(__doc__)
    new = sys.argv[1].rstrip("/")
    page = ROOT / "index.html"
    html = page.read_text(encoding="utf-8")
    old = re.search(r'<link rel="canonical" href="([^"]+?)/?">', html).group(1).rstrip("/")
    html = html.replace(old, new)
    page.write_text(html, encoding="utf-8")
    print(f"index.html: {old} -> {new}")

    host = urlparse(new).netloc
    cname = ROOT / "CNAME"
    if not host.endswith("github.io"):
        cname.write_text(host + "\n")
        print("CNAME written:", host)
    elif cname.exists():
        cname.unlink()
        print("CNAME removed (github.io address)")

    try:
        subprocess.run([sys.executable, str(ROOT / "_build" / "make_visuals.py"), new], check=True)
        subprocess.run([sys.executable, str(ROOT / "_build" / "make_zips.py")], check=True)
    except Exception as e:  # missing Pillow/qrcode
        print("QR/zips not rebuilt:", e)
        print("Install with:  pip install pillow numpy opencv-python-headless qrcode fonttools brotli  then rerun.")


if __name__ == "__main__":
    main()
