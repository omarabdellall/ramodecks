# RAMO press kit

One-page, bilingual (EN / JP) press kit. Plain HTML, CSS and JS. No build step, no framework, no tracking.

```
index.html            the page (all copy lives here, EN and JP side by side)
assets/               css, js, fonts (subset), images, video
press/                downloadable photos, bios, ZIPs
visuals/              wordmark SVG/PNG, LED banner, square + story art, QR codes
_build/               the scripts that made everything (Jekyll ignores this folder on GitHub Pages)
```

## Live site

**https://omarabdellall.github.io/ramodecks/** (repo: `github.com/omarabdellall/ramodecks`). Send Japanese promoters `https://omarabdellall.github.io/ramodecks/?lang=ja`.

**To update the site:** edit the files in this folder, then run

```
git add -A && git commit -m "Update" && git push
```

GitHub rebuilds in about a minute. Anything in `_build/` is not published (GitHub Pages skips folders that start with an underscore).

## Deploy on GitHub Pages (how it was set up)

1. Create a **public** repo on GitHub, for example `ramo`.
2. Upload everything in this folder to the repo root (drag the contents into GitHub's web uploader, or `git init`, `git add .`, `git commit`, `git push`).
3. Repo **Settings → Pages → Build and deployment**: Source = *Deploy from a branch*, Branch = `main`, folder = `/ (root)`. Save.
4. After a minute the site is live at `https://YOUR-USERNAME.github.io/ramo/`.
5. Run `python _build/set_domain.py https://YOUR-USERNAME.github.io/ramo` so the share previews and QR code use the real address, then commit and push again.

## Custom domain (recommended: `ramodj.com`)

`ramodj.com` showed as unregistered when checked on 2026-10-05. `ramo.tokyo`, `ramo.jp`, `ramo.live` and `ramo.club` are taken. Buy `ramodj.com` at any registrar (Cloudflare, Namecheap, Google/Squarespace Domains), then:

1. At the registrar's DNS settings add these records:

   | Type | Host | Value |
   |---|---|---|
   | A | `@` | `185.199.108.153` |
   | A | `@` | `185.199.109.153` |
   | A | `@` | `185.199.110.153` |
   | A | `@` | `185.199.111.153` |
   | CNAME | `www` | `YOUR-USERNAME.github.io` |

   (Optional IPv6: AAAA `@` → `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`.)
2. Run `python _build/set_domain.py https://ramodj.com`. It rewrites the canonical and social tags, adds the `CNAME` file, and regenerates the QR codes and ZIPs.
3. Commit and push. In **Settings → Pages**, enter `ramodj.com` as the custom domain and tick **Enforce HTTPS** once it becomes available (can take up to an hour).
4. Once the domain works, make a booking address on it (`booking@ramodj.com`, via Cloudflare Email Routing for free) and swap it in. It looks better than a Gmail address.

## Things you edit

| What | Where |
|---|---|
| Booking email | `index.html` (search `enygmabiz`: 3 places in `index.html`, plus `_build/make_zips.py`) and `_build/make_zips.py` |
| "Skip to the best part" time | `assets/js/main.js`, top of file: `BEST_PART_MS` (milliseconds) |
| Mix to play | `assets/js/main.js`: `TRACK_URL` (SoundCloud API track URL, see below) |
| Circus Tokyo flyer | save as `assets/img/circus-flyer.webp` (portrait, about 800 px wide). It appears on its own |
| Any text | `index.html`. If you change Japanese text, run `python _build/build_assets.py` so the font subset picks up new characters (the system Japanese font covers any gap meanwhile) |

**Getting a track's API URL:** open `https://soundcloud.com/oembed?format=json&url=<track link>` in a browser and copy the `api.soundcloud.com/tracks/NNN` number out of the `src` in the result.

## Add the three clips

1. Put your reels in a folder.
2. `python _build/make_clips.py /path/to/folder --sheet` makes contact sheets (one frame every 2 s) so you can pick the moments.
3. Edit `CLIPS` at the top of `_build/make_clips.py` (file, start second, length), then `python _build/make_clips.py /path/to/folder`.
4. It writes `assets/video/clip1-3.mp4/.webm` (540×960, silent, under 3 MB each) and poster frames. The page already points at those names.

## Rebuilding assets

```
python3 -m venv venv && source venv/bin/activate
pip install pillow numpy opencv-python-headless "qrcode[pil]" fonttools brotli pillow-avif-plugin
python _build/process_photos.py   # grade + crop photos from _build/source
python _build/make_visuals.py     # wordmark, banners, QR, favicons, OG image
python _build/build_assets.py     # font subsets, inline sprite
python _build/make_zips.py        # press ZIPs + bios.txt
```

Source photos are in `_build/source/` and are git-ignored; remove that line from `.gitignore` if you want them in the repo.

## Notes

- Share preview (Instagram DMs, LINE, email): `assets/img/og.jpg`, 1200×630. After changing the domain, paste the link into the [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/) once to refresh the cache.
- Language: the site opens in Japanese for Japanese browsers and English otherwise. Force one with `?lang=ja` or `?lang=en`. Send Tokyo promoters the `?lang=ja` link.
- Fonts: Archivo, DM Mono, Zen Kaku Gothic New (all SIL Open Font License), subset and self-hosted.
