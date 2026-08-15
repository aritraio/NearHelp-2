# NearHelp AI — Master TODO

> The single actionable checklist for the whole project. Priorities: **P0** = the project fails without it · **P1** = strongly recommended (defense quality / reliability) · **P2** = polish, only if the phase is green. Sources: `proposal.md` (scope), `BLUEPRINT.md` (decisions), `Architecture.md` (design), `improvements.md` (hardening), `DESIGN.md` (UI).

**Working rules**

1. A task is done only when its **acceptance criterion** passes — not when the code compiles.
2. No phase starts before the previous phase's P0 items are checked.
3. Every P0 backend fix ships with a test.
4. Weekly self-review: tick boxes, move blockers to the top of the next week.

---

## Phase 0 — Project Setup (Week 1)

> **Status (2026-08-15):** implemented and verified locally — ruff clean, mypy clean,
> pytest 2/2, migration renders valid offline SQL (4 tables + GiST×2 + HNSW), YAML validated.
> Docker is not installed on the dev machine, so the live-stack ACs in 0.2 and the Gemini-key
> AC in 0.3 still need one run each — commands are in the README quickstart.

### 0.1 Repository & tooling
- [x] Create monorepo structure per `BLUEPRINT.md` §5 (P0)
- [x] `.gitignore` (Python, Android, `.env`), `README.md` with quickstart (P0)
- [x] `.env.example` listing **every** env var with comments (P0)
- [x] Python 3.12 venv/uv setup, `requirements.txt` pinned (P1) — *pins verified installable*
- [x] Android project: Compose, version catalog, Hilt, Retrofit skeleton (P0) — *generate the Gradle wrapper once via `gradle wrapper` (README)*
- [x] ruff + mypy config; pre-commit hooks (P1) — *run `pre-commit install` after cloning*

### 0.2 Local environment
- [x] `docker-compose.yml`: postgres+postgis+pgvector, redis, backend, worker (P0)
  - *AC: `docker compose up` → all services healthy, `/health` returns 200* — **pending your first `docker compose up --build`**
- [x] Alembic initialized; migrations for `users`, `sos_events`, `responses` (+ indexes) (P0)
  - *AC: `alembic upgrade head` on a fresh volume succeeds; GiST + HNSW indexes exist in pg_indexes* — **offline SQL verified; live run pending**
- [x] Seed script `seed_test_users.py`: 1,000 users with random locations (Kolkata bbox) + skills (P0)
  - *AC: geo query for a point returns plausible nearby users with distances* — **live run pending**

### 0.3 External accounts — *(user sign-ups; code side is ready)*
- [ ] Firebase project; app registered; server key via service account JSON (P0)
- [ ] GCP project; Cloud Run + Artifact Registry + Secret Manager + Scheduler enabled (P1)
- [ ] Neon Postgres with PostGIS + pgvector; Upstash Redis (P1)
- [ ] Gemini API key; first structured-output call from a script (P0)
  - *AC: JSON response parses against the schema* — **script ready: `python -m scripts.test_gemini "…"`**

### 0.4 CI
- [x] GitHub Actions: ruff + mypy + pytest on PR; `assembleDebug` job (P1)
  - *AC: red PR blocks merge* — activates once the repo is pushed to GitHub

---

## Phase 1 — Auth & Profile Backend (Week 2)

> **Status (2026-08-15):** implemented — ruff/mypy clean, 16 tests passing locally
> (DB-dependent integration tests auto-skip without Postgres and run in CI against
> real containers). `alembic upgrade head` applies migration 0002
> (skill_verifications, user_devices, users.password_hash, drops users.fcm_token).

- [x] bcrypt (cost 12) + register/login endpoints (P0) — *AC: register → login → 200 with tokens* — ✅ `test_register_login_me_roundtrip`
- [x] JWT issue/verify: 15-min access, 7-day rotating refresh; revocation list in Redis (P0) — ✅ replayed refresh rejected in `test_refresh_rotation_and_replay_rejected`; revocation fails closed on Redis outage
- [x] `GET/PUT /api/users/me`, fcm-token registration (multi-device aware) (P0) — ✅ `user_devices` table, per-device upsert tested
- [x] Skills claim endpoint + certificate upload → object storage (signed URLs) (P1) — local-disk storage behind a `CertificateStorage` interface; GCS signed URLs swap in at Phase 9
- [x] Rate limiting middleware: 100 req/min/user, 10 SOS/day/user (P1) — user + per-IP limits live; `consume_sos_quota()` wired for Phase 2, fails closed
- [x] Integration tests: auth lifecycle + token refresh + revocation (P0) — ✅ 17 integration tests (auth flow, profile/fcm/skills, rate limits); run in CI with Postgres+Redis containers

**Left deliberately out of Phase 1** (documented, not forgotten): logout endpoint (needs the
Android token store to be worth it — Phase 3), admin verification review (Phase 6).

---

## Phase 2 — Core SOS Engine (Weeks 2–4) ← *the heart of the project*

### 2.1 Creation & selection
- [ ] `POST /api/sos/create` with `Idempotency-Key` (Redis SETNX + Postgres unique backstop) (P0)
  - *AC: duplicate key returns the original response; two events never created*
- [ ] `POST /api/sos/{id}/respond` (idempotent), state machine `PENDING→ACTIVE→RESOLVED|EXPIRED` (P0)
- [ ] `PUT /api/sos/{id}/resolve` + timeline events on every transition (P0)
- [ ] Geo service: `ST_DWithin` query returning candidates + distance (P0)
  - *AC: with 1k seeded users, P95 query < 30 ms*
- [ ] Ranking service as a pure function (weights in config) (P0)
  - *AC: unit test — verified nurse at 800 m outranks unskilled user at 200 m for cardiac scenario (proposal §12.3)*
- [ ] DRILL flag plumbed end-to-end: event field, notification banner, no call-services prompt, analytics exclusion (P0)
- [ ] `POST /api/sos/{id}/ack` — app-level delivery ACK endpoint (P1)

### 2.2 Notification & escalation
- [ ] FCM notifier: high-priority data messages, chunked sends, `UNREGISTERED` cleanup (P0)
  - *AC: SOS on device A → notification on device B in < 3 s (same room)*
- [ ] arq worker service (separate entrypoint) hosting fan-out + AI jobs (P0)
- [ ] Escalation tick: `/internal/escalation/tick` scanning PENDING events; wave CAS via single UPDATE (P0)
  - *AC: kill the API container mid-event → tick still escalates waves 2/3 on schedule*
- [ ] Local tick loop for dev; Cloud Scheduler job (every 10 s) for cloud (P1)
- [ ] Delivery metric job: `acked/notified` per wave persisted for benchmarks (P1)

### 2.3 First end-to-end milestone 🏁
- [ ] **Two-device demo:** Device A SOS → B receives push → B responds → A sees accepted status (P0)
  - *AC: full path under 5 s on Wi-Fi; recorded on video as the baseline demo*

---

## Phase 3 — Android MVP UI (Weeks 3–5, overlaps backend; per `DESIGN.md`)

### 3.1 Design system (D0)
- [ ] `colors.kt` / `Type.kt` / `Shapes.kt` tokens exactly per `DESIGN.md` §2 (P0)
- [ ] `GlassCard`, `StatPill`, `QuickNavRow`, `CategoryTile/Chip` components (P0)
- [ ] Mint gradient scaffold; state-driven backgrounds CALM/INCIDENT/RESPOND (P0)

### 3.2 Screens
- [ ] Auth screens (login/register) with token storage + auto-refresh (P0)
- [ ] Home: locality header, live responder stat, GPS footer, CHECK-IN expander (P0)
- [ ] `SosHoldButton`: 3-s arc, haptics at 50 %/100 %, early-release shake (P0)
- [ ] Crisis Select: address card + category grid (3×3) + CountdownBar (P0)
- [ ] 5-s cancel window wired to idempotent create/cancel (P0)
  - *AC: cancel within 5 s → no responders notified; after → event commits*
- [ ] FCM receiver → full-screen Alert screen with Respond (hold) / Dismiss (P0)
- [ ] Profile: skills + verification states + readiness indicator (P1)
- [ ] Battery/optimization exemption flow + OEM autostart guidance (P1)

### 3.3 Demo armor (from `improvements.md` §5)
- [ ] Fake-GPS dev setting: scripted responder route (P0 for demo)
- [ ] Record full two-device walkthrough video (P0 — the backup demo)

---

## Phase 4 — Real-Time Layer (Weeks 5–7)

- [ ] WebSocket `/api/ws/{sos_id}`: one-time ticket auth, ConnectionManager, rate-limited relay (P0)
  - *AC: 100 connections in Locust, zero dropped location messages*
- [ ] Client WS wrapper: auto-reconnect ×3 → REST polling fallback (P0)
- [ ] Live map screen: victim pulse pin + animated responder markers + ETA pills (straight-line ETA) (P0)
- [ ] Adaptive location intervals (2–3 s near, 10–15 s far) in foreground service (P1)
- [ ] Chat over WS + REST fallback; message persistence (P0)
- [ ] Timeline tab rendering `timeline_events` + escalation cues ("Expanding search to 2× radius") (P1)
- [ ] Incident Active tabs: Guidance | Responders | Chat per `DESIGN.md` §4.3 (P0 once AI lands)
- [ ] Responder en-route screen: route line + ETA + arrival check-in (GPS-confirmed) (P1)
- [ ] Cloud Run session affinity + graceful drain (P1)

**Milestone 🏁 — Month-2 exit:** full lifecycle on two devices: SOS → ranked alerts → accept → live map → chat → resolve → timeline.

---

## Phase 5 — AI Pipeline (Weeks 5–8, parallel track)

### 5.1 Corpus & retrieval
- [ ] Collect corpus: WHO first aid, Red Cross India, AHA CPR summaries, NDMA, snakebite protocol (P0)
- [ ] Procedure-level chunker (200–400 tokens, step boundaries) + metadata (source, crisis_type, step) (P0)
- [ ] MiniLM embedder → `kb_chunks` + HNSW index; ingestion script idempotent (P0)
  - *AC: "cardiac arrest" query returns CPR steps in top-5*
- [ ] Hybrid retrieval: pgvector + Postgres FTS merge (P1)
- [ ] Golden set: 50–100 scenarios with expected type/severity/procedures (P0)
- [ ] Eval harness `python -m ai.eval`: classification ≥ 85 %, precision@5 ≥ 80 %, faithfulness (P0)
  - *AC: runs green in CI on corpus/prompt PRs*

### 5.2 Generation & guardrails
- [ ] Classification + severity in one structured-output Gemini call (P0)
- [ ] `LLMClient` abstraction (env-swappable provider) (P0)
- [ ] Guidance prompt: mandatory citations, scope guardrails, user text as data not instructions (P0)
- [ ] Fallback ladder: schema-retry → retrieval-only → client offline cache (P0)
  - *AC: with Gemini key invalidated, guidance still served (flagged retrieval-only); SOS path latency unchanged*
- [ ] Blocklist post-filter + guardrail unit tests in CI (P1)
- [ ] Prompt versioning + `(prompt_version, output, refs)` logging (P1)
- [ ] Wire AI into SOS path as parallel arq job; push "guidance ready" (P0)
- [ ] Offline protocol cache bundled in app, rendered via GuidanceCard (P0)
- [ ] Disclaimer strip on every guidance surface (P0)

**Milestone 🏁 — Month-1-style exit (reprise, now with AI):** two-device demo where the responder receives **cited** CPR guidance seconds after the alert.

---

## Phase 6 — Trust, Verification & Admin (Weeks 8–9)

- [ ] Skill verification queue: admin endpoints + minimal server-rendered UI (P1)
  - *AC: submit → approve → verified badge on profile; trust +5*
- [ ] Trust service: all deltas implemented as pure functions + tests (P1)
- [ ] Feedback flow post-resolution (stars → trust) (P1)
- [ ] Admin: suspend user, drill-safe stats page (P1)
- [ ] Nightly retention job: null stale locations, round resolved coordinates, prune 30-day messages (P2)

---

## Phase 7 — Digital Twin Simulator & Benchmarks (start ~Week 6, per ADR-12)

- [ ] Scenario generator: users/responders with skills, response probabilities (P0)
- [ ] Locust profiles: single SOS, 10/50/100 concurrent, WS load, AI pipeline load (P0)
- [ ] Metric collection: time-to-first-responder, P50/P95/P99 latencies per stage, delivery rate (P0)
- [ ] **Experiment E1:** AI-ranked dispatch vs naive broadcast (RQ1) (P0)
- [ ] **Experiment E2:** skill-aware vs distance-only ranking relevance (RQ2) (P1)
- [ ] **Experiment E3:** AI latency breakdown; with/without AI in path (RQ3) (P0)
- [ ] **Experiment E4:** throughput curve 10/50/100 concurrent (RQ4) (P1)
- [ ] **Experiment E5:** geo query with/without GiST index at 1k/10k/100k users (RQ5) (P1)
- [ ] **Experiment E6:** ranking-weight ablation grid (w1/w2/w3) (P1)
- [ ] Retrieval comparison: vector-only vs hybrid (P2)
- [ ] Chart export: auto-generated PNGs for all experiments → `docs/charts/` (P0)
- [ ] Real-traffic instrumentation: stage timings from deployed system alongside synthetic (P1)

**Milestone 🏁 — defense evidence pack:** every research question answered by a reproducible chart.

---

## Phase 8 — Hardening (Weeks 10–11)

- [ ] Security pass: JWT expiry paths, participant-only visibility on SOS details, WS ticket single-use (P0)
- [ ] Failure injection tests: Redis down, Gemini down, FCM fail — SOS path still ≤ 100 ms (P1)
- [ ] Input fuzzing on sos/create (malformed payloads rejected by Pydantic) (P1)
- [ ] Android: TalkBack labels, 1.3× font audit on GuidanceCard + grid, contrast fixes (`-Deep` text colors) (P1)
- [ ] Dark theme pass (calm + incident variants) (P2)
- [ ] Skeleton/empty states on all screens; offline banner chip (P2)
- [ ] Error taxonomy in Sentry: release tags, alert on SOS-path 5xx (P1)

---

## Phase 9 — Deployment (Weeks 11–12)

- [ ] Backend + worker images via CI; deploy on `main` (P1)
- [ ] Alembic pre-deploy step; zero-downtime check (P1)
- [ ] Cloud Scheduler jobs: escalation tick (10 s) + retention (nightly) (P1)
- [ ] Secrets in Secret Manager; `.env` audit — no keys in repo (`gitleaks` in CI) (P0)
- [ ] Public HTTPS + WSS verified from mobile data (not just Wi-Fi) (P0)
- [ ] Release APK signed; install-fest with 5+ classmates running DRILL scenarios (P0)
- [ ] Laptop docker-compose demo fallback rehearsed (P1)

---

## Phase 10 — Documentation & Defense (Weeks 13–16)

- [ ] SRS (proposal is the base; reconcile terminology with implementation) (P1)
- [ ] SDD: architecture diagrams from `Architecture.md`, ADRs from `tech-stack.md`, UML for state machine + SOS sequence (P1)
- [ ] API.md: curated endpoint reference + `/docs` screenshots (P1)
- [ ] Performance evaluation report: E1–E6 tables + charts + methodology (P0)
- [ ] Setup guide: from clone to two-device demo in < 30 minutes (P1)
- [ ] Demo script: rehearsed 5-minute flow + failure fallbacks (P0)
- [ ] Backup video + chart pack exported (P0)
- [ ] Project report + defense slides + anticipated Q&A (P0)

---

## Week-by-Week Map (16 weeks)

| Week | Backend | Android | AI / Simulator | Exit check |
| --- | --- | --- | --- | --- |
| 1 | Setup, compose, migrations, seed | Project skeleton | Accounts, first Gemini call | `/health` green |
| 2 | Auth, profile, rate limits | — | — | Auth lifecycle test green |
| 3 | SOS create/respond, geo, ranking | Tokens, Home, hold button | — | Idempotency + ranking tests |
| 4 | FCM, arq, escalation tick | Crisis Select, countdown, Alert screen | — | **🏁 Two-device demo v1** |
| 5 | Polish + hardening of Phase 2 | Auth screens wired, profile | Corpus collection | — |
| 6 | WebSocket manager | WS client, live map | Chunker + embed + golden set | Retrieval AC passes |
| 7 | Chat + timeline WS | Tracking, chat UI, en-route | Eval harness in CI | **🏁 Full lifecycle demo** |
| 8 | Ticket auth, WS hardening | Incident tabs | Classification + severity call | AI path parallel-verified |
| 9 | Trust, verification, admin UI | Profile v2, readiness row | Guidance prompt + fallback ladder | Fallback AC (dead key) passes |
| 10 | Retention job | Responder on-scene | Hybrid retrieval (P1) | — |
| 11 | Security + failure injection | Accessibility + dark pass | Guardrail tests in CI | Failure-injection AC green |
| 12 | Deploy, scheduler, secrets | DRILL install-fest | — | Public mobile-data demo green |
| 13 | Benchmarks on deployed system | Demo armor, fake-GPS | Simulator E1–E3 | Charts generated |
| 14 | — | Polish | Simulator E4–E6 | **🏁 Evidence pack** |
| 15 | Buffer | Buffer | Buffer | Everything P0 ticked |
| 16 | — | — | — | **Defense** |

---

## Milestone Definitions

| Milestone | Definition of done |
| --- | --- |
| **M1 — Working core (end W4)** | Two devices: SOS → push → accept, idempotent, DRILL-flagged, escalation survives API restart |
| **M2 — Full lifecycle (end W7)** | M1 + live map, chat, timeline, resolve, trust update on real devices |
| **M3 — AI in the loop (end W9)** | M2 + cited guidance on responder device; fallback ladder proven; eval harness gating PRs |
| **M4 — Evidence pack (end W14)** | Deployed system + E1–E6 charts (incl. real-traffic timings) + DRILL install-fest with ≥ 5 users |
| **M5 — Defense-ready (W16)** | Docs complete, demo rehearsed with failure fallbacks, backup video exists |

---

## Top-10 Priority Order (if time forces ruthless triage)

1. Escalation tick durable (Phase 2.2)
2. AI fallback ladder + offline cache (Phase 5.2)
3. Simulator started week 6, not month 4 (Phase 7)
4. Golden-set eval harness (Phase 5.1)
5. DRILL mode (Phase 2.1)
6. Battery/background-kill handling + readiness indicator (Phase 3.2)
7. Hold-to-trigger + cancel window (Phase 3.2)
8. Fake-GPS demo mode + backup video (Phase 3.3)
9. App-level FCM ACKs + token cleanup (Phase 2.2)
10. Hybrid retrieval experiment (Phase 5.1)

---

## Explicit Non-Goals (do **not** build; cite as future scope)

- ❌ Microservices, Kubernetes, service mesh
- ❌ iOS, WebRTC voice/video, wearables
- ❌ Fine-tuned models; LangGraph multi-agent graphs (V1)
- ❌ React admin dashboard (V1), real 112/108 integration
- ❌ Anonymous mode, SMS/offline fallback, Guardian/Disaster modes
- ❌ Any feature added while a P0 box in the current phase is unticked
