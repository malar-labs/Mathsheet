"""
One-time content generator for the Grade 3 "Math Gym" unit.

This script is NOT called by the running app. It writes the static lessons.json
and questions.json files that ship with the app; the app only ever reads those
JSON files, and nothing in this feature calls any AI/LLM API.

Re-run with `python _generate.py` from this folder after editing anything below.

Math Gym is a drill, not a lesson unit: the goal is recall fast enough that the
fact arrives before the child has time to count it out. So every fact in the
2-12 tables appears, each question carries the strategy for its own table, and
every answer is computed here rather than typed — which is what makes shipping
169 of them safe.

Tables are grouped by the strategy that unlocks them, not by numeric order:
    x2, x5, x10   double / halve the ten fact / shift a place  -> warmup
    x3, x4        built on doubling                            -> x3-x4
    x6, x7        built on the 5 fact                          -> x6-x7
    x8, x9        double three times / ten minus one           -> x8-x9
    x11, x12      repeat the digit / ten fact plus two fact    -> x11-x12
then the two drills that test recall rather than reconstruction: the missing
factor, and a shuffled workout of the facts children miss most.
"""
import json
from pathlib import Path

# Every table is drilled against these. 0 and 1 are left out: they are rules
# ("anything times 0 is 0"), not facts that need memorising.
MULTIPLICANDS = list(range(2, 13))


# ---------------------------------------------------------------------------
# Strategies — how to rebuild a fact that hasn't been memorised yet
# ---------------------------------------------------------------------------

def strategy(anchor, other):
    """The worked line for `anchor x other`.

    Each is the strategy actually taught for that table, written out with the
    real numbers so the reasoning is visible rather than asserted."""
    product = anchor * other
    if anchor == 2:
        return f"Doubling: {other} + {other} = {product}."
    if anchor == 3:
        return (f"Double {other} to get {2 * other}, then add one more {other}: "
                f"{2 * other} + {other} = {product}.")
    if anchor == 4:
        return (f"Double twice. {other} doubles to {2 * other}, and {2 * other} "
                f"doubles to {product}.")
    if anchor == 5:
        return (f"Ten {other}s is {10 * other}, and 5 is half of 10, so halve it: "
                f"half of {10 * other} is {product}.")
    if anchor == 6:
        return (f"Start from the 5 fact. Five {other}s is {5 * other}, then add one "
                f"more {other}: {5 * other} + {other} = {product}.")
    if anchor == 7:
        return (f"Split the 7 into 5 and 2. Five {other}s is {5 * other}, two {other}s "
                f"is {2 * other}, and {5 * other} + {2 * other} = {product}.")
    if anchor == 8:
        return (f"Double three times: {other} to {2 * other}, {2 * other} to "
                f"{4 * other}, {4 * other} to {product}.")
    if anchor == 9:
        return (f"Ten {other}s is {10 * other}, then take one {other} back off: "
                f"{10 * other} - {other} = {product}.")
    if anchor == 10:
        return f"Times 10 moves every digit up one place, so {other} becomes {product}."
    if anchor == 11:
        if other <= 9:
            return (f"For 11 times a single digit, write the digit twice: {other} and "
                    f"{other} gives {product}.")
        return (f"Ten {other}s is {10 * other}, plus one more {other}: "
                f"{10 * other} + {other} = {product}.")
    if anchor == 12:
        return (f"Ten {other}s is {10 * other}, two {other}s is {2 * other}, and "
                f"{10 * other} + {2 * other} = {product}.")
    raise ValueError(f"no strategy written for the {anchor} times table")


TIPS = {
    "warmup": "These three are the anchors. Nearly every other fact is built out of "
              "them, so make these instant first.",
    "x3-x4": "Both of these lean on doubling. If you can double a number, you already "
             "have most of the 3 and 4 tables.",
    "x6-x7": "Reach for the 5 fact first, then adjust. Six of something is five of it "
             "plus one more; seven is five plus two.",
    "x8-x9": "8 is doubling three times. 9 is the 10 fact minus one of the number — "
             "and the digits of every 9 fact add up to 9.",
    "x11-x12": "11 repeats the digit as far as 11 x 9. 12 is the 10 fact plus the 2 "
               "fact, both of which you already know.",
    "missing": "Read it as a question: how many of this make that? If nothing comes to "
               "mind, divide — dividing undoes multiplying.",
    "mixed": "No pattern to lean on here, which is the point. If you have to work one "
             "out, that fact needs another lap.",
}


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------

QUESTIONS = []
_counters = {}


def ask(section, prompt, value, steps, difficulty):
    _counters[section] = _counters.get(section, 0) + 1
    QUESTIONS.append({
        "id": f"{section}-{_counters[section]:02d}",
        "section": section,
        "qtype": "integer",
        "kind": "number",
        "difficulty": difficulty,
        "prompt": prompt,
        "answer": {"value": value, "display": str(value)},
        "steps": steps,
        "tip": TIPS[section],
    })


def drill(section, anchor, difficulty):
    """One whole table, in order — which is how a table gets learned."""
    for other in MULTIPLICANDS:
        ask(section, f"{anchor} x {other} = ?", anchor * other,
            strategy(anchor, other), difficulty)


drill("warmup", 2, 1)
drill("warmup", 5, 1)
drill("warmup", 10, 1)

drill("x3-x4", 3, 1)
drill("x3-x4", 4, 2)

drill("x6-x7", 6, 2)
drill("x6-x7", 7, 3)

drill("x8-x9", 8, 3)
drill("x8-x9", 9, 3)

drill("x11-x12", 11, 2)
drill("x11-x12", 12, 3)


# Missing factor. Producing 42 on demand and recognising 42 as six sevens are
# different skills, and the second is the one that makes division click later.
MISSING = [
    (2, 8), (5, 6), (10, 7), (3, 9), (4, 6), (2, 12), (5, 11),
    (6, 7), (7, 8), (6, 9), (8, 9), (7, 7), (4, 8), (3, 12),
    (9, 9), (12, 6), (8, 8), (11, 7), (6, 6), (9, 12), (7, 12), (8, 11),
]
for _a, _b in MISSING:
    ask("missing", f"{_a} x ? = {_a * _b}", _b,
        f"How many {_a}s make {_a * _b}? {_a} x {_b} = {_a * _b}, so the missing number "
        f"is {_b}. Dividing gets there too: {_a * _b} / {_a} = {_b}.",
        2 if _a <= 5 or _b <= 5 else 3)


# The workout: weighted towards the middle of the tables, where no easy pattern
# helps and guesses survive longest. Ordered so no two neighbours share a table.
MIXED = [
    (6, 7), (4, 9), (8, 7), (3, 8), (9, 6), (7, 4), (12, 8), (5, 9),
    (8, 8), (6, 4), (7, 9), (11, 12), (4, 12), (9, 8), (3, 7), (7, 7),
    (6, 8), (12, 9), (9, 9), (8, 4), (6, 6), (7, 11), (12, 12), (9, 3),
    (8, 6), (7, 6),
]
for _a, _b in MIXED:
    ask("mixed", f"{_a} x {_b} = ?", _a * _b, strategy(_a, _b), 3)


# ---------------------------------------------------------------------------
# Lessons — short on purpose. A gym needs coaching cues, not a chapter.
# ---------------------------------------------------------------------------

SECTIONS = [
    {
        "id": "warmup",
        "title": "Warm-Up: 2s, 5s and 10s",
        "emoji": "🏃",
        "color": "#4ECDC4",
        "blurb": "Start here even if you think you know them. The 2, 5 and 10 tables are "
                 "what every other fact is built out of — the 6 table leans on the 5 "
                 "table, the 9 table leans on the 10 table. Make these three automatic "
                 "and the hard tables stop being hard.",
        "key_concepts": [
            "Times {2} is just doubling. 2 x 7 is 7 + 7.",
            "Times {10} moves every digit up one place: 7 becomes 70, 12 becomes 120.",
            "Times {5} is half of times 10. Ten 8s is 80, so five 8s is 40. Every answer "
            "in the 5 table ends in 5 or 0.",
            "Order never changes the answer: 3 x 8 and 8 x 3 are both 24. That roughly "
            "halves how many facts there are to learn.",
        ],
        "examples": [
            {"prompt": "5 x 9", "steps": "Ten 9s is 90. Five is half of ten, so halve 90.",
             "answer_display": "45"},
            {"prompt": "10 x 12", "steps": "Every digit moves up one place, so 12 becomes 120.",
             "answer_display": "120"},
        ],
    },
    {
        "id": "x3-x4",
        "title": "3s and 4s",
        "emoji": "🔁",
        "color": "#6C63FF",
        "blurb": "Both of these come straight out of doubling, so with the warm-up solid "
                 "they follow close behind. Three of something is two of it plus one "
                 "more. Four of something is just double, twice.",
        "key_concepts": [
            "Times {3}: double it, then add one more. 3 x 7 is 14 + 7 = 21.",
            "Times {4}: double, then double again. 4 x 7 goes 7 to 14 to 28.",
            "Every answer in the 4 table is even, and each is double the matching answer "
            "in the 2 table.",
            "A check for the 3 table: add up the digits of the answer and you always "
            "land on 3, 6 or 9. For 24, that's 2 + 4 = 6.",
        ],
        "examples": [
            {"prompt": "3 x 8", "steps": "Double 8 to get 16, then add one more 8: 16 + 8.",
             "answer_display": "24"},
            {"prompt": "4 x 9", "steps": "9 doubles to 18, and 18 doubles to 36.",
             "answer_display": "36"},
        ],
    },
    {
        "id": "x6-x7",
        "title": "6s and 7s",
        "emoji": "🎯",
        "color": "#FF9F43",
        "blurb": "This is where guessing usually starts, because no single trick covers "
                 "the whole table. The way through is to land on the 5 fact first and "
                 "step up from there — and 5 facts you already own.",
        "key_concepts": [
            "Times {6}: take the 5 fact and add one more. Five 8s is 40, so six 8s is 48.",
            "Times {7}: split the 7 into 5 and 2. Five 6s is 30, two 6s is 12, and "
            "30 + 12 = 42.",
            "6 x 7 = 42 is the single most-missed fact there is. Worth memorising on its "
            "own rather than rebuilding it every time.",
            "Every answer in the 6 table is even, so landing on an odd number means "
            "something has gone wrong.",
        ],
        "examples": [
            {"prompt": "6 x 9", "steps": "Five 9s is 45, then add one more 9: 45 + 9.",
             "answer_display": "54"},
            {"prompt": "7 x 8", "steps": "Five 8s is 40, two 8s is 16, and 40 + 16 = 56.",
             "answer_display": "56"},
        ],
    },
    {
        "id": "x8-x9",
        "title": "8s and 9s",
        "emoji": "💪",
        "color": "#FF6B6B",
        "blurb": "These two look like the hardest tables and are secretly among the "
                 "easiest, because both have a shortcut that always works: 8 is doubling "
                 "three times, and 9 is the 10 fact with one taken back off.",
        "key_concepts": [
            "Times {8}: double, double, double. 8 x 6 goes 6 to 12 to 24 to 48.",
            "Times {9}: do the 10 fact, then subtract the number. 9 x 7 is 70 - 7 = 63.",
            "The digits of every 9-table answer add up to 9. 63 gives 6 + 3 = 9, and 45 "
            "gives 4 + 5 = 9. Use it to check yourself.",
            "Up to 9 x 10, the tens digit is one less than the number you multiplied by: "
            "9 x 7 = 63, and 6 is one less than 7.",
        ],
        "examples": [
            {"prompt": "8 x 7", "steps": "7 to 14 to 28 to 56 — three doubles.",
             "answer_display": "56"},
            {"prompt": "9 x 6", "steps": "Ten 6s is 60, take one 6 back off: 60 - 6.",
             "answer_display": "54"},
        ],
    },
    {
        "id": "x11-x12",
        "title": "11s and 12s",
        "emoji": "🚀",
        "color": "#0652DD",
        "blurb": "The 11 table is the easiest one on this page as long as you stay "
                 "single-digit. The 12 table has no trick of its own, but it doesn't "
                 "need one: it's the 10 fact and the 2 fact added together.",
        "key_concepts": [
            "Times {11} up to 9: write the digit twice. 11 x 4 is 44, 11 x 8 is 88.",
            "That stops working at 10. From there, do ten of them plus one more: "
            "11 x 12 is 120 + 12 = 132.",
            "Times {12}: add the 10 fact and the 2 fact. 12 x 7 is 70 + 14 = 84.",
            "12s turn up constantly outside school — a dozen, hours on a clock, inches "
            "in a foot — so they're worth the effort.",
        ],
        "examples": [
            {"prompt": "11 x 7", "steps": "Single digit, so write the 7 twice.",
             "answer_display": "77"},
            {"prompt": "12 x 9", "steps": "Ten 9s is 90, two 9s is 18, and 90 + 18 = 108.",
             "answer_display": "108"},
        ],
    },
    {
        "id": "missing",
        "title": "Find the Missing Number",
        "emoji": "🔍",
        "color": "#10AC84",
        "blurb": "The same facts, asked backwards. Knowing that 6 x 7 is 42 is one "
                 "skill; seeing 42 and recognising it as six sevens is another — and "
                 "it's the one that makes division make sense when you get there.",
        "key_concepts": [
            "Read it as a question. For 6 x ? = 42, ask yourself how many 6s make 42.",
            "If no answer jumps out, divide — dividing undoes multiplying. 42 divided by "
            "6 is 7.",
            "You can also count up in the number you have: 6, 12, 18, 24, 30, 36, 42. "
            "That's seven steps, so the answer is 7. Slower, but it always works.",
            "Check by multiplying back. Put your answer in and see whether it really "
            "makes the number on the right.",
        ],
        "examples": [
            {"prompt": "8 x ? = 56",
             "steps": "How many 8s make 56? 8 x 7 = 56. Check by dividing: 56 / 8 = 7.",
             "answer_display": "7"},
            {"prompt": "9 x ? = 108",
             "steps": "Ten 9s is only 90, so it's more than 10. Twelve 9s is 90 + 18 = 108.",
             "answer_display": "12"},
        ],
    },
    {
        "id": "mixed",
        "title": "Mixed Workout",
        "emoji": "🏆",
        "color": "#FF8B94",
        "blurb": "Every table at once, in no order, weighted towards the facts that get "
                 "missed most. Drilling one table at a time lets you ride the pattern; "
                 "this is where you find out which facts you actually know.",
        "key_concepts": [
            "Having to stop and work one out isn't a failure — it's that fact telling "
            "you it needs another lap.",
            "Speed is the point. A fact you can rebuild in ten seconds isn't memorised "
            "yet, and it will slow you down inside every longer problem later.",
            "Order still helps: if 7 x 12 feels hard, try it as 12 x 7.",
            "Come back to this one. Facts fade if you leave them, and a short workout "
            "now and then beats one long session.",
        ],
        "examples": [
            {"prompt": "7 x 6",
             "steps": "Five 6s is 30, two 6s is 12, so 30 + 12 = 42. Worth knowing "
                      "outright — it's the most-missed fact in the tables.",
             "answer_display": "42"},
            {"prompt": "12 x 12",
             "steps": "Ten 12s is 120, two 12s is 24, and 120 + 24 = 144.",
             "answer_display": "144"},
        ],
    },
]


def main():
    here = Path(__file__).parent
    counts = {s["id"]: sum(1 for q in QUESTIONS if q["section"] == s["id"])
              for s in SECTIONS}

    known = {s["id"] for s in SECTIONS}
    stray = {q["section"] for q in QUESTIONS} - known
    assert not stray, f"questions in unknown sections: {stray}"
    assert len({q["id"] for q in QUESTIONS}) == len(QUESTIONS), "duplicate question id"
    for q in QUESTIONS:
        assert q["answer"]["value"] > 0, q["id"]

    lessons = {
        "meta": {
            "grade": 3,
            "unit": "math-gym",
            "title": "Math Gym",
            "emoji": "🏋️",
            "description": "Multiplication facts from the 2 times table up to the 12s, "
                           "drilled one at a time until they come back without thinking.",
            "sections": [
                {"id": s["id"], "title": s["title"], "emoji": s["emoji"],
                 "question_count": counts[s["id"]]}
                for s in SECTIONS
            ],
        },
        "sections": SECTIONS,
    }

    (here / "lessons.json").write_text(
        json.dumps(lessons, indent=2, ensure_ascii=False), encoding="utf-8")
    (here / "questions.json").write_text(
        json.dumps({"questions": QUESTIONS}, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote {len(SECTIONS)} topics and {len(QUESTIONS)} questions:")
    for s in SECTIONS:
        print(f"  {s['id']:<10} {counts[s['id']]:>3} questions")


if __name__ == "__main__":
    main()
