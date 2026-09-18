import os

from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv


# Load Cosmos DB settings from the project environment file.
load_dotenv()

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE", "resume-analyzer-db")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER", "analyses")


# Validate required Cosmos DB credentials.
if not COSMOS_ENDPOINT or not COSMOS_KEY:
    raise ValueError("Cosmos DB credentials are missing from .env.")


# Connect to the Cosmos DB account.
client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)


# Create the database only if it does not already exist.
database = client.create_database_if_not_exists(id=COSMOS_DATABASE)


# Create the analysis-history container only if it does not already exist.
container = database.create_container_if_not_exists(id=COSMOS_CONTAINER, partition_key=PartitionKey(path="/id"), offer_throughput=400)


print("Cosmos DB setup successful.")
print("Database:", COSMOS_DATABASE)
print("Container:", COSMOS_CONTAINER)
print("Partition key: /id")