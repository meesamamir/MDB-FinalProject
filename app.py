from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from py2neo import Graph
import uuid
from config import ATLAS_URI, DB_NAME, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# Load configuration
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

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

verify_connection()
# Set up Neo4j connection


# neo4j_graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

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
    recommendations = neo4j_graph.run("""
        MATCH (s:Skill)<-[:REQUIRES_SKILL]-(j:Job)
        WHERE s.name IN $skills
        RETURN j LIMIT 10
    """, skills=user["user_personal"]["skills"]).data()

    relevant_jobs = jobs_collection.find({"location": user["user_personal"]["preferred_location"]})

    if request.method == "POST":
        search_query = request.form.get("search_query")
        search_results = jobs_collection.find({
            "$text": {"$search": search_query}
        })
        return render_template("main.html", user=user, recommendations=recommendations, relevant_jobs=relevant_jobs, search_results=search_results)

    return render_template("main.html", user=user, recommendations=recommendations, relevant_jobs=relevant_jobs)


# Saved Jobs
@app.route("/saved_jobs")
def saved_jobs():
    if 'user_id' not in session:
        return redirect(url_for("landing"))
    
    user = users_collection.find_one({"user.user_id": session['user_id']})
    saved_jobs = jobs_collection.find({"job_id": {"$in": user["user_job_preferences"]["saved_jobs"]}})
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
            "user_personal.linkedin_profile": request.form.get("linkedin_profile")
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
    app.run(debug=True) 