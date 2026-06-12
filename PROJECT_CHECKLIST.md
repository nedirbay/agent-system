# Proýekt Sanawy — AI Multi-Agent Platform

> `PROJECT_ROADMAP.md` boýunça 10 faza / 32 tabşyryk.
> ✅ = doly edildi · 🟡 = diňe scaffold (logika ýok) · ⬜ = başlanmadyk
> Iň soňky täzeleniş: 2026-06-12

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

## 🟡 Galan modullar — scaffold bar, EMMA hakyky logika ÝOK

> Aşakdaky modullaryň köpüsinde häzir diňe boş CRUD scaffold bar — hakyky iş logikasy ýazylmaly.

### Faza 3 — Bilim gatlagy (Knowledge Layer)
- [ ] ⬜ **Tabşyryk 8 — Chunk generasiýasy**
- [ ] ⬜ **Tabşyryk 9 — Embedding pipeline** (LLM / embedding modeli)
- [ ] ⬜ **Tabşyryk 10 — Vektor saklama** (Qdrant integrasiýasy)

### Faza 4 — Orchestrator
- [ ] ⬜ **Tabşyryk 11 — Tabşyryk meýilleşdirmek**
- [ ] ⬜ **Tabşyryk 12 — Agent marşrutizasiýasy**
- [ ] ⬜ **Tabşyryk 13 — Workflow dolandyryşy** (`WORKFLOW_ENGINE_SPECIFICATION.md`)

### Faza 5 — Ýöriteleşdirilen agentler
- [ ] ⬜ **Tabşyryk 14 — Document Agent**
- [ ] ⬜ **Tabşyryk 15 — Analysis Agent**
- [ ] ⬜ **Tabşyryk 16 — Q&A Agent** (RAG — `LLM_AND_RAG_STRATEGY.md`)
- [ ] ⬜ **Tabşyryk 17 — Reporting Agent**

### Faza 6 — Ýat ulgamy (Memory)
- [ ] ⬜ **Tabşyryk 18 — Sessiýa ýady** (Redis)
- [ ] ⬜ **Tabşyryk 19 — Uzak möhletli ýat**
- [ ] ⬜ **Tabşyryk 20 — Bilim dolandyryşy**

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
| ✅ Doly edildi | Foundation (3) + infra (serwerde) + auth + logging + **Faza 2 doly (Tabşyryk 4–7)** |
| 🟡 Diňe scaffold | ~11 modul (CRUD bar, biznes logika ýok) |
| ⬜ Asla başlanmadyk | Faza 3–10 (chunking, embedding, agentler, workflow, UI…) |

**Ýagny:** Esas / skelet **100% taýýar**, **Faza 2 (maglumat ýükleme zynjyry) doly işleýär**,
indi Faza 3 (Bilim gatlagy — chunking + embedding + Qdrant) we ondan soňkular ýazylmaly.
