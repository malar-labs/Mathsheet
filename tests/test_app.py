"""
MathSheet Pro — Test Suite
Covers: extract_json, curriculum data, system prompt, API endpoints,
        max_tokens formula, and the static unit-learning content.
No LLM calls made — all AI interactions mocked.
"""
import os
import json
import importlib.util
import pytest
from math import gcd
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure no real API keys are used during tests
os.environ["GEMINI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["OPENROUTER_API_KEY"] = ""

from app import app, UNITS_CATALOG, UNITS_DIR, extract_json, load_unit_bundle
from curriculum import CURRICULUM, build_system_prompt

client = TestClient(app)

AVAILABLE_UNITS = [(u["grade"], u["unit"]) for u in UNITS_CATALOG if u["available"]]


# =============================================
#   extract_json
# =============================================

class TestExtractJson:
    def test_plain_json(self):
        assert extract_json('{"key": "value"}') == {"key": "value"}

    def test_json_in_markdown_json_block(self):
        text = '```json\n{"key": "value"}\n```'
        assert extract_json(text) == {"key": "value"}

    def test_json_in_plain_code_block(self):
        text = '```\n{"key": "value"}\n```'
        assert extract_json(text) == {"key": "value"}

    def test_json_with_surrounding_text(self):
        text = 'Sure! Here is your worksheet:\n{"title": "Math"}\nEnd of response.'
        assert extract_json(text) == {"title": "Math"}

    def test_whitespace_stripped(self):
        assert extract_json('   {"x": 1}   ') == {"x": 1}

    def test_nested_json(self):
        data = extract_json('{"questions": [{"number": 1, "answer": "42"}]}')
        assert data["questions"][0]["answer"] == "42"

    def test_invalid_json_raises_value_error(self):
        with pytest.raises(ValueError):
            extract_json("this is not json at all")

    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError):
            extract_json("")


# =============================================
#   Curriculum data
# =============================================

class TestCurriculum:
    def test_all_grades_1_to_9_present(self):
        for grade in range(1, 10):
            assert grade in CURRICULUM, f"Grade {grade} missing from CURRICULUM"

    def test_each_grade_has_at_least_one_topic(self):
        for grade in range(1, 10):
            assert len(CURRICULUM[grade]) > 0, f"Grade {grade} has no topics"

    def test_every_topic_has_name_field(self):
        for grade, topics in CURRICULUM.items():
            for key, topic in topics.items():
                assert "name" in topic, f"Topic '{key}' in grade {grade} missing 'name'"

    def test_topic_names_are_non_empty_strings(self):
        for grade, topics in CURRICULUM.items():
            for key, topic in topics.items():
                assert isinstance(topic["name"], str) and topic["name"].strip(), \
                    f"Topic '{key}' in grade {grade} has blank name"


# =============================================
#   build_system_prompt
# =============================================

class TestBuildSystemPrompt:
    @pytest.mark.parametrize("grade", range(1, 10))
    def test_returns_non_empty_string_for_all_grades(self, grade):
        prompt = build_system_prompt(grade)
        assert isinstance(prompt, str) and len(prompt) > 200

    def test_contains_rules_section(self):
        prompt = build_system_prompt(8)
        assert "RULES" in prompt

    def test_contains_scope_restriction(self):
        prompt = build_system_prompt(8)
        assert "ONLY" in prompt and "NEVER" in prompt

    def test_contains_json_output_instruction(self):
        prompt = build_system_prompt(8)
        assert "JSON" in prompt

    def test_contains_correct_grade_label(self):
        assert "Grade 4" in build_system_prompt(4)
        assert "Grade 9" in build_system_prompt(9)

    def test_unknown_grade_falls_back_to_grade_8(self):
        prompt = build_system_prompt(99)
        assert "Grade 8" in prompt

    def test_prompt_contains_curriculum_topics(self):
        prompt = build_system_prompt(8)
        assert "BC GRADE 8" in prompt.upper()


# =============================================
#   max_tokens formula
# =============================================

class TestMaxTokensFormula:
    """Tests the formula: min(4000, max(800, n * 200 + 300))"""

    def _calc(self, n):
        return min(4000, max(800, n * 200 + 300))

    def test_1_question_uses_floor(self):
        assert self._calc(1) == 800

    def test_5_questions(self):
        assert self._calc(5) == 1300

    def test_10_questions(self):
        assert self._calc(10) == 2300

    def test_20_questions(self):
        assert self._calc(20) == 4000

    def test_25_questions_capped_at_4000(self):
        assert self._calc(25) == 4000

    def test_always_between_800_and_4000(self):
        for n in range(1, 26):
            result = self._calc(n)
            assert 800 <= result <= 4000


# =============================================
#   API — Auth endpoints
# =============================================

class TestAuthEndpoints:
    def test_login_valid_name(self):
        r = client.post("/api/login", json={"username": "Malar"})
        assert r.status_code == 200
        assert r.json()["success"] is True
        assert r.json()["username"] == "Malar"

    def test_login_name_too_short(self):
        r = client.post("/api/login", json={"username": "A"})
        assert r.status_code == 200
        assert r.json()["success"] is False

    def test_login_empty_name(self):
        r = client.post("/api/login", json={"username": ""})
        assert r.status_code == 200
        assert r.json()["success"] is False

    def test_login_strips_whitespace(self):
        r = client.post("/api/login", json={"username": "  B  "})
        assert r.status_code == 200
        assert r.json()["success"] is False  # stripped to "B" = 1 char

    def test_guest_login(self):
        r = client.post("/api/guest")
        assert r.status_code == 200
        assert r.json()["success"] is True
        assert r.json()["username"] == "Guest"

    def test_logout(self):
        r = client.post("/api/logout")
        assert r.status_code == 200
        assert r.json()["success"] is True


# =============================================
#   API — Topics endpoint
# =============================================

class TestTopicsEndpoint:
    @pytest.mark.parametrize("grade", range(1, 10))
    def test_valid_grade_returns_topics(self, grade):
        r = client.get(f"/api/topics/{grade}")
        assert r.status_code == 200
        assert len(r.json()) > 0

    def test_invalid_grade_returns_404(self):
        r = client.get("/api/topics/99")
        assert r.status_code == 404

    def test_response_is_dict_of_topics(self):
        r = client.get("/api/topics/8")
        data = r.json()
        assert isinstance(data, dict)
        for topic in data.values():
            assert "name" in topic


# =============================================
#   Grade-wise learning pages (static content)
# =============================================

class TestTopLevelPages:
    def test_landing_page_is_grade_wise_learning(self):
        r = client.get("/")
        assert r.status_code == 200
        assert "Grade-Wise Learning" in r.text
        # the catalog, not the worksheet generator
        assert "/units/grade9/rational-numbers" in r.text
        assert 'id="login-btn"' not in r.text

    def test_worksheet_generator_moved_to_generator(self):
        r = client.get("/generator")
        assert r.status_code == 200
        assert 'id="login-btn"' in r.text

    def test_generator_is_not_linked_from_the_landing_page(self):
        # The generator is turned off for now: the header button is inert and
        # nothing in the copy offers a way in. /generator itself still answers,
        # so old links and bookmarks keep working.
        assert 'href="/generator"' not in client.get("/").text

    def test_landing_page_is_reachable_from_the_generator(self):
        assert 'href="/"' in client.get("/generator").text

    @pytest.mark.parametrize("path", ["/", "/account", "/units/grade9/rational-numbers"])
    def test_times_tables_is_one_click_from_every_page(self, path):
        """It is the one unit a child returns to daily, so it gets a header tab
        rather than living three clicks down behind a grade."""
        assert 'href="/units/grade3/times-tables"' in client.get(path).text

    def test_old_units_url_still_works(self):
        r = client.get("/units", follow_redirects=False)
        assert r.status_code in (307, 308)
        assert r.headers["location"] == "/"
        assert client.get("/units").status_code == 200


class TestUnitPages:
    @pytest.mark.parametrize("grade,unit", AVAILABLE_UNITS)
    def test_unit_page_is_overview(self, grade, unit):
        r = client.get(f"/units/grade{grade}/{unit}")
        assert r.status_code == 200
        assert "const UNIT_FOCUS_SECTION = null" in r.text

    @pytest.mark.parametrize("grade,unit", AVAILABLE_UNITS)
    def test_every_topic_has_its_own_page(self, grade, unit):
        sections = load_unit_bundle(grade, unit)["lessons"]["sections"]
        assert len(sections) >= 3
        for section in sections:
            page = client.get(f"/units/grade{grade}/{unit}/{section['id']}")
            assert page.status_code == 200
            assert section["title"] in page.text
            assert f'const UNIT_FOCUS_SECTION = "{section["id"]}"' in page.text

    @pytest.mark.parametrize("grade,unit", AVAILABLE_UNITS)
    def test_unknown_topic_returns_404(self, grade, unit):
        r = client.get(f"/units/grade{grade}/{unit}/nope")
        assert r.status_code == 404

    def test_catalog_entries_that_claim_to_be_available_really_are(self):
        for item in UNITS_CATALOG:
            bundle = load_unit_bundle(item["grade"], item["unit"])
            assert (bundle is not None) == item["available"], item

    def test_compare_has_10_number_and_5_word_problems(self):
        questions = [q for q in load_unit_bundle(8, "fractions")["questions"]
                     if q["section"] == "compare"]
        kinds = [q["kind"] for q in questions]
        assert kinds == ["number"] * 10 + ["word"] * 5
        for q in questions:
            if q["kind"] == "word":
                assert q["answer"]["choice"] in q["options"]


# =============================================
#   Unit question data — the contract the front-end engine relies on
# =============================================

ALL_UNIT_QUESTIONS = [
    pytest.param(grade, unit, q, id=f"grade{grade}-{unit}-{q['id']}")
    for grade, unit in AVAILABLE_UNITS
    for q in load_unit_bundle(grade, unit)["questions"]
]


class TestUnitQuestions:
    @pytest.mark.parametrize("grade,unit", AVAILABLE_UNITS)
    def test_question_ids_are_unique_and_sections_exist(self, grade, unit):
        bundle = load_unit_bundle(grade, unit)
        ids = [q["id"] for q in bundle["questions"]]
        assert len(ids) == len(set(ids))
        section_ids = {s["id"] for s in bundle["lessons"]["sections"]}
        assert {q["section"] for q in bundle["questions"]} <= section_ids

    @pytest.mark.parametrize("grade,unit", AVAILABLE_UNITS)
    def test_number_problems_come_before_word_problems(self, grade, unit):
        """The topic page prints a 'word problems start here' banner at the
        changeover, so a word problem must never be followed by a number one."""
        bundle = load_unit_bundle(grade, unit)
        for section in bundle["lessons"]["sections"]:
            kinds = [q.get("kind", "number") for q in bundle["questions"]
                     if q["section"] == section["id"]]
            assert kinds == sorted(kinds, key=lambda k: k != "number"), (section["id"], kinds)

    @pytest.mark.parametrize("grade,unit,q", ALL_UNIT_QUESTIONS)
    def test_question_has_the_fields_the_engine_reads(self, grade, unit, q):
        for field in ("id", "section", "qtype", "difficulty", "prompt", "answer", "steps", "tip"):
            assert q.get(field) not in (None, ""), field
        assert q["difficulty"] in (1, 2, 3)
        assert q["answer"].get("display")

    @pytest.mark.parametrize("grade,unit,q", ALL_UNIT_QUESTIONS)
    def test_answer_shape_matches_question_type(self, grade, unit, q):
        answer, qtype = q["answer"], q["qtype"]
        if qtype == "fraction":
            assert answer["den"] > 0
            # Answers are always given fully reduced.
            assert gcd(abs(answer["num"]), answer["den"]) == 1
        elif qtype == "decimal":
            assert float(answer["display"].replace("$", "")) == pytest.approx(answer["value"])
        elif qtype == "integer":
            assert isinstance(answer["value"], int)
        elif qtype == "compare":
            assert answer["symbol"] in ("<", "=", ">")
        elif qtype == "choice":
            assert answer["choice"] in q["options"]
        elif qtype == "order":
            assert sorted(answer["order"]) == sorted(q["options"])
            assert len(set(q["options"])) == len(q["options"])
        else:
            pytest.fail(f"unknown qtype {qtype!r}")


class TestGeneratedContentIsUpToDate:
    """The JSON files are build output. If someone edits them by hand the
    generator becomes a lie, so check the two still agree."""

    def test_rational_numbers_json_matches_its_generator(self):
        path = UNITS_DIR / "grade9" / "rational-numbers" / "_generate.py"
        spec = importlib.util.spec_from_file_location("rn_generate", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        bundle = load_unit_bundle(9, "rational-numbers")
        assert bundle["questions"] == module.QUESTIONS
        assert bundle["lessons"]["sections"] == module.SECTIONS

    def test_times_tables_json_matches_its_generator(self):
        path = UNITS_DIR / "grade3" / "times-tables" / "_generate.py"
        spec = importlib.util.spec_from_file_location("times_tables_generate", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        bundle = load_unit_bundle(3, "times-tables")
        assert bundle["questions"] == module.QUESTIONS
        assert bundle["lessons"]["sections"] == module.SECTIONS

    def test_times_tables_covers_every_fact(self):
        """A fact the drill never asks is a fact a child never practises, so the
        2-12 tables have to be covered exhaustively rather than sampled."""
        import re

        facts = set()
        for q in load_unit_bundle(3, "times-tables")["questions"]:
            product = re.fullmatch(r"(\d+) x (\d+) = \?", q["prompt"])
            missing = re.fullmatch(r"(\d+) x \? = (\d+)", q["prompt"])
            assert product or missing, q["prompt"]
            if product:
                a, b = int(product.group(1)), int(product.group(2))
                assert a * b == q["answer"]["value"], q["id"]
            else:
                a, total = int(missing.group(1)), int(missing.group(2))
                b = q["answer"]["value"]
                assert a * b == total, q["id"]
            facts.add(tuple(sorted((a, b))))

        every_fact = {tuple(sorted((a, b))) for a in range(2, 13) for b in range(2, 13)}
        assert facts == every_fact


# =============================================
#   API — Generate endpoint (no LLM calls)
# =============================================

class TestGenerateEndpoint:
    def test_no_api_keys_returns_error(self):
        with patch("app.GROQ_API_KEY", ""), patch("app.OPENROUTER_API_KEY", ""):
            r = client.post("/api/generate", json={
                "topics": ["fractions"],
                "grade": 8,
                "num_questions": 5,
            })
        assert r.status_code == 200
        assert r.json()["success"] is False
        assert "API key" in r.json()["error"]

    def test_empty_topics_returns_error(self):
        with patch("app.GROQ_API_KEY", "fake-key"), patch("app.OPENROUTER_API_KEY", ""):
            r = client.post("/api/generate", json={
                "topics": [],
                "grade": 8,
                "num_questions": 5,
            })
        assert r.status_code == 200
        assert r.json()["success"] is False

    def test_groq_429_falls_back_to_openrouter(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "title": "Test Worksheet",
            "grade": "Grade 8",
            "topic": "Fractions",
            "curriculum": "BC Mathematics Curriculum",
            "instructions": "Answer all questions.",
            "estimated_time": "30 minutes",
            "questions": [
                {
                    "number": 1,
                    "question": "What is 1/2 + 1/4?",
                    "type": "number",
                    "difficulty": "easy",
                    "space_needed": "small",
                    "answer": "3/4",
                    "solution_steps": "1/2 + 1/4 = 2/4 + 1/4 = 3/4"
                }
            ]
        })

        groq_error = Exception("Error code: 429 - rate limit exceeded")

        with patch("app.GROQ_API_KEY", "fake-groq-key"), \
             patch("app.OPENROUTER_API_KEY", "fake-or-key"), \
             patch("app.Groq") as mock_groq, \
             patch("app.OpenAI") as mock_openai:

            mock_groq.return_value.chat.completions.create.side_effect = groq_error
            mock_openai.return_value.chat.completions.create.return_value = mock_response

            r = client.post("/api/generate", json={
                "topics": ["fractions"],
                "grade": 8,
                "num_questions": 1,
            })

        assert r.status_code == 200
        assert r.json()["success"] is True

    def test_successful_generation_returns_worksheet(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "title": "Grade 8 Fractions Worksheet",
            "grade": "Grade 8",
            "topic": "Fractions",
            "curriculum": "BC Mathematics Curriculum",
            "instructions": "Show all your work.",
            "estimated_time": "30 minutes",
            "questions": [
                {
                    "number": 1,
                    "question": "Solve 3/4 + 1/8",
                    "type": "number",
                    "difficulty": "easy",
                    "space_needed": "small",
                    "answer": "7/8",
                    "solution_steps": "3/4 = 6/8, so 6/8 + 1/8 = 7/8"
                }
            ]
        })

        with patch("app.GROQ_API_KEY", "fake-key"), \
             patch("app.OPENROUTER_API_KEY", ""), \
             patch("app.Groq") as mock_groq:

            mock_groq.return_value.chat.completions.create.return_value = mock_response

            r = client.post("/api/generate", json={
                "topics": ["fractions"],
                "grade": 8,
                "num_questions": 1,
                "student_name": "Malar",
                "include_answers": True,
            })

        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        ws = data["worksheet"]
        assert "questions" in ws
        assert ws["student_name"] == "Malar"
        assert ws["include_answers"] is True
        assert len(ws["questions"]) == 1
