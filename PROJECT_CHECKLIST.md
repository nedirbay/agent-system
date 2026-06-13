# Proýekt Sanawy — AI Multi-Agent Platform

> `PROJECT_ROADMAP.md` boýunça 10 faza / 32 tabşyryk.
> ✅ = doly edildi · 🟡 = diňe scaffold (logika ýok) · ⬜ = başlanmadyk
> Iň soňky täzeleniş: 2026-06-13 (Faza 6 — Memory ulgamy doly: session / long-term / Memory Agent)

---

## 📦 Infrastruktura we esas (Foundation)

- [x] ✅ **Talaplaryň derňewi** — 11 sany spesifikasiýa resminamasy (`SYSTEM_REQUIREMENTS`, `HIGH_LEVEL_ARCHITECTURE`, ...)
- [x] ✅ **Ýokary derejeli arhitektura** — clean / hexagonal dizaýn
- [x] ✅ **Proýekt gurluşy** — frontend (Vue 3 + Vite + TS + Tailwind v4 + Element Plus) + backend (FastAPI)
- [x] ✅ **13 modul scaffold** (domain / application / infrastructure / presentation)
- [x] ✅ **Docker Compose** — Postgres, Redis, Qdrant, Kafka, MinIO
- [x] ✅ **Infra serwerde işleýär (172.16.6.76)** — 5 hyzmat hem işleýär; Postgres `5433`, Qdrant `6335/6336` (öňki serwisler bilen çaknyşmazlyk üçin). Backend `.env` şoňa baglandy, migrasiýa goýberildi.
- [x] ✅ **Alembic başlangyç migrasiýasy** — 13 tablisa, round-trip barlandy
- [x] ✅ **Auth (username + parol)** — register / login + JWT, testler geçýär
- [x] ✅ **Marketing sahypalary** — Home / Features / About + dark mode

---

## ✅ Faza 2 — Maglumat ýükleme (Data Ingestion) — DOLY TAMAMLANDY

> Faýl ýükleme → parsing → OCR → metadata zynjyry doly işleýär we serwere garşy synag edildi.

### Faza 2 — Maglumat ýükleme (Data Ingestion)
- [x] ✅ **Tabşyryk 4 — Faýl ýükleme** — `POST /documents/upload` (MinIO-a real upload) + presigned download URL. Uçdan-uca synag edildi (serwerdäki MinIO + Postgres).
- [x] ✅ **Tabşyryk 5 — Faýl parsing** — `POST /documents/{id}/parse` (MinIO-dan ýükläp, teksti çykarýar). PDF (pypdf) / DOCX + tablisalar (python-docx) / XLSX (openpyxl) / tekst. `extracted_text` + `page_count` saklanýar, status `parsed`. 4 format hem uçdan-uca synag edildi.
- [x] ✅ **Tabşyryk 6 — OCR** — Tesseract (türkmen `tuk`+eng+rus) + poppler. Surat faýllary (PNG/JPG/TIFF…) göni OCR; tekst gatlagy boş **skan-PDF** awtomatik OCR-a geçýär. Jogapda `ocr_used` baýdagy. Surat we skan-PDF uçdan-uca synag edildi.
- [x] ✅ **Tabşyryk 7 — Metadata çykarmak** — parse wagtynda `doc_metadata` (JSON) saklanýar: kontent statistikasy (char/word/line sany + **dil kesgitlemesi** langdetect), format props (PDF/DOCX/XLSX — awtor, title, sene…). DOCX/XLSX/rusça tekst uçdan-uca synag edildi.

---

## ✅ Faza 3 — Bilim gatlagy (Knowledge Layer) — DOLY TAMAMLANDY

> RAG ingestion + retrieval zynjyry doly işleýär: chunk → embed → Qdrant → gözleg.
> Serwerdäki Postgres (chunk tablisasy) + Qdrant (`6335`, `documents` kolleksiýasy) bilen uçdan-uca synag edildi.

- [x] ✅ **Tabşyryk 8 — Chunk generasiýasy** — `StructureAwareChunker`: struktura-duýgur (paragraf/tablisa setir) bölmek, token-çäkli (~512 token, 64 overlap, max 1024), `document_chunks` tablisasy + repozitoriý. Köp-chunk + overlap synag edildi.
- [x] ✅ **Tabşyryk 9 — Embedding pipeline** — `EmbeddingProvider` port + offline `HashingEmbeddingProvider` (256-dim, kontent-hash keş). Hiç API/GPU gerek däl; Voyage/BGE-M3 üçin çalşylýan. Meňzeşlik tertibi synag edildi.
- [x] ✅ **Tabşyryk 10 — Vektor saklama** — `VectorStore` port + `QdrantVectorStore` (async client, kolleksiýa döretmek, upsert, payload-filter gözleg). `POST /knowledge/documents/{id}/index` + `POST /knowledge/search`. Topical ranking 4/4 query dogry; document_id boýunça filter + idempotent re-index synag edildi.

---

## 🟡 Galan modullar — scaffold bar, EMMA hakyky logika ÝOK

> Aşakdaky modullaryň köpüsinde häzir diňe boş CRUD scaffold bar — hakyky iş logikasy ýazylmaly.

### Faza 4 — Orchestrator — DOLY TAMAMLANDY
- [x] ✅ **Tabşyryk 11 — Tabşyryk meýilleşdirmek**
- [x] ✅ **Tabşyryk 12 — Agent marşrutizasiýasy**
- [x] ✅ **Tabşyryk 13 — Workflow dolandyryşy** — Dynamic plan → persisted workflow instance → ordered step execution. Context passing, retry, human approval wait/resume/reject lifecycle bar. `backend/tests/test_workflow_engine.py` bilen awtomat test edildi.

### Faza 5 — Ýöriteleşdirilen agentler — DOLY TAMAMLANDY
- [x] ✅ **Tabşyryk 14 — Document Agent** — Parsed dokumentiň üstünden summary, classification, categories, language + top terms çykarýar; netijäni `doc_metadata.document_agent` içine ýazýar we statusy `analyzed` edýär. Endpoint: `POST /agents/document-agent/documents/{document_id}/analyze`. `backend/tests/test_document_agent.py` bilen awtomat test edildi.
- [x] ✅ **Tabşyryk 15 — Analysis Agent** — Birnäçe parsed/analyzed dokumentiň üstünden agregat statistika (söz/char sany, ortaça uzynlyk, diller, kategoriýalar, top terminler, iň uly dokument), trendler, findings we recommendations çykarýar; netijäni `AnalysisJob` (kind=`document_analysis`, status=`completed`) hökmünde saklaýar. Endpoint: `POST /analysis/documents/analyze`. `backend/tests/test_analysis_agent.py` bilen awtomat test edildi (3 test geçýär).
- [x] ✅ **Tabşyryk 16 — Q&A Agent** (RAG — `LLM_AND_RAG_STRATEGY.md`) — Sorag → vektor gözleg (retrieval) → diňe tapylan kontekste daýanýan jogap + sitatalar (citations). LLMProvider (Ollama) bilen grounded jogap; retrieval boş bolsa hallýusinasiýa etmän ret edýär; LLM elýeterli däl bolsa ekstraktiw jogaba degrade bolýar (FH-001). Endpoint: `POST /qa/ask`. `backend/tests/test_qa_agent.py` (5 test geçýär).
- [x] ✅ **Tabşyryk 17 — Reporting Agent** — Analysis Agent jobynyň netijesinden okalýan hasabat (Markdown / tekst) generasiýa edýär: summary, statistika, trendler, findings, recommendations. Netije `Report` setiri hökmünde (`content` sütüni — täze Alembic migrasiýa `a1c4e7b2f9d0`, round-trip barlandy) saklanýar. Endpoint: `POST /reports/generate-from-analysis`. `backend/tests/test_report_agent.py` (4 test geçýär).

### Faza 6 — Ýat ulgamy (Memory) — DOLY TAMAMLANDY
- [x] ✅ **Tabşyryk 18 — Sessiýa ýady (Redis)** — Häzirki söhbetdeşligiň turnlary Redis-de saklanýar (30 gün TTL, DATABASE_DESIGN retention). `SessionMemoryService`: turn goşmak, `[Memory]` blok üçin kontekst ýygnamak, arassalamak. Kontekst gysmak (ME-002): turn sany `max_turns`-dan geçende köne turnlar awtomat summary-a bukulýar, diňe iň soňkular galýar. Redis elýeterli däl bolsa in-memory adaptere degrade bolýar. Endpointler: `POST/GET /memory/sessions/{id}[/turns]`, `DELETE /memory/sessions/{id}`. Redis serwere garşy uçdan-uca synag edildi.
- [x] ✅ **Tabşyryk 19 — Uzak möhletli ýat** — Geçmiş tabşyryklaryň ýady: `MemoryItem` + `MemoryReference` (täze `memory_references` tablisasy — Alembic migrasiýa `b2d5f8c3a1e4`, round-trip barlandy). `LongTermMemoryService.remember()` ýady saklaýar, referensleri belleýär, embed edip aýratyn Qdrant kolleksiýasyna (`memory`) ýazýar; `recall()` semantik gözleg + importance agram bilen tertipleýär. Embed/vektor näsaz bolsa iň soňky ýatlara degrade bolýar (FH-001). Endpointler: `POST /memory/long-term`, `POST /memory/long-term/recall`. Qdrant serwere garşy uçdan-uca synag edildi.
- [x] ✅ **Tabşyryk 20 — Bilim dolandyryşy (Memory Agent)** — `MemoryAgentService` birleşdirilen `[Memory]` blogyny ýygnaýar (ME-001): working + session + long-term + knowledge (RAG retrieval) ýat zolaklary. Her zolak özbaşdak degrade bolýar (session ýok / long-term boş / retriever elýeterli däl bolsa diňe şol bölüm aýrylýar). Endpoint: `POST /memory/context`. `backend/tests/test_memory.py` (12 test geçýär).

### Faza 7 — Computer Use
- [ ] ⬜ **Tabşyryk 21 — Brauzer operasiýalary**
- [ ] ⬜ **Tabşyryk 22 — Desktop operasiýalary**
- [ ] ⬜ **Tabşyryk 23 — Howpsuz ýerine ýetiriş (sandbox)**

### Faza 8 — Ulanyjy interfeýsi (UI)
- [ ] ⬜ **Tabşyryk 24 — Chat interfeýsi**
- [ ] ⬜ **Tabşyryk 25 — Workspace**
- [ ] ⬜ **Tabşyryk 26 — Dashboard**
- [ ] ⬜ **Frontend → Backend baglanyşygy** (API client, real login / register form)

### Faza 9 — Monitoring
- [x] ✅ **Tabşyryk 27 — Logging** (structlog konfigurasiýasy bar)
- [ ] ⬜ **Tabşyryk 28 — Performance tracking** (metrikalar)
- [ ] 🟡 **Tabşyryk 29 — Audit ulgamy** (modul scaffold bar, logika ýok)

### Faza 10 — Önümçilige taýýarlyk
- [ ] ⬜ **Tabşyryk 30 — Howpsuzlyk barlagy** (`SECURITY_ARCHITECTURE.md`)
- [ ] ⬜ **Tabşyryk 31 — Masştablaşma barlagy**
- [ ] ⬜ **Tabşyryk 32 — Jemleýji walidasiýa** (CI/CD, integrasiýa testleri)

---

## 📊 Gysga jemi

| Ýagdaý | San |
|--------|-----|
| ✅ Doly edildi | Foundation (3) + infra (serwerde) + auth + logging + **Faza 2 (Tabşyryk 4–7)** + **Faza 3 doly (Tabşyryk 8–10)** + **Faza 4 doly (Tabşyryk 11–13)** + **Faza 5 doly (Tabşyryk 14–17: Document / Analysis / Q&A / Reporting Agent)** + **Faza 6 doly (Tabşyryk 18–20: session / long-term / Memory Agent)** |
| 🟡 Diňe scaffold | ~8 modul (CRUD bar, biznes logika ýok) |
| ⬜ Asla başlanmadyk | Faza 7–10 (Computer Use, UI, monitoring, production…) |

**Ýagny:** Esas / skelet **100% taýýar**, **Faza 2 (maglumat ýükleme), Faza 3 (RAG — chunking + embedding + Qdrant gözleg), Faza 4 (Orchestrator — planning/routing/workflow lifecycle), Faza 5 doly (Document / Analysis / Q&A / Reporting Agent) we Faza 6 doly (Memory — Redis session ýady + semantik long-term ýat + birleşdirilen Memory Agent konteksti) işleýär**,
indi Faza 7 (Computer Use), UI we ondan soňkular ýazylmaly.
