from pymongo import MongoClient
from datetime import datetime
from config import ATLAS_URI, DB_NAME

# MongoDB connection -- IF YOU'RE USING CLOUD VERSION OF MONGODB
client = MongoClient(ATLAS_URI)
db = client[DB_NAME]

# # MongoDB connection -- IF YOU'RE USING LOCAL MONGODB
# client = MongoClient("mongodb://localhost:27017/")
# db = client['db_name']

def verify_connection():
    try:
        db.list_collection_names()
        print("\n------ Connected to MongoDB Atlas successfully ------\n")
    except Exception as e:
        print(f"\n------ Failed to connect to MongoDB: {e} ------\n")
        raise e

verify_connection()

# Check if the 'users' collection already exists
if 'users' in db.list_collection_names():
    print("The 'users' collection already exists. Skipping creation.")
else:
    # Create the 'users' collection with initial data
    users_collection = db['users']

    # Sample users to populate the collection
    sample_users = [
        {
            "user": {
                "user_id": 1,  # Unique, numeric user ID
                "name": "John Doe",
                "email": "johndoe@gmail.com",
                "password": "hashed_password_1",  # Replace with hashed passwords in app.py
                "profile_created_at": datetime.now()
            },
            "user_personal": {
                "skills": ["Python", "SQL", "Machine Learning"],
                "experience": "5",
                "preferred_location": "New York",
                "work_type": "Full-Time",
                "preferred_industry": "Technology",
                "linkedin_profile": "https://linkedin.com/in/johndoe"
            },
            "user_job_preferences": {
                "preferred_salary_range": {
                    "min": 80000,  # Minimum salary as integer
                    "max": 100000  # Maximum salary as integer
                },
                "preferred_roles": ["Data Scientist", "AI Engineer"],
                "upskilling_interest": ["Cloud Computing", "Deep Learning"],
                "saved_jobs": []
            }
        },
        {
            "user": {
                "user_id": 2,
                "name": "Jane Smith",
                "email": "janesmith@gmail.com",
                "password": "hashed_password_2",
                "profile_created_at": datetime.now()
            },
            "user_personal": {
                "skills": ["JavaScript", "React", "Node.js"],
                "experience": "3",
                "preferred_location": "San Francisco",
                "work_type": "Remote",
                "preferred_industry": "Software",
                "linkedin_profile": "https://linkedin.com/in/janesmith"
            },
            "user_job_preferences": {
                "preferred_salary_range": {
                    "min": 80000,  # Minimum salary as integer
                    "max": 100000  # Maximum salary as integer
                },
                "preferred_roles": ["Data Scientist", "AI Engineer"],
                "upskilling_interest": ["Cloud Computing", "Deep Learning"],
                "saved_jobs": []
            }
        }
    ]

    # Insert sample documents into the users collection
    users_collection.insert_many(sample_users)
    print("Users collection established with sample data.")