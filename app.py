from datetime import datetime
import re
from flask import Flask, render_template, request, redirect, url_for, session
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from py2neo import Graph
import uuid
from config import ATLAS_URI, DB_NAME, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# Load configuration
import config

app = Flask(__name__)
app.secret_key = 'Secret'

# Set up MongoDB connection
client = MongoClient(ATLAS_URI)
db = client[DB_NAME]

users_collection = db['users']
jobs_collection = db['jobs']

# Set up Neo4j connection
neo4j_graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Verify Databases connection
def verify_connection():
    try:
        db.list_collection_names()
        print("\n------ Connected to MongoDB Atlas successfully ------\n")
    except Exception as e:
        print(f"\n------ Failed to connect to MongoDB: {e} ------\n")
        raise e
    try:
        neo4j_graph.run("RETURN 1 AS test")
        print("\n------ Connected to Neo4j successfully ------\n")
    except Exception as error:
        print(f"\n------ Failed to connect to Neo4j: {error} ------\n")
        raise error

# Verify the MongoDB and Neo4j connections
verify_connection()

def setup():
    """Sets up necessary indexes in MongoDB."""
    try:
        # Check existing indexes
        existing_indexes = jobs_collection.index_information()
        if "job_text_index" not in existing_indexes:
            # Create full-text index if it doesn't already exist
            jobs_collection.create_index([
                ("Job Title", "text"),
                ("Role", "text"),
                ("skills", "text"),
                ("Job Description", "text"),
                ("Company", "text"),
                ("location", "text")
            ], name="job_text_index")
            print("\nFull-text index 'job_text_index' created successfully.\n")
        else:
            print("\nFull-text index 'job_text_index' already exists.\n")

        # # Create geospatial index for latitude and longitude
        # if "job_location_index" not in jobs_collection.index_information():
        #     jobs_collection.create_index([("location", "2dsphere")])
        #     print("\nGeospatial index created successfully.\n")

    except Exception as e:
        print(f"Error creating indexes: {e}")

    
# Run the setup tasks
setup()


# Landing Page (Login/Sign-Up)
@app.route("/", methods=["GET", "POST"])
def landing():
    if request.method == "POST":
        user_id = int(request.form.get("user_id"))  # Convert to integer for matching
        user = users_collection.find_one({"user.user_id": user_id})
        if user:
            session['user_id'] = user_id
            return redirect(url_for("main"))
        else:
            return render_template("landing.html", error="Invalid User ID")
    return render_template("landing.html")

@app.route("/api/skill-demand")
def skill_demand():
    try:
        query = """
        MATCH (j:Job)-[:REQUIRES_SKILL]->(s:Skill)
        RETURN s.name AS skill, COUNT(j) AS demand
        ORDER BY demand DESC LIMIT 10
        """
        result = neo4j_graph.run(query).data()
        return jsonify(result or [])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/job-distribution")
def job_distribution():
    pipeline = [
        {"$group": {"_id": "$Role", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    result = list(jobs_collection.aggregate(pipeline))
    formatted_result = [{"role": r["_id"], "count": r["count"]} for r in result]
    return jsonify(formatted_result)

@app.route("/api/average-salary")
def average_salary():
    pipeline = [
        {"$group": {"_id": "$Work Type", "average_salary": {"$avg": "$Salary Range"}}},
        {"$sort": {"average_salary": -1}}
    ]
    result = list(jobs_collection.aggregate(pipeline))
    formatted_result = [{"work_type": r["_id"], "average_salary": round(r["average_salary"], 2)} for r in result]
    return jsonify(formatted_result)


# Sign-Up
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")  # Password hashing handled elsewhere
        skills = request.form.getlist("skills")
        experience = int(request.form.get("experience"))
        preferred_location = request.form.get("preferred_location")
        work_type = request.form.get("work_type")
        preferred_industry = request.form.get("preferred_industry")
        linkedin_profile = request.form.get("linkedin_profile")
        salary_min = int(request.form.get("salary_min", 0))
        salary_max = int(request.form.get("salary_max", 0))

        # Generate unique User ID
        max_id_doc = users_collection.find_one({}, sort=[("user.user_id", -1)])
        user_id = max_id_doc["user"]["user_id"] + 1 if max_id_doc else 1

        # Insert user into the database
        users_collection.insert_one({
            "user": {
                "user_id": user_id,
                "name": name,
                "email": email,
                "password": password,
                "profile_created_at": datetime.now()
            },
            "user_personal": {
                "skills": skills,
                "experience": experience,
                "preferred_location": preferred_location,
                "work_type": work_type,
                "preferred_industry": preferred_industry,
                "linkedin_profile": linkedin_profile
            },
            "user_job_preferences": {
                "preferred_salary_range": None,
                "preferred_roles": [],
                "upskilling_interest": [],
                "saved_jobs": []
            },
            "user_job_preferences": {
                "preferred_salary_range": {
                    "min": salary_min,
                    "max": salary_max
                },
                "preferred_roles": [],
                "upskilling_interest": [],
                "saved_jobs": []
            }
        })
        
        return render_template("signup.html", success=f"User ID created: {user_id}")
    
    return render_template("signup.html")


# Main Page
@app.route("/main", methods=["GET", "POST"])
def main():
    if 'user_id' not in session:
        return redirect(url_for("landing"))
    
    user = users_collection.find_one({"user.user_id": session['user_id']})
    search_results = []

    # recommendations = neo4j_graph.run("""
    #     MATCH (s:Skill)<-[:REQUIRES_SKILL]-(j:Job)
    #     WHERE s.name IN $skills
    #     RETURN j LIMIT 10
    # """, skills=user["user_personal"]["skills"]).data()

    if request.method == "POST":
        # Perform full-text search
        search_query = request.form.get("search_query")
        search_results = jobs_collection.find({
            "$text": {"$search": search_query}
        }, {"_id": 0, "Job Id": 1, "Job Title": 1, "Company": 1, "location": 1, "Salary Range": 1}).limit(10)

    # Find relevant jobs based on OR filter for user's preferences
    query_criteria = {
        "$or": [
            {"Location": user["user_personal"]["preferred_location"]},
            {"Work Type": user["user_personal"]["work_type"]},
            {"Preferred Industry": user["user_personal"]["preferred_industry"]},
            {"Salary Range": user["user_job_preferences"]["preferred_salary_range"]},
            {"Role": {"$in": user["user_job_preferences"]["preferred_roles"]}},
            {"Skills": {"$in": user["user_job_preferences"]["upskilling_interest"]}}
        ]
    }

    # Fetch jobs and filter for salary range dynamically
    relevant_jobs = []
    salary_min = user["user_job_preferences"]["preferred_salary_range"]["min"]
    salary_max = user["user_job_preferences"]["preferred_salary_range"]["max"]

    for job in jobs_collection.find(query_criteria).limit(30):  
        job_min, job_max = extract_numeric_salary(job.get("Salary Range"))
        if job_min is not None and job_max is not None:
            # Add job if it falls within the user's salary range preference
            if job_max >= salary_min and job_min <= salary_max:
                relevant_jobs.append(job)
        if len(relevant_jobs) >= 20:  # Limit to 20 relevant jobs
            break

    return render_template(
        "main.html",
        user=user,
        search_results=list(search_results),
        relevant_jobs=relevant_jobs
    )

    # return render_template("main.html", user=user, recommendations=recommendations, relevant_jobs=relevant_jobs)

def extract_numeric_salary(salary_range):
    """Extract min and max salary from a string like '$58K–$104K'."""
    if not salary_range:
        return None, None

    try:
        # Use regex to find all numbers in the salary range
        salary_values = re.findall(r'\d+', salary_range)
        if len(salary_values) == 2:
            min_salary = int(salary_values[0]) * 1000  # Convert to full numbers
            max_salary = int(salary_values[1]) * 1000
            return min_salary, max_salary
    except Exception as e:
        print(f"Error parsing salary range: {e}")

    return None, None

# Endpoint for Top 10 Most In-Demand Skills
@app.route("/api/top-skills")
def top_skills():
    query = """
        MATCH (s:Skill)<-[:REQUIRES_SKILL]-(j:Job)
        RETURN s.name AS skill, COUNT(j) AS demand
        ORDER BY demand DESC
        LIMIT 10
    """
    result = neo4j_graph.run(query).data()
    return jsonify(result)

# Endpoint for Top 10 Companies with Most Job Postings
@app.route("/api/top-companies")
def top_companies():
    query = """
        MATCH (c:Company)<-[:POSTED_BY]-(j:Job)
        RETURN c.name AS company, COUNT(j) AS job_count
        ORDER BY job_count DESC
        LIMIT 10
    """
    result = neo4j_graph.run(query).data()
    return jsonify(result)

# Saved Jobs
@app.route("/saved_jobs")
def saved_jobs():
    if 'user_id' not in session:
        return redirect(url_for("landing"))
    
    user = users_collection.find_one({"user.user_id": session['user_id']})
    saved_jobs = jobs_collection.find({"Job Id": {"$in": [int(x) for x user["user_job_preferences"]["saved_jobs"]}})
    return render_template("saved_jobs.html", saved_jobs=saved_jobs)


# Add job to saved jobs
@app.route("/save_job/<job_id>")
def save_job(job_id):
    if 'user_id' not in session:
        return redirect(url_for("landing"))
    
    user = users_collection.find_one({"user.user_id": session['user_id']})
    if job_id not in user["user_job_preferences"]["saved_jobs"]:
        users_collection.update_one(
            {"user.user_id": session['user_id']},
            {"$push": {"user_job_preferences.saved_jobs": job_id}}
        )
    return redirect(url_for("main"))


# Remove job from saved jobs
@app.route("/remove_job/<job_id>")
def remove_job(job_id):
    if 'user_id' not in session:
        return redirect(url_for("landing"))
    
    users_collection.update_one(
        {"user.user_id": session['user_id']},
        {"$pull": {"user_job_preferences.saved_jobs": job_id}}
    )
    return redirect(url_for("saved_jobs"))


# Insights Page
@app.route("/insights")
def insights():
    skill_trends = neo4j_graph.run("""
        MATCH (j:Job)-[:REQUIRES_SKILL]->(s:Skill)
        RETURN s.name AS skill, COUNT(j) AS demand
        ORDER BY demand DESC LIMIT 10
    """).data()

    career_paths = neo4j_graph.run("""
        MATCH (s:Skill)<-[:REQUIRES_SKILL]-(j:Job)-[:LEADS_TO]->(nextJob:Job)
        RETURN nextJob.title AS next_role, COUNT(*) AS frequency
        ORDER BY frequency DESC LIMIT 5
    """).data()

    best_cities = jobs_collection.aggregate([
        {"$group": {"_id": "$location", "job_count": {"$sum": 1}}},
        {"$sort": {"job_count": -1}},
        {"$limit": 10}
    ])

    return render_template("insights.html", skill_trends=skill_trends, career_paths=career_paths, best_cities=best_cities)


# Profile Page
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if 'user_id' not in session:
        return redirect(url_for("landing"))
    
    user = users_collection.find_one({"user.user_id": session['user_id']})
    if request.method == "POST":
        updated_data = {
            "user.name": request.form.get("name"),
            "user_personal.skills": request.form.getlist("skills"),
            "user_personal.experience": int(request.form.get("experience")),
            "user_personal.preferred_location": request.form.get("preferred_location"),
            "user_personal.work_type": request.form.get("work_type"),
            "user_personal.preferred_industry": request.form.get("preferred_industry"),
            "user_personal.linkedin_profile": request.form.get("linkedin_profile"),
            "user_job_preferences.preferred_salary_range.min": int(request.form.get("salary_min", 0)),
            "user_job_preferences.preferred_salary_range.max": int(request.form.get("salary_max", 0)),
        }
        users_collection.update_one({"user.user_id": session['user_id']}, {"$set": updated_data})

        return redirect(url_for("profile"))
    
    return render_template("profile.html", user=user)


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

if __name__ == "__main__":
    app.run(debug=True, port=5001)  # Change 5001 to any available port
 
