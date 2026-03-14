# MathSheet Pro — Technical Notes

---

## ✅ Implemented

### Token Optimisation
**Problem:** Groq free tier = 6,000 TPM. Hardcoded `max_tokens=8192` burned the entire quota per request.
**Fix:** Dynamic `max_tokens = min(4000, num_questions × 220 + 400)`. Also trimmed user prompt by ~150 tokens.
**Result:** 10 questions now uses ~2,600 tokens instead of 8,192.

### OpenRouter Fallback
**Problem:** Single LLM provider = single point of failure on 429 rate limit.
**Fix:** Groq fails with 429 → automatically retries with OpenRouter (`llama-3.3-70b-instruct:free`).
**Result:** Users never see a rate limit error during normal usage.
**Caveat:** OpenRouter free tier has daily limits (~200 req/day). Exhausted during testing. Resets daily. Not suitable as primary — fallback only.

### Network Timeout
**Problem:** India user got "Network error" — browser silently killed slow connections.
**Fix:** `AbortController` (2 min) on fetch + 90s timeout on Groq API call.
**Result:** Clear timeout message instead of silent failure.

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
