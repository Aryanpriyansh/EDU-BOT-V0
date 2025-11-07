# insert_contact.py
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")

# -----------------------------
# Define admin contact data
# -----------------------------
admin_contact = {
    "name": "Mr. Rajesh Kumar",
    "email": "rajesh.kumar@gat.ac.in"
}

def insert_admin_contact():
    """
    Safely connect to local MongoDB and insert admin contact.
    This function is called manually from main.py after MongoDB is connected.
    """
    try:
        # Local MongoDB → no TLS/SSL
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        db = client["chatbot_db"]
        contacts = db["contacts"]

        contacts.delete_many({})  # clear old entries
        contacts.insert_one(admin_contact)

        print("✅ Admin contact inserted successfully!")
    except Exception as e:
        print("⚠️ Failed to insert admin contact:", e)
