import pymongo
import certifi

MONGO_URL = "mongodb+srv://yr555560_db_user:QApYnHOUPq6cAlHX@cluster0.qzgozqz.mongodb.net/?retryWrites=true&w=majority"

client = pymongo.MongoClient(MONGO_URL, tlsCAFile=certifi.where())
db = client["chatbot_db"]

print("✅ Connected successfully!")
print("Collections:", db.list_collection_names())
