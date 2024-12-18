# MDB-FinalProject

JobFusion is a web-based job-matching platform that provides personalized job recommendations and insightful analytics. The system uses two database technologies:
1. MongoDB: For storing user profiles and job postings, supporting full-text search.
2. Neo4j: For graph-based recommendations and analytics, enabling advanced insights into skills, jobs, and career paths.

Users can create detailed profiles, receive personalized job recommendations, search for jobs, save opportunities, and explore analytics such as skill demand trends and best cities for job seekers. The platform focuses on simplicity and utility, ensuring a seamless experience. Original dataset from https://www.kaggle.com/datasets/ravindrasinghrana/job-description-dataset/data
<br/><br/>
This was our final group project for ECE:5845 Modern Databases at the University of Iowa during the Fall 2024 semester.

This group project had three members:
- Meesam Amir Syed
- Kasra Shahrivar
- Eli Paulsen

## to setup and run the app
**Install requirements**
```
pip install flask pymongo py2neo
```

**Setup config variables in config.py**
```
ATLAS_URI = "mongodb://localhost:27017"
DB_NAME = "jobs"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "username"
NEO4J_PASSWORD = "password"
```
**import jobs collection into MongoDB**
```
mongoimport --db jobs --collection jobs --type csv --file jobs_10k.csv --headerline
```
**import mock users into MongoDB**
```
python mock_users.py
```
**setup neo 4j (may take several minutes)**
```
python populate_neo4j.py
```
**setup current saved jobs relationship**
```
python savedImport.py
```

## Run the app
`Make sure Neo4j is running before running the app. The command below starts the Flask development server on http://127.0.0.1:5002`
```
python app.py
```

# Data Flow
### Login
User enters User ID.
MongoDB queries the users database for validation.
On success:
A user session is created.
User is redirected to the Main Page.
### Sign-Up
User fills out the sign-up form.
System generates a unique User ID and stores the profile in MongoDB.
User is redirected to the Main Page with their new ID displayed.

### Search
User enters keywords in the search bar.
MongoDB performs a full-text search on relevant fields, such as:
Job Title
Skills
Job Description
Results are displayed dynamically on the page.

### Analytics
Queries are executed in MongoDB and Neo4j to generate insights, such as:
Skill trends
Career paths
Data is visualized using:
Charts
Maps
Graphs

## Recommendations
User profile details are matched against Neo4j's graph database.
Jobs that other users with similar skills have saved in the past will be recommended to the current user. 

## Saving Jobs
Users can save jobs which creates a :SAVED relationship between user and job node in neo4j, which the app uses to recommend jobs to other users with similar skills. Saved jobs can be viewed or unsaved on the saved_jobs route
