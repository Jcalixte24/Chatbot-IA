from flask import Flask, render_template, request, jsonify, session
import uuid
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chatbot import IAChatbot

app = Flask(__name__)
app.secret_key = "ia-institut-2024"
chat_sessions = {}


def get_or_create_chatbot(session_id):
    if session_id not in chat_sessions:
        chat_sessions[session_id] = IAChatbot()
    return chat_sessions[session_id]


@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/overlay")
def overlay():
    """Page d'overlay integrable dans n'importe quel site via iframe."""
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("overlay.html")


@app.route("/embed.js")
def embed_js():
    """Script JS a coller sur le site de l'ecole pour afficher le widget."""
    host = request.host_url.rstrip("/")
    js = f"""
(function() {{
  var btn = document.createElement("div");
  btn.id = "ia-chat-btn";
  btn.innerHTML = "&#128172;";
  btn.style.cssText = "position:fixed;bottom:24px;right:24px;width:56px;height:56px;background:#6B35C8;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:24px;box-shadow:0 4px 20px rgba(107,53,200,0.4);z-index:99999;transition:transform 0.2s";
  btn.onmouseover = function(){{ this.style.transform="scale(1.1)"; }};
  btn.onmouseout  = function(){{ this.style.transform="scale(1)"; }};

  var frame = document.createElement("iframe");
  frame.id = "ia-chat-frame";
  frame.src = "{host}/overlay";
  frame.style.cssText = "position:fixed;bottom:90px;right:24px;width:380px;height:580px;border:none;border-radius:16px;box-shadow:0 8px 40px rgba(0,0,0,0.18);z-index:99998;display:none;transition:opacity 0.2s";

  var open = false;
  btn.onclick = function() {{
    open = !open;
    frame.style.display = open ? "block" : "none";
    btn.innerHTML = open ? "&#10005;" : "&#128172;";
  }};

  document.body.appendChild(frame);
  document.body.appendChild(btn);
}})();
"""
    from flask import Response
    return Response(js, mimetype="application/javascript")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message vide"}), 400
    sid = session.get("session_id", str(uuid.uuid4()))
    reply = get_or_create_chatbot(sid).chat(message)
    return jsonify({"response": reply})


@app.route("/reset", methods=["POST"])
def reset():
    sid = session.get("session_id")
    if sid and sid in chat_sessions:
        del chat_sessions[sid]
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Chatbot demarre sur http://localhost:{port}")
    app.run(debug=False, host="0.0.0.0", port=port)