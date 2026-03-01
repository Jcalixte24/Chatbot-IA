from flask import Flask, render_template, request, jsonify, session
import uuid
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chatbot import IAChatbot

app = Flask(__name__)
app.secret_key = "ia-institut-2024"
chat_sessions = {}


@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message vide"}), 400
    sid = session.get("session_id", str(uuid.uuid4()))
    if sid not in chat_sessions:
        chat_sessions[sid] = IAChatbot()
    reply = chat_sessions[sid].chat(message)
    return jsonify({"response": reply})


@app.route("/reset", methods=["POST"])
def reset():
    sid = session.get("session_id")
    if sid and sid in chat_sessions:
        del chat_sessions[sid]
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("Chatbot demarre sur http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
