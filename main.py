import os
import json
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from rag_chain import load_rag_chain, get_answer
from sarvam_transcribe import transcribe_chunk, transcribe_file, generate_meeting_notes
from ingest import ingest_project, delete_project_vectors, delete_file_vectors

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

PROJECTS_FILE  = "projects.json"
PROJECTS_DIR   = "projects"
ALLOWED_EXTS   = {".pdf", ".pptx", ".xlsx"}

# In-memory cache for RAG chains per project
rag_cache = {}
meeting_transcripts = {}

def load_projects():
    if not os.path.exists(PROJECTS_FILE):
        return {"projects": []}
    with open(PROJECTS_FILE, "r") as f:
        return json.load(f)

def save_projects(data):
    with open(PROJECTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_rag(project_id: str = None):
    """Get or create RAG chain for a project."""
    key = project_id or "all"
    if key not in rag_cache:
        rag_cache[key] = load_rag_chain(project_id)
    return rag_cache[key]

def invalidate_rag_cache(project_id: str = None):
    """Clear cache when docs change."""
    key = project_id or "all"
    if key in rag_cache:
        del rag_cache[key]
    if "all" in rag_cache:
        del rag_cache["all"]

# ── Models ──
class QuestionRequest(BaseModel):
    question: str
    project_id: str = None   # None = search all projects

class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""

class RenameProjectRequest(BaseModel):
    name: str

class EndMeetingRequest(BaseModel):
    session_id: str
    meeting_type: str = "internal"

# ══════════════════════════════════════
# ── Document Q&A ──
# ══════════════════════════════════════
@app.post("/ask")
async def ask_question(req: QuestionRequest):
    chain_tuple = get_rag(req.project_id)
    answer, sources, _ = get_answer(chain_tuple, req.question)
    return {"answer": answer, "sources": sources}

# ══════════════════════════════════════
# ── Project Management ──
# ══════════════════════════════════════
@app.get("/projects")
async def list_projects():
    data = load_projects()
    return data

@app.post("/projects")
async def create_project(req: CreateProjectRequest):
    data = load_projects()

    # Generate unique ID from name
    project_id = req.name.lower().strip().replace(" ", "-").replace("/", "-")
    project_id = ''.join(c for c in project_id if c.isalnum() or c == '-')

    # Check if already exists
    existing_ids = [p["id"] for p in data["projects"]]
    if project_id in existing_ids:
        raise HTTPException(status_code=400, detail="Project with this name already exists.")

    # Create folders
    docs_folder = os.path.join(PROJECTS_DIR, project_id, "docs")
    os.makedirs(docs_folder, exist_ok=True)

    # Add to projects.json
    new_project = {
        "id": project_id,
        "name": req.name,
        "description": req.description,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "doc_count": 0,
        "docs": []
    }
    data["projects"].append(new_project)
    save_projects(data)

    print(f"Created project: {req.name} ({project_id})")
    return new_project

@app.put("/projects/{project_id}")
async def rename_project(project_id: str, req: RenameProjectRequest):
    data = load_projects()
    for project in data["projects"]:
        if project["id"] == project_id:
            project["name"] = req.name
            save_projects(data)
            invalidate_rag_cache(project_id)
            return project
    raise HTTPException(status_code=404, detail="Project not found.")

@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    data = load_projects()
    project = next((p for p in data["projects"] if p["id"] == project_id), None)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Delete vectors from Qdrant
    try:
        delete_project_vectors(project_id)
    except Exception as e:
        print(f"Vector delete warning: {e}")

    # Delete project folder
    folder = os.path.join(PROJECTS_DIR, project_id)
    if os.path.exists(folder):
        shutil.rmtree(folder)

    # Remove from projects.json
    data["projects"] = [p for p in data["projects"] if p["id"] != project_id]
    save_projects(data)
    invalidate_rag_cache(project_id)

    return {"message": f"Project '{project_id}' deleted successfully."}

@app.post("/projects/{project_id}/upload")
async def upload_to_project(
    project_id: str,
    file: UploadFile = File(...)
):
    data = load_projects()
    project = next((p for p in data["projects"] if p["id"] == project_id), None)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Validate file format
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"File format '{ext}' is not supported. Allowed: PDF, PPTX, XLSX"
        )

    # Save file to project docs folder
    docs_folder = os.path.join(PROJECTS_DIR, project_id, "docs")
    os.makedirs(docs_folder, exist_ok=True)
    file_path = os.path.join(docs_folder, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    print(f"Saved: {file.filename} to project {project_id}")

    # Re-index this project in Qdrant
    success = ingest_project(project_id, project["name"])

    if success:
        # Update metadata
        if file.filename not in project["docs"]:
            project["docs"].append(file.filename)
            project["doc_count"] = len(project["docs"])
        save_projects(data)
        invalidate_rag_cache(project_id)
        return {
            "message": f"{file.filename} uploaded and indexed successfully.",
            "project": project
        }
    else:
        raise HTTPException(status_code=500, detail="Indexing failed.")

@app.delete("/projects/{project_id}/docs/{filename}")
async def delete_document(project_id: str, filename: str):
    data = load_projects()
    project = next((p for p in data["projects"] if p["id"] == project_id), None)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Delete file from disk
    file_path = os.path.join(PROJECTS_DIR, project_id, "docs", filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete vectors from Qdrant
    try:
        delete_file_vectors(project_id, filename)
    except Exception as e:
        print(f"Vector delete warning: {e}")

    # Update metadata
    project["docs"] = [d for d in project["docs"] if d != filename]
    project["doc_count"] = len(project["docs"])
    save_projects(data)
    invalidate_rag_cache(project_id)

    return {"message": f"{filename} deleted from project {project_id}."}

# ══════════════════════════════════════
# ── Meeting Intelligence ──
# ══════════════════════════════════════
@app.post("/meeting/transcribe-chunk")
async def transcribe_meeting_chunk(
    session_id: str = Query(...),
    language: str = Query("en-IN"),
    file: UploadFile = File(...)
):
    audio_bytes = await file.read()
    print(f"[CHUNK] Session: {session_id} | Size: {len(audio_bytes)} bytes")

    chunk_transcript = transcribe_chunk(audio_bytes, language)
    print(f"[CHUNK] Transcript: '{chunk_transcript}'")

    if session_id not in meeting_transcripts:
        meeting_transcripts[session_id] = []

    if chunk_transcript.strip():
        meeting_transcripts[session_id].append(chunk_transcript)

    return {
        "chunk_transcript": chunk_transcript,
        "full_transcript": " ".join(meeting_transcripts.get(session_id, []))
    }

@app.post("/meeting/end")
async def end_meeting(req: EndMeetingRequest):
    session_id = req.session_id
    if session_id not in meeting_transcripts:
        return {"error": "No transcript found for this session."}

    full_transcript = " ".join(meeting_transcripts[session_id])
    if not full_transcript.strip():
        return {"error": "No speech detected during the meeting."}

    notes = generate_meeting_notes(full_transcript, req.meeting_type)
    notes["full_transcript"] = full_transcript
    del meeting_transcripts[session_id]
    return notes

@app.post("/meeting/transcribe-file")
async def transcribe_meeting_file(
    language: str = Query("en-IN"),
    meeting_type: str = Query("internal"),
    file: UploadFile = File(...)
):
    os.makedirs("temp", exist_ok=True)
    path = f"temp/{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())

    transcript = transcribe_file(path, language)
    notes = generate_meeting_notes(transcript, meeting_type)
    notes["full_transcript"] = transcript
    return notes

