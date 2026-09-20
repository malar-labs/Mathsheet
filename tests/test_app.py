"""
MathSheet Pro — Test Suite
Covers: extract_json, curriculum data, system prompt, API endpoints,
        max_tokens formula, and the static unit-learning content.
No LLM calls made — all AI interactions mocked.
"""
import os
import json
import importlib.util
import re
import pytest
from fractions import Fraction
from math import gcd
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure no real API keys are used during tests
os.environ["GEMINI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["OPENROUTER_API_KEY"] = ""

from app import (app, UNITS_CATALOG, MARATHON_UNITS, UNITS_DIR, extract_json,
                 load_unit_bundle, unit_path, unit_url)
from curriculum import CURRICULUM, build_system_prompt

client = TestClient(app)

# Marathon units are listed too, so the per-question contract checks below
# keep covering them now that they no longer sit under a grade.
AVAILABLE_UNITS = (
    [dict(u) for u in UNITS_CATALOG if u["available"]]
    + [dict(u, marathon=True) for u in MARATHON_UNITS if u["available"]]
)


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

    def test_math_marathon_is_reached_from_the_landing_page(self):
        """It sits with the grades, as one of the things you can start on."""
        assert 'href="/math-marathon"' in client.get("/").text

    @pytest.mark.parametrize("path", ["/account", "/units/grade9/rational-numbers"])
    def test_no_page_carries_a_math_marathon_button_in_its_header(self, path):
        """Deliberate: the header is for getting back out, not for a shortcut
        into one particular unit."""
        assert "btn-header-tab" not in client.get(path).text

    @pytest.mark.parametrize("path", ["/", "/account", "/units/grade9/rational-numbers",
                                      "/math-marathon"])
    def test_the_way_back_is_called_grades_not_units(self, path):
        page = client.get(path).text
        assert "All Units" not in page

    def test_the_marathon_pill_sits_with_the_grades_not_in_the_header(self):
        """It belongs beside the grades, as one of the things you can start
        on — not as a button in the chrome."""
        page = client.get("/").text
        assert "ul-marathon-pill" in page
        assert "btn-header-tab" not in page

    def test_the_marathon_pill_is_not_mistaken_for_a_grade(self):
        """The grade-tab script drives every pill carrying data-grade. This one
        navigates away instead, so it must not carry one or its click would be
        intercepted and swallowed."""
        page = client.get("/").text
        pill = page[page.index("ul-marathon-pill"):]
        pill = pill[:pill.index("</a>")]
        assert "data-grade" not in pill
        assert 'href="/math-marathon"' in pill

    def test_math_marathon_is_not_under_a_grade(self):
        """It belongs to no grade, so its URL must not claim one."""
        assert client.get("/math-marathon").status_code == 200
        page = client.get("/math-marathon").text
        assert "Grade 3" not in page

    @pytest.mark.parametrize("old,new", [
        ("/units/grade3/math-marathon", "/math-marathon"),
        ("/units/grade3/math-marathon/t7", "/math-marathon/multiplication-facts/t7"),
    ])
    def test_the_old_grade_3_url_redirects(self, old, new):
        r = client.get(old, follow_redirects=False)
        assert r.status_code == 308
        assert r.headers["location"] == new

    def test_old_units_url_still_works(self):
        r = client.get("/units", follow_redirects=False)
        assert r.status_code in (307, 308)
        assert r.headers["location"] == "/"
        assert client.get("/units").status_code == 200


class TestUnitPages:
    @pytest.mark.parametrize("item", AVAILABLE_UNITS, ids=lambda i: i["unit"])
    def test_unit_page_is_overview(self, item):
        r = client.get(unit_url(item))
        assert r.status_code == 200
        assert "const UNIT_FOCUS_SECTION = null" in r.text

    @pytest.mark.parametrize("item", AVAILABLE_UNITS, ids=lambda i: i["unit"])
    def test_every_topic_has_its_own_page(self, item):
        sections = load_unit_bundle(unit_path(item))["lessons"]["sections"]
        assert len(sections) >= 3
        for section in sections:
            page = client.get(f"{unit_url(item)}/{section['id']}")
            assert page.status_code == 200
            assert section["title"] in page.text
            assert f'const UNIT_FOCUS_SECTION = "{section["id"]}"' in page.text

    @pytest.mark.parametrize("item", AVAILABLE_UNITS, ids=lambda i: i["unit"])
    def test_unknown_topic_returns_404(self, item):
        r = client.get(f"{unit_url(item)}/nope")
        assert r.status_code == 404

    def test_catalog_entries_that_claim_to_be_available_really_are(self):
        for item in ([dict(u) for u in UNITS_CATALOG]
                     + [dict(u, marathon=True) for u in MARATHON_UNITS]):
            bundle = load_unit_bundle(unit_path(item))
            assert (bundle is not None) == item["available"], item

    def test_compare_has_10_number_and_5_word_problems(self):
        questions = [q for q in load_unit_bundle("grade8/fractions")["questions"]
                     if q["section"] == "compare"]
        kinds = [q["kind"] for q in questions]
        assert kinds == ["number"] * 10 + ["word"] * 5
        for q in questions:
            if q["kind"] == "word":
                assert q["answer"]["choice"] in q["options"]


# =============================================
#   Unit question data — the contract the front-end engine relies on
# =============================================

def lcm(a, b):
    return a * b // gcd(a, b)


# {3/8}, {-1_1/4} and 5 are how a prompt writes its operands; brackets are
# decoration the worksheets put round a negative.
PROMPT_RE = re.compile(
    r"^\(?\{?(?P<a>-?\d+(?:_\d+)?(?:/\d+)?)\}?\)? (?P<op>[-+×÷]) "
    r"\(?\{?(?P<b>-?\d+(?:_\d+)?(?:/\d+)?)\}?\)? =$")


PROMPT_PIECE = re.compile(
    r"\{(?P<mw>-?\d+)_(?P<mn>\d+)/(?P<md>\d+)\}"     # {1_2/5}
    r"|\{(?P<fn>-?\d+)/(?P<fd>\d+)\}"                  # {3/5}
    r"|(?P<whole>\d+)"                                   # a bare whole number
    r"|(?P<sq>\u00b2)"
    r"|(?P<mul>\u00d7)|(?P<div>\u00f7)"
    r"|(?P<op>[-+()])"
    r"|(?P<space>\s+)")


def eval_prompt(prompt):
    """What a question's prompt is actually worth, worked out from the prompt.

    Translates the tokens the question prints into a Python expression over
    exact Fractions and evaluates it. Python's own precedence is BEDMAS, so this
    checks the answer key against the question AS PRINTED rather than against
    the generator that produced both of them.
    """
    text = prompt.strip()
    assert text.endswith("="), prompt
    text, pieces, i = text[:-1].strip(), [], 0
    while i < len(text):
        m = PROMPT_PIECE.match(text, i)
        assert m, (prompt, text[i:])
        i = m.end()
        if m.group("space"):
            continue
        if m.group("mw") is not None:
            w, n, d = (int(m.group(g)) for g in ("mw", "mn", "md"))
            pieces.append("Fraction(%d, %d)" % (w * d + n if w >= 0 else w * d - n, d))
        elif m.group("fn") is not None:
            pieces.append("Fraction(%s, %s)" % (m.group("fn"), m.group("fd")))
        elif m.group("whole") is not None:
            pieces.append("Fraction(%s)" % m.group("whole"))
        elif m.group("sq"):
            pieces.append("**2")
        elif m.group("mul"):
            pieces.append("*")
        elif m.group("div"):
            pieces.append("/")
        else:
            pieces.append(m.group("op"))
    return eval(" ".join(pieces), {"Fraction": Fraction, "__builtins__": {}})


def read_prompt(prompt):
    """The two operands and the operator a chain question actually asks about."""
    m = PROMPT_RE.fullmatch(prompt)
    assert m, prompt
    return (parse_answer_text(m.group("a").replace("_", " ")),
            parse_answer_text(m.group("b").replace("_", " ")),
            m.group("op"))


def parse_answer_text(text):
    """The front-end's own fraction parser, in Python: "-2 7/12" and "-4/3" and
    "5" all come back as an exact Fraction, anything else as None."""
    s = str(text).strip()
    mixed = re.fullmatch(r"(-?\d+) (\d+)/(\d+)", s)
    if mixed:
        whole, num, den = (int(g) for g in mixed.groups())
        if den == 0:
            return None
        return Fraction(whole * den - num if whole < 0 else whole * den + num, den)
    simple = re.fullmatch(r"(-?\d+)/(\d+)", s)
    if simple:
        num, den = int(simple.group(1)), int(simple.group(2))
        return None if den == 0 else Fraction(num, den)
    return Fraction(int(s)) if re.fullmatch(r"-?\d+", s) else None


ALL_UNIT_QUESTIONS = [
    pytest.param(item, q, id=f"{item['unit']}-{q['id']}")
    for item in AVAILABLE_UNITS
    for q in load_unit_bundle(unit_path(item))["questions"]
]


class TestUnitQuestions:
    @pytest.mark.parametrize("item", AVAILABLE_UNITS, ids=lambda i: i["unit"])
    def test_question_ids_are_unique_and_sections_exist(self, item):
        bundle = load_unit_bundle(unit_path(item))
        ids = [q["id"] for q in bundle["questions"]]
        assert len(ids) == len(set(ids))
        section_ids = {s["id"] for s in bundle["lessons"]["sections"]}
        assert {q["section"] for q in bundle["questions"]} <= section_ids

    @pytest.mark.parametrize("item", AVAILABLE_UNITS, ids=lambda i: i["unit"])
    def test_number_problems_come_before_word_problems(self, item):
        """The topic page prints a 'word problems start here' banner at the
        changeover, so a word problem must never be followed by a number one."""
        bundle = load_unit_bundle(unit_path(item))
        for section in bundle["lessons"]["sections"]:
            kinds = [q.get("kind", "number") for q in bundle["questions"]
                     if q["section"] == section["id"]]
            assert kinds == sorted(kinds, key=lambda k: k != "number"), (section["id"], kinds)

    @pytest.mark.parametrize("item,q", ALL_UNIT_QUESTIONS)
    def test_question_has_the_fields_the_engine_reads(self, item, q):
        for field in ("id", "section", "qtype", "difficulty", "prompt", "answer", "steps", "tip"):
            assert q.get(field) not in (None, ""), field
        assert q["difficulty"] in (1, 2, 3)
        assert q["answer"].get("display")

    @pytest.mark.parametrize("item,q", ALL_UNIT_QUESTIONS)
    def test_answer_shape_matches_question_type(self, item, q):
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
        elif qtype == "equivalent":
            # Deliberately NOT reduced: which equivalent form comes next IS the
            # question, so 4/8 is the answer and 1/2 would be the wrong one.
            assert answer["den"] > 0 and answer["num"] > 0
            assert answer["display"] == f"{answer['num']}/{answer['den']}"
        elif qtype == "steps":
            assert answer["steps"], q["id"]
            for row in answer["steps"]:
                assert row["label"] and row["note"], q["id"]
                assert 1 <= len(row["fields"]) <= 2, q["id"]
                assert ("join" in row) == (len(row["fields"]) > 1), q["id"]
                for field in row["fields"]:
                    assert parse_answer_text(field) is not None, (q["id"], field)
            # The last box of the last line IS the answer, or the chain and the
            # answer key could drift apart.
            assert answer["steps"][-1]["fields"] == [answer["display"]], q["id"]
        else:
            pytest.fail(f"unknown qtype {qtype!r}")


# Every worked-chain question in the app, whichever grade it belongs to. The
# contracts below hold for all of them; the grade-specific design rules get
# their own classes underneath.
CHAIN_UNITS = {
    "grade8/fractions": load_unit_bundle("grade8/fractions"),
    "grade9/rational-numbers": load_unit_bundle("grade9/rational-numbers"),
}
ALL_CHAINS = [
    pytest.param(unit, q, id=f"{unit.split('/')[0]}-{q['id']}")
    for unit, bundle in CHAIN_UNITS.items()
    for q in bundle["questions"] if q["qtype"] == "steps"
]


def is_rewrite_chain(q):
    """Two kinds of chain live under the `steps` type.

    A REWRITE chain takes one calculation — a + b — and writes it a different
    way on every line, so every line is worth the same. A STAGE chain takes an
    order-of-operations expression and takes one operation out of it per line,
    so the lines are deliberately different numbers and only the last is the
    answer. The prompt says which: two operands means a rewrite.
    """
    return PROMPT_RE.fullmatch(q["prompt"]) is not None


REWRITE_CHAINS = [c for c in ALL_CHAINS if is_rewrite_chain(c.values[1])]
STAGE_CHAINS = [c for c in ALL_CHAINS if not is_rewrite_chain(c.values[1])]


def chain_sections(unit):
    """The sections of `unit` that ask for a worked chain, in order."""
    bundle = CHAIN_UNITS[unit]
    with_chains = {q["section"] for q in bundle["questions"] if q["qtype"] == "steps"}
    return [s for s in bundle["lessons"]["sections"] if s["id"] in with_chains]


def chain_questions(unit, section_id):
    return [q for q in CHAIN_UNITS[unit]["questions"]
            if q["section"] == section_id and q["qtype"] == "steps"]


class TestWorkedChains:
    """A worked-chain question asks for every line of the solution, the way the
    teacher's worksheets do, and marks each line on its own. That only works if
    each line really does follow from the last."""

    @pytest.mark.parametrize("unit,q", ALL_CHAINS)
    def test_the_last_line_is_the_answer_to_the_prompt(self, unit, q):
        """The chain has to land on the value the prompt actually asks for."""
        assert parse_answer_text(q["answer"]["display"]) == eval_prompt(q["prompt"]), q["id"]

    @pytest.mark.parametrize("unit,q", STAGE_CHAINS)
    def test_a_stage_chain_takes_one_operation_out_per_line(self, unit, q):
        """Order of operations is the one topic where the lines are SUPPOSED to
        be different numbers: each is the expression with one more operation
        done. A line that repeats the one above it means an operation was
        skipped — except the last, which may restate the answer as a mixed
        number."""
        rows = q["answer"]["steps"]
        assert len(rows) >= 2, q["id"]
        assert all(len(r["fields"]) == 1 for r in rows), q["id"]
        values = [parse_answer_text(r["fields"][0]) for r in rows]
        assert None not in values, q["id"]
        body = values[:-1] if rows[-1]["label"] == "Mixed number" else values
        assert len(set(body)) == len(body), (q["id"], body)
        assert values[-1] == eval_prompt(q["prompt"]), q["id"]

    @pytest.mark.parametrize("unit,q", REWRITE_CHAINS)
    def test_no_line_changes_the_value(self, unit, q):
        """Convert, common denominator, solve, simplify — every line is a
        rewrite of the same number, so they must all be equal."""
        a, b, op = read_prompt(q["prompt"])
        expected = {"+": a + b, "-": a - b, "×": a * b, "÷": a / b}[op]
        for row in q["answer"]["steps"]:
            values = [parse_answer_text(f) for f in row["fields"]]
            assert all(v is not None for v in values), (q["id"], row["fields"])
            if len(values) == 1:
                assert values[0] == expected, (q["id"], row["label"])
            else:
                # A Convert line keeps the original operator, so ÷ turns up
                # here as well as on the Invert line's ×.
                joined = {"+": values[0] + values[1], "-": values[0] - values[1],
                          "×": values[0] * values[1],
                          "÷": values[0] / values[1]}[row["join"]]
                assert joined == expected, (q["id"], row["label"])

    @pytest.mark.parametrize("unit,q", ALL_CHAINS)
    def test_every_line_is_a_different_form_from_the_one_before(self, unit, q):
        """A line the student can pass by copying the line above teaches
        nothing, and the front-end would mark the copy right."""
        seen = [row["fields"] for row in q["answer"]["steps"]]
        assert len(seen) == len({tuple(f) for f in seen}), q["id"]

    @pytest.mark.parametrize("unit,q", ALL_CHAINS)
    def test_the_last_box_is_the_answer_key(self, unit, q):
        """The front-end marks the last box against answer.display. If those two
        drift apart it marks a correct final line wrong."""
        assert q["answer"]["steps"][-1]["fields"] == [q["answer"]["display"]], q["id"]

    @pytest.mark.parametrize("unit,q", ALL_CHAINS)
    def test_the_chain_finishes_reduced_and_as_a_mixed_number(self, unit, q):
        final = q["answer"]["display"]
        value = parse_answer_text(final)
        assert gcd(abs(value.numerator), value.denominator) == 1, q["id"]
        if abs(value) > 1 and value.denominator != 1:
            assert " " in final, (q["id"], final)

    @pytest.mark.parametrize("unit", list(CHAIN_UNITS))
    def test_the_scaffold_comes_away_before_the_topic_does(self, unit):
        """Every chain topic opens with worked samples and ends with a few
        questions that have none — copying the shape off the top of the page is
        a stage, not the skill."""
        for section in chain_sections(unit):
            questions = chain_questions(unit, section["id"])
            sets = [q.get("set") for q in questions]
            assert sets[0] is not None, section["id"]
            assert sets[-1] is None, section["id"]
            unscaffolded = [x for x in sets if x is None]
            assert 3 <= len(unscaffolded) < len(sets), (section["id"], sets)
            # ...and once the samples stop they don't start again.
            assert sets == sorted(sets, key=lambda x: (x is None, x or 0)), section["id"]

    @pytest.mark.parametrize("unit", list(CHAIN_UNITS))
    def test_every_set_has_the_sample_it_promises(self, unit):
        """A question tagged with a set whose sample doesn't exist would render
        a page with nothing at the top and no way to tell that was a mistake."""
        for section in chain_sections(unit):
            samples = section.get("samples", [])
            assert samples, section["id"]
            asked = {q["set"] for q in chain_questions(unit, section["id"])
                     if q.get("set") is not None}
            assert {x["set"] for x in samples} == asked, section["id"]
            # Sets run 1..n in the order the questions are listed, so the sample
            # at the top of a page never jumps backwards through the topic.
            assert asked == set(range(1, max(asked) + 1)), section["id"]

    @pytest.mark.parametrize("unit", list(CHAIN_UNITS))
    def test_a_sample_models_the_move_the_page_asks_for(self, unit):
        """Optional lines vary problem to problem — Simplify only shows up when
        the answer reduces — so what must match is the operator and the line the
        method opens with."""
        for section in chain_sections(unit):
            for sample in section.get("samples", []):
                expected = eval_prompt(sample["prompt"])
                rewrite = PROMPT_RE.fullmatch(sample["prompt"]) is not None
                for row in sample["steps"]:
                    values = [parse_answer_text(f) for f in row["fields"]]
                    assert all(v is not None for v in values), sample["prompt"]
                    if not rewrite:
                        continue     # a stage sample's lines are meant to differ
                    if len(values) == 1:
                        assert values[0] == expected, (sample["prompt"], row["label"])
                    else:
                        joined = {"+": values[0] + values[1],
                                  "-": values[0] - values[1],
                                  "×": values[0] * values[1],
                                  "÷": values[0] / values[1]}[row["join"]]
                        assert joined == expected, (sample["prompt"], row["label"])
                assert parse_answer_text(sample["steps"][-1]["fields"][-1]) == expected, \
                    sample["prompt"]

                in_set = [q for q in chain_questions(unit, section["id"])
                          if q.get("set") == sample["set"]]
                assert in_set, (section["id"], sample["set"])
                opening = {q["answer"]["steps"][0]["label"] for q in in_set}
                assert sample["steps"][0]["label"] in opening, sample["prompt"]


class TestGrade9FractionOperations:
    """Grade 9's chain topic is built straight off the teacher's five Math-Drills
    worksheets, so it carries design rules the Grade 8 one doesn't."""

    QS = [q for q in load_unit_bundle("grade9/rational-numbers")["questions"]
          if q["section"] == "frac-ops"]

    def test_the_topic_exists_and_every_question_in_it_is_a_chain(self):
        bundle = load_unit_bundle("grade9/rational-numbers")
        section = next(s for s in bundle["lessons"]["sections"] if s["id"] == "frac-ops")
        assert section["title"] == "Basic Operations with Fractions"
        assert self.QS and all(q["qtype"] == "steps" for q in self.QS)

    def test_one_problem_to_a_page(self):
        """A chain is a long enough row on its own; nothing shares its page."""
        assert all("page" not in q for q in self.QS)

    @pytest.mark.parametrize("q", QS, ids=lambda q: q["id"])
    def test_the_numbers_stay_small_enough_to_do_in_your_head(self, q):
        """This topic is meant to be calculator-free throughout."""
        for row in q["answer"]["steps"]:
            for field in row["fields"]:
                value = parse_answer_text(field)
                assert abs(value.numerator) <= 40, (q["id"], field)
                assert value.denominator <= 30, (q["id"], field)

    def test_the_first_sets_keep_the_denominators_easy(self):
        """Sets 1-2 share a denominator outright and set 3 holds the LCM at 12
        throughout, so the layout is the only new thing to learn at the start."""
        for q in self.QS:
            a, b, op = read_prompt(q["prompt"])
            if q.get("set") in (1, 2):
                assert a.denominator == b.denominator, q["id"]
            elif q.get("set") == 3:
                assert lcm(a.denominator, b.denominator) == 12, q["id"]

    def test_the_topic_has_its_own_page(self):
        page = client.get("/units/grade9/rational-numbers/frac-ops")
        assert page.status_code == 200
        assert "Basic Operations with Fractions" in page.text


class TestGrade8FractionArithmetic:
    """Grade 8's four arithmetic topics ask for the same chain, with Grade 8's
    own conventions: positive fractions, and mixed numbers as the final form."""

    ARITHMETIC = ["add", "subtract", "multiply", "divide"]

    def test_every_arithmetic_topic_asks_for_the_working(self):
        for section_id in self.ARITHMETIC:
            chains = chain_questions("grade8/fractions", section_id)
            assert len(chains) >= 8, section_id

    def test_the_word_problem_keeps_a_single_answer_box(self):
        """Working out WHICH sum to do is the question in a word problem. A
        chain would hand that over on the first line."""
        for section_id in self.ARITHMETIC:
            questions = [q for q in CHAIN_UNITS["grade8/fractions"]["questions"]
                         if q["section"] == section_id]
            assert questions[-1]["qtype"] == "fraction", section_id
            assert "?" in questions[-1]["prompt"], section_id
            assert all(q["qtype"] == "steps" for q in questions[:-1]), section_id

    def test_order_of_operations_runs_easy_to_tough(self):
        """The topic goes two operations, then brackets, then long chains, then
        applying it to a story. Difficulty has to climb within each of those
        strands or the ordering is decorative."""
        questions = [q for q in CHAIN_UNITS["grade8/fractions"]["questions"]
                     if q["section"] == "order-ops"]
        assert questions, "the topic should exist"

        strands = {}
        for q in questions:
            strands.setdefault("chain" if q["qtype"] == "steps" else q["qtype"],
                               []).append(q["difficulty"])
        assert set(strands) == {"chain", "choice", "fraction", "integer"}

        chain = strands["chain"]
        assert chain == sorted(chain), chain
        assert chain[0] == 1 and chain[-1] == 3, chain

        # The word problems are one strand however they are answered, so they
        # are checked in the order they appear rather than by answer type.
        words = [q["difficulty"] for q in questions
                 if q["qtype"] in ("fraction", "integer")]
        assert words == sorted(words), words

    def test_order_of_operations_is_the_last_topic(self):
        """It needs all four operations, so it cannot come before them."""
        ids = [s["id"] for s in CHAIN_UNITS["grade8/fractions"]["lessons"]["sections"]]
        assert ids[-1] == "order-ops", ids
        for section_id in self.ARITHMETIC:
            assert ids.index(section_id) < ids.index("order-ops")

    @pytest.mark.parametrize("section_id", ARITHMETIC + ["order-ops"])
    def test_the_topic_page_still_loads(self, section_id):
        page = client.get(f"/units/grade8/fractions/{section_id}")
        assert page.status_code == 200
        assert f'const UNIT_FOCUS_SECTION = "{section_id}"' in page.text


class TestFractionAdditionDrill:
    """Skip counting is the gym exercise behind multiplication; equivalence is
    the one behind adding fractions. This unit drills that first, then the three
    moves it makes possible — match the bottoms, add the tops, tidy up."""

    BUNDLE = load_unit_bundle("math-marathon/fraction-addition")
    QS = BUNDLE["questions"]
    SECTIONS = BUNDLE["lessons"]["sections"]

    def test_it_uses_the_drill_engine(self):
        assert self.BUNDLE["lessons"]["meta"]["engine"] == "drill"
        page = client.get("/math-marathon/fraction-addition").text
        assert "js/times_tables.js" in page
        assert "js/unit_learning.js" not in page

    def test_it_walks_the_four_stages_in_order(self):
        """Equivalence has to come before matching bottoms, and matching before
        adding, or the drill is asking for a move that hasn't been built yet.
        Nothing on the page says so, so the order of the levels has to."""
        assert [s["id"] for s in self.SECTIONS] == [
            "eq-half", "eq-third", "eq-quarter",     # 1 · equivalence
            "match-fit", "match-lcm",                # 2 · make them match
            "same-bottom",                           # 3 · add the tops
            "simplify",                              # 4 · tidy up
            "make-them-match", "mixed",              # 5 · all four at once
        ]

    def test_it_reads_as_one_flat_list_like_the_other_marathon_units(self):
        """A unit that groups its levels when its neighbours don't looks like a
        different kind of thing."""
        for section in self.SECTIONS:
            assert "group" not in section, section["id"]

    def test_pages_hold_four_to_six_questions(self):
        """Short enough to finish in a sitting and see a score for. The
        equivalence ladders are the short ones: a chain only has so many rungs
        worth blanking."""
        from collections import Counter
        sizes = Counter((q["section"], q["set"]) for q in self.QS)
        assert set(sizes.values()) <= {3, 4, 5, 6}, sorted(set(sizes.values()))

    def test_every_level_runs_easiest_pass_first(self):
        order = {"equiv": 0, "equivpair": 1, "pick": 2, "type": 3}
        for section in self.SECTIONS:
            modes = [q["mode"] for q in self.QS if q["section"] == section["id"]]
            assert set(modes) <= set(order), section["id"]
            assert {"pick", "type"} <= set(modes), section["id"]
            assert modes == sorted(modes, key=lambda m: order[m]), section["id"]

    def test_every_equivalence_ladder_is_one_amount_cut_finer(self):
        """A rung that isn't equal to the base would teach the opposite of what
        the ladder exists for."""
        laddered = [s for s in self.SECTIONS if "ladder" in s]
        assert laddered, "the unit's whole premise is the equivalence ladder"
        for section in laddered:
            ladder = section["ladder"]
            assert ladder["mode"] == "equiv", section["id"]
            base = Fraction(*ladder["base"])
            for k, (num, den) in enumerate(ladder["chain"], start=1):
                assert Fraction(num, den) == base, (section["id"], num, den)
                # each rung is the base cut k times finer, in order
                assert (num, den) == (base.numerator * k, base.denominator * k)

    def test_the_ladder_shows_the_pattern_before_it_asks_for_it(self):
        for section in self.SECTIONS:
            if "ladder" not in section:
                continue
            chain = section["ladder"]["chain"]
            blanks = [q for q in self.QS
                      if q["section"] == section["id"] and q["mode"] == "equiv"]
            steps = [q["step"] for q in blanks]
            assert steps == sorted(steps) == sorted(set(steps)), section["id"]
            # The first two rungs stay filled in, and some rung always does.
            assert min(steps) > 2, section["id"]
            assert 0 < len(steps) < len(chain), section["id"]
            assert all(q["set"] == 1 for q in blanks), section["id"]
            for q in blanks:
                assert q["answer"]["value"] == chain[q["step"] - 1][0], q["id"]

    def test_the_first_ladder_pass_only_asks_for_the_top(self):
        """The bottom is printed. "How many of THESE make it?" is the question
        worth asking first; producing a whole fraction is the pass after."""
        for q in self.QS:
            if q["mode"] != "equiv":
                continue
            assert q["qtype"] == "integer", q["id"]
            assert re.fullmatch(r"\{\d+/\d+\} = \?/\d+", q["prompt"]), q["prompt"]

    def test_the_second_ladder_pass_asks_for_the_whole_fraction(self):
        """With the bottom given you only count the top up; with both gone you
        have to know what size piece comes next as well."""
        pairs = [q for q in self.QS if q["mode"] == "equivpair"]
        assert pairs, "the second pass is the point of this change"
        laddered = {s["id"] for s in self.SECTIONS if "ladder" in s}
        assert {q["section"] for q in pairs} == laddered
        for q in pairs:
            assert q["qtype"] == "equivalent", q["id"]
            assert q["answer"]["num"] > 0 and q["answer"]["den"] > 0, q["id"]
            base = next(s["ladder"]["base"] for s in self.SECTIONS
                        if s["id"] == q["section"])
            assert (Fraction(q["answer"]["num"], q["answer"]["den"])
                    == Fraction(*base)), q["id"]

    def test_the_two_ladder_passes_blank_different_rungs(self):
        """Otherwise the second page is the first one again with more typing."""
        for section in self.SECTIONS:
            if "ladder" not in section:
                continue
            tops = {q["step"] for q in self.QS
                    if q["section"] == section["id"] and q["mode"] == "equiv"}
            both = {q["step"] for q in self.QS
                    if q["section"] == section["id"] and q["mode"] == "equivpair"}
            assert both and not (tops & both), section["id"]

    def test_fraction_answers_are_always_tidied(self):
        """The drill marks an untidy answer wrong, so the key had better not
        contain one."""
        for q in self.QS:
            if q["qtype"] != "fraction":
                continue
            num, den = q["answer"]["num"], q["answer"]["den"]
            assert gcd(num, den) == 1, q["id"]
            assert q["answer"]["display"] == f"{num}/{den}", q["id"]

    def test_a_page_of_equivalences_starts_every_question_the_same_way(self):
        """Not just the same amount — the same fraction, written the same way.
        A page that asks about 1/3 and then about 2/6 makes a child who is still
        learning what a third looks like read two of them at once, and they are
        the same amount, so "same value" is not a strong enough rule to catch
        it."""
        from collections import defaultdict
        pages = defaultdict(set)
        for q in self.QS:
            # Mixed Review is the one lap where jumbling them up IS the point.
            if q["mode"] not in ("pick", "type") or q["section"] == "mixed":
                continue
            m = re.match(r"\{(\d+)/(\d+)\} = \?/(\d+)", q["prompt"])
            if not m:
                continue
            pages[(q["section"], q["set"])].add((int(m.group(1)), int(m.group(2))))
        assert pages
        for key, written in pages.items():
            assert len(written) == 1, (key, sorted(written))

    def test_the_sums_are_ones_a_child_can_hold_in_their_head(self):
        """Fraction fluency, not arithmetic with big numbers."""
        for q in self.QS:
            for num, den in re.findall(r"\{(\d+)/(\d+)\}", q["prompt"]):
                assert int(den) <= 24, (q["id"], q["prompt"])
                assert int(num) <= int(den), (q["id"], q["prompt"])

    def test_every_sum_asked_is_the_answer_given(self):
        """The whole-sum levels are the only place both sides are written out,
        so they can be checked against each other."""
        checked = 0
        for q in self.QS:
            m = re.fullmatch(r"\{(\d+)/(\d+)\} \+ \{(\d+)/(\d+)\} = \?", q["prompt"])
            if not m:
                continue
            a, b, c, d = (int(g) for g in m.groups())
            total = Fraction(a, b) + Fraction(c, d)
            if q["qtype"] == "choice":
                assert q["answer"]["choice"] == "{%d/%d}" % (total.numerator,
                                                             total.denominator), q["id"]
            else:
                assert Fraction(q["answer"]["num"], q["answer"]["den"]) == total, q["id"]
            checked += 1
        assert checked >= 20, checked

    def test_the_wrong_options_are_the_mistakes_children_make(self):
        """A distractor nobody would pick tests nothing. The one that matters
        here is adding the bottoms as well as the tops."""
        tempting = 0
        for q in self.QS:
            m = re.fullmatch(r"\{(\d+)/(\d+)\} \+ \{(\d+)/(\d+)\} = \?", q["prompt"])
            if not m or q["qtype"] != "choice":
                continue
            a, b, c, d = (int(g) for g in m.groups())
            if "{%d/%d}" % (a + c, b + d) in q["options"]:
                tempting += 1
        assert tempting >= 5, tempting

    def test_every_level_has_its_own_page(self):
        for section in self.SECTIONS:
            page = client.get(f"/math-marathon/fraction-addition/{section['id']}")
            assert page.status_code == 200
            assert f'const UNIT_FOCUS_SECTION = "{section["id"]}"' in page.text


class TestGeneratedContentIsUpToDate:
    """The JSON files are build output. If someone edits them by hand the
    generator becomes a lie, so check the two still agree."""

    def test_rational_numbers_json_matches_its_generator(self):
        path = UNITS_DIR / "grade9" / "rational-numbers" / "_generate.py"
        spec = importlib.util.spec_from_file_location("rn_generate", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        bundle = load_unit_bundle("grade9/rational-numbers")
        assert bundle["questions"] == module.QUESTIONS
        assert bundle["lessons"]["sections"] == module.SECTIONS

    @pytest.mark.parametrize(
        "slug", ["multiplication-facts", "division-facts", "fraction-addition"])
    def test_math_marathon_json_matches_its_generator(self, slug):
        path = UNITS_DIR / "math-marathon" / "_generate.py"
        spec = importlib.util.spec_from_file_location("math_marathon_generate", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        bundle = load_unit_bundle(f"math-marathon/{slug}")
        assert bundle["questions"] == module.UNITS[slug].questions
        assert bundle["lessons"]["sections"] == module.UNITS[slug].sections

    def test_math_marathon_covers_every_fact(self):
        """A fact the drill never asks is a fact a child never practises, so the
        2-12 tables have to be covered exhaustively rather than sampled."""
        import re

        facts = set()
        for q in load_unit_bundle("math-marathon/multiplication-facts")["questions"]:
            if q["mode"] in ("skip", "back"):
                continue   # a rung on the ladder, not a stated fact
            product = re.fullmatch(r"(\d+) x (\d+) = \?", q["prompt"])
            missing = re.fullmatch(r"(\d+) x \? = (\d+)", q["prompt"])
            assert product or missing, q["prompt"]
            # Half the questions are multiple choice, so the answer arrives as
            # a chosen string rather than a number.
            value = (int(q["answer"]["choice"]) if q["qtype"] == "choice"
                     else q["answer"]["value"])
            if product:
                a, b = int(product.group(1)), int(product.group(2))
                assert a * b == value, q["id"]
            else:
                a, total = int(missing.group(1)), int(missing.group(2))
                b = value
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
