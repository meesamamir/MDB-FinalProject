from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from py2neo import Graph
import uuid

# Load configuration
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Database connections
mongo_client = MongoClient(config.MONGO_URI)
db = mongo_client['jobfusion']
users_collection = db['users']
jobs_collection = db['jobs']

neo4j_graph = Graph(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))

# Landing Page (Login/Sign-Up)
@app.route("/", methods=["GET", "POST"])
def landing():
    if request.method == "POST":
        user_id = request.form.get("user_id")
        user = users_collection.find_one({"user_id": user_id})
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
        skills = request.form.getlist("skills")
        experience = int(request.form.get("experience"))
        preferred_location = request.form.get("preferred_location")
        work_type = request.form.get("work_type")

        user_id = str(uuid.uuid4())[:8]  # Generate unique User ID
        users_collection.insert_one({
            "user_id": user_id,
            "name": name,
            "skills": skills,
            "experience": experience,
            "preferred_location": preferred_location,
            "work_type": work_type,
            "saved_jobs": []
        })
        return render_template("signup.html", success=f"User ID created: {user_id}")
    return render_template("signup.html")


# Main Page
@app.route("/main", methods=["GET", "POST"])
def main():
    if 'user_id' not in session:
        return redirect(url_for("landing"))
    
    user = users_collection.find_one({"user_id": session['user_id']})
    recommendations = neo4j_graph.run("""
        MATCH (u:User {id: $user_id})-[:HAS_SKILL]->(s:Skill)<-[:REQUIRES_SKILL]-(j:Job)
        RETURN j LIMIT 10
    """, user_id=session['user_id']).data()

    relevant_jobs = jobs_collection.find({"location": user['preferred_location']})

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
    
    user = users_collection.find_one({"user_id": session['user_id']})
    saved_jobs = jobs_collection.find({"job_id": {"$in": user['saved_jobs']}})
    return render_template("saved_jobs.html", saved_jobs=saved_jobs)

# Add job to saved jobs
@app.route("/save_job/<job_id>")
def save_job(job_id):
    if 'user_id' not in session:
        return redirect(url_for("landing"))
    
    user = users_collection.find_one({"user_id": session['user_id']})
    if job_id not in user['saved_jobs']:
        users_collection.update_one({"user_id": session['user_id']}, {"$push": {"saved_jobs": job_id}})
    return redirect(url_for("main"))

# Remove job from saved jobs
@app.route("/remove_job/<job_id>")
def remove_job(job_id):
    if 'user_id' not in session:
        return redirect(url_for("landing"))
    
    user = users_collection.find_one({"user_id": session['user_id']})
    if job_id in user['saved_jobs']:
        users_collection.update_one({"user_id": session['user_id']}, {"$pull": {"saved_jobs": job_id}})
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
        MATCH (u:User {id: $user_id})-[:HAS_SKILL]->(s:Skill)<-[:REQUIRES_SKILL]-(j:Job)-[:LEADS_TO]->(nextJob:Job)
        RETURN nextJob.title AS next_role, COUNT(*) AS frequency
        ORDER BY frequency DESC LIMIT 5
    """, user_id=session['user_id']).data()

    best_cities = jobs_collection.aggregate([
        {"$group": {"_id": "$location", "job_count": {"$sum": 1}}},
        {"$sort": {"job_count": -1}},
        {"$limit": 5}
    ])

    return render_template("insights.html", skill_trends=skill_trends, career_paths=career_paths, best_cities=best_cities)


# Profile Page
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if 'user_id' not in session:
        return redirect(url_for("landing"))
    
    user = users_collection.find_one({"user_id": session['user_id']})
    if request.method == "POST":
        updated_data = {
            "name": request.form.get("name"),
            "skills": request.form.getlist("skills"),
            "experience": int(request.form.get("experience")),
            "preferred_location": request.form.get("preferred_location"),
            "work_type": request.form.get("work_type")
        }
        users_collection.update_one({"user_id": session['user_id']}, {"$set": updated_data})
        return redirect(url_for("profile"))
    return render_template("profile.html", user=user)

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))
