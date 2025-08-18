from flask import Flask, jsonify
from sentiment_service import analyze_posts
from dotenv import load_dotenv
import os

environment = os.getenv("FLASK_ENV", "development")
load_dotenv(".env.production" if environment == "production" else ".env.local")

app = Flask(__name__)

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "Sentiment Service Pong!"}), 200

@app.route("/analyze", methods=["GET"])
def get_sentiment_analysis():
    try:
        results = analyze_posts()
        return jsonify({"message": "Sentiment analysis completed!", "results": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
