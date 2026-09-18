"""
One-time content generator for the Grade 3 "Times Tables" unit.

This script is NOT called by the running app. It writes the static lessons.json
and questions.json files that ship with the app; the app only ever reads those
JSON files, and nothing in this feature calls any AI/LLM API.

Re-run with `python _generate.py` from this folder after editing anything below.

This unit is a drill, not a lesson. It is built the way a Kumon worksheet is
built: one table at a time, a page of questions at a time, the same facts coming
round again and again until the answer arrives before the child has time to
count. So there is no lesson page and no reading — you open a level and start.

Two passes per table, because recognising an answer and producing one are
different skills and the easier one has to come first:

    pick   multiple choice, four options — recognition
    type   free text, nothing to choose from — recall

Every table gets both, in that order. Levels run 2, 5, 10 first (the anchors
every other fact is built from), then 3, 4, then 6 through 9, then 11 and 12,
and finish with a mixed review and a missing-number level that ask for the same
facts with no pattern to lean on.

Questions are grouped into sets of 5 or 6 — one page, short enough to finish in
a sitting and see a score for.
"""
import json
from pathlib import Path

# Each table is drilled against these. 0 and 1 are left out: they are rules
# ("anything times 0 is 0"), not facts that need memorising.
MULTIPLICANDS = list(range(2, 13))

# Tables in teaching order, not numeric order: the anchors first.
TABLE_ORDER = [2, 5, 10, 3, 4, 6, 7, 8, 9, 11, 12]

TABLE_EMOJI = {
    2: "✌️", 3: "🔺", 4: "🟦", 5: "🖐️", 6: "🎲", 7: "🌈",
    8: "🎱", 9: "🐈", 10: "🔟", 11: "🎏", 12: "🕛",
}

# Cycled so neighbouring level tiles never share a colour.
PALETTE = ["#4ECDC4", "#6C63FF", "#FF9F43", "#FF6B6B", "#10AC84", "#0652DD", "#FF8B94"]

SET_SIZE = 6


# ---------------------------------------------------------------------------
# Strategies — what a wrong answer explains, in place of a lesson page
# ---------------------------------------------------------------------------

def strategy(anchor, other):
    """How to rebuild `anchor x other` when it hasn't been memorised yet."""
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


TABLE_TIP = {
    2: "Every answer is the number added to itself.",
    3: "Double it, then add one more of the number.",
    4: "Double, then double again. Every answer is even.",
    5: "Half of the 10 fact. Every answer ends in 5 or 0.",
    6: "The 5 fact plus one more. Every answer is even.",
    7: "Split the 7 into 5 and 2, then add the two parts.",
    8: "Double three times. Every answer is even.",
    9: "The 10 fact minus one of the number. The digits of the answer add up to 9.",
    10: "Every digit moves up one place.",
    11: "Write the digit twice, up to 11 x 9. After that, ten of them plus one more.",
    12: "The 10 fact plus the 2 fact.",
}


# ---------------------------------------------------------------------------
# Multiple choice — wrong options a child might actually pick
# ---------------------------------------------------------------------------

def distractors(answer, near, slot):
    """Three wrong options for `answer`, drawn from the mistakes that actually
    happen — off by one step of either factor, or a neighbouring fact — rather
    than random numbers, which a child can rule out without knowing the fact.

    `slot` makes the pick deterministic while stopping every question in a set
    from using the same shape of wrong answer."""
    candidates = []
    for value in near:
        if value > 0 and value != answer and value not in candidates:
            candidates.append(value)
    # Closest first: an option miles away is no test of anything.
    candidates.sort(key=lambda v: (abs(v - answer), v))
    rotated = candidates[slot % 3:] + candidates[:slot % 3]
    return rotated[:3]


def choice_options(answer, near, slot):
    """Four options as strings.

    The answer's slot rotates rather than the options being sorted: distractors
    cluster just above and below the answer, so sorting would park the right
    one in the middle almost every time and a child would learn to never pick
    the ends."""
    wrong = distractors(answer, near, slot)
    assert len(wrong) == 3, (answer, near)
    options = sorted(wrong)
    options.insert(slot % 4, answer)
    return [str(v) for v in options], str(answer)


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------

QUESTIONS = []


# Which rungs of the skip-counting ladder are left blank. The first two are
# given so the pattern is visible before anything is asked, and the rest are
# spread out rather than bunched, so a child has to keep stepping rather than
# reading one number off the one beside it.
SKIP_BLANKS = [3, 5, 6, 8, 10, 12]


def build_skip(level_id, table, tip):
    """The skip-counting ladder: 7, 14, 21 ... with some rungs missing.

    Counting up in a number is how the chain gets learned in the first place,
    and it is the bridge to multiplication — the 3rd number you land on IS
    7 x 3. So it comes before anything else in the level.
    """
    chain = [table * step for step in range(1, 13)]
    for order, step in enumerate(SKIP_BLANKS, start=1):
        value = chain[step - 1]
        QUESTIONS.append({
            "id": f"{level_id}-skip-{order:02d}",
            "section": level_id,
            "set": 1,
            "mode": "skip",
            "step": step,
            "qtype": "integer",
            "kind": "number",
            "difficulty": 1,
            "prompt": f"Count by {table}s — number {step}",
            "answer": {"value": value, "display": str(value)},
            "steps": (f"Keep adding {table}. Number {step - 1} is {chain[step - 2]}, "
                      f"so number {step} is {chain[step - 2]} + {table} = {value}. "
                      f"That is the same as {table} x {step}."),
            "tip": tip,
        })
    return chain


def build_level(level_id, items, tip, difficulty, skip_table=None):
    """Lay a level's facts out as pages of SET_SIZE.

    A table level starts with one skip-counting page, then goes through its
    facts twice: choosing from four options first, typing from nothing second.

    `items` is a list of (prompt, answer, near_misses, steps).
    """
    number = 0
    set_index = 1 if skip_table is not None else 0
    for mode in ("pick", "type"):
        for start in range(0, len(items), SET_SIZE):
            set_index += 1
            for slot, (prompt, answer, near, steps) in enumerate(items[start:start + SET_SIZE]):
                number += 1
                question = {
                    "id": f"{level_id}-{number:03d}",
                    "section": level_id,
                    "set": set_index,
                    "mode": mode,
                    "kind": "number",
                    "difficulty": difficulty,
                    "prompt": prompt,
                    "steps": steps,
                    "tip": tip,
                }
                if mode == "pick":
                    options, correct = choice_options(answer, near, slot)
                    question["qtype"] = "choice"
                    question["options"] = options
                    question["answer"] = {"choice": correct, "display": correct}
                else:
                    question["qtype"] = "integer"
                    question["answer"] = {"value": answer, "display": str(answer)}
                QUESTIONS.append(question)


SECTIONS = []


def add_level(level_id, title, emoji, items, tip, difficulty, blurb, skip_table=None):
    section = {
        "id": level_id,
        "title": title,
        "emoji": emoji,
        "color": PALETTE[len(SECTIONS) % len(PALETTE)],
        "blurb": blurb,
    }
    SECTIONS.append(section)
    # The ladder is drawn from the section, not repeated on every blank, so the
    # page can show the whole chain with the answered rungs still in place.
    if skip_table is not None:
        section["table"] = skip_table
        section["skip_chain"] = build_skip(level_id, skip_table, tip)
    build_level(level_id, items, tip, difficulty, skip_table)


# --- one level per table ---------------------------------------------------

for table in TABLE_ORDER:
    facts = []
    for other in MULTIPLICANDS:
        product = table * other
        near = [
            product - table, product + table,      # one step along this table
            product - other, product + other,      # one step along the other
            product + 1, product - 1,
            product + 10, product - 10,
        ]
        facts.append((f"{table} x {other} = ?", product, near, strategy(table, other)))

    add_level(
        f"t{table}",
        f"{table} Times Table",
        TABLE_EMOJI[table],
        facts,
        TABLE_TIP[table],
        1 if table in (2, 5, 10) else 2 if table in (3, 4, 11) else 3,
        f"Count by {table}s first, then every fact in the {table} times table — "
        f"picked, then typed.",
        skip_table=table,
    )


# --- mixed review ----------------------------------------------------------
# Weighted towards the middle of the tables, where no easy pattern helps and a
# guess survives longest. Ordered so no two neighbours share a table.
MIXED = [
    (6, 7), (4, 9), (8, 7), (3, 8), (9, 6), (7, 4),
    (12, 8), (5, 9), (8, 8), (6, 4), (7, 9), (11, 12),
    (4, 12), (9, 8), (3, 7), (7, 7), (6, 8), (12, 9),
    (9, 9), (8, 4), (6, 6), (7, 11), (12, 12), (9, 3),
    (8, 6), (7, 6), (4, 7), (9, 12), (6, 9), (8, 12),
]
add_level(
    "mixed", "Mixed Review", "🏆",
    [(f"{a} x {b} = ?", a * b,
      [a * b - a, a * b + a, a * b - b, a * b + b, a * b + 1, a * b - 1,
       a * b + 10, a * b - 10],
      strategy(a, b)) for a, b in MIXED],
    "No pattern to lean on here. If you have to work one out, that fact needs "
    "another lap.",
    3,
    "Every table at once, in no order, weighted to the facts that get missed most.",
)


# --- missing number --------------------------------------------------------
# The same facts asked backwards. Producing 42 and recognising 42 as six sevens
# are different skills, and the second is what makes division click later.
MISSING = [
    (2, 8), (5, 6), (10, 7), (3, 9), (4, 6), (2, 12),
    (5, 11), (6, 7), (7, 8), (6, 9), (8, 9), (7, 7),
    (4, 8), (3, 12), (9, 9), (12, 6), (8, 8), (11, 7),
    (6, 6), (9, 12), (7, 12), (8, 11), (12, 9), (9, 4),
]
add_level(
    "missing", "Find the Missing Number", "🔍",
    [(f"{a} x ? = {a * b}", b,
      [b - 1, b + 1, b - 2, b + 2, b + 3, b - 3, 12, 2],
      f"How many {a}s make {a * b}? {a} x {b} = {a * b}, so the missing number is "
      f"{b}. Dividing gets there too: {a * b} / {a} = {b}.")
     for a, b in MISSING],
    "Read it as a question: how many of this make that? If nothing comes to mind, "
    "divide — dividing undoes multiplying.",
    3,
    "The same facts asked backwards, which is what makes division make sense later.",
)


# Stamped here rather than inside main(): the test imports this module without
# running it and compares SECTIONS to the shipped JSON, so anything main() added
# would show up as a mismatch.
for _section in SECTIONS:
    _section["set_count"] = len({q["set"] for q in QUESTIONS
                                 if q["section"] == _section["id"]})


def main():
    here = Path(__file__).parent

    # The engine trusts this data completely, so check it here rather than
    # discovering a bad question in front of a child.
    assert len({q["id"] for q in QUESTIONS}) == len(QUESTIONS), "duplicate question id"
    known = {s["id"] for s in SECTIONS}
    assert {q["section"] for q in QUESTIONS} <= known, "question in an unknown level"
    for q in QUESTIONS:
        if q["qtype"] == "choice":
            assert q["answer"]["choice"] in q["options"], q["id"]
            assert len(q["options"]) == len(set(q["options"])) == 4, q["id"]
        else:
            assert q["answer"]["value"] > 0, q["id"]
        assert 1 <= q["set"], q["id"]

    counts = {s["id"]: sum(1 for q in QUESTIONS if q["section"] == s["id"])
              for s in SECTIONS}
    set_counts = {s["id"]: s["set_count"] for s in SECTIONS}

    lessons = {
        "meta": {
            "grade": 3,
            "unit": "times-tables",
            "engine": "drill",
            "emoji": "✖️",
            "title": "Times Tables",
            "description": "Multiplication facts from the 2 times table up to the 12s. "
                           "Pick the answer first, type it later, one short page at a "
                           "time — until they come back without thinking.",
            "sections": [
                {"id": s["id"], "title": s["title"], "emoji": s["emoji"],
                 "question_count": counts[s["id"]], "set_count": set_counts[s["id"]]}
                for s in SECTIONS
            ],
        },
        "sections": SECTIONS,
    }

    (here / "lessons.json").write_text(
        json.dumps(lessons, indent=2, ensure_ascii=False), encoding="utf-8")
    (here / "questions.json").write_text(
        json.dumps({"questions": QUESTIONS}, indent=2, ensure_ascii=False), encoding="utf-8")

    total_sets = sum(set_counts.values())
    print(f"Wrote {len(SECTIONS)} levels, {total_sets} sets, {len(QUESTIONS)} questions:")
    for s in SECTIONS:
        print(f"  {s['id']:<8} {counts[s['id']]:>4} questions  "
              f"{set_counts[s['id']]:>2} sets")


if __name__ == "__main__":
    main()
