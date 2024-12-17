from pymongo import MongoClient
from neo4j import GraphDatabase

# Connect to MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client['jobfusion']  # MongoDB database
users_collection = db['users']  # MongoDB collection for users

# Connect to Neo4j
neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "neo4jneo4j"))

def create_user_and_saved_jobs(user_data):
    with neo4j_driver.session() as session:
        for user in user_data:
            user_id = user["user"]["user_id"]
            skills = user["user_personal"]["skills"]
            saved_jobs = user["user_job_preferences"]["saved_jobs"]

            # Create User node with user_id and skills
            session.run("""
                MERGE (u:User {user_id: $user_id})
                SET u.skills = $skills
            """, user_id=user_id, skills=skills)

            # Create :SAVED relationships to Jobs
            for job_id in saved_jobs:
                session.run("""
                    MATCH (u:User {user_id: $user_id})
                    MERGE (j:Job {job_id: $job_id})
                    MERGE (u)-[:SAVED]->(j)
                """, user_id=user_id, job_id=job_id)

# Fetch user data from MongoDB
user_data = users_collection.find({})

# Create users and saved jobs relationships in Neo4j
create_user_and_saved_jobs(user_data)

# Close the connection
neo4j_driver.close()

