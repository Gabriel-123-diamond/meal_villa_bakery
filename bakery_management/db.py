from pymongo import MongoClient

def get_mongo_db():
    """
    Connects to the MongoDB database used by the original application.
    """
    client = MongoClient("mongodb://localhost:27017/")
    # This connects to your original database
    db = client['staff_management_db']
    return db

