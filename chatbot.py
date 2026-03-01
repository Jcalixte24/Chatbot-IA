import json
import os
from pathlib import Path
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DATA_FILE = "data/ia_institut_data.json"
MODEL_NAME = "llama-3.3-70b-versatile"


def load_school_data(filepath):
    if not Path(filepath).exists():
        print("ERREUR : Fichier de donnees introuvable. Lance d'abord : python scraper.py")
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    parts = [
        "# " + data["school_name"],
        "Site : " + data["website"],
        "Mise a jour : " + data["scraping_date"][:10],
        ""
    ]
    for page in data["pages"]:
        if page.get("status") != "success":
            continue
        parts.append("## " + page["title"])
        parts.append("URL : " + page["url"])
        if page.get("meta_description"):
            parts.append(page["meta_description"])
        if page.get("content"):
            parts.append(page["content"][:1500])
        parts.append("")
    return "\n".join(parts)


def build_system_prompt(context):
    return (
        "Tu es l'assistant virtuel officiel de l'IA Institut, ecole specialisee en Intelligence Artificielle "
        "et Data Engineering, adossee a l'EPITA.\n"
        "Reponds toujours en francais. Sois accueillant et professionnel.\n"
        "Base-toi uniquement sur les informations ci-dessous.\n"
        "Si une info est absente, dis-le et invite a contacter l'ecole sur ia-institut.fr.\n\n"
        "INFORMATIONS SUR L'ECOLE :\n" + context
    )


class IAChatbot:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("Cle API Groq introuvable. Verifie ta variable d'environnement GROQ_API_KEY.")
        self.client = Groq(api_key=GROQ_API_KEY)
        self.context = load_school_data(DATA_FILE)
        self.system_prompt = build_system_prompt(self.context)
        self.history = []

    def chat(self, user_message):
        try:
            self.history.append({"role": "user", "content": user_message})

            messages = [{"role": "system", "content": self.system_prompt}] + self.history

            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
            )
            reply = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            return "Erreur : " + str(e)