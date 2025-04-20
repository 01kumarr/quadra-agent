import pymongo
from pymongo import MongoClient, errors
from datetime import datetime, timezone

class UserDocumentDB:
    def __init__(self, connection_uri="mongodb://localhost:27017", 
                 db_name="Finance_suite", collection_name="Salaried"):
        try:
            self.client = MongoClient(connection_uri)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
            self._create_indexes()
            print("✅ Database connection successful.")
        except errors.ConnectionError as e:
            print("❌ Failed to connect to MongoDB:", e)

    def _create_indexes(self):
        """Create required indexes for fast querying"""
        try:
            indexes = [
                pymongo.IndexModel([("userId", 1)], name="user_id_unique", unique=True, 
                                   partialFilterExpression={"userId": {"$exists": True, "$ne": None}}),
                pymongo.IndexModel([("pan.PAN_number", 1)], name="pan_number_index"),
                pymongo.IndexModel([("aadhar.Aadhar_number", 1)], name="aadhar_number_index"),
                pymongo.IndexModel([("form16.Employee_PAN", 1)], name="form16_pan_index"),
                pymongo.IndexModel([("itr.PAN_number", 1)], name="itr_pan_index")
            ]
            self.collection.create_indexes(indexes)
            print("✅ Indexes created successfully.")
        except errors.OperationFailure as e:
            print("❌ Failed to create indexes:", e)

    # CRUD Operations
    
    def create_user(self, user_id, documents):
        """Create a new user document"""
        if not user_id:
            print("❌ Error: userId cannot be null.")
            return None

        document = {
            "userId": user_id,
            "lastUpdated": datetime.now(timezone.utc),
            **documents
        }

        try:
            result = self.collection.insert_one(document)
            print(f"✅ User {user_id} created successfully.")
            return result.inserted_id
        except errors.DuplicateKeyError:
            print(f"❌ Error: User ID '{user_id}' already exists.")
        except Exception as e:
            print("❌ Unexpected error during insertion:", e)

    def get_user(self, user_id, projection=None):
        """Retrieve a user document"""
        try:
            user = self.collection.find_one({"userId": user_id}, projection)
            if user:
                print(f"✅ User {user_id} retrieved successfully.")
                return user
            else:
                print(f"❌ No user found with ID: {user_id}")
        except Exception as e:
            print("❌ Unexpected error during retrieval:", e)

    def update_document_section(self, user_id, section, data):
        """Update a specific document section"""
        try:
            result = self.collection.update_one(
                {"userId": user_id},
                {"$set": {section: data}, "$currentDate": {"lastUpdated": True}}
            )
            if result.modified_count:
                print(f"✅ {section} updated successfully for User {user_id}.")
            else:
                print(f"⚠️ No updates made for User {user_id}.")
            return result.modified_count
        except Exception as e:
            print("❌ Unexpected error during update:", e)

    def delete_user(self, user_id):
        """Delete a user document"""
        try:
            result = self.collection.delete_one({"userId": user_id})
            if result.deleted_count:
                print(f"✅ User {user_id} deleted successfully.")
            else:
                print(f"⚠️ No user found with ID: {user_id}.")
            return result.deleted_count
        except Exception as e:
            print("❌ Unexpected error during deletion:", e)

    def partial_update(self, user_id, update_dict):
        """Perform a partial update on any document fields"""
        try:
            result = self.collection.update_one(
                {"userId": user_id},
                {"$set": update_dict, "$currentDate": {"lastUpdated": True}}
            )
            if result.modified_count:
                print(f"✅ Partial update successful for User {user_id}.")
            else:
                print(f"⚠️ No updates made for User {user_id}.")
            return result.modified_count
        except Exception as e:
            print("❌ Unexpected error during partial update:", e)

