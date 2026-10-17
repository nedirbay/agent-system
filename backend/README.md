# AI Multi-Agent Platform — Backend (Türkmen dilinde)

FastAPI bilen gurlan, AI Multi-Agent Knowledge & Automation Platform-yň backend bölegi. Bu taslama **Clean / Hexagonal (Geksagonal) Arhitektura** ýörelgelerine we taslamanyň spesifikasiýalaryna (`SYSTEM_REQUIREMENTS.md`, `HIGH_LEVEL_ARCHITECTURE.md`, `DATABASE_DESIGN.md`, `EVENT_BUS_SPECIFICATION.md`, `TECH_STACK_DECISION.md`) laýyklykda işlenip düzüldi.

---

## 🏗️ Ulgamyň Arhitekturasy (Architecture)

Her bir aýratyn aýratynlyk (feature) `app/modules/<module>/` bukdasynda ýerleşýär we dördüňji gatlaga bölünýär. Bu ýerde garaşlylyklar hemişe **içeri tarapa** (Presentation → Application → Domain; Infrastructure bolsa Domain portlaryny implementasiýa edýär) gönükdirilendir:

```text
app/modules/<module>/
├── domain/              # Entity-ler we repository portlary (hemişe garaşsyz, framework-syz)
│   ├── entities.py
│   └── repositories.py
├── application/         # Use-case (ulanyş senariýalary) servisleri we command DTO-lar
│   ├── commands.py
│   └── services.py
├── infrastructure/      # SQLAlchemy ORM modelleri we repository adapterleri
│   ├── models.py
│   └── repositories.py
└── presentation/        # FastAPI router, Pydantic shemalary we DI (Dependency Injection) wiring
    ├── router.py
    ├── schemas.py
    └── dependencies.py
```

Ulgamyň umumy we kesişýän (cross-cutting) infrastruktura bölekleri bolsa `app/core/` içinde jemlenendir. Bu bukda konfigurasiýany, database sesionlaryny, bcrypt + JWT howpsuzlygyny, structlog arkaly structured loglary, Event Bus interfeýslerini we Redis / Qdrant / MinIO üçin "lazy" (giçki/zerurlyk bolanda işe düşýän) client-leri öz içine alýar.

---

## 🛠️ Modullar we Edilen Işler (Implemented Modules & Features)

Taslama boýunça **10 faza** we **32 tabşyryk** dolulygyna tamamlandy we serwerde synag edildi. Aşakda backend tarapynda ýerine ýetirilen işleriň jikme-jik beýany berilýär:

### 1. Auth (Awtorizasiýa we Hasaba Alyş)
* **Ulanyjy hasaba alyş we login:** `POST /api/v1/auth/register` we `POST /api/v1/auth/login` endpointleri gurnaldy.
* **JWT Howpsuzlygy:** Ulanyjy identifikasiýasy we sessiýa dolandyryşy üçin stateless JWT tokenleri ulanýar. Parollar bcrypt arkaly heşlenýär we gizlin saklanýar.
* **Goralan Endpoint-ler:** `GET /api/v1/auth/me` ýaly endpointler diňe dogry JWT Bearer token bilen elýeterlidir.

### 2. Documents (Maglumat we Faýl Ýükleme - Faza 2)
* **MinIO Object Storage:** Faýllary hasapda saklamak üçin MinIO ulgamyna göni upload edýän `POST /documents/upload` endpointi we presigned download URL alýan `GET /documents/{id}/download-url` gurnaldy.
* **Faýl Parsing:** PDF (`pypdf`), DOCX (`python-docx`), XLSX (`openpyxl`) we adaty tekst formatlaryny goldaýar. Tekstler awtomatik çykarylyp, statusy `parsed` edilip saklanýar.
* **OCR (Skan-PDF we Suratlar):** Eger PDF-iň içinde tekst gatlagy bolmasa ýa-da faýl surat (PNG, JPG, TIFF) bolsa, Tesseract OCR (default `tuk+eng+rus`) we poppler arkaly awtomatik surat okalyp tekst formatyna geçirilýär.
* **Metadata we Dil Kesgitlemek:** Parsed faýllaryň söz/simwol sany, awtorlary, döredilen wagty we dilleri `langdetect` arkaly kesgitlenip `doc_metadata` içinde saklanýar.

### 3. Knowledge Layer (Bilim we Vektor Gatlagy - Faza 3)
* **Structure-Aware Chunking:** Paragraf we tablisa setirlerine duýgur bolan `StructureAwareChunker` arkaly tekstler optimal böleklere (~512 token) bölünýär.
* **Embedding Pipeline:** `HashingEmbeddingProvider` arkaly offline heşleme keş ulgamy döredildi. Bu ulgam hiç hili GPU ýa-da daşarky API talap etmän, meňzeşlik we semantik barlaglary deterministik amala aşyrýar.
* **Qdrant Vector Store:** Çykarylan chunklar we heşler Qdrant vector database-indäki `documents` kolleksiýasyna ýazylýar. payload-filter goldawy bar.

### 4. Orchestrator we Workflows (Faza 4)
* **Dynamic Workflows:** Ulgam dynamic planlar döredip, persisted workflow instance-lar arkaly ädim-ädim işlemegi goldaýar.
* **Retry we Context Passing:** Şowsuz ädimleri gaýtadan işletmek (retry), iş statusyny saklamak we kontekstleri indiki ädimlere geçirmek mümkinçiligi döredildi.
* **Human Approval (Adam Tassyklamasy):** Düýgur amallar ýerine ýetirilmezden öň ulgam "wait" ýagdaýyna geçýär we administratoryň tassyklamagyna (`approve/reject`) garaşýar.

### 5. Ýöriteleşdirilen Agentler (Specialist Agents - Faza 5)
* **Document Agent:** Ýeke-täk resminamany analiz edip, gysgaça mazmunyny (summary), kategoriýalaryny, esasy terminlerini we dilini çykarýar. Netijäni `POST /agents/document-agent/documents/{document_id}/analyze` endpointi arkaly amala aşyrýar.
* **Analysis Agent:** Birnäçe resminamanyň üstünden agregat hasabatlary, kategoriýalaryň paýlanyşyny, umumy söz sanlaryny, trendleri we maslahatlary çykarýar (`POST /analysis/documents/analyze`).
* **QA Agent (RAG):** Soraglara semantik gözleg arkaly tapylan subutnamalar esasynda jogap berýär. Tapylan subutnama ýok bolsa hallýusinasiýa etmezlik üçin jogap bermekden ýüz öwürýär. Vektor baza elýeterli bolmasa adaty ekstraktiw jogaba degredasiýa bolýar.
* **Reporting Agent:** Analysis Agent tarapyndan ýerine ýetirilen joblary Markdown hasabaty hökmünde eksport edýär.

### 6. Memory (Ýat Ulgamy - Faza 6)
* **Session Memory (Redis):** Häzirki gepleşikleri Redis cache-da 30 gün TTL bilen saklaýar. Gepleşik möçberi çäkden geçende köne habarlar awtomatik gysylyp summary-a öwrülýär. Redis elýeterli bolmasa in-memory degradasiýa guruldy.
* **Long-Term Memory:** Öňki tabşyryklary we olaryň referenslerini semantic gözleg arkaly yzyna çagyrýar. Maglumatlar Qdrant vector database-iň `memory` kolleksiýasynda saklanýar.
* **Memory Agent:** Ähli working, session, long-term we knowledge kontekstlerini birleşdirip, `[Memory]` blogy hökmünde gaýtarýar.

### 7. Computer Use / Safe Execution (Faza 7)
* **Browser Driver:** `SimulatedBrowserDriver` arkaly brauzer hereketleri (nawigasiýa, click, form fill, submit, download, screenshot) offline placeholder görnüşinde imitasiýa edilýär. Duýgur maglumatlar (parol) loglarda maskalanýar.
* **Desktop Driver:** `LocalSandboxDesktopDriver` arkaly hakyky faýl amallary we çäklendirilen prosesleri (run_process) diňe rugsat berlen `scratch` bukdasynyň içinde ýerine ýetirýär.
* **Safe Execution Sandbox:** Her bir amaly `ALLOW`, `DENY` we `REQUIRE_APPROVAL` syýasatlaryna garşy barlap, rugsat berilmedik daşarky aragatnaşyklary we pozmak amallaryny bloka salýar.

### 8. Monitoring we Audit (Faza 9)
* **Structured Logging & Correlation ID:** `structlog` middleware arkaly her bir HTTP soragyna `Correlation-ID` (x-correlation-id) baglanýar we loglarda yzarlanýar.
* **Metrics (Prometheus):** request/error sanlary, error rate, p50/p90/p99 latency we işjeň task sanlary ýygnalyp, `/monitoring/metrics/prometheus` endpointi arkaly eksport edilýär.
* **Tamper-Evident Audit:** Her bir audit logs SHA-256 kriptografik zynjyry arkaly öňki heşe baglanyp ýazylýar (`prev_hash` -> `entry_hash`). Islendik log pozulanda ýa-da üýtgedilende zynjyr bozulýar we `/audit/verify` arkaly derrew anyklanýar.

### 9. Önümçilige Taýýarlyk (Faza 10)
* **Security Headers:** ASGI middleware arkaly `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` we beýleki howpsuzlyk header-leri ähli jogaplarda gaýtarylýar.
* **Readiness Aggregator:** `/health/ready` barlagy PostgreSQL, Redis we Qdrant ýagdaýlaryny barlap aggregator baha berýär. PostgreSQL ýaly esasy servis dowm bolsa `503 Service Unavailable` gaýtarýar, emma Redis ýaly komponentler degraded ýagdaýda hem işläp bilýär.
* **Unit & Smoke Tests:** 60-dan gowrak pytest testleri (sqlite in-memory arkaly) doly we üstünlikli işleýär.

---

## 📁 Taslamanyň Gurluşy (Repository Layout)

```text
backend/
├── app/
│   ├── api/                 # API Router-i birleşdiriji gatlak
│   ├── core/                # Umumy konfigurasiýa we esasy hyzmatlar
│   │   ├── auth.py          # JWT awtorizasiýa dependency-si
│   │   ├── clients.py       # Redis, Qdrant we MinIO "lazy" client-leri
│   │   ├── config.py        # Environment variables we Settings klassy
│   │   ├── crypto.py        # Audit log-laryň heş zynjyryny gurujy
│   │   ├── database.py      # Async SQLAlchemy PostgreSQL sessiýasy
│   │   ├── event_bus.py     # Kafka ýa-da in-memory event bus
│   │   ├── exceptions.py    # Global FastAPI error handler
│   │   ├── logging.py       # Structlog konfigurasiýasy
│   │   ├── metrics.py       # Prometheus/App metrics registry
│   │   ├── middleware.py    # Correlation ID + Security headers
│   │   ├── readiness.py     # Database/Redis/Qdrant barlagy
│   │   ├── registry.py      # Orm model bellige alyş (Alembic üçin)
│   │   └── security.py      # Parol heş we JWT generator
│   ├── modules/             # Hexagonal dizaýndaky biznes logikalary
│   │   ├── agents           # Agent registrasiýasy we dolandyryşy
│   │   ├── analysis         # Multi-document analiz agenti
│   │   ├── audit            # Append-only audit yzy (SHA-256 zynjyry)
│   │   ├── auth             # Ulanyjy auth/register logikasy
│   │   ├── connectors       # Daşarky birikmeler dizaýny
│   │   ├── documents        # Faýl ýükleme, PDF/DOCX parser, OCR we metadata
│   │   ├── events           # Event bus we Kafka habarlaşygy
│   │   ├── execution        # Computer Use sandbox (fill/click/process)
│   │   ├── knowledge        # Chunking we Qdrant indexing
│   │   ├── memory           # Redis we Qdrant memory (Working, Session, Long-term)
│   │   ├── monitoring       # Metrikalar API
│   │   ├── notifications    # Duýduryş scaffold-y
│   │   ├── qa               # RAG we QA agent logikasy
│   │   ├── reports          # Hasabat eksport logikasy (Markdown)
│   │   └── workflows        # Ädim-ädim workflow engine we tassyklama akymy
│   └── shared/              # Paýlaşylýan interfeýsler (LLM provider we ş.m.)
├── migrations/              # Alembic database migrasiýa faýllary
├── tests/                   # Pytest testleri
├── docker-compose.yml       # Local ulanmak üçin docker hyzmatlary
├── docker-compose.server.yml# Server (172.16.6.76) üçin port variantlary
└── requirements.txt         # Gerekli python paketleri
```

---

## ⚙️ Gurnamak we Işletmek (Setup & Installation)

### Prerequisitler:
* Python 3.11 ýa-da täzeräk
* Docker we Docker Compose
* Tesseract OCR we Poppler utilities (surat parsing we OCR üçin)

Ubuntu-da OCR gurnamak üçin:
```bash
sudo apt-get install tesseract-ocr poppler-utils
```

### Setup:

1. Gerekli Python bibliotekalaryny gurnamak:
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. `.env` faýlyny döretmek:
   ```bash
   cp .env.example .env
   ```
   *Eger backend docker-compose-yň içindäki local bazalara birikmeli bolsa, default bahalary saklap bilersiňiz.*

3. Docker hyzmatlaryny işletmek:
   ```bash
   docker compose up -d
   ```
   *Bu komanda Postgres, Redis, Qdrant, Kafka we MinIO hyzmatlaryny işleder.*

4. Database migrasiýasyny ýerine ýetirmek:
   ```bash
   alembic upgrade head
   ```

5. FastAPI backend-i işletmek:
   ```bash
   uvicorn app.main:app --reload
   ```

Default salgylar:
* API: `http://localhost:8000/`
* Swagger UI Docs: `http://localhost:8000/docs`
* Health check: `http://localhost:8000/health`
* Readiness check: `http://localhost:8000/health/ready`

---

## 🧪 Testleri Işletmek (Running Tests)

Backend synaglary SQLite in-memory database ulanýar, şonuň üçin daşarky Docker hyzmatlaryny işletmän hem testleri goýberip bilersiňiz:

```bash
cd backend
pytest
```

Jemi 60 sany integrasion we smoke testler bar bolup, hemmesi üstünlikli geçýär.
