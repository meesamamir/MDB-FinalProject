import pandas as pd
from py2neo import Graph, Node, Relationship, NodeMatcher
import re

# Step 1: Connect to Neo4j
graph = Graph("bolt://localhost:7687", auth=("neo4j", "TestTest"))

# Step 2: Load the Dataset
dataset_path = r"C:\Users\shahr\Documents\GitHub\MDB-FinalProject\dataset\jobs_10k.csv"
df = pd.read_csv(dataset_path)

# Step 3: Preprocess Skills
def clean_and_split_skills(skills_text):
    """Clean the skills text and split into individual skills."""
    if not isinstance(skills_text, str) or not skills_text.strip():
        return []
    skills_text = re.sub(r"\(.*?\)", "", skills_text)  # Remove text in parentheses
    return [skill.strip() for skill in re.split(r",| and ", skills_text) if skill.strip()]

# Step 4: Extract Key Phrases from Responsibilities
def extract_keywords_from_responsibilities(text):
    """Extract simple keywords/phrases from Responsibilities."""
    if not isinstance(text, str) or not text.strip():
        return []
    phrases = re.split(r",|\.| and ", text)  # Split on commas, periods, or 'and'
    return [phrase.strip() for phrase in phrases if phrase.strip()]

# Step 5: Standardize Roles
def standardize_role(role_text):
    """Standardize job roles by removing unnecessary words."""
    if not isinstance(role_text, str):
        return role_text
    return re.sub(r"[^a-zA-Z0-9\s]", "", role_text).strip()

print("Preprocessing data...")
df['skills_cleaned'] = df['skills'].apply(clean_and_split_skills)
df['Responsibilities_cleaned'] = df['Responsibilities'].apply(extract_keywords_from_responsibilities)
df['Role'] = df['Role'].apply(standardize_role)

# Step 6: Create Nodes and Relationships
print("Creating nodes and relationships...")
matcher = NodeMatcher(graph)

# Create Skill Nodes
skills_set = set()
for skills in df['skills_cleaned']:
    skills_set.update(skills)

for i, skill in enumerate(skills_set, start=1):
    skill_node = Node("Skill", name=skill)
    graph.merge(skill_node, "Skill", "name")
    if i % 100 == 0 or i == len(skills_set):
        print(f"Processed {i}/{len(skills_set)} skills...")

# Create Job Nodes and Relationships
for i, row in df.iterrows():
    # Create Job Node
    job_node = Node(
        "Job",
        job_id=row['Job Id'],
        title=row['Job Title'],
        role=row['Role'],
        company=row['Company'],
        location=row['location']
    )
    graph.merge(job_node, "Job", "job_id")

    # Create REQUIRES_SKILL relationships
    for skill in row['skills_cleaned']:
        skill_node = matcher.match("Skill", name=skill).first()
        if skill_node:
            graph.merge(Relationship(job_node, "REQUIRES_SKILL", skill_node))

    # Create HAS_RESPONSIBILITY relationships
    for resp in row['Responsibilities_cleaned']:
        resp_node = Node("Responsibility", description=resp)
        graph.merge(resp_node, "Responsibility", "description")
        graph.merge(Relationship(job_node, "HAS_RESPONSIBILITY", resp_node))

    # Create Company Nodes and POSTED_BY relationships
    company_node = Node("Company", name=row['Company'])
    graph.merge(company_node, "Company", "name")
    graph.merge(Relationship(job_node, "POSTED_BY", company_node))

    if (i + 1) % 100 == 0 or (i + 1) == len(df):
        print(f"Processed {i+1}/{len(df)} jobs...")

# Step 7: Create IS_SIMILAR_TO Relationships for Skills
print("Creating IS_SIMILAR_TO relationships for similar skills...")
skills_list = list(skills_set)
for i, skill1 in enumerate(skills_list):
    for skill2 in skills_list:
        if skill1 != skill2 and skill1.lower() in skill2.lower():  # Text-based similarity
            node1 = matcher.match("Skill", name=skill1).first()
            node2 = matcher.match("Skill", name=skill2).first()
            if node1 and node2:
                existing_rel = graph.relationships.match((node1, node2), "IS_SIMILAR_TO").first()
                if not existing_rel:
                    graph.create(Relationship(node1, "IS_SIMILAR_TO", node2))
    if (i + 1) % 100 == 0 or i == len(skills_list):
        print(f"Processed {i}/{len(skills_list)} skills for similarity...")


# Step 9: Query - Top 10 Companies with Most Job Postings
print("Retrieving top companies by job postings...")
top_companies_query = """
    MATCH (c:Company)<-[:POSTED_BY]-(j:Job)
    RETURN c.name AS company, COUNT(j) AS job_count
    ORDER BY job_count DESC
    LIMIT 10
"""
top_companies = graph.run(top_companies_query).data()

print("Top 10 Companies with Most Job Postings:")
for company in top_companies:
    print(f"{company['company']}: {company['job_count']} jobs")

print("All relationships created successfully.")
print("Data import and processing complete!")
