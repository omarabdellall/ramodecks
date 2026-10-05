"""Cut the site's three vertical clips from your reels.

1. Put the source videos in one folder.
2. Edit CLIPS below: which file, where to start (seconds), how long (8 to 20 s).
3. Run from the repo root:   python _build/make_clips.py /path/to/folder-with-reels
   python _build/make_clips.py /path/to/folder --sheet     (just makes contact sheets so you can pick moments)

Output: assets/video/clipN.mp4 + .webm (540x960, silent, under ~3 MB) and assets/img/poster-clipN.jpg.
Needs ffmpeg on PATH.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VID = ROOT / "assets" / "video"
IMG = ROOT / "assets" / "img"

# name -> (source file name, start seconds, duration seconds, hue shift in degrees, sharpen)
# hue: negative pulls magenta/purple club light toward cobalt, like the photo grade. 0 = leave alone.
# sharpen: True for low-resolution sources that get scaled up.
CLIPS = {
    "clip1": ("bf29fe6863944027a290417887efe264.mov", 2, 12, -14, True),    # RAMO mixing, 360x640 source
    "clip2": ("IMG_4196.MP4", 0.5, 10.5, -22, False),                        # room from above, CDJ in frame
    "clip3": ("IMG_0437.MP4", 0, 7.5, -22, False),                           # room from above
}

# same look as the photos: cooler shadows, warm lights, slightly calmer saturation
GRADE = ("eq=contrast=1.06:gamma=1.06:saturation=0.92,"
         "colorbalance=bs=0.05:gs=0.01:rh=0.025:bh=-0.02")


def vf(hue, sharp):
    chain = ["scale=540:960:force_original_aspect_ratio=increase:flags=lanczos", "crop=540:960"]
    if sharp:
        chain.append("unsharp=5:5:0.7:5:5:0.0")
    if hue:
        chain.append(f"hue=h={hue}")
    chain += [GRADE, "format=yuv420p"]
    return ",".join(chain)


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    src = Path(sys.argv[1]).expanduser()
    VID.mkdir(parents=True, exist_ok=True)
    if "--sheet" in sys.argv:
        out = ROOT / "_build" / "sheets"
        out.mkdir(exist_ok=True)
        for f in sorted(src.glob("*.mp4")) + sorted(src.glob("*.MOV")) + sorted(src.glob("*.mov")):
            run(["ffmpeg", "-y", "-i", str(f), "-vf", "fps=1/2,scale=180:-1,tile=8x4", "-frames:v", "1", str(out / (f.stem + ".jpg"))])
            print("sheet:", out / (f.stem + ".jpg"), " (one frame every 2 s)")
        return
    for name, (fname, ss, dur, hue, sharp) in CLIPS.items():
        f = src / fname
        if not f.exists():
            print("missing:", f)
            continue
        mp4, webm = VID / f"{name}.mp4", VID / f"{name}.webm"
        base = ["ffmpeg", "-y", "-ss", str(ss), "-t", str(dur), "-i", str(f), "-an", "-vf", vf(hue, sharp)]
        run(base + ["-c:v", "libx264", "-profile:v", "main", "-preset", "slow", "-crf", "27",
                    "-maxrate", "1400k", "-bufsize", "2800k", "-movflags", "+faststart", str(mp4)])
        run(base + ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "38", "-row-mt", "1", "-deadline", "good", "-cpu-used", "2", str(webm)])
        run(["ffmpeg", "-y", "-ss", str(min(dur / 2, 3)), "-i", str(mp4), "-frames:v", "1", "-vf", "scale=540:-1", "-q:v", "4", str(IMG / f"poster-{name}.jpg")])
        print(f"{name}: mp4 {mp4.stat().st_size/1e6:.2f} MB, webm {webm.stat().st_size/1e6:.2f} MB")


if __name__ == "__main__":
    main()
