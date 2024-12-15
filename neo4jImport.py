from neo4j import GraphDatabase
import csv
import json  
import re  
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# File path for jobs CSV file
CSV_FILE_PATH = "jobs_filtered_sampled.csv"

class Neo4jImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def import_jobs(self, csv_file_path):
        with self.driver.session() as session:
            # Check if the data has already been imported
            if session.execute_read(self.is_data_imported, csv_file_path):
                print("Data from this file has already been imported. Skipping import.")
                return
            
            # Mark the dataset as imported
            session.execute_write(self.mark_data_as_imported, csv_file_path)

            with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    # Pre-process and safely parse nested JSON fields (e.g., Company Profile)
                    raw_company_profile = row.get('Company Profile', "{}")
                    cleaned_company_profile = self.clean_mid_sentence_quotes(raw_company_profile)
                    company_profile = self.safe_parse_json(cleaned_company_profile)

                    session.execute_write(self.create_job, row)
                    session.execute_write(self.create_company, row, company_profile)
                    session.execute_write(self.link_job_to_company, row)
                    session.execute_write(self.create_location, row)
                    session.execute_write(self.link_job_to_location, row)

    @staticmethod
    def clean_mid_sentence_quotes(json_string):
        """
        Replace double quotes surrounded by spaces with single quotes in the JSON string.
        Specifically targets patterns like: (SPACE)"Duke"(SPACE).
        """
        # Replace quotes with single quotes when surrounded by spaces
        fixed_json = re.sub(r'\s"([^"]+)"\s', r" '\1' ", json_string)
        return fixed_json

    @staticmethod
    def safe_parse_json(json_string):
        """
        Safely parse a JSON string. If the string is invalid or empty, return an empty dictionary.
        """
        try:
            # Check for empty or malformed JSON and handle gracefully
            if not json_string.strip() or json_string.strip() == "{}":
                return {}
            
            # Attempt to decode the JSON string
            return json.loads(json_string)
        except json.JSONDecodeError:
            print(f"Warning: Failed to decode JSON: {json_string}")
            return {}

    @staticmethod
    def is_data_imported(tx, csv_file_path):
        query = """
        MATCH (d:Dataset {file_path: $file_path})
        RETURN COUNT(d) > 0 AS is_imported
        """
        result = tx.run(query, file_path=csv_file_path).single()
        return result["is_imported"]

    @staticmethod
    def mark_data_as_imported(tx, csv_file_path):
        query = """
        MERGE (d:Dataset {file_path: $file_path})
        SET d.imported_at = datetime()
        """
        tx.run(query, file_path=csv_file_path)

    @staticmethod
    def create_job(tx, row):
        query = """
        MERGE (job:Job {job_id: $job_id})
        SET job.job_title = $job_title,
            job.role = $role,
            job.experience = $experience,
            job.qualifications = $qualifications,
            job.salary_range = $salary_range,
            job.location = $location,
            job.country = $country,
            job.latitude = toFloat($latitude),
            job.longitude = toFloat($longitude),
            job.work_type = $work_type,
            job.company_size = $company_size,
            job.job_posting_date = $job_posting_date,
            job.preference = $preference,
            job.contact_person = $contact_person,
            job.contact = $contact,
            job.job_portal = $job_portal,
            job.job_description = $job_description,
            job.benefits = $benefits,
            job.responsibilities = $responsibilities
        """
        tx.run(query,
               job_id=row['Job Id'],
               job_title=row['Job Title'],
               role=row['Role'],
               experience=row['Experience'],
               qualifications=row['Qualifications'],
               salary_range=row['Salary Range'],
               location=row['location'],
               country=row['Country'],
               latitude=row['latitude'],
               longitude=row['longitude'],
               work_type=row['Work Type'],
               company_size=row['Company Size'],
               job_posting_date=row['Job Posting Date'],
               preference=row['Preference'],
               contact_person=row['Contact Person'],
               contact=row['Contact'],
               job_portal=row['Job Portal'],
               job_description=row['Job Description'],
               benefits=row['Benefits'],
               responsibilities=row['Responsibilities'])

    @staticmethod
    def create_company(tx, row, company_profile):
        query = """
        MERGE (company:Company {name: $company_name})
        SET company.sector = $sector,
            company.industry = $industry,
            company.city = $city,
            company.state = $state,
            company.zipcode = $zipcode,
            company.website = $website,
            company.ticker = $ticker,
            company.ceo = $ceo
        """
        tx.run(query,
               company_name=row['Company'],
               sector=company_profile.get('Sector', None),
               industry=company_profile.get('Industry', None),
               city=company_profile.get('City', None),
               state=company_profile.get('State', None),
               zipcode=company_profile.get('Zip', None),
               website=company_profile.get('Website', None),
               ticker=company_profile.get('Ticker', None),
               ceo=company_profile.get('CEO', None))

    @staticmethod
    def link_job_to_company(tx, row):
        query = """
        MATCH (job:Job {job_id: $job_id})
        MATCH (company:Company {name: $company_name})
        MERGE (job)-[:POSTED_BY]->(company)
        """
        tx.run(query, job_id=row['Job Id'], company_name=row['Company'])

    @staticmethod
    def create_location(tx, row):
        query = """
        MERGE (location:Location {
            city: $city,
            country: $country,
            latitude: toFloat($latitude),
            longitude: toFloat($longitude)
        })
        """
        tx.run(query,
               city=row['location'],
               country=row['Country'],
               latitude=row['latitude'],
               longitude=row['longitude'])

    @staticmethod
    def link_job_to_location(tx, row):
        query = """
        MATCH (job:Job {job_id: $job_id})
        MATCH (location:Location {city: $city, country: $country})
        MERGE (job)-[:LOCATED_IN]->(location)
        """
        tx.run(query, job_id=row['Job Id'], city=row['location'], country=row['Country'])

# Import data
if __name__ == "__main__":
    importer = Neo4jImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    importer.import_jobs(CSV_FILE_PATH)
    importer.close()
    print("Job data imported successfully into Neo4j!")
