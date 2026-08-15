# NearHelp AI — App Design Document

> **Reference:** the shared image defines our design language: a *calm-by-default, loud-when-it-matters* safety app. Screen 1 (mint dashboard, glass cards, central hold-for-SOS button) and Screen 2 (emergency category grid, address confirm, countdown SOS bar) are the north star. This document translates that language into NearHelp's full screen set and gives the build order.
>
> Platform: **Android, Kotlin + Jetpack Compose (Material 3)**. One design system, two experiences: the **Citizen flow** (triggering and tracking help) and the **Responder flow** (receiving and acting on alerts).

---

## 1. Design Language

**Four principles, in priority order:**

1. **Calm by default, loud in emergency.** Normal state = soft mint, generous whitespace, quiet grayscale text. Active SOS = the screen physically changes (red tint, pulsing, full-bleed urgency). A user should feel the state change in their peripheral vision.
2. **One giant action per screen.** The SOS control is the largest element on the home screen (as in the reference's central mic circle). Nothing competes with it.
3. **Glass, not chrome.** Translucent white surfaces (`white @ 80–90%` opacity) floating over a tinted gradient background, 8–24dp radii, 2–4dp soft shadows. No hard borders anywhere.
4. **Color = meaning, never decoration.** Green means safe/positive, red means emergency, and every emergency category keeps its own hue (fire = orange, medical = blue…) everywhere it appears — grid, chip, marker, notification.

**Gestalt:** minimal flat icons (20–24dp, no gradients/3D), rounded sans-serif type with bold-only-for-primary hierarchy, and a 4dp spacing grid.

### 1.1 Mapping the reference to NearHelp

| Reference element | NearHelp adaptation |
| --- | --- |
| "China Basin" + "Safety Index 91%" header | Locality name + **"N verified responders nearby · avg 3 min"** live stat |
| Search bar with mic ("Where are you going today?") | Kept as-is on Home; mic launches Voice SOS (Phase 2 feature) |
| Central circular mic button + "HOLD FOR SOS" | **The core SOS control** — hold 3s with progress ring (also our false-alarm guard) |
| "CHECK IN" chevron expander | Expands to quick actions: "I'm safe" check-in, emergency contacts, resources nearby |
| Coordinates footer | Kept — live GPS readout adds credibility and matches the safety-tool aesthetic |
| 4 quick circles (Community / Sharing / Message / Alert) | Become: **Respond · Map · Chat · Profile** quick nav on relevant screens |
| Address card + "Confirm Address" | SOS confirmation step: reverse-geocoded location + editable description before send |
| 4×4 category grid with one highlighted | Crisis-type selector — trimmed to NearHelp's types (see §4.3) |
| Green ✕ Cancel / red "3" countdown / red Send SOS | Exact pattern reused for the **5-second cancel window** and send action |

---

## 2. Design Tokens (source of truth = `ui/theme/`)

### 2.1 Color

```kotlin
// Backgrounds
val BgCalm      = Color(0xFFE6F7EF)   // mint — normal state
val BgCalmDeep  = Color(0xFFCDEFDD)   // gradient top
val BgNeutral   = Color(0xFFF0F0F0)   // panels/forms
val BgIncident  = Color(0xFFFDECEA)   // red-tinted — active SOS victim screen
val BgRespond   = Color(0xFFE8F0FE)   // blue-tinted — responder active screen

// Brand / semantic
val Green       = Color(0xFF4CAF50)   // safe, positive, arrival
val GreenDeep   = Color(0xFF2E7D32)   // green text (contrast-safe)
val Red         = Color(0xFFF44336)   // emergency accents, SOS button
val RedDeep     = Color(0xFFD32F2F)   // red text / small labels (contrast-safe)
val Blue        = Color(0xFF2196F3)   // medical, responder identity

// Category hues (consistent app-wide)
val CatMedical  = Blue
val CatFire     = Color(0xFFFF9800)   // orange
val CatGas      = Color(0xFFFF9800)
val CatAccident = Blue
val CatPolice   = Color(0xFF3F51B5)   // indigo (security threat)
val CatDisaster = Color(0xFF795548)   // brown (flood/quake collapsed to one)
val CatPower    = Color(0xFFFFC107)   // amber
val CatOther    = Color(0xFF9E9E9E)   // gray

// Surfaces & text
val Surface     = Color(0xCCFFFFFF)   // white @ 80% — glass cards
val SurfaceHi   = Color(0xE6FFFFFF)   // white @ 90% — inputs, address card
val Text1       = Color(0xFF111111)
val Text2       = Color(0xFF6B6B6B)
val Text3       = Color(0xFF9A9A9A)   // coordinates, timestamps
```

Contrast rule: `Red`/`Green` are for fills and icons only; **text always uses the `-Deep` variants** (WCAG AA on white/mint).

### 2.2 Type — Inter (fallback Roboto)

| Style | Spec | Used for |
| --- | --- | --- |
| `display` | 28sp / Bold | Home locality, "EMERGENCY ACTIVE" |
| `title` | 24sp / Bold | Screen 1 reference title, section heads |
| `label` | 16sp / Bold | HOLD FOR SOS, Confirm Address |
| `body` | 14sp / Regular | Buttons, card body, chat |
| `caption` | 12sp / Regular | Category labels, secondary lines |
| `micro` | 10sp / Regular | Coordinates, disclaimers |

### 2.3 Shape, space, elevation

- Radii: **8dp** (small buttons, grid tiles) · **12dp** (cards, inputs) · **16dp** (sheets) · **24dp** (large buttons) · **50%** (circles).
- Spacing: 4dp base grid; screen padding 20dp; card padding 16dp; grid gap 8dp.
- Shadows: 2–4dp blur equivalent → Compose `tonalElevation` + faint `ambientShadow`, never harsh drop shadows.
- Glass recipe: `Surface` color at 80–90% alpha, 12dp radius, subtle shadow; on API 31+ optionally add `Modifier.blur()` on the layer *behind* the card — blur is polish, not identity, since cheap devices and battery matter here.

---

## 3. Component Library (build these before any screen)

| Component | Spec |
| --- | --- |
| **GlassCard** | `SurfaceHi` bg, 12dp radius, 16dp padding. The universal container. |
| **SosHoldButton** | 96dp circle, white glass ring + category-colored core (mic icon default). Hold fills a progress arc over 3s (sweep animation) → haptic tick at 50%, success haptic + scale-bounce at 100%. Release early = gentle shake + toast "Hold for 3 seconds". |
| **CategoryTile** | 60×60dp white tile, 8dp radius, flat category icon + 12sp label below; selected state = filled with category color, white icon/text (exactly like the reference's highlighted "Robbery"). |
| **CategoryChip** | Pill version of the tile for map legend, chat headers, guidance cards. |
| **CountdownBar** | Bottom bar: green ✕ Cancel \| red circle with live countdown number \| red "Send SOS →". Drives the 5-second cancel window. |
| **StatPill** | Small glass pill with icon + "12 responders · 3 min" style live stats. |
| **TimelineRow** | icon-dot + connecting line, `event_type`, actor, relative time — used in incident timeline and AI guidance steps. |
| **GuidanceCard** | Glass card: numbered step (bold), source citation in `caption` gray ("WHO First Aid — CPR, Step 3"), confidence dot. Non-dismissible disclaimer strip docked below. |
| **ChatBubble** | Sender-left (glass) / self-right (category-tinted 20% alpha); translated text shown in `caption` under the original when languages differ. |
| **QuickNavRow** | The reference's 4 circles: 40dp white circles, icon + 12sp label under each. Contextual per screen. |
| **MapPin (custom)** | Circular category-colored markers (victim = red pulse, verified responder = blue with ✓ badge, hospital = white cross on green). |
| **MapStyle** | Google Map styled: desaturated/whited-down base so mint UI and colored markers pop; dark variant for dark theme. |

---

## 4. Screen Specs (Citizen flow)

### 4.1 Home — *"Calm dashboard"* (reference Screen 1)

```
┌──────────────────────────────────────┐
│ 11:30                    ▂ ▄ ⚡ 87%  │  status bar
│  ( ◀ )                  slide to exit│  glass header (map-preview mode only)
│                                      │
│            Salt Lake                 │  display/bold, centered
│     14 responders · avg 3 min        │  caption, live stat
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ 🔍  Where are you going today? 🎙│ │  glass search (mic = voice SOS, P2)
│ └──────────────────────────────────┘ │
│                                      │
│              ╭─────╮                 │
│              │  ◉  │                 │  SosHoldButton, 96dp+
│              ╰─────╯                 │
│            HOLD FOR SOS              │  label/bold
│            CHECK IN ⌄                │  caption → expands contacts/safe-check
│                                      │
│      22.5726° N  88.3639° E          │  micro, live GPS
└──────────────────────────────────────┘
```

Background: mint gradient (deep top → light bottom). The center circle can sit over a faint radar/coverage ring showing responder radius — the reference's green overlay circle.

### 4.2 Crisis Select — *"Emergency panel"* (reference Screen 2)

Full-screen sheet, `BgNeutral`. Top: QuickNavRow (Respond · Map · Chat · Profile). Address glass card (pin icon, reverse-geocoded address, edit) + **Confirm Location** (Red, 24dp radius). Category grid 3×3: **Medical · Fire · Gas Leak · Accident · Security · Disaster · Power · Water/Flood · Other** — one tile highlighted at a time; selection arms the SOS. Bottom: CountdownBar — green ✕ dismisses, red countdown circle (5s) with Send SOS → fires `POST /api/sos/create` (idempotency key). Optional one-line description input above the bar (what AI classifies from; preselecting a tile just seeds it).

### 4.3 Incident Active — victim view, `BgIncident` background

Top: "EMERGENCY ACTIVE" + category chip + elapsed timer. Middle: live map — victim pin pulsing, accepted responders as blue pins streaming, ETA pill per responder. Bottom: collapsing card with tabs **Guidance | Responders | Chat**:
- **Guidance:** GuidanceCards with citations + the non-dismissible disclaimer strip.
- **Responders:** TimelineRows per responder (notified → accepted → arrived) + trust/skill badges.
- **Chat:** ChatBubbles + input.
Docked actions: **Call 108/112** (appears at escalation, pre-filled summary note) and **Resolve**.

### 4.4 Resolved / Feedback
Calm mint returns. Summary card (timeline condensed, "first responder in 2m 30s"), feedback stars for responders, trust-note explainer. This closure moment is what makes the loop feel trustworthy.

### 4.5 Auth screens
`BgNeutral`, single GlassCard per screen (Email/Password → Register → OTP-lite), full-width 24dp-radius buttons, Red primary CTA. No decoration — speed to Home matters.

### 4.6 Profile
Skills list as CategoryChips with verified ✓ / pending ⏳ states, certificate upload, trust score shown as a subtle progress arc (not a gamified badge wall). Readiness indicator (notifications / battery / location permissions) as a three-icon status row — turns the invisible reliability problem visible.

---

## 5. Screen Specs (Responder flow) — same system, blue accent

| Screen | Spec |
| --- | --- |
| **Alert (from FCM)** | Full-bleed `BgRespond`: category icon large, "Medical emergency · 400 m away · severity 92", mini-map preview, two actions — **Respond** (Blue, hold-to-confirm 1.5s) / **Dismiss** (glass). Countdown auto-dismiss 20s so stale alerts don't haunt the notification tray. |
| **En route** | Map with route line + victim pin, ETA pill, distance; GuidanceCards docked (the RAG output — this is where the AI visibly earns its keep); "I've arrived" button → GPS-confirmed check-in. |
| **On scene** | Action log (quick buttons: "Started CPR", "Called 108" → timeline events), chat, resolve assist. |

---

## 6. Interaction & Motion Spec

| Interaction | Behavior |
| --- | --- |
| **Hold-for-SOS (3s)** | Sweep-arc progress on the ring, haptic at 50%, success haptic + scale-bounce (spring `stiffness = Medium`) at fire. |
| **5s cancel window** | CountdownBar after send: red circle counts 5→0; ✕ cancels with "SOS cancelled" snackbar; at 0 the event is committed and screen transitions to Incident Active with a red wash fade. |
| **State transition** | Calm→Incident: 300ms crossfade of background tint + status bar color. Incident→Resolved: reverse, with a calming green confirmation. |
| **Live markers** | Compose `animateFloatAsState` on lat/lng (300ms) so movement is smooth at 3s updates; victim pin pulses (alpha 0.4→1, 1.2s loop) while status = active. |
| **Escalation cue** | At 30/45/60s gates: brief edge glow + "Expanding search to 2× radius" caption — visible system behavior builds trust. |
| **Empty/error** | Skeleton glass cards, never spinners on the SOS path; offline banner chip when network lost + "cached guidance available" note. |
| **Haptics everywhere** | Every commit/cancel/state change has one haptic event. In emergencies, touch confirmation must not rely on vision. |

**Dark theme:** same hues, `Bg` variants darkened (mint→`#0E1F16`, incident→`#2A0F0D`), surfaces `#1E1E1E @ 88%`. Ship in Phase 4 — night-time emergencies are real.

**Accessibility:** all touch targets ≥ 48dp (CategoryTiles get invisible 8dp padding); TalkBack labels on every icon-button ("Hold for three seconds to send emergency alert"); `RedDeep/GreenDeep` for text; respect font scaling to 1.3× (test GuidanceCard and grid at 1.3× before sign-off); SOS flow usable one-handed.

---

## 7. Compose Implementation Notes

- Single `NearHelpTheme` (M3) exporting the tokens in §2; no raw hex values inside screens — ever. One `colors.kt`, one `Type.kt`, one `Shapes.kt`.
- `GlassCard(modifier, content)` = one reusable composable wrapping `Surface` + elevation; blur is a parameter defaulting off.
- Map: `google-maps-android-compose` library; custom marker renderer per §3; styled map JSON committed in `res/raw/`.
- Hold gesture: `pointerInput { detectTapGestures + press-time tracking }` driving an `Animatable` arc — encapsulated inside `SosHoldButton(onSosFired)`.
- State-driven backgrounds: a top-level `UiState` (CALM / INCIDENT / RESPOND) sets the scaffold's background gradient — the "loud mode" is one flag, not per-screen styling.
- Screen structure mirrors `android/.../ui/screens/{home, crisis_select, incident, responder, chat, auth, profile}` with shared `components/` from §3.

---

## 8. Design Roadmap (aligned to BLUEPRINT.md phases)

### Phase D0 — Tokens & primitives (Week 1, alongside project setup)
- [ ] `colors.kt` / `Type.kt` / `Shapes.kt` with §2 values (P0)
- [ ] `GlassCard`, `StatPill`, `QuickNavRow`, `CategoryTile`, `CategoryChip` (P0)
- [ ] Mint gradient scaffold + status-bar styling (P0)

### Phase D1 — Static citizen screens (Week 2–3)
- [ ] Home dashboard layout, live-GPS footer, CHECK-IN expander (P0)
- [ ] Auth screens (P0)
- [ ] Crisis Select sheet: address card, category grid, CountdownBar *with local state only* (P0)
- [ ] Profile (basic) + readiness status row (P1)

### Phase D2 — The SOS interaction (Week 3–4)
- [ ] `SosHoldButton` with arc + haptics (P0)
- [ ] 5s cancel window wired to real API (idempotent create/cancel) (P0)
- [ ] Calm→Incident background transition + elapsed timer (P0)
- [ ] FCM deep-link → Alert screen (P0)

### Phase D3 — Live incident & responder screens (Week 5–8, with backend WebSockets)
- [ ] Incident Active: map + responder pins + ETA pills (P0)
- [ ] GuidanceCard + disclaimer strip + tabs (P0)
- [ ] Chat bubbles; translated caption (P1)
- [ ] TimelineRows; escalation cues ("expanding radius") (P1)
- [ ] Responder Alert / En route / On scene (P0 for alert+en-route)
- [ ] Custom map style + marker set (P1)

### Phase D4 — Polish & armor (Week 9+)
- [ ] Dark theme pass (P1)
- [ ] Accessibility pass: TalkBack, 1.3× font, contrast audit (P1)
- [ ] Resolved/feedback screen (P1)
- [ ] Micro-interactions: marker animation, empty states, skeletons (P2)
- [ ] Fake-GPS demo mode toggle in dev settings (P0 for the demo — moving pins sell live tracking)
- [ ] Record the UI walkthrough video for the defense backup (P0)

**Definition of "design demo-ready":** a person who has never seen the app can pick up the phone, hold the SOS button, pick a category, watch the cancel countdown commit, see responders converge on the map, and follow one cited guidance card — without a single word of instruction. That is the bar for every phase exit.

---

## 9. Guardrails (what this design deliberately avoids)

- No bottom-nav tab bar — the app is a flow, not a feed; navigation is contextual (QuickNavRow + back). Deep apps-within-apps are how emergency UIs die.
- No dark patterns on urgency: "Send SOS" is never upsold, animated bait, or blocked behind confirmations beyond the one countdown.
- No gamification of emergencies (no streaks, no leaderboards on the citizen side; trust score stays subtle).
- No glassmorphism *on* the map itself — overlays stay outside map padding so markers remain readable in sunlight.
- No red anywhere in the calm state. Red must always mean one thing.
