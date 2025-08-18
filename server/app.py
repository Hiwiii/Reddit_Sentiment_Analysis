from flask import Flask, jsonify
from dotenv import load_dotenv
import os

# Load environment variables
environment = os.getenv("FLASK_ENV", "development")
load_dotenv(".env.production" if environment == "production" else ".env.local")

app = Flask(__name__)

# Root route
@app.route("/", methods=["GET"])
def home():
    return jsonify(
        status="ok",
        message="Reddit Sentiment Analysis API is running ✅",
        env=environment
    )

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "pong"}), 200

if __name__ == "__main__":
    debug_mode = environment != "production"
    app.run(host="0.0.0.0", port=7500, debug=debug_mode)
