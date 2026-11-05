# Multi-Tenant Personal Document RAG System
### Enterprise Production-Grade Architecture: FastAPI + Supabase (pgvector & RLS) + React (Vite) + Flutter (Dart) + OpenRouter

This repository contains a fully operational, multi-tenant Personal Document Retrieval-Augmented Generation (RAG) system engineered to production standards. It enforces strict PostgreSQL Row Level Security (RLS), layout-aware PDF extraction, 768-dimensional vector embeddings, verifiable page-level source citations, and anti-hallucination guardrails with explicit refusal triggers.

---

## 🏛️ Architecture Overview

```
                                      ┌────────────────────────┐
                                      │   Supabase PostgreSQL  │
                                      │   (pgvector + HNSW)    │
                                      │   • profiles           │
                                      │   • documents          │
                                      │   • document_chunks    │
                                      │   • conversations      │
                                      │   • messages           │
                                      └───────────▲────────────┘
                                                  │
                                   RLS auth.uid() │ Vector Search RPC
                                                  │
┌─────────────────────────┐          ┌────────────┴───────────┐          ┌─────────────────────────┐
│   React 18 Web Client   │◄────────►│ Python FastAPI Backend │◄────────►│   Flutter 3 Mobile App  │
│  (Vite + Tailwind CSS)  │   REST   │  • PDF Extractor       │   REST   │      (Material 3)       │
│  • Citation Drawer      │   SSE    │  • Semantic Chunker    │   SSE    │  • Citation BottomSheet │
│  • Document Manager     │          │  • Embedding Generator │          │  • Dynamic URL Resolver │
└─────────────────────────┘          │  • RAG Synthesizer     │          └─────────────────────────┘
                                     └────────────┬───────────┘
                                                  │
                                                  ▼
                                      ┌────────────────────────┐
                                      │     OpenRouter API     │
                                      │ • Nemotron 3 / Llama 3 │
                                      │ • text-embedding-3-lg  │
                                      └────────────────────────┘
```

---

## 📁 Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth_middleware.py     # Supabase JWT authentication dependency
│   │   │   ├── routes_documents.py    # Document upload, status polling, delete
│   │   │   └── routes_chat.py         # Multi-turn RAG chat with streaming SSE & citations
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic v2 BaseSettings
│   │   │   └── supabase_client.py     # Service-role & user-scoped Supabase client factories
│   │   ├── rag/
│   │   │   ├── extractor.py           # Layout-aware PDF/TXT extraction (pdfplumber)
│   │   │   ├── chunker.py             # Recursive semantic chunker preserving page numbers
│   │   │   ├── embeddings.py          # Batch vector embedding generator with backoff (768-dim)
│   │   │   └── synthesizer.py         # LLM synthesis via OpenRouter with strict citations
│   │   └── main.py                    # FastAPI application with CORS & lifespan events
│   ├── migrations/
│   │   └── 001_init_rag.sql           # Complete PostgreSQL 15+ schema, HNSW index & RLS
│   ├── tests/
│   │   └── test_rag_pipeline.py       # Automated end-to-end ingestion and query test
│   ├── run_server.py                  # Standalone backend server runner
│   ├── requirements.txt               # Backend dependencies
│   └── .env.example
├── frontend_web/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AuthModal.tsx          # Supabase Auth sign-in / sign-up modal
│   │   │   ├── ChatInterface.tsx      # Multi-turn streaming chat with clickable citations
│   │   │   ├── CitationDrawer.tsx     # Inspection modal for verified source passages
│   │   │   ├── DocumentManager.tsx    # Drag-and-drop document uploader with status badges
│   │   │   └── Navbar.tsx             # Tenant profile, RLS status, tab switcher
│   │   ├── lib/
│   │   │   ├── api.ts                 # FastAPI client methods
│   │   │   └── supabase.ts            # Supabase JS client
│   │   └── types/index.ts             # TypeScript definitions
│   ├── package.json
│   └── vite.config.ts
├── client_mobile/
│   ├── lib/
│   │   ├── core/
│   │   │   ├── config/env_config.dart # Dynamic host switcher (Android 10.0.2.2 vs localhost)
│   │   │   ├── services/              # Supabase & FastAPI HTTP clients
│   │   │   └── theme/app_theme.dart   # Material 3 dark aesthetic
│   │   └── features/
│   │       ├── auth/                  # Mobile login & registration screen
│   │       ├── documents/             # Native file picker & document manager
│   │       └── chat/                  # Chat screen with clickable citation badges & modal sheet
│   └── pubspec.yaml
├── supabase/
│   └── migrations/
│       └── 20261104000000_init_rag_schema.sql
├── verify_rag.py                      # Automated CLI benchmark script
├── .env.example
└── README.md
```

---

## 🚀 Phase 1: Database Migration (Supabase PostgreSQL + pgvector)

1. Open your **Supabase Dashboard** -> **SQL Editor**.
2. Copy and paste the contents of `backend/migrations/001_init_rag.sql` (or `supabase/migrations/20261104000000_init_rag_schema.sql`).
3. Click **Run**.
4. The migration will configure:
   * Extensions: `vector` and `uuid-ossp`.
   * Tables: `profiles`, `documents`, `document_chunks`, `conversations`, `messages`.
   * HNSW Index: Cosine distance index on `document_chunks.embedding` with `m = 16, ef_construction = 64`.
   * RPC Function: `public.match_document_chunks` scoped to `auth.uid() = user_id`.
   * Row Level Security: Strict policies restricting `SELECT`, `INSERT`, `UPDATE`, and `DELETE` on all tables.
   * Storage: Creates private bucket `user-documents` with RLS restricting path access to `auth.uid()`.

---

## ⚙️ Phase 2: Python FastAPI Backend

### 1. Requirements & Environment
Ensure Python 3.11+ is installed. Your `.env` or `backend/.env` file contains:
```env
NEXT_PUBLIC_SUPABASE_URL=https://sbkxmevrereobziaubsl.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-secret

OPENROUTER_API_KEY=sk-or-v1-your-key
OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

EMBEDDING_PROVIDER=openrouter
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSION=768
STORAGE_BUCKET=user-documents

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

### 2. Run the Automated Tests
```bash
python -m pytest backend/tests/test_rag_pipeline.py -v
```

### 3. Start the Backend Server
```bash
python backend/run_server.py
```
Or with uvicorn directly:
```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```
Check health at: `http://localhost:8000/health` or `http://localhost:8000/docs`.

---

## 🌐 Phase 3: React Web Client

The React client features full email/password authentication via `@supabase/supabase-js`, drag-and-drop document upload with real-time status polling, streaming typewriter chat output, and clickable citation badges with an inspection drawer.

### 1. Start Development Server
```bash
cd frontend_web
npm run dev
```
Open `http://localhost:3000` in your browser.

### 2. Build for Production
```bash
cd frontend_web
npm run build
```

---

## 📱 Phase 4: Flutter Mobile Client

The mobile app is built with Flutter 3 (Dart 3) following Material 3 design and clean architecture.

### Features:
* **Dynamic URL Resolver**: Automatically uses `http://10.0.2.2:8000` on Android emulator and `http://localhost:8000` on iOS/Web/Desktop.
* **Document Picker**: Selects PDFs or TXT files natively with `file_picker` (supporting both mobile `File.readAsBytes()` and web `PlatformFile.bytes`).
* **Interactive Citations**: Tapping any inline citation badge (`[Doc.pdf, Page X]`) opens a custom `showModalBottomSheet` displaying the exact verified excerpt.

### Run Mobile App:
```bash
cd client_mobile
flutter run
```

---

## 🧪 Phase 5: Automated CLI Benchmark Verification (`verify_rag.py`)

Run the automated verification suite to ingest a multi-page document, generate 768-dimensional embeddings, and execute question-answering benchmarks with strict citation audits and anti-hallucination checks:

```bash
python verify_rag.py
```

### Benchmark Results Output:
```
================================================================================
🚀 ENTERPRISE RAG VERIFICATION BENCHMARK SUITE
LLM Gateway: OpenRouter (nvidia/nemotron-3-ultra-550b-a55b:free)
Embedding Model: text-embedding-3-large (dim=768)
================================================================================

[Step 1] Ingesting multi-page benchmark document...
✅ Extracted 3 pages successfully.

[Step 2] Chunking text preserving page boundaries...
✅ Generated 3 semantic chunks.

[Step 3] Generating batch vector embeddings...
✅ Generated 3 embeddings in 1.63s (dim=768).

================================================================================
🎯 EXECUTING QUESTION-ANSWERING BENCHMARK
================================================================================

[Test Case 1] Category: Direct Fact Retrieval
❓ Question: What was the enterprise software revenue in Q3 2026, and what was the growth rate?
💬 Answer:
In the third quarter of fiscal year 2026, enterprise software revenue reached $48.6 million, representing a 35% year-over-year growth rate [Enterprise_Architecture_Overview.pdf, Page 3].
📎 Citations:
   • [Enterprise_Architecture_Overview.pdf, Page 3] (Sim: 0.792)
🔍 Citation Verification: ✅ PASSED (Page 3 cited)

[Test Case 2] Category: Architectural Analysis
❓ Question: How does the architecture enforce multi-tenant isolation and security?
💬 Answer:
1. Database-level isolation using Supabase Row Level Security [Enterprise_Architecture_Overview.pdf, Page 2]
2. Strict partitioning of vector queries by auth.uid() matching user_id [Enterprise_Architecture_Overview.pdf, Page 2]
3. Storage isolation where private documents are stored in the dedicated 'user-documents' storage bucket [Enterprise_Architecture_Overview.pdf, Page 2]
📎 Citations:
   • [Enterprise_Architecture_Overview.pdf, Page 2] (Sim: 0.610)
🔍 Citation Verification: ✅ PASSED (Page 2 cited)

[Test Case 3] Category: Anti-Hallucination Guardrail
❓ Question: What is the capital of Mars and the average Martian rainfall?
💬 Answer:
I could not find the answer in your documents.
📎 Citations: None (Refusal / Non-grounded query)
🔍 Anti-Hallucination Guardrail: ✅ PASSED (Strict refusal executed)
```

