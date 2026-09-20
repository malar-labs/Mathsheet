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

Three units so far. The first two are the same skill from two directions; the
third is the skill they exist to make possible:

    multiplication-facts   7 x 8
    division-facts         56 / 7
    fraction-addition      1/2 + 1/4

Each is a drill, not a lesson: one table at a time, a page of questions at a
time, the same facts coming round until the answer arrives before the child has
time to count. Every level runs three passes, easiest first:

    skip   the counting ladder, 7, 14, __, 28 — where the chain is learned,
           and the answer key for both times-table units
    equiv  the equivalence ladder, 1/2 = 2/4 = __/6 = 4/8 — the same exercise
           for fractions, where "same amount, more pieces" gets into the hand
    equivpair  the same ladder with the bottom taken away too, __/__ — now you
           have to know what size piece comes next, not just how many
    pick   four options — recognition
    type   nothing to choose from — recall
"""
import json
from math import gcd
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
    return (f"Take {divisor} away from {dividend} again and again and you land on "
            f"0 after {quotient} jumps, so {dividend} / {divisor} = {quotient}. "
            f"The times table says the same thing: {divisor} x {quotient} = "
            f"{dividend}.")


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
    return (f"How many {divisor}s fit? Take {divisor} away again and again and "
            f"count the jumps, or read the {divisor} times table backwards.")


# ---------------------------------------------------------------------------
# Multiple choice — wrong options a child might actually pick
# ---------------------------------------------------------------------------

def as_number(value):
    """An option's size, whether it is a whole number or an (n, d) fraction."""
    return value if isinstance(value, int) else value[0] / value[1]


def is_usable(value):
    return value[0] > 0 and value[1] > 0 if isinstance(value, tuple) else value > 0


def distractors(answer, near, slot):
    """Three wrong options for `answer`, drawn from the mistakes that actually
    happen — off by one step of either factor, a neighbouring fact, or (for
    fractions) the bottoms added together — rather than random numbers, which a
    child can rule out without knowing the fact."""
    candidates = []
    for value in near:
        if is_usable(value) and value != answer and value not in candidates:
            candidates.append(value)
    size = as_number(answer)
    candidates.sort(key=lambda v: (abs(as_number(v) - size), as_number(v)))
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
    options = sorted(wrong, key=as_number)
    options.insert(slot % 4, answer)
    # A fraction option carries its {a/b} token so the drill stacks it, the same
    # way the prompt is written.
    show = (lambda v: str(v)) if isinstance(answer, int) else ftok
    return [show(v) for v in options], show(answer)


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

    def add_level(self, level_id, title, emoji, items, tip, difficulty,
                  ladder=None):
        section = {
            "id": level_id,
            "title": title,
            "emoji": emoji,
            "color": PALETTE[len(self.sections) % len(PALETTE)],
        }
        self.sections.append(section)

        set_index = 0
        number = 0

        if ladder is not None:
            # The ladder is drawn from the section, not repeated on every blank,
            # so the page can show the whole chain with the answered rungs still
            # in place.
            section["ladder"] = ladder
            chain, mode = ladder["chain"], ladder["mode"]
            step_size = ladder.get("step")
            set_index = 1
            blanks = SKIP_BLANKS if mode != "equiv" else ladder_blanks(len(chain))
            for order, step in enumerate(blanks, start=1):
                if mode == "equiv":
                    # The denominator is printed and only the top is asked for,
                    # so the question is exactly "how many of THESE make it?"
                    base_n, base_d = ladder["base"]
                    num, den = chain[step - 1]
                    times = den // base_d
                    self.questions.append({
                        "id": f"{level_id}-{mode}-{order:02d}",
                        "section": level_id,
                        "set": 1,
                        "mode": mode,
                        "step": step,
                        "qtype": "integer",
                        "kind": "number",
                        "difficulty": 1,
                        "prompt": "{%d/%d} = ?/%d" % (base_n, base_d, den),
                        "answer": {"value": num, "display": str(num)},
                        "steps": (f"{base_d} goes into {den} {times} times, so the "
                                  f"top does the same: {base_n} x {times} = {num}."),
                        "tip": tip,
                    })
                    continue
                value = chain[step - 1]
                before = chain[step - 2]
                if mode == "skip":
                    prompt = f"Count by {step_size}s — number {step}"
                    steps = (f"Keep adding {step_size}. Number {step - 1} is {before}, "
                             f"so number {step} is {before} + {step_size} = {value}. "
                             f"That is the same as {step_size} x {step}.")
                else:
                    prompt = (f"Count back in {step_size}s from {chain[0]} "
                              f"— jump {step}")
                    steps = (f"Keep taking {step_size} away. Jump {step - 1} lands on "
                             f"{before}, so jump {step} is {before} - {step_size} "
                             f"= {value}.")
                self.questions.append({
                    "id": f"{level_id}-{mode}-{order:02d}",
                    "section": level_id,
                    "set": 1,
                    "mode": mode,
                    "step": step,
                    "qtype": "integer",
                    "kind": "number",
                    "difficulty": 1,
                    "prompt": prompt,
                    "answer": {"value": value, "display": str(value)},
                    "steps": steps,
                    "tip": tip,
                })

        # Second pass over the same ladder: the whole rung is blank now.
        if ladder is not None and ladder["mode"] == "equiv":
            set_index = 2
            base_n, base_d = ladder["base"]
            for order, step in enumerate(ladder_blanks(len(chain), second=True),
                                         start=1):
                num, den = chain[step - 1]
                self.questions.append({
                    "id": f"{level_id}-pair-{order:02d}",
                    "section": level_id,
                    "set": 2,
                    "mode": "equivpair",
                    "step": step,
                    "qtype": "equivalent",
                    "kind": "number",
                    "difficulty": 2,
                    "prompt": "{%d/%d} = ?/? — rung %d of the chain" % (base_n, base_d, step),
                    "answer": {"num": num, "den": den, "display": f"{num}/{den}"},
                    "steps": (f"Rung {step} means {base_n}/{base_d} with the top and the "
                              f"bottom both multiplied by {step}: {base_n} x {step} = {num} "
                              f"and {base_d} x {step} = {den}, so {num}/{den}."),
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
                    elif isinstance(answer, tuple):
                        num, den = answer
                        assert gcd(num, den) == 1, (question["id"], answer)
                        question["qtype"] = "fraction"
                        question["answer"] = {"num": num, "den": den, "whole": 0,
                                              "display": fdisp(answer)}
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
            elif q["qtype"] == "fraction":
                assert q["answer"]["den"] > 0 and q["answer"]["num"] > 0, q["id"]
                assert gcd(q["answer"]["num"], q["answer"]["den"]) == 1, q["id"]
            elif q["qtype"] == "equivalent":
                # 4/8 is the whole point here, so this one is NOT reduced.
                assert q["answer"]["den"] > 0 and q["answer"]["num"] > 0, q["id"]
            elif q["mode"] == "back":
                # A count-back chain finishes on 0, which is the whole point.
                assert q["answer"]["value"] >= 0, q["id"]
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
            ladder={"mode": "skip", "step": table,
                    "chain": [table * n for n in range(1, 13)]},
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
    )
    return unit.finish()


# ---------------------------------------------------------------------------
# Division
# ---------------------------------------------------------------------------

def build_division():
    unit = Unit(
        "division-facts", "Division Facts", "➗",
        "How many 7s make 56? Take 7 away again and again, count the jumps, and "
        "the answer falls out.",
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
            # Counting up is the multiplication tool. Dividing is taking away
            # until nothing is left, so this ladder runs the other way: start at
            # the whole amount and subtract to 0. The number of jumps IS the
            # answer, which is the thing worth seeing.
            ladder={"mode": "back", "step": divisor,
                    "chain": [divisor * n for n in range(12, -1, -1)]},
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
    )
    return unit.finish()


# ---------------------------------------------------------------------------
# Fraction addition
# ---------------------------------------------------------------------------
#
# Skip counting is the gym exercise behind multiplication. The one behind adding
# fractions is equivalence: seeing instantly that 1/2 and 3/6 are the same
# amount cut differently. Everything else in a fraction sum is bookkeeping.
#
# So this unit drills the sequence in the order the muscle actually builds:
#
#   1  equivalence   1/2 = 2/4 = 3/6 = 4/8 ...   the ladder, same as skip counting
#   2  make them match   1/3 + 1/6 -> thirds into sixths
#   3  add the tops      2/6 + 1/6 = 3/6          once the pieces are one size
#   4  tidy up           3/6 -> 1/2
#   5  all four at once  1/2 + 1/4 = ?
#
# That sequence is carried by the order the levels are declared in, not by
# headings over them: the unit reads as one flat list of levels, the same as the
# two times-table units beside it.
#
# Stages 1-3 ask for a single number with the denominator already printed, so
# the drill stays on the one move being practised. Only stages 4 and 5 ask for a
# whole fraction, because by then writing one IS the skill.

def ladder_blanks(rungs, second=False):
    """Which rungs of an equivalence ladder are blank.

    The first two are always given, the way SKIP_BLANKS gives them, so the
    pattern is visible before anything is asked. After that the two passes take
    alternate rungs — the second page is a different question, not the first one
    again with more typing.
    """
    rest = list(range(3, rungs + 1))
    return rest[1::2] if second else rest[0::2]


def ftok(pair):
    """{a/b} — the token the drill renders as a stacked fraction."""
    return "{%d/%d}" % pair


def fdisp(pair):
    n, d = pair
    return str(n) if d == 1 else f"{n}/{d}"


def lcm(a, b):
    return a * b // gcd(a, b)


def near_num(answer, den):
    """Plausible wrong numerators: a step either way, or the denominator itself
    — which is what a child writes when they lose track of what they are
    counting."""
    return [answer - 1, answer + 1, answer + 2, answer - 2, answer + 3,
            den, den - answer, answer * 2, den + answer, 2 * answer + 1]


# ---------------------------------------------------------------------------
# Level 1-3 — equivalence ladders
# ---------------------------------------------------------------------------

def equiv_items(rows):
    """`rows` are (from_pair, to_den, answer) — "3/6 = ?/12" and its 6."""
    items = []
    for pair, den, answer in rows:
        n, d = pair
        times = den // d
        items.append((
            f"{ftok(pair)} = ?/{den}",
            answer,
            near_num(answer, den),
            f"{d} goes into {den} {times} times, so multiply the top by {times} "
            f"as well: {n} x {times} = {answer}. {n}/{d} = {answer}/{den} — the "
            f"same amount, cut into more pieces.",
        ))
    return items


def equiv_level(unit, level_id, title, emoji, base, rungs, rows, tip, difficulty):
    n, d = base
    unit.add_level(
        level_id, title, emoji, equiv_items(rows), tip, difficulty,
        ladder={"mode": "equiv", "base": [n, d],
                "chain": [[n * k, d * k] for k in range(1, rungs + 1)]},
    )


# ---------------------------------------------------------------------------
# The unit
# ---------------------------------------------------------------------------

def build_fraction_addition():
    unit = Unit(
        "fraction-addition", "Fraction Addition", "🍕",
        "Halves into sixths without stopping to think. Equivalence first, then "
        "matching the bottoms, adding the tops, and tidying up — one short page "
        "at a time.",
    )

    # --- 1. equivalence ladders --------------------------------------------
    # One written fraction to a page, all the way down. A page that starts some
    # questions from 1/3 and others from 2/6 is asking a child who is still
    # learning what a third looks like to read two of them at once — even though
    # they are the same amount. Reading a fraction backwards (3/9 is a third) is
    # the Tidy It Up level's job, not this one's.
    equiv_level(
        unit, "eq-half", "Halves", "🌗", (1, 2), 8,
        [((1, 2), 4, 2), ((1, 2), 6, 3), ((1, 2), 8, 4),
         ((1, 2), 10, 5), ((1, 2), 12, 6), ((1, 2), 14, 7),
         ((1, 2), 16, 8), ((1, 2), 18, 9), ((1, 2), 20, 10),
         ((1, 2), 22, 11), ((1, 2), 24, 12), ((1, 2), 26, 13)],
        "Half is always the top being exactly half the bottom. If the bottom "
        "doubles, so does the top.",
        1,
    )
    equiv_level(
        unit, "eq-third", "Thirds", "🥧", (1, 3), 8,
        # A page of 1/3, then a page of 2/3.
        [((1, 3), 6, 2), ((1, 3), 9, 3), ((1, 3), 12, 4),
         ((1, 3), 15, 5), ((1, 3), 18, 6), ((1, 3), 21, 7),
         ((2, 3), 6, 4), ((2, 3), 9, 6), ((2, 3), 12, 8),
         ((2, 3), 15, 10), ((2, 3), 18, 12), ((2, 3), 21, 14)],
        "Thirds live in every bottom number that 3 divides into: 6, 9, 12, 15, 18.",
        2,
    )
    equiv_level(
        unit, "eq-quarter", "Quarters", "🍰", (1, 4), 8,
        # A page of 1/4, then a page of 3/4. (2/4 is left out — that is a half.)
        [((1, 4), 8, 2), ((1, 4), 12, 3), ((1, 4), 16, 4),
         ((1, 4), 20, 5), ((1, 4), 24, 6), ((1, 4), 28, 7),
         ((3, 4), 8, 6), ((3, 4), 12, 9), ((3, 4), 16, 12),
         ((3, 4), 20, 15), ((3, 4), 24, 18), ((3, 4), 28, 21)],
        "Quarters are halves halved. Every quarter bottom — 8, 12, 16, 20 — is 4 "
        "times something.",
        2,
    )

    # --- 2. make the bottoms match -----------------------------------------
    fits = [((1, 2), (1, 4)), ((1, 3), (1, 6)), ((1, 2), (1, 6)), ((1, 4), (1, 8)),
            ((2, 3), (1, 6)), ((1, 2), (3, 8)), ((1, 5), (3, 10)), ((3, 4), (1, 8)),
            ((1, 2), (1, 10)), ((2, 5), (1, 10)), ((1, 3), (1, 12)), ((1, 6), (1, 12))]
    items = []
    for (a, b), (c, d) in fits:
        times = d // b
        answer = a * times
        items.append((
            f"{ftok((a, b))} + {ftok((c, d))} — write {ftok((a, b))} as ?/{d}",
            answer,
            near_num(answer, d),
            f"{b} fits into {d} {times} times, so the top goes up by the same "
            f"{times}: {a} x {times} = {answer}. Now it reads "
            f"{answer}/{d} + {c}/{d}, two piles of the same size piece.",
        ))
    unit.add_level(
        "match-fit", "One Bottom Fits the Other", "🔁", items,
        "Check the bigger bottom first: if the smaller one divides into it, that "
        "is the size you want, and only one fraction has to change.",
        2,
    )

    pairs = [((1, 2), (1, 3)), ((1, 3), (1, 4)), ((1, 2), (1, 5)), ((1, 4), (1, 6)),
             ((1, 6), (1, 8)), ((1, 3), (1, 5)), ((1, 4), (1, 5)), ((1, 6), (1, 9)),
             ((1, 2), (1, 7)), ((1, 3), (1, 8)), ((1, 4), (1, 10)), ((1, 2), (1, 9))]
    items = []
    for (a, b), (c, d) in pairs:
        answer = lcm(b, d)
        items.append((
            f"{ftok((a, b))} + {ftok((c, d))} — what bottom do they both fit into?",
            answer,
            # b + d is the answer to the question a child asks instead: the
            # bottoms get added, which is the mistake worth showing.
            [b * d, b + d, answer + 2, answer - 2, answer + 1, answer - 1, d * 2, b * 2],
            f"Count up in {b}s and in {d}s until both land on the same number: "
            f"{answer} is the first one they share. Bottoms are never added — "
            f"{b} + {d} would be {b + d}, which is not a size either fraction is "
            f"cut into.",
        ))
    unit.add_level(
        "match-lcm", "Find the Common Bottom", "🎯", items,
        "Count up in the bigger bottom — 8, 16, 24 — until you hit a number the "
        "smaller one divides into. That is the first one they share.",
        3,
    )

    # --- 3. add the tops ----------------------------------------------------
    sums = [(2, 1, 6), (1, 1, 4), (3, 1, 8), (3, 2, 10), (1, 5, 12), (2, 4, 9),
            (5, 4, 12), (1, 4, 6), (3, 1, 5), (2, 5, 8), (7, 2, 12), (1, 1, 3)]
    items = []
    for a, c, d in sums:
        answer = a + c
        items.append((
            f"{ftok((a, d))} + {ftok((c, d))} = ?/{d}",
            answer,
            near_num(answer, d),
            f"The pieces are already the same size, so only the tops are counted: "
            f"{a} + {c} = {answer}. The bottom stays {d} — you are still counting "
            f"the same size piece, just more of them.",
        ))
    unit.add_level(
        "same-bottom", "Same Bottom, Add the Tops", "➕", items,
        "Once the bottoms match, the bottom is finished. Add the tops and leave "
        "it alone.",
        1,
    )

    # --- 4. tidy up ---------------------------------------------------------
    raws = [(3, 6), (2, 4), (6, 8), (2, 6), (4, 6), (6, 9),
            (3, 9), (4, 12), (8, 12), (5, 10), (2, 10), (9, 12)]
    items = []
    for n, d in raws:
        g = gcd(n, d)
        answer = (n // g, d // g)
        near = [(n, d), (d // g, n // g), (answer[0] + 1, answer[1]),
                (answer[0], answer[1] + 1)]
        if n % 2 == 0 and d % 2 == 0 and g > 2:
            near.insert(1, (n // 2, d // 2))
        items.append((
            f"{ftok((n, d))} = ?",
            answer,
            near,
            f"{g} divides into both {n} and {d}, so cut both by {g}: "
            f"{n} / {g} = {answer[0]} and {d} / {g} = {answer[1]}. "
            f"{n}/{d} and {fdisp(answer)} are the same amount.",
        ))
    unit.add_level(
        "simplify", "Tidy It Up", "✂️", items,
        "Look for the biggest number that divides into the top AND the bottom, "
        "then cut both by it. Type the tidied fraction, like 1/2.",
        2,
    )

    # --- 5. all four moves at once -----------------------------------------
    adds = [((1, 2), (1, 4)), ((1, 3), (1, 6)), ((2, 3), (1, 6)), ((1, 4), (3, 8)),
            ((1, 2), (1, 3)), ((1, 2), (1, 6)), ((1, 4), (1, 8)), ((2, 5), (1, 10)),
            ((1, 2), (3, 8)), ((1, 3), (1, 4)), ((3, 4), (1, 8)), ((1, 5), (3, 10))]
    unit.add_level(
        "make-them-match", "Make Them Match", "🏁", [add_item(x, y) for x, y in adds],
        "Same bottom? Add the tops. Different bottoms? Make them match first. "
        "Then tidy up. Type the answer as a fraction, like 3/4.",
        3,
    )

    # A lap with no pattern to lean on: any of the four moves, in any order.
    mixed = (
        [("equiv", ((1, 2), 6, 3)), ("equiv", ((2, 3), 12, 8)), ("equiv", ((3, 4), 8, 6))]
        + [("simplify", (4, 8)), ("simplify", (6, 9)), ("simplify", (10, 12))]
        + [("tops", (3, 2, 8)), ("tops", (1, 4, 10)), ("tops", (5, 1, 12))]
        + [("add", ((1, 2), (1, 4))), ("add", ((1, 6), (1, 3))), ("add", ((1, 4), (1, 6)))]
    )
    items = []
    for kind, payload in mixed:
        if kind == "equiv":
            items += equiv_items([payload])
        elif kind == "simplify":
            n, d = payload
            g = gcd(n, d)
            answer = (n // g, d // g)
            items.append((
                f"{ftok((n, d))} = ?", answer,
                [(n, d), (d // g, n // g), (answer[0] + 1, answer[1]),
                 (answer[0], answer[1] + 1)],
                f"Cut the top and the bottom by {g}: {n}/{d} = {fdisp(answer)}.",
            ))
        elif kind == "tops":
            a, c, d = payload
            answer = a + c
            items.append((
                f"{ftok((a, d))} + {ftok((c, d))} = ?/{d}", answer, near_num(answer, d),
                f"Same size pieces already, so add the tops: {a} + {c} = {answer}, "
                f"over {d}.",
            ))
        else:
            items.append(add_item(*payload))
    unit.add_level(
        "mixed", "Mixed Review", "🏆", items,
        "Every move in one lap. Read what the question is actually asking for "
        "before you start writing.",
        3,
    )
    return unit.finish()


def add_item(left, right):
    """One whole sum: match the bottoms, add the tops, tidy up."""
    a, b = left
    c, d = right
    low = lcm(b, d)
    raw = a * (low // b) + c * (low // d)
    g = gcd(raw, low)
    answer = (raw // g, low // g)

    # The wrong answers are the two mistakes that actually happen: adding the
    # bottoms as well as the tops, and stopping before tidying up.
    near = [(a + c, b + d)]
    if (raw, low) != answer:
        near.append((raw, low))
    near += [(answer[0] + 1, answer[1]), (a + c, low), (answer[0], answer[1] + 1)]

    if b == d:
        working = f"The bottoms already match, so add the tops: {a} + {c} = {raw}, over {low}."
    else:
        working = (f"The first bottom they share is {low}, so {a}/{b} = "
                   f"{a * (low // b)}/{low} and {c}/{d} = {c * (low // d)}/{low}. "
                   f"Add the tops: {a * (low // b)} + {c * (low // d)} = {raw}, over {low}.")
    tidy = (f" {raw}/{low} tidies to {fdisp(answer)}." if (raw, low) != answer
            else f" {fdisp(answer)} is already as tidy as it goes.")
    return (f"{ftok(left)} + {ftok(right)} = ?", answer, near, working + tidy)


def main():
    here = Path(__file__).parent
    print("Math Marathon:")
    for unit in (MULTIPLICATION, DIVISION, FRACTION_ADDITION):
        unit.write(here)


MULTIPLICATION = build_multiplication()
DIVISION = build_division()
FRACTION_ADDITION = build_fraction_addition()
UNITS = {unit.slug: unit
         for unit in (MULTIPLICATION, DIVISION, FRACTION_ADDITION)}


if __name__ == "__main__":
    main()
