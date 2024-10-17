from flask import Flask, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)

# Get MongoDB URI from environment variable (set in docker-compose.yml)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/reddit_sentiment")

# Create a MongoDB client and access the database
client = MongoClient(MONGO_URI)
# Use 'reddit_sentiment' database
db = client.reddit_sentiment


@app.route("/")
def home():
    return "Hello, Reddit Sentiment Analysis!"


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "Pong!"}), 200


# Test route to insert a document into MongoDB
@app.route("/add_test", methods=["POST"])
def add_test():
    """Insert a test document to verify the MongoDB connection."""
    db.test.insert_one({"name": "Reddit", "status": "active"})
    return jsonify({"message": "Test data added!"}), 201


# Test route to retrieve documents from MongoDB
@app.route("/get_tests", methods=["GET"])
def get_tests():
    """Retrieve documents from the test collection."""
    # Hide the '_id' field in results
    data = list(db.test.find({}, {"_id": 0}))
    return jsonify(data), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
