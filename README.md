# 🇯🇴 Jordan Vision 2033 Advisory Agent

> **Citizen & Investor AI Assistant** — Commissioned by the Office of the Prime Minister, Hashemite Kingdom of Jordan

A **government-grade, production-ready RAG advisory agent** that delivers accurate, grounded, and cited answers about Jordan's **Economic Modernization Vision (2023–2033)** and **Public Sector Modernization Roadmap**. Built on **Google Cloud Vertex AI** with intelligent fallback to **Groq LLMs** for maximum uptime.

---

## 🎯 Objective

Serve citizens, entrepreneurs, and international investors seeking fact-based guidance on:
- 🏛️ Jordan's strategic priorities and reform programs
- 💰 Investment landscape, incentives, and sectoral opportunities
- 🚀 Digital transformation, energy, tourism, and transport initiatives
- 📋 Regulatory direction and institutional reforms

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      CITIZEN / INVESTOR                          │
│                    (Web Chat Interface)                           │
└────────────────────────┬─────────────────────────────────────────┘
                         │ HTTPS
┌────────────────────────▼─────────────────────────────────────────┐
│                NEXT.JS FRONTEND (Port 3000)                       │
│  • Bilingual Chat UI (AR/EN with RTL support)                     │
│  • Admin Console (4 Tabs: Tickets, Logs, Evaluation, Ingestion)  │
│  • API Proxies with configurable timeouts (60s chat, 600s ingest)│
└────────────────────────┬─────────────────────────────────────────┘
                         │ HTTP
┌────────────────────────▼─────────────────────────────────────────┐
│                 FASTAPI BACKEND (Port 8000)                       │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    6-LAYER RAG PIPELINE                      │ │
│  │                                                              │ │
│  │  1. Input Guardrails  → 3-tier scope control + safety        │ │
│  │  2. Hybrid Retrieval  → Vertex AI Semantic + BM25 (RRF)     │ │
│  │  3. Confidence Gate   → Normalized score threshold (0.70)    │ │
│  │  4. Generation        → Gemini 2.5 Flash (Groq fallback)    │ │
│  │  5. Output Guardrails → Refusal + safety + length filters   │ │
│  │  6. Logging & Audit   → SQLite with evaluation metrics      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Lifespan Startup → Non-blocking DB init for fast server boot    │
│  LLM Timeouts    → 30s request timeout on all AI calls           │
│  Services: guardrails | output_guardrails | hitl_service          │
│  Models:   Ticket | LogRecord (confidence, latency, guardrails)  │
└───────────┬───────────────────┬────────────────┬─────────────────┘
            │                   │                │
┌───────────▼───────────┐ ┌────▼──────────┐ ┌───▼──────────────────┐
│  VERTEX AI VECTOR     │ │  BM25 INDEX   │ │  SQLITE DATABASE     │
│  SEARCH (GCS + IDX)   │ │  (SQLite)     │ │  Tickets + Logs +    │
│  Semantic Embeddings  │ │  Keyword      │ │  Evaluation Data     │
│  text-embedding-004   │ │  Search       │ │  (Full Audit Trail)  │
└───────────────────────┘ └───────────────┘ └──────────────────────┘
```

---

## ✨ Key Features

### 🤖 Hybrid RAG Pipeline
| Component | Technology | Details |
|---|---|---|
| **Embeddings** | Vertex AI `text-embedding-004` | Native Arabic & English support |
| **Semantic Search** | Vertex AI Vector Search | Streaming index updates, GCS-backed text storage |
| **Keyword Search** | BM25 (rank-bm25 + SQLite) | Lightweight keyword index for AR + EN |
| **Hybrid Fusion** | Reciprocal Rank Fusion (RRF) | Merges semantic + keyword results, normalized to 0–1 |
| **Primary LLM** | Gemini 2.5 Flash (Vertex AI) | Strict grounding prompt, 30s timeout, 2048 max tokens |
| **Fallback LLM** | Groq (Llama 3.3 70B Versatile) | Automatic failover if Vertex AI is unavailable |
| **Bilingual** | Arabic & English | Automatically replies in the same language as the query |

### 🛡️ Input Guardrails (3-Tier)

| Tier | Speed | Method | Action |
|---|---|---|---|
| **Blocked Terms** | < 1ms | Keyword match (AR + EN) | Immediate reject — harmful or clearly off-topic |
| **Jordan Keywords** | < 1ms | 20+ keyword match | Fast pass — clearly in-scope (economy, investment, reform, etc.) |
| **LLM Classifier** | ~500ms | Gemini 2.5 Flash | Classifies ambiguous queries as VALID or INVALID |

**Blocked Terms Include:** bomb, weapon, hack, kill, virus, recipe, football, movie, dating (+ Arabic equivalents)

**Fast-Pass Keywords Include:** Jordan, رؤية, economy, استثمار, reform, إصلاح, tourism, سياحة, energy, طاقة, digital, رقمي, trade, تجارة, industry, صناعة, and more.

### 🔒 Output Guardrails (4 Checks)

| Check | Patterns | Action on Fail |
|---|---|---|
| **HITL Escalation Signal** | `HITL_ESCALATION_REQUIRED` | Escalate to human agent |
| **LLM Refusal Detection** | 13 patterns (AR + EN): "لا أملك معلومات", "I cannot find", "not found in the provided context", etc. | Escalate to human agent |
| **Minimum Length** | Answer < 30 characters | Escalate (likely incomplete/refusal) |
| **Safety Blocklist** | bomb, weapon, kill, hack, قنبلة, سلاح, اغتيال, قرصنة | Block + log safety alert |

### 🎫 Human-in-the-Loop (HITL)
- **Automatic ticket creation** when confidence is too low or any guardrail triggers
- **Admin review console** at `/admin` with resolve workflow
- **Agent writes official answers** that are persisted in the audit trail
- **Full ticket history** — open + resolved, with timestamps

### 📊 Evaluation & Monitoring Dashboard
- **KPI Cards**: Total queries, answer rate (%), average confidence (%), average response time (ms)
- **Guardrail Breakdown**: Counts for passed, input-blocked, low-confidence, output-guardrail triggers
- **Interaction Logs**: Expandable details per query (answer, citations, confidence, timing, guardrail status)
- **Data Ingestion**: Trigger ingestion from the UI, monitor progress, view results

### 🌐 Bilingual Support (Arabic + English)
- Users toggle language in the chat header (`عربي` / `EN`)
- The LLM detects the query language and responds accordingly
- Full RTL/LTR UI adaptation with appropriate labels
- Guardrail messages and evaluation metrics display in both languages

---

## 🗂️ Project Structure

```
jordan_vision_agent/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py              # Main RAG endpoint (6-layer pipeline)
│   │   │   ├── hitl.py              # Ticket management (create / resolve / list)
│   │   │   ├── ingest.py            # Document ingestion (Vertex AI + BM25 + DB migration)
│   │   │   └── logs.py              # Interaction logs + evaluation metrics API
│   │   └── dependencies.py          # DB session dependency injection
│   ├── core/
│   │   ├── config.py                # All settings (GCP, thresholds, fallback keys)
│   │   └── database.py              # SQLAlchemy engine, session, base
│   ├── models/
│   │   ├── ticket.py                # HITL Ticket ORM model
│   │   └── log_record.py            # Interaction log model (confidence, latency, guardrails)
│   ├── rag/
│   │   ├── generator.py             # LLM chain: Gemini 2.5 Flash primary, Groq fallback
│   │   ├── retriever.py             # Hybrid retrieval: Semantic + BM25 + RRF + normalization
│   │   ├── vector_store.py          # Vertex AI Vector Search (stream_update, batch=50)
│   │   ├── bm25_store.py            # BM25 keyword index (SQLite-backed, AR+EN tokenizer)
│   │   ├── embeddings.py            # Vertex AI text-embedding-004
│   │   ├── document_loader.py       # PDF loader (PyMuPDF) with source metadata
│   │   └── text_splitter.py         # Text chunking strategy
│   ├── schemas/
│   │   ├── chat_schema.py           # ChatRequest / ChatResponse (scores + guardrail_status)
│   │   └── hitl_schema.py           # TicketResponse / ResolveTicketRequest
│   ├── services/
│   │   ├── guardrails.py            # Input guardrails (3-tier: keyword → fast-pass → LLM)
│   │   ├── output_guardrails.py     # Output guardrails (refusal + safety + length checks)
│   │   └── hitl_service.py          # Ticket creation + interaction logging
│   └── main.py                      # FastAPI app with lifespan, CORS, router registration
│
├── jordan-vision-frontend/          # Next.js 14 frontend application
│   ├── app/
│   │   ├── page.tsx                 # Citizen chat (AR/EN, guardrail badges, RTL support)
│   │   ├── admin/page.tsx           # Admin console (4 tabs: Tickets, Logs, Eval, Ingest)
│   │   └── api/
│   │       ├── chat/route.ts        # Proxy → /api/v1/chat/ (60s timeout)
│   │       ├── tickets/route.ts     # Proxy → /api/v1/hitl/tickets
│   │       ├── tickets/[id]/resolve/route.ts
│   │       ├── tickets/all/route.ts
│   │       ├── logs/route.ts        # Proxy → /api/v1/admin/logs
│   │       ├── ingest/route.ts      # Proxy → /api/v1/ingest/ (600s timeout)
│   │       └── evaluation/route.ts  # Proxy → /api/v1/admin/evaluation
│   └── ...
│
├── data/                            # Place PDF documents here for ingestion
├── jordan_vision_agent.db           # SQLite database (auto-created on startup)
├── bm25_index.db                    # BM25 keyword index (auto-created on ingestion)
├── requirements.txt                 # All Python dependencies (8 categories)
└── .env                             # GCP credentials & configuration (never committed)
```

---

## 🚀 Getting Started

### Prerequisites
| Requirement | Version |
|---|---|
| Python | 3.10+ |
| Node.js | 18+ |
| Google Cloud CLI | Latest (`gcloud auth application-default login`) |
| Vertex AI | Enabled in your GCP project |
| Vector Search | Index + Endpoint already created |

### 1. Clone & Setup Backend

```bash
git clone <your-repo-url>
cd jordan_vision_agent

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate        # Windows
source venv/bin/activate       # macOS / Linux

# Install all dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
# ── App Settings ──────────────────────────────────────
PROJECT_NAME="Jordan Vision 2033 Advisory Agent"
VERSION="1.0.0"
API_V1_STR="/api/v1"
ENVIRONMENT="development"

# ── Google Cloud / Vertex AI (Required) ───────────────
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
VERTEX_INDEX_ID=your-vertex-index-id
VERTEX_ENDPOINT_ID=your-vertex-endpoint-id
GCS_BUCKET_NAME=your-gcs-bucket-name

# ── Database ──────────────────────────────────────────
DATABASE_URL=sqlite:///./jordan_vision_agent.db

# ── RAG Configuration ────────────────────────────────
CONFIDENCE_THRESHOLD=0.70      # Min hybrid score to answer (below → HITL)
MAX_RETRIEVED_DOCS=5           # Number of documents retrieved per query

# ── Fallback LLM (Optional but recommended) ──────────
GROQ_API_KEY=your-groq-api-key # Get free key at console.groq.com
```

### 3. Start the Backend

```bash
uvicorn app.main:app --reload --port 8000
```

> The backend uses a **lifespan event** for database initialization, so the server starts instantly without blocking.

### 4. Ingest Documents

Place your PDF documents in the `data/` directory, then trigger ingestion:

```bash
# Via curl
curl -X POST http://localhost:8000/api/v1/ingest/

# Or use the Admin Console → Data Ingestion tab at http://localhost:3000/admin
```

> **Why ingestion is required:** The ingestion step reads your PDFs using PyMuPDF, splits them into chunks, embeds them using Vertex AI `text-embedding-004`, stores the **text content in GCS** alongside the **vectors in Vector Search**, and builds the **BM25 keyword index** in SQLite. Without this step, the retriever has no documents to search.

### 5. Start the Frontend

```bash
cd jordan-vision-frontend
npm install
npm run dev
```

### 6. Open the App

| Interface | URL | Description |
|---|---|---|
| 💬 Citizen Chat | http://localhost:3000 | Ask questions in Arabic or English |
| ⚙️ Admin Console | http://localhost:3000/admin | Manage tickets, view logs, metrics, ingestion |
| 📖 API Docs (Swagger) | http://localhost:8000/docs | Interactive API documentation |

---

## 🔌 API Reference

### Chat Endpoint
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/chat/` | Send a query, receive a grounded answer with citations, confidence, and guardrail status |

**Request:**
```json
{
  "query": "ما هي محاور رؤية التحديث الاقتصادي؟"
}
```

**Response:**
```json
{
  "answer": "تقوم رؤية التحديث الاقتصادي على ثمانية محاور رئيسية... [Source: vision-en.pdf]",
  "citations": [
    { "document_title": "Economic Modernization Vision", "page_number": 12 }
  ],
  "is_escalated": false,
  "ticket_id": null,
  "confidence_score": 0.8423,
  "retrieved_scores": [0.8423, 0.7891, 0.7234],
  "guardrail_status": "passed"
}
```

### HITL Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/hitl/tickets` | Get all open tickets |
| `GET` | `/api/v1/hitl/tickets/all` | Get all tickets (open + resolved) |
| `POST` | `/api/v1/hitl/tickets/{id}/resolve` | Submit human answer and close ticket |

### Admin & Evaluation
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/admin/logs` | Get interaction logs with full details |
| `GET` | `/api/v1/admin/evaluation` | Get aggregate evaluation metrics (KPIs) |

### Data Ingestion
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/ingest/` | Ingest all PDFs from `data/` into Vertex AI + BM25 index |

---

## ⚙️ Configuration Reference

| Setting | Default | Description |
|---|---|---|
| `GCP_PROJECT_ID` | — | Google Cloud project ID **(required)** |
| `GCP_LOCATION` | `us-central1` | GCP region for Vertex AI |
| `VERTEX_INDEX_ID` | — | Vertex AI Vector Search Index ID **(required)** |
| `VERTEX_ENDPOINT_ID` | — | Vertex AI Vector Search Endpoint ID **(required)** |
| `GCS_BUCKET_NAME` | — | GCS bucket for document text storage **(required)** |
| `CONFIDENCE_THRESHOLD` | `0.70` | Minimum normalized hybrid score to answer (below → HITL escalation) |
| `MAX_RETRIEVED_DOCS` | `5` | Number of documents retrieved per query |
| `GROQ_API_KEY` | `None` | API key for Groq Cloud (automatic fallback LLM) |
| `OPENAI_API_KEY` | `None` | API key for OpenAI (optional fallback) |
| `DATABASE_URL` | `sqlite:///./jordan_vision_agent.db` | SQLAlchemy database URL |

---

## 🛡️ Guardrail System — Detailed Breakdown

### Input Guardrails Flow
```
User Query
    │
    ▼
┌─────────────────────────┐
│  Length Check            │──── Too short (< 3 chars) or too long (> 1000 chars) → BLOCK
│  (< 1ms, no LLM)        │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│  Blocked Terms           │──── Harmful/off-topic keyword found → BLOCK
│  (< 1ms, no LLM)        │    (bomb, weapon, recipe, football, dating, etc.)
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│  Jordan Keywords         │──── Relevant keyword found → PASS (fast path)
│  (< 1ms, no LLM)        │    (Jordan, economy, investment, reform, etc.)
└─────────┬───────────────┘
          │ (no keyword matched — ambiguous)
          ▼
┌─────────────────────────┐
│  LLM Classifier          │──── Gemini classifies → VALID or INVALID
│  (~500ms, uses Gemini)   │    (fail-open: if LLM unreachable, query passes)
└─────────────────────────┘
```

### Output Guardrails Flow
```
LLM Answer
    │
    ▼
┌─────────────────────────┐
│  Refusal Detection       │──── 13 refusal phrases (AR + EN) → ESCALATE
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│  Length Check            │──── Answer < 30 chars → ESCALATE
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│  Safety Blocklist        │──── Harmful terms in output → BLOCK + ALERT
└─────────┬───────────────┘
          │
          ▼
       ✅ PASS
```

### Guardrail Status Codes
| Status | Meaning | UI Display |
|---|---|---|
| `passed` | All checks passed, answer is grounded | ✅ Verified |
| `input_blocked` | Input guardrail rejected the query | 🚫 Out of Scope |
| `low_confidence` | Hybrid retrieval score below threshold | ⚠️ Low Confidence |
| `output_llm_refusal:*` | LLM admitted it couldn't answer | ⚠️ Output Guardrail |
| `output_answer_too_short` | Answer was too short (likely refusal) | ⚠️ Output Guardrail |
| `output_safety_block:*` | Harmful term detected in output | 🚨 Safety Block |

---

## 📊 Admin Console Tabs

| Tab | Description |
|---|---|
| 🎫 **Tickets** | Open HITL tickets with resolve workflow — agent writes and submits official answers. Includes resolved ticket history with timestamps. |
| 📊 **Logs** | Expandable interaction logs with: full answer text, citations, confidence score, response time, guardrail status badge, escalation flag. |
| 📈 **Evaluation** | KPI cards (total queries, answer rate %, avg confidence %, avg response time ms). Guardrail breakdown chart. Answer vs escalation rate comparison. |
| 📥 **Ingestion** | Trigger document ingestion from the UI. Shows progress indicator and final results (chunks processed, BM25 index size). 10-minute timeout for large PDF sets. |

---

## 🔧 Technical Details

### LLM Configuration
| Parameter | Primary (Vertex AI) | Fallback (Groq) |
|---|---|---|
| **Model** | `gemini-2.5-flash` | `llama-3.3-70b-versatile` |
| **Temperature** | 0.0 (deterministic) | 0.0 (deterministic) |
| **Max Tokens** | 2048 | Default |
| **Request Timeout** | 30 seconds | 30 seconds |
| **Failover** | — | Automatic if Vertex AI init fails |

### Score Normalization
All retrieval scores are **normalized to the 0–1 range** before being returned:
- **Hybrid RRF Fusion**: Weighted combination (60% semantic, 40% BM25), then normalized by max score
- **Single-Engine Fallback**: If only BM25 or semantic is available, raw scores are normalized by the max score in the result set
- **Confidence Gate**: Uses `CONFIDENCE_THRESHOLD` (default 0.70) against the normalized top score

### Database Schema
The SQLite database (`jordan_vision_agent.db`) auto-creates on first startup via the lifespan event:

| Table | Key Columns | Purpose |
|---|---|---|
| `tickets` | id, user_query, status, admin_response, timestamps | HITL ticket management |
| `interaction_logs` | id, user_query, llm_response, citations, is_escalated, confidence_score, response_time_ms, guardrail_status | Full audit trail |

### Dependencies (requirements.txt — 8 categories)
| Category | Key Packages |
|---|---|
| Core API | FastAPI 0.111, Uvicorn, Pydantic 2.7+ |
| RAG Orchestration | LangChain 0.3.x (core, community) |
| Google Cloud | langchain-google-vertexai 2.0+, google-cloud-aiplatform 1.74+ |
| Hybrid Search | rank-bm25 0.2+ |
| Document Processing | PyMuPDF 1.24+ (PDF parsing) |
| Database | SQLAlchemy 2.0+, Alembic 1.13+ |
| Utilities | python-dotenv 1.0+, loguru 0.7+ |
| Fallback LLMs | langchain-groq 0.2+, langchain-openai 0.2+ |

---

## 🔒 Security & Production Notes

- ✅ All responses are **grounded exclusively in official documents** — the LLM cannot invent facts
- ✅ **Input guardrails** reject out-of-scope, harmful, and prompt-injection queries
- ✅ **Output guardrails** catch hallucinations, refusals, and safety violations before delivery
- ✅ Full **audit trail** in SQLite for every interaction (query, answer, confidence, timing, guardrail status)
- ✅ **LLM timeouts** (30s) prevent indefinite hangs on slow API calls
- ✅ **Lifespan-based startup** prevents server hangs during database initialization
- ✅ CORS configured — restrict `allow_origins` to your production domain
- ✅ GCP credentials via Application Default Credentials (never hardcoded)
- ✅ `.env` file excluded from version control via `.gitignore`

---

## 👥 Team

Built as part of the **9XAI D5** program.
Commissioned by the Office of the Prime Minister — Hashemite Kingdom of Jordan.

---

*Jordan Vision 2033 Advisory Agent — v1.0.0 | Powered by Google Cloud Vertex AI & Gemini 2.5 Flash*
