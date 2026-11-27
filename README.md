# AxonArcadeWeb

The Axon Arcade website: a plain static site (HTML + CSS, no build step) served by GitHub Pages.

Live at **https://axonarcade.github.io/AxonArcadeWeb/** once Pages is turned on.

## Pages

| Path | Page |
|---|---|
| `index.html` | Studio home page with the games list |
| `swipe-mania/index.html` | Swipe Mania: how to play, the 9 levels, screenshots, features |
| `swipe-mania/privacy.html` | Swipe Mania privacy policy (use this URL in the Play Console) |
| `404.html` | Shown by GitHub Pages for any missing path |
| `assets/css/site.css` | All styles, shared by every page |
| `assets/fonts/` | Fredoka, self-hosted (SIL Open Font License, see `OFL-Fredoka.txt`) |
| `assets/img/` | Axon Arcade mark, share image, and one folder per game |

## Preview locally

```sh
python3 -m http.server 8000
# open http://localhost:8000/
```

## Publish with GitHub Pages

1. Push to `main`.
2. On GitHub: **Settings → Pages → Build and deployment**, set Source to **Deploy from a branch**, branch `main`, folder `/ (root)`.
3. The site appears at https://axonarcade.github.io/AxonArcadeWeb/ after a minute or so.

`.nojekyll` tells Pages to serve the files as they are, without running Jekyll.

### If the address changes

Links between pages are relative, so they work at any address. Three things use the full address and need updating if the site moves (for example to `axonarcade.github.io` by renaming the repo to `AxonArcade.github.io`, or to a custom domain):

- `<base href="/AxonArcadeWeb/">` in `404.html`: change it to the new path (`/` for a root domain).
- The `og:image` URLs in `index.html` and `swipe-mania/index.html` (the picture shown when a link is shared).

## Adding a game

1. Copy `swipe-mania/` to a new folder and rewrite the content.
2. Put its images in `assets/img/<game>/`. Screenshots are 540×960 WebP; 1080×1920 game captures can be converted with Pillow or `cwebp -resize 540 960`.
3. Add a `game-card` for it in the Games section of `index.html`, and remove the "More games on the way" box if it no longer fits.
4. Add it to the footer links.

## Swipe Mania assets

The logo, icon and screenshots are copied from the game project (`ui/logo.png`, `icon.svg`, `screenshots/`). If the game's art changes, re-export them here.
