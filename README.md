# 🇯🇴 Jordan Vision 2033 Advisory Agent

> **Citizen & Investor Assistant** — Commissioned by the Office of the Prime Minister, Hashemite Kingdom of Jordan

A government-grade, RAG-powered advisory agent built **entirely on Google Cloud Vertex AI** that delivers accurate, grounded, and cited answers about Jordan's **Economic Modernization Vision (2023–2033)** and **Public Sector Modernization Roadmap**.

---

## 🎯 Objective

Serve citizens, entrepreneurs, and international investors seeking fact-based guidance on:
- Jordan's strategic priorities and reform programs
- Investment landscape and incentives
- Sectoral growth engines and digital transformation initiatives
- Regulatory direction and institutional reforms

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CITIZEN / INVESTOR                        │
│                  (Web Chat Interface)                        │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS
┌───────────────────────▼─────────────────────────────────────┐
│               NEXT.JS FRONTEND (Port 3000)                   │
│  • Chat Interface (AR/EN)  • Admin Console (4 Tabs)          │
│  • API Proxies (chat / tickets / logs / ingest / evaluation) │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP
┌───────────────────────▼─────────────────────────────────────┐
│                FASTAPI BACKEND (Port 8000)                   │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                  6-LAYER PIPELINE                      │ │
│  │                                                        │ │
│  │  1. Input Guardrails  → Scope control + safety         │ │
│  │  2. Hybrid Retrieval  → Vertex AI + BM25 (RRF fusion)  │ │
│  │  3. Confidence Gate   → Hybrid score threshold (0.55)   │ │
│  │  4. Generation        → Vertex AI Gemini 1.5 Flash     │ │
│  │  5. Output Guardrails → Refusal + safety filters       │ │
│  │  6. Logging & Audit   → SQLite with evaluation metrics │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  Services: guardrails | output_guardrails | hitl_service    │
│  Models:   Ticket | LogRecord (with metrics)               │
└──────────┬──────────────────┬───────────────┬──────────────┘
           │                  │               │
┌──────────▼──────────┐ ┌────▼────────┐ ┌────▼──────────────┐
│  VERTEX AI VECTOR   │ │  BM25 INDEX │ │  SQLITE DATABASE  │
│  SEARCH (GCS + IDX) │ │  (SQLite)   │ │  Tickets + Logs   │
│  Semantic Embeddings│ │  Keyword    │ │  Evaluation Data  │
│  text-embedding-004 │ │  Search     │ │  (Audit Trail)    │
└─────────────────────┘ └─────────────┘ └───────────────────┘
```

---

## ✨ Features

### 🤖 RAG Pipeline (100% Vertex AI)
- **Embeddings**: Vertex AI `text-embedding-004` — supports Arabic & English natively
- **Semantic Search**: Vertex AI Vector Search with streaming index updates
- **BM25 Keyword Search**: Lightweight SQLite-backed keyword index for Arabic + English
- **Hybrid Retrieval**: Reciprocal Rank Fusion (RRF) merges semantic + keyword results
- **Generation**: Vertex AI Gemini 1.5 Flash with strict grounding prompt
- **Bilingual Responses**: Automatically answers in the same language as the question (AR/EN)

### 🛡️ Input Guardrails (3-Tier)
1. **Fast Pre-Check** — Keyword blocking + length validation (< 1ms, no LLM)
2. **Fast Pass** — 20+ Jordan/economy keywords bypass the LLM check
3. **LLM Classifier** — Gemini classifies ambiguous queries as in-scope or out-of-scope

### 🔒 Output Guardrails
- HITL escalation signal detection (`HITL_ESCALATION_REQUIRED`)
- LLM refusal signal detection (Arabic + English, 18 patterns)
- Minimum answer length check (< 30 chars → likely refusal)
- Safety content blocklist (harmful terms in AR + EN)
- Automatic escalation to HITL on any guardrail trigger

### 🎫 Human-in-the-Loop (HITL)
- Automatic ticket creation when confidence is too low or guardrails trigger
- Human agent review console at `/admin`
- Agent writes and submits official answers
- Full resolved ticket history with answer audit trail

### 📊 Evaluation & Monitoring
- **Confidence Scores**: Hybrid similarity score per response (color-coded)
- **Guardrail Status**: Visible on every chat response and in admin logs
- **KPI Dashboard**: Total queries, answer rate, avg confidence, avg response time
- **Guardrail Breakdown**: Counts for passed, input-blocked, low-confidence, output-guardrail
- **Response Timing**: Tracks end-to-end latency per query

### 📝 Full Interaction Logging
- Every query, answer, citation, confidence, timing, and guardrail status saved
- Expandable log details in admin console
- Filter by escalation status

---

## 🗂️ Project Structure

```
jordan_vision_agent/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py          # Main RAG endpoint (6-layer pipeline)
│   │   │   ├── hitl.py          # Ticket management (open / resolve / all)
│   │   │   ├── ingest.py        # Document ingestion (Vertex AI + BM25)
│   │   │   └── logs.py          # Interaction logs + evaluation metrics API
│   │   └── dependencies.py      # DB session dependency
│   ├── core/
│   │   ├── config.py            # Settings (GCP project, thresholds, etc.)
│   │   └── database.py          # SQLAlchemy setup
│   ├── models/
│   │   ├── ticket.py            # HITL Ticket model
│   │   └── log_record.py        # Interaction log model (with metrics)
│   ├── rag/
│   │   ├── generator.py         # Vertex AI Gemini generation (LCEL chain)
│   │   ├── retriever.py         # Hybrid retrieval (Semantic + BM25 + RRF)
│   │   ├── vector_store.py      # Vertex AI Vector Search (stream_update)
│   │   ├── bm25_store.py        # BM25 keyword search index (SQLite)
│   │   ├── embeddings.py        # Vertex AI text-embedding-004
│   │   ├── document_loader.py   # PDF document loader
│   │   └── text_splitter.py     # Text chunking strategy
│   ├── schemas/
│   │   ├── chat_schema.py       # ChatRequest / ChatResponse (with guardrail_status)
│   │   └── hitl_schema.py       # TicketResponse / ResolveTicketRequest
│   ├── services/
│   │   ├── guardrails.py        # Input guardrails (3-tier, uses Gemini for LLM check)
│   │   ├── output_guardrails.py # Output guardrails (refusal + safety + length)
│   │   └── hitl_service.py      # Ticket creation + interaction logging
│   └── main.py                  # FastAPI app, CORS, router registration
│
├── jordan-vision-frontend/
│   ├── app/
│   │   ├── page.tsx             # Citizen chat (AR/EN, with guardrail badges)
│   │   ├── admin/page.tsx       # Admin console (4 tabs: Tickets, Logs, Eval, Ingest)
│   │   └── api/
│   │       ├── chat/route.ts    # Proxy → /api/v1/chat/
│   │       ├── tickets/route.ts # Proxy → /api/v1/hitl/tickets
│   │       ├── tickets/[id]/resolve/route.ts
│   │       ├── tickets/all/route.ts
│   │       ├── logs/route.ts    # Proxy → /api/v1/admin/logs
│   │       ├── ingest/route.ts  # Proxy → /api/v1/ingest/
│   │       └── evaluation/route.ts # Proxy → /api/v1/admin/evaluation
│   └── ...
│
├── data/                        # Place PDF documents here for ingestion
├── jordan_vision_agent.db       # SQLite database (auto-created)
├── bm25_index.db               # BM25 keyword index (auto-created)
├── requirements.txt
└── .env                         # GCP credentials & config (not committed)
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Cloud project with Vertex AI enabled
- GCP Application Default Credentials (`gcloud auth application-default login`)
- Vertex AI Vector Search Index + Endpoint already created

### 1. Clone & Setup Backend

```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
# Google Cloud / Vertex AI (Required)
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
VERTEX_INDEX_ID=your-vertex-index-id
VERTEX_ENDPOINT_ID=your-vertex-endpoint-id
GCS_BUCKET_NAME=your-gcs-bucket-name

# Database
DATABASE_URL=sqlite:///./jordan_vision_agent.db

# RAG Configuration
CONFIDENCE_THRESHOLD=0.55
MAX_RETRIEVED_DOCS=5
```

### 3. Ingest Documents

Place your PDF documents in the `data/` directory, then run:

```bash
# Start the backend first
uvicorn app.main:app --reload --port 8000

# Then trigger ingestion (in a new terminal)
curl -X POST http://localhost:8000/api/v1/ingest/

# Or use the Admin Console → Data Ingestion tab
```

> **Why ingestion is required:** The ingestion step reads your PDFs, splits them into chunks, embeds them using Vertex AI `text-embedding-004`, and stores both the **text content in GCS** and the **vectors in Vector Search**. Without this step, the retriever can't find any documents to answer questions.

### 4. Start the Backend

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Start the Frontend

```bash
cd jordan-vision-frontend
npm install
npm run dev
```

### 6. Open the App

| Interface | URL |
|---|---|
| Citizen Chat | http://localhost:3000 |
| Admin Console | http://localhost:3000/admin |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## 🔌 API Reference

### Chat
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/chat/` | Send a query, receive grounded answer with citations + confidence + guardrail status |

**Request:**
```json
{ "query": "ما هي محاور رؤية التحديث الاقتصادي؟" }
```

**Response:**
```json
{
  "answer": "تقوم رؤية التحديث الاقتصادي على...",
  "citations": [{ "document_title": "Economic Modernization Vision", "page_number": 12 }],
  "is_escalated": false,
  "ticket_id": null,
  "confidence_score": 0.8423,
  "retrieved_scores": [0.8423, 0.7891, 0.7234],
  "guardrail_status": "passed"
}
```

### HITL (Human-in-the-Loop)
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
| `POST` | `/api/v1/ingest/` | Ingest PDFs into Vertex AI + BM25 index |

---

## ⚙️ Configuration Reference

| Setting | Default | Description |
|---|---|---|
| `GCP_PROJECT_ID` | — | Google Cloud project ID (required) |
| `GCP_LOCATION` | `us-central1` | GCP region for Vertex AI |
| `VERTEX_INDEX_ID` | — | Vertex AI Vector Search Index ID (required) |
| `VERTEX_ENDPOINT_ID` | — | Vertex AI Vector Search Endpoint ID (required) |
| `GCS_BUCKET_NAME` | — | GCS bucket for document text storage (required) |
| `CONFIDENCE_THRESHOLD` | `0.55` | Minimum hybrid score to answer (below → HITL escalation) |
| `MAX_RETRIEVED_DOCS` | `5` | Number of documents retrieved per query |

---

## 🛡️ Guardrail System

### Input Guardrails
| Layer | Speed | Method | Action |
|---|---|---|---|
| Blocked Terms | < 1ms | Keyword match | Immediate reject (harmful/off-topic) |
| Jordan Keywords | < 1ms | Keyword match | Fast pass (clearly in-scope) |
| LLM Classifier | ~500ms | Gemini 1.5 Flash | Classify ambiguous queries |

### Output Guardrails
| Check | Action on Fail |
|---|---|
| HITL_ESCALATION_REQUIRED detected | Escalate to human |
| LLM refusal phrases (18 patterns, AR+EN) | Escalate to human |
| Answer < 30 characters | Escalate to human |
| Safety blocklist terms | Escalate + log safety alert |

### Guardrail Status Codes
| Status | Meaning | UI Display |
|---|---|---|
| `passed` | All checks passed | ✅ Verified |
| `input_blocked` | Input guardrail rejected | 🚫 Out of Scope |
| `low_confidence` | Hybrid score below threshold | ⚠️ Low Confidence |
| `output_*` | Output guardrail triggered | ⚠️ Output Guardrail |

---

## 🔒 Security & Production Notes

- All responses are **grounded in official documents only** — the LLM cannot invent facts
- **Input guardrails** reject out-of-scope, harmful, or prompt-injection queries
- **Output guardrails** catch LLM hallucinations and safety violations before delivery
- Full **audit trail** in SQLite for every interaction (query, answer, confidence, timing, guardrail status)
- CORS configured — restrict `allow_origins` to your domain in production
- GCP credentials via Application Default Credentials (never hardcoded)

---

## 🌐 Language Support

The system fully supports **Arabic (RTL)** and **English (LTR)**:
- Users toggle language in the chat header (`عربي` / `EN`)
- The LLM detects query language and responds accordingly
- The entire UI adapts direction and labels
- Guardrail badges and evaluation metrics display in both languages

---

## 📊 Admin Console Tabs

| Tab | Description |
|---|---|
| 🎫 **Tickets** | Open HITL tickets with resolve workflow + resolved history |
| 📊 **Logs** | Expandable interaction logs with full details, guardrail badges, confidence, timing |
| 📈 **Evaluation** | KPI cards (total queries, answer rate, avg confidence, avg response time), guardrail breakdown chart, answer vs escalation rate bar |
| 📥 **Ingestion** | Trigger document ingestion from UI with progress and results display |

---

## 👥 Team

Built as part of the **9XAI D5** program.
Commissioned by the Office of the Prime Minister — Hashemite Kingdom of Jordan.

---

*Jordan Vision 2033 Advisory Agent — v1.0.0*
