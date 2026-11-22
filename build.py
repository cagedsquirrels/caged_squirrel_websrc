"""
Build the Caged Squirrels website: Markdown pages in content/ -> HTML in public/.

    python build.py                    build the site into public/
    python build.py --sync ../coffee   first copy the game's credits (coffee/assets/CREDITS.md)
                                       into content/credits.md, then build

Preview locally:  python -m http.server -d public   then open http://localhost:8000

Each page in content/ starts with a small header, then Markdown:

    ---
    title: Coffee
    url: /coffee/
    ---
    # Coffee
    ...

Shortcodes you can put on a line of their own in a page:
    {{credits}}       the game credits (content/credits.md), styled like the in-game credits roll
    {{kofi}}          the Ko-fi tip button
    {{screenshots}}   every image in static/img/screenshots/, in name order
    {{devblog}}       every numbered post in content/devblog/ ("01 first.md", "02 ...md"), in number order
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
PUBLIC = ROOT / "public"

SITE_NAME = "Caged Squirrels"
KOFI_URL = "https://ko-fi.com/cagedsquirrels"
NAV = [("Home", "/"), ("Coffee", "/coffee/"), ("Tips", "/tips/"), ("Devblog", "/devblog/")]
DEVBLOG = CONTENT / "devblog"
NUMBERED = re.compile(r"^(\d+)")  # "01 first.md" -> 1

LINE_BREAK = re.compile(r"\s*<br\s*/?>\s*", re.IGNORECASE)
URL = re.compile(r"(https?://[^\s<]+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|io|co\.uk|academy)(?:/[^\s<]*)?)", re.IGNORECASE)


# --- pages -------------------------------------------------------------------
def read_page(path: Path) -> tuple[dict[str, str], str]:
    """
    Split a content file into its header (title, url, ...) and Markdown body.
    :returns: a dictionary of strings and a body
    """
    text = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    if text.startswith("---"):
        _, header, text = text.split("---", 2)
        for line in header.strip().splitlines():
            key, _, value = line.partition(":")
            meta[key.strip().lower()] = value.strip()
    meta.setdefault("title", path.stem.title())
    meta.setdefault("url", "/" if path.stem == "index" else f"/{path.stem}/")
    return meta, text


def output_path(url: str) -> Path:
    """
    / -> public/index.html, /coffee/ -> public/coffee/index.html (so the address has no .html).

    /404/ -> public/404.html, which Cloudflare Pages serves for unknown addresses.
    """
    parts = [part for part in url.split("/") if part]
    if parts == ["404"]:
        return PUBLIC / "404.html"
    return PUBLIC.joinpath(*parts, "index.html")


# --- shortcodes ----------------------------------------------------------------
def linkify(text: str) -> str:
    """
    Escape a line of plain text and turn the web addresses in it into links.
    """
    out, last = [], 0
    for match in URL.finditer(text):
        address = match.group(0).rstrip(".,)")
        out.append(html.escape(text[last : match.start()]))
        href = address if address.startswith("http") else f"https://{address}"
        out.append(f'<a href="{html.escape(href)}">{html.escape(address)}</a>')
        last = match.start() + len(address)
    out.append(html.escape(text[last:]))
    return "".join(out)


def render_credits() -> str:
    """
    content/credits.md as HTML, following the game's rules (coffee/credits_view.py):
    # large amber, ## medium amber, ### large cyan, "- " bullets, <br> breaks, a line of
    only <br> leaves an empty line.
    """
    path = CONTENT / "credits.md"
    if not path.is_file():
        return "<p><em>Credits not found: run <code>python build.py --sync ../coffee</code>.</em></p>"
    parts = ['<div class="credits">']
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            parts.append('<div class="gap"></div>')
            continue
        pieces = LINE_BREAK.split(line)
        if not any(pieces):
            parts.append('<div class="gap"></div>' * (len(pieces) - 1))
            continue
        body = "<br>".join(linkify(piece) for piece in pieces)
        if line.startswith("#"):
            level = min(len(line) - len(line.lstrip("#")), 3)
            body = "<br>".join(linkify(piece.lstrip("#").strip()) for piece in pieces)
            css = {1: "h1", 2: "h2", 3: "h3"}[level]
            parts.append(f'<p class="credit-{css}">{body}</p>')
        elif line.startswith(("- ", "* ")):
            parts.append(f'<p class="credit-item">{body[2:] if body[:2] in ("- ", "* ") else body}</p>')
        else:
            parts.append(f"<p>{body}</p>")
    parts.append("</div>")
    return "\n".join(parts)


def render_kofi() -> str:
    """
    kofi-button
    """
    return (
        f'<p class="kofi"><a class="button" href="{KOFI_URL}" rel="noopener">'
        '<img src="/static/icons/cup.png" alt="" width="32" height="32"> Leave a tip on Ko-fi</a></p>'
    )


def render_screenshots() -> str:
    folder = STATIC / "img" / "screenshots"
    images = sorted(folder.glob("*.png")) if folder.is_dir() else []
    if not images:
        return ""
    figures = []
    for image in images:
        # "3-talking-to-Mia.png" -> "Talking to Mia" (only the first letter is changed)
        caption = re.sub(r"^\d+[-_ ]*", "", image.stem).replace("-", " ").replace("_", " ")
        caption = caption[:1].upper() + caption[1:]
        src = f"/static/img/screenshots/{image.name}"
        figures.append(
            f'<figure><a href="{src}"><img src="{src}" alt="{html.escape(caption)}" loading="lazy"></a>'
            f"<figcaption>{html.escape(caption)}</figcaption></figure>"
        )
    return '<div class="screenshots">' + "".join(figures) + "</div>"


def devblog_posts() -> list[Path]:
    """
    The numbered Markdown files in content/devblog/, in number order (2 comes before 10).
    Files whose names don't start with a number are left out, so drafts can sit there unnumbered.
    """
    if not DEVBLOG.is_dir():
        return []
    posts = [path for path in DEVBLOG.glob("*.md") if NUMBERED.match(path.name)]
    sorted_posts = sorted(posts, key=lambda path: (int(NUMBERED.match(path.name).group(1)), path.name))
    sorted_posts.reverse()
    return sorted_posts


def render_devblog() -> str:
    """
    Every devblog post, one below the other. A post may start with a --- header like a page;
    only its Markdown body is shown.
    """
    posts = devblog_posts()
    if not posts:
        return '<p class="placeholder">No posts yet.</p>'
    parts = ['<div class="devblog">']
    for path in posts:
        _, body = read_page(path)
        number = NUMBERED.match(path.name).group(1)
        content = apply_shortcodes(render_markdown(body), allow_devblog=False)
        parts.append(f'<article class="post" id="post-{number}">\n{content}\n</article>')
    parts.append("</div>")
    return "\n".join(parts)


SHORTCODES = {"credits": render_credits,
              "kofi": render_kofi,
              "screenshots": render_screenshots,
              "devblog": render_devblog}


def render_markdown(body: str) -> str:
    return markdown.markdown(body, extensions=["attr_list", "md_in_html"])


def apply_shortcodes(page_html: str, allow_devblog: bool = True) -> str:
    def replace(match: re.Match) -> str:
        name = match.group(1).lower()
        if name not in SHORTCODES:
            raise SystemExit(f"Unknown shortcode {{{{{name}}}}}")
        if name == "devblog" and not allow_devblog:
            raise SystemExit("{{devblog}} can't be used inside a devblog post")
        return SHORTCODES[name]()

    return re.sub(r"<p>\s*\{\{\s*(\w+)\s*\}\}\s*</p>", replace, page_html)


# --- build -----------------------------------------------------------------------
def render_nav(current_url: str) -> str:
    items = []
    for label, url in NAV:
        here = ' aria-current="page"' if url == current_url else ""
        items.append(f'<a href="{url}"{here}>{label}</a>')
    return "\n".join(items)


def build() -> list[Path]:
    template = (TEMPLATES / "page.html").read_text(encoding="utf-8")
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    shutil.copytree(STATIC, PUBLIC / "static")
    written = []
    for path in sorted(CONTENT.glob("*.md")):
        if path.name == "credits.md":
            continue  # used by the {{credits}} shortcode, not a page of its own
        meta, body = read_page(path)
        content = apply_shortcodes(render_markdown(body))
        title = SITE_NAME if meta["url"] == "/" else f"{meta['title']} - {SITE_NAME}"
        page = (
            template.replace("{{title}}", html.escape(title))
            .replace("{{description}}", html.escape(meta.get("description", "")))
            .replace("{{nav}}", render_nav(meta["url"]))
            .replace("{{content}}", content)
            .replace("{{site_name}}", SITE_NAME)
            .replace("{{kofi_url}}", KOFI_URL)
            .replace("{{year}}", str(date.today().year))
        )
        out = output_path(meta["url"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")
        written.append(out)
    return written


def sync_credits(game_dir: Path) -> None:
    source = game_dir / "coffee" / "assets" / "CREDITS.md"
    if not source.is_file():
        raise SystemExit(f"Can't find the game's credits at {source}")
    shutil.copyfile(source, CONTENT / "credits.md")
    print(f"Copied {source} -> content/credits.md (commit it so the live site gets it)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sync", metavar="GAME_DIR", type=Path, help="copy the credits from the game folder first")
    args = parser.parse_args()
    if args.sync:
        sync_credits(args.sync)
    for path in build():
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    result = main()
    sys.exit(result)
