from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType
import os
from dotenv import load_dotenv
from sympy import python

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

COLLECTION = "knowbot"

print("Creating indexes on existing collection...")

try:
    client.create_payload_index(
        collection_name=COLLECTION,
        field_name="metadata.project_id",
        field_schema=PayloadSchemaType.KEYWORD
    )
    print("Index created: metadata.project_id")
except Exception as e:
    print(f"metadata.project_id: {e}")

try:
    client.create_payload_index(
        collection_name=COLLECTION,
        field_name="metadata.source",
        field_schema=PayloadSchemaType.KEYWORD
    )
    print("Index created: metadata.source")
except Exception as e:
    print(f"metadata.source: {e}")

print("Done! Indexes created successfully.")
