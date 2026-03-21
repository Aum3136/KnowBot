import os
import json
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import UnstructuredPowerPointLoader
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

load_dotenv()

QDRANT_URL     = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION     = "knowbot"
PROJECTS_FILE  = "projects.json"

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

def get_qdrant_client():
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def ensure_collection():
    """Create Qdrant collection and payload indexes if they don't exist."""
    from qdrant_client.models import PayloadSchemaType

    client = get_qdrant_client()
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION not in existing:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print(f"Created Qdrant collection: {COLLECTION}")

    # Create payload indexes for filtering — required by Qdrant
    try:
        client.create_payload_index(
            collection_name=COLLECTION,
            field_name="metadata.project_id",
            field_schema=PayloadSchemaType.KEYWORD
        )
        print("Created index for metadata.project_id")
    except Exception as e:
        print(f"Index already exists or error: {e}")

    try:
        client.create_payload_index(
            collection_name=COLLECTION,
            field_name="metadata.source",
            field_schema=PayloadSchemaType.KEYWORD
        )
        print("Created index for metadata.source")
    except Exception as e:
        print(f"Index already exists or error: {e}")

def load_documents(folder_path: str):
    """Load all supported documents from a folder."""
    all_docs = []
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return []

    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        try:
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(filepath)
                docs = loader.load()
                print(f"Loaded PDF: {filename} ({len(docs)} pages)")
            elif filename.endswith(".pptx"):
                loader = UnstructuredPowerPointLoader(filepath)
                docs = loader.load()
                print(f"Loaded PPTX: {filename}")
            elif filename.endswith(".xlsx"):
                loader = UnstructuredExcelLoader(filepath)
                docs = loader.load()
                print(f"Loaded XLSX: {filename}")
            else:
                print(f"Skipped: {filename}")
                continue
            all_docs.extend(docs)
        except Exception as e:
            print(f"Error loading {filename}: {e}")

    return all_docs

def ingest_project(project_id: str, project_name: str):
    """
    Ingest all docs from a project folder into Qdrant.
    Each chunk gets project metadata attached.
    """
    folder_path = os.path.join("projects", project_id, "docs")
    print(f"\n--- Ingesting project: {project_name} ({project_id}) ---")

    docs = load_documents(folder_path)
    if not docs:
        print("No documents found.")
        return False

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(docs)
    print(f"Total chunks: {len(chunks)}")

    # Inject project metadata into EVERY chunk
    for chunk in chunks:
        chunk.metadata["project_id"]   = project_id
        chunk.metadata["project_name"] = project_name
        chunk.metadata["source"] = os.path.basename(
            chunk.metadata.get("source", "unknown")
        )

    # Ensure collection exists
    ensure_collection()

    # Upload to Qdrant
    embeddings = get_embeddings()
    QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name=COLLECTION,
    )

    print(f"Uploaded {len(chunks)} chunks to Qdrant for project '{project_name}'")
    return True

def delete_project_vectors(project_id: str):
    """Delete all vectors belonging to a project from Qdrant."""
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    client = get_qdrant_client()
    client.delete(
        collection_name=COLLECTION,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="metadata.project_id",
                    match=MatchValue(value=project_id)
                )
            ]
        )
    )
    print(f"Deleted all vectors for project: {project_id}")

def delete_file_vectors(project_id: str, filename: str):
    """Delete vectors for a specific file within a project."""
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    client = get_qdrant_client()
    client.delete(
        collection_name=COLLECTION,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="metadata.project_id",
                    match=MatchValue(value=project_id)
                ),
                FieldCondition(
                    key="metadata.source",
                    match=MatchValue(value=filename)
                )
            ]
        )
    )
    print(f"Deleted vectors for file: {filename} in project: {project_id}")

if __name__ == "__main__":
    # For testing — ingest all existing projects
    if os.path.exists(PROJECTS_FILE):
        with open(PROJECTS_FILE, "r") as f:
            data = json.load(f)
        for project in data.get("projects", []):
            ingest_project(project["id"], project["name"])
    else:
        print("No projects.json found. Create a project first via the UI.")