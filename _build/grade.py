"""One consistent grade for every RAMO photo: cobalt shadows, warm sodium highlights,
magenta/purple club light pulled toward blue so the set reads as one shoot."""
import cv2
import numpy as np
from PIL import Image


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0


def denoise(rgb, h=3):
    u8 = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    out = cv2.fastNlMeansDenoisingColored(u8, None, h, h, 5, 15)
    return out.astype(np.float32) / 255.0


def hue_pull(rgb, strength=1.0):
    """Shift purple/magenta (250-335 deg) toward cobalt (~228 deg). Skin reds and orange lights stay put."""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)  # float32: H 0-360, S/V 0-1
    h = hsv[..., 0]
    w = smoothstep(238, 262, h) * (1 - smoothstep(318, 342, h)) * strength
    target = 226 + (np.clip(h, 250, 330) - 250) / 80.0 * 16  # 250..330 -> 226..242
    hsv[..., 0] = h * (1 - w) + target * w
    hsv[..., 1] = hsv[..., 1] * (1 - 0.18 * w)  # slightly calmer saturation where we shifted
    return np.clip(cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB), 0, 1)


def tone(rgb, target_median=0.17):
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    lo, hi = np.percentile(lum, 0.4), np.percentile(lum, 99.8)
    x = np.clip((rgb - lo) / max(hi - lo, 1e-3), 0, 1)
    lum2 = x @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    med = max(np.median(lum2), 0.02)
    gamma = np.clip(np.log(target_median) / np.log(med), 0.72, 1.12)
    x = x ** gamma
    # soft S-curve
    x = x + 0.22 * (x - 0.5) * (1 - np.abs(2 * x - 1)) * 0.9
    return np.clip(x, 0, 1)


def split_tone(rgb):
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    sh = ((1 - lum) ** 2.2)[..., None]
    hi = (lum ** 2.0)[..., None]
    rgb = rgb + sh * np.array([-0.012, 0.002, 0.034], dtype=np.float32)   # cobalt in the shadows
    rgb = rgb + hi * np.array([0.020, 0.006, -0.016], dtype=np.float32)   # warm in the lights
    # black floor close to the page background (#08090c)
    floor = np.array([0.028, 0.032, 0.046], dtype=np.float32)
    return np.clip(floor + rgb * (1 - floor), 0, 1)


def vignette(rgb, amt=0.22):
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    return rgb * (1 - amt * smoothstep(0.55, 1.35, d))[..., None]


def dodge(rgb, cx, cy, r, amt):
    """Soft light lift around a point (the face) so the subject separates from the dark room."""
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d2 = ((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)
    return np.clip(rgb * (1 + amt * np.exp(-d2))[..., None], 0, 1)


def grade(path, hue=1.0, nr=3, median=0.17, face=None, lift=1.0):
    rgb = load(path)
    if nr:
        rgb = denoise(rgb, nr)
    rgb = hue_pull(rgb, hue)
    rgb = tone(rgb, median)
    if lift != 1.0:
        rgb = np.clip(rgb * lift, 0, 1)
    if face:
        rgb = dodge(rgb, *face)
    rgb = split_tone(rgb)
    rgb = vignette(rgb)
    return rgb


def to_img(rgb):
    return Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8))
