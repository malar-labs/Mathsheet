"""
One-time content generator for the Grade 8 "Fractions" unit.

This script is NOT called by the running app — it was used once (by Claude,
from a curriculum prompt + a sample worksheet PDF the teacher provided) to
produce the static lessons.json and questions.json files that ship with the
app. The app only ever reads those JSON files; nothing here runs at request
time and nothing in this feature calls any AI/LLM API.

Re-run with `python3 _generate.py` from this folder if you ever want to
regenerate the files (e.g. after editing the question list below).
Every answer is computed with Python's exact `fractions`/`math.gcd`, so the
math is guaranteed correct instead of hand-typed.
"""
import json
from math import gcd


# ---------------------------------------------------------------------------
# Fraction helpers — all answers are derived from these, never hand-typed.
# ---------------------------------------------------------------------------

def lcm(a, b):
    return a * b // gcd(a, b)


def analyze(raw_n, raw_d, context="answer"):
    """Describe a raw (unreduced, possibly improper) positive fraction.

    Returns the reduced form, whether reduction was needed, whether the
    reduced form is improper, its mixed-number breakdown, a display string,
    and a ready-to-show "mandatory tip" paragraph covering exactly the two
    checks Claude was asked to always include: does it need reducing, and
    does an improper result need converting to a mixed number.
    """
    assert raw_d > 0 and raw_n >= 0
    g = gcd(raw_n, raw_d) if raw_n else raw_d
    red_n, red_d = raw_n // g, raw_d // g
    needs_reduction = g != 1

    if red_d == 1:
        whole, num, den = red_n, 0, 1
        is_improper = False
        display = str(red_n)
    else:
        is_improper = red_n > red_d
        if is_improper:
            whole = red_n // red_d
            num = red_n % red_d
            den = red_d
            display = f"{whole} {num}/{den}" if num else str(whole)
        else:
            whole, num, den = 0, red_n, red_d
            display = f"{num}/{den}"

    tip_parts = []
    if needs_reduction:
        tip_parts.append(
            f"Reduce first: your raw {context} is {raw_n}/{raw_d}. "
            f"GCD({raw_n}, {raw_d}) = {g}, so divide top and bottom by {g} "
            f"to get {red_n}/{red_d}."
        )
    else:
        tip_parts.append(
            f"Check for reducing: GCD({raw_n}, {raw_d}) = 1, so {raw_n}/{raw_d} "
            f"is already in simplest form."
        )
    if den == 1:
        tip_parts.append("It actually simplifies all the way down to a whole number.")
    elif is_improper:
        tip_parts.append(
            f"Check for improper form: {red_n}/{red_d} is improper (top ≥ bottom), "
            f"so convert it to the mixed number {display}."
        )
    else:
        tip_parts.append(
            f"Check for improper form: {red_n}/{red_d} is proper (top < bottom), "
            f"so it's already in final form — no mixed number needed."
        )

    return {
        "raw_num": raw_n, "raw_den": raw_d, "gcd": g,
        "needs_reduction": needs_reduction,
        "num": num, "den": den, "whole": whole,
        "is_improper": is_improper,
        "display": display,
        "tip": " ".join(tip_parts),
    }


def frac_tok(n, d):
    return str(n) if d == 1 else f"{{{n}/{d}}}"


def mixed_tok(w, n, d):
    if w == 0:
        return frac_tok(n, d)
    if n == 0:
        return str(w)
    return f"{{{w}_{n}/{d}}}"


def to_improper(w, n, d):
    return w * d + n, d


def combine(op, n1, d1, n2, d2):
    """Add or subtract two fractions via the LCM of their denominators. Returns (raw_num, L, steps)."""
    if d1 == d2:
        raw = n1 + n2 if op == "+" else n1 - n2
        steps = (
            f"Same denominator ({d1}) — just {'add' if op == '+' else 'subtract'} the "
            f"numerators: {n1} {op} {n2} = {raw}, keep the denominator: {raw}/{d1}."
        )
        return raw, d1, steps
    L = lcm(d1, d2)
    f1, f2 = n1 * (L // d1), n2 * (L // d2)
    raw = f1 + f2 if op == "+" else f1 - f2
    steps = (
        f"Find the LCM of the denominators {d1} and {d2} → {L}. "
        f"Rewrite: {n1}/{d1} = {f1}/{L} and {n2}/{d2} = {f2}/{L}. "
        f"{'Add' if op == '+' else 'Subtract'}: {f1} {op} {f2} = {raw} → {raw}/{L}."
    )
    return raw, L, steps


def qid(section, n):
    return f"{section}-{n:02d}"


# ---------------------------------------------------------------------------
# Question bank
# ---------------------------------------------------------------------------

sections = []


def add_section(sid, title, emoji, color, blurb, key_concepts, examples, questions):
    sections.append({
        "id": sid, "title": title, "emoji": emoji, "color": color,
        "blurb": blurb, "key_concepts": key_concepts, "examples": examples,
        "questions": questions,
    })


# ===== 1. INTRO — What is a fraction? ======================================
intro_q = []


def add_identify(n, stars, prompt, raw_n, raw_d):
    a = analyze(raw_n, raw_d, context="fraction")
    intro_q.append({
        "id": qid("intro", n), "section": "intro", "qtype": "fraction",
        "difficulty": stars, "prompt": prompt,
        "answer": {"num": a["num"], "den": a["den"], "whole": a["whole"], "display": a["display"]},
        "steps": f"{raw_n} out of {raw_d} equal parts → {raw_n}/{raw_d}." + (
            f" Simplify: {a['tip']}" if a["needs_reduction"] or a["is_improper"] else ""
        ),
        "tip": a["tip"],
    })


add_identify(1, 1, "A pizza is cut into {4} equal slices. You eat {1} slice. What fraction of the pizza did you eat?", 1, 4)
add_identify(2, 1, "A chocolate bar has {6} equal pieces. Your friend eats {2} pieces. What fraction of the bar did they eat?", 2, 6)
add_identify(3, 1, "A pizza is cut into {8} slices. After the party, {5} slices are left. What fraction of the pizza is LEFT?", 5, 8)
add_identify(4, 2, "A box has {12} cupcakes. {9} of them have sprinkles. What fraction of the cupcakes do NOT have sprinkles?", 3, 12)
add_identify(5, 2, "Two identical pizzas are each cut into {6} slices ({12} slices total). You eat {9} of the {12} slices. What fraction of all the pizza did you eat?", 9, 12)
add_identify(6, 2, "You have {2} identical granola bars, each cut into {5} pieces ({10} pieces total). You eat {7} pieces. What fraction of all the pieces did you eat?", 7, 10)
add_identify(7, 3, "A pizza is cut into {6} slices. Between two pizzas, you and your friends finish {10} slices in total. What fraction of ONE whole pizza's worth of slices did you eat? (Hint: your answer can be more than 1 whole!)", 10, 6)
add_identify(8, 3, "A sandwich is cut into {8} equal pieces. Friends eat {9} pieces in total (from more than one sandwich). What fraction of ONE whole sandwich's worth did they eat?", 9, 8)

add_section(
    "intro", "What Is a Fraction?", "🍕", "#FF6B6B",
    "A fraction tells you how many equal parts you have out of a whole. The bottom "
    "number (denominator) says how many equal parts the whole is cut into. The top "
    "number (numerator) says how many of those parts you're talking about — like "
    "slices of a pizza!",
    [
        "The denominator (bottom) = how many equal parts make up the WHOLE thing.",
        "The numerator (top) = how many of those parts you actually have.",
        "If the numerator is bigger than the denominator, you have MORE than one whole — that's an improper fraction, and it can be rewritten as a mixed number.",
    ],
    [
        {
            "prompt": "A pizza is cut into {8} equal slices. You eat {3} of them. What fraction did you eat?",
            "steps": "3 slices out of 8 total slices → 3/8. GCD(3,8) = 1, so it's already in simplest form, and 3 < 8 so it's already proper.",
            "answer_display": "3/8",
        },
        {
            "prompt": "A pan of brownies is cut into {9} pieces. {6} pieces get eaten. What fraction is eaten?",
            "steps": "6 out of 9 → 6/9. GCD(6,9) = 3, so reduce: 6/9 = 2/3.",
            "answer_display": "2/3",
        },
    ],
    intro_q,
)

# ===== 2. COMPARE ============================================================
compare_q = []


def compare_fracs(n1, d1, n2, d2):
    """Return (symbol, steps) comparing n1/d1 with n2/d2 via the LCM of the denominators."""
    L = lcm(d1, d2)
    c1, c2 = n1 * (L // d1), n2 * (L // d2)
    symbol = ">" if c1 > c2 else ("<" if c1 < c2 else "=")
    if d1 == d2:
        steps = (
            f"Same denominator ({d1}), so just compare numerators: "
            f"{n1} vs {n2} → {n1}/{d1} {symbol} {n2}/{d2}."
        )
    else:
        steps = (
            f"LCM of the denominators {d1} and {d2} is {L}. Rewrite: {n1}/{d1} = {c1}/{L} and {n2}/{d2} = {c2}/{L}. "
            f"Compare numerators: {c1} vs {c2} → {n1}/{d1} {symbol} {n2}/{d2}."
        )
    return symbol, steps


def add_compare(n, stars, n1, d1, n2, d2):
    symbol, steps = compare_fracs(n1, d1, n2, d2)
    compare_q.append({
        "id": qid("compare", n), "section": "compare", "qtype": "compare", "kind": "number",
        "difficulty": stars,
        "prompt": f"Which sign goes between {frac_tok(n1, d1)} and {frac_tok(n2, d2)}?  (< , > , or =)",
        "answer": {"symbol": symbol, "display": symbol},
        "steps": steps,
        "tip": "You can only compare numerators once both fractions share the same denominator — find the LCM of the denominators first, rewrite both fractions with it, then compare the tops.",
    })


def add_compare_word(n, stars, prompt, name1, n1, d1, name2, n2, d2, asks="more", leftover=False):
    """Word problem: pick which person has more/less (or 'Same').

    With leftover=True the story gives the part used up, and the question is
    about what is LEFT, so each fraction is first subtracted from 1 whole.
    """
    steps = ""
    if leftover:
        steps = (
            f"First find what is left: {name1}: 1 − {n1}/{d1} = {d1 - n1}/{d1}. "
            f"{name2}: 1 − {n2}/{d2} = {d2 - n2}/{d2}.\n"
        )
        n1, n2 = d1 - n1, d2 - n2
    symbol, cmp_steps = compare_fracs(n1, d1, n2, d2)
    if symbol == "=":
        choice = "Same"
    elif (symbol == ">") == (asks == "more"):
        choice = name1
    else:
        choice = name2
    conclusion = (
        "The fractions are equal, so the answer is: the same."
        if choice == "Same" else
        f"The question asks for the {'BIGGER' if asks == 'more' else 'SMALLER'} fraction, so the answer is {choice}."
    )
    compare_q.append({
        "id": qid("compare", n), "section": "compare", "qtype": "choice", "kind": "word",
        "difficulty": stars,
        "prompt": prompt,
        "options": [name1, name2, "Same"],
        "answer": {"choice": choice, "display": choice},
        "steps": steps + cmp_steps + "\n" + conclusion,
        "tip": "Find the two fractions in the story, compare them (use the LCM of the denominators), then read the question again — does it ask for MORE or LESS?",
    })


# --- Kid-friendly visuals for the key concepts (drawn by unit_learning.js) ---

def pizzas_visual(n1, d1, n2, d2):
    symbol, _ = compare_fracs(n1, d1, n2, d2)
    big, small = max(n1, n2), min(n1, n2)
    return {
        "type": "pizzas",
        "items": [{"n": n1, "d": d1}, {"n": n2, "d": d2}],
        "sign": symbol,
        "caption": (
            f"Both pizzas are cut into {d1} same-size slices. {big} slices is more than "
            f"{small} slices, so {frac_tok(n1, d1)} {symbol} {frac_tok(n2, d2)}."
        ),
    }


def lcm_pizzas_visual(n1, d1, n2, d2):
    """Pizzas with different slice sizes → find the LCM of the denominators → re-cut into same-size slices."""
    L = lcm(d1, d2)
    c1, c2 = n1 * (L // d1), n2 * (L // d2)
    symbol, _ = compare_fracs(n1, d1, n2, d2)
    cuts = [
        f"every slice of the {which} pizza into {L // d}"
        for which, d in (("first", d1), ("second", d2)) if d != L
    ]
    rewrites = [
        f"{frac_tok(n, d)} = {frac_tok(c, L)}"
        for n, d, c in ((n1, d1, c1), (n2, d2, c2)) if d != L
    ]
    def multiples(d):
        # multiples of d up to the LCM plus one more; the LCM is wrapped as {L} so it shows in bold
        out, m = [], d
        while m <= L:
            out.append(f"{{{m}}}" if m == L else str(m))
            m += d
        return ", ".join(out + [str(m), "…"])

    return {
        "type": "pizzas",
        "rows": [
            {
                "note": (
                    f"Step 1: the first pizza is cut into {d1} slices and the second into {d2} slices, "
                    f"so the slices are NOT the same size 🤔 Counting slices won't work yet — "
                    f"first we need the same denominator (same-size slices)."
                ),
                "items": [{"n": n1, "d": d1}, {"n": n2, "d": d2}],
                "sign": "?",
            },
            {
                "title": "Step 2: Find the LCM of the denominators 🔍",
                "lines": [
                    "LCM = Least Common Multiple: the smallest number that is a multiple of both denominators.",
                    f"Multiples of {d1}: {multiples(d1)}",
                    f"Multiples of {d2}: {multiples(d2)}",
                    f"The smallest number in both lists is {L}, so the LCM = {{{L}}}.",
                    f"{L} becomes the new denominator for both fractions.",
                ],
            },
            {
                "note": f"Step 3: ✂️ cut {' and '.join(cuts)}. Now both pizzas have {L} same-size slices!",
                "items": [{"n": c1, "d": L}, {"n": c2, "d": L}],
                "sign": symbol,
            },
        ],
        "caption": (
            f"Same amount of pizza, just smaller slices: {', '.join(rewrites)}. "
            f"Now count: {frac_tok(c1, L)} {symbol} {frac_tok(c2, L)}, "
            f"so {frac_tok(n1, d1)} {symbol} {frac_tok(n2, d2)}."
        ),
    }


def halfway_visual(n1, d1, n2, d2, icons=("🐢", "🐇"), colors=("coral", "teal")):
    """Number line with ½ marked; uses the 'double the top number' check for each fraction."""
    lines = []
    for n, d in ((n1, d1), (n2, d2)):
        assert n * 2 != d, "halfway check needs fractions that are not exactly one half"
        more = n * 2 > d
        lines.append(
            f"{frac_tok(n, d)}: {n} × 2 = {n * 2}, which is {'MORE' if more else 'LESS'} than {d} "
            f"→ {'more' if more else 'less'} than half."
        )
    if (n1 * 2 > d1) == (n2 * 2 > d2):
        raise ValueError("pick one fraction below half and one above half for this visual")
    big, small = ((n1, d1), (n2, d2)) if n1 * 2 > d1 else ((n2, d2), (n1, d1))
    lines.append(f"More than half beats less than half, so {frac_tok(*big)} > {frac_tok(*small)} 🎉")
    return {
        "type": "numberline",
        "halfway": True,
        "points": [
            {"n": n1, "d": d1, "icon": icons[0], "color": colors[0]},
            {"n": n2, "d": d2, "icon": icons[1], "color": colors[1]},
        ],
        "caption": "Trick: double the top number and compare it with the bottom number.\n" + "\n".join(lines),
    }


# 10 number problems — easy → hard
add_compare(1, 1, 3, 8, 5, 8)
add_compare(2, 1, 7, 10, 3, 10)
add_compare(3, 1, 1, 2, 1, 3)
add_compare(4, 2, 2, 3, 3, 4)
add_compare(5, 2, 3, 6, 1, 2)
add_compare(6, 2, 5, 6, 7, 9)
add_compare(7, 2, 4, 7, 3, 5)
add_compare(8, 3, 7, 12, 5, 8)
add_compare(9, 3, 6, 9, 8, 12)
add_compare(10, 3, 9, 8, 7, 6)

# 5 word problems — easy → hard
add_compare_word(
    11, 1,
    "Maya ate {3/8} of a pizza. Leo ate {5/8} of the same size pizza. Who ate MORE pizza?",
    "Maya", 3, 8, "Leo", 5, 8,
)
add_compare_word(
    12, 2,
    "Ava walks {2/3} km to school. Noah walks {3/5} km to school. Who walks FARTHER?",
    "Ava", 2, 3, "Noah", 3, 5,
)
add_compare_word(
    13, 2,
    "For a recipe, Jordan used {3/4} cup of flour and Priya used {6/8} cup of flour. Who used MORE flour?",
    "Jordan", 3, 4, "Priya", 6, 8,
)
add_compare_word(
    14, 3,
    "Liam has finished {5/6} of his homework. Sofia has finished {7/9} of hers. Who has finished LESS?",
    "Liam", 5, 6, "Sofia", 7, 9, asks="less",
)
add_compare_word(
    15, 3,
    "Ethan and Mia have the same size water bottles. Ethan drank {7/12} of his bottle and Mia drank {5/8} of hers. Who has MORE water LEFT?",
    "Ethan", 7, 12, "Mia", 5, 8, leftover=True,
)

add_section(
    "compare", "Greater or Smaller?", "⚖️", "#4ECDC4",
    "It's easy to compare fractions when the denominators already match — just look "
    "at the numerators! When the denominators are different, first rewrite both fractions "
    "so they have the same denominator (use the LCM of the denominators), THEN compare.",
    [
        {
            "text": "Same denominator? Just compare the numerators — bigger numerator wins.",
            "visual": pizzas_visual(3, 8, 5, 8),
        },
        {
            "text": "Different denominators? Find the LCM of the denominators, rewrite both fractions with it, then compare numerators.",
            "visual": lcm_pizzas_visual(3, 4, 5, 8),
        },
        {
            "text": "Quick check: is each fraction MORE or LESS than half? A fraction that's more than half is always bigger than one that's less than half.",
            "visual": halfway_visual(2, 5, 9, 10),
        },
    ],
    [
        {
            "prompt": "Compare {2/5} and {3/5}.",
            "steps": "Same denominator (5), so just compare numerators: 2 < 3, so 2/5 < 3/5.",
            "answer_display": "2/5 < 3/5",
        },
        {
            "prompt": "Compare {3/4} and {5/8}.",
            "steps": "LCM of 4 and 8 is 8. 3/4 = 6/8. Compare 6/8 and 5/8 → 6 > 5, so 3/4 > 5/8.",
            "answer_display": "3/4 > 5/8",
        },
        {
            "prompt": "Sam ran {3/4} km. Kai ran {2/3} km. Who ran farther?",
            "steps": "Pull out the fractions: 3/4 and 2/3. LCM of 4 and 3 is 12. 3/4 = 9/12 and 2/3 = 8/12. 9 > 8, so 3/4 > 2/3 — Sam ran farther.",
            "answer_display": "Sam",
        },
    ],
    compare_q,
)

# ===== 3. LCM =================================================================
lcm_q = []


def add_lcm(n, stars, prompt, a, b):
    L = lcm(a, b)
    steps = (
        f"Multiples of {a}: {', '.join(str(a * k) for k in range(1, 7))}, ...\n"
        f"Multiples of {b}: {', '.join(str(b * k) for k in range(1, 7))}, ...\n"
        f"The smallest number that appears in both lists is {L}."
    )
    lcm_q.append({
        "id": qid("lcm", n), "section": "lcm", "qtype": "integer",
        "difficulty": stars, "prompt": prompt,
        "answer": {"value": L, "display": str(L)},
        "steps": steps,
        "tip": "List the multiples of each number (skip-count) until the same number shows up in both lists — that's the LCM. Use it as the new denominator when adding or comparing fractions.",
    })


add_lcm(1, 1, "What is the LCM (Least Common Multiple) of {4} and {6}?", 4, 6)
add_lcm(2, 1, "What is the LCM of {3} and {5}?", 3, 5)
add_lcm(3, 1, "What is the LCM of {6} and {8}?", 6, 8)
add_lcm(4, 2, "What is the LCM of {4} and {10}?", 4, 10)
add_lcm(5, 2, "What is the LCM of {9} and {12}?", 9, 12)
add_lcm(6, 2, "What is the LCM of {8} and {20}?", 8, 20)
add_lcm(7, 3, "To add {1/12} and {1/18}, what should the new denominator be? (Hint: find the LCM of 12 and 18.)", 12, 18)
add_lcm(8, 3, "To add {2/15} and {3/25}, what should the new denominator be? (Hint: find the LCM of 15 and 25.)", 15, 25)

add_section(
    "lcm", "Common Multiples & the LCM", "🔢", "#FFE66D",
    "Before you can add, subtract, or compare fractions with different denominators, "
    "both fractions need the same denominator. The best one to use is the LCM "
    "(Least Common Multiple) of the two denominators.",
    [
        "A multiple of a number is what you get multiplying it by 1, 2, 3, 4...",
        "The LCM of two numbers is the smallest multiple they have in common.",
        "With fractions, use the LCM of the denominators as the new denominator for both fractions.",
    ],
    [
        {
            "prompt": "Find the LCM of {4} and {6}.",
            "steps": "Multiples of 4: 4, 8, 12, 16... Multiples of 6: 6, 12, 18... The smallest match is 12.",
            "answer_display": "12",
        },
        {
            "prompt": "To add {1/6} and {1/8}, what should the new denominator be?",
            "steps": "Multiples of 6: 6,12,18,24... Multiples of 8: 8,16,24... First match: 24.",
            "answer_display": "24",
        },
    ],
    lcm_q,
)

# ===== 4. SIMPLIFY ============================================================
simplify_q = []


def add_simplify(n, stars, raw_n, raw_d):
    a = analyze(raw_n, raw_d, context="fraction")
    steps = (
        f"Find the GCF of {raw_n} and {raw_d}: GCF = {a['gcd']}. "
        f"Divide both top and bottom by {a['gcd']}: {raw_n}/{a['gcd']} = {a['raw_num']//a['gcd']}, "
        f"{raw_d}/{a['gcd']} = {a['raw_den']//a['gcd']} → {a['display']}."
    )
    simplify_q.append({
        "id": qid("simplify", n), "section": "simplify", "qtype": "fraction",
        "difficulty": stars,
        "prompt": f"Reduce {frac_tok(raw_n, raw_d)} to lowest terms.",
        "answer": {"num": a["num"], "den": a["den"], "whole": a["whole"], "display": a["display"]},
        "steps": steps,
        "tip": "Find the greatest common factor (GCF) of the numerator and denominator, then divide both by it. If the GCF is 1, it's already fully reduced.",
    })


add_simplify(1, 1, 4, 8)
add_simplify(2, 1, 6, 9)
add_simplify(3, 1, 10, 15)
add_simplify(4, 2, 14, 21)
add_simplify(5, 2, 18, 24)
add_simplify(6, 2, 20, 30)
add_simplify(7, 3, 36, 48)
add_simplify(8, 3, 40, 64)

add_section(
    "simplify", "Simplifying & Reducing", "✂️", "#A8E6CF",
    "\"Simplifying\" and \"reducing\" mean the same thing: rewriting a fraction with "
    "the smallest possible numerator and denominator, without changing its value. "
    "You do this by dividing top and bottom by their greatest common factor (GCF).",
    [
        "GCF = the biggest number that divides evenly into both the numerator and denominator.",
        "Divide numerator AND denominator by the GCF — never just one of them.",
        "A fraction is 'in simplest form' once its GCF is 1.",
    ],
    [
        {
            "prompt": "Reduce {8/12} to lowest terms.",
            "steps": "GCF(8,12) = 4. 8÷4 = 2, 12÷4 = 3 → 2/3.",
            "answer_display": "2/3",
        },
        {
            "prompt": "Reduce {15/20} to lowest terms.",
            "steps": "GCF(15,20) = 5. 15÷5 = 3, 20÷5 = 4 → 3/4.",
            "answer_display": "3/4",
        },
    ],
    simplify_q,
)

# ===== 5. ADD =================================================================
add_q = []


def add_compute(bucket, section, n, stars, op, prompt, operands, raw_n, raw_d, context):
    a = analyze(raw_n, raw_d, context=context)
    bucket.append({
        "id": qid(section, n), "section": section, "qtype": "fraction",
        "difficulty": stars, "prompt": prompt,
        "answer": {"num": a["num"], "den": a["den"], "whole": a["whole"], "display": a["display"]},
        "steps": operands["steps"] + " " + a["tip"],
        "tip": a["tip"],
    })


# same denominator
raw, L, st = combine("+", 1, 5, 2, 5)
add_compute(add_q, "add", 1, 1, "+", f"{frac_tok(1,5)} + {frac_tok(2,5)} =", {"steps": st}, raw, L, "sum")
raw, L, st = combine("+", 2, 9, 5, 9)
add_compute(add_q, "add", 2, 1, "+", f"{frac_tok(2,9)} + {frac_tok(5,9)} =", {"steps": st}, raw, L, "sum")
raw, L, st = combine("+", 3, 8, 5, 8)
add_compute(add_q, "add", 3, 1, "+", f"{frac_tok(3,8)} + {frac_tok(5,8)} =", {"steps": st}, raw, L, "sum")
# unlike denominators
raw, L, st = combine("+", 1, 4, 1, 6)
add_compute(add_q, "add", 4, 2, "+", f"{frac_tok(1,4)} + {frac_tok(1,6)} =", {"steps": st}, raw, L, "sum")
raw, L, st = combine("+", 1, 7, 2, 3)
add_compute(add_q, "add", 5, 2, "+", f"{frac_tok(1,7)} + {frac_tok(2,3)} =", {"steps": st}, raw, L, "sum")
raw, L, st = combine("+", 5, 6, 3, 4)
add_compute(add_q, "add", 6, 2, "+", f"{frac_tok(5,6)} + {frac_tok(3,4)} =", {"steps": st}, raw, L, "sum")
# mixed numbers
i1 = to_improper(1, 1, 4); i2 = to_improper(0, 2, 5)
raw, L, st = combine("+", i1[0], i1[1], i2[0], i2[1])
st = f"Convert to improper fractions: 1 1/4 = 5/4, 2/5 stays 2/5. " + st
add_compute(add_q, "add", 7, 3, "+", f"{mixed_tok(1,1,4)} + {frac_tok(2,5)} =", {"steps": st}, raw, L, "sum")
i1 = to_improper(2, 1, 3); i2 = to_improper(1, 3, 4)
raw, L, st = combine("+", i1[0], i1[1], i2[0], i2[1])
st = f"Convert to improper fractions: 2 1/3 = 7/3, 1 3/4 = 7/4. " + st
add_compute(add_q, "add", 8, 3, "+", f"{mixed_tok(2,1,3)} + {mixed_tok(1,3,4)} =", {"steps": st}, raw, L, "sum")
# word problem
raw, L, st = combine("+", 3, 4, 5, 8)
add_compute(add_q, "add", 9, 3, "+", "You jog {3/4} km in the morning and {5/8} km in the evening. How many km did you jog in total?", {"steps": st}, raw, L, "total distance")

add_section(
    "add", "Adding Fractions", "➕", "#7EC8E3",
    "Same denominator? Just add the numerators. Different denominators? Find the "
    "LCM of the denominators first, rewrite both fractions, THEN add. With mixed numbers, it's easiest "
    "to convert to improper fractions first.",
    [
        "Same denominator: add the numerators, keep the denominator.",
        "Different denominators: find the LCM of the denominators, rewrite both fractions with it, then add.",
        "Mixed numbers: convert to improper fractions first, add, then convert back and simplify.",
    ],
    [
        {
            "prompt": "{2/9} + {4/9} =",
            "steps": "Same denominator: 2 + 4 = 6 → 6/9. Reduce: GCD(6,9)=3 → 2/3.",
            "answer_display": "2/3",
        },
        {
            "prompt": "{1/3} + {1/4} =",
            "steps": "LCM of 3 and 4 is 12. 1/3 = 4/12, 1/4 = 3/12. Add: 4/12 + 3/12 = 7/12.",
            "answer_display": "7/12",
        },
    ],
    add_q,
)

# ===== 6. SUBTRACT ============================================================
sub_q = []
raw, L, st = combine("-", 5, 7, 2, 7)
add_compute(sub_q, "subtract", 1, 1, "-", f"{frac_tok(5,7)} - {frac_tok(2,7)} =", {"steps": st}, raw, L, "difference")
raw, L, st = combine("-", 8, 9, 3, 9)
add_compute(sub_q, "subtract", 2, 1, "-", f"{frac_tok(8,9)} - {frac_tok(3,9)} =", {"steps": st}, raw, L, "difference")
raw, L, st = combine("-", 7, 10, 3, 10)
add_compute(sub_q, "subtract", 3, 1, "-", f"{frac_tok(7,10)} - {frac_tok(3,10)} =", {"steps": st}, raw, L, "difference")
raw, L, st = combine("-", 5, 6, 3, 4)
add_compute(sub_q, "subtract", 4, 2, "-", f"{frac_tok(5,6)} - {frac_tok(3,4)} =", {"steps": st}, raw, L, "difference")
raw, L, st = combine("-", 3, 4, 1, 6)
add_compute(sub_q, "subtract", 5, 2, "-", f"{frac_tok(3,4)} - {frac_tok(1,6)} =", {"steps": st}, raw, L, "difference")
raw, L, st = combine("-", 7, 8, 2, 5)
add_compute(sub_q, "subtract", 6, 2, "-", f"{frac_tok(7,8)} - {frac_tok(2,5)} =", {"steps": st}, raw, L, "difference")
i1 = to_improper(3, 1, 6); i2 = to_improper(1, 2, 3)
raw, L, st = combine("-", i1[0], i1[1], i2[0], i2[1])
st = f"Convert to improper fractions: 3 1/6 = 19/6, 1 2/3 = 5/3. " + st
add_compute(sub_q, "subtract", 7, 3, "-", f"{mixed_tok(3,1,6)} - {mixed_tok(1,2,3)} =", {"steps": st}, raw, L, "difference")
i1 = to_improper(4, 1, 5); i2 = to_improper(2, 3, 10)
raw, L, st = combine("-", i1[0], i1[1], i2[0], i2[1])
st = f"Convert to improper fractions: 4 1/5 = 21/5, 2 3/10 = 23/10. " + st
add_compute(sub_q, "subtract", 8, 3, "-", f"{mixed_tok(4,1,5)} - {mixed_tok(2,3,10)} =", {"steps": st}, raw, L, "difference")
raw, L, st = combine("-", 7, 8, 1, 4)
add_compute(sub_q, "subtract", 9, 3, "-", "A ribbon is {7/8} m long. You cut off {1/4} m to make a bow. How much ribbon is left?", {"steps": st}, raw, L, "remaining length")

add_section(
    "subtract", "Subtracting Fractions", "➖", "#FF8B94",
    "Subtracting works just like adding: same denominator, subtract the numerators; "
    "different denominators, find the LCM of the denominators first. For mixed numbers, convert to "
    "improper fractions first so you never have to \"borrow\".",
    [
        "Same denominator: subtract the numerators, keep the denominator.",
        "Different denominators: find the LCM of the denominators, rewrite both fractions, then subtract.",
        "Mixed numbers: convert to improper fractions first — it avoids borrowing mistakes.",
    ],
    [
        {
            "prompt": "{7/9} - {4/9} =",
            "steps": "Same denominator: 7 - 4 = 3 → 3/9. Reduce: GCD(3,9)=3 → 1/3.",
            "answer_display": "1/3",
        },
        {
            "prompt": "{3/4} - {1/6} =",
            "steps": "LCM of 4 and 6 is 12. 3/4 = 9/12, 1/6 = 2/12. Subtract: 9/12 - 2/12 = 7/12.",
            "answer_display": "7/12",
        },
    ],
    sub_q,
)

# ===== 7. MULTIPLY ============================================================
mul_q = []


def add_multiply(n, stars, prompt, n1, d1, n2, d2, context="product"):
    raw_n, raw_d = n1 * n2, d1 * d2
    a = analyze(raw_n, raw_d, context=context)
    steps = (
        f"Multiply straight across: numerator × numerator, denominator × denominator: "
        f"({n1}×{n2})/({d1}×{d2}) = {raw_n}/{raw_d}. {a['tip']}"
    )
    mul_q.append({
        "id": qid("multiply", n), "section": "multiply", "qtype": "fraction",
        "difficulty": stars, "prompt": prompt,
        "answer": {"num": a["num"], "den": a["den"], "whole": a["whole"], "display": a["display"]},
        "steps": steps, "tip": a["tip"],
    })


add_multiply(1, 1, f"{frac_tok(1,7)} × {frac_tok(3,4)} =", 1, 7, 3, 4)
add_multiply(2, 1, f"{frac_tok(2,5)} × {frac_tok(7,9)} =", 2, 5, 7, 9)
add_multiply(3, 1, f"{3} × {frac_tok(2,11)} =", 3, 1, 2, 11)
add_multiply(4, 2, f"{frac_tok(5,30)} × {frac_tok(9,5)} =", 5, 30, 9, 5)
add_multiply(5, 2, f"{frac_tok(7,12)} × {frac_tok(8,13)} =", 7, 12, 8, 13)
add_multiply(6, 2, f"{frac_tok(11,25)} × {75} =", 11, 25, 75, 1)
i1 = to_improper(1, 1, 5)
add_multiply(7, 3, f"{frac_tok(3,4)} × {mixed_tok(1,1,5)} =", 3, 4, i1[0], i1[1])
i1 = to_improper(3, 1, 4)
add_multiply(8, 3, f"{mixed_tok(3,1,4)} × {frac_tok(3,8)} =", i1[0], i1[1], 3, 8)
i1 = to_improper(1, 10, 11); i2 = to_improper(1, 1, 3)
add_multiply(9, 3, f"{mixed_tok(1,10,11)} × {mixed_tok(1,1,3)} =", i1[0], i1[1], i2[0], i2[1])
i1 = to_improper(1, 1, 2)
add_multiply(10, 3, "A recipe needs {2/3} cup of sugar per batch. How much sugar do you need for {1_1/2} batches?", 2, 3, i1[0], i1[1], context="amount of sugar")

add_section(
    "multiply", "Multiplying Fractions", "✖️", "#6C63FF",
    "Multiplying fractions is the most straightforward operation: multiply the "
    "numerators together, multiply the denominators together — no common "
    "denominator needed! For mixed numbers, convert to improper fractions first.",
    [
        "Multiply straight across: (numerator × numerator) / (denominator × denominator).",
        "Mixed numbers: convert to improper fractions before multiplying.",
        "Shortcut: you can cancel common factors between a numerator and a denominator BEFORE multiplying — it keeps the numbers smaller.",
    ],
    [
        {
            "prompt": "{2/3} × {5/7} =",
            "steps": "Multiply across: (2×5)/(3×7) = 10/21. GCD(10,21)=1, already simplest form.",
            "answer_display": "10/21",
        },
        {
            "prompt": "{5/30} × {9/5} =",
            "steps": "Multiply across: 45/150. GCD(45,150)=15 → 3/10. (You could also cancel the two 5's first!)",
            "answer_display": "3/10",
        },
    ],
    mul_q,
)

# ===== 8. DIVIDE ==============================================================
div_q = []


def add_divide(n, stars, prompt, n1, d1, n2, d2, context="quotient"):
    raw_n, raw_d = n1 * d2, d1 * n2
    a = analyze(raw_n, raw_d, context=context)
    steps = (
        f"Dividing by a fraction = multiplying by its reciprocal: "
        f"{n1}/{d1} ÷ {n2}/{d2} = {n1}/{d1} × {d2}/{n2} = ({n1}×{d2})/({d1}×{n2}) = {raw_n}/{raw_d}. {a['tip']}"
    )
    div_q.append({
        "id": qid("divide", n), "section": "divide", "qtype": "fraction",
        "difficulty": stars, "prompt": prompt,
        "answer": {"num": a["num"], "den": a["den"], "whole": a["whole"], "display": a["display"]},
        "steps": steps, "tip": a["tip"],
    })


add_divide(1, 1, f"{frac_tok(1,2)} ÷ {frac_tok(1,4)} =", 1, 2, 1, 4)
add_divide(2, 1, f"{frac_tok(3,5)} ÷ {frac_tok(2,5)} =", 3, 5, 2, 5)
add_divide(3, 1, f"{frac_tok(2,3)} ÷ {4} =", 2, 3, 4, 1)
add_divide(4, 2, f"{frac_tok(5,6)} ÷ {frac_tok(2,3)} =", 5, 6, 2, 3)
add_divide(5, 2, f"{frac_tok(7,8)} ÷ {frac_tok(3,4)} =", 7, 8, 3, 4)
add_divide(6, 2, f"{4} ÷ {frac_tok(2,5)} =", 4, 1, 2, 5)
i1 = to_improper(1, 1, 2)
add_divide(7, 3, f"{mixed_tok(1,1,2)} ÷ {frac_tok(1,3)} =", i1[0], i1[1], 1, 3)
i1 = to_improper(2, 1, 4); i2 = to_improper(1, 1, 2)
add_divide(8, 3, f"{mixed_tok(2,1,4)} ÷ {mixed_tok(1,1,2)} =", i1[0], i1[1], i2[0], i2[1])
add_divide(9, 3, "You have {3/4} of a pizza left and want to split it evenly among {3} friends. What fraction of a WHOLE pizza does each friend get?", 3, 4, 3, 1, context="each share")

add_section(
    "divide", "Dividing Fractions", "➗", "#FF9F43",
    "\"Keep, Change, Flip\": keep the first fraction, change ÷ to ×, and flip "
    "(reciprocal) the second fraction. Then multiply straight across like normal.",
    [
        "Dividing by a fraction is the same as multiplying by its reciprocal (flip it).",
        "Whole numbers can be written as a fraction over 1 before flipping.",
        "Mixed numbers: convert to improper fractions first, then keep-change-flip.",
    ],
    [
        {
            "prompt": "{2/3} ÷ {1/6} =",
            "steps": "Keep-change-flip: 2/3 × 6/1 = 12/3 = 4.",
            "answer_display": "4",
        },
        {
            "prompt": "{3/4} ÷ {2/5} =",
            "steps": "Keep-change-flip: 3/4 × 5/2 = 15/8 → improper → mixed 1 7/8.",
            "answer_display": "1 7/8",
        },
    ],
    div_q,
)

# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------
lessons = [
    {k: v for k, v in s.items() if k != "questions"}
    for s in sections
]
questions = [q for s in sections for q in s["questions"]]

meta = {
    "grade": 8,
    "unit": "fractions",
    "title": "Fractions",
    "emoji": "🍕",
    "description": "Learn fractions step by step: what they are, comparing, common multiples, simplifying, and the four operations.",
    "sections": [{"id": s["id"], "title": s["title"], "emoji": s["emoji"], "question_count": len(s["questions"])} for s in sections],
}

with open("lessons.json", "w", encoding="utf-8") as f:
    json.dump({"meta": meta, "sections": lessons}, f, ensure_ascii=False, indent=2)

with open("questions.json", "w", encoding="utf-8") as f:
    json.dump({"questions": questions}, f, ensure_ascii=False, indent=2)

print(f"Wrote {len(lessons)} sections and {len(questions)} questions.")
