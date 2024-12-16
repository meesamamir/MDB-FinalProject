import pandas as pd
from py2neo import Graph, Node, Relationship, NodeMatcher
import re

# Step 1: Connect to Neo4j
graph = Graph("bolt://localhost:7687", auth=("neo4j", "Apples123z?"))

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

    if (i + 1) % 100 == 0 or (i + 1) == len(df):
        print(f"Processed {i+1}/{len(df)} jobs...")

# Step 7: Dynamically Create LEADS_TO Relationships
print("Inferring LEADS_TO relationships dynamically...")
roles = list(df['Role'].dropna().unique())
hierarchical_keywords = ["Junior", "Mid", "Senior", "Lead", "Manager", "Director"]

for i, role1 in enumerate(roles, start=1):
    for role2 in roles:
        # Check if role1 logically progresses to role2
        role1_lower, role2_lower = role1.lower(), role2.lower()
        if any(k1 in role1_lower and k2 in role2_lower for k1, k2 in zip(hierarchical_keywords, hierarchical_keywords[1:])):
            job1_nodes = matcher.match("Job", role=role1)
            job2_nodes = matcher.match("Job", role=role2)
            for job1 in job1_nodes:
                for job2 in job2_nodes:
                    # Avoid creating duplicate relationships
                    existing_rel = graph.relationships.match((job1, job2), "LEADS_TO").first()
                    if not existing_rel:
                        graph.create(Relationship(job1, "LEADS_TO", job2))
            print(f"LEADS_TO: {role1} → {role2}")
    if i % 10 == 0:
        print(f"Processed {i}/{len(roles)} roles...")

# Step 8: Create IS_SIMILAR_TO Relationships for Skills
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

print("All relationships created successfully.")
print("Data import and processing complete!")
