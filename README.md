# KnowBot — AI-Powered Enterprise Knowledge Assistant

---

## What is KnowBot?

KnowBot is a GenAI-powered enterprise knowledge platform that eliminates the time employees waste searching through scattered internal documents. It lets employees ask natural language questions about company policies, processes, and project documents — and get instant, cited answers.

Built for IT companies, KnowBot combines **RAG-based document intelligence**, **real-time meeting transcription**, and **project-based document management** into a single unified interface.

---

## Features

### Document Q&A
- Ask questions across company documents in natural language
- Answers are cited with source filename and project name
- Supports project-scoped search — ask within a specific project or across all

### Project Management
- Create projects (HR Policies, Engineering, Client — Apprn, etc.)
- Upload PDF, PPTX, and XLSX documents per project
- Rename and delete projects and individual files
- Documents automatically embedded into Qdrant vector database on upload

### Meeting Intelligence (powered by Sarvam AI)
- Live real-time transcription during meetings — transcript appears every 3 seconds
- Supports English (Indian), Hindi, Gujarati, and Marathi etc.
- Auto-generates structured meeting notes on meeting end: Summary, Key Decisions, Action Items, Next Steps
- Upload existing recordings (MP3, WAV, M4A) for post-meeting transcription
- Handles files of any length via automatic chunking

### Slack Integration
- @mention KnowBot in any Slack channel for instant answers
- Direct message support
- Answers include source citations in Slack Block Kit format

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Axios |
| Backend | Python, FastAPI, Uvicorn |
| LLM | Google Gemini 2.5 Flash |
| Vector Database | Qdrant Cloud |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (HuggingFace) |
| RAG Framework | LangChain |
| Speech-to-Text | Sarvam AI (saarika:v2.5) |
| Audio Recording | extendable-media-recorder (WAV) |
| Slack | slack-bolt (Socket Mode) |

---

## Project Structure

```
KnowBot/
├── main.py                  # FastAPI backend — all endpoints
├── rag_chain.py             # RAG chain with Qdrant + Gemini
├── ingest.py                # Document ingestion into Qdrant
├── sarvam_transcribe.py     # Sarvam speech-to-text + meeting notes
├── slack_bot.py             # Slack bot integration
├── projects.json            # Project metadata store
├── projects/                # Per-project document storage
│   └── {project-id}/
│       └── docs/            # Uploaded files
├── requirements.txt
├── .env                     # API keys (never commit)
└── frontend/
    └── src/
        ├── App.jsx          # Main app with chat + meeting tabs
        ├── Projects.jsx     # Projects management screen
        └── App.css          # Styling
```

---

## Setup & Installation

### Prerequisites
- Python 3.11
- Node.js 18+
- Qdrant Cloud account (free at cloud.qdrant.io)
- Google AI Studio API key (free at aistudio.google.com)
- Sarvam AI API key (free at sarvam.ai)
- Slack workspace + app (optional, for Slack integration)

### 1. Clone and set up Python environment

```bash
git clone <repo-url>
cd KnowBot
py -3.11 -m venv venv311
venv311\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key
QDRANT_URL=https://your-cluster.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
SARVAM_API_KEY=your_sarvam_api_key
SLACK_BOT_TOKEN=xoxb-your-token      # optional
SLACK_APP_TOKEN=xapp-your-token      # optional
```

### 3. Set up Qdrant indexes

Run once after first setup:

```bash
python fix_indexes.py
```

### 4. Install and run frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Start the backend

In a separate terminal:

```bash
uvicorn main:app --reload --port 8000
```

### 6. (Optional) Start Slack bot

In a third terminal:

```bash
python slack_bot.py
```

App runs at `http://localhost:5173`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ask` | Ask a question (optional project_id filter) |
| GET | `/projects` | List all projects |
| POST | `/projects` | Create a new project |
| PUT | `/projects/{id}` | Rename a project |
| DELETE | `/projects/{id}` | Delete project + vectors |
| POST | `/projects/{id}/upload` | Upload doc to project |
| DELETE | `/projects/{id}/docs/{filename}` | Delete a document |
| POST | `/meeting/transcribe-chunk` | Live audio chunk transcription |
| POST | `/meeting/end` | End meeting + generate notes |
| POST | `/meeting/transcribe-file` | Transcribe uploaded audio file |

Full interactive API docs available at `http://localhost:8000/docs`

---

## How RAG Works

```
User question
    ↓
Load Qdrant retriever (filtered by project_id if selected)
    ↓
Find top 4 most similar chunks
    ↓
Inject chunks + metadata into Gemini prompt
    ↓
Gemini generates cited answer
    ↓
Return answer + source filenames to UI
```

Each document chunk stored in Qdrant carries:
- `metadata.project_id` — which project it belongs to
- `metadata.project_name` — human-readable project name  
- `metadata.source` — original filename

---

## Supported File Formats

| Format | Document Q&A | Meeting Upload |
|--------|-------------|----------------|
| PDF | ✅ | — |
| PPTX | ✅ | — |
| XLSX | ✅ | — |
| MP3 | — | ✅ |
| WAV | — | ✅ |
| M4A | — | ✅ |

---

## SDG Alignment

**SDG 8 — Decent Work & Economic Growth**
Knowledge workers spend 2.5 hours/day searching for information (McKinsey, 2023). KnowBot recovers that time, directly improving workplace productivity.

**SDG 9 — Industry, Innovation & Infrastructure**
Built on open government AI infrastructure (Sarvam AI — India's own speech model), enabling Indian IT companies to adopt AI without dependency on foreign-only tools.

---

## Startup Vision

KnowBot is positioned as a **SaaS platform for Indian IT SMEs** — targeting the 50,000+ software companies that lack enterprise-grade knowledge management tools.

---

## Team

Built for Solution Challenge 2026 — CSPIT