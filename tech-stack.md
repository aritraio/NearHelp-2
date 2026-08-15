# NearHelp AI — Technology Stack

> Layer-by-layer choices with reasoning, alternatives, versions, and costs. Companion to `Architecture.md` (how it fits together) and `BLUEPRINT.md` (scope). Rule applied throughout: **one primary technology per layer, chosen for a solo developer on a 4-month timeline and a ₹0 budget.**

---

## Table of Contents

1. [Stack at a Glance](#1-stack-at-a-glance)
2. [Client Layer](#2-client-layer)
3. [Backend Layer](#3-backend-layer)
4. [Data Layer](#4-data-layer)
5. [AI Layer](#5-ai-layer)
6. [Infrastructure & DevOps](#6-infrastructure--devops)
7. [Quality & Testing](#7-quality--testing)
8. [Architecture Decision Records](#8-architecture-decision-records)
9. [Cost Summary](#9-cost-summary)
10. [Version Pinning](#10-version-pinning)

---

## 1. Stack at a Glance

| Layer | Technology | Role in NearHelp |
| --- | --- | --- |
| Mobile app | **Kotlin + Jetpack Compose (Material 3)** | Citizen + Responder flows, hold-for-SOS UI |
| Maps | **Google Maps SDK for Android** (+ Compose wrapper) | Incident map, markers, directions deep-link |
| Push | **Firebase Cloud Messaging (data messages)** | SOS alerts that wake backgrounded apps |
| Backend | **Python 3.12 + FastAPI** | REST API, WebSocket server, all coordination logic |
| ORM / migrations | **SQLAlchemy 2.0 + GeoAlchemy2 + Alembic** | Models incl. PostGIS geometry, versioned schema |
| Database | **PostgreSQL 16 + PostGIS + pgvector** | Operational data, geo queries, RAG vectors — one engine |
| Cache / queue | **Redis 7 + arq** | Idempotency, rate limits, background jobs |
| LLM | **Google Gemini 2.5** (structured output) | Classification, severity, guidance generation, summaries |
| Embeddings | **sentence-transformers `all-MiniLM-L6-v2`** | Corpus + query embeddings (384-dim) |
| Auth | **JWT (PyJWT) + bcrypt** | Email/password MVP; simple, fully testable |
| Containers | **Docker + Docker Compose** | Reproducible dev = deployable demo |
| Hosting | **Google Cloud Run + Neon + Upstash** | Serverless backend, managed Postgres/Redis |
| Scheduling | **Cloud Scheduler** | Escalation tick (10 s), nightly retention |
| CI/CD | **GitHub Actions** | Lint, types, tests, build, deploy |
| Monitoring | **Sentry + structured JSON logs** | Errors + correlation by `sos_id` |
| Docs | **OpenAPI (auto, FastAPI) + Mermaid** | API reference, architecture diagrams |
| Design system | **Compose tokens per `DESIGN.md`** | Mint/glass calm UI, red emergency mode |

---

## 2. Client Layer

### 2.1 Kotlin + Jetpack Compose — *primary*

**Why:** Declarative UI maps cleanly to a state-driven app (calm → incident → resolved are just states); coroutines/Flow are the natural fit for a WebSocket client and location streams; Material 3 is customized by a single token theme (`DESIGN.md` §2) instead of fighting XML themes.

**What it replaces:**
- *XML Views + Fragments* — more boilerplate, state syncing pain for a live-map app.
- *Flutter/React Native* — fine tools, but the project already needs Kotlin-native behavior (foreground services, FCM data-message handling, battery-optimization exemptions, OEM autostart quirks). Going native removes a bridge layer in exactly the riskiest part of the app.

**Libraries (client):**

| Library | Purpose |
| --- | --- |
| Retrofit + OkHttp | REST client (JWT interceptor, idempotency-header interceptor) |
| kotlinx-serialization | JSON models |
| okhttp WebSocket (via a wrapper) | Event channel client |
| Play Services Location (FusedLocationProvider) | Adaptive-interval GPS streaming |
| Firebase Messaging | FCM data-message receiver + ACK |
| Hilt | DI (token store, API, WS client) |
| DataStore (Preferences) | Token + settings storage |
| Coil | Certificate image loading |
| google-maps-android-compose | Map composable + custom markers |

### 2.2 Google Maps SDK — *primary*

**Why:** Best base-map quality and coverage for India (the demo region); Compose wrapper exists; traffic layer and directions deep-links cover MVP routing with zero server work. ETA for the MVP is straight-line ÷ realistic speed (`improvements.md` §2.5) — no Directions API billing, no key on the critical path. Static resources (hospitals, police/fire stations) come from a one-time OpenStreetMap/Overpass export committed as JSON.

**Alternative considered:** Mapbox (comparable quality, generous free tier) — rejected only because Google's India coverage and the team's familiarity outweigh it. osmdroid (fully free, no key) is the offline-first fallback if Maps billing ever becomes a blocker.

### 2.3 Firebase Cloud Messaging — *primary*

**Why:** The only reliable way to reach a backgrounded Android app — WebSockets die when Android dozes, FCM rides Play Services. Chosen delivery shape: **high-priority data messages**, app-side rendering (full-screen SOS activity, DRILL banners). Delivery confirmation is app-level ACK (`POST /api/sos/{id}/ack`) because FCM display-message receipts are not dependable ground truth (`improvements.md` §1.3).

**Alternative considered:** Web Push / MQTT / self-hosted sockets — all require a foreground app or a persistent service that OEM battery managers kill. Not viable for the responder-alert path in India.

---

## 3. Backend Layer

### 3.1 Python 3.12 + FastAPI — *primary*

**Why:**
- **Async-first** — hundreds of concurrent WebSocket connections and parallel FCM/LLM I/O are the normal case, not an optimization.
- **Pydantic v2 validation** at every boundary — malformed mobile payloads die at the edge with clear errors.
- **Auto OpenAPI docs** at `/docs` — the API reference is a deliverable for free.
- **Native WebSocket support** in the same process as REST.
- One language across backend, AI (transformers, sentence-transformers), and the Digital Twin simulator — a solo developer's most precious optimization.

**Alternatives rejected:**

| Option | Why not |
| --- | --- |
| Django + DRF | Async geo + WebSocket story is bolted-on; ORM's PostGIS path is clunkier than GeoAlchemy2 |
| Flask | No native async/WebSocket; you'd assemble FastAPI badly by hand |
| Node/Express or NestJS | Would split the project into two languages (Python is non-negotiable for the AI side) |
| Go | Superb fit for the coordination layer, wrong fit for the AI/simulator side for a solo student |

**Libraries (backend):**

| Library | Purpose |
| --- | --- |
| Uvicorn | ASGI server (Cloud Run entrypoint) |
| SQLAlchemy 2.0 (async) + GeoAlchemy2 | Models, PostGIS `GEOGRAPHY(Point)` columns |
| asyncpg | Driver — fastest async Postgres client |
| Alembic | Migrations (run as a pre-deploy step) |
| pydantic-settings | Typed config from env |
| PyJWT + bcrypt | Token issue/verify, password hashing |
| arq | Redis-based async job queue (fan-out, AI jobs, retention) |
| firebase-admin | FCM v1 sends |
| google-genai | Gemini client (behind `LLMClient` abstraction) |
| structlog / stdlib JSON logging | Correlated logs |
| sentry-sdk | Error tracking |
| ruff + mypy | Lint + types (CI gates) |

### 3.2 JWT + bcrypt auth — *primary (MVP)*

**Why:** One mechanism, fully under test control, no third party on the login critical path. Access 15 min / rotating refresh 7 days, revocation list in Redis. The proposal's Firebase Auth (Google Sign-In, phone OTP) is **V1** — wiring it *and* custom JWT was double bookkeeping with no MVP payoff.

---

## 4. Data Layer

### 4.1 PostgreSQL 16 + PostGIS + pgvector — *primary*

**Why one engine wins:**
- **ACID transactions** for the SOS state machine — an emergency event must never be half-created.
- **PostGIS** is the reference geospatial implementation: `ST_DWithin` + GiST indexes answer "who is within R meters" in milliseconds at any scale the project will see, and it's the benchmark subject itself.
- **pgvector** absorbs the vector-store role (HNSW, cosine) — one backup, one migration tool, one connection pool, one thing to learn.
- Managed hosting with all three extensions is free-tier friendly (Neon).

**Alternatives rejected:**

| Option | Why not |
| --- | --- |
| MongoDB + 2dsphere | Document model fine, but eventual-consistency semantics and weaker transactional guarantees on the critical path; adds a second engine anyway for relations |
| Postgres + separate vector DB (Chroma/Pinecone/Weaviate) | Another service to run, back up, and debug for a corpus of ~500–2,000 chunks — pure overhead (BLUEPRINT D2). Chroma remains an acceptable local fallback if pgvector setup blocks |
| SQLite (+SpatiaLite) | Tempting for a college project; no concurrent writers, poor story for Cloud Run, no pgvector |

**Schema ownership:** `BLUEPRINT.md` §3 (ER + indexes) is authoritative; migrations live in Alembic, never hand-applied SQL.

### 4.2 Redis 7 (+ Upstash) — *primary*

**Why:** Idempotency keys, rate limits, refresh revocation, and arq's queue all want the same primitive: fast ephemeral state with TTLs. Correctness never depends on it — Postgres unique indexes backstop idempotency — so the free tier (Upstash) is fine, and single-instance MVP could technically run without it (kept anyway because arq and rate limiting want it from day one).

---

## 5. AI Layer

### 5.1 Gemini 2.5 — *primary LLM*

**Why:**
- **Structured (JSON-schema) output** — classification, severity, and guidance are parsed, not vibes; malformed output triggers the schema retry (`Architecture.md` §6).
- **Multilingual strength** — the demo region is bilingual (Bengali/Hindi/English); translation is a prompt away in V1.
- **Vision input** for photo classification (Phase 2 modality) without a second vendor.
- **Free tier** comfortably covers development, evaluation runs, and the demo.

**Alternative considered:** OpenAI GPT-4o-mini class models — equally viable; the `LLMClient` abstraction keeps the swap to an env var. Gemini won on free tier + multilingual + vision in one endpoint. Local models (Ollama) — no GPU laptop dependency wanted for the demo.

### 5.2 sentence-transformers `all-MiniLM-L6-v2` — *primary embeddings*

**Why:** 384-dim, CPU-fast, runs in-process at startup; for a corpus of this size, embedding quality is not the bottleneck (chunking strategy is — procedure-level chunks per `proposal.md` Module 11). Query-side latency ≈ milliseconds, which matters because queries happen inside the SOS path's parallel AI job.

**Alternative considered:** Gemini `text-embedding` — would offload compute but adds a network hop and quota dependency to retrieval; MiniLM keeps the hot path local. Upgrade path: swap embedder → re-embed corpus → rebuild HNSW index (one script).

### 5.3 RAG, not fine-tuning — *standing decision*

Corpus updates (new WHO guidance, regional protocols) must be a document drop, not a training run; citations require retrieval; no training data exists anyway. Retrieval is **hybrid** (pgvector cosine + Postgres full-text merge) — medical terminology is keyword-shaped, and the merge is an afternoon of code that also yields a report experiment (vector-only vs hybrid precision/recall).

### 5.4 No agent framework in MVP — *standing decision*

The "Crisis Assistant" is one structured RAG chain with a clarifying-question prompt. LangGraph's multi-node graphs are V1 once the single chain is measured. Nothing in the MVP needs graph orchestration, and every framework layer is another way for a demo to fail.

---

## 6. Infrastructure & DevOps

| Concern | Choice | Why |
| --- | --- | --- |
| Container runtime | Docker + Compose | Dev environment *is* the demo fallback (laptop runs the whole stack when the venue Wi-Fi dies) |
| Backend hosting | Cloud Run | Scale-to-zero cost, session affinity for WebSockets, deploys from the same image CI builds; min-instances 1 during demo week |
| Postgres | Neon (free tier) | Managed, branching for experiments, PostGIS + pgvector supported |
| Redis | Upstash (free tier) | Managed, generous limits for ephemeral state + arq |
| Scheduler | Cloud Scheduler | Drives the escalation tick (10 s) and nightly retention — the durable-timer design in `Architecture.md` §5 |
| Secrets | Secret Manager (+ `.env` locally, `.env.example` in git) | No key ever touches the repo; one doc lists every secret and its location |
| CI/CD | GitHub Actions | Free for the repo; PR gate = ruff + mypy + pytest + assembleDebug; `main`/tags deploy Cloud Run; Alembic runs pre-traffic |
| Monitoring | Sentry + JSON logs | `sos_id` correlation across backend stages; Cloud Run logs for the rest; Prometheus/Grafana explicitly deferred to V1 |
| API docs | FastAPI OpenAPI | `/docs` is the always-current reference; screenshots go straight into the report |

---

## 7. Quality & Testing

| Level | Tooling | Scope |
| --- | --- | --- |
| Unit (backend) | pytest + pytest-asyncio | Ranking (pure function — exhaustive), trust deltas, state-machine transitions, guardrail regexes |
| Integration (backend) | pytest + httpx against real Postgres in docker-compose | SOS lifecycle end-to-end, idempotency behavior, geo queries with seeded 1k users, pgvector retrieval |
| AI evaluation | golden set, `python -m ai.eval` | 50–100 scenarios; classification ≥ 85 %, retrieval precision@5 ≥ 80 %, faithfulness (every step cited); gate on prompt/corpus PRs |
| Android | JUnit + Turbine (Flow) + Compose UI tests | Hold-gesture, countdown window, token refresh, WS reconnect logic |
| Load / research | Locust + Digital Twin (`simulator/`) | 10/50/100 concurrent SOS, geo-query benchmark with/without index, naive-broadcast vs ranked dispatch, ranking-weight ablation |
| Error tracking | Sentry | Backend + Android, release-tagged |

**Rule:** every P0 backend fix ships with a test; the eval suite is a CI gate, not a local ritual.

---

## 8. Architecture Decision Records

Condensed; full context in `BLUEPRINT.md` §0 and `Architecture.md`.

| # | Decision | Rationale | Reversible? |
| --- | --- | --- | --- |
| ADR-1 | FastAPI over Django/Flask/Node | Async + WS + Pydantic + OpenAPI in one box; Python shared with AI/simulator | Painful to reverse — decided first |
| ADR-2 | Postgres + PostGIS over MongoDB | ACID state machine + best geo indexing; one engine | No (decided early, locked by migrations) |
| ADR-3 | pgvector over ChromaDB/Pinecone | One fewer service; corpus is tiny | Yes — re-embed script |
| ADR-4 | FCM data messages + app ACK over WebSockets/receipts | Only reliable background reach; honest delivery metric | No (platform physics) |
| ADR-5 | AI as in-backend module, not microservice | Solo-dev deployability; interface keeps extraction cheap | Yes, by design |
| ADR-6 | Durable escalation tick over in-memory timers | Cloud Run kills idle containers; timers must survive | Yes but never needed |
| ADR-7 | JWT email/password MVP; Firebase OAuth/OTP in V1 | One testable mechanism; OAuth adds no research value | Yes |
| ADR-8 | Single RAG chain; LangGraph in V1 | Simplicity; measured chain beats unmeasured graph | Yes |
| ADR-9 | LLM fallback ladder (retry → retrieval-only → offline cache) | Safety system must not depend on one vendor's uptime | Yes |
| ADR-10 | DRILL mode as a first-class flag | Multi-user rehearsals without alerting/112 risk; clean analytics | Permanent feature |
| ADR-11 | Straight-line ETA; no Directions API in MVP | Free, adequate, no key on critical path | Yes |
| ADR-12 | Digital Twin simulator at ~week 6, not month 4 | It's the research instrument, load harness, and chart factory in one | Scheduling, not architecture |
| ADR-13 | Minimal admin (server-rendered/CLI); React dashboard V1 | Verification queue ≠ SPA justification | Yes |
| ADR-14 | `LLMClient` abstraction over Gemini | A rate limit must never end a viva | Trivial |

---

## 9. Cost Summary

Student budget target: **₹0 recurring** (excluding the domain, which is optional).

| Service | Tier | Projected usage |
| --- | --- | --- |
| Cloud Run | Free (2M req/mo) | Thousands of demo/test requests |
| Neon Postgres | Free (0.5 GB) | Well under with 30-day message retention |
| Upstash Redis | Free (10k cmd/day) | Idempotency + rate limits at demo scale |
| Cloud Scheduler | Free (3 jobs) | Exactly 2 jobs used |
| Gemini API | Free tier | Classify + severity + guidance ≈ hundreds of calls/week incl. eval runs |
| FCM | Free | Unlimited for this scale |
| Maps SDK | Free (map loads) | Demo + dev only; no billed Directions usage in MVP |
| GitHub Actions | Free (public repo) | Full CI/CD |
| Sentry | Free developer tier | Both apps |
| **Total** | **₹0/mo** | Card-on-file alerts set for all quotas |

**Quota armor:** eval runs batched; LLM responses cached by normalized input (P2); `LLMClient` env-swap provider; demo rehearsed against cached/retrieval-only paths.

---

## 10. Version Pinning

Pin at project initialization; upgrade only with CI green and the eval suite passing.

| Component | Pin (at start) |
| --- | --- |
| Kotlin / AGP / Compose BOM | Latest stable at init (Compose BOM via version catalog) |
| Python | 3.12 |
| FastAPI / Pydantic | 0.115+ / 2.x |
| SQLAlchemy / Alembic / asyncpg | 2.0.x / 1.13+ / 0.29+ |
| PostgreSQL / PostGIS / pgvector | 16 / 3.4 / 0.7+ |
| Redis | 7.x |
| sentence-transformers / torch (CPU) | 3.x / 2.x-CPU |
| google-genai, firebase-admin, arq, PyJWT, bcrypt | Latest stable at init |
| Docker images | `postgres:16-postgis`, `redis:7`, `python:3.12-slim` |

`requirements.txt` pins exact versions; Android uses a version catalog (`libs.versions.toml`). One `UPDATE_DEPENDENCIES.md` note per upgrade — what changed, what broke, eval delta.
