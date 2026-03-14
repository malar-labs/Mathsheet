from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from markupsafe import Markup
from pydantic import BaseModel
from typing import List
from groq import Groq
from openai import OpenAI
import os
import json
import re
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from curriculum import CURRICULUM, build_system_prompt

load_dotenv()

# ===== APP SETUP =====
app = FastAPI(title="MathSheet Pro — BC Math Worksheet Generator")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get('SECRET_KEY', 'mathsheet-bc-grade8-secret-2024'),
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.filters['tojson'] = lambda v: Markup(json.dumps(v, ensure_ascii=False))

GROQ_API_KEY       = os.environ.get('GROQ_API_KEY', '')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')

OPENROUTER_MODEL   = "qwen/qwen3-4b:free"

# ===== REQUEST MODELS =====
class LoginBody(BaseModel):
    username: str

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
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "curriculum": CURRICULUM}
    )


@app.post("/api/login")
async def login(body: LoginBody, request: Request):
    username = body.username.strip()
    if not username or len(username) < 2:
        return JSONResponse({"success": False, "error": "Please enter a name (at least 2 characters)"})
    request.session["user"] = username
    request.session["is_guest"] = False
    return JSONResponse({"success": True, "username": username})


@app.post("/api/guest")
async def guest(request: Request):
    request.session["user"] = "Guest"
    request.session["is_guest"] = True
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
    if not GROQ_API_KEY and not OPENROUTER_API_KEY:
        return JSONResponse({
            "success": False,
            "error": "No API key configured. Add GROQ_API_KEY or OPENROUTER_API_KEY to your .env file."
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

        # Dynamic max_tokens: ~220 tokens per question + 400 overhead, capped at 4000
        max_tokens = min(4000, max(1200, num_questions * 220 + 400))

        prompt = f"""Create a BC Grade {grade} Mathematics worksheet with EXACTLY {num_questions} questions.

TOPICS: {", ".join(topic_names)}
PROBLEM TYPES: {problem_type_desc}
DIFFICULTY: {difficulty_desc}
DISTRIBUTION: ~{per_topic} question(s) per topic across {len(topic_names)} topic(s).

REQUIREMENTS:
- Mathematically verified correct answers
- Word problems: BC contexts (Vancouver, Fraser River, First Peoples traditions, CAD, hockey)
- space_needed: "small" (one line), "medium" (3–5 lines), "large" (multi-step/diagrams)
- solution_steps: full step-by-step working
"""
        if custom_prompt:
            prompt += f"\nTEACHER INSTRUCTIONS: {custom_prompt}\n"

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

        response = None

        # --- Primary: Groq ---
        if GROQ_API_KEY:
            try:
                groq_client = Groq(api_key=GROQ_API_KEY)
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    timeout=90,
                    **common_params,
                )
            except Exception as e:
                if "429" not in str(e):
                    raise  # non-rate-limit error — don't fall back, surface it
                # 429 → fall through to OpenRouter

        # --- Fallback: OpenRouter ---
        if response is None:
            if not OPENROUTER_API_KEY:
                raise Exception("Groq rate limit reached and no OpenRouter API key configured.")
            or_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=OPENROUTER_API_KEY,
                timeout=90.0,
            )
            response = or_client.chat.completions.create(
                model=OPENROUTER_MODEL,
                **common_params,
            )

        msg = response.choices[0].message
        raw = msg.content or getattr(msg, 'reasoning', None)
        if not raw:
            raise ValueError("Model returned empty response.")
        worksheet_data = extract_json(raw)
        worksheet_data["student_name"]    = student_name
        worksheet_data["date"]            = datetime.now().strftime("%B %d, %Y")
        worksheet_data["include_answers"] = include_answers

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
    print("=" * 60)
    print("  MathSheet Pro — BC Math Worksheet Generator (KG–9)")
    print("  Framework: FastAPI + Uvicorn")
    print("=" * 60)
    if not GROQ_API_KEY:
        print("  ⚠  WARNING: GROQ_API_KEY not set in .env file!")
        print("  Get a free key at: https://console.groq.com/keys")
    else:
        print("  ✓  Groq API key loaded")
    print("  Open browser at: http://localhost:5000")
    print("=" * 60)
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
