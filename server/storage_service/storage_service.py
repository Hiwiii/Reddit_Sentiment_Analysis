from flask import Flask, jsonify, request
from mongoengine import Document, StringField, connect
from dotenv import load_dotenv
import os

app = Flask(__name__)

# ✅ Load Environment Variables
load_dotenv(".env.production" if os.getenv("FLASK_ENV") == "production" else ".env.local")
MONGO_URI = os.getenv("MONGODB_URI")

# ✅ Connect to MongoDB
connect(db="reddit_sentiment", host=MONGO_URI, alias="default")

# ✅ Define MongoDB Collection Schema
class TestData(Document):
    title = StringField(required=True)
    body = StringField()

# ✅ Insert Test Data on Startup (If DB is empty)
if TestData.objects.count() == 0:
    TestData(title="Startup Test Post", body="Testing MongoDB Connection").save()
    print("✅ MongoDB is connected, and test data is inserted.")

# ✅ Function to Store a New Post (REPLACE YOUR EXISTING FUNCTION)
def store_post(data):
    """Store Reddit post data in MongoDB."""
    try:
        post = TestData(title=data.get("title"), body=data.get("body"))
        post.save()
        print(f"✅ New post inserted: {post.title}")  # Debugging log
        return str(post.id)  # Return MongoDB Object ID as a string
    except Exception as e:
        print(f"❌ Error inserting post: {str(e)}")
        return None

# ✅ API Route to Store Reddit Posts
@app.route("/store", methods=["POST"])
def store_data():
    """Store Reddit posts into MongoDB."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        result = store_post(data)
        if result:
            return jsonify({"message": "Data stored!", "id": result}), 201
        else:
            return jsonify({"error": "Failed to store data"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ API Route to Test MongoDB Connection
@app.route("/test-db-connection", methods=["GET"])
def test_db_connection():
    try:
        collections = connect().list_collection_names()
        return jsonify({"message": "MongoDB connection successful!", "collections": collections}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
