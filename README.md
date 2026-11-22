# Caged Squirrels website

Static site for cagedsquirrels.co.uk: the studio home page, the Coffee game page and a tips page.
Pages are written in Markdown and turned into plain HTML by `build.py`; no JavaScript.

| Address    | Source              |
|------------|---------------------|
| `/`        | `content/index.md`  |
| `/coffee/` | `content/coffee.md` |
| `/tips/`   | `content/tips.md`   |
| `/devblog/`| `content/devblog.md` + the posts in `content/devblog/` |
| 404 page   | `content/404.md`    |

## Preview locally

```
python -m pip install -r requirements.txt
(or use a venv?)

python build.py --sync ../coffee
(this updates the credits)

python -m http.server -d public

```

Then open http://localhost:8000. `public/` is rebuilt from scratch each time and isn't committed.

## Editing

- **Text:** edit the `.md` files in `content/`. Each starts with a small header (`title`, `url`,
  `description`) between `---` lines.
- **Shortcodes**, on a line of their own:
  - `{{kofi}}` - the Ko-fi tip button (the address is `KOFI_URL` in `build.py`)
  - `{{screenshots}}` - every PNG in `static/img/screenshots/`, in file-name order; the caption
    comes from the name (`3-talking-to-Mia.png` -> "Talking to Mia")
  - `{{credits}}` - the game credits, styled like the in-game credits roll
  - `{{devblog}}` - every devblog post, one below the other (used by `content/devblog.md`)
- **Devblog posts:** one Markdown file per post in `content/devblog/`, named with a number first
  (`01 first.md`, `02 new engine.md`, ...). They appear in number order, so `2` comes before `10`.
  A file without a number at the start is skipped, which is handy for drafts. A `---` header in a
  post is allowed but ignored.
- **Look:** `static/css/style.css`. Keep the m6x11 pixel font at 16, 32 or 48 px so it stays sharp.
- **Shared parts** (header, navigation, footer): `templates/page.html`. Navigation links are `NAV`
  in `build.py`.

## Things that come from the game

The game repo is private, so copies live here and are committed:

- **Credits:** `content/credits.md` is a copy of the game's `coffee/assets/CREDITS.md`. Refresh it with
  `python build.py --sync ../coffee`, then commit it.
- **Screenshots:** in the game folder run `python tools/website_screenshots.py`. It writes
  `static/img/hero.png`, `static/img/coffee-card.png` and `static/img/screenshots/*.png` into this
  folder (it expects `website` next to `coffee`). Commit the new images.

## Publishing on Cloudflare Pages

```
git add *
git commit -m <changes reason>
git push
```
1. Push this folder to its own git repo.
2. In the Cloudflare dashboard: **Workers & Pages > Create > Pages > Connect to Git**, pick the repo.
3. Build settings:
   - Framework preset: **None**
   - Build command: `pip install -r requirements.txt && python build.py`
   - Build output directory: `public`
   - Environment variable: `PYTHON_VERSION` = `3.12`
4. Save and deploy. Every push to the main branch redeploys the site.
5. **Custom domains > Set up a domain:** `cagedsquirrels.co.uk` (and `www.` if wanted). Cloudflare
   shows the DNS record to add.

The game's globe icon opens `https://cagedsquirrels.co.uk/coffee`, which this site serves.

## Credits for the site itself

Pixel font m6x11 by Daniel Linssen (free with attribution; credited in the footer).
The coffee-cup icon (`static/icons/cup.png`) was drawn for this site.
