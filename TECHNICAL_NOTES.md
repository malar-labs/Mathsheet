# MathSheet Pro — Technical Notes

---

## ✅ Implemented

### Token Optimisation (Round 1)
**Problem:** Groq free tier = 6,000 TPM. Hardcoded `max_tokens=8192` burned the entire quota per request.
**Fix:** Dynamic `max_tokens = min(4000, num_questions × 220 + 400)`. Also trimmed user prompt by ~150 tokens.
**Result:** 10 questions now uses ~2,600 tokens instead of 8,192.

### Token Optimisation (Round 2)
**Problem:** ~2,600 tokens per 10-question request still only allowed ~2.3 requests/minute within 6,000 TPM.
**Fix:**
- Trimmed system prompt in `curriculum.py` (~140 tokens): removed verbose role padding, preserved scope restriction and accuracy rules
- Trimmed user prompt in `app.py` (~50 tokens): removed requirements already enforced by system prompt
- Lowered `max_tokens` formula: `min(4000, max(1200, n×220+400))` → `min(4000, max(800, n×200+300))`
**Result:** 10-question request drops from ~2,600 to ~2,150 tokens. ~2.7 requests/minute instead of ~2.3.

### Custom Prompt Difficulty Drift
**Problem:** When a teacher adds a custom instruction (e.g. "skip division"), the LLM compensated by escalating number complexity beyond the curriculum spec (e.g. 3-digit × 3-digit multiplication for Grade 4 instead of 2-3 digit × 1 digit). This happened because the custom instruction repositioned the LLM's attention, causing earlier curriculum difficulty constraints to fade.
**Fix:** Added a guardrail *after* the custom instruction block in the user prompt:
```
NOTE: Teacher instructions modify topic/type selection only. Curriculum difficulty and number ranges for this grade still apply.
```
**Key principle:** In LLMs, later instructions tend to override earlier ones. Guardrails must come *after* the instruction that might break them, not before.
**Result:** Custom prompts now correctly modify problem type selection without affecting difficulty or number ranges.

### OpenRouter Fallback
**Problem:** Single LLM provider = single point of failure on 429 rate limit.
**Fix:** Groq fails with 429 → automatically retries with OpenRouter (`llama-3.3-70b-instruct:free`).
**Result:** Users never see a rate limit error during normal usage.
**Caveat:** OpenRouter free tier has daily limits (~200 req/day). Exhausted during testing. Resets daily. Not suitable as primary — fallback only.

### Network Timeout
**Problem:** User got "Network error" — browser silently killed slow connections.
**Fix:** `AbortController` (2 min) on fetch + 90s timeout on Groq API call.
**Result:** Clear timeout message instead of silent failure.

### Grade-Wise Learning — One Engine, Many Units
**Problem:** The unit-learning front end was written for the Grade 8 Fractions unit (`unit_fractions.js`). Grade 9 Rational Numbers needs negatives, decimal answers and "put these in order" questions, none of which it could express.
**Fix:** Renamed the file to `static/js/unit_learning.js` — it was already driven entirely by `UNIT_SECTIONS` / `UNIT_QUESTIONS`, so only the name was unit-specific — and extended it:
- A mixed number's sign now lives on the whole part, so `-1 3/4` grades as `-(1 + 3/4)` instead of `-1×4 + 3`. The reduce and improper→mixed checks compare magnitudes.
- New `decimal` qtype (value compared with a 1e-9 epsilon, so `0.50`, `0.5` and even `3/4` for `0.75` all pass). New `order` qtype: click the tiles into sequence, click again to take one back out.
- New lesson visuals: `signline` (a number line that spans negatives) and `rules` (the sign-rule grid).
**Key principle:** Each unit stays pure data. Adding a unit means adding `units/gradeN/<unit>/` plus one `UNITS_CATALOG` entry — no new JS unless the unit needs a genuinely new kind of question.

### Unit Answers Are Computed, Not Typed
**Problem:** ~160 questions of hand-written answers across two units is a guaranteed source of wrong answers in front of students, and the worked "steps" can silently drift away from the answer they explain.
**Fix:** Each unit ships a `_generate.py` that the app never calls. It computes every answer with Python's exact `fractions.Fraction` / `decimal.Decimal`, and builds the worked steps from those same numbers, then writes `lessons.json` and `questions.json`. A test imports the generator and asserts the checked-in JSON still matches it, so hand-editing the JSON fails the build rather than quietly de-syncing.
**Note:** Grade 9 answer keys want fully reduced *improper* fractions (`-81/20`), while Grade 8 wants mixed numbers. Storing the Grade 9 answers with `whole: 0` gets both: the improper form is canonical, and a student who types `-4 1/20` is still marked correct.

### Curriculum Split
**Problem:** `app.py` was ~1000 lines mixing app logic with curriculum data.
**Fix:** Moved all curriculum data + `build_system_prompt()` to `curriculum.py`.
**Result:** `app.py` is now ~230 lines, clean and readable.

---

## ❌ Not Implemented

| What | Why Not |
|---|---|
| Response caching | App's value = unique worksheets every time. Caching defeats the purpose. |
| Gemini as LLM | Requires Google Cloud project setup — too complex for free tier. |
| React / Angular | Only 3 screens, simple state. Framework adds build complexity for zero user benefit. |
| Redis cache | Needs paid Render add-on (~$10/month). Not justified at current scale. |
| HTTP Keep-Alive | Already handled automatically by browser, Groq SDK, and FastAPI. No code needed. |

---

## 🔮 Future Improvements

| What | Value |
|---|---|
| Rate limiting per IP | Prevent one user from exhausting TPM for everyone |
| Pre-generated worksheet pool | Zero latency, zero TPM pressure during peak hours |
| Database + saved worksheets | High user value — teachers can revisit past worksheets |
| Teacher dashboard | Class management, assign worksheets, track progress |
| Real auth (Google OAuth) | Replace name-only login with actual accounts |
| Paid LLM (Claude Haiku) | Better math quality if app is monetised |

---

## LLM Stack

```
Primary:  Groq        →  llama-3.3-70b-versatile       (fast, free, ~6000 TPM)
Fallback: OpenRouter  →  llama-3.3-70b-instruct:free   (on Groq 429, ~200 req/day free)
```

### Models Tested on OpenRouter
| Model | Result |
|---|---|
| `meta-llama/llama-3.3-70b-instruct:free` | ✅ Works — slow (~5 min), confirmed working |
| `google/gemini-2.0-flash-exp:free` | ❌ API error — geo/access restrictions |
| `mistralai/mistral-7b-instruct:free` | ❌ No endpoints available |
| `meta-llama/llama-3.1-8b-instruct:free` | ❌ No endpoints available |
| `qwen/qwen3-4b:free` | ❌ Rate limit hit immediately |
| `qwen/qwen-2.5-72b-instruct:free` | ❌ 404 — wrong model ID |
