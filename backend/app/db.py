from pymongo import MongoClient
from app.config import config

# MongoDB Connection usando la configurazione centralizzata
client = MongoClient(config.MONGO_URI)
db = client["EnglishLearning"]

def get_db():
    """Return the database instance."""
    return db
