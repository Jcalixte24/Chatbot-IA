"""
chatbot.py
RAG TF-IDF + cache LRU pour eviter les appels redondants au LLM.
"""

import os
import pickle
import hashlib
import numpy as np
from pathlib import Path
from functools import lru_cache
from sklearn.metrics.pairwise import cosine_similarity
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
INDEX_FILE = "data/index.pkl"
MODEL_NAME = "llama-3.3-70b-versatile"
TOP_K = 5
MAX_HISTORY = 8
CACHE_SIZE = 256  # nb de reponses en cache


# Cache global partage entre toutes les sessions
_response_cache = {}


def get_cache_key(query, context):
    """Cle de cache basee sur la question + le contexte RAG."""
    raw = query.strip().lower() + "|" + context[:200]
    return hashlib.md5(raw.encode()).hexdigest()


class RAGRetriever:
    _instance = None  # Singleton : charge l'index une seule fois

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        if not Path(INDEX_FILE).exists():
            raise FileNotFoundError(
                "Index introuvable. Lance : python build_index.py"
            )
        print("Chargement de l'index RAG...")
        with open(INDEX_FILE, "rb") as f:
            index = pickle.load(f)
        self.chunks = index["chunks"]
        self.vectorizer = index["vectorizer"]
        self.matrix = index["matrix"]
        print(f"Index charge : {len(self.chunks)} chunks")

    def retrieve(self, query, top_k=TOP_K):
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [
            {
                "text": self.chunks[i]["text"],
                "title": self.chunks[i]["title"],
                "url": self.chunks[i]["url"],
                "score": float(scores[i])
            }
            for i in top_indices
            if scores[i] > 0.01
        ]


class IAChatbot:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY introuvable dans les variables d'environnement.")
        self.client = Groq(api_key=GROQ_API_KEY)
        self.retriever = RAGRetriever()  # Singleton
        self.history = []

    def chat(self, user_message):
        try:
            # 1. Recuperer les chunks pertinents
            docs = self.retriever.retrieve(user_message, top_k=TOP_K)
            context = "\n\n---\n\n".join(
                f"[{d['title']}]\n{d['text']}"
                for d in docs
            ) if docs else "Aucun extrait pertinent."

            # 2. Verifier le cache
            cache_key = get_cache_key(user_message, context)
            if cache_key in _response_cache:
                cached = _response_cache[cache_key]
                self.history.append({"role": "user", "content": user_message})
                self.history.append({"role": "assistant", "content": cached})
                return cached

            # 3. Prompt systeme
            system_prompt = (
                "Tu es l'assistant virtuel officiel de l'IA Institut, "
                "ecole specialisee en Intelligence Artificielle et Data Engineering, "
                "adossee a l'EPITA.\n"
                "Reponds toujours en francais. Sois accueillant, clair et professionnel.\n"
                "Base-toi sur les extraits ci-dessous pour repondre.\n"
                "Si l'info est absente des extraits, dis-le et invite a contacter "
                "l'ecole (ia-institut.fr ou f.touzanne@ia-institut.fr / 01 84 07 16 46).\n\n"
                "EXTRAITS PERTINENTS :\n" + context
            )

            # 4. Historique limite
            recent = self.history[-(MAX_HISTORY * 2):]
            messages = (
                [{"role": "system", "content": system_prompt}]
                + recent
                + [{"role": "user", "content": user_message}]
            )

            # 5. Appel LLM
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=1024,
                temperature=0.4,
            )
            reply = response.choices[0].message.content

            # 6. Mettre en cache + historique
            if len(_response_cache) >= CACHE_SIZE:
                # Supprimer la premiere entree si cache plein
                oldest = next(iter(_response_cache))
                del _response_cache[oldest]
            _response_cache[cache_key] = reply

            self.history.append({"role": "user", "content": user_message})
            self.history.append({"role": "assistant", "content": reply})

            return reply

        except Exception as e:
            return "Erreur : " + str(e)