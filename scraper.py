import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime
from urllib.parse import urljoin

BASE_URL = "https://www.ia-institut.fr"
OUTPUT_FILE = "data/ia_institut_data.json"
DELAY = 1.5

PAGES = [
    "/",
    "/ecole-intelligence-artificielle/",
    "/ecole-intelligence-artificielle/ecoles-partenaires/",
    "/ecole-intelligence-artificielle/advisory-board/",
    "/bachelor-ia-business/",
    "/bachelor-data-ia/",
    "/bachelor-data-engineering-ia/",
    "/master-ia-strategies-marketing/",
    "/master-transformation-digitale-intelligence-artificielle/",
    "/master-intelligence-artificielle-systeme-information/",
    "/admission-ecole-ia/",
    "/admission-ecole-ia/candidature/",
    "/debouches-metiers-intelligence-artificielle/",
    "/debouches-metiers-intelligence-artificielle/temoignages-anciens-etudiants/",
    "/ecole-intelligence-artificielle/nous-rencontrer/",
    "/ecole-intelligence-artificielle/contact/",
    "/programme-grande-ecole/etudier-ia-apres-bac/",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; IA-Institut-Chatbot/1.0)"}


def scrape_page(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        title = ""
        if soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)
        elif soup.find("title"):
            title = soup.find("title").get_text(strip=True)

        meta_desc = ""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            meta_desc = meta.get("content", "")

        for tag in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript"]):
            tag.decompose()

        main = soup.find("main") or soup.find("article") or soup.find("div", id="content")
        text = (main or soup).get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        clean = "\n".join(lines)

        return {
            "url": url,
            "title": title,
            "meta_description": meta_desc,
            "content": clean[:8000],
            "scraped_at": datetime.now().isoformat(),
            "status": "success"
        }
    except Exception as e:
        return {"url": url, "status": "error", "error": str(e), "scraped_at": datetime.now().isoformat()}


def run_scraper():
    print("=" * 50)
    print("Scraper IA Institut - Demarrage")
    print("=" * 50)
    os.makedirs("data", exist_ok=True)
    pages = []
    ok = 0
    for i, path in enumerate(PAGES, 1):
        url = urljoin(BASE_URL, path)
        print(f"[{i}/{len(PAGES)}] {url}")
        data = scrape_page(url)
        pages.append(data)
        if data["status"] == "success":
            ok += 1
            print(f"  OK - {data['title'][:60]}")
        else:
            print(f"  ERREUR - {data.get('error')}")
        if i < len(PAGES):
            time.sleep(DELAY)

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

    print(f"\nTermine ! {ok}/{len(pages)} pages - Donnees dans {OUTPUT_FILE}")


if __name__ == "__main__":
    run_scraper()
