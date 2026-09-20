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

### Fraction Addition Is a Fact-Fluency Drill, Not a Lesson
**Problem:** Adding fractions gets taught as a four-step procedure and practised as whole sums, so a child who isn't fluent at "1/2 = 3/6" spends their working memory on the conversion and has none left for the sum. Skip counting is the gym exercise that makes multiplication automatic; nothing in the app was the equivalent for fractions.
**Fix:** A third Math Marathon unit built on the claim that the equivalent exercise is **equivalence**. It drills the sequence in the order the muscle builds: equivalence ladders → make the bottoms match → add the tops → tidy up → all four at once.
- The ladder mechanism generalised rather than being rebuilt: a new `equiv` mode runs along one fraction's equivalents (`1/2 = 2/4 = __/6 = 4/8`) exactly as `skip` runs up a table. Same blanking rule, same page, same marking.
- Stages 1-3 print the denominator and ask only for the top (`1/3 + 1/6 — write 1/3 as ?/6`), so the answer stays a single integer and the drill stays on the one move being practised. Only tidying up and whole sums ask for a fraction, because by then writing one *is* the skill.
- Distractors are the two mistakes that actually happen — adding the bottoms as well as the tops (`1/3 + 1/6 = 2/9`), and stopping before tidying (`1/2 + 1/4 = 2/4`) — and a test asserts the first of those is on offer in at least five questions. A distractor nobody would pick tests nothing.
- A typed fraction is only right in lowest terms. Tidying is half the skill, so accepting `3/6` would quietly drop stage 4; the help line on a wrong answer shows the reduction.
**Also:** the drill engine learned to render `{a/b}` stacked. A fraction drill that prints `1/2` makes a child parse the sum before they can start it. Levels can now carry a `group`, which the overview already knew how to render — nine levels in one flat grid would be a wall, five named stages are a route.

### Worked Chains — Marking Every Line, Not Just the Answer
**Problem:** The teacher's Math-Drills worksheets don't ask for an answer, they ask for a row of blanks — convert, common denominator, solve, simplify — with the labels printed underneath, and every blank gets marked. The engine only ever had one box per question, so a student who reached the right answer by a wrong route looked identical to one who didn't.
**Fix:** A `steps` qtype whose answer carries the chain: `steps: [{label, note, join?, fields: ["-6/30", "20/30"]}]`. The whole row renders as the worksheet renders it — problem, then a box per line with its label under it — one `Check answer` submits the lot, and each box comes back ticked or crossed with a sentence saying what that line wanted.
- A box is graded on **form**, not value: `20/30` and `2/3` are the same number, but only one of them is the common-denominator line. The three outcomes map onto the engine's existing ones — every box exactly right is `correct`, every box at least the right *number* is `close`, anything else is `wrong` — so the score and the question map keep meaning what they meant.
- Wrong-form is diagnosed rather than just flagged: not reduced yet, needs to be over 12, still has to be a mixed number. Each is a different mistake and gets its own sentence.
- A question nobody has typed into is not marked wrong for being untouched — submitting an entirely blank row returns a nudge instead.

### The Admin Page, and Who Gets to See It
**Problem:** A teacher can see one learner's progress only by signing in as them. There was no way to look at a class.
**Fix:** `/admin` lists every account with what they have answered and how they scored; `/admin/learner/<id>` breaks one learner down by unit and topic and names the topics where the most answers came back less than right.
**Who is an admin:** a flag on the learner row (`is_admin`, added by the schema file, default false), set by hand in Supabase. Deliberately **not** a username check — registering the username `admin` has to buy nothing, or the first person to think of it owns everybody's data. There is a test for exactly that.
**The flag is re-read on every request**, never trusted from the session. Caching it would mean revoking someone's admin only took effect once they happened to sign out. The session copy exists solely to decide whether to draw the link on the account page; it authorises nothing.
**404, not 403.** A 403 confirms the page exists to anyone who pokes at it. Signed out, ordinary learner, accounts switched off entirely — all get the same not-found page.
**Gotcha:** PostgREST caps a response at 1000 rows and says nothing when it truncates, which here would silently under-report a class. Anything that reads a table in full goes through `_get_all()`, which walks pages until one comes back short.

### Two Kinds of Worked Chain
**Problem:** Grade 8's Order of Operations topic wanted the same row-of-boxes treatment as the arithmetic topics, but a chain there means something different. In `3/4 + 1/6`, every line is another way of writing one number. In `1/4 x 5/6 - 1/6`, the lines are deliberately *different* numbers: each is the expression with one more operation taken out of it. The existing chain contract — "no line changes the value" — is exactly wrong for the second kind.
**Fix:** Both still ship as `steps`; the prompt says which kind it is (two operands means a rewrite). Value-invariance is asserted only for rewrite chains; stage chains get their own contract — one field per line, values strictly changing, last line equal to the answer.
**Better test:** rather than trusting the generator that produced both sides, the tests now **read the prompt back**. `eval_prompt()` translates a question's own printed tokens into a Python expression over exact `Fraction`s and evaluates it — Python's precedence *is* BEDMAS — so every chain's answer key is checked against the question as a student sees it. That covers both kinds and replaced the old two-operand-only check.
**Expressions are data:** an order-of-operations question is built from nested tuples, and one evaluator produces the prompt, every box and the answer from the same arithmetic. A leaf remembers how it was *written* as well as what it is worth, because the worksheet prints `3/6` where the value is a half.

### The Scaffold Has to Come Away
**Problem:** A worked example at the top of every page is a crutch a student can ride to the end of a topic without ever choosing a method — they copy the shape off the sample and fill in different numbers. The topic then reports fluency it hasn't tested.
**Fix:** Questions carry a `set`, which picks the sample shown above them; the last few in every chain topic carry none, so the page comes up bare. Grade 9 ends with five mixed problems and a tip that says as much; each Grade 8 topic ends with three, then the word problem. A test asserts every chain topic starts scaffolded, ends unscaffolded, and never goes back — the samples stop once and stay stopped.
**Also:** Grade 8's four arithmetic topics moved onto the same chain machinery, with Grade 8's own conventions (positive fractions, mixed numbers as the final form) rather than Grade 9's. The word problem at the end of each keeps its single answer box: working out *which* sum to do is the question there, and a chain hands that over on its first line.

### Pages That Hold More Than One Problem
**Problem:** A worksheet page has ten problems on it and one worked example at the top; the engine had exactly one question per page.
**Fix:** Questions carrying the same `q.page` render together — five to a page in the chain topic — under a filled-in sample from `section.samples` built by the same generator code as the questions, so it can never model a different method from the one being marked. Everything untagged still gets a page to itself, so no existing topic changed. Routing, the question map and "continue where I left off" count pages now; the score still counts questions.
**Gotcha:** Checking one question re-renders the whole topic, which would have wiped whatever was half-typed into the other four. Every box therefore writes through to `ulState` (`stepState[qid].typed`, `draft[qid]`) on each keystroke and is re-read on render. Element ids had to go too — five questions on one page can't all own `#ul-answer` — so the card is addressed by `data-qid` and everything inside it by class.

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
