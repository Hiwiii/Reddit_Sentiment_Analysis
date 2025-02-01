from flask import Flask, request, jsonify
from storage_service import store_post
from dotenv import load_dotenv
import os

environment = os.getenv("FLASK_ENV", "development")
load_dotenv(".env.production" if environment == "production" else ".env.local")

app = Flask(__name__)


@app.route("/store", methods=["POST"])
def store_data():
    """Store Reddit posts into MongoDB."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        result = store_post(data)
        return jsonify({"message": "Data stored!", "id": str(result)}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
