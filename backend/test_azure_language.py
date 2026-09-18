import os

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient


# Load variables from the .env file
load_dotenv()

endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT")
key = os.getenv("AZURE_LANGUAGE_KEY")


# Check that credentials exist before calling Azure
if not endpoint or not key:
    raise ValueError(
        "Azure Language credentials are missing. "
        "Check AZURE_LANGUAGE_ENDPOINT and AZURE_LANGUAGE_KEY in .env"
    )


# Create the Azure AI Language client
client = TextAnalyticsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)


# Simple resume-style text for our first test
documents = [
    """
    DevOps Engineer with experience in Jenkins, Docker, Linux,
    Git, CI/CD pipelines, Azure, Python, and deployment automation.
    """
]


# Send text to Azure AI Language
response = client.extract_key_phrases(documents)


# Process Azure's response
for document in response:
    if document.is_error:
        print("Azure Language error:")
        print(document.error)
    else:
        print("Azure Language connection successful.")
        print("Key phrases found:")

        for phrase in document.key_phrases:
            print("-", phrase)