"""
scraper.py
Crawl complet du site ia-institut.fr :
- Decouvre automatiquement toutes les URLs internes
- Scrape chaque page
- Sauvegarde dans data/ia_institut_data.json
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse
from collections import deque

BASE_URL = "https://www.ia-institut.fr"
OUTPUT_FILE = "data/ia_institut_data.json"
DELAY = 1.2
MAX_PAGES = 200  # securite pour ne pas crawler a l'infini

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; IA-Institut-Chatbot/1.0; educational)"
}

# Extensions et patterns a ignorer
IGNORE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
                     ".pdf", ".zip", ".mp4", ".mp3", ".woff", ".woff2", ".css", ".js"}
IGNORE_PATTERNS = ["#", "mailto:", "tel:", "javascript:", "wp-login",
                   "wp-admin", "wp-content", "wp-json", "xmlrpc",
                   "feed", "sitemap", "cdn-cgi", "?s=", "page=",
                   "/tag/", "/category/", "/author/"]


def should_ignore(url):
    parsed = urlparse(url)
    path = parsed.path.lower()
    # Ignore si hors domaine
    if parsed.netloc and parsed.netloc != "www.ia-institut.fr":
        return True
    # Ignore extensions
    for ext in IGNORE_EXTENSIONS:
        if path.endswith(ext):
            return True
    # Ignore patterns
    for pattern in IGNORE_PATTERNS:
        if pattern in url:
            return True
    return False


def normalize_url(url):
    parsed = urlparse(url)
    # Supprimer fragments et query strings inutiles
    clean = parsed._replace(fragment="", query="")
    url_str = clean.geturl()
    # S'assurer que ca finit par /
    if not url_str.endswith("/") and "." not in urlparse(url_str).path.split("/")[-1]:
        url_str += "/"
    return url_str


def extract_links(soup, base_url):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href:
            continue
        full_url = urljoin(base_url, href)
        full_url = normalize_url(full_url)
        parsed = urlparse(full_url)
        # Garder uniquement les pages du meme domaine
        if parsed.netloc == "www.ia-institut.fr" and not should_ignore(full_url):
            links.add(full_url)
    return links


def scrape_page(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()

        # Ignorer les pages non-HTML
        content_type = r.headers.get("content-type", "")
        if "text/html" not in content_type:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        # Titre
        title = ""
        if soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)
        elif soup.find("title"):
            title = soup.find("title").get_text(strip=True).split("|")[0].strip()

        # Meta description
        meta_desc = ""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            meta_desc = meta.get("content", "")

        # Extraire tous les liens avant nettoyage
        discovered_links = extract_links(soup, url)

        # Extraire emails et telephones (avant que Cloudflare les cache)
        phones = []
        emails = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("tel:"):
                phones.append(a.get_text(strip=True))
            elif href.startswith("mailto:"):
                emails.append(href.replace("mailto:", "").strip())

        # Nettoyer le HTML
        for tag in soup(["script", "style", "nav", "footer", "header",
                          "iframe", "noscript", "figure", "img"]):
            tag.decompose()

        # Contenu principal
        main = (soup.find("main") or
                soup.find("article") or
                soup.find("div", class_=lambda c: c and "content" in c.lower()) or
                soup.find("div", id="content") or
                soup)

        text = main.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 2]
        # Dedoublonner les lignes consecutives identiques
        deduped = []
        prev = None
        for line in lines:
            if line != prev:
                deduped.append(line)
            prev = line
        clean = "\n".join(deduped)

        # Ajouter contacts trouves
        if phones:
            clean += "\nTelephones : " + ", ".join(set(phones))
        if emails:
            clean += "\nEmails : " + ", ".join(set(emails))

        return {
            "url": url,
            "title": title,
            "meta_description": meta_desc,
            "content": clean[:10000],
            "scraped_at": datetime.now().isoformat(),
            "status": "success",
            "_links": discovered_links  # temporaire pour le crawl
        }

    except requests.HTTPError as e:
        return {"url": url, "status": "error", "error": f"HTTP {e.response.status_code}", "scraped_at": datetime.now().isoformat(), "_links": set()}
    except Exception as e:
        return {"url": url, "status": "error", "error": str(e), "scraped_at": datetime.now().isoformat(), "_links": set()}


def run_scraper():
    print("=" * 55)
    print("  Crawl complet IA Institut")
    print("=" * 55)
    os.makedirs("data", exist_ok=True)

    visited = set()
    queue = deque([normalize_url(BASE_URL + "/")])
    pages = []
    ok = 0

    while queue and len(visited) < MAX_PAGES:
        url = queue.popleft()

        if url in visited:
            continue
        visited.add(url)

        idx = len(visited)
        print(f"[{idx}] {url}")

        result = scrape_page(url)
        if result is None:
            print("  -> Ignore (non HTML)")
            continue

        # Ajouter les nouvelles URLs decouvertes a la queue
        new_links = result.pop("_links", set())
        for link in new_links:
            if link not in visited:
                queue.append(link)

        pages.append(result)

        if result["status"] == "success":
            ok += 1
            print(f"  OK  [{len(new_links)} liens] - {result['title'][:55]}")
        else:
            print(f"  ERR - {result.get('error')}")

        time.sleep(DELAY)

    # Sauvegarder
    output = {
        "school_name": "IA Institut by EPITA",
        "website": BASE_URL,
        "scraping_date": datetime.now().isoformat(),
        "total_pages": len(pages),
        "success_count": ok,
        "pages": pages
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 55)
    print(f"  Termine : {ok}/{len(pages)} pages scrapees")
    print(f"  Donnees : {OUTPUT_FILE}")
    print("=" * 55)


if __name__ == "__main__":
    run_scraper()