"""
One-time content generator for the Math Marathon units.

This script is NOT called by the running app. It writes the static lessons.json
and questions.json files for every unit under math-marathon/; the app only ever
reads those JSON files, and nothing here runs at request time or calls any
AI/LLM API.

Re-run with `python _generate.py` from this folder after editing anything below.
It writes every unit, so both stay in step.

Math Marathon belongs to no grade. Fact fluency is not something a child
finishes in Grade 3 and never needs again — a Grade 8 student still counting on
their fingers for 7 x 8 is slowed down in every fraction question — so it sits
outside the grade list and anyone can open it.

Two units so far, built the same way because they are the same skill from two
directions:

    multiplication-facts   7 x 8
    division-facts         56 / 7

Each is a drill, not a lesson: one table at a time, a page of questions at a
time, the same facts coming round until the answer arrives before the child has
time to count. Every level runs three passes, easiest first:

    skip   the counting ladder, 7, 14, __, 28 — where the chain is learned,
           and the answer key for both units
    pick   four options — recognition
    type   nothing to choose from — recall
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

# Which rungs of the skip-counting ladder are left blank. The first two are
# given so the pattern is visible before anything is asked, and the rest are
# spread out rather than bunched, so a child has to keep stepping rather than
# reading one number off the one beside it.
SKIP_BLANKS = [3, 5, 6, 8, 10, 12]


# ---------------------------------------------------------------------------
# Strategies — what a wrong answer explains, in place of a lesson page
# ---------------------------------------------------------------------------

def mul_strategy(anchor, other):
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


def div_strategy(divisor, quotient):
    """How to work out `dividend / divisor` from the table you already know."""
    dividend = divisor * quotient
    if divisor == 2:
        return f"Halving: half of {dividend} is {quotient}."
    if divisor == 10:
        return (f"Dividing by 10 moves every digit down one place, so {dividend} "
                f"becomes {quotient}.")
    return (f"Division undoes multiplication. {divisor} x {quotient} = {dividend}, "
            f"so {dividend} / {divisor} = {quotient}. Counting up in {divisor}s, "
            f"{dividend} is the {quotient}th step.")


MUL_TIP = {
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


def div_tip(divisor):
    return (f"Ask how many {divisor}s make the number. The {divisor} times table "
            f"has every answer in it — that is why the ladder comes first.")


# ---------------------------------------------------------------------------
# Multiple choice — wrong options a child might actually pick
# ---------------------------------------------------------------------------

def distractors(answer, near, slot):
    """Three wrong options for `answer`, drawn from the mistakes that actually
    happen — off by one step of either factor, or a neighbouring fact — rather
    than random numbers, which a child can rule out without knowing the fact."""
    candidates = []
    for value in near:
        if value > 0 and value != answer and value not in candidates:
            candidates.append(value)
    candidates.sort(key=lambda v: (abs(v - answer), v))
    rotated = candidates[slot % 3:] + candidates[:slot % 3]
    assert len(rotated) >= 3, (answer, near)
    return rotated[:3]


def choice_options(answer, near, slot):
    """Four options as strings.

    The answer's slot rotates rather than the options being sorted: distractors
    cluster just above and below the answer, so sorting would park the right one
    in the middle almost every time and a child would learn to never pick the
    ends."""
    wrong = distractors(answer, near, slot)
    options = sorted(wrong)
    options.insert(slot % 4, answer)
    return [str(v) for v in options], str(answer)


# ---------------------------------------------------------------------------
# One unit's worth of levels
# ---------------------------------------------------------------------------

class Unit:
    """Accumulates the sections and questions for a single unit."""

    def __init__(self, slug, title, emoji, description):
        self.slug = slug
        self.title = title
        self.emoji = emoji
        self.description = description
        self.sections = []
        self.questions = []

    def add_level(self, level_id, title, emoji, items, tip, difficulty, blurb,
                  ladder_of=None):
        section = {
            "id": level_id,
            "title": title,
            "emoji": emoji,
            "color": PALETTE[len(self.sections) % len(PALETTE)],
            "blurb": blurb,
        }
        self.sections.append(section)

        set_index = 0
        number = 0

        if ladder_of is not None:
            # The ladder is drawn from the section, not repeated on every blank,
            # so the page can show the whole chain with the answered rungs in
            # place. Division gets one too: it IS the answer key for dividing.
            chain = [ladder_of * step for step in range(1, 13)]
            section["table"] = ladder_of
            section["skip_chain"] = chain
            set_index = 1
            for order, step in enumerate(SKIP_BLANKS, start=1):
                value = chain[step - 1]
                self.questions.append({
                    "id": f"{level_id}-skip-{order:02d}",
                    "section": level_id,
                    "set": 1,
                    "mode": "skip",
                    "step": step,
                    "qtype": "integer",
                    "kind": "number",
                    "difficulty": 1,
                    "prompt": f"Count by {ladder_of}s — number {step}",
                    "answer": {"value": value, "display": str(value)},
                    "steps": (f"Keep adding {ladder_of}. Number {step - 1} is "
                              f"{chain[step - 2]}, so number {step} is "
                              f"{chain[step - 2]} + {ladder_of} = {value}. That is "
                              f"the same as {ladder_of} x {step}."),
                    "tip": tip,
                })

        for mode in ("pick", "type"):
            for start in range(0, len(items), SET_SIZE):
                set_index += 1
                for slot, (prompt, answer, near, steps) in enumerate(
                        items[start:start + SET_SIZE]):
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
                    self.questions.append(question)

    def finish(self):
        for section in self.sections:
            section["set_count"] = len({q["set"] for q in self.questions
                                        if q["section"] == section["id"]})
        return self

    def write(self, here):
        counts = {s["id"]: sum(1 for q in self.questions if q["section"] == s["id"])
                  for s in self.sections}

        assert len({q["id"] for q in self.questions}) == len(self.questions), self.slug
        known = {s["id"] for s in self.sections}
        assert {q["section"] for q in self.questions} <= known, self.slug
        for q in self.questions:
            if q["qtype"] == "choice":
                assert q["answer"]["choice"] in q["options"], q["id"]
                assert len(q["options"]) == len(set(q["options"])) == 4, q["id"]
            else:
                assert q["answer"]["value"] > 0, q["id"]

        lessons = {
            "meta": {
                "unit": self.slug,
                "engine": "drill",
                "emoji": self.emoji,
                "title": self.title,
                "description": self.description,
                "sections": [
                    {"id": s["id"], "title": s["title"], "emoji": s["emoji"],
                     "question_count": counts[s["id"]], "set_count": s["set_count"]}
                    for s in self.sections
                ],
            },
            "sections": self.sections,
        }

        folder = here / self.slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "lessons.json").write_text(
            json.dumps(lessons, indent=2, ensure_ascii=False), encoding="utf-8")
        (folder / "questions.json").write_text(
            json.dumps({"questions": self.questions}, indent=2, ensure_ascii=False),
            encoding="utf-8")

        sets = sum(s["set_count"] for s in self.sections)
        print(f"  {self.slug:<22} {len(self.sections):>3} levels  {sets:>3} pages  "
              f"{len(self.questions):>4} questions")


def near_misses(value, a, b):
    """Plausible wrong answers: one step along either factor, or next door."""
    return [value - a, value + a, value - b, value + b,
            value + 1, value - 1, value + 10, value - 10]


# ---------------------------------------------------------------------------
# Multiplication
# ---------------------------------------------------------------------------

def build_multiplication():
    unit = Unit(
        "multiplication-facts", "Multiplication Facts", "✖️",
        "Every fact from the 2 times table up to the 12s. Count up the ladder, "
        "pick the answer, then type it — one short page at a time.",
    )

    for table in TABLE_ORDER:
        facts = [
            (f"{table} x {other} = ?", table * other,
             near_misses(table * other, table, other), mul_strategy(table, other))
            for other in MULTIPLICANDS
        ]
        unit.add_level(
            f"t{table}", f"{table} Times Table", TABLE_EMOJI[table], facts,
            MUL_TIP[table],
            1 if table in (2, 5, 10) else 2 if table in (3, 4, 11) else 3,
            f"Count by {table}s first, then every fact in the {table} times table — "
            f"picked, then typed.",
            ladder_of=table,
        )

    mixed = [
        (6, 7), (4, 9), (8, 7), (3, 8), (9, 6), (7, 4),
        (12, 8), (5, 9), (8, 8), (6, 4), (7, 9), (11, 12),
        (4, 12), (9, 8), (3, 7), (7, 7), (6, 8), (12, 9),
        (9, 9), (8, 4), (6, 6), (7, 11), (12, 12), (9, 3),
        (8, 6), (7, 6), (4, 7), (9, 12), (6, 9), (8, 12),
    ]
    unit.add_level(
        "mixed", "Mixed Review", "🏆",
        [(f"{a} x {b} = ?", a * b, near_misses(a * b, a, b), mul_strategy(a, b))
         for a, b in mixed],
        "No pattern to lean on here. If you have to work one out, that fact needs "
        "another lap.",
        3,
        "Every table at once, in no order, weighted to the facts that get missed most.",
    )

    missing = [
        (2, 8), (5, 6), (10, 7), (3, 9), (4, 6), (2, 12),
        (5, 11), (6, 7), (7, 8), (6, 9), (8, 9), (7, 7),
        (4, 8), (3, 12), (9, 9), (12, 6), (8, 8), (11, 7),
        (6, 6), (9, 12), (7, 12), (8, 11), (12, 9), (9, 4),
    ]
    unit.add_level(
        "missing", "Find the Missing Number", "🔍",
        [(f"{a} x ? = {a * b}", b, [b - 1, b + 1, b - 2, b + 2, b + 3, b - 3, 12, 2],
          f"How many {a}s make {a * b}? {a} x {b} = {a * b}, so the missing number "
          f"is {b}. Dividing gets there too: {a * b} / {a} = {b}.")
         for a, b in missing],
        "Read it as a question: how many of this make that? If nothing comes to "
        "mind, divide — dividing undoes multiplying.",
        3,
        "The same facts asked backwards, which is what makes division make sense later.",
    )
    return unit.finish()


# ---------------------------------------------------------------------------
# Division
# ---------------------------------------------------------------------------

def build_division():
    unit = Unit(
        "division-facts", "Division Facts", "➗",
        "The times tables read backwards — how many 7s make 56? Same ladder, same "
        "facts, asked the other way round.",
    )

    for divisor in TABLE_ORDER:
        facts = []
        for quotient in MULTIPLICANDS:
            dividend = divisor * quotient
            facts.append((
                f"{dividend} / {divisor} = ?", quotient,
                # Wrong answers here are neighbouring quotients, which is what a
                # child lands on when they miscount the ladder by a step.
                [quotient - 1, quotient + 1, quotient - 2, quotient + 2,
                 quotient + 3, quotient - 3, 12, 2],
                div_strategy(divisor, quotient),
            ))
        unit.add_level(
            f"d{divisor}", f"Divide by {divisor}", TABLE_EMOJI[divisor], facts,
            div_tip(divisor),
            1 if divisor in (2, 5, 10) else 2 if divisor in (3, 4, 11) else 3,
            f"Count by {divisor}s first — that ladder is the answer key — then "
            f"divide by {divisor}, picked and then typed.",
            ladder_of=divisor,
        )

    mixed = [
        (7, 6), (9, 4), (7, 8), (8, 3), (6, 9), (4, 7),
        (8, 12), (9, 5), (8, 8), (4, 6), (9, 7), (12, 11),
        (12, 4), (8, 9), (7, 3), (7, 7), (8, 6), (9, 12),
        (9, 9), (4, 8), (6, 6), (11, 7), (12, 12), (3, 9),
        (6, 8), (6, 7), (7, 4), (12, 9), (9, 6), (12, 8),
    ]
    unit.add_level(
        "mixed", "Mixed Review", "🏆",
        [(f"{d * q} / {d} = ?", q,
          [q - 1, q + 1, q - 2, q + 2, q + 3, q - 3, 12, 2], div_strategy(d, q))
         for d, q in mixed],
        "No single table to lean on here. If you have to work one out, that fact "
        "needs another lap.",
        3,
        "Every divisor at once, in no order, weighted to the facts that get missed most.",
    )

    # Both blanks a division sentence can have. Finding the dividend is the one
    # that catches children out, because it is multiplying in disguise.
    missing = [
        (2, 8), (5, 6), (10, 7), (3, 9), (4, 6), (2, 12),
        (5, 11), (6, 7), (7, 8), (6, 9), (8, 9), (7, 7),
        (4, 8), (3, 12), (9, 9), (12, 6), (8, 8), (11, 7),
        (6, 6), (9, 12), (7, 12), (8, 11), (12, 9), (9, 4),
    ]
    items = []
    for index, (d, q) in enumerate(missing):
        dividend = d * q
        if index % 2 == 0:
            items.append((
                f"{dividend} / ? = {q}", d,
                [d - 1, d + 1, d - 2, d + 2, d + 3, d - 3, 12, 2],
                f"What do you divide {dividend} by to get {q}? {d} x {q} = "
                f"{dividend}, so the missing number is {d}.",
            ))
        else:
            items.append((
                f"? / {d} = {q}", dividend,
                near_misses(dividend, d, q),
                f"Which number gives {q} when you split it into {d}s? {d} x {q} = "
                f"{dividend}, so the missing number is {dividend}.",
            ))
    unit.add_level(
        "missing", "Find the Missing Number", "🔍", items,
        "Multiply to check. Whatever you put in, the sentence has to come out true.",
        3,
        "The blank moves around: sometimes the number being divided, sometimes what "
        "you divide it by.",
    )
    return unit.finish()


def main():
    here = Path(__file__).parent
    print("Math Marathon:")
    for unit in (MULTIPLICATION, DIVISION):
        unit.write(here)


MULTIPLICATION = build_multiplication()
DIVISION = build_division()
UNITS = {unit.slug: unit for unit in (MULTIPLICATION, DIVISION)}


if __name__ == "__main__":
    main()
