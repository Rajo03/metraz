#!/usr/bin/env python3
"""
Metraż Static Generator
=======================
Użycie:
    python generate.py

Wymaga:
    pip install jinja2

Efekt:
    Generuje dist/index.html + podstrony artykułów + sitemap.xml
"""

import json
import shutil
from datetime import date
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

ROOT          = Path(__file__).parent
TEMPLATES_DIR = ROOT / "templates"
DIST_DIR      = ROOT / "dist"
DATA_FILE     = ROOT / "artykuly.json"


def load_data() -> dict:
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def clear_expired_promos(data: dict) -> int:
    today = date.today()
    cleared = 0
    for section in ("kredyty", "ubezpieczenia", "remonty"):
        for art in data.get(section, []):
            for oferta in art.get("oferty", []):
                end = oferta.get("promo_end")
                if end:
                    try:
                        if date.fromisoformat(end) < today:
                            del oferta["promo_end"]
                            cleared += 1
                    except ValueError:
                        pass
    return cleared


def copy_assets():
    for folder in ["logos-metraz", "images"]:
        src = ROOT / folder
        dst = DIST_DIR / folder
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"  skopiowano: {folder}/")


def build():
    DIST_DIR.mkdir(exist_ok=True)
    data = load_data()
    meta = data["meta"]
    meta["updated"] = date.today().isoformat()
    site_url = meta["site_url"].rstrip("/")

    n = clear_expired_promos(data)
    if n:
        print(f"  [promo] wyczyszczono {n} wygasłych promocji\n")

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    sitemap_urls = [site_url + "/"]

    # ── Strona główna ──────────────────────────────────────────────
    tmpl_index = env.get_template("index.html")
    html = tmpl_index.render(**data)
    (DIST_DIR / "index.html").write_text(html, encoding="utf-8")
    print("  wygenerowano: dist/index.html")

    # ── Podstrony kredytów ─────────────────────────────────────────
    tmpl_art = env.get_template("artykul.html")
    for art in data.get("kredyty", []):
        out_dir = DIST_DIR / "kredyty" / art["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        html = tmpl_art.render(art=art, meta=meta, base="../../",
                               kategoria="Kredyty hipoteczne", kat_slug="kredyty")
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        sitemap_urls.append(f"{site_url}/kredyty/{art['slug']}/")
    print(f"  wygenerowano: {len(data.get('kredyty',[]))} podstron kredytów")

    # ── Podstrony ubezpieczeń ──────────────────────────────────────
    for art in data.get("ubezpieczenia", []):
        out_dir = DIST_DIR / "ubezpieczenia" / art["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        html = tmpl_art.render(art=art, meta=meta, base="../../",
                               kategoria="Ubezpieczenia nieruchomości", kat_slug="ubezpieczenia")
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        sitemap_urls.append(f"{site_url}/ubezpieczenia/{art['slug']}/")
    print(f"  wygenerowano: {len(data.get('ubezpieczenia',[]))} podstron ubezpieczeń")

    # ── Podstrony remontów ─────────────────────────────────────────
    for art in data.get("remonty", []):
        out_dir = DIST_DIR / "remonty" / art["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        html = tmpl_art.render(art=art, meta=meta, base="../../",
                               kategoria="Remonty i ceny", kat_slug="remonty")
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        sitemap_urls.append(f"{site_url}/remonty/{art['slug']}/")
    print(f"  wygenerowano: {len(data.get('remonty',[]))} podstron remontów")

    # ── Sitemap XML ────────────────────────────────────────────────
    today_str = meta["updated"]
    sitemap  = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in sitemap_urls:
        priority = "1.0" if url == site_url + "/" else "0.8"
        sitemap += f"  <url><loc>{url}</loc><lastmod>{today_str}</lastmod><priority>{priority}</priority></url>\n"
    sitemap += "</urlset>"
    (DIST_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print(f"  wygenerowano: sitemap.xml ({len(sitemap_urls)} URL)")

    # ── robots.txt ─────────────────────────────────────────────────
    robots = (
        "User-agent: *\n"
        "Allow: /\n"
        f"\nSitemap: {site_url}/sitemap.xml\n"
    )
    (DIST_DIR / "robots.txt").write_text(robots, encoding="utf-8")
    print("  wygenerowano: robots.txt")

    # ── _redirects dla Netlify ─────────────────────────────────────
    redirects = (
        "/kredyty/:slug        /kredyty/:slug/index.html        200\n"
        "/ubezpieczenia/:slug  /ubezpieczenia/:slug/index.html  200\n"
        "/remonty/:slug        /remonty/:slug/index.html        200\n"
    )
    (DIST_DIR / "_redirects").write_text(redirects, encoding="utf-8")

    copy_assets()
    print("\nGotowe! Wgraj zawartość folderu dist/ na serwer.")


if __name__ == "__main__":
    print("Metraż Generator — start\n")
    build()
