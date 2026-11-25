import os
import sqlite3
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, os.getenv("DATABASE_PATH", "generations.db"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "180"))

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                output TEXT NOT NULL,
                model TEXT NOT NULL,
                temperature REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        connection.commit()


def ollama_is_available():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return response.ok
    except requests.RequestException:
        return False


@app.get("/")
def home():
    return render_template("index.html", model_name=MODEL_NAME)


@app.get("/api/health")
def health():
    available = ollama_is_available()
    return jsonify({
        "app": "ok",
        "ollama": "connected" if available else "disconnected",
        "model": MODEL_NAME
    }), (200 if available else 503)


@app.post("/api/generate")
def generate():
    data = request.get_json(silent=True) or {}
    prompt = str(data.get("prompt", "")).strip()
    temperature = data.get("temperature", 0.7)
    max_tokens = data.get("max_tokens", 300)

    if not prompt:
        return jsonify({"error": "Please enter a prompt."}), 400
    if len(prompt) > 5000:
        return jsonify({"error": "Prompt must be 5,000 characters or fewer."}), 400

    try:
        temperature = float(temperature)
        max_tokens = int(max_tokens)
    except (TypeError, ValueError):
        return jsonify({"error": "Temperature and max tokens must be valid numbers."}), 400

    if not 0 <= temperature <= 2:
        return jsonify({"error": "Temperature must be between 0 and 2."}), 400
    if not 32 <= max_tokens <= 2048:
        return jsonify({"error": "Max tokens must be between 32 and 2048."}), 400

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens}
    }

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        output = str(result.get("response", "")).strip()

        if not output:
            return jsonify({"error": "The model returned an empty response. Try another prompt."}), 502

        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with get_db() as connection:
            cursor = connection.execute(
                """INSERT INTO generations
                   (prompt, output, model, temperature, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (prompt, output, MODEL_NAME, temperature, created_at)
            )
            generation_id = cursor.lastrowid
            connection.commit()

        return jsonify({
            "id": generation_id,
            "prompt": prompt,
            "output": output,
            "model": MODEL_NAME,
            "created_at": created_at
        })

    except requests.ConnectionError:
        return jsonify({
            "error": "Cannot connect to Ollama. Start Ollama and make sure it is running on localhost:11434."
        }), 503
    except requests.Timeout:
        return jsonify({"error": "The model took too long to respond. Try a shorter prompt."}), 504
    except requests.HTTPError as exc:
        detail = ""
        try:
            detail = response.json().get("error", "")
        except (ValueError, UnboundLocalError):
            pass
        return jsonify({"error": detail or f"Ollama returned an HTTP error: {exc}"}), 502
    except requests.RequestException as exc:
        return jsonify({"error": f"Model request failed: {exc}"}), 502


@app.get("/api/history")
def history():
    with get_db() as connection:
        rows = connection.execute(
            """SELECT id, prompt, output, model, temperature, created_at
               FROM generations ORDER BY id DESC LIMIT 30"""
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.delete("/api/history/<int:generation_id>")
def delete_history(generation_id):
    with get_db() as connection:
        cursor = connection.execute(
            "DELETE FROM generations WHERE id = ?", (generation_id,)
        )
        connection.commit()
    if cursor.rowcount == 0:
        return jsonify({"error": "Generation not found."}), 404
    return jsonify({"message": "Generation deleted."})


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Endpoint not found."}), 404


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=True)
