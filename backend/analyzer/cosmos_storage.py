import os
import uuid
from datetime import datetime, timezone

from azure.cosmos import CosmosClient
from dotenv import load_dotenv


# Load Cosmos DB configuration from environment variables.
load_dotenv()

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE", "resume-analyzer-db")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER", "analyses")


# Create and return the configured Cosmos container client.
def get_cosmos_container():
    if not COSMOS_ENDPOINT or not COSMOS_KEY:
        raise ValueError("Cosmos DB credentials are missing.")
    client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
    database = client.get_database_client(COSMOS_DATABASE)
    return database.get_container_client(COSMOS_CONTAINER)


# Build a Cosmos-safe analysis-history document.
def build_analysis_document(filename, resume, resume_quality, ats, jd, jd_match, recommendations):
    return {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "candidate_name": resume.get("name"),
        "resume_filename": filename,
        "job_title": jd.get("job_title"),
        "resume_score": resume_quality,
        "ats_score": ats.get("score"),
        "job_match_score": jd_match.get("match_score"),
        "matched_skills": jd_match.get("matched_skills", []),
        "missing_skills": jd_match.get("missing_skills", []),
        "critical_missing_skills": jd_match.get("critical_missing_skills", []),
        "required_skill_breakdown": jd_match.get("required_skill_breakdown", {}),
        "preferred_skill_breakdown": jd_match.get("preferred_skill_breakdown", {}),
        "experience_match": jd_match.get("experience_match", {}),
        "role_match": jd_match.get("role_match", {}),
        "keyword_match": jd_match.get("keyword_match"),
        "keyword_match_details": jd_match.get("keyword_match_details", {}),
        "score_explanations": jd_match.get("score_explanations", {}),
        "recommendations": recommendations,
    }


# Save one completed analysis result in Cosmos DB.
def save_analysis(document):
    container = get_cosmos_container()
    return container.upsert_item(document)

# Retrieve one analysis by its unique ID.
def get_analysis(analysis_id):
    container = get_cosmos_container()
    return container.read_item(item=analysis_id, partition_key=analysis_id)


# Retrieve recent analysis history ordered by creation time.
def get_analysis_history(limit=10):
    container = get_cosmos_container()
    query = "SELECT * FROM c ORDER BY c.created_at DESC"
    items = container.query_items(query=query, enable_cross_partition_query=True)
    return list(items)[:limit]