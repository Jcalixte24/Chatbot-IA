"""
build_index.py
Construit l'index RAG TF-IDF depuis :
1. data/ia_institut_data.json (pages scrapees)
2. MANUAL_DATA (contacts et infos non scrapables)
"""

import json
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer

DATA_FILE = "data/ia_institut_data.json"
INDEX_FILE = "data/index.pkl"
CHUNK_SIZE = 300
CHUNK_OVERLAP = 60

# Donnees manuelles : contacts proteges par Cloudflare et infos cles
MANUAL_DATA = [
    {
        "title": "Contacts officiels de l'IA Institut",
        "url": "https://www.ia-institut.fr/ecole-intelligence-artificielle/contact/",
        "content": """Contacts et responsables de l'IA Institut

Frederic TOUZANNE
Poste : Responsable pedagogique
Telephone : 01 84 07 16 46
Email : f.touzanne@ia-institut.fr

Stella AKPAGNONITE-TALON
Poste : Responsable du developpement commercial
Telephone : 01 84 07 16 47
Email : s.akpagnonite-talon@ia-institut.fr

Adresse :
IA Institut - Campus Paris Sud
14-16 rue Voltaire, 94270 Le Kremlin-Bicetre

Liens utiles :
Prendre RDV : https://www.ia-institut.fr/ecole-intelligence-artificielle/rdv-personnalise/
Documentation : https://www.ia-institut.fr/ecole-intelligence-artificielle/demande-documentation/
Candidature : https://www.ia-institut.fr/admission-ecole-ia/candidature/
"""
    },
    {
        "title": "Reseaux sociaux et contacts digitaux",
        "url": "https://www.ia-institut.fr/",
        "content": """Reseaux sociaux de l'IA Institut :
Facebook : https://www.facebook.com/iainstitut
LinkedIn : https://www.linkedin.com/school/ia-institut/
Instagram : https://www.instagram.com/iainstitut/
Twitter/X : https://twitter.com/iainstitut
YouTube : https://www.youtube.com/@iainstitut

L'IA Institut by EPITA est membre de IONIS Education Group.
Etablissement prive d'enseignement superieur technique.
Inscription au Rectorat de Creteil.
Plus de 40 ans d'expertise via EPITA.
Plus de 2000 entreprises partenaires.
"""
    },
]


def split_into_chunks(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + size])
        if chunk.strip():
            chunks.append(chunk)
        i += size - overlap
    return chunks


def build_index():
    print("=" * 50)
    print("  Construction de l'index RAG")
    print("=" * 50)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_chunks = []

    # 1. Pages scrapees
    for page in data["pages"]:
        if page.get("status") != "success" or not page.get("content"):
            continue
        for chunk in split_into_chunks(page["content"]):
            all_chunks.append({
                "text": chunk,
                "title": page.get("title", ""),
                "url": page.get("url", "")
            })
    print(f"  Scraping  : {len(all_chunks)} chunks")

    # 2. Donnees manuelles
    before = len(all_chunks)
    for item in MANUAL_DATA:
        for chunk in split_into_chunks(item["content"]):
            all_chunks.append({
                "text": chunk,
                "title": item["title"],
                "url": item["url"]
            })
    print(f"  Manuel    : {len(all_chunks) - before} chunks")
    print(f"  Total     : {len(all_chunks)} chunks")

    print("  Vectorisation TF-IDF...")
    texts = [c["text"] for c in all_chunks]
    vectorizer = TfidfVectorizer(
        max_features=15000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1
    )
    matrix = vectorizer.fit_transform(texts)

    os.makedirs("data", exist_ok=True)
    with open(INDEX_FILE, "wb") as f:
        pickle.dump({"chunks": all_chunks, "vectorizer": vectorizer, "matrix": matrix}, f)

    print(f"  Index sauvegarde : {INDEX_FILE}")
    print("=" * 50)


if __name__ == "__main__":
    build_index()