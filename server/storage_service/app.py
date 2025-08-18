from flask import Flask, request, jsonify
from storage_service import store_posts  
import os
import database  
from dotenv import load_dotenv  

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env.production" if os.getenv("FLASK_ENV") == "production" else ".env.local"))

app = Flask(__name__)

@app.route("/store-posts", methods=["POST"])
def store_reddit_posts():
    """Endpoint to store Reddit posts in MongoDB."""
    return store_posts()

@app.route("/ping", methods=["GET"])
def ping():
    """Health check endpoint."""
    return jsonify({"message": "Storage Service Pong!"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
