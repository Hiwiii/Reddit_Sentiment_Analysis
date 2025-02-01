from flask import Flask, jsonify
from sentiment_service import analyze_posts
from dotenv import load_dotenv
import os

# Load environment variables based on the environment
environment = os.getenv("FLASK_ENV", "development")
if environment == "production":
    load_dotenv(".env.production")
else:
    load_dotenv(".env.local")

app = Flask(__name__)


@app.route("/analyze", methods=["GET"])
def get_sentiment_analysis():
    """Fetch posts from MongoDB and perform sentiment analysis."""
    try:
        results = analyze_posts()
        return (
            jsonify({"message": "Sentiment analysis completed!", "results": results}),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
