# NashmiBot Documentation

Team:

Karam Balasmeh, Ali Tamimi

## 1) Overview

NashmiBot is a bilingual (Arabic/English) Retrieval-Augmented Generation (RAG) web application for answering Jordan Vision 2033 questions with grounded, cited responses.

Core goals:

- Grounded answers from official PDFs (no external hallucinated facts)
- Auditability (logs, tickets, citations, confidence)
- Human-in-the-loop (HITL) escalation when confidence is low
- Bilingual UX and bilingual answering (AR/EN)
- Resilience: Vertex AI primary + Groq fallback for LLM calls

## 2) Tech Stack

Backend:

- FastAPI (REST API)
- SQLAlchemy (SQLite by default)
- LangChain orchestration
- Vertex AI (Gemini + Vector Search + text-embedding-004)
- BM25 (rank-bm25) for keyword retrieval

Frontend:

- Next.js App Router
- Tailwind CSS
- Next.js API routes as backend proxies (adds auth headers, timeouts)

## 3) Repository Layout

High-level folders:

- `app/` - FastAPI backend, RAG pipeline, DB models/services
- `jordan-vision-frontend/` - Next.js frontend
- `data/` - PDF sources for ingestion (place official PDFs here)
- `jordan_vision_agent.db` - SQLite database (created at runtime)
- `bm25_index.db` - BM25 index persistence

## 4) Backend: FastAPI

Entry point:

- `app/main.py`
  - Creates DB tables on startup
  - Optionally bootstraps an admin user (via env vars)
  - Repairs legacy mojibake in conversation titles (best-effort)
  - Registers all routers under `API_V1_STR` (default `/api/v1`)

### 4.1 Authentication (JWT)

Backend issues JWT access tokens, used by the frontend via a httpOnly cookie (`auth_token`).

Key files:

- `app/api/routes/auth.py`
- `app/api/security.py`
- `app/services/auth_service.py`
- `app/models/user.py`

Endpoints:

- `POST /api/v1/auth/register`
  - Body: `{ "username": "...", "password": "..." }`
- `POST /api/v1/auth/login`
  - Body: `{ "username": "...", "password": "..." }`
  - Response: `{ "access_token": "...", "token_type": "bearer" }`
- `GET /api/v1/auth/me`
  - Header: `Authorization: Bearer <token>`

Admin authorization:

- Admin-only endpoints use `require_admin` dependency (401/403 if not admin).

### 4.2 Conversations + Messages (History)

Key files:

- `app/api/routes/conversations.py`
- `app/models/conversation.py`
- `app/models/message.py`

Endpoints:

- `GET /api/v1/conversations`
- `POST /api/v1/conversations`
- `GET /api/v1/conversations/{conversation_id}`

The chat endpoint persists every user message and assistant reply into `messages`.

Conversation memory:

- The last N messages (default 10) are passed into the generator prompt as "history" for disambiguation.
- History is explicitly *not* treated as a source of truth (sources must come from retrieved documents).

### 4.3 Chat Endpoint (RAG)

Key file:

- `app/api/routes/chat.py`

Endpoint:

- `POST /api/v1/chat/`
  - Body: `{ "query": "...", "conversation_id": 123 | null }`

Pipeline layers:

1) Input guardrails (`app/services/guardrails.py`)
2) Resolved answer cache (cross-user) (`app/services/resolved_answer_service.py`)
3) Retrieval (`app/rag/retriever.py`)
   - Vertex Vector Search semantic retrieval + BM25 keyword retrieval
4) Confidence gate (`CONFIDENCE_THRESHOLD`)
5) Generation (`app/rag/generator.py`)
6) Output guardrails (`app/services/output_guardrails.py`)
7) HITL ticket creation (if escalated) (`app/services/hitl_service.py`)

Bilingual retrieval (AR/EN):

- If the user asks in Arabic and retrieval is weak, NashmiBot translates the retrieval query to English and retries retrieval.
- Answer language still follows the original user query language.

### 4.4 HITL Tickets (Escalation + Admin Resolution)

Key files:

- `app/api/routes/hitl.py`
- `app/models/ticket.py` (table: `hitl_tickets`)
- `app/services/hitl_service.py`

Endpoints:

- `GET /api/v1/hitl/tickets` (admin-only, open tickets)
- `GET /api/v1/hitl/tickets/all` (admin-only, all tickets)
- `POST /api/v1/hitl/tickets/{ticket_id}/resolve` (admin-only)

Resolved answers are saved into:

- `hitl_tickets.human_answer` (per ticket)
- `resolved_answers` (cross-user reuse cache)

Duplicate open tickets:

- If multiple identical open tickets exist (older data), resolving one will resolve the duplicates too.

### 4.5 Interaction Logs + Evaluation

Key file:

- `app/api/routes/logs.py`

Endpoints (admin-only):

- `GET /api/v1/admin/logs?limit=50`
- `GET /api/v1/admin/evaluation`

Logs store: query, response, citations, escalation, confidence score, response time, and guardrail status.

### 4.6 Ingestion (PDF -> Chunks -> Vertex + BM25)

Key files:

- `app/api/routes/ingest.py` (admin-only)
- `app/rag/document_loader.py`
- `app/rag/text_splitter.py`
- `app/rag/vector_store.py`
- `app/rag/bm25_store.py`

Endpoint:

- `POST /api/v1/ingest/`

What ingestion does:

1) Loads PDFs from `data/`
2) Splits into chunks
3) Uploads to Vertex Vector Search (streaming)
4) Builds BM25 index locally

### 4.7 Report Generator (Agentic Feature)

Key files:

- `app/api/routes/reports.py`
- `app/services/report_service.py`

Endpoint:

- `POST /api/v1/reports/generate`
  - Body:
    - `topic` (required)
    - `format`: `"docx"` (default) or `"pdf"`
    - `conversation_id` (optional)
    - `include_charts` (optional)

How it works (high level):

1) Retrieve relevant documents for the topic (same bilingual retrieval fallback)
2) Generate a structured Markdown report (grounded + cited)
3) Optionally generate chart specs (JSON) if numeric series exist in sources
4) Build DOCX report (python-docx)
5) If PDF is requested:
   - Convert DOCX -> PDF using docx2pdf (MS Word) or LibreOffice (soffice), if available

## 5) LLM Provider Routing (Vertex Primary + Groq Fallback)

Key file:

- `app/services/llm_router.py`

Used by:

- Chat generation
- Input guardrails classifier
- Arabic->English translation for retrieval fallback
- Report generation

Behavior:

- Tries Vertex first (Gemini via `langchain-google-vertexai`)
- On runtime failure/timeout, falls back to Groq (Llama 70B) if `GROQ_API_KEY` is set

## 6) Database Schema (SQLite)

Default DB file:

- `jordan_vision_agent.db`

Tables (current):

- `users`
  - `id`, `username`, `password_hash`, `is_admin`, timestamps
- `conversations`
  - `id`, `user_id`, `title`, timestamps
- `messages`
  - `id`, `conversation_id`, `role` (`user|agent`), `content`, citations/meta fields, timestamps
- `hitl_tickets`
  - `id`, `user_query`, `status`, `human_answer`, timestamps
- `resolved_answers`
  - `id`, `ticket_id`, `question`, `normalized_question`, `answer`, `citations`, timestamps
- `interaction_logs`
  - `id`, `user_query`, `llm_response`, `citations`, `is_escalated`, `ticket_id`, `confidence_score`, `response_time_ms`, `guardrail_status`, timestamp

## 7) Frontend: Next.js

Pages:

- `/` landing page
- `/login` user login/register
- `/chat` chat UI + history sidebar + report generator
- `/admin/login` admin login
- `/admin` admin console (tickets/logs/evaluation/ingestion)

API proxy routes:

- `jordan-vision-frontend/app/api/*`
  - Add `Authorization: Bearer <token>` from the httpOnly cookie
  - Enforce request timeouts to prevent hanging UIs

The frontend stores the JWT in a httpOnly cookie (`auth_token`), and all client calls go through Next API routes (server-side), so the token is not exposed to client JS.

## 8) Environment Variables

Backend (`.env`):

- Core: `PROJECT_NAME`, `VERSION`, `API_V1_STR`, `ENVIRONMENT`
- DB: `DATABASE_URL`
- Vertex: `GCP_PROJECT_ID`, `GCP_LOCATION`, `VERTEX_INDEX_ID`, `VERTEX_ENDPOINT_ID`, `GCS_BUCKET_NAME`
- LLM routing:
  - `VERTEX_LLM_MODEL`
  - `GROQ_API_KEY` (optional)
  - `GROQ_FALLBACK_MODEL` (optional; legacy `MAIN_LLM_MODEL` also accepted)
  - `LLM_REQUEST_TIMEOUT_SECONDS`
- Guardrails: `CONFIDENCE_THRESHOLD`, `MAX_RETRIEVED_DOCS`
- Auth: `JWT_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- Admin bootstrap: `ADMIN_BOOTSTRAP_USERNAME`, `ADMIN_BOOTSTRAP_PASSWORD`

Frontend (Next.js environment):

- `BACKEND_URL` (defaults to `http://127.0.0.1:8000`)

## 9) Troubleshooting

Arabic queries always escalate:

- Ensure ingestion is complete and retrieval is returning docs.
- NashmiBot retries retrieval with Arabic->English translation when low confidence. If it still escalates:
  - Lower `CONFIDENCE_THRESHOLD` slightly (carefully)
  - Verify your Vertex Vector Search index contains your ingested docs

PDF export fails:

- DOCX export is always available.
- For PDF export you need one of:
  - Microsoft Word available on the server (docx2pdf), OR
  - LibreOffice installed and `soffice` available in PATH

Groq fallback not working:

- Confirm `GROQ_API_KEY` is set and the model name is valid (`GROQ_FALLBACK_MODEL`).

## 10) Security Notes

- Keep `.env` out of version control (already in `.gitignore`)
- Use a strong `JWT_SECRET_KEY` for stable sessions
- Restrict CORS origins for production (current config allows `*` for local dev)
- Admin bootstrap values should be used only for initial setup and then removed/rotated
