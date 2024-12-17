import random
from faker import Faker
from pymongo import MongoClient
from datetime import datetime

# Initialize Faker and MongoDB client
fake = Faker()
client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB connection string
db = client['jobs']  # Replace with your database name
users_collection = db['users']  # Replace with your user collection name
jobs_collection = db['jobs']  # Replace with your job collection name


print("Populating jobs collection...")
cities = jobs_collection.distinct("location")
job_ids = [str(x["Job Id"]) for x in jobs_collection.find({"Country": "USA"}, {"Job Id": 1})]

# Step 2: Generate mock users with saved jobs referencing job IDs
def create_mock_user(id):
    return {
        "user": {
            "user_id": id,
            "name": fake.name(),
            "email": fake.email(),
            "password": fake.password(length=10),
            "profile_created_at": datetime.utcnow()
        },
        "user_personal": {
            "skills": random.sample(['Python', 'SQL', 'Java', 'C++', 'JavaScript', 'HTML', 'CSS'], k=random.randint(1, 4)),
            "experience": random.randint(1, 40),  # Experience in years
            "preferred_location": random.choice(cities),
            "work_type": random.choice(['Full-Time', 'Part-Time', 'Remote', 'Contract']),
            "preferred_industry": random.choice(['Tech', 'Finance', 'Healthcare', 'Education', 'Retail']),
            "linkedin_profile": fake.url()
        },
        "user_job_preferences": {
            "preferred_salary_range": {
                "min": random.randint(50000, 100000),
                "max": random.randint(110000, 200000)
            },
            "preferred_roles": random.sample(['Software Engineer', 'Data Scientist', 'Manager', 'Consultant'], k=random.randint(0, 3)),
            "upskilling_interest": random.sample(['AI', 'Cloud Computing', 'Machine Learning', 'Blockchain'], k=random.randint(0, 2)),
            "saved_jobs": random.sample(job_ids, k=random.randint(1, 5))  # Randomly pick job IDs
        }
    }

print("Populating users collection...")
users_collection.drop()  # Clear existing users (optional)
mock_users = [create_mock_user(id) for id in range(0, 1000)]
users_collection.insert_many(mock_users)

print("Mock data generated successfully.")
