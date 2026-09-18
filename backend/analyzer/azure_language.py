import os

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv


MAX_AZURE_TEXT_LENGTH = 5000

load_dotenv()

AZURE_LANGUAGE_ENDPOINT = os.getenv("AZURE_LANGUAGE_ENDPOINT")
AZURE_LANGUAGE_KEY = os.getenv("AZURE_LANGUAGE_KEY")


# Create an authenticated Azure AI Language client.
def get_azure_language_client() -> TextAnalyticsClient:
    if not AZURE_LANGUAGE_ENDPOINT or not AZURE_LANGUAGE_KEY:
        raise ValueError(
            "Azure Language credentials are missing. "
            "Check AZURE_LANGUAGE_ENDPOINT and AZURE_LANGUAGE_KEY."
        )

    return TextAnalyticsClient(
        endpoint=AZURE_LANGUAGE_ENDPOINT,
        credential=AzureKeyCredential(AZURE_LANGUAGE_KEY),
    )


# Split long text into Azure-safe chunks.
def chunk_text(text: str, max_length: int = MAX_AZURE_TEXT_LENGTH) -> list[str]:
    text = text.strip()

    if not text:
        return []

    return [
        text[index:index + max_length]
        for index in range(0, len(text), max_length)
    ]


# Extract key phrases from one or more text chunks.
def extract_key_phrases(text: str) -> list[str]:
    chunks = chunk_text(text)

    if not chunks:
        return []

    client = get_azure_language_client()
    phrases = []

    for chunk in chunks:
        response = client.extract_key_phrases([chunk])
        document = response[0]

        if document.is_error:
            raise RuntimeError(
                f"Azure key phrase extraction failed: {document.error}"
            )

        phrases.extend(document.key_phrases)

    return list(dict.fromkeys(phrases))


# Recognize named entities from one or more text chunks.
def recognize_entities(text: str) -> list[dict]:
    chunks = chunk_text(text)

    if not chunks:
        return []

    client = get_azure_language_client()
    entities = []

    for chunk in chunks:
        response = client.recognize_entities([chunk])
        document = response[0]

        if document.is_error:
            raise RuntimeError(
                f"Azure entity recognition failed: {document.error}"
            )

        for entity in document.entities:
            entities.append(
                {
                    "text": entity.text,
                    "category": entity.category,
                    "subcategory": entity.subcategory,
                    "confidence_score": entity.confidence_score,
                }
            )

    return entities


# Return all Azure NLP enrichment for the supplied text.
def analyze_text_with_azure(text: str) -> dict:
    if not text or not text.strip():
        return {
            "key_phrases": [],
            "entities": [],
        }

    return {
        "key_phrases": extract_key_phrases(text),
        "entities": recognize_entities(text),
    }