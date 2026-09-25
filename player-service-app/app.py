import ollama
import pandas as pd
from flask import Flask, jsonify
from sqlalchemy import create_engine

from app_paths import PLAYER_CSV, PLAYER_DB
from player_service import PlayerService

app = Flask(__name__)


def ensure_player_db() -> None:
    if PLAYER_DB.exists():
        return
    df = pd.read_csv(PLAYER_CSV)
    engine = create_engine(f"sqlite:///{PLAYER_DB}", echo=False)
    df.to_sql("players", con=engine, if_exists="replace", index=False)


ensure_player_db()


@app.route("/v1/players", methods=["GET"])
def get_players():
    player_service = PlayerService()
    result = player_service.get_all_players()
    return result


@app.route("/v1/players/<string:player_id>")
def query_player_id(player_id):
    player_service = PlayerService()
    result = player_service.search_by_player(player_id)

    if len(result) == 0:
        return jsonify({"error": "No record found with player_id={}".format(player_id)})
    else:
        return jsonify(result)


@app.route("/v1/chat/list-models")
def list_models():
    try:
        return jsonify(ollama.list())
    except Exception as exc:
        return jsonify(
            {
                "error": "Ollama is unavailable. Start the Ollama container and pull tinyllama.",
                "detail": str(exc),
            }
        ), 503


@app.route("/v1/chat", methods=["POST"])
def chat():
    try:
        response = ollama.chat(
            model="tinyllama",
            messages=[
                {
                    "role": "user",
                    "content": "Why is the sky blue?",
                },
            ],
        )
        return jsonify(response), 200
    except Exception as exc:
        return jsonify(
            {
                "error": "Ollama chat failed. Ensure tinyllama is pulled and Ollama is running on port 11434.",
                "detail": str(exc),
            }
        ), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
