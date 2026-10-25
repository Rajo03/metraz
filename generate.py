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
AFFILIATE_FILE = ROOT.parent / "affiliate_links.json"
BLOG_KEY      = "metraz-generator"


def load_data() -> dict:
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_affiliate() -> dict:
    if AFFILIATE_FILE.exists():
        with open(AFFILIATE_FILE, encoding="utf-8") as f:
            return json.load(f).get(BLOG_KEY, {})
    return {}


def inject_affiliate(data: dict, affiliate: dict) -> None:
    """Wstrzykuje linki affiliate do artykułów z pustą tablicą oferty."""
    kategorie = affiliate.get("kategorie", {})
    for kat_slug, artykuly in [("kredyty", data.get("kredyty", [])),
                                ("ubezpieczenia", data.get("ubezpieczenia", [])),
                                ("remonty", data.get("remonty", []))]:
        linki = kategorie.get(kat_slug, [])
        for art in artykuly:
            if not art.get("oferty") and linki:
                art["oferty"] = linki


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


def build_legal_pages(meta, site_url):
    """Strony wymagane przez AdSense: polityka prywatności, o nas, kontakt."""
    name = meta["site_name"]
    desc = meta["description"]
    email = "biuro@fitnesspromo.online"
    css = (
        "*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,sans-serif;background:#f8fafc;color:#1e293b;line-height:1.75}"
        "header{background:#fff;border-bottom:1px solid #e2e8f0;padding:16px 20px}header a{font-weight:800;font-size:20px;color:#0f172a;text-decoration:none}"
        "main{max-width:760px;margin:0 auto;padding:32px 20px 64px}h1{font-size:32px;line-height:1.2;margin:0 0 8px}"
        "h2{font-size:21px;margin:32px 0 8px}p,li{font-size:16px}a{color:#2563eb}"
        ".upd{color:#64748b;font-size:14px;margin-bottom:24px}footer{border-top:1px solid #e2e8f0;padding:24px 20px;text-align:center;font-size:14px;color:#64748b}"
        "footer a{color:#64748b;margin:0 8px}"
    )
    footer = (
        f'<footer><a href="/o-nas/">O nas</a><a href="/kontakt/">Kontakt</a>'
        f'<a href="/polityka-prywatnosci/">Polityka prywatności</a><p>© {date.today().year} {name}</p></footer>'
    )

    def page(slug, title, body):
        html = (
            f'<!DOCTYPE html>\n<html lang="pl">\n<head>\n<meta charset="UTF-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            f'<title>{title} | {name}</title>\n<meta name="description" content="{title} — {name}. {desc}">\n'
            f'<meta name="robots" content="index, follow">\n<link rel="canonical" href="{site_url}/{slug}/">\n'
            f'<!-- Google AdSense -->\n<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9406644927707143"\n'
            f'     crossorigin="anonymous"></script>\n<style>{css}</style>\n</head>\n<body>\n'
            f'<header><a href="/">{name}</a></header>\n<main>\n<h1>{title}</h1>\n{body}\n</main>\n{footer}\n</body>\n</html>\n'
        )
        out = DIST_DIR / slug
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(html, encoding="utf-8")

    today = date.today().isoformat()
    page("polityka-prywatnosci", "Polityka prywatności", f"""
<p class="upd">Ostatnia aktualizacja: {today}</p>
<h2>1. Administrator serwisu</h2>
<p>Administratorem serwisu {name} ({site_url}) jest jego redakcja. Kontakt w sprawach prywatności i danych osobowych: <a href="mailto:{email}">{email}</a>.</p>
<h2>2. Jakie dane zbieramy</h2>
<p>Serwis nie wymaga rejestracji i nie prowadzi kont użytkowników. Podczas korzystania ze strony automatycznie przetwarzane są dane techniczne: adres IP, typ przeglądarki i urządzenia, odwiedzane podstrony, czas wizyty oraz źródło wejścia. Jeśli napiszesz do nas wiadomość e-mail, przetwarzamy Twój adres e-mail i treść wiadomości wyłącznie w celu odpowiedzi.</p>
<h2>3. Pliki cookies i technologie śledzące</h2>
<p>Serwis korzysta z plików cookies i podobnych technologii własnych oraz podmiotów trzecich, w celu analizy ruchu, wyświetlania reklam i rozliczania programów partnerskich. Możesz w każdej chwili usunąć lub zablokować pliki cookies w ustawieniach przeglądarki. Zablokowanie cookies nie uniemożliwia czytania serwisu.</p>
<h2>4. Google Analytics i Google Tag Manager</h2>
<p>Używamy usług Google Analytics i Google Tag Manager do zbierania zbiorczych statystyk odwiedzin. Dane są anonimowe lub pseudonimizowane i służą wyłącznie ulepszaniu serwisu.</p>
<h2>5. Reklamy — Google AdSense i inne sieci reklamowe</h2>
<p>W serwisie wyświetlane są reklamy dostarczane przez Google AdSense oraz inne sieci reklamowe. Dostawcy zewnętrzni, w tym Google, używają plików cookies do wyświetlania reklam na podstawie wcześniejszych odwiedzin użytkownika w tym i innych serwisach. Dzięki plikom cookie reklamowym Google i jego partnerzy mogą wyświetlać reklamy dopasowane do Twoich zainteresowań. Spersonalizowane reklamy możesz wyłączyć w <a href="https://adssettings.google.com" rel="noopener nofollow">Ustawieniach reklam Google</a>. Więcej informacji: <a href="https://policies.google.com/technologies/ads" rel="noopener nofollow">jak Google wykorzystuje dane z witryn partnerów</a>.</p>
<h2>6. Linki afiliacyjne</h2>
<p>Część linków w serwisie to linki afiliacyjne. Jeśli klikniesz taki link i dokonasz zakupu lub zawrzesz umowę u partnera, możemy otrzymać prowizję. Nie zwiększa to ceny, którą płacisz. Linki są oznaczone atrybutem sponsorowanym, a prowizja nie wpływa na treść naszych artykułów.</p>
<h2>7. Twoje prawa</h2>
<p>Zgodnie z RODO masz prawo dostępu do swoich danych, ich sprostowania, usunięcia, ograniczenia przetwarzania, przenoszenia, wniesienia sprzeciwu oraz wniesienia skargi do Prezesa Urzędu Ochrony Danych Osobowych. Aby skorzystać z tych praw, napisz na <a href="mailto:{email}">{email}</a>.</p>
<h2>8. Zmiany polityki</h2>
<p>Możemy aktualizować niniejszą politykę. Aktualna wersja jest zawsze dostępna na tej stronie, a data ostatniej zmiany widnieje na górze.</p>
""")
    page("o-nas", "O nas", f"""
<p>{name} to serwis informacyjny. {desc}</p>
<h2>Cel serwisu</h2>
<p>Zbieramy w jednym miejscu praktyczne informacje, porównania i poradniki, aby ułatwić czytelnikom podejmowanie decyzji. Artykuły mają charakter informacyjny i nie stanowią porady specjalistycznej.</p>
<h2>Jak się utrzymujemy</h2>
<p>Serwis jest bezpłatny dla czytelników. Utrzymujemy go z reklam oraz z prowizji od linków afiliacyjnych. Oznaczamy takie linki i nie pozwalamy, by prowizja decydowała o treści artykułów.</p>
<h2>Błędy i uwagi</h2>
<p>Informacje mogą się zmieniać, a oferty partnerów bywają aktualizowane. Jeśli zauważysz błąd lub nieaktualne dane, napisz do nas: <a href="mailto:{email}">{email}</a>. Poprawiamy zgłoszone nieścisłości.</p>
""")
    page("kontakt", "Kontakt", f"""
<p>Masz pytanie, uwagę do artykułu albo propozycję współpracy? Napisz do nas.</p>
<h2>E-mail</h2>
<p><a href="mailto:{email}">{email}</a></p>
<p>Odpowiadamy zwykle w ciągu kilku dni roboczych. W sprawach dotyczących danych osobowych zobacz <a href="/polityka-prywatnosci/">Politykę prywatności</a>.</p>
""")
    return [f"{site_url}/polityka-prywatnosci/", f"{site_url}/o-nas/", f"{site_url}/kontakt/"]


def build():
    DIST_DIR.mkdir(exist_ok=True)
    data = load_data()
    affiliate = load_affiliate()
    inject_affiliate(data, affiliate)
    sidebar_oferty = affiliate.get("sidebar", [])
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
    html = tmpl_index.render(**data, sidebar_oferty=sidebar_oferty)
    (DIST_DIR / "index.html").write_text(html, encoding="utf-8")
    print("  wygenerowano: dist/index.html")

    # ── Podstrony kredytów ─────────────────────────────────────────
    tmpl_art = env.get_template("artykul.html")
    for art in data.get("kredyty", []):
        out_dir = DIST_DIR / "kredyty" / art["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        html = tmpl_art.render(art=art, meta=meta, base="../../",
                               kategoria="Kredyty hipoteczne", kat_slug="kredyty",
                               sidebar_oferty=sidebar_oferty)
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        sitemap_urls.append(f"{site_url}/kredyty/{art['slug']}/")
    print(f"  wygenerowano: {len(data.get('kredyty',[]))} podstron kredytów")

    # ── Podstrony ubezpieczeń ──────────────────────────────────────
    for art in data.get("ubezpieczenia", []):
        out_dir = DIST_DIR / "ubezpieczenia" / art["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        html = tmpl_art.render(art=art, meta=meta, base="../../",
                               kategoria="Ubezpieczenia nieruchomości", kat_slug="ubezpieczenia",
                               sidebar_oferty=sidebar_oferty)
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        sitemap_urls.append(f"{site_url}/ubezpieczenia/{art['slug']}/")
    print(f"  wygenerowano: {len(data.get('ubezpieczenia',[]))} podstron ubezpieczeń")

    # ── Podstrony remontów ─────────────────────────────────────────
    for art in data.get("remonty", []):
        out_dir = DIST_DIR / "remonty" / art["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        html = tmpl_art.render(art=art, meta=meta, base="../../",
                               kategoria="Remonty i ceny", kat_slug="remonty",
                               sidebar_oferty=sidebar_oferty)
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        sitemap_urls.append(f"{site_url}/remonty/{art['slug']}/")
    print(f"  wygenerowano: {len(data.get('remonty',[]))} podstron remontów")

    sitemap_urls += build_legal_pages(meta, site_url)
    print("  wygenerowano: polityka-prywatnosci, o-nas, kontakt")

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

    # ── ads.txt (AdSense) ──────────────────────────────────────────
    (DIST_DIR / "ads.txt").write_text(
        "google.com, pub-9406644927707143, DIRECT, f08c47fec0942fa0\n", encoding="utf-8"
    )
    print("  wygenerowano: ads.txt")

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
