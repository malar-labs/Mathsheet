from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from markupsafe import Markup
from pydantic import BaseModel
from typing import List
from groq import Groq
from openai import OpenAI
from google import genai
from google.genai import types as genai_types
import os
import json
import re
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from curriculum import CURRICULUM, build_system_prompt
import store

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("mathsheet")

# ===== APP SETUP =====

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Let go of the shared Supabase connection on the way out.
    await store.aclose()


app = FastAPI(title="MathSheet Pro — BC Math Worksheet Generator", lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get('SECRET_KEY', 'mathsheet-bc-grade8-secret-2024'),
)

# Absolute paths: on serverless hosts the process starts from somewhere else.
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.filters['tojson'] = lambda v: Markup(json.dumps(v, ensure_ascii=False))


def asset_url(path: str) -> str:
    """/static URL with the file's modified time appended, so browsers load edited CSS/JS right away."""
    try:
        version = int((STATIC_DIR / path).stat().st_mtime)
    except OSError:
        version = 0
    return f"/static/{path}?v={version}"


templates.env.globals['asset_url'] = asset_url
# Cloudflare Web Analytics site token. Public by design (it ships in the HTML),
# so the live site's token is the default; set CF_ANALYTICS_TOKEN to '' to turn
# the beacon off, e.g. when running locally.
templates.env.globals['cf_analytics_token'] = os.environ.get(
    'CF_ANALYTICS_TOKEN', '14d3a471abb949d9bf14c1ef99334ffc'
)

GEMINI_API_KEY     = os.environ.get('GEMINI_API_KEY', '')
GROQ_API_KEY       = os.environ.get('GROQ_API_KEY', '')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')

GEMINI_MODEL       = "gemini-2.5-flash-lite"
GROQ_MODEL         = "llama-3.3-70b-versatile"
OPENROUTER_MODEL   = "meta-llama/llama-3.3-70b-instruct:free"

# ===== REQUEST MODELS =====
class LoginBody(BaseModel):
    username: str

class AccountBody(BaseModel):
    username: str = ''
    pin: str = ''
    grade: int | None = None

class ProgressBody(BaseModel):
    unit_key: str
    verdicts: dict[str, str] = {}

class ClearProgressBody(BaseModel):
    unit_key: str
    question_ids: List[str] = []

class GenerateBody(BaseModel):
    topics: List[str] = []
    grade: int = 8
    student_name: str = ''
    problem_type: str = 'mixed'
    difficulty: str = 'mixed'
    num_questions: int = 10
    include_answers: bool = False
    custom_prompt: str = ''

def extract_json(text: str) -> dict:
    """Robustly extract JSON from AI response text."""
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    raise ValueError("Could not parse AI response as JSON")


# ===== ROUTES =====

@app.get("/")
async def home(request: Request):
    """Grade-wise learning is the landing page; the worksheet generator is one
    click away at /generator."""
    return templates.TemplateResponse(
        request,
        "units_home.html",
        {"grades": catalog_by_grade(), "learner": current_learner(request)}
    )


@app.get("/generator")
async def generator(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"curriculum": CURRICULUM}
    )


# ===== UNIT-WISE LEARNING (static content, no AI/LLM calls) =====
# Lessons + practice questions here are pre-written and stored as JSON under
# units/gradeN/<unit>/. They were generated once (offline, from a curriculum
# prompt and a sample worksheet) and are just read from disk at request time
# — this feature never calls Gemini/Groq/OpenRouter.

UNITS_DIR = BASE_DIR / "units"

UNITS_CATALOG = [
    {
        "grade": 8, "unit": "fractions", "title": "Fractions", "emoji": "🍕",
        "description": "What fractions are, comparing, common multiples, simplifying, and all four operations.",
        "available": True,
    },
    {
        "grade": 8, "unit": "algebra", "title": "Algebra", "emoji": "⚖️",
        "description": "Writing and simplifying expressions, and solving two-step equations.",
        "available": False,
    },
    {
        "grade": 9, "unit": "rational-numbers", "title": "Rational Numbers", "emoji": "±",
        "description": "Comparing and ordering, the four operations in decimal and fraction form with negatives, and order of operations.",
        "available": True,
    },
    {
        "grade": 9, "unit": "exponents", "title": "Exponents & Powers", "emoji": "xⁿ",
        "description": "Powers with integral exponents, and the exponent laws for multiplying, dividing and raising powers.",
        "available": False,
    },
    {
        "grade": 3, "unit": "math-gym", "title": "Math Gym", "emoji": "🏋️",
        "description": "Multiplication facts from the 2 times table up to the 12s, drilled one at a time until they come back without thinking.",
        "available": True,
    },
    {
        "grade": 3, "unit": "coming-soon", "title": "Coming soon", "emoji": "🧮",
        "description": "More Grade 3 units are on the way.", "available": False,
    },
]


def load_unit_bundle(grade: int, unit: str):
    base = UNITS_DIR / f"grade{grade}" / unit
    lessons_file = base / "lessons.json"
    questions_file = base / "questions.json"
    if not lessons_file.is_file() or not questions_file.is_file():
        return None
    with open(lessons_file, encoding="utf-8") as f:
        lessons = json.load(f)
    with open(questions_file, encoding="utf-8") as f:
        questions = json.load(f)
    return {"lessons": lessons, "questions": questions.get("questions", [])}


def catalog_by_grade():
    """The catalog grouped under its grades, so the landing page shows the
    Grade → Unit → Topics hierarchy. Counts come from each unit's own JSON,
    so they can't drift from the content.

    Grades you can actually study come first, in grade order; grades that only
    hold "coming soon" placeholders sink to the bottom rather than leading the
    page with something nobody can open."""
    grades: dict[int, list] = {}
    for item in UNITS_CATALOG:
        entry = dict(item)
        bundle = load_unit_bundle(item["grade"], item["unit"]) if item["available"] else None
        if bundle:
            entry["topics"] = [
                {"id": s["id"], "title": s["title"]} for s in bundle["lessons"]["sections"]
            ]
            entry["question_count"] = len(bundle["questions"])
        grades.setdefault(item["grade"], []).append(entry)

    def order(grade):
        has_units = any(unit["available"] for unit in grades[grade])
        return (0 if has_units else 1, grade)

    # ...and inside a grade, the units you can open come before the placeholders.
    return [
        {"grade": grade, "units": sorted(grades[grade], key=lambda u: not u["available"])}
        for grade in sorted(grades, key=order)
    ]


@app.get("/units")
async def units_home():
    # The catalog moved to the landing page; keep older links working.
    return RedirectResponse("/", status_code=308)


async def render_unit_page(request: Request, grade: int, unit: str, section_id: str | None = None):
    bundle = load_unit_bundle(grade, unit)
    focus = None
    if bundle and section_id:
        focus = next((s for s in bundle["lessons"]["sections"] if s["id"] == section_id), None)
    if not bundle or (section_id and not focus):
        return templates.TemplateResponse(
            request,
            "units_home.html",
            {"grades": catalog_by_grade(), "not_found": True, "learner": current_learner(request)},
            status_code=404,
        )

    # A signed-in learner's saved answers ship with the page, so the progress
    # bar is right in the first paint instead of jumping after a fetch. If
    # Supabase is unreachable the page still renders — the browser's own copy
    # takes over and syncing resumes later.
    learner = current_learner(request)
    unit_key = f"grade{grade}_{unit}"
    saved: dict = {}
    if learner:
        try:
            saved = (await store.load_progress(learner["id"], unit_key)).get(unit_key, {})
        except store.StoreError as exc:
            logger.warning("PROGRESS| %s", exc)

    return templates.TemplateResponse(
        request,
        "unit_page.html",
        {
            "meta": bundle["lessons"]["meta"],
            "sections": bundle["lessons"]["sections"],
            "questions": bundle["questions"],
            "focus": focus,
            "learner": learner,
            "saved_progress": saved,
        },
    )


@app.get("/units/grade{grade}/{unit}")
async def unit_page(request: Request, grade: int, unit: str):
    return await render_unit_page(request, grade, unit)


# One topic on its own page (no topic tabs), e.g. /units/grade8/fractions/compare
@app.get("/units/grade{grade}/{unit}/{section}")
async def unit_section_page(request: Request, grade: int, unit: str, section: str):
    return await render_unit_page(request, grade, unit, section)


# ===== LEARNER ACCOUNTS (username + 4-digit PIN) =====
# Deliberately not email/OAuth: most of these learners are under 13, so the less
# we know about them the better. A username and a PIN carry progress between
# devices and identify nobody. The cost is that a forgotten PIN has to be reset
# by hand from the Supabase dashboard — there's no email to send a link to.

def current_learner(request: Request) -> dict | None:
    return request.session.get("learner")


@app.get("/account")
async def account_page(request: Request, next: str = "/"):
    return templates.TemplateResponse(
        request,
        "account.html",
        {
            "learner": current_learner(request),
            "accounts_enabled": store.enabled(),
            "next_url": next if next.startswith("/") else "/",
        },
    )


@app.post("/api/account/signup")
async def account_signup(body: AccountBody, request: Request):
    if not store.enabled():
        return JSONResponse({"success": False, "error": "Accounts aren't set up on this server."}, status_code=503)

    display_name = (body.username or '').strip()
    username = store.normalize_username(display_name)
    problem = store.username_problem(username) or store.pin_problem(body.pin)
    if problem:
        return JSONResponse({"success": False, "error": problem}, status_code=400)

    try:
        if await store.find_learner(username):
            raise store.UsernameTaken("That username is taken — try another.")
        learner = await store.create_learner(username, display_name, body.pin, body.grade)
    except store.UsernameTaken as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=409)
    except store.StoreError as exc:
        logger.warning("SIGNUP  | %s", exc)
        return JSONResponse({"success": False, "error": "Couldn't save your account — try again."}, status_code=502)

    request.session["learner"] = {
        "id": learner["id"], "username": username, "display_name": learner["display_name"],
    }
    logger.info("SIGNUP  | user=%-20s | ip=%s", username, get_client_ip(request))
    return JSONResponse({"success": True, "learner": request.session["learner"]})


@app.post("/api/account/login")
async def account_login(body: AccountBody, request: Request):
    if not store.enabled():
        return JSONResponse({"success": False, "error": "Accounts aren't set up on this server."}, status_code=503)

    username = store.normalize_username(body.username)
    try:
        learner = await store.find_learner(username)
    except store.StoreError as exc:
        logger.warning("LOGIN   | %s", exc)
        return JSONResponse({"success": False, "error": "Couldn't reach the progress server — try again."}, status_code=502)

    # One message for "no such user" and "wrong PIN" alike, so the form can't be
    # used to find out which usernames exist.
    wrong = JSONResponse({"success": False, "error": "That username and PIN don't match."}, status_code=401)
    if not learner:
        return wrong

    locked = store.lockout_remaining(learner)
    if locked:
        return JSONResponse(
            {"success": False, "error": f"Too many wrong tries. Try again in {locked} minutes."},
            status_code=429,
        )

    if not store.verify_pin(body.pin, learner["pin_hash"]):
        minutes = await store.note_failed_attempt(learner)
        if minutes:
            return JSONResponse(
                {"success": False, "error": f"Too many wrong tries. Try again in {minutes} minutes."},
                status_code=429,
            )
        return wrong

    await store.note_signed_in(learner["id"])
    request.session["learner"] = {
        "id": learner["id"], "username": username, "display_name": learner["display_name"],
    }
    logger.info("LOGIN   | user=%-20s | ip=%s", username, get_client_ip(request))
    return JSONResponse({"success": True, "learner": request.session["learner"]})


@app.post("/api/account/logout")
async def account_logout(request: Request):
    request.session.pop("learner", None)
    return JSONResponse({"success": True})


@app.get("/api/progress")
async def get_progress(request: Request):
    learner = current_learner(request)
    if not learner:
        return JSONResponse({"success": False, "error": "Not signed in."}, status_code=401)
    try:
        return JSONResponse({"success": True, "progress": await store.load_progress(learner["id"])})
    except store.StoreError as exc:
        logger.warning("PROGRESS| %s", exc)
        return JSONResponse({"success": False, "error": "Couldn't load your progress."}, status_code=502)


@app.post("/api/progress")
async def post_progress(body: ProgressBody, request: Request):
    learner = current_learner(request)
    if not learner:
        return JSONResponse({"success": False, "error": "Not signed in."}, status_code=401)
    try:
        merged = await store.save_progress(learner["id"], body.unit_key, body.verdicts)
    except store.StoreError as exc:
        # Losing a sync isn't fatal — the browser still holds the answers.
        logger.warning("PROGRESS| %s", exc)
        return JSONResponse({"success": False, "error": "Couldn't save right now."}, status_code=502)
    return JSONResponse({"success": True, "progress": merged})


@app.post("/api/progress/clear")
async def post_progress_clear(body: ClearProgressBody, request: Request):
    learner = current_learner(request)
    if not learner:
        return JSONResponse({"success": False, "error": "Not signed in."}, status_code=401)
    try:
        await store.clear_progress(learner["id"], body.unit_key, body.question_ids)
    except store.StoreError as exc:
        logger.warning("PROGRESS| %s", exc)
        return JSONResponse({"success": False, "error": "Couldn't clear that topic."}, status_code=502)
    return JSONResponse({"success": True})


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    return forwarded.split(",")[0].strip() if forwarded else request.client.host

def get_browser(request: Request) -> str:
    ua = request.headers.get("user-agent", "unknown")
    for name in ("Chrome", "Firefox", "Safari", "Edge", "Opera"):
        if name in ua:
            return name
    return "unknown"


@app.post("/api/login")
async def login(body: LoginBody, request: Request):
    username = body.username.strip()
    if not username or len(username) < 2:
        return JSONResponse({"success": False, "error": "Please enter a name (at least 2 characters)"})
    request.session["user"] = username
    request.session["is_guest"] = False
    logger.info("LOGIN   | user=%-20s | ip=%-15s | browser=%s",
                username, get_client_ip(request), get_browser(request))
    return JSONResponse({"success": True, "username": username})


@app.post("/api/guest")
async def guest(request: Request):
    request.session["user"] = "Guest"
    request.session["is_guest"] = True
    logger.info("GUEST   | ip=%-15s | browser=%s",
                get_client_ip(request), get_browser(request))
    return JSONResponse({"success": True, "username": "Guest"})


@app.post("/api/logout")
async def logout(request: Request):
    request.session.clear()
    return JSONResponse({"success": True})


@app.get("/api/topics/{grade}")
async def get_topics(grade: int):
    topics = CURRICULUM.get(grade)
    if not topics:
        return JSONResponse({"error": "Invalid grade"}, status_code=404)
    return JSONResponse(topics)


@app.post("/api/generate")
async def generate(body: GenerateBody, request: Request):
    if not GEMINI_API_KEY and not GROQ_API_KEY and not OPENROUTER_API_KEY:
        return JSONResponse({
            "success": False,
            "error": "No API key configured. Add GEMINI_API_KEY, GROQ_API_KEY, or OPENROUTER_API_KEY to your .env file."
        })

    try:
        topics = body.topics
        grade = body.grade
        grade_topics = CURRICULUM.get(grade, CURRICULUM[8])
        problem_type = body.problem_type
        difficulty = body.difficulty
        num_questions = max(1, min(25, body.num_questions))
        custom_prompt = body.custom_prompt.strip()
        include_answers = body.include_answers
        student_name = body.student_name.strip()

        if not topics:
            return JSONResponse({"success": False, "error": "Please select at least one topic"})

        topic_names = [grade_topics[t]["name"] for t in topics if t in grade_topics]
        user = request.session.get("user", "anonymous")
        logger.info("GENERATE| user=%-20s | ip=%-15s | grade=%-3s | q=%-2s | topics=%s",
                    user, get_client_ip(request), grade, num_questions, ", ".join(topic_names))
        if not topic_names:
            return JSONResponse({"success": False, "error": "Invalid topics selected"})

        problem_type_desc = {
            "word":   "WORD PROBLEMS ONLY — every question must be a real-life story/scenario problem with a BC or First Peoples context",
            "number": "NUMERICAL/COMPUTATION PROBLEMS ONLY — direct calculation problems, no story contexts needed",
            "mixed":  "MIX of approximately 50% word problems (BC contexts) and 50% direct numerical computation problems"
        }.get(problem_type, "a mix of word and numerical problems")

        difficulty_desc = {
            "easy":   "EASY — straightforward, single-step or simple two-step problems testing basic understanding",
            "medium": "MEDIUM — problems requiring application of concepts and some multi-step reasoning",
            "hard":   "HARD — challenging problems requiring deeper understanding, multi-step reasoning, and synthesis",
            "mixed":  "MIXED — begin with 2–3 easy questions, progress through medium, end with 2–3 hard/challenge questions"
        }.get(difficulty, "mixed difficulty progressing from easy to hard")

        per_topic = max(1, num_questions // len(topic_names))

        # Dynamic max_tokens: ~200 tokens per question + 300 overhead, capped at 4000
        max_tokens = min(4000, max(800, num_questions * 200 + 300))

        prompt = f"""Create a BC Grade {grade} Mathematics worksheet with EXACTLY {num_questions} questions.

TOPICS: {", ".join(topic_names)}
PROBLEM TYPES: {problem_type_desc}
DIFFICULTY: {difficulty_desc}
DISTRIBUTION: ~{per_topic} question(s) per topic across {len(topic_names)} topic(s).

- space_needed: small/medium/large
- solution_steps: full step-by-step working
"""
        if custom_prompt:
            prompt += f"\nTEACHER INSTRUCTIONS: {custom_prompt}\n"
            prompt += "NOTE: Teacher instructions modify topic/type selection only. Curriculum difficulty and number ranges for this grade still apply.\n"

        prompt += "\nReturn ONLY the raw JSON object. No markdown. No extra text."

        messages = [
            {"role": "system", "content": build_system_prompt(grade)},
            {"role": "user",   "content": prompt}
        ]
        common_params = dict(
            messages=messages,
            temperature=0.65,
            max_tokens=max_tokens,
        )

        raw      = None
        llm_used = None

        # --- Primary: Gemini (Google AI Studio) ---
        if GEMINI_API_KEY:
            try:
                logger.info("Sending request to Gemini (%s)", GEMINI_MODEL)
                gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                system_content = messages[0]['content']
                user_content   = messages[1]['content']
                gemini_response = gemini_client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=user_content,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=system_content,
                        max_output_tokens=max_tokens,
                        temperature=0.65,
                    ),
                )
                raw      = gemini_response.text
                llm_used = "Gemini"
            except Exception as e:
                logger.warning("Gemini error (%s): %s — falling back to Groq", type(e).__name__, str(e))

        # --- First Fallback: Groq ---
        if raw is None and GROQ_API_KEY:
            try:
                logger.info("Sending request to Groq (%s)", GROQ_MODEL)
                groq_client = Groq(api_key=GROQ_API_KEY)
                groq_response = groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    timeout=90,
                    **common_params,
                )
                msg      = groq_response.choices[0].message
                raw      = msg.content or getattr(msg, 'reasoning', None)
                llm_used = "Groq"
            except Exception as e:
                logger.warning("Groq error (%s): %s", type(e).__name__, str(e))
                if "429" not in str(e):
                    raise  # non-rate-limit error — surface it
                logger.warning("Groq rate limit hit — falling back to OpenRouter")

        # --- Second Fallback: OpenRouter ---
        if raw is None:
            if not OPENROUTER_API_KEY:
                raise Exception("All providers failed and no OpenRouter API key configured.")
            logger.info("Sending request to OpenRouter (%s)", OPENROUTER_MODEL)
            or_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=OPENROUTER_API_KEY,
                timeout=90.0,
            )
            or_response = or_client.chat.completions.create(
                model=OPENROUTER_MODEL,
                **common_params,
            )
            msg      = or_response.choices[0].message
            raw      = msg.content or getattr(msg, 'reasoning', None)
            llm_used = "OpenRouter"

        if not raw:
            raise ValueError("All providers returned an empty response.")
        worksheet_data = extract_json(raw)
        worksheet_data["student_name"]    = student_name
        worksheet_data["date"]            = datetime.now().strftime("%B %d, %Y")
        worksheet_data["include_answers"] = include_answers

        logger.info("SUCCESS | user=%-20s | llm=%-12s | tokens=%s",
                    user, llm_used, max_tokens)
        return JSONResponse({"success": True, "worksheet": worksheet_data})

    except Exception as e:
        msg = str(e)
        if any(k in msg.upper() for k in ("API_KEY", "INVALID", "CREDENTIAL", "AUTH")):
            msg = "Invalid API key. Please check your GROQ_API_KEY in the .env file."
        elif any(k in msg.upper() for k in ("QUOTA", "LIMIT", "429")):
            msg = "API rate limit reached. Please wait a moment and try again."
        elif any(k in msg.lower() for k in ("timeout", "timed out", "read timeout")):
            msg = "The AI took too long to respond. Please try again — it usually works on the second attempt."
        elif "JSON" in msg.upper() or "parse" in msg.lower():
            msg = "AI returned an unexpected format. Please try again."
        return JSONResponse({"success": False, "error": f"Generation error: {msg}"})


# ===== ENTRY POINT =====
if __name__ == "__main__":
    import uvicorn
    logger.info("MathSheet Pro — BC Math Worksheet Generator (Grade 1–9)")
    logger.info("Framework: FastAPI + Uvicorn")
    if GEMINI_API_KEY:
        logger.info("Gemini primary         | model=%s", GEMINI_MODEL)
    else:
        logger.warning("GEMINI_API_KEY not set — Gemini disabled")
    if GROQ_API_KEY:
        logger.info("Groq first fallback    | model=%s", GROQ_MODEL)
    else:
        logger.warning("GROQ_API_KEY not set — Groq fallback disabled")
    if OPENROUTER_API_KEY:
        logger.info("OpenRouter second fallback | model=%s", OPENROUTER_MODEL)
    else:
        logger.warning("OPENROUTER_API_KEY not set — OpenRouter fallback disabled")
    logger.info("Open browser at: http://localhost:5000")
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
