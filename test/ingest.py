import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import UnstructuredPowerPointLoader
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()  # loads your .env file

DATA_FOLDER = "data/"
VECTORSTORE_PATH = "vectorstore"

def load_documents():
    all_docs = []
    if not os.path.exists(DATA_FOLDER):
        print("ERROR: data/ folder not found. Create it and add documents.")
        return []

    files = os.listdir(DATA_FOLDER)
    if not files:
        print("ERROR: data/ folder is empty. Add PDF, PPTX, or XLSX files.")
        return []

    for filename in files:
        filepath = os.path.join(DATA_FOLDER, filename)
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
                print(f"Skipped unsupported file: {filename}")
                continue
            all_docs.extend(docs)
        except Exception as e:
            print(f"Failed to load {filename}: {e}")

    return all_docs

def build_vectorstore():
    print("\n--- KnowBot Document Ingestion ---")
    docs = load_documents()

    if not docs:
        print("No documents loaded. Exiting.")
        return

    # Split into chunks - 500 chars each with 50 char overlap
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len
    )
    chunks = splitter.split_documents(docs)
    print(f"\nTotal chunks created: {len(chunks)}")

    # Create embeddings using free HuggingFace model (no API key needed)
    print("Creating embeddings (this may take 2-3 minutes first time)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Save to local FAISS database
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(VECTORSTORE_PATH)
    print(f"\nDone! Vector store saved to '{VECTORSTORE_PATH}/'")
    print("You can now run: streamlit run app.py")

if __name__ == "__main__":
    build_vectorstore()