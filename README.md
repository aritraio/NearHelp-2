# NearHelp AI

**AI-Powered Community Emergency Response Network** — final-year BCA project.

> *Connecting People. Coordinating Rescue. Powered by AI.*

NearHelp coordinates nearby trained volunteers during the critical minutes
before professional help arrives: one tap sends an SOS, the backend ranks and
notifies the nearest capable responders over push, and a RAG pipeline delivers
cited first-aid guidance grounded in WHO/Red Cross protocols.

## Documentation map

| Document | What it holds |
| --- | --- |
| [`proposal.md`](proposal.md) | Academic proposal — problem, literature, modules, timeline |
| [`BLUEPRINT.md`](BLUEPRINT.md) | Engineering blueprint — scope cuts, DB schema, API, security |
| [`Architecture.md`](Architecture.md) | System architecture — components, flows, failure modes |
| [`tech-stack.md`](tech-stack.md) | Layer-by-layer technology choices + ADRs + costs |
| [`DESIGN.md`](DESIGN.md) | App design language, tokens, screens, UI roadmap |
| [`improvements.md`](improvements.md) | Reviewer hardening suggestions (escalation tick, fallbacks…) |
| [`todos.md`](todos.md) | The master checklist — phase by phase |

## Quickstart (local development)

Prerequisites: **Docker** (with Compose v2). Everything else runs in containers.

```bash
cp .env.example .env          # defaults work out of the box for local dev
docker compose up --build     # db + redis + migrate + backend + worker
```

The `migrate` service applies all Alembic revisions before the API starts.
The `worker` runs the arq jobs (FCM fan-out) **and the escalation tick every
10 s** — waves advance even if the API container restarts. Once healthy:

- API + auto-generated docs: **http://localhost:8000/docs**
- Health: **http://localhost:8000/api/health** → `{"status": "ok", "db": "up", ...}`

### Try the SOS loop (docs → `POST /api/sos/create`)

1. Register two users (`/api/auth/register`), authorize both.
2. Each user: `PUT /api/users/me/location` (responder must be within 2 km of the victim).
3. Victim: `POST /api/sos/create` with an `Idempotency-Key` header → returns ranked responders.
4. Responder: `POST /api/sos/{id}/ack` then `/respond` → event flips to `active`.
5. Victim: `GET /api/sos/{id}` shows the accepted responder; `/timeline` shows the story.
6. Age an event 100 s (or wait) and the worker's tick expands the radius ×2/×3 and
   (non-drill events) prompts calling 108/112 — see `GET /api/sos/{id}/timeline`.

Push notifications need the Firebase service account JSON in
`secrets/firebase-service-account.json` (path via `FCM_SERVICE_ACCOUNT_FILE` in
`.env`); without it the LogPushSender logs what would have been sent.

Seed 1,000 test users across the Kolkata bbox and run the geo-query sanity check:

```bash
docker compose exec backend python -m scripts.seed_test_users
```

You should see the nearby-user count for a 3 km radius around Salt Lake plus
the five closest volunteers with distances — that's the Phase 0 acceptance
criterion for the PostGIS path (todos.md §0.2).

Reset everything: `docker compose down -v`.

### Backend without Docker

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head          # needs a local Postgres with PostGIS + pgvector
pytest                        # health tests don't need a database
```

Quality gates (same ones CI runs):

```bash
ruff check app scripts tests && ruff format --check app scripts tests
mypy
pytest -q
```

### Gemini smoke test (Phase 0 §0.3)

```bash
# put GEMINI_API_KEY in .env first (https://aistudio.google.com/apikey)
docker compose exec backend python -m scripts.test_gemini "man collapsed, not breathing"
```

Passes only when the model's JSON parses against the classification schema —
the contract that later becomes `POST /api/ai/classify`.

### Android app

Open `android/` in **Android Studio** (it will configure Gradle), or from a
terminal:

```bash
cd android
gradle wrapper               # once — generates gradlew (the wrapper JAR isn't committed)
./gradlew :app:assembleDebug
```

The emulator reaches the local backend via `http://10.0.2.2:8000/` by default.
For a physical device, build with `-PbaseUrl=http://<your-lan-ip>:8000/`.

## Repository layout

```
backend/            FastAPI app, models, Alembic migrations, scripts, tests
android/            Kotlin + Compose app (Hilt, Retrofit, design tokens)
docker/             Custom Postgres image (PostGIS + pgvector)
docker-compose.yml  Full local stack (db, redis, migrate, backend, worker)
*.md                Project documents (see table above)
```

## Phase status

Phases 0–2 complete (setup, auth/profile, core SOS engine) — see `todos.md`
for the per-item acceptance status and the remaining external-account steps
(Firebase, GCP, Gemini key) that require user sign-ups. Next: Phase 3
(Android MVP UI per `DESIGN.md`).
