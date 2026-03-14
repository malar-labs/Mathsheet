# MathSheet Pro — Technical Improvement Notes

> This document covers all technical decisions made during development:
> what was improved, why it was done, what was skipped and why,
> and what can be done in the future.

---

## 1. Token Limit Optimisation

### What is a Token?
A token is roughly ¾ of a word. LLMs charge and rate-limit by token count.
- 100 words ≈ 130–150 tokens
- Every API call has **input tokens** (prompt) + **output tokens** (response)

### The Problem
Groq free tier allows **~6,000 Tokens Per Minute (TPM)**.
Groq counts `max_tokens` (the ceiling you set) against your quota — not actual usage.

| Component | Tokens |
|---|---|
| System prompt | ~650 |
| User prompt | ~500 |
| `max_tokens` (hardcoded) | 8,192 |
| **Total charged to TPM** | **~8,192** |

A single request consumed more than the entire per-minute quota. A second request
within the same minute was guaranteed to fail with a 429 error.

### What Was Improved ✅
- **Dynamic `max_tokens`** calculated from question count:
  ```
  max_tokens = min(4000, max(1200, num_questions × 220 + 400))
  ```
  | Questions | Before | After | Saved |
  |---|---|---|---|
  | 5  | 8,192 | 1,500 | 6,692 |
  | 10 | 8,192 | 2,600 | 5,592 |
  | 20 | 8,192 | 4,000 | 4,192 |

- **Trimmed user prompt** — removed redundant TOPIC-SPECIFIC NOTES section
  (~150 tokens saved per request)

### Why It Matters
With dynamic tokens, 2–3 users can now generate worksheets simultaneously
without hitting the rate limit, compared to 1 user before.

---

## 2. Response Caching

### The Problem
Every worksheet generation hits the Groq API, consuming TPM quota even if the
same grade/topic/difficulty combination was requested recently.

### What Was NOT Implemented ❌
Caching was discussed but not implemented for a key reason:
**the core value of the app is unique, AI-generated worksheets**.
Teachers and students expect fresh questions every time — serving the same
cached worksheet defeats the purpose.

### What Could Be Implemented 🔮
Three viable approaches for the future:

**Option A — In-Memory TTL Cache (simplest)**
Cache based on a hash of `(grade, topics, difficulty, problem_type, num_questions)`.
Exclude `student_name` and `custom_prompt` from the key (those make it unique).
TTL of 1 hour. No extra dependencies. Cache lost on server restart.

**Option B — Pre-Generated Worksheet Pool (best for TPM)**
Generate 3–5 worksheets per popular grade/topic combo at startup or during quiet
periods. Serve randomly from the pool. Replenish in the background when pool drops
below threshold. Zero latency for users, zero TPM pressure during peak.

**Option C — Redis (production-grade)**
Distributed cache that survives server restarts. Shared across multiple server
instances. Render free tier does not include Redis — requires a paid add-on (~$10/month).
Worthwhile only when you have significant traffic.

**Groq Prompt Caching (already active, free)**
Groq automatically caches repeated system prompts on their servers. Since
`build_system_prompt(grade)` is identical for all requests of the same grade,
Groq reuses the cached tokens. This saves ~650 input tokens per request automatically
with no code changes required.

---

## 3. LLM Provider: Gemini vs Groq vs OpenRouter

### Why Gemini Was Rejected ❌
Google's Gemini API (both old `google-generativeai` and new `google-genai` SDK)
requires linking a **Google Cloud project**, which involves billing setup and
project configuration. This was too complex for a free-tier prototype aimed at
quick sharing with friends.

### Why Groq Was Chosen ✅
- Completely free tier, no credit card required
- No Google Cloud project needed
- Fastest inference speed (custom LPU hardware)
- Simple Python SDK (`groq` package)
- Runs `llama-3.3-70b-versatile` — high quality output

### What Is OpenRouter ✅ (Implemented as Fallback)
OpenRouter is an API aggregator giving access to 100+ LLMs through a single
OpenAI-compatible endpoint. It was added as an **automatic fallback** when Groq
hits its 429 rate limit.

**Flow:**
```
User clicks Generate
        ↓
Try Groq (fast, free)
        ↓
  429 rate limit? ──Yes──► Try OpenRouter (meta-llama/llama-3.3-70b-instruct:free)
        │
        No
        ↓
  Return worksheet
```

**Benefit:** Eliminates the 429 error for users. Two free providers = double the
capacity with no extra cost.

**Setup required:** Add `OPENROUTER_API_KEY` to `.env` and Render environment variables.
Get a free key at openrouter.ai — no credit card needed.

### Future LLM Options 🔮
| Model | Provider | Cost | Quality | Best For |
|---|---|---|---|---|
| `llama-3.3-70b-versatile` | Groq | Free | High | Primary (current) |
| `llama-3.3-70b-instruct:free` | OpenRouter | Free | High | Fallback (current) |
| `gemini-flash-1.5` | OpenRouter | ~$0.001/req | Very High | Premium tier |
| `claude-3-haiku` | OpenRouter | ~$0.002/req | Excellent | Best quality |
| `gpt-4o-mini` | OpenRouter | ~$0.001/req | High | Alternative |

---

## 4. HTTP Connection Reuse (Keep-Alive)

### What Is It?
HTTP Keep-Alive (persistent connections) reuses the same TCP connection for
multiple requests instead of opening and closing a new connection each time.

```
WITHOUT Keep-Alive:
Browser → open → request → response → close
Browser → open → request → response → close  (wasteful)

WITH Keep-Alive:
Browser → open → request → response
               → request → response
               → request → response → close  (efficient)
```

### Why It Was NOT Explicitly Implemented ❌
It doesn't need to be. All layers handle this automatically:

| Layer | Who Handles It |
|---|---|
| Browser → Render | Browser does HTTP/1.1 Keep-Alive automatically |
| Render → Groq | `groq` Python SDK uses `httpx` which reuses connections |
| Render → OpenRouter | `openai` Python SDK uses `httpx` which reuses connections |
| FastAPI / Uvicorn | Built-in Keep-Alive on all connections |

HTTP/1.1 made Keep-Alive the default since 1997. No code needed.

**Note:** Keep-Alive (reuse) and Reconnection (recover after failure) are different:
- Keep-Alive = performance, normal operation
- Reconnection = reliability, after failure

Both are handled — Keep-Alive automatically, Reconnection via our retry/fallback logic.

---

## 5. UI Framework: React or Angular

### The Question
Should the frontend be migrated from Vanilla JS to React or Angular?

### Why It Was NOT Done ❌
The current app has:
- **3 screens** — Topics → Options → Worksheet
- **Simple state** — a single `state` object in JS
- **One API call** — generate worksheet, render result
- **No real-time updates** or complex component trees

Adding React or Angular would introduce:
- npm, webpack/vite build step
- node_modules (~200MB)
- Deployment complexity on Render
- Significant rewrite time
- Zero user-facing benefit

The current bottleneck is **Groq API response time**, not the frontend architecture.

### When React/Angular WOULD Be Worth It 🔮
| If You Add... | Then Consider... |
|---|---|
| User accounts with saved worksheet history | React + proper backend |
| Teacher dashboard with class management | React or Angular |
| Real-time collaboration / live editing | React + WebSockets |
| Mobile app version | React Native |
| 10+ developers on the frontend | React (component reuse, tooling) |
| Complex filtered/searchable worksheet library | React (state management) |

**Recommendation:** Invest time in features first (saved worksheets, teacher dashboard,
progress tracking) — those are what users will notice. Migrate to React only when
the app's complexity genuinely requires it.

---

## 6. Network Timeout & Reconnection

### The Problem (India User)
A user in India reported "network error" when generating worksheets. The cause:
- Render servers are in the US
- Groq API adds another round trip
- High latency for India users (200–300ms extra each way)
- Groq can take 15–30 seconds for long worksheets
- **The fetch call had no timeout** — browsers eventually killed the connection silently

### What Was Improved ✅

**Client-side (browser):** Added `AbortController` with 2-minute timeout:
```javascript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 120000);
fetch('/api/generate', { signal: controller.signal, ... })
```
Shows a clear "Request timed out — try again" message instead of generic "Network error".

**Server-side (Groq call):** Added explicit 90-second timeout:
```python
response = groq_client.chat.completions.create(timeout=90, ...)
```
Fails cleanly instead of hanging indefinitely.

---

## 7. Summary Table

| Improvement | Status | Reason |
|---|---|---|
| Dynamic `max_tokens` | ✅ Done | Fixes 429 rate limit for all users |
| Trim user prompt | ✅ Done | Saves ~150 tokens per request |
| OpenRouter fallback | ✅ Done | Eliminates 429 errors automatically |
| Network timeout (client) | ✅ Done | Fixes India user "network error" |
| Network timeout (server) | ✅ Done | Prevents hanging requests |
| HTTP Keep-Alive | ✅ Auto | Handled by frameworks, no code needed |
| Response caching | ❌ Skipped | Conflicts with "unique worksheets" value prop |
| Gemini as LLM | ❌ Rejected | Requires Google Cloud project setup |
| React / Angular | ❌ Skipped | Overkill for current app complexity |
| Redis cache | ❌ Skipped | Requires paid Render add-on |
| Pre-generated pool | 🔮 Future | Good for high traffic, adds complexity |
| Teacher dashboard | 🔮 Future | High user value, needs auth + database |
| Saved worksheets | 🔮 Future | Needs database (PostgreSQL / SQLite) |
| User accounts (real auth) | 🔮 Future | OAuth or email/password + database |
| Mobile app | 🔮 Future | React Native when web is stable |
| Paid LLM tier (Claude/GPT) | 🔮 Future | Better quality if monetised |
| Rate limiting per IP | 🔮 Future | Prevents abuse on public deployment |

---

## 8. Recommended Next Steps (Priority Order)

1. **Add `OPENROUTER_API_KEY` to Render** — immediate fix for 429 errors in production
2. **In-memory TTL cache** — low effort, meaningful TPM reduction for repeated requests
3. **Rate limiting per IP** — prevents one user from exhausting TPM quota for everyone
4. **Database + saved worksheets** — highest user value, enables teacher workflow
5. **Teacher dashboard** — class management, assign worksheets, track progress
6. **Real auth (Google OAuth)** — replace the current name-only login

---

*Last updated: March 2026*
