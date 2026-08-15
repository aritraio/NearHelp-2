# NearHelp AI — Suggested Improvements

> Reviewer hat on: experienced developer, pragmatic about a 4-month solo final-year project. Nothing here adds new "features" for their own sake — every suggestion either fixes a real weakness, increases reliability of the demo, or strengthens the academic/defense story. Priorities: **P0** = do it, **P1** = strongly recommended, **P2** = nice to have.

---

## 1. Critical fixes (design flaws to correct before they bite)

### 1.1 Escalation timers cannot live in process memory — P0
The 30s/45s/60s escalation logic cannot be an in-memory `asyncio` timer in the backend. Cloud Run scales instances to zero and kills idle containers — your timers die with them, silently. In a safety-critical path this is the worst kind of bug: it works on your laptop, fails in production.

**Fix (simple and durable):** store `escalated_at` state on the `sos_events` row and drive escalation from a periodic tick:
- A small `/internal/escalation/tick` endpoint that scans for `pending` events past each threshold and re-notifies with expanded radius.
- Trigger it with Cloud Scheduler every 10–15 seconds (free), or even a `while True: sleep(10)` loop in a worker container for the college demo.
- Idempotent by construction (event state machine decides whether an action already happened), so overlapping ticks are harmless.

This also becomes a nice talking point in your defense: *why* fire-and-forget timers don't survive serverless cold starts.

### 1.2 The system must not depend on Gemini being available — P0
Right now, if the Gemini API is down, quota-exhausted, or returns malformed JSON, the guidance path produces nothing. For a system whose pitch is "AI assistance in the critical minutes," that's unacceptable — and it's also your single biggest demo-day risk.

**Fix — layered fallback (each layer simpler and more reliable than the last):**
1. Retry with structured-output schema once (handles transient errors / malformed JSON).
2. **Retrieval-only mode:** if the LLM fails, return the top retrieved protocol steps *verbatim* with their citations. RAG without the G is still genuinely useful — the WHO text is the ground truth anyway.
3. **Offline cache:** bundle the top ~10 emergency protocols (CPR, choking, bleeding, burns, snakebite, etc.) as static content *inside the app*. Guidance for common crises works with zero network. This is your demo insurance policy and a real feature emergency apps ship.

Log which layer served each request — "AI fallback rate" is an interesting metric for your report.

### 1.3 FCM "delivery receipts" are not a real thing (as designed) — P1
The proposal's "wait for FCM delivery receipt up to 30s" doesn't match how FCM works: notification messages to Android don't give you reliable per-device receipts. Pretending they do will burn a week.

**Fix — app-level ACK (honest and simple):** send high-priority *data* messages; when the app processes the SOS push, it calls `POST /api/sos/{id}/ack`. No ACK within N seconds → treat as undelivered for that responder (used by your escalation logic). Also handle FCM's `UNREGISTERED` response by deleting stale tokens — otherwise your "notified 12 responders" stat quietly becomes fiction as classmates reinstall the app.

### 1.4 Android will kill your app — plan for it — P0
In India this is worse than anywhere: Xiaomi/Oppo/Vivo/Samsung battery managers aggressively kill background apps, and FCM *data* messages often don't wake them. Your responder network only works if responder phones are reachable.

**Fix:**
- On first launch, detect the OEM and walk the user to the battery-optimization whitelist ("Autostart" settings on MIUI, etc.) — libraries like DontKillMyApp's guides tell you the right intent per manufacturer.
- Request `SCHEDULE_EXACT_ALARM`/foreground-service permissions only where needed; document why in the report.
- In the app settings, show a "responder readiness" indicator (battery optimized? notifications on? location permission set to Allow all the time?). This turns an invisible reliability problem into a visible, fixable one — and examiners love it.

---

## 2. High-impact engineering improvements

### 2.1 Move FCM fan-out off the request path — P0
`POST /api/sos/create` should return in well under 500ms. Do geo query + ranking inline (fast, indexed), then push the actual FCM sending and AI task to a background worker (FastAPI `BackgroundTasks` is enough at your scale; `arq` if you want a real queue). The victim's app gets an instant "help is being alerted" state instead of a spinner.

### 2.2 DRILL mode — P0 for your sanity
You will demo this with classmates as fake responders, repeatedly. Add a server-side `drill` flag on SOS events that:
- Renders an unmistakable "DRILL — NOT A REAL EMERGENCY" banner in every screen and notification.
- Never triggers the layer-2 "call 108/112" prompt.
- Tags analytics so drill events don't pollute your benchmarks.

Real emergency systems (PulsePoint included) have training modes; this is both a safety necessity and a legitimate feature to list.

### 2.3 SOS confirmation & undo — P1
Accidental SOS triggers are the #1 source of false alarms in panic-button apps (pocket presses). Two cheap mitigations:
- **Hold-to-trigger:** press and hold the SOS button for 3 seconds with a ring animation.
- **5-second cancel window** after triggering, before any responder is notified.

Fewer false events → your trust-score penalties actually stay meaningful, and responders don't get alert fatigue (the death of any real deployment).

### 2.4 Hybrid retrieval (keyword + vector) — P1
Pure vector search with MiniLM embeddings misses exact medical terminology ("epinephrine", "AVPU", protocol step numbers). Postgres already gives you full-text search — combine BM25-style keyword scoring with pgvector cosine similarity (even a simple weighted sum of the two rankings). At your corpus size this is an afternoon of work, and it gives you a genuine experiment for the report: *retrieval precision/recall: vector-only vs hybrid* (directly enriches RQ-level claims about guidance quality).

### 2.5 Cut Google Directions API out of the MVP ETA — P1
You don't need real routing for MVP ETA. Straight-line distance ÷ realistic urban speed (say 15 km/h walking/jogging, 30 km/h vehicle) recalculated as the responder moves is 20 lines of code, free, and perfectly adequate for "Amit, ~2 min away". Swap in OSRM (self-hostable, free) or Google Directions only if you keep the project alive afterwards. One less API key, one less quota failure mode during the viva.

### 2.6 Source map data from OpenStreetMap once — P1
Hospitals, police stations, fire stations for the demo area: pull them from the Overpass API a single time, commit the result as a JSON fixture, ship it with the app/backend. No Google Places key needed, works offline, deterministic for demos.

### 2.7 Adaptive location streaming — P2
Every 3 seconds of GPS streaming is a battery killer and mostly noise. Stream every 2–3s only when the responder is within 500m of the victim; relax to 10–15s when further out. Add a one-line note in the report about the battery/latency tradeoff — it shows engineering maturity.

### 2.8 Nightly retention job — P2
A tiny cron that nulls `users.location` for non-participants, anonymizes resolved event locations, and prunes messages past 30 days. Ten lines of SQL, and it turns your "privacy by design" claims into something you can *show* in the defense.

---

## 3. Strengthen the AI (quality + safety)

### 3.1 Build the evaluation harness before you tune anything — P0
You cannot improve what you don't measure, and "the guidance looks good" is not a defense answer.
- Curate a **golden set**: 50–100 scenarios (text → expected crisis type, expected relevant procedures, expected severity band). Write it once; reuse forever.
- Run it on every prompt/corpus change; track classification accuracy, retrieval precision@5, and a faithfulness check (does every generated step cite a retrieved chunk?).
- Keep the harness as a script (`python -m ai.eval`) and paste its output table straight into the report. Examiners rarely see measured AI quality in student projects — this alone differentiates you.

### 3.2 Version your prompts like code — P1
Store prompts as versioned template files, log `(prompt_version, output, retrieved_refs)` with every AI call. When guidance quality regresses, you'll know exactly which prompt version did it. Cheap discipline that real LLM teams consider mandatory.

### 3.3 Guardrail tests in CI — P1
Turn your safety rules into unit tests that run on every push:
- Feed the RAG chain adversarial inputs ("what dosage of X should I give", "how do I stitch a wound", off-topic requests) and assert the refusal/fallback path fires.
- Regex blocklist assertions (mg/ml/dosage/prescription terms) on generated output.
Safety claims backed by automated tests are far stronger than safety claims backed by a paragraph in the report.

### 3.4 Cache classification results — P2
Identical or near-identical emergency descriptions ("person not breathing", typed by multiple bystanders of the same event) should hit a cache keyed on normalized text, not fresh Gemini calls. Saves quota for the demo and improves P95 latency numbers.

---

## 4. Strengthen the academics (this is what your grade is made of)

### 4.1 Build the Digital Twin simulator at week ~6, not month 4 — P0
This is the single biggest scheduling change I'd make. The simulator is simultaneously (a) your research instrument, (b) your load-test harness during development, and (c) your defense evidence generator. Built early, you'll use it constantly; built last, it's a rushed slide factory. A scrappy v1 (seed users, scripted SOS, naive-broadcast vs ranked dispatch) takes days, and every later feature gets benchmarked for free.

### 4.2 Add a ranking-weights ablation study — P1
You already have the ranking formula (w1·distance + w2·skill + w3·trust = 0.4/0.35/0.25). Run the simulator across a grid of weight combinations and show how time-to-first-*useful*-responder changes. One table + one chart, nearly free given the simulator, and it converts "we picked weights" into "we validated weights" — exactly the kind of claim evaluators probe in a viva.

### 4.3 Report P95, not just averages — P1
Averages hide exactly the tail behavior that matters in emergencies. For every latency you report (SOS end-to-end, geo query, AI pipeline, notification delivery), give P50/P95/P99 from the simulator and real demo traffic.

### 4.4 Instrument the real pipeline for per-stage timings — P1
A tiny middleware that logs per-event stage durations (`geo_ms`, `rank_ms`, `fcm_ms`, `ai_ms`) into `ai_outputs`/timeline gives you *real* latency breakdown charts alongside the synthetic ones — and lets you truthfully say "measured on the deployed system."

### 4.5 Write short ADRs as you go — P2
Five-line Architecture Decision Records for every meaningful choice (pgvector over ChromaDB, FCM over WebSocket alerts, in-backend AI module). They take minutes, prevent you re-litigating decisions at 2am, and paste beautifully into your SDD chapter.

---

## 5. Demo-day armor (learned the hard way)

- **Fake-GPS demo mode (P0):** a hidden dev setting that teleports/moves the responder device along a scripted route. Without it, your "live tracking" demo depends on someone actually jogging down a corridor, and your map shows two dots standing still.
- **Recorded backup demo (P0):** screen-record the full two-device flow the week before. If Wi-Fi, Firebase, or the college network fails, you still present.
- **Provider abstraction behind one interface (P1):** wrap Gemini behind an `LLMClient` interface so a quota burn during rehearsals doesn't deadlock you — swap to any OpenAI-compatible endpoint via env var. Not for lock-in ideology; purely so the viva cannot be ruined by a rate limit.
- **Local docker-compose demo fallback (P2):** the whole stack runs on your laptop; the Cloud Run URL is the primary, laptop is the spare.

---

## 6. What NOT to do (resist the urge)

Every week someone will suggest one of these. The correct answer is "future scope," and your report already says so:

- ❌ Microservices/Kubernetes — one container is a feature at this scale, not a compromise.
- ❌ WebRTC voice/video, iOS, wearables — zero defense value, enormous cost.
- ❌ Fine-tuning any model — RAG was the right call; don't relitigate it.
- ❌ A polished React admin dashboard before the core loop is bulletproof — the verification queue works fine as a server-rendered page.
- ❌ Real 112/108 integration — legally and institutionally out of reach for a student project; simulate it.
- ❌ Adding "just one more" crisis-type input modality — text first, voice only if Month 2 goes perfectly.

The graveyard of final-year projects is full of half-finished platforms. A complete, measured, reliable two-device demo with benchmark charts beats a sprawling half-working system every single time.

---

## Suggested priority order (if you do nothing else from this file)

| Order | Item | Section |
| --- | --- | --- |
| 1 | Escalation via durable tick, not in-memory timers | 1.1 |
| 2 | AI fallback layers + offline protocol cache | 1.2 |
| 3 | Digital Twin simulator pulled forward to ~week 6 | 4.1 |
| 4 | Golden-set eval harness for the AI | 3.1 |
| 5 | DRILL mode | 2.2 |
| 6 | Android background-kill handling + readiness indicator | 1.4 |
| 7 | Hold-to-trigger + cancel window | 2.3 |
| 8 | Fake-GPS demo mode + recorded backup | 5 |
| 9 | App-level FCM ACKs + token cleanup | 1.3 |
| 10 | Hybrid retrieval experiment | 2.4 |
