# NearHelp AI — Project Proposal

**AI-Powered Community Emergency Response Network**

> *Connecting People. Coordinating Rescue. Powered by AI.*

---

| Field                | Details                                                    |
| -------------------- | ---------------------------------------------------------- |
| **Project Title**    | NearHelp AI — AI-Powered Community Emergency Response Network |
| **Project Category** | Final Year BCA Project                                  |
| **Domain**           | AI/ML, Mobile Computing, Real-Time Systems, Geospatial Computing |
| **Duration**         | 4 Months                                                   |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Problem Statement](#2-problem-statement)
3. [Motivation](#3-motivation)
4. [Literature Survey](#4-literature-survey)
5. [Project Objectives](#5-project-objectives)
6. [Core Research Question](#6-core-research-question)
7. [System Architecture](#7-system-architecture)
8. [Detailed Module Design](#8-detailed-module-design)
9. [AI/ML Pipeline Design](#9-aiml-pipeline-design)
10. [Data Model & Database Design](#10-data-model--database-design)
11. [API Design](#11-api-design)
12. [Responder Ranking Algorithm](#12-responder-ranking-algorithm)
13. [Safety-Critical Engineering](#13-safety-critical-engineering)
14. [Security & Privacy Design](#14-security--privacy-design)
15. [Technology Stack](#15-technology-stack)
16. [Development Methodology](#16-development-methodology)
17. [Project Timeline & Milestones](#17-project-timeline--milestones)
18. [Testing Strategy](#18-testing-strategy)
19. [Research Contributions](#19-research-contributions)
20. [Deliverables](#20-deliverables)
21. [Risk Analysis & Mitigation](#21-risk-analysis--mitigation)
22. [Future Scope](#22-future-scope)
23. [References](#23-references)

---

## 1. Introduction

Emergency situations — cardiac arrests, fires, gas leaks, accidents — share one critical property: **the first few minutes determine outcomes**. Medical literature consistently shows that bystander intervention within the first 3–5 minutes of a cardiac arrest can double or triple survival rates. Yet existing emergency infrastructure (112/108 in India) is designed around dispatching *professional* responders from *centralized* locations, introducing an unavoidable delay that no amount of fleet optimization can fully eliminate.

**NearHelp AI** proposes an alternative, complementary layer: an AI-assisted, real-time community emergency response network that identifies, ranks, and coordinates *nearby capable individuals* (trained volunteers, off-duty medical professionals, skilled community members) to provide structured assistance during the critical gap before professional help arrives.

This is not a replacement for emergency services. It is the layer that acts *before* they arrive — and it uses AI not as a novelty, but as the mechanism that makes unstructured community response *safe, structured, and measurable*.

The project answers a single, concrete question:

> **Can AI reduce effective emergency response time by intelligently coordinating community responders before professional help arrives?**

---

## 2. Problem Statement

During the first critical minutes of an emergency, professional responders (ambulances, fire services, police) are often several minutes to tens of minutes away. Meanwhile, the nearest person capable of providing meaningful help — a neighbor with CPR training, an off-duty nurse, a volunteer firefighter — is frequently within walking distance but has no structured way to:

1. **Know** that an emergency is happening nearby.
2. **Know** whether their specific skills are relevant.
3. **Receive** verified, step-by-step guidance for the specific situation.
4. **Coordinate** with other responders without chaos.
5. **Communicate** across language barriers with the victim.

Existing solutions fall short:

| Solution | Limitation |
| --- | --- |
| Traditional 112/108 calls | Professional-only dispatch; no community layer |
| Social media posts | Unstructured, no verification, no coordination |
| Neighborhood WhatsApp groups | No skill matching, no AI guidance, no accountability |
| Generic SOS apps | Broadcast-only (notify everyone equally), no intelligence |

NearHelp AI addresses this gap by creating an intelligent emergency response network that uses AI for emergency detection, responder ranking, guided first-aid assistance, and real-time coordination — while maintaining trust through skill verification and reputation systems.

---

## 3. Motivation

The motivation for this project stems from several converging factors:

### 3.1 The Bystander Response Gap
Studies show that in urban India, average ambulance response time ranges from 15–30 minutes in many cities. In contrast, a community responder within a 1 km radius could arrive in under 3 minutes. The gap between "someone nearby can help" and "someone nearby actually helps effectively" is a coordination and information problem — exactly what software can solve.

### 3.2 Untapped Community Capability
India has millions of individuals with relevant emergency skills — doctors, nurses, paramedics, NCC/NSS-trained students, Red Cross volunteers, trained first-aiders — who are never mobilized during nearby emergencies because no system connects them.

### 3.3 AI as a Safety Layer, Not a Novelty
Large Language Models (LLMs) grounded in verified medical protocols via Retrieval-Augmented Generation (RAG) can provide step-by-step first-aid guidance that is *more reliable* than an untrained bystander's improvisation, while being *more accessible* than calling a doctor who may not answer. The key insight is that AI is not replacing medical judgment — it is surfacing *already-published, expert-verified protocols* at the moment they are needed.

### 3.4 Academic Significance
This project sits at the intersection of multiple computer science domains — mobile computing, real-time systems, geospatial databases, natural language processing, information retrieval, and distributed systems — making it suitable for a final-year project that demonstrates breadth and depth.

---

## 4. Literature Survey

### 4.1 Emergency Response Systems
| System/Study | Key Finding | Gap Addressed by NearHelp |
| --- | --- | --- |
| PulsePoint (USA) | CPR-trained bystanders alerted to nearby cardiac arrests; improved survival rates | Limited to CPR; no AI guidance; not available in India |
| GoodSAM (UK) | Connects first-aiders with emergencies via app | No AI-driven severity assessment or skill matching |
| mRespond (Research, 2020) | Mobile-based emergency response with geolocation | No AI component; simple broadcast model |
| Ziqitza Healthcare (India) | 108 ambulance dispatch optimization | Professional-only; no community responder layer |

### 4.2 AI in Emergency Medicine
| Study/System | Contribution | Relevance |
| --- | --- | --- |
| Lewis et al. (2023) — "LLMs for Emergency Triage" | LLMs can perform emergency severity triage comparable to trained nurses | Validates AI severity prediction (Module 5) |
| RAG for Medical QA (Xiong et al., 2024) | Retrieval-augmented generation reduces hallucination in medical advice | Foundation for our RAG knowledge base (Module 11) |
| WHO First Aid Guidelines (2023) | Standardized, publicly available first-aid protocols | Primary knowledge source for our retrieval corpus |

### 4.3 Geospatial Query Optimization
| Technology | Use Case | Relevance |
| --- | --- | --- |
| PostGIS `ST_DWithin` | Radius-based spatial queries on PostgreSQL | Primary geospatial query engine |
| MongoDB 2dsphere Index | Native geospatial indexing with `$nearSphere` | Alternative geospatial backend |
| R-tree Indexing | Efficient spatial lookups | Underlying index structure used by PostGIS |

### 4.4 Real-Time Communication
| Technology | Characteristic | Use in NearHelp |
| --- | --- | --- |
| Firebase Cloud Messaging (FCM) | Reliable push delivery to backgrounded Android apps | Primary alert delivery mechanism |
| WebSockets / Socket.io | Persistent bidirectional connection | Live location tracking, chat, coordination |
| WebRTC | Peer-to-peer media streams | Future: voice/video between victim and responder |

---

## 5. Project Objectives

| # | Objective | Measurable Outcome |
| --- | --- | --- |
| O1 | Reduce emergency response time through intelligent community mobilization | Measure average time-to-first-responder in simulation vs. naive broadcast |
| O2 | Build a trusted community responder network with verified skills | Implement skill verification workflow; measure verification completion rate |
| O3 | Provide AI-grounded first-aid guidance using RAG | Measure retrieval precision/recall against standard first-aid protocols |
| O4 | Enable real-time coordination between victim and responders | Demonstrate live location tracking, chat, and timeline generation |
| O5 | Support multimodal emergency intake (text, voice, photo) | Implement and test all three input modalities |
| O6 | Ensure privacy-preserving design with anonymous emergency mode | Demonstrate that anonymous SOS reveals no PII to responders |
| O7 | Provide actionable analytics for authorities | Build admin dashboard with heatmaps, response time analytics, and trends |
| O8 | Scientifically evaluate system performance | Load test with Digital Twin simulator; publish benchmark results |

---

## 6. Core Research Question

> **Can AI reduce effective emergency response time by intelligently coordinating community responders before professional help arrives?**

This decomposes into the following sub-questions, each answerable through experiments:

1. **RQ1**: How much faster is AI-based responder selection (skill-aware, severity-weighted) compared to fixed-radius broadcasting?
2. **RQ2**: Does RAG-grounded guidance improve the quality of bystander first-aid compared to no guidance?
3. **RQ3**: What is the latency overhead of AI processing in the critical SOS path, and is it acceptable?
4. **RQ4**: How does the system perform under concurrent load (multiple simultaneous SOS events)?
5. **RQ5**: Which geospatial indexing strategy (PostGIS vs. MongoDB 2dsphere) performs best for nearby-user queries at scale?

---

## 7. System Architecture

### 7.1 High-Level Architecture

The system follows a **three-tier architecture** with clear subsystem ownership:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER (Android)                          │
│                                                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │   Auth   │  │ SOS UI   │  │ Live Map │  │   Chat   │  │ Profile │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│                         │           │            │                      │
│                    HTTPS │     WebSocket    WebSocket                   │
└─────────────────────────┼───────────┼────────────┼─────────────────────┘
                          │           │            │
┌─────────────────────────┼───────────┼────────────┼─────────────────────┐
│                    BACKEND LAYER (FastAPI)                              │
│                                                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Auth API │  │ SOS API  │  │ WebSocket│  │ Admin API│              │
│  │          │  │          │  │  Server  │  │          │              │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘              │
│       │             │              │              │                    │
│  ┌────┴─────────────┴──────────────┴──────────────┴────┐              │
│  │              Core Services Layer                     │              │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │              │
│  │  │Geo Query│ │Responder │ │   FCM    │ │  Event │  │              │
│  │  │ Engine  │ │ Ranker   │ │ Notifier │ │ Manager│  │              │
│  │  └─────────┘ └──────────┘ └──────────┘ └────────┘  │              │
│  └─────────────────────────────────────────────────────┘              │
│       │                                          │                    │
│  ┌────┴────┐    ┌──────────┐              ┌──────┴───┐               │
│  │PostgreSQL│   │  Redis   │              │   FCM    │               │
│  │+ PostGIS│    │  Cache   │              │  Server  │               │
│  └─────────┘    └──────────┘              └──────────┘               │
└───────────────────────────────────────────────────────────────────────┘
                          │
                    HTTP (internal)
                          │
┌─────────────────────────┼─────────────────────────────────────────────┐
│                    AI SERVICE LAYER                                    │
│                                                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Emergency │  │ Severity │  │   RAG    │  │ Crisis   │             │
│  │Classifier│  │Predictor │  │ Pipeline │  │ Agent    │             │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘             │
│       │              │             │              │                    │
│  ┌────┴──────────────┴─────────────┴──────────────┴────┐             │
│  │              AI Infrastructure                       │             │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────────────────┐  │             │
│  │  │Embedding│ │  Vector  │ │   Gemini 2.5 (LLM)   │  │             │
│  │  │  Model  │ │  Store   │ │   via LangGraph      │  │             │
│  │  └─────────┘ └──────────┘ └──────────────────────┘  │             │
│  └─────────────────────────────────────────────────────┘             │
└───────────────────────────────────────────────────────────────────────┘
```

### 7.2 Design Principles

1. **Subsystem Ownership**: The backend owns PostgreSQL/PostGIS (real-time coordination data). The AI service owns its vector store (retrieval data). These are deliberately decoupled so that each can be built, tested, and debugged independently.

2. **Reliability-First for the Critical Path**: The SOS trigger uses HTTPS (request/response), not fire-and-forget WebSockets. Alert delivery uses FCM push (which wakes backgrounded phones), not WebSocket messages (which Android kills). Real-time features (chat, live tracking) use WebSockets only *after* the reliable delivery path has succeeded.

3. **AI as a Parallel Enhancement**: AI processing happens in parallel with the alert fan-out. The system delivers alerts immediately; AI-generated guidance arrives shortly after. The critical path (alerting responders) never blocks on the AI path.

### 7.3 Data Flow — Complete SOS Lifecycle

```
User taps SOS
     │
     ▼
[1] HTTPS POST /api/sos/create  ──────────────────────────────┐
     │                                                          │
     ▼                                                          ▼
[2] Backend validates request                          [4] AI Service called
     │                                                   (async, parallel)
     ▼                                                          │
[3] Geospatial query:                                          ▼
    SELECT users WHERE                                  [5] Emergency classified
    ST_DWithin(location,                                    (type + severity)
    sos_location, radius)                                      │
     │                                                          ▼
     ▼                                                  [6] RAG retrieval:
[3a] Responder Ranking:                                    query vector store
     score = w1·(1/dist)                                   for relevant protocols
           + w2·(skill_match)                                  │
           + w3·(reliability)                                  ▼
     │                                                  [7] LLM generates:
     ▼                                                     - First-aid guidance
[3b] Fan-out:                                              - Emergency summary
     ├── FCM Push to all                                       │
     │   ranked responders                                     │
     │                                                          │
     ▼                                                          ▼
[8] Responder taps                                     [9] AI guidance delivered
    "I'm Responding"                                       to responder via
     │                                                     WebSocket/push
     ▼
[10] WebSocket channel opened
     ├── Live location streaming
     ├── In-app chat
     └── Timeline events recorded
     │
     ▼
[11] Emergency resolved
     │
     ▼
[12] AI generates incident report
     Trust scores updated
     Analytics recorded
```

---

## 8. Detailed Module Design

### MoSCoW Prioritisation (3-Phase Model)

To manage scope and ensure a viable product is delivered within the 4-month timeline, all 24 modules are classified into three phases using the MoSCoW framework:

| Phase | Priority | Modules | Rationale |
| --- | --- | --- | --- |
| **Phase 1 — MVP** | **Must Have** | 1–11 (Auth → RAG Knowledge Base) | Core SOS lifecycle: trigger, classify, rank, alert, guide, coordinate, resolve. This is the minimum system that proves the research question. |
| **Phase 2 — Enhancement** | **Should Have** | 12–17 (Translation, Voice SOS, Timeline, Incident Report, Reputation, Community Layer) | Features that enrich the responder/victim experience but are not required for the core SOS loop to function. |
| **Phase 3 — Stretch** | **Could Have** | 18–24 (Admin Dashboard, AI Analytics, Disaster Mode, Guardian Mode, Offline Mode, Digital Twin, Developer Dashboard) | Administrative, analytical, and edge-case features. Built only after Phases 1 and 2 are stable. |

> **Development rule**: No Phase 2 module begins until all Phase 1 modules pass their acceptance criteria. No Phase 3 module begins until Phase 2 is stable. This prevents scope creep from undermining the core deliverable.

---

### Module 1 — Authentication & Identity

**Purpose**: Secure user registration and login with support for anonymous emergency use.

| Feature | Implementation |
| --- | --- |
| Email/Password Login | Firebase Auth + JWT tokens |
| Google Sign-In | OAuth 2.0 via Firebase |
| Phone OTP | Firebase Phone Auth |
| JWT Token Management | Access tokens (15 min) + Refresh tokens (7 days) |
| Anonymous Emergency Mode | Temporary anonymous JWT; no PII stored; SOS location stripped post-resolution |
| Device Registration | FCM token stored per device; updated on each app launch |

**Key Design Decision**: Anonymous mode creates a temporary session with a disposable ID. The SOS event stores `is_anonymous = true`, which triggers privacy guards throughout the system (location is never exposed to responders; only crisis type and guidance are shared).

---

### Module 2 — User Profile

**Purpose**: Comprehensive user identity for trust and skill-based responder matching.

**Schema**:
```
User {
    id: UUID (primary key)
    email: string (unique, nullable for anonymous)
    name: string
    photo_url: string
    phone: string (verified via OTP)
    blood_group: enum [A+, A-, B+, B-, AB+, AB-, O+, O-]
    medical_conditions: string[] (encrypted at rest)
    known_allergies: string[] (encrypted at rest)
    emergency_contacts: [{name, phone, relationship}] (max 5)
    languages: string[] (ISO 639-1 codes)
    skills: [{skill_type, verified, certificate_url, verified_at}]
    trust_score: float (0.0 – 100.0, default 50.0)
    badges: string[]
    location: PostGIS POINT (updated only during active SOS participation)
    fcm_token: string
    is_active: boolean
    created_at: timestamp
    updated_at: timestamp
}
```

**Privacy**: `medical_conditions` and `known_allergies` are encrypted at rest (AES-256) and only decrypted for the user themselves or for an active SOS where the user is the victim (shared with responders only with explicit consent).

---

### Module 3 — Skill Verification

**Purpose**: Build trust in the responder network by verifying claimed skills.

**Workflow**:
```
User claims skill (e.g., "CPR Certified")
        │
        ▼
User uploads proof (certificate photo/PDF)
        │
        ▼
Submission enters Admin verification queue
        │
        ├── Admin approves → Verified badge ✓
        │                    Skill tagged as verified in DB
        │                    Trust score +5 per verified skill
        │
        └── Admin rejects → User notified with reason
                             Can re-submit with corrections
```

**Supported Skills**:
| Skill | Required Proof |
| --- | --- |
| Doctor | Medical License / Registration Number |
| Nurse | Nursing Council Registration |
| Paramedic | Paramedic certification |
| Firefighter | Department ID / Certificate |
| Police | Service ID |
| CPR Certified | CPR/BLS certification |
| First Aid Trained | Red Cross / St. John certificate |
| Blood Donor | Donor card or recent donation receipt |
| Electrician | Trade license |
| Mechanic | Trade license |

---

### Module 4 — AI Emergency Detection

**Purpose**: Automatically classify emergency type from multimodal input instead of requiring manual selection.

**Input Modalities**:
| Modality | Processing Pipeline |
| --- | --- |
| Text | Direct embedding → similarity match against crisis type embeddings |
| Voice | Speech-to-Text (Google Speech API) → Text pipeline |
| Photo | Vision model (Gemini 2.5 Vision) → scene description → Text pipeline |
| Video | Frame extraction → Vision model → aggregated classification |

**Output Schema**:
```json
{
    "emergency_type": "medical",
    "sub_type": "cardiac_arrest",
    "priority": "critical",
    "confidence": 0.94,
    "recommended_radius_km": 3,
    "suggested_responder_skills": ["doctor", "nurse", "cpr_certified"],
    "immediate_action": "Begin CPR immediately if victim is unresponsive",
    "requires_professional": true,
    "call_emergency_services": true
}
```

**Classification Method**: Embedding-similarity matching against a predefined set of crisis type descriptions, not a custom-trained classifier. Each crisis type (medical, fire, gas leak, accident, natural disaster, security threat, etc.) has a reference embedding. The input's embedding is compared via cosine similarity to find the best match. This is simple, explainable, and does not require training data.

---

### Module 5 — AI Severity Prediction

**Purpose**: Go beyond simple High/Medium/Low to provide a quantified severity assessment that drives responder radius and priority.

**Severity Calculation**:
```
Input: emergency_type + free_text_description + detected_keywords

LLM Prompt (structured):
  "Given the following emergency description, assess severity on a 0-100 scale.
   Consider: immediacy of threat to life, number of people affected,
   whether professional help is required, time sensitivity.
   Return: score, confidence, reasoning, recommended_actions."

Output:
  severity_score: 96/100
  confidence: 0.94
  reasoning: [
    "Unconscious victim indicates possible cardiac arrest",
    "No breathing suggests immediate life threat",
    "CPR needed within 4 minutes for survival"
  ]
  recommended_radius_km: 3  (auto-scaled based on severity)
  auto_call_services: true   (severity > 80 triggers this flag)
```

**How Severity Affects the System**:
| Severity Range | Radius | Notification Priority | Auto-call Services |
| --- | --- | --- | --- |
| 80–100 (Critical) | 3–5 km | Immediate push to all matched | Yes |
| 50–79 (High) | 2–3 km | Push to top-ranked responders | Suggested |
| 20–49 (Medium) | 1–2 km | Standard notification | No |
| 0–19 (Low) | 0.5–1 km | Low-priority notification | No |

---

### Module 6 — Smart SOS Engine

**Purpose**: Replace naive "notify everyone in radius" with intelligent, context-aware responder selection.

**Decision Pipeline**:
```
Emergency Created
       │
       ▼
AI classifies type + severity (Modules 4, 5)
       │
       ▼
Geospatial query returns candidates within radius
       │
       ▼
Responder Ranking Algorithm scores each candidate
(see Section 12 for algorithm details)
       │
       ▼
Top-N responders notified via FCM (N based on severity)
       │
       ▼
┌─────────────────────────────────────────────────┐
│         3-LAYER ESCALATION PROTOCOL             │
├─────────────────────────────────────────────────┤
│                                                 │
│  LAYER 1 — Auto-Radius Expansion (0–60 sec)     │
│  ├── Initial radius based on severity           │
│  ├── If no acceptance within 30s → 2× radius    │
│  ├── If still none within 45s → 3× radius       │
│  └── Re-rank and notify new candidates          │
│                                                 │
│  LAYER 2 — Direct 108/112 Dial (60 sec)         │
│  ├── If no volunteer accepts within 60s         │
│  ├── System triggers Android ACTION_CALL intent │
│  │   to 108 (ambulance) or 112 (unified)        │
│  ├── Pre-filled emergency summary read by TTS   │
│  └── User consent obtained during SOS setup     │
│                                                 │
│  LAYER 3 — Guided Self-Care AI (fallback)       │
│  ├── If no responder AND no network for calling │
│  ├── AI Crisis Assistant (Module 10) activates  │
│  ├── Step-by-step self-care via RAG pipeline    │
│  └── Guidance cached offline for common crises  │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Escalation Timing**:
| Time Since SOS | Layer | Action |
| --- | --- | --- |
| 0–30 seconds | Layer 1a | Initial radius, top-N responders notified |
| 30–45 seconds | Layer 1b | Radius doubled, re-rank and notify new candidates |
| 45–60 seconds | Layer 1c | Radius tripled, all available responders notified |
| 60 seconds | Layer 2 | Auto-dial 108/112 with AI-generated emergency summary |
| Any time (no connectivity) | Layer 3 | AI Self-Care guidance activated for victim |

**Example Scenarios**:
| Emergency | Primary Responders | Secondary | Radius |
| --- | --- | --- | --- |
| Cardiac arrest | Doctors, Nurses, CPR-trained | All nearby | 3 km |
| Gas leak | Firefighters, Electricians | Nearby volunteers | 2 km |
| Road accident | Doctors, Paramedics | Police, Volunteers | 2 km |
| Fire | Firefighters | All nearby | 3 km |
| Security threat | Police | Nearby volunteers | 1 km |

---

### Module 7 — Live Map

**Purpose**: Real-time situational awareness for all participants.

**Map Layers**:
| Layer | Data Source | Update Frequency |
| --- | --- | --- |
| Victim location | SOS event | On creation (static for anonymous) |
| Responder locations | WebSocket location stream | Every 3–5 seconds |
| Hospitals | Static dataset + Google Places API | Cached, refreshed daily |
| Police stations | Static dataset | Cached |
| Fire stations | Static dataset | Cached |
| AED locations | Community-contributed + verified | On update |
| Traffic conditions | Google Maps Traffic Layer | Real-time |

**Implementation**: Google Maps SDK for Android with custom markers, polyline routes, and real-time overlay updates via WebSocket data.

---

### Module 8 — Live Tracking

**Purpose**: Uber-like tracking where the victim can see responders approaching.

**Technical Implementation**:
```
Responder accepts → WebSocket connection opened
       │
       ▼
Android FusedLocationProvider streams GPS every 3 seconds
       │
       ▼
Location sent via WebSocket to backend
       │
       ▼
Backend broadcasts to victim's WebSocket channel
       │
       ▼
Victim's map updates responder marker position
       │
       ▼
ETA calculated using Google Directions API
(recalculated every 15 seconds)
```

---

### Module 9 — AI Navigation

**Purpose**: Provide the fastest *rescue* route, not just the shortest route.

**Factors Considered**:
- Real-time traffic data (Google Maps Traffic)
- Known road closures and construction (stored in local DB, admin-updated)
- Weather-related blockages (flood zones, landslide areas)
- One-way restrictions and emergency vehicle access

**Implementation**: Google Directions API with `departure_time=now` for real-time traffic, combined with a local overlay of known blockages. The AI layer can suggest alternate routes when the primary route has known issues.

---

### Module 10 — AI Crisis Assistant (Emergency Agent)

**Purpose**: An AI agent that actively assists during an emergency, not a passive chatbot.

**Agent Architecture (LangGraph)**:
```
                    ┌─────────────────┐
                    │   User Input    │
                    │  (text/voice)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Intent Router   │
                    │ (LangGraph node)│
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼───┐  ┌──────▼──────┐ ┌─────▼──────┐
     │First Aid   │  │ Follow-up   │ │ Coordinate │
     │ Guidance   │  │ Questions   │ │ Responders │
     │ (RAG node) │  │ (LLM node)  │ │  (API node)│
     └────────┬───┘  └──────┬──────┘ └─────┬──────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼────────┐
                    │Response Builder │
                    │+ Translation   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Deliver to     │
                    │  User/Responder │
                    └─────────────────┘
```

**Agent Capabilities**:
1. **Understand**: Parse emergency description, classify type and severity.
2. **Ask**: Generate clarifying follow-up questions ("Is the person breathing?", "How old is the patient?").
3. **Guide**: Provide step-by-step first aid from RAG knowledge base.
4. **Summarize**: Generate a structured emergency summary for ambulance dispatch.
5. **Translate**: Real-time translation between victim and responder languages.
6. **Coordinate**: Suggest task distribution among multiple responders.
7. **Locate**: Recommend nearest appropriate hospital based on emergency type and availability.

---

### Module 11 — RAG Knowledge Base

**Purpose**: Ground all AI-generated medical/emergency guidance in verified, published protocols to prevent hallucination.

**Knowledge Sources**:
| Source | Content | License |
| --- | --- | --- |
| WHO First Aid Guidelines | Standardized first-aid procedures | Public |
| Indian Red Cross Society | India-specific emergency protocols | Public |
| National Disaster Management Authority (NDMA) | Disaster response procedures | Public/Government |
| American Heart Association CPR Guidelines | CPR and BLS protocols | Public summary |
| St. John Ambulance First Aid Manual | Comprehensive first-aid procedures | Public excerpts |
| AIIMS Poison Information | Poison management protocols | Public |
| National Snakebite Protocol (India) | Snakebite first-response | Government |
| Fire Safety Manual (National Fire Service) | Fire emergency procedures | Public |

**RAG Pipeline**:
```
[1] Document Ingestion
     │
     ├── PDF/HTML parsing
     ├── Chunking: procedure-level passages (not whole documents)
     │   Target: 200-400 tokens per chunk
     │   Overlap: 50 tokens
     │   Strategy: Split by procedure steps, not arbitrary word count
     │
     ▼
[2] Embedding Generation
     │
     ├── Model: sentence-transformers/all-MiniLM-L6-v2 (or similar)
     │   Dimension: 384
     │   Reason: Small, fast, sufficient for this corpus size
     │
     ▼
[3] Vector Store Indexing
     │
     ├── Store: ChromaDB (in-process, simple deployment)
     │   Alternative: pgvector (if co-located with PostgreSQL)
     │   Metadata per chunk: source, procedure_name, crisis_type, step_number
     │
     ▼
[4] Query-Time Retrieval
     │
     ├── Query: crisis_type + user_description embedded
     ├── Top-K retrieval: K=5 (tunable)
     ├── Re-ranking: by metadata match (crisis_type filter) + similarity score
     │
     ▼
[5] LLM Generation (Gemini 2.5)
     │
     ├── Prompt template (structured):
     │   """
     │   You are an emergency first-aid assistant.
     │   Given the following verified medical procedures:
     │   {retrieved_passages}
     │
     │   And the following emergency:
     │   Type: {crisis_type}
     │   Description: {user_description}
     │   Severity: {severity_score}
     │
     │   Provide step-by-step guidance. CITE which procedure and step
     │   number you are referencing for each instruction.
     │   Do NOT provide any advice not supported by the retrieved procedures.
     │   If the retrieved procedures do not cover this situation,
     │   say "Please wait for professional medical help" and suggest
     │   calling emergency services.
     │   """
     │
     ▼
[6] Response with Citations
     │
     └── Each guidance step includes:
         - The instruction
         - Source reference (e.g., "WHO First Aid, Choking Response, Step 3")
         - Confidence indicator
```

**Chunking Strategy Rationale**: Emergency protocols are inherently step-based ("Step 1: Check responsiveness", "Step 2: Call for help", "Step 3: Begin chest compressions"). Chunking at the procedure-step level preserves the natural granularity of the source material and ensures that retrievals return actionable, specific instructions rather than entire manual chapters.

---

### Module 12 — AI Translation

**Purpose**: Break language barriers during emergencies.

**Implementation**:
| Feature | Method |
| --- | --- |
| Text translation | Gemini 2.5 (supports 100+ languages natively) |
| Voice translation | Speech-to-Text → Translate → Text-to-Speech |
| Emergency summary translation | Pre-translate summary into all responder languages |

**Key Design**: Translation happens at the *message level* in the chat system. Each message is stored in its original language; translations are generated on-demand for the recipient's language preference.

---

### Module 13 — Voice SOS

**Purpose**: Enable emergency creation without typing — critical when the user is injured, scared, or in a situation where typing is impractical.

**Pipeline**:
```
User presses SOS button and speaks
           │
           ▼
Google Speech-to-Text API
(streaming recognition, language auto-detect)
           │
           ▼
Transcribed text sent to Gemini 2.5
with structured extraction prompt:
  "Extract: emergency_type, description, number_of_victims,
   victim_condition, location_description, urgency_level"
           │
           ▼
Structured JSON returned
           │
           ▼
Emergency created via standard SOS API
(user confirms on screen before submission)
```

---

### Module 14 — Emergency Timeline

**Purpose**: Automatic, auditable record of every event during an emergency.

**Events Tracked**:
```
timestamp | event_type         | actor        | details
──────────┼───────────────────┼──────────────┼──────────────────
7:10:00   | sos_created        | victim       | Medical emergency
7:10:02   | ai_classified      | system       | Cardiac arrest, severity 96
7:10:03   | responders_notified| system       | 12 responders in 3km
7:10:15   | response_accepted  | Dr. Sharma   | ETA 4 min
7:10:18   | response_accepted  | Amit (CPR)   | ETA 2 min
7:10:22   | ai_guidance_sent   | system       | CPR protocol delivered
7:12:30   | responder_arrived  | Amit (CPR)   | GPS confirmed on-site
7:12:45   | action_logged      | Amit (CPR)   | CPR started
7:15:00   | responder_arrived  | Dr. Sharma   | GPS confirmed on-site
7:19:00   | ambulance_arrived  | system       | 108 ambulance on-site
7:24:00   | sos_resolved       | Dr. Sharma   | Patient transported
```

**Implementation**: Events are appended to a `timeline_events` table with `sos_event_id` as a foreign key. Each event is also broadcast to all connected participants via WebSocket for real-time display.

---

### Module 15 — AI Incident Report

**Purpose**: Auto-generate a structured incident report for authorities, hospitals, and records.

**Report Contents**:
```
INCIDENT REPORT — #SOS-2026-07-27-0042

Type: Medical — Suspected Cardiac Arrest
Location: 22.5726° N, 88.3639° E (Salt Lake, Kolkata)
Time: 07:10 – 07:24 (14 minutes)

Victim: Anonymous (anonymous mode)
Responders: 2 (Dr. Priya Sharma [verified], Amit Kumar [CPR certified])

Timeline: [auto-generated from Module 14]

Treatment Given:
- CPR administered for 6 minutes by Amit Kumar
- Dr. Sharma assessed and monitored vitals upon arrival

Outcome: Patient stabilized, transported via 108 ambulance to
         AMRI Hospital, Salt Lake

Average Response Time: 2 min 30 sec (first responder)
AI Latency: 1.8 sec (classification + guidance generation)

AI Guidance Accuracy: Cited WHO CPR Protocol Steps 1-5
                      All steps were applicable and followed
```

---

### Module 16 — Reputation Engine

**Purpose**: Build trust in the network by rewarding genuine responders and penalizing misuse.

**Trust Score Algorithm**:
```
Initial Score: 50.0

Positive Factors:
  +5  per verified skill
  +3  per successful response (arrived + helped)
  +2  per positive feedback from victim
  +1  per response acceptance
  +5  bonus for response time < 5 min

Negative Factors:
  -10 for false emergency creation
  -5  for accepting and not showing up
  -3  for negative feedback from victim
  -20 for reported misconduct (admin-reviewed)
  -50 for confirmed fraud (account suspension)

Score clamped to [0.0, 100.0]
```

**Feedback Loop**: After each resolved SOS, both victim and responders can rate the interaction. Consistent positive behavior earns badges (e.g., "First Responder", "Community Hero", "Lifesaver").

---

### Module 17 — Community Resource Layer

**Purpose**: Overlay critical community resources on the map for everyday and emergency use.

**Resources**:
| Resource | Data Source | Update Method |
| --- | --- | --- |
| AED (Automated External Defibrillator) locations | Community-contributed | Admin-verified |
| Blood banks | Government database + Google Places | Periodic sync |
| Hospitals | Google Places API | Cached, refreshed daily |
| Police stations | Government database | Static |
| Fire stations | Government database | Static |
| Shelters | Government + NGO data | Admin-managed |
| Public restrooms | Community-contributed | Admin-verified |
| Wheelchair-accessible routes | Community-contributed | Admin-verified |

---

### Module 18 — Admin Dashboard

**Purpose**: Web-based administrative panel for system management and oversight.

**Features**:
| Feature | Description |
| --- | --- |
| Live Map | All active SOS events with real-time status |
| Analytics | Response time trends, peak hours, heatmaps |
| User Management | Verify skills, suspend users, review reports |
| Fraud Detection | Flag suspicious patterns (rapid SOS creation, always nearby) |
| Skill Verification Queue | Review and approve/reject skill submissions |
| Emergency Trends | Historical data visualization |
| System Health | API latency, WebSocket connections, DB performance |

**Implementation**: React.js or Next.js web application, deployed separately from the mobile API.

---

### Module 19 — AI Analytics

**Purpose**: Use AI to derive actionable insights from emergency data.

**Queries the System Can Answer**:
- Which areas have the highest emergency frequency? (Heatmap)
- What is the average response time by area, time of day, and emergency type?
- What are the most common emergency types?
- Who are the most active and reliable volunteers?
- What are peak emergency hours?
- Are there emerging patterns (e.g., increasing gas leak reports in a specific neighborhood)?

**Implementation**: Scheduled batch analysis jobs that aggregate data and generate reports. Visualization via Chart.js / Recharts on the admin dashboard.

---

### Module 20 — Disaster Mode

**Purpose**: Scale from individual SOS events to mass-casualty / natural disaster scenarios.

**Differences from Normal Mode**:
| Aspect | Normal SOS | Disaster Mode |
| --- | --- | --- |
| Events | Single victim | Multiple concurrent victims |
| Coordination | 1:N (one victim, many responders) | N:M (many victims, coordinated teams) |
| Communication | Single chat channel | Coordination room with sub-channels |
| Resources | Nearby individuals | Organized teams, shelters, supply points |
| Duration | Minutes | Hours to days |

**Trigger**: Admin-activated or auto-detected when multiple SOS events cluster in the same area within a short time window.

---

### Module 21 — Guardian Mode

**Purpose**: Proactive safety for vulnerable users.

**Implementation**:
- Users can designate themselves as "protected" (children, senior citizens, disabled) or be designated by a guardian.
- Guardians are linked accounts who receive immediate notification on any SOS from their ward.
- Guardian notifications bypass normal ranking — they are always notified first.
- Optional: periodic "safety check-in" ping that alerts guardians if unanswered.

---

### Module 22 — Offline Mode (SMS Fallback)

**Purpose**: Ensure SOS functionality even without internet connectivity.

**Flow**:
```
No internet detected on device
         │
         ▼
User triggers SOS → pre-formatted SMS sent to
dedicated server phone number
         │
         ▼
SMS gateway receives message
         │
         ▼
Server parses SMS → creates SOS event
(location from last known GPS or cell tower triangulation)
         │
         ▼
Normal SOS pipeline continues
(notifications to internet-connected responders)
```

**Limitation**: No real-time tracking or chat in offline mode. Responders are notified, but coordination relies on phone calls.

---

### Module 23 — Digital Twin Simulator

**Purpose**: Scientifically evaluate system performance without needing real emergencies.

**Simulation Parameters**:
| Parameter | Range |
| --- | --- |
| Virtual users | 100 – 10,000 |
| Virtual responders (with skills) | 50 – 2,000 |
| Concurrent SOS events | 1 – 100 |
| Geographic area | Configurable (e.g., Kolkata metro, 500 km²) |
| Emergency type distribution | Configurable per scenario |
| Responder response probability | 0.3 – 0.9 |
| Network latency simulation | 50ms – 500ms |

**Metrics Measured**:
| Metric | How Measured |
| --- | --- |
| Average time-to-first-responder | From SOS creation to first acceptance |
| Notification delivery rate | FCM delivery receipts |
| Geospatial query latency | Database query timing (with and without index) |
| WebSocket message latency | End-to-end timestamp comparison |
| AI pipeline latency | Time from request to generated response |
| System throughput | Max concurrent SOS events before degradation |

**Implementation**: Python-based simulation framework using Locust (for load testing) and custom scripts for scenario generation. Results are stored and visualized on the admin dashboard.

**Defense Demo Charts (Viva Preparation)**:

The Digital Twin Simulator generates the following comparison visualisations specifically designed for the project defense/viva presentation. These charts provide **empirical evidence** answering the core research questions:

| Chart | Comparison | Research Question |
| --- | --- | --- |
| **Time-to-First-Responder** | AI-ranked dispatch vs. naive broadcast-all | RQ1: Is AI-based selection faster? |
| **Geospatial Query Latency** | With PostGIS index vs. without index (at 1K, 10K, 100K users) | RQ5: Index performance impact |
| **AI Pipeline Latency Breakdown** | Classification time + Retrieval time + Generation time (stacked bar) | RQ3: Is AI latency acceptable? |
| **Throughput Curve** | Response time (y-axis) vs. concurrent SOS events (x-axis) at 10, 50, 100 events | RQ4: How does the system scale? |
| **Skill-Aware vs. Distance-Only** | Responder relevance score comparison across emergency types | RQ2: Does skill matching improve quality? |

```
Example Defense Chart: Time-to-First-Responder

  Response     │
  Time (sec)   │
               │
  180 ─────────│─── ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
               │                                 │  ← Broadcast-all
  120 ─────────│─── ─ ─ ─ ─ ─ ─ ─ ─ ┐           │     (avg 162s)
               │                     │           │
   60 ─────────│──── ┐               │           │
               │     │ ← AI-ranked   │           │
    0 ─────────┼─────┴───────────────┴───────────┴──
               │   AI-Ranked     Broadcast    No System
               │   Dispatch      All          (baseline)
```

These charts are auto-generated from simulation data and exported as high-resolution PNGs for inclusion in the defense presentation slides.

---

### Module 24 — Developer Dashboard

**Purpose**: Internal tooling for development, debugging, and monitoring.

**Components**:
| Component | Tool |
| --- | --- |
| API Documentation | Swagger/OpenAPI (auto-generated by FastAPI) |
| Application Logs | Structured JSON logging → aggregated view |
| Performance Monitoring | Prometheus metrics + Grafana dashboards |
| Database Inspector | pgAdmin / Adminer |
| Redis Monitor | Redis CLI / RedisInsight |
| WebSocket Inspector | Custom debug panel showing active connections |
| Error Tracking | Sentry (or equivalent) |

---

## 9. AI/ML Pipeline Design

### 9.1 Overview

The AI subsystem is designed as a **separate, independently deployable service** that the backend calls via internal HTTP. This separation ensures that:
- AI latency does not block the critical alert path.
- The AI service can be scaled, updated, and debugged independently.
- Vector store maintenance (re-indexing, corpus updates) does not affect the main application.

### 9.2 Model Selection Rationale

| Component | Model | Reason |
| --- | --- | --- |
| LLM (Generation) | Gemini 2.5 | Strong multilingual support (critical for India), vision capabilities for photo/video input, structured output support |
| Embeddings | `all-MiniLM-L6-v2` or Gemini embedding model | Small, fast, sufficient for a corpus of ~500–2000 chunks |
| Speech-to-Text | Google Speech API | Best-in-class for Indian languages and accents |
| Agent Orchestration | LangGraph | Graph-based agent state management; supports multi-step reasoning with tool use |

### 9.3 Why RAG, Not Fine-Tuning

| Approach | Pros | Cons | Decision |
| --- | --- | --- | --- |
| Fine-tuning | Faster inference, no retrieval step | Requires training data, hard to update, expensive, risk of catastrophic forgetting | ❌ Not chosen |
| RAG | Easy to update corpus, citations possible, no training required, grounded in sources | Retrieval latency, depends on chunking quality | ✅ Chosen |

For a corpus of verified medical protocols that may be updated (new WHO guidelines, regional protocol changes), RAG is the correct choice. Updates require only re-embedding new documents, not retraining a model.

### 9.4 Hallucination Prevention

1. **Source grounding**: The LLM prompt explicitly instructs the model to cite retrieved passages and refuse to provide advice not supported by them.
2. **Retrieval confidence threshold**: If the top retrieved passage has a similarity score below 0.6, the system returns a "Please wait for professional help" message instead of generating potentially incorrect guidance.
3. **Post-generation verification**: The generated response is checked for references to retrieved passage IDs. If no references are found, the response is flagged for review.
4. **Structured output**: Using Gemini's structured output (JSON mode), the response format is enforced, preventing free-form generation.
5. **Strict scope guardrail**: The system prompt explicitly prohibits dosage recommendations, medical diagnosis, surgical advice, and medication prescriptions. Output is limited exclusively to publicly-available, expert-verified first-aid protocols (e.g., WHO, Red Cross, AHA). Any query outside this scope returns: *"This is beyond first-aid guidance. Please consult a medical professional or call emergency services."*

---

## 10. Data Model & Database Design

### 10.1 Entity-Relationship Diagram

```
┌──────────────┐       ┌───────────────────┐       ┌──────────────┐
│    users     │       │    sos_events     │       │  responses   │
├──────────────┤       ├───────────────────┤       ├──────────────┤
│ id (PK)      │──┐    │ id (PK)           │──┐    │ id (PK)      │
│ email        │  │    │ broadcaster_id(FK)│  │    │sos_event_id  │
│ name         │  └───>│ crisis_type       │  │    │  (FK)        │
│ phone        │       │ sub_type          │  └───>│ responder_id │
│ blood_group  │       │ severity_score    │       │  (FK → users)│
│ medical_cond │       │ location (POINT)  │       │ status       │
│ allergies    │       │ status            │       │ joined_at    │
│ emerg_contact│       │ is_anonymous      │       │ arrived_at   │
│ languages    │       │ created_at        │       │ feedback_score│
│ skills (JSON)│       │ resolved_at       │       └──────────────┘
│ trust_score  │       │ description       │
│ badges       │       └───────────────────┘       ┌──────────────┐
│ location     │                │                   │   messages   │
│  (POINT)     │                │                   ├──────────────┤
│ fcm_token    │                │                   │ id (PK)      │
│ is_active    │                └──────────────────>│sos_event_id  │
│ created_at   │                                    │  (FK)        │
└──────────────┘                                    │ sender_id    │
                                                    │  (FK → users)│
┌──────────────┐       ┌───────────────────┐       │ text         │
│ai_summaries  │       │ timeline_events   │       │ language     │
├──────────────┤       ├───────────────────┤       │ timestamp    │
│ id (PK)      │       │ id (PK)           │       └──────────────┘
│sos_event_id  │       │sos_event_id (FK)  │
│  (FK)        │       │ event_type        │
│ guidance     │       │ actor_id (FK)     │
│ summary      │       │ details (JSON)    │
│ retrieved_   │       │ timestamp         │
│  refs (JSON) │       └───────────────────┘
│ severity     │
│ crisis_type  │       ┌───────────────────┐
│ confidence   │       │skill_verifications│
│ created_at   │       ├───────────────────┤
└──────────────┘       │ id (PK)           │
                       │ user_id (FK)      │
                       │ skill_type        │
                       │ certificate_url   │
                       │ status            │
                       │ reviewed_by (FK)  │
                       │ submitted_at      │
                       │ reviewed_at       │
                       └───────────────────┘
```

### 10.2 Geospatial Indexing

```sql
-- PostgreSQL + PostGIS
CREATE INDEX idx_users_location ON users USING GIST (location);

-- Nearby user query
SELECT id, name, skills, trust_score,
       ST_Distance(location, ST_SetSRID(ST_MakePoint(lon, lat), 4326)) as distance
FROM users
WHERE ST_DWithin(
    location,
    ST_SetSRID(ST_MakePoint(lon, lat), 4326),
    radius_meters
)
AND is_active = true
ORDER BY distance;
```

### 10.3 Privacy Constraints

| Data | Storage Rule | Access Rule |
| --- | --- | --- |
| `users.location` | Updated only during active SOS participation; set to NULL otherwise | Never exposed to other users directly |
| `sos_events.location` | Stored for event duration; anonymized for analytics after resolution | Visible to responders ONLY if `is_anonymous = false` |
| `users.medical_conditions` | Encrypted at rest (AES-256) | Decrypted only for the user or for consented emergency sharing |
| `messages.text` | Stored for event duration + 30 days | Accessible only to event participants |

---

## 11. API Design

### 11.1 Core REST Endpoints

#### Authentication
```
POST   /api/auth/register          Register new user
POST   /api/auth/login             Email/password login
POST   /api/auth/google            Google OAuth login
POST   /api/auth/phone/send-otp    Send phone OTP
POST   /api/auth/phone/verify      Verify phone OTP
POST   /api/auth/refresh           Refresh JWT token
POST   /api/auth/anonymous         Create anonymous session
```

#### User Profile
```
GET    /api/users/me               Get current user profile
PUT    /api/users/me               Update profile
POST   /api/users/me/skills        Add skill claim
POST   /api/users/me/fcm-token     Update FCM token
PUT    /api/users/me/location      Update location (active SOS only)
```

#### SOS Events
```
POST   /api/sos/create             Create SOS event (idempotency key required)
GET    /api/sos/{id}               Get SOS event details
PUT    /api/sos/{id}/resolve       Resolve SOS event
GET    /api/sos/active             Get user's active SOS events
POST   /api/sos/{id}/respond       Accept/respond to SOS (idempotency key required)
GET    /api/sos/{id}/timeline      Get event timeline
GET    /api/sos/{id}/report        Get AI-generated incident report
```

#### AI Service
```
POST   /api/ai/classify            Classify emergency from text/voice/image
POST   /api/ai/severity            Predict severity score
POST   /api/ai/guidance            Get RAG-based first-aid guidance
POST   /api/ai/translate           Translate text between languages
POST   /api/ai/summary             Generate emergency summary
```

#### Admin
```
GET    /api/admin/dashboard         Dashboard statistics
GET    /api/admin/verifications     Pending skill verifications
PUT    /api/admin/verifications/{id} Approve/reject verification
GET    /api/admin/analytics         Analytics data
GET    /api/admin/users             User management
PUT    /api/admin/users/{id}/suspend Suspend user
```

### 11.2 WebSocket Events

```
# Client → Server
ws:connect          { sos_event_id, token }
ws:location_update  { lat, lon, timestamp }
ws:send_message     { text, language }
ws:action_log       { action_type, details }

# Server → Client
ws:responder_update { responder_id, lat, lon, eta }
ws:new_message      { sender, text, translated_text, timestamp }
ws:timeline_event   { event_type, actor, details, timestamp }
ws:ai_guidance      { guidance_text, source_refs }
ws:sos_resolved     { resolved_by, timestamp }
```

---

## 12. Responder Ranking Algorithm

### 12.1 Scoring Function

```
Score(responder, emergency) = w1 · D(responder, emergency)
                            + w2 · S(responder, emergency)
                            + w3 · R(responder)
```

Where:

**D (Distance Score)** — Normalized inverse distance:
```
D = 1 - (distance / max_radius)
Range: [0, 1] where 1 = at the location, 0 = at the radius boundary
```

**S (Skill Match Score)** — How well the responder's skills match the emergency needs:
```
S = |responder_skills ∩ required_skills| / |required_skills|
Bonus: +0.2 if any matching skill is verified
Range: [0, 1.2]
```

**R (Reliability Score)** — Normalized trust score:
```
R = trust_score / 100
Range: [0, 1]
```

### 12.2 Default Weights

| Weight | Value | Rationale |
| --- | --- | --- |
| w1 (Distance) | 0.4 | Proximity is the strongest factor — minutes matter |
| w2 (Skill Match) | 0.35 | A skilled responder further away is often more valuable than an unskilled one nearby |
| w3 (Reliability) | 0.25 | Ensures consistently reliable responders are preferred |

### 12.3 Validation Scenario

**Scenario**: Cardiac arrest at Location A. Two potential responders:
- **Responder 1**: 200m away, no medical skills, trust score 60
- **Responder 2**: 800m away, verified nurse + CPR, trust score 85

With max_radius = 3000m:

```
Responder 1: 0.4 × (1 - 200/3000) + 0.35 × 0 + 0.25 × 0.60 = 0.373 + 0 + 0.150 = 0.523
Responder 2: 0.4 × (1 - 800/3000) + 0.35 × 1.2 + 0.25 × 0.85 = 0.293 + 0.420 + 0.213 = 0.926
```

**Result**: The nurse at 800m ranks significantly higher than the unskilled responder at 200m. ✅ Correct behavior.

---

## 13. Safety-Critical Engineering

### 13.1 Idempotency

All state-changing operations on the critical path require client-generated idempotency keys:

```
POST /api/sos/create
Header: Idempotency-Key: <UUID generated by client>

Server behavior:
  1. Check if Idempotency-Key exists in Redis (TTL: 24 hours)
  2. If exists → return cached response (no duplicate event created)
  3. If not → process request, cache response with Idempotency-Key
```

This prevents duplicate SOS events when a user's flaky connection causes request retries.

### 13.2 FCM Delivery Confirmation

```
FCM Push Sent
     │
     ▼
Wait for delivery receipt (up to 30 seconds)
     │
     ├── Delivered → Mark as delivered in DB
     │
     └── Not delivered → 
         ├── Retry (up to 3 times, exponential backoff)
         └── If still failed → Flag for SMS fallback
```

### 13.3 Load Testing Plan

**Tool**: Locust (Python-based load testing framework)

**Test Scenarios**:
| Scenario | Description | Target |
| --- | --- | --- |
| Single SOS | One SOS event, measure full pipeline latency | < 2 seconds end-to-end |
| Concurrent SOS | 10/50/100 simultaneous SOS events | < 5 seconds per event |
| Geo query benchmark | 1000 users in DB, measure query time with/without index | < 50ms with index |
| WebSocket load | 100 concurrent WebSocket connections, location updates every 3s | No dropped messages |
| AI pipeline | 50 concurrent RAG queries | < 3 seconds per query |

### 13.4 Medical Liability Safeguards

NearHelp AI provides **protocol-based first-aid guidance**, not medical advice. The following safeguards address medical liability:

**Legal Framework**:
| Protection | Reference | Application |
| --- | --- | --- |
| Good Samaritan Law (India) | Supreme Court of India, *SaveLIFE Foundation v. Union of India* (2016) | Protects bystanders who assist accident victims in good faith from legal liability |
| MoRTH Guidelines | Ministry of Road Transport & Highways, 2015 | Establishes that Good Samaritans shall not be liable for civil or criminal action for any injury/death of the victim |
| WHO Good Samaritan Principles | World Health Organization, 2023 | International framework supporting bystander intervention with legal protections |

**UI Disclaimer Requirements**:

A persistent, non-dismissible disclaimer must be displayed on all AI guidance screens:

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️ DISCLAIMER                                                 │
│                                                                 │
│  This guidance is based on published first-aid protocols        │
│  (WHO, Red Cross, AHA) and is NOT a substitute for              │
│  professional medical advice, diagnosis, or treatment.          │
│                                                                 │
│  Always call emergency services (108/112) for serious           │
│  medical emergencies. By using this guidance, you               │
│  acknowledge that NearHelp AI provides protocol-based           │
│  assistance only.                                               │
│                                                                 │
│  Protected under India's Good Samaritan Law (2016).             │
└─────────────────────────────────────────────────────────────────┘
```

**Technical Enforcement (RAG Guardrails)**:

The following constraints are enforced at the prompt level (see §9.4 for implementation):

| Rule | Enforcement |
| --- | --- |
| No dosage recommendations | System prompt prohibition + post-generation filter |
| No medical diagnosis | System prompt prohibition; response must use "possible" / "suspected" language only |
| No surgical or invasive procedure advice | System prompt prohibition; hardcoded blocklist of terms |
| No medication prescriptions | System prompt prohibition + post-generation filter |
| Citation required for every instruction | Prompt template enforces source citation; uncited instructions are stripped |
| Confidence threshold | Retrieval similarity < 0.6 triggers fallback: "Please wait for professional help" |
| Scope boundary | Any query outside first-aid protocols returns a referral to emergency services |

---

## 14. Security & Privacy Design

### 14.1 Authentication & Authorization

| Mechanism | Implementation |
| --- | --- |
| Password hashing | bcrypt (cost factor 12) |
| Token management | JWT with RS256 signing |
| API rate limiting | Redis-based, 100 req/min per user, 10 SOS/day per user |
| Role-based access | User, Verified Responder, Admin roles |
| Input validation | Pydantic models with strict type checking |

### 14.2 Data Protection

| Data Category | Protection |
| --- | --- |
| Passwords | bcrypt hash, never stored in plaintext |
| Medical data | AES-256 encryption at rest |
| Location data | Stored only during active events; purged after resolution (or anonymized for analytics) |
| Communication | TLS 1.3 for all API and WebSocket connections |
| FCM tokens | Stored encrypted; rotated on each app launch |

### 14.3 Anonymous Mode Privacy Guarantees

When `is_anonymous = true`:
1. No user ID is associated with the SOS event (only a temporary session ID).
2. Location is used for geospatial query but **never** sent to responders — responders receive only crisis type, severity, and AI guidance.
3. After resolution, the temporary session is destroyed and the location is removed from the event record.
4. Chat messages are stored with the temporary session ID and auto-deleted after 24 hours.

---

## 15. Technology Stack

### 15.1 Full Stack Breakdown

| Layer | Technology | Version | Justification |
| --- | --- | --- | --- |
| **Mobile** | Kotlin + Jetpack Compose | Latest stable | Modern Android UI toolkit; declarative UI |
| **Mobile Maps** | Google Maps SDK for Android | Latest | Best-in-class maps for India; traffic layer, directions API |
| **Mobile Push** | Firebase Cloud Messaging | Latest | Reliable push delivery to backgrounded Android apps; free tier sufficient |
| **Backend Framework** | FastAPI (Python) | 0.100+ | Async-first, auto-generated OpenAPI docs, Pydantic validation, WebSocket support |
| **Database** | PostgreSQL 16 + PostGIS 3.4 | Latest | Mature RDBMS + best-in-class geospatial extension |
| **Cache** | Redis 7 | Latest | Idempotency keys, session cache, rate limiting, pub/sub for WebSocket fan-out |
| **ORM** | SQLAlchemy 2.0 + GeoAlchemy2 | Latest | Async support, PostGIS integration |
| **LLM** | Google Gemini 2.5 | Latest | Multilingual, vision, structured output, generous free tier |
| **Agent Framework** | LangGraph | Latest | Graph-based agent orchestration; supports complex multi-step reasoning |
| **Embeddings** | sentence-transformers or Gemini embeddings | Latest | Lightweight, fast, sufficient for corpus size |
| **Vector Store** | ChromaDB | Latest | Simple, in-process, no infrastructure overhead |
| **WebSockets** | FastAPI WebSocket + Redis Pub/Sub | Built-in | Native FastAPI support; Redis for multi-instance fan-out |
| **Auth** | Firebase Auth + python-jose (JWT) | Latest | Firebase for OAuth/OTP; custom JWT for API access |
| **Containerization** | Docker + Docker Compose | Latest | Reproducible development and deployment |
| **Cloud** | Google Cloud Run | N/A | Serverless containers; auto-scaling; pay-per-use |
| **CI/CD** | GitHub Actions | N/A | Free for public repos; tight GitHub integration |
| **Monitoring** | Prometheus + Grafana | Latest | Industry-standard metrics and dashboards |
| **Error Tracking** | Sentry | Latest | Real-time error tracking with context |
| **API Docs** | Swagger/OpenAPI (auto-generated) | 3.1 | FastAPI generates this automatically |

### 15.2 Architecture Decision Records

**Why FastAPI over Django/Flask?**
FastAPI is async-first (critical for WebSocket and concurrent geo queries), has native Pydantic validation (reduces boilerplate), and auto-generates OpenAPI documentation. Django's ORM does not natively support async geo queries. Flask lacks built-in WebSocket support.

**Why PostgreSQL + PostGIS over MongoDB?**
PostgreSQL + PostGIS provides ACID transactions (critical for SOS event creation), mature geospatial indexing (GiST/SP-GiST), and the ability to use pgvector for the vector store if needed — keeping everything in one database engine. MongoDB's eventual consistency model introduces risk in a safety-critical path.

**Why FCM over raw WebSockets for alerts?**
Android aggressively kills background processes and WebSocket connections. FCM uses Google Play Services to deliver push notifications reliably to backgrounded/killed apps. WebSockets are used only for live coordination *after* the user has foregrounded the app.

**Why ChromaDB over Pinecone/Weaviate?**
The retrieval corpus is small (~500–2000 chunks). ChromaDB runs in-process with zero infrastructure overhead, which is appropriate for a final-year project. Enterprise vector databases add operational complexity without proportional benefit at this scale.

---

## 16. Development Methodology

### 16.1 Approach

**Agile with 2-week sprints**, adapted for a single-developer project:
- Each sprint has defined deliverables aligned with the monthly milestones.
- End-of-sprint self-review against acceptance criteria.
- Git-based version control with feature branches and PR-style self-review.

### 16.2 Development Workflow

```
Feature branch created
         │
         ▼
Development + unit tests
         │
         ▼
Local testing (Docker Compose)
         │
         ▼
Self code review
         │
         ▼
Merge to main
         │
         ▼
CI/CD pipeline runs (GitHub Actions)
  ├── Lint (ruff, mypy)
  ├── Unit tests (pytest)
  ├── Integration tests
  └── Docker build
         │
         ▼
Deploy to staging (Cloud Run)
         │
         ▼
Manual verification
         │
         ▼
Tag release
```

### 16.3 Repository Structure

```
NearHelp/
├── android/                    # Android application (Kotlin)
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── java/com/nearhelp/
│   │   │   │   ├── data/       # Repositories, data sources
│   │   │   │   ├── domain/     # Use cases, models
│   │   │   │   ├── ui/         # Composable screens
│   │   │   │   └── di/         # Dependency injection
│   │   │   └── res/
│   │   └── build.gradle.kts
│   └── build.gradle.kts
│
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/                # Route handlers
│   │   │   ├── auth.py
│   │   │   ├── sos.py
│   │   │   ├── users.py
│   │   │   ├── admin.py
│   │   │   └── websocket.py
│   │   ├── core/               # Configuration, security
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Business logic
│   │   │   ├── geo_service.py
│   │   │   ├── ranking_service.py
│   │   │   ├── notification_service.py
│   │   │   └── event_service.py
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── ai_service/                 # AI microservice
│   ├── app/
│   │   ├── agents/             # LangGraph agent definitions
│   │   ├── rag/                # RAG pipeline
│   │   │   ├── chunker.py
│   │   │   ├── embedder.py
│   │   │   ├── retriever.py
│   │   │   └── generator.py
│   │   ├── classifiers/        # Emergency classification
│   │   ├── knowledge_base/     # Raw protocol documents
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── admin_dashboard/            # Web admin panel
│   ├── src/
│   └── package.json
│
├── simulator/                  # Digital Twin simulator
│   ├── scenarios/
│   ├── locustfile.py
│   └── analysis.py
│
├── docker-compose.yml          # Local development environment
├── .github/workflows/          # CI/CD pipelines
├── docs/                       # Documentation
│   ├── SRS.md
│   ├── SDD.md
│   ├── API.md
│   └── diagrams/
└── README.md
```

---

## 17. Project Timeline & Milestones

### Month 1 — Foundation & De-Risking (Weeks 1–4)

**Goal**: Prove the two hardest pieces end-to-end: real-time alert delivery and AI-guided response.

| Week | Deliverable | Acceptance Criteria |
| --- | --- | --- |
| 1 | Project setup: repo, Docker Compose, PostgreSQL + PostGIS, FastAPI skeleton | `docker-compose up` starts all services; health check endpoint returns 200 |
| 1 | Android project setup: Jetpack Compose, navigation, Firebase integration | App builds and runs on emulator; FCM token registered |
| 2 | Auth module: registration, login (email + Google), JWT | User can register, login, receive JWT, and make authenticated requests |
| 2 | SOS creation endpoint with geospatial query | POST creates SOS, geo query returns nearby users (verified with test data) |
| 3 | FCM integration: SOS → push notification to nearby devices | SOS on Device A triggers push notification on Device B (end-to-end proven) |
| 3 | AI service setup: ChromaDB, embedding pipeline, one crisis type (medical/CPR) | Query "cardiac arrest" returns correct CPR procedure chunks |
| 4 | RAG generation: retrieved chunks → Gemini → structured guidance | Full pipeline: text input → classification → retrieval → generated guidance with citations |
| 4 | Integration: SOS trigger → backend → AI service → guidance delivered to responder | End-to-end demo on two physical devices |

**Month 1 Exit Criteria**: Two Android devices can demonstrate: Device A triggers SOS → Device B receives push notification with AI-generated CPR guidance.

---

### Month 2 — Responder Flow & Real-Time (Weeks 5–8)

**Goal**: Complete the responder experience with live tracking, chat, and event resolution.

| Week | Deliverable | Acceptance Criteria |
| --- | --- | --- |
| 5 | Responder acceptance flow + WebSocket connection | Responder taps "I'm Responding" → WebSocket opens → status updated in real-time |
| 5 | User profile module (Android) | Users can view/edit profile, add skills, upload certificates |
| 6 | Live map (Android): victim + responder locations | Google Maps shows victim marker + responder markers updating in real-time |
| 6 | Live tracking: responder location streaming with ETA | Victim sees responder moving on map with ETA countdown |
| 7 | In-app chat (WebSocket-based) | Text messages delivered in real-time between victim and responders |
| 7 | Emergency timeline auto-generation | All events (created, accepted, arrived, resolved) logged and displayed |
| 8 | SOS resolution flow | Responder/victim can resolve SOS; feedback prompt; trust scores updated |
| 8 | Voice SOS: speech → structured emergency | User speaks into mic → emergency created without typing |

**Month 2 Exit Criteria**: Full SOS lifecycle demonstrated end-to-end: SOS → notification → response → live tracking → chat → resolution → timeline.

---

### Month 3 — AI Intelligence & Trust (Weeks 9–12)

**Goal**: Multi-crisis RAG, responder ranking, skill verification, severity prediction.

| Week | Deliverable | Acceptance Criteria |
| --- | --- | --- |
| 9 | Multi-crisis RAG: all emergency types (fire, gas leak, accident, etc.) | Each crisis type retrieves correct procedures from expanded corpus |
| 9 | AI emergency classification from free text | Free-text input correctly classified to crisis type with >80% accuracy on test set |
| 10 | AI severity prediction | Severity scores generated and validated against test scenarios |
| 10 | Responder ranking algorithm | Ranking verified: skilled responders rank above closer unskilled ones in relevant scenarios |
| 11 | Skill verification workflow (admin + user) | User submits certificate → admin reviews → verified badge appears |
| 11 | AI translation integration | Messages auto-translated between Hindi/Bengali/English |
| 12 | AI Crisis Assistant agent (LangGraph) | Multi-turn agent: classifies → asks follow-up → provides guidance → generates summary |
| 12 | Smart SOS engine: AI-driven responder selection | Different emergencies produce different responder lists (validated with test data) |

**Month 3 Exit Criteria**: AI pipeline handles multiple crisis types, ranks responders intelligently, and provides grounded guidance with citations.

---

### Month 4 — Polish, Evaluation & Defense (Weeks 13–16)

**Goal**: Admin dashboard, load testing, benchmarks, documentation, defense preparation.

| Week | Deliverable | Acceptance Criteria |
| --- | --- | --- |
| 13 | Admin dashboard: live map, user management, skill verification queue | Admin can view active events, manage users, approve/reject skill submissions |
| 13 | Reputation engine: trust score updates, badges | Trust scores change correctly based on test scenarios |
| 14 | Digital Twin simulator: scenario generation + load testing | Simulated 100 concurrent SOS events; measured and documented all latency metrics |
| 14 | Analytics: heatmaps, response time trends, emergency type distribution | Dashboard shows visualized analytics from simulated data |
| 15 | Dockerized deployment to Google Cloud Run | Full system deployed and accessible via public URL |
| 15 | Documentation: SRS, SDD, API docs, UML diagrams | All documents complete and reviewed |
| 16 | Performance evaluation report | Load test results, AI latency benchmarks, geo query benchmarks documented |
| 16 | Defense presentation preparation | Slides, demo script, anticipated Q&A prepared |

**Month 4 Exit Criteria**: Complete system deployed, documented, benchmarked, and ready for defense.

---

## 18. Testing Strategy

### 18.1 Testing Pyramid

| Level | Scope | Tools | Coverage Target |
| --- | --- | --- | --- |
| Unit Tests | Individual functions, models, services | pytest, JUnit/Kotest | 80%+ for backend services |
| Integration Tests | API endpoints, database queries, WebSocket flows | pytest + httpx, TestContainers | All critical paths |
| End-to-End Tests | Full SOS lifecycle (Android → Backend → AI → Android) | Manual + scripted (Appium future) | All user-facing flows |
| Load Tests | Concurrent SOS, geo queries, WebSocket connections | Locust | Benchmark metrics documented |
| AI Evaluation | RAG retrieval quality, classification accuracy | Custom evaluation scripts | Precision/Recall on test set |

### 18.2 AI-Specific Testing

| Test | Metric | Target |
| --- | --- | --- |
| Retrieval precision | % of retrieved chunks that are relevant | > 80% |
| Retrieval recall | % of relevant chunks that are retrieved | > 70% |
| Classification accuracy | % of test inputs correctly classified | > 85% |
| Hallucination rate | % of generated instructions not grounded in sources | < 5% |
| Latency (classification + RAG) | End-to-end AI pipeline time | < 3 seconds |

---

## 19. Research Contributions

This project contributes to the following research areas:

### 19.1 Experimental Questions

| # | Research Question | Experiment Design |
| --- | --- | --- |
| RQ1 | How much faster is AI-based responder selection vs. fixed-radius broadcast? | Compare time-to-first-arrival: ranked dispatch vs. broadcast-all in Digital Twin simulation |
| RQ2 | Does skill-aware matching improve response quality? | Compare responder skill relevance: skill-ranked vs. distance-only ranking |
| RQ3 | What is the latency impact of AI processing? | Measure AI pipeline latency across 100 test queries; compare SOS delivery time with/without AI |
| RQ4 | How does the system scale under concurrent load? | Load test with 10, 50, 100 concurrent SOS events; measure degradation |
| RQ5 | PostGIS vs. MongoDB 2dsphere: which performs better for nearby-user queries? | Benchmark identical queries on both engines with 1K, 10K, 100K users |

### 19.2 Expected Contributions

1. **A working prototype** of an AI-augmented community emergency response system.
2. **Benchmark data** on geospatial query performance for emergency response scenarios.
3. **Evaluation of RAG** for safety-critical real-time guidance delivery.
4. **A responder ranking algorithm** with documented behavior across test scenarios.
5. **Load testing results** demonstrating system capacity and bottlenecks.

---

## 20. Deliverables

| # | Deliverable | Format |
| --- | --- | --- |
| D1 | Native Android Application | APK + source code |
| D2 | FastAPI Backend API | Dockerized, deployed to Cloud Run |
| D3 | AI Service (RAG + Agent) | Dockerized, deployed to Cloud Run |
| D4 | Admin Dashboard | Web application (React/Next.js) |
| D5 | Digital Twin Simulator | Python scripts + Locust configuration |
| D6 | Knowledge Base | Curated, chunked, embedded protocol corpus |
| D7 | Docker Compose Setup | Full local development environment |
| D8 | CI/CD Pipeline | GitHub Actions workflows |
| D9 | Software Requirements Specification (SRS) | Markdown document |
| D10 | Software Design Document (SDD) | Markdown document with UML diagrams |
| D11 | API Documentation | Auto-generated Swagger/OpenAPI |
| D12 | Performance Evaluation Report | Benchmark results with analysis |
| D13 | Project Report | Complete academic report |
| D14 | Defense Presentation | Slides + demo script |

---

## 21. Risk Analysis & Mitigation

### 21.1 Risk Register

| Risk | Probability | Impact | Strategic Solution | Implementation |
| --- | --- | --- | --- | --- |
| **Scope Overload** (24 modules for one developer) | High | High | **3-Phase MoSCoW Model** | Build MVP (Modules 1–11) first; mark complex features as Phase 2/3. No phase advances until prior phase is stable. See §8 MoSCoW Prioritisation. |
| **No Volunteers Nearby** | Medium | Critical | **3-Layer Escalation** | Auto-radius expansion (30s/45s/60s gates) → direct 108/112 dial → Guided Self-Care AI fallback. See Module 6. |
| **Medical Liability** | Medium | Critical | **Good Samaritan Law + Strict RAG Guardrails** | Legal disclaimer in UI (non-dismissible) + strict RAG prompt constraints (no dosage, no diagnosis, no prescriptions). See §13.4. |
| **Viva/Defense Weakness** | Medium | High | **Digital Twin Simulation** | Generate real latency/response-time comparison charts during demo. 5 chart types covering all research questions. See Module 23. |
| AI hallucination in medical advice | Medium | Critical | RAG grounding + scope guardrails | Citation enforcement, confidence thresholds (< 0.6 = fallback), strict scope prohibition, fallback to "call emergency services". See §9.4. |
| FCM delivery failures | Low | High | Multi-channel delivery | Delivery receipt tracking, retry with exponential backoff, SMS fallback (Module 22). |
| Geospatial query performance degradation | Low | Medium | Early benchmarking | PostGIS GiST indexing, load testing in Month 1, query optimization. Benchmark results in defense charts. |
| API rate limits (Gemini, Google Maps) | Medium | Medium | Defensive caching | Caching, request batching, fallback to cached responses. |
| Single developer bottleneck | High | High | Strict phase discipline | MoSCoW phases enforce focus; weekly self-review; core over polish. |
| Data privacy regulatory compliance | Low | Medium | Privacy-by-design | Anonymous mode, AES-256 encryption at rest, data minimization, GDPR-aligned data retention. |

### 21.2 Strategic Risk Deep-Dives

#### Strategy 1: 3-Phase MoSCoW Model (Scope Control)

| Phase | Modules | Timeline | Exit Criteria |
| --- | --- | --- | --- |
| **Phase 1 — MVP** (Must Have) | 1–11: Auth, Profile, Skills, Emergency Detection, Severity, Smart SOS, Live Map, Live Tracking, Navigation, Crisis Assistant, RAG KB | Months 1–3 | Full SOS lifecycle works end-to-end on two devices with AI guidance |
| **Phase 2 — Enhancement** (Should Have) | 12–17: Translation, Voice SOS, Timeline, Incident Report, Reputation, Community Layer | Month 3–4 | Features integrated and tested against Phase 1 acceptance criteria |
| **Phase 3 — Stretch** (Could Have) | 18–24: Admin Dashboard, AI Analytics, Disaster Mode, Guardian Mode, Offline Mode, Digital Twin, Developer Dashboard | Month 4 (if time permits) | Features functional; load tested where applicable |

#### Strategy 2: 3-Layer Escalation (No Volunteer Nearby)

```
Time ──────────────────────────────────────────────────────────────►

0s          30s           45s           60s           ongoing
│           │             │             │             │
▼           ▼             ▼             ▼             ▼
┌─────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌──────────┐
│ Layer 1a│ │ Layer 1b  │ │ Layer 1c  │ │ Layer 2   │ │ Layer 3  │
│ Initial │ │ 2× radius │ │ 3× radius │ │ Auto-dial │ │ Self-Care│
│ radius  │ │ expansion │ │ expansion │ │ 108/112   │ │ AI Guide │
└─────────┘ └───────────┘ └───────────┘ └───────────┘ └──────────┘
```

**Guarantee**: The victim is *never* left without assistance. Even in the worst case (no volunteers, no network), the AI Crisis Assistant provides cached, offline self-care guidance.

#### Strategy 3: Medical Liability Safeguards

- **Legal protection**: India's Good Samaritan Law (2016) + MoRTH Guidelines (2015) protect bystanders acting in good faith.
- **UI enforcement**: Non-dismissible disclaimer on all AI guidance screens.
- **Technical enforcement**: 7 RAG guardrail rules (see §13.4) ensure the system never exceeds first-aid protocol scope.
- **Audit trail**: Every AI-generated instruction is logged with source citations for post-incident review.

#### Strategy 4: Digital Twin Defense Preparation

- **5 comparison charts** auto-generated from simulation data (see Module 23).
- **Empirical answers** to all 5 research questions (RQ1–RQ5).
- **Live demo capability**: Simulator can run during the viva to generate real-time results.
- **Benchmark reproducibility**: All simulation parameters are configurable and documented.

---

## 22. Future Scope

The following features are explicitly deferred to maintain focus, but represent natural extensions:

1. **iOS Application**: Cross-platform with Kotlin Multiplatform or separate Swift implementation.
2. **WebRTC Voice/Video**: Direct voice/video calls between victim and responder.
3. **Wearable Integration**: Apple Watch / WearOS for fall detection and auto-SOS.
4. **Government API Integration**: Direct integration with 112/108 dispatch systems.
5. **ML-based Fraud Detection**: Pattern recognition for false emergency detection.
6. **Predictive Analytics**: Predict emergency hotspots based on historical data, weather, and events.
7. **Multi-language Voice SOS**: Support for regional Indian languages beyond Hindi/Bengali/English.
8. **Ambulance Fleet Integration**: Real-time ambulance tracking and coordination.

---

## 23. References

1. World Health Organization. (2023). *International First Aid and Resuscitation Guidelines*. WHO Press.
2. Indian Red Cross Society. (2022). *First Aid Manual*. IRCS Publications.
3. National Disaster Management Authority. (2019). *National Disaster Management Guidelines*. Government of India.
4. American Heart Association. (2020). *CPR & ECC Guidelines*. AHA.
5. Lewis, M. et al. (2023). "Large Language Models for Emergency Triage Assessment." *Journal of Medical Internet Research*.
6. Xiong, W. et al. (2024). "Retrieval-Augmented Generation for Medical Question Answering." *ACL 2024*.
7. PulsePoint Foundation. (2023). *PulsePoint Respond: Citizen CPR Notification*. pulsepoint.org.
8. GoodSAM. (2023). *Instant Help. Anywhere. Anytime.* goodsamapp.org.
9. PostGIS Development Team. (2024). *PostGIS 3.4 Documentation*. postgis.net.
10. Google. (2024). *Firebase Cloud Messaging Documentation*. firebase.google.com.
11. Google. (2024). *Gemini API Documentation*. ai.google.dev.
12. LangChain. (2024). *LangGraph Documentation*. langchain.com.
13. FastAPI. (2024). *FastAPI Documentation*. fastapi.tiangolo.com.
14. Locust. (2024). *Locust Load Testing Documentation*. locust.io.

---

*This document is a living specification and will be updated as the project progresses.*
