# NashmiBot

NashmiBot is a bilingual (Arabic/English) government-grade RAG assistant for Jordan Vision 2033, built with:

- Backend: FastAPI + SQLAlchemy (SQLite) + LangChain
- Retrieval: Vertex AI Vector Search (semantic) + BM25 (keyword)
- LLM: Vertex AI Gemini (primary) with Groq Llama 70B fallback
- Frontend: Next.js (App Router) + Tailwind

Workers: Karam Balasmeh, Ali Tamimi

## Key Features

- User login + registration (JWT sessions via httpOnly cookie on the frontend)
- Saved conversations per user (sidebar history)
- Conversation memory for follow-ups (last turns are passed as context)
- HITL escalation tickets + admin dashboard to resolve
- Resolved answer reuse (cross-user cache for previously approved answers)
- Arabic + English chat:
  - Answers follow the user's language
  - If Arabic retrieval is weak, the query is translated to English for retrieval (generation stays Arabic)
- User-selectable LLM provider in the UI:
  - `auto` (Vertex -> Groq), `vertex`, or `groq`
- Report Generator (agentic feature):
  - Generate a grounded report as DOCX (recommended) or PDF (optional)
  - Optional charts/plots when numeric series are available in sources

## Quickstart (Local)

### 1) Backend

Create `.env` (copy from `.env.example`) and set at least:

- `GCP_PROJECT_ID`, `GCP_LOCATION`
- `VERTEX_INDEX_ID`, `VERTEX_ENDPOINT_ID`, `GCS_BUCKET_NAME`
- `JWT_SECRET_KEY`

Install and run:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### 2) Frontend

Set `BACKEND_URL` for Next.js (example on Windows PowerShell):

```powershell
cd jordan-vision-frontend
$env:BACKEND_URL="http://127.0.0.1:8000"
npm install
npm run dev
```

Open the UI at `http://localhost:3000`.

### 3) Ingest PDFs

Put your official PDFs into `data/` then (admin-only) trigger ingestion from the Admin Console tab, or call:

```text
POST /api/v1/ingest/
```

## Groq Fallback (Optional)

If Vertex is unavailable or times out, NashmiBot falls back to Groq for LLM calls (chat generation, guardrails, translation, reports).

Set:

- `GROQ_API_KEY`
- `GROQ_FALLBACK_MODEL` (or legacy `MAIN_LLM_MODEL`)

## Report Generator (DOCX/PDF)

In the chat page, click the **Report** button to generate a report for a topic.

- DOCX: always supported (server-side generation via `python-docx`)
- PDF: best-effort conversion from DOCX
  - Works if MS Word is installed (docx2pdf), or LibreOffice is available (`soffice`)

## Full Documentation

See `documentation.md` for architecture, endpoints, database schema, env variables, and operational details.

## Fast Deploy (Docker Compose)

This repo includes a Docker Compose setup that runs:

- Backend (FastAPI) on `http://localhost:8000`
- Frontend (Next.js) on `http://localhost:3000`

Steps:

```bash
docker compose up -d --build
```

Notes:

- Keep your real secrets in `.env` (don’t bake them into images).
- Persistent storage is mounted from `./data/` (PDFs) and `./persist/` (SQLite DBs).
