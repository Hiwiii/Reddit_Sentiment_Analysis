from flask import Flask, jsonify, request
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Determine environment and load the appropriate .env file
environment = os.getenv("FLASK_ENV", "development")  # Default to 'development'
if environment == "production":
    load_dotenv(".env.production")
else:
    load_dotenv(".env.local")

app = Flask(__name__)

# Get MongoDB URI and other environment variables
MONGO_URI = os.getenv("MONGODB_URI")
CLIENT_ID = os.getenv("CLIENT_ID")
USER_AGENT = os.getenv("USER_AGENT")

# Create a MongoDB client and access the database
client = MongoClient(MONGO_URI)
db = client.reddit_sentiment  # Use 'reddit_sentiment' database


@app.route("/")
def home():
    return "Hello, Reddit Sentiment Analysis!"


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "Pong!"}), 200


# Test route to check environment variables
@app.route("/env")
def show_env():
    return jsonify({"client_id": CLIENT_ID, "user_agent": USER_AGENT})


# Test route to check MongoDB connection
@app.route("/test-mongo", methods=["GET"])
def test_mongo_connection():
    try:
        collections = db.list_collection_names()
        return (
            jsonify(
                {
                    "message": "MongoDB connection successful!",
                    "collections": collections,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to insert a document into MongoDB with dynamic data
@app.route("/add_test", methods=["POST"])
def add_test():
    data = request.get_json()  # Get JSON data from the request body

    if not data:
        return jsonify({"error": "No data provided"}), 400

    result = db.test.insert_one(data)  # Insert data into the 'test' collection
    return jsonify({"message": "Test data added!", "id": str(result.inserted_id)}), 201


# Route to retrieve documents from MongoDB with logging
@app.route("/get_tests", methods=["GET"])
def get_tests():
    data = list(db.test.find({}, {"_id": 0}))  # Retrieve all documents, hide '_id'
    print(f"Retrieved data: {data}")  
    return jsonify(data), 200


# Route to list all collections in the database for debugging
@app.route("/list_collections", methods=["GET"])
def list_collections():
    collections = db.list_collection_names()
    return jsonify({"collections": collections}), 200


if __name__ == "__main__":
    # Run in debug mode only in development
    debug_mode = environment != "production"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
