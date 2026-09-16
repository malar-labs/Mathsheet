"""
One-time content generator for the Grade 9 "Rational Numbers" unit.

This script is NOT called by the running app. It was used once (by Claude, from
the teacher's Math 9 Rational Numbers unit package — lesson notes 1-4,
assignments 1-4 and checkpoints 1-4) to produce the static lessons.json and
questions.json files that ship with the app. The app only ever reads those JSON
files; nothing here runs at request time and nothing in this feature calls any
AI/LLM API.

Re-run with `python _generate.py` from this folder after editing the question
list below. Every answer is computed with Python's exact `fractions.Fraction`
and `decimal.Decimal`, so the math is guaranteed correct rather than hand-typed
— and so are the worked "steps", which are built from the same numbers.

The unit follows the teacher's 9-day unit plan:
    1 Comparing and Evaluating Rational Numbers  -> intro, compare
    2 Basic Operations with Decimals             -> dec-add, dec-mult
    4 Basic Operations with Fractions            -> frac-add, frac-mult
    5 Order of Operations                        -> order-ops
"""
import json
from decimal import Decimal as D
from fractions import Fraction as F
from math import gcd
from pathlib import Path


# ---------------------------------------------------------------------------
# Number formatting — display strings and prompt tokens
# ---------------------------------------------------------------------------

def lcm(a, b):
    return a * b // gcd(a, b)


def fdisp(fr):
    """Plain-text display for a Fraction: '13', '-81/20'."""
    return str(fr.numerator) if fr.denominator == 1 else f"{fr.numerator}/{fr.denominator}"


def ftok(fr, mixed=False):
    """Prompt token for a Fraction. {a/b} renders stacked; {w_a/b} renders as a
    mixed number; a whole number is printed plainly."""
    if fr.denominator == 1:
        return str(fr.numerator)
    if not mixed or abs(fr) < 1:
        return "{%d/%d}" % (fr.numerator, fr.denominator)
    sign = -1 if fr < 0 else 1
    size = abs(fr)
    whole, num = divmod(size.numerator, size.denominator)
    if num == 0:
        return str(sign * whole)
    return "{%d_%d/%d}" % (sign * whole, num, size.denominator)


def operand(fr, mixed=False, paren=None):
    """An operand inside a prompt. Negatives get brackets, the way the teacher's
    worksheets write them — except where `paren=False` asks for a bare leading term."""
    tok = ftok(fr, mixed)
    wrap = (fr < 0) if paren is None else paren
    return f"({tok})" if wrap else tok


def dnum(x):
    """Plain-text display for a Decimal: '920', '-0.48', '-7.56'."""
    d = D(x).normalize()
    if d == 0:
        return "0"
    if d.as_tuple().exponent > 0:          # 9.2E+2 -> 920
        d = d.quantize(D(1))
    return format(d, "f")


def dabs(x):
    return dnum(abs(D(x)))


def to_dec(fr):
    """Exact Decimal for a Fraction whose decimal form terminates."""
    return D(fr.numerator) / D(fr.denominator)


def dop(x, paren=None):
    """A Decimal operand inside a prompt."""
    wrap = (D(x) < 0) if paren is None else paren
    return f"({dnum(x)})" if wrap else dnum(x)


def pd(x):
    """A Decimal as it reads mid-sentence — negatives get brackets."""
    return f"({dnum(x)})" if D(x) < 0 else dnum(x)


# ---------------------------------------------------------------------------
# Worked-solution builders — the steps are derived from the same numbers as the
# answer, so they can never disagree with it.
# ---------------------------------------------------------------------------

def pf(fr):
    """A Fraction as it reads mid-sentence — negatives get brackets."""
    return f"({fdisp(fr)})" if fr < 0 else fdisp(fr)


def signed(n):
    """An integer as it reads after a + sign: '51' but '(-76)'."""
    return f"({n})" if n < 0 else str(n)


def reduce_step(raw_num, raw_den, result, what="answer"):
    g = gcd(abs(raw_num), raw_den)
    if g != 1:
        return (f"Reduce: GCD({abs(raw_num)}, {raw_den}) = {g}, so divide top and bottom by "
                f"{g} to get {fdisp(result)}.")
    return f"GCD({abs(raw_num)}, {raw_den}) = 1, so {fdisp(result)} is already fully reduced."


def frac_addsub_steps(a, b, op):
    """Steps for a +/- b on fractions (negatives and mixed numbers included)."""
    b_eff = b if op == "+" else -b
    steps = []
    if op == "-":
        steps.append(f"Subtracting is the same as adding the opposite: {fdisp(a)} - {pf(b)} "
                     f"= {fdisp(a)} + {pf(b_eff)}.")
    low = lcm(a.denominator, b_eff.denominator)
    an = a.numerator * (low // a.denominator)
    bn = b_eff.numerator * (low // b_eff.denominator)
    if a.denominator != b_eff.denominator:
        steps.append(f"The LCM of the denominators {a.denominator} and {b_eff.denominator} "
                     f"is {low}. Rewrite both: {fdisp(a)} = {an}/{low} and {fdisp(b_eff)} = {bn}/{low}.")
    steps.append(f"Add the numerators and keep the denominator: {an} + {signed(bn)} = {an + bn}, "
                 f"so {an + bn}/{low}.")
    steps.append(reduce_step(an + bn, low, a + b_eff))
    return " ".join(steps)


def frac_muldiv_steps(a, b, op):
    """Steps for a x/÷ b on fractions."""
    steps = []
    factor = b
    if op == "÷":
        factor = 1 / b
        steps.append(f"Keep-change-flip: {fdisp(a)} ÷ {pf(b)} = {fdisp(a)} × {pf(factor)}.")
    steps.append("The two numbers have different signs, so the answer is negative."
                 if (a < 0) != (factor < 0) else
                 "The two numbers have the same sign, so the answer is positive.")
    raw_n = a.numerator * factor.numerator
    raw_d = a.denominator * factor.denominator
    steps.append(f"Multiply straight across: ({a.numerator} × {factor.numerator}) / "
                 f"({a.denominator} × {factor.denominator}) = {raw_n}/{raw_d}.")
    steps.append(reduce_step(raw_n, raw_d, a * factor))
    return " ".join(steps)


def dec_addsub_steps(a, b, op):
    """Steps for a +/- b on decimals."""
    a, b = D(a), D(b)
    b_eff = b if op == "+" else -b
    total = a + b_eff
    steps = []
    if op == "-":
        steps.append(f"Subtracting is the same as adding the opposite: {dnum(a)} - {pd(b)} "
                     f"= {dnum(a)} + {pd(b_eff)}.")
    if (a < 0) == (b_eff < 0):
        steps.append(f"Both numbers have the same sign, so add the sizes and keep that sign: "
                     f"{dabs(a)} + {dabs(b_eff)} = {dabs(total)}, giving {dnum(total)}.")
    else:
        big, small = (a, b_eff) if abs(a) >= abs(b_eff) else (b_eff, a)
        steps.append(f"The signs are different, so take the smaller size away from the bigger "
                     f"one: {dabs(big)} - {dabs(small)} = {dabs(total)}.")
        steps.append(f"The bigger size came from {dnum(big)}, so the answer keeps that sign: "
                     f"{dnum(total)}.")
    return " ".join(steps)


def dec_muldiv_steps(a, b, op):
    """Steps for a x/÷ b on decimals."""
    a, b = D(a), D(b)
    result = a * b if op == "×" else a / b
    steps = ["The two numbers have different signs, so the answer is negative."
             if (a < 0) != (b < 0) else
             "The two numbers have the same sign, so the answer is positive."]
    steps.append(f"Now work with the sizes only: {dabs(a)} {op} {dabs(b)} = {dabs(result)}.")
    steps.append(f"Put the sign back on: {dnum(result)}.")
    return " ".join(steps)


# ---------------------------------------------------------------------------
# Question builders
# ---------------------------------------------------------------------------

QUESTIONS = []
_counters = {}


def _new_id(section):
    _counters[section] = _counters.get(section, 0) + 1
    return f"{section}-{_counters[section]:02d}"


def _add(section, kind, difficulty, prompt, qtype, answer, steps, tip, **extra):
    QUESTIONS.append({
        "id": _new_id(section),
        "section": section,
        "qtype": qtype,
        "kind": kind,
        "difficulty": difficulty,
        "prompt": prompt,
        **extra,
        "answer": answer,
        "steps": steps,
        "tip": tip,
    })


def ask_fraction(section, kind, difficulty, prompt, value, steps, tip):
    """Answer is a Fraction. Fully reduced improper fractions are the expected
    form in this unit, matching the teacher's answer keys."""
    value = F(value)
    _add(section, kind, difficulty, prompt, "fraction", {
        "num": value.numerator, "den": value.denominator, "whole": 0,
        "display": fdisp(value),
    }, steps, tip)


def ask_decimal(section, kind, difficulty, prompt, value, steps, tip, display=None):
    value = D(value)
    _add(section, kind, difficulty, prompt, "decimal", {
        "value": float(value), "display": display or dnum(value),
    }, steps, tip)


def ask_compare(section, kind, difficulty, prompt, left, right, steps, tip):
    symbol = "<" if left < right else (">" if left > right else "=")
    _add(section, kind, difficulty, prompt, "compare",
         {"symbol": symbol, "display": symbol}, steps, tip)


def ask_choice(section, kind, difficulty, prompt, options, choice, steps, tip):
    assert choice in options, choice
    # `choice` is matched against the tile the student clicked, so it keeps its
    # fraction-rendering braces; `display` is read back in plain sentences.
    _add(section, kind, difficulty, prompt, "choice",
         {"choice": choice, "display": plain(choice)}, steps, tip, options=options)


def ask_order(section, kind, difficulty, prompt, scrambled, correct, steps, tip):
    """`scrambled` is how the tiles are laid out; `correct` is the order to click."""
    assert sorted(scrambled) == sorted(correct), (scrambled, correct)
    assert len(set(scrambled)) == len(scrambled), scrambled
    _add(section, kind, difficulty, prompt, "order",
         {"order": list(correct), "display": ", ".join(plain(c) for c in correct)},
         steps, tip, options=list(scrambled))


def plain(token):
    """Strip the fraction-rendering braces so a token reads normally in a message."""
    return token.replace("{", "").replace("}", "").replace("_", " ")


def frac_op(section, difficulty, a, b, op, tip, a_mixed=False, b_mixed=False, a_paren=False):
    """A pure computation question: a op b, with the answer and steps derived."""
    a, b = F(a), F(b)
    value = {"+": a + b, "-": a - b, "×": a * b, "÷": a / b}[op]
    prompt = f"{operand(a, a_mixed, a_paren)} {op} {operand(b, b_mixed)} ="
    steps = (frac_addsub_steps(a, b, op) if op in "+-" else frac_muldiv_steps(a, b, op))
    ask_fraction(section, "number", difficulty, prompt, value, steps, tip)


def dec_op(section, difficulty, a, b, op, tip, a_paren=False):
    a, b = D(a), D(b)
    value = {"+": lambda: a + b, "-": lambda: a - b,
             "×": lambda: a * b, "÷": lambda: a / b}[op]()
    prompt = f"{dop(a, a_paren)} {op} {dop(b)} ="
    steps = (dec_addsub_steps(a, b, op) if op in "+-" else dec_muldiv_steps(a, b, op))
    ask_decimal(section, "number", difficulty, prompt, value, steps, tip)


# ===========================================================================
#   SECTION 1 — intro: What Is a Rational Number?
# ===========================================================================

TIP_INTRO = ("Ask yourself: can I write this as one integer over another integer? "
             "Whole numbers, terminating decimals and repeating decimals always can. "
             "A square root can only if the root comes out exactly.")

ask_choice("intro", "number", 1, "Is {-3} a rational number?", ["Yes", "No"], "Yes",
           "Every integer is already a fraction: -3 = -3/1. The top and bottom are both "
           "integers and the bottom isn't 0, so -3 is rational.", TIP_INTRO)

ask_choice("intro", "number", 1, "Is 0.25 a rational number?", ["Yes", "No"], "Yes",
           "0.25 = 25/100, and both 25 and 100 are integers. Reduced, that's 1/4. "
           "Every terminating decimal is rational.", TIP_INTRO)

ask_choice("intro", "number", 2, "Is √10 a rational number?", ["Yes", "No"], "No",
           "10 is not a perfect square: 3² = 9 and 4² = 16, so √10 sits between 3 and 4. "
           "Its decimal never ends and never repeats, so it can't be written as a fraction.", TIP_INTRO)

ask_fraction("intro", "number", 1, "Write 0.25 as a fully reduced fraction.", F(1, 4),
             "0.25 has 2 decimal places, so put 25 over 100: 25/100. "
             + reduce_step(25, 100, F(1, 4)),
             "Put the digits over the matching power of 10 — one decimal place means /10, "
             "two decimal places means /100 — then reduce.")

ask_fraction("intro", "number", 2, "Write -0.7 as a fully reduced fraction.", F(-7, 10),
             "0.7 has 1 decimal place, so that's 7/10, and the number is negative: -7/10. "
             + reduce_step(-7, 10, F(-7, 10)),
             "Work with the size first (0.7 = 7/10), then put the minus sign back on the top.")

ask_fraction("intro", "number", 2, "Simplify √16 / √49.", F(4, 7),
             "√16 = 4 because 4² = 16, and √49 = 7 because 7² = 49. "
             "Both roots come out exactly, so the value is 4/7 — a rational number. "
             + reduce_step(4, 7, F(4, 7)),
             "Take the square root of the top and the bottom separately. If both are perfect "
             "squares, the result is a rational number.")

ask_fraction("intro", "number", 3, "Simplify √(50/72).", F(5, 6),
             "Reduce inside the root first: GCD(50, 72) = 2, so 50/72 = 25/36. "
             "Now √25 = 5 and √36 = 6, so the value is 5/6. "
             + reduce_step(5, 6, F(5, 6)),
             "Reduce the fraction under the root before taking any roots — 50 and 72 aren't "
             "perfect squares, but 25 and 36 are.")

ask_choice("intro", "word", 2,
           "Kai says that 7.656565... (the 65 repeats forever) is a rational number. Is Kai right?",
           ["Yes", "No"], "Yes",
           "Repeating decimals are rational. 7.656565... = 7 + 65/99 = 758/99, which is one "
           "integer over another, so Kai is right.", TIP_INTRO)

ask_choice("intro", "word", 3,
           "A square patio has an area of 2.5 m². Ana says its side length, √2.5 m, is a "
           "rational number. Is Ana right?", ["Yes", "No"], "No",
           "For √2.5 to be rational the root would have to come out exactly. "
           "1.5² = 2.25 and 1.6² = 2.56, so √2.5 is between 1.5 and 1.6 and never settles "
           "into a terminating or repeating decimal. Ana is wrong.", TIP_INTRO)

ask_fraction("intro", "word", 2,
             "A hiker ends a walk 0.8 km lower than where she started, so her change in "
             "elevation is -0.8 km. Write -0.8 as a fully reduced fraction.", F(-4, 5),
             "0.8 has 1 decimal place, so that's 8/10, and the change is downwards so it is "
             "negative: -8/10. " + reduce_step(-8, 10, F(-4, 5)),
             "'Lower than where she started' means the signed number is negative. "
             "Convert 0.8 to a fraction first, then attach the minus sign.")


# ===========================================================================
#   SECTION 2 — compare: Comparing & Ordering Rational Numbers
# ===========================================================================

TIP_COMPARE = ("Turn everything into a decimal, then picture a number line. The further "
               "LEFT a number is, the smaller it is — so with two negatives, the one with "
               "the bigger size is the smaller number.")

ask_compare("compare", "number", 1, "Which sign goes between {-3/4} and -0.8?  (< , > , or =)",
            F(-3, 4), D("-0.8"),
            "-3/4 = -0.75 and the other number is -0.8. On a number line -0.8 is further left, "
            "so -3/4 is the bigger number: -3/4 > -0.8.", TIP_COMPARE)

ask_compare("compare", "number", 2, "Which sign goes between {-26/8} and {-3_1/4}?  (< , > , or =)",
            F(-26, 8), F(-13, 4),
            "-26/8 reduces to -13/4 = -3.25, and -3 1/4 is also -3.25. They are the same "
            "number written two ways, so the sign is =.", TIP_COMPARE)

ask_compare("compare", "number", 2, "Which sign goes between -8.29 and -8.3?  (< , > , or =)",
            D("-8.29"), D("-8.3"),
            "Line the decimals up as -8.29 and -8.30. The size 8.29 is smaller than 8.30, so "
            "-8.29 is closer to zero — which makes it the bigger number: -8.29 > -8.3.", TIP_COMPARE)

ask_compare("compare", "number", 3, "Which sign goes between 4.2 and √20?  (< , > , or =)",
            D("4.2"), D("20").sqrt(),
            "4.2² = 17.64, which is less than 20, so √20 must be bigger than 4.2 "
            "(√20 ≈ 4.47). So 4.2 < √20.",
            "You don't need a calculator: square the decimal and compare it with the number "
            "under the root sign.")

ask_compare("compare", "number", 2, "Which sign goes between {-3/4} and {-2/3}?  (< , > , or =)",
            F(-3, 4), F(-2, 3),
            "-3/4 = -0.75 and -2/3 = -0.6666... -0.75 is further left on the number line, "
            "so -3/4 < -2/3.", TIP_COMPARE)

ask_order("compare", "number", 3,
          "Click these in ascending order (least to greatest).",
          ["-1.2", "{4/5}", "{7/8}", "-0.4", "{-5/8}"],
          ["-1.2", "{-5/8}", "-0.4", "{4/5}", "{7/8}"],
          "As decimals: -1.2, 4/5 = 0.8, 7/8 = 0.875, -0.4, -5/8 = -0.625. "
          "Reading a number line left to right: -1.2, -0.625, -0.4, 0.8, 0.875.",
          "Convert every fraction to a decimal first, then sort. All the negatives come "
          "before all the positives.")

ask_order("compare", "number", 2,
          "Click these in descending order (greatest to least).",
          ["0.25", "{-1_1/2}", "{1/2}", "-0.1", "-0.6"],
          ["{1/2}", "0.25", "-0.1", "-0.6", "{-1_1/2}"],
          "As decimals: 0.25, -1 1/2 = -1.5, 1/2 = 0.5, -0.1, -0.6. "
          "Biggest to smallest: 0.5, 0.25, -0.1, -0.6, -1.5.",
          "Descending means you start at the right-hand end of the number line and work left. "
          "Among the negatives, the one closest to zero comes first.")

ask_choice("compare", "number", 3,
           "Which of these lies between -0.7 and -0.8?",
           ["{-3/4}", "{-2/3}", "{-7/8}", "{-1/2}"], "{-3/4}",
           "As decimals: -3/4 = -0.75, -2/3 = -0.666..., -7/8 = -0.875, -1/2 = -0.5. "
           "Only -0.75 sits between -0.8 and -0.7.",
           "Convert each option to a decimal and check which one falls between -0.8 and -0.7 "
           "on the number line. Remember -0.8 is to the LEFT of -0.7.")

ask_order("compare", "word", 2,
          "Daily temperatures in Kamloops B.C. were: Monday -2.1 °C, Tuesday -7.5 °C, "
          "Wednesday 3.6 °C, Thursday -0.5 °C, Friday 1.5 °C. "
          "Click the days in order from coldest to warmest.",
          ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
          ["Tuesday", "Monday", "Thursday", "Friday", "Wednesday"],
          "Sort the temperatures from least to greatest: -7.5, -2.1, -0.5, 1.5, 3.6. "
          "That gives Tuesday, Monday, Thursday, Friday, Wednesday.",
          "Coldest means most negative. -7.5 is colder than -2.1, even though 7.5 is the "
          "bigger number.")

ask_order("compare", "word", 2,
          "Boiling points: Water 100 °C, Oxygen -183 °C, Carbon Dioxide -78.5 °C, "
          "Helium -269 °C, Olive Oil 300 °C. Click them from least to greatest.",
          ["Water", "Oxygen", "Carbon Dioxide", "Helium", "Olive Oil"],
          ["Helium", "Oxygen", "Carbon Dioxide", "Water", "Olive Oil"],
          "Least to greatest: -269, -183, -78.5, 100, 300. "
          "That gives Helium, Oxygen, Carbon Dioxide, Water, Olive Oil.",
          "All three negative boiling points come before the positive ones. Among the "
          "negatives, the biggest size is the smallest number.")

ask_order("compare", "word", 2,
          "Melting points: Oxygen -222.7 °C, Mercury -38.7 °C, Nitrogen -209.9 °C, "
          "Sulfur 115.4 °C, Sodium 98 °C. Click them in descending order (highest "
          "melting point first).",
          ["Oxygen", "Mercury", "Nitrogen", "Sulfur", "Sodium"],
          ["Sulfur", "Sodium", "Mercury", "Nitrogen", "Oxygen"],
          "Greatest to least: 115.4, 98, -38.7, -209.9, -222.7. "
          "That gives Sulfur, Sodium, Mercury, Nitrogen, Oxygen.",
          "Start with the positives, biggest first. Then the negatives, closest to zero first "
          "— -38.7 is higher than -209.9.")

ask_decimal("compare", "word", 2,
            "In Kamloops the warmest day was 3.6 °C and the coldest was -7.5 °C. "
            "What is the difference between the warmest and the coldest day, in °C?",
            D("3.6") - D("-7.5"),
            "Difference = warmest - coldest = 3.6 - (-7.5). Subtracting a negative is adding: "
            "3.6 + 7.5 = 11.1 °C.",
            "Difference means bigger minus smaller. Subtracting a negative turns into adding, "
            "so the gap is bigger than either number on its own.")


# ===========================================================================
#   SECTION 3 — dec-add: Adding & Subtracting Decimals
# ===========================================================================

TIP_DEC_ADD = ("Estimate first by rounding to whole numbers, so you know what sign and "
               "roughly what size to expect. Same signs: add the sizes and keep the sign. "
               "Different signs: subtract the smaller size from the bigger one and keep the "
               "sign of the bigger.")

dec_op("dec-add", 1, "-2.8", "-4.3", "+", TIP_DEC_ADD, a_paren=False)
dec_op("dec-add", 1, "5.2", "-3.9", "+", TIP_DEC_ADD)
dec_op("dec-add", 1, "-5.7", "11.2", "+", TIP_DEC_ADD, a_paren=False)
dec_op("dec-add", 2, "-7.83", "1.61", "+", TIP_DEC_ADD, a_paren=True)
dec_op("dec-add", 2, "-2.75", "-4.81", "+", TIP_DEC_ADD, a_paren=False)
dec_op("dec-add", 2, "2.47", "3.1", "-", TIP_DEC_ADD)
dec_op("dec-add", 2, "5.21", "-6.92", "-", TIP_DEC_ADD)
dec_op("dec-add", 2, "-5.21", "-6.92", "-", TIP_DEC_ADD, a_paren=False)

ask_decimal("dec-add", "word", 2,
            "In Prince George B.C. the average mid-afternoon temperature in January is "
            "-4.1 °C. In July it is 22.5 °C. How many degrees colder is Prince George in "
            "January than in July?",
            D("22.5") - D("-4.1"),
            "Take the difference: 22.5 - (-4.1). Subtracting a negative is adding, so "
            "22.5 + 4.1 = 26.6. Prince George is 26.6 °C colder in January.",
            "'How much colder' is a difference: warmer temperature minus colder temperature. "
            "Watch for the double minus.")

ask_decimal("dec-add", "word", 1,
            "A pelican dives from a height of 2.4 m above the water to catch a fish 1.3 m "
            "below the water. How long is the pelican's dive, in metres?",
            D("2.4") + D("1.3"),
            "Above the water is +2.4 and below the water is -1.3. The length of the dive is "
            "the distance between them: 2.4 - (-1.3) = 2.4 + 1.3 = 3.7 m.",
            "Draw the water line as 0. The dive covers the distance above it plus the "
            "distance below it.")

ask_decimal("dec-add", "word", 2,
            "A Death Valley ultra-marathon starts 86 m below sea level and finishes at an "
            "elevation of 2548 m above sea level. What is the total elevation gained, in metres?",
            D("2548") - D("-86"),
            "Below sea level is -86 and above sea level is +2548. Elevation gained = "
            "finish - start = 2548 - (-86) = 2548 + 86 = 2634 m.",
            "Below sea level is a negative elevation. Finish minus start, and the double "
            "minus turns into a plus.")


# ===========================================================================
#   SECTION 4 — dec-mult: Multiplying & Dividing Decimals
# ===========================================================================

TIP_DEC_MULT = ("Work out the sizes first and put the sign on at the end: same signs give a "
                "positive answer, different signs give a negative one.")

dec_op("dec-mult", 1, "2.8", "-0.2", "×", TIP_DEC_MULT)
dec_op("dec-mult", 1, "-0.6", "-2.5", "×", TIP_DEC_MULT, a_paren=True)
dec_op("dec-mult", 2, "-0.12", "4.0", "×", TIP_DEC_MULT, a_paren=True)
dec_op("dec-mult", 2, "0.3", "-0.07", "×", TIP_DEC_MULT)
dec_op("dec-mult", 2, "-0.9", "-4", "×", TIP_DEC_MULT, a_paren=True)
dec_op("dec-mult", 1, "-5.5", "1.1", "÷", TIP_DEC_MULT, a_paren=True)
dec_op("dec-mult", 2, "-14.4", "1.2", "÷", TIP_DEC_MULT, a_paren=True)
dec_op("dec-mult", 2, "-4.2", "0.7", "÷", TIP_DEC_MULT, a_paren=False)
dec_op("dec-mult", 3, "-9.2", "-0.01", "÷", TIP_DEC_MULT, a_paren=True)

ask_decimal("dec-mult", "word", 2,
            "A pelican's dive is 3.7 m long and takes 0.2 seconds. What is the pelican's dive "
            "speed, in metres per second?",
            D("3.7") / D("0.2"),
            "Speed = distance ÷ time = 3.7 ÷ 0.2. Shift both numbers one place to divide by a "
            "whole number: 37 ÷ 2 = 18.5 m/s.",
            "Speed is distance divided by time. Dividing by a number smaller than 1 makes the "
            "answer bigger than the distance.")

ask_decimal("dec-mult", "word", 3,
            "On Saturday the temperature at Okanagan Lake near Kelowna B.C. decreased by "
            "1.8 °C/h for 2.5 h, then decreased by 0.6 °C/h for 3.5 h. What was the total "
            "change in temperature, in °C?",
            D("-1.8") * D("2.5") + D("-0.6") * D("3.5"),
            "A decrease is a negative rate. First stretch: -1.8 × 2.5 = -4.5. "
            "Second stretch: -0.6 × 3.5 = -2.1. Total change: -4.5 + (-2.1) = -6.6 °C.",
            "'Decreased by' means the rate is negative. Work out each stretch separately, "
            "then add the two changes together.")

ask_decimal("dec-mult", "word", 3,
            "Over those same 6 hours at Okanagan Lake the temperature changed by a total of "
            "-6.6 °C. What was the average rate of change, in °C per hour?",
            D("-6.6") / D("6"),
            "Average rate = total change ÷ total time. The total time is 2.5 + 3.5 = 6 h, so "
            "-6.6 ÷ 6 = -1.1 °C/h.",
            "Add the two stretches of time together first, then divide the total change by "
            "the total time. The answer stays negative because the temperature fell.")

ask_decimal("dec-mult", "word", 3,
            "A submarine was travelling at a depth of 153 m and rose at 2.4 metres per minute "
            "for 8 minutes. What was the submarine's depth at the end of the rise, in metres?",
            D("153") - D("2.4") * D("8"),
            "How far it rose: 2.4 × 8 = 19.2 m. Rising makes the depth smaller: "
            "153 - 19.2 = 133.8 m.",
            "Find the total distance risen first (rate × time), then take it off the starting "
            "depth — rising means less depth.")


# ===========================================================================
#   SECTION 5 — frac-add: Adding & Subtracting Fractions
# ===========================================================================

TIP_FRAC_ADD = ("Turn mixed numbers into improper fractions first (keeping the sign), then "
                "find the LCM of the denominators, rewrite both fractions with it, and "
                "combine the numerators. Reduce at the end.")

frac_op("frac-add", 1, F(-2, 3), F(1, 5), "+", TIP_FRAC_ADD)
frac_op("frac-add", 1, F(4, 5), F(-3, 10), "-", TIP_FRAC_ADD)
frac_op("frac-add", 1, F(5, 6), F(2), "-", TIP_FRAC_ADD)
frac_op("frac-add", 2, F(3, 2), F(-4, 15), "+", TIP_FRAC_ADD, a_mixed=True)
frac_op("frac-add", 2, F(-1, 4), F(11, 6), "+", TIP_FRAC_ADD, b_mixed=True)
frac_op("frac-add", 2, F(5, 3), F(-5, 2), "+", TIP_FRAC_ADD, a_mixed=True, b_mixed=True)
frac_op("frac-add", 2, F(-1, 4), F(-19, 5), "+", TIP_FRAC_ADD, b_mixed=True)
frac_op("frac-add", 2, F(-3, 14), F(15, 7), "-", TIP_FRAC_ADD, b_mixed=True)
frac_op("frac-add", 3, F(5, 9), F(-17, 12), "-", TIP_FRAC_ADD, b_mixed=True)

_cory = F(5, 2) + F(1, 4) + F(4, 3)
ask_fraction("frac-add", "word", 2,
             "Cory is a baker. Today he needs {2_1/2} cups of sugar for tarts, {1/4} cup for "
             "bread and {1_1/3} cup for cake. How much sugar does he need in total, in cups?",
             _cory,
             "As improper fractions the total is 5/2 + 1/4 + 4/3. "
             "The LCM of 2, 4 and 3 is 12, so rewrite all three: 30/12 + 3/12 + 16/12. "
             f"Add the numerators: 30 + 3 + 16 = 49, so 49/12. {reduce_step(49, 12, _cory)} "
             "(That's just over 4 cups.)",
             "Convert every mixed number to an improper fraction, then use the LCM of 2, 4 "
             "and 3 as the common denominator.")

_lori = F(1) - F(2, 3) - F(1, 4)
ask_fraction("frac-add", "word", 3,
             "Lori is a carpenter with 24 m of baseboard. She installs {2/3} of the baseboard "
             "in one room and {1/4} of it in another. What FRACTION of the baseboard does she "
             "have left over?",
             _lori,
             "She starts with 1 whole lot of baseboard and uses 2/3 + 1/4 of it. "
             "The LCM of 3 and 4 is 12, so she uses 8/12 + 3/12 = 11/12 of it. "
             "What is left is 1 - 11/12 = 12/12 - 11/12 = 1/12. "
             "(As a length that is 1/12 of 24 m = 2 m.)",
             "Both fractions are fractions OF the same 24 m, so work with 1 whole and "
             "subtract. The LCM of 3 and 4 is 12.")

_maka = F(1) - F(2, 5) - F(1, 4) - F(1, 8)
ask_fraction("frac-add", "word", 3,
             "At the start of a week Maka had $40 of her allowance left. That week she spent "
             "{2/5} of the money on bus fares, another {1/4} on shopping and {1/8} on snacks. "
             "What fraction of her money did she have left at the end of the week?",
             _maka,
             "She spent 2/5 + 1/4 + 1/8 of her money. The LCM of 5, 4 and 8 is 40, so that is "
             "16/40 + 10/40 + 5/40 = 31/40. What is left is 1 - 31/40 = 9/40. "
             "(As money that is 9/40 of $40 = $9.)",
             "Every fraction is a fraction of the same $40, so add them up and subtract from "
             "1 whole. The LCM of 5, 4 and 8 is 40.")

_andy = F(2, 8) + F(1, 6)
_bee = F(2, 6) + F(1, 8)
ask_fraction("frac-add", "word", 3,
             "Andy and Bee shared two same-size pizzas: the pepperoni was cut into {6} slices "
             "and the Hawaiian into {8} slices. Andy ate two slices of Hawaiian and one slice "
             "of pepperoni. Bee ate two slices of pepperoni and one slice of Hawaiian. "
             "How much more pizza did Bee eat than Andy, as a fraction of one pizza?",
             _bee - _andy,
             f"Andy: 2/8 + 1/6 = {fdisp(_andy)}. Bee: 2/6 + 1/8 = {fdisp(_bee)}. "
             + frac_addsub_steps(_bee, _andy, "-"),
             "A slice of Hawaiian is 1/8 of a pizza and a slice of pepperoni is 1/6. Work out "
             "each person's total first, then subtract.")

_left = (F(2) - (_andy + _bee)) / 2
ask_fraction("frac-add", "word", 3,
             "Andy and Bee started with two whole pizzas. What fraction of the TOTAL pizza "
             "(both pizzas together) was left over?",
             _left,
             f"Together they ate {fdisp(_andy)} + {fdisp(_bee)} = {fdisp(_andy + _bee)} of a "
             f"pizza. That leaves 2 - {fdisp(_andy + _bee)} = {fdisp(F(2) - _andy - _bee)} of "
             f"a pizza. As a fraction of the two whole pizzas, divide by 2: "
             f"{fdisp(F(2) - _andy - _bee)} ÷ 2 = {fdisp(_left)}.",
             "Careful what the fraction is OF. Work out how much pizza is left first, then "
             "divide by 2 because there were two whole pizzas to begin with.")


# ===========================================================================
#   SECTION 6 — frac-mult: Multiplying & Dividing Fractions
# ===========================================================================

TIP_FRAC_MULT = ("No common denominator needed. Multiply straight across; to divide, "
                 "keep-change-flip. Same signs give a positive answer, different signs give "
                 "a negative one.")

frac_op("frac-mult", 1, F(5, 7), F(-2, 3), "×", TIP_FRAC_MULT)
frac_op("frac-mult", 1, F(3, 4), F(-6, 7), "×", TIP_FRAC_MULT)
frac_op("frac-mult", 2, F(-13, 5), F(-5), "×", TIP_FRAC_MULT, a_mixed=True, a_paren=True)
frac_op("frac-mult", 2, F(-5), F(8, 3), "×", TIP_FRAC_MULT, b_mixed=True)
frac_op("frac-mult", 2, F(3, 4), F(-6, 7), "÷", TIP_FRAC_MULT)
frac_op("frac-mult", 2, F(4), F(-6, 7), "÷", TIP_FRAC_MULT)
frac_op("frac-mult", 2, F(-4, 9), F(-3, 5), "÷", TIP_FRAC_MULT, a_paren=True)
frac_op("frac-mult", 3, F(-15, 2), F(-20, 21), "÷", TIP_FRAC_MULT, a_mixed=True, a_paren=True)
frac_op("frac-mult", 3, F(-9, 7), F(-7, 6), "×", TIP_FRAC_MULT, a_mixed=True, b_mixed=True, a_paren=True)

ask_decimal("frac-mult", "word", 1,
            "Maka spent {2/5} of her $40 allowance on bus fares. How many dollars is that?",
            to_dec(F(2, 5) * 40),
            "'Of' means multiply: 2/5 × 40 = 80/5 = 16. She spent $16 on bus fares.",
            "'A fraction of an amount' means multiply. 2/5 of 40 is (2 × 40) ÷ 5.")

_soup = F(8) / F(4, 3)
ask_fraction("frac-mult", "word", 2,
             "A soup recipe calls for {1_1/3} cups of broth. How many full batches of soup can "
             "you make with 2 litres of broth?  (1 L is about 4 cups.)",
             _soup,
             "2 L is about 2 × 4 = 8 cups. Each batch takes 1 1/3 cups = 4/3 cups. "
             + frac_muldiv_steps(F(8), F(4, 3), "÷"),
             "Convert the litres to cups first. 'How many batches fit' is a division: "
             "total cups ÷ cups per batch.")

_diver = F(-3, 4) * F(8, 3)
ask_fraction("frac-mult", "word", 2,
             "A diver descends {3/4} of a metre every second, so her change in depth is "
             "{-3/4} m each second. Written as a signed number, what is her total change in "
             "depth after {2_2/3} seconds, in metres?",
             _diver,
             "Total change = rate × time = -3/4 × 8/3. " + frac_muldiv_steps(F(-3, 4), F(8, 3), "×"),
             "Descending makes the change negative. Convert 2 2/3 to the improper fraction "
             "8/3, then multiply straight across.")


# ===========================================================================
#   SECTION 7 — order-ops: Order of Operations
# ===========================================================================

TIP_ORDER = ("BEDMAS: Brackets, then Exponents (and square roots), then Division and "
             "Multiplication left to right, then Addition and Subtraction left to right. "
             "Division and multiplication are the SAME step — do whichever comes first.")

_o1 = D("-2.1") * 3 + D("4.3")
ask_decimal("order-ops", "number", 1, "-2.1 × 3 + 4.3 =", _o1,
            "No brackets or exponents, so multiply first: -2.1 × 3 = -6.3. "
            "Then add: -6.3 + 4.3 = -2.",
            "Multiplication comes before addition, even though the addition is written "
            "further to the right.")

_o2 = (D("-7.2") + D("7.6")) / D("-0.2")
ask_decimal("order-ops", "number", 1, "((-7.2) + 7.6) ÷ (-0.2) =", _o2,
            "Brackets first: -7.2 + 7.6 = 0.4. Then divide: 0.4 ÷ (-0.2) = -2 — "
            "different signs, so the answer is negative.",
            "A fraction bar is a bracket: work out everything on top before you divide by "
            "what is underneath.")

_o3 = D("-0.2") * (D("4.8") - D("5.6"))
ask_decimal("order-ops", "number", 2, "-0.2(4.8 - 5.6) =", _o3,
            "Brackets first: 4.8 - 5.6 = -0.8. A number written against a bracket means "
            "multiply: -0.2 × (-0.8) = 0.16 — two negatives make a positive.",
            "A number sitting right beside a bracket means multiply. Do the subtraction "
            "inside the bracket first.")

_o4 = (D("4.5") - D("5.3")) * (D("5.7") - D("6.5"))
ask_decimal("order-ops", "number", 2, "(4.5 - 5.3)(5.7 - 6.5) =", _o4,
            "Work out each bracket: 4.5 - 5.3 = -0.8 and 5.7 - 6.5 = -0.8. "
            "Then multiply: -0.8 × (-0.8) = 0.64 — same signs, positive answer.",
            "Two brackets written side by side means multiply them. Do both brackets first.")

_o5 = D("0.3") ** 2 + D("-0.8") / 2
ask_decimal("order-ops", "number", 2, "0.3² + (-0.8) ÷ 2 =", _o5,
            "Exponents first: 0.3² = 0.09. Then divide: -0.8 ÷ 2 = -0.4. "
            "Finally add: 0.09 + (-0.4) = -0.31.",
            "Exponents come before division, and division comes before addition. "
            "0.3² is 0.3 × 0.3, not 0.6.")

_o6 = (F(2, 5) - F(1, 2)) / F(3, 10)
ask_fraction("order-ops", "number", 2, "({2/5} - {1/2}) ÷ {3/10} =", _o6,
             "Brackets first: the LCM of 5 and 2 is 10, so 4/10 - 5/10 = -1/10. "
             "Now the division, -1/10 ÷ 3/10. "
             + frac_muldiv_steps(F(-1, 10), F(3, 10), "÷"),
             "Finish everything inside the bracket before you divide. Then keep-change-flip.")

_o7 = (F(3, 8) - F(7, 4)) * F(-1, 3)
ask_fraction("order-ops", "number", 2, "({3/8} - {7/4}) × ({-1/3}) =", _o7,
             "Brackets first: the LCM of 8 and 4 is 8, so 3/8 - 14/8 = -11/8. "
             "Now the multiplication, -11/8 × (-1/3). "
             + frac_muldiv_steps(F(-11, 8), F(-1, 3), "×"),
             "Do the subtraction inside the bracket first — you need a common denominator "
             "for that, but not for the multiplication that follows.")

_o8 = F(3, 4) + F(-3, 2) / F(6, 7)
ask_fraction("order-ops", "number", 3, "{3/4} + ({-1_1/2}) ÷ {6/7} =", _o8,
             "Division comes before addition. Convert the mixed number first: -1 1/2 = -3/2. "
             + frac_muldiv_steps(F(-3, 2), F(6, 7), "÷")
             + " Now do the addition, 3/4 + (-7/4). "
             + frac_addsub_steps(F(3, 4), F(-7, 4), "+"),
             "Do the division before the addition. Turn the mixed number into an improper "
             "fraction before you flip anything.")

_o9 = D("2.4") + D("1.8") * D("-2") / D("-0.6")
ask_decimal("order-ops", "number", 3, "2.4 + 1.8 × (-2) ÷ (-0.6) =", _o9,
            "No brackets or exponents. Multiplication and division are the same step, so "
            "work left to right: 1.8 × (-2) = -3.6, then -3.6 ÷ (-0.6) = 6. "
            "Finally add: 2.4 + 6 = 8.4.",
            "× and ÷ rank equally — do them in the order they appear, left to right. Only "
            "then do the addition.")

_o10 = (D("-0.5") - D("0.36").sqrt()) + D("-3") ** 2 * D("0.1")
ask_decimal("order-ops", "number", 3, "(-0.5 - √0.36) + (-3)² × 0.1 =", _o10,
            "The square root is an exponent, so it goes first: √0.36 = 0.6. "
            "The bracket is then -0.5 - 0.6 = -1.1. Next exponent: (-3)² = 9 — the bracket "
            "squares the minus sign too. Then multiply: 9 × 0.1 = 0.9. "
            "Finally add: -1.1 + 0.9 = -0.2.",
            "(-3)² = 9 because the bracket squares the minus as well. Square roots are "
            "handled at the Exponents step.")

_o11 = F(1, 3) * (F(2, 3) - F(3, 4)) + F(5, 12)
ask_fraction("order-ops", "number", 3, "{1/3}({2/3} - {3/4}) + {5/12} =", _o11,
             "Brackets first: the LCM of 3 and 4 is 12, so 8/12 - 9/12 = -1/12. "
             + frac_muldiv_steps(F(1, 3), F(-1, 12), "×")
             + " Now do the addition, -1/36 + 5/12. "
             + frac_addsub_steps(F(-1, 36), F(5, 12), "+"),
             "Bracket, then the multiplication written against it, then the addition.")

_cube_edge = D(150 // 6).sqrt()
ask_decimal("order-ops", "word", 2,
            "The surface area of a cube is 150 cm². A cube has 6 identical square faces. "
            "What is the edge length of the cube, in cm?",
            _cube_edge,
            "Each face has area 150 ÷ 6 = 25 cm². A face is a square, so the edge is "
            "√25 = 5 cm.",
            "Divide the surface area by 6 to get the area of one square face, then take the "
            "square root of that.")

ask_decimal("order-ops", "word", 2,
            "That same cube has an edge length of 5 cm. What is its volume, in cm³?",
            D(5) ** 3,
            "Volume = edge³ = 5³ = 5 × 5 × 5 = 125 cm³.",
            "Volume of a cube is the edge length cubed — multiply the edge by itself three "
            "times.")

_fence = D(19) * (4 * D(36).sqrt()) - D(250)
ask_decimal("order-ops", "word", 3,
            "Matt is building a fence around his square garden. The garden's area is 36 m² "
            "and the fence costs $19.00 per metre. He has $250 to spend and will borrow the "
            "rest from his brother. How many dollars will he owe his brother?",
            _fence,
            "The garden is square with area 36 m², so each side is √36 = 6 m and the "
            "perimeter is 4 × 6 = 24 m. The fence costs 24 × $19.00 = $456. "
            "He pays $250 himself, so he owes 456 - 250 = $206.",
            "Find the side length from the area first, then the perimeter, then the cost. "
            "Only the part he can't pay for is borrowed.")

_hours = D("7.75")
_james = _hours * (D("1.5") * D("24.80"))
ask_decimal("order-ops", "word", 3,
            "James works at a hospital. On a holiday he is paid time and a half — 1.5 times "
            "his regular wage of $24.80 per hour. He worked from 8:30 AM to 4:15 PM. "
            "How many dollars did he earn that day?",
            _james,
            "From 8:30 AM to 4:15 PM is 7 h 45 min = 7.75 hours. His holiday rate is "
            "1.5 × $24.80 = $37.20 per hour. He earned 7.75 × 37.20 = $288.30.",
            "Work out the hours as a decimal first (45 minutes is 0.75 of an hour), then the "
            "holiday rate, then multiply.",
            display="288.30")


# ===========================================================================
#   Lessons
# ===========================================================================

SECTIONS = [
    {
        "id": "intro",
        "title": "What Is a Rational Number?",
        "emoji": "\U0001F522",
        "color": "#6C63FF",
        "blurb": "A rational number is any number you can write as a fraction — one integer "
                 "over another, as long as the bottom one isn't 0. Positive or negative, "
                 "whole numbers, terminating decimals like 0.25 and repeating decimals like "
                 "3.3333... all count. Numbers that can't be written that way, such as "
                 "√10, are irrational.",
        "key_concepts": [
            "Every integer is already rational: 5 = {5/1} and -3 = {-3/1}. The bottom number "
            "just has to be an integer that isn't 0.",
            {
                "text": "Negative rational numbers live to the LEFT of 0 on the number line. "
                        "The further left you go, the smaller the number gets.",
                "visual": {
                    "type": "signline", "min": -2, "max": 2, "step": 0.5,
                    "points": [
                        {"v": -1.2, "label": "-1.2", "color": "coral"},
                        {"v": -0.625, "label": "{-5/8}", "color": "orange"},
                        {"v": 0.8, "label": "{4/5}", "color": "teal"},
                    ],
                    "caption": "-1.2 is the smallest of these three even though 1.2 is not the "
                               "biggest number — what counts is how far LEFT it sits.",
                },
            },
            "A terminating decimal is rational: put the digits over the matching power of 10, "
            "then reduce. 0.25 = {25/100} = {1/4}, and -0.7 = {-7/10}.",
            "A repeating decimal is rational too: 3.3333... = {10/3} and 7.656565... = {758/99}.",
            "A square root is rational only when the root comes out exactly: √9 = 3 and "
            "√0.81 = 0.9 are rational, and so is √(50/72) = √(25/36) = {5/6}. "
            "But √10 is irrational.",
        ],
        "examples": [
            {
                "prompt": "Is 0.25 a rational number?",
                "steps": "0.25 has 2 decimal places, so it is 25/100. Both 25 and 100 are "
                         "integers and the bottom isn't 0, so yes. Reduced, 0.25 = 1/4.",
                "answer_display": "Yes — it equals 1/4",
            },
            {
                "prompt": "Simplify √16 / √49.",
                "steps": "√16 = 4 and √49 = 7. Both roots come out exactly, so the value "
                         "is 4/7 — a rational number.",
                "answer_display": "4/7",
            },
            {
                "prompt": "Is √10 a rational number?",
                "steps": "10 is not a perfect square: 3² = 9 and 4² = 16. So √10 lies "
                         "between 3 and 4 and its decimal never terminates or repeats.",
                "answer_display": "No — it is irrational",
            },
        ],
    },
    {
        "id": "compare",
        "title": "Comparing & Ordering",
        "emoji": "⚖️",
        "color": "#4ECDC4",
        "blurb": "To compare rational numbers, get them all into the same form — usually "
                 "decimals — then picture them on a number line. Be careful with negatives: "
                 "the further LEFT a number is, the smaller it is, so -7.5 is smaller than "
                 "-2.1 even though 7.5 is bigger than 2.1.",
        "key_concepts": [
            "Turn every fraction into a decimal by dividing the top by the bottom: "
            "{4/5} = 0.8, {7/8} = 0.875 and {-5/8} = -0.625.",
            {
                "text": "Then place them on a number line and read left to right — that is "
                        "ascending order.",
                "visual": {
                    "type": "signline", "min": -1.5, "max": 1, "step": 0.5,
                    "points": [
                        {"v": -1.2, "label": "-1.2", "color": "coral"},
                        {"v": -0.625, "label": "{-5/8}", "color": "orange"},
                        {"v": -0.4, "label": "-0.4", "color": "purple"},
                        {"v": 0.8, "label": "{4/5}", "color": "teal"},
                    ],
                    "caption": "Ascending order, straight off the line: -1.2, {-5/8}, -0.4, {4/5}.",
                },
            },
            {
                "text": "With two negatives, the one with the BIGGER size is the SMALLER "
                        "number — it sits further from zero on the left.",
                "visual": {
                    "type": "signline", "min": -1, "max": 0, "step": 0.25,
                    "zones": False,
                    "points": [
                        {"v": -0.75, "label": "{-3/4}", "color": "coral"},
                        {"v": -0.6666666, "label": "{-2/3}", "color": "teal"},
                    ],
                    "caption": "{-3/4} = -0.75 and {-2/3} = -0.6666... -0.75 is further left, "
                               "so {-3/4} < {-2/3} — even though 3/4 > 2/3.",
                },
            },
            "To find a number between two others, compare their decimals. Between -0.7 and "
            "-0.8 sits -0.75, which is {-3/4}.",
            "No calculator for a square root? Square the decimal instead: 4.2² = 17.64, "
            "which is less than 20, so 4.2 < √20.",
        ],
        "examples": [
            {
                "prompt": "Write -1.2, {4/5}, {7/8}, -0.4 and {-5/8} in ascending order.",
                "steps": "As decimals: -1.2, 0.8, 0.875, -0.4, -0.625. Sorted from smallest "
                         "to biggest: -1.2, -0.625, -0.4, 0.8, 0.875.",
                "answer_display": "-1.2, -5/8, -0.4, 4/5, 7/8",
            },
            {
                "prompt": "Which is greater, {-3/4} or {-2/3}?",
                "steps": "-3/4 = -0.75 and -2/3 = -0.6666... -0.6666... is further right on "
                         "the number line, so -2/3 is the greater number.",
                "answer_display": "-2/3",
            },
            {
                "prompt": "Put the right sign between -8.29 and -8.3.",
                "steps": "Line the decimals up as -8.29 and -8.30. The size 8.29 is smaller, "
                         "so -8.29 is closer to zero and therefore the bigger number.",
                "answer_display": "-8.29 > -8.3",
            },
        ],
    },
    {
        "id": "dec-add",
        "title": "Adding & Subtracting Decimals",
        "emoji": "➕",
        "color": "#FF9F43",
        "blurb": "Estimate first by rounding to whole numbers — it tells you what sign and "
                 "roughly what size to expect, which catches most mistakes. Then work "
                 "exactly. Subtracting a number is the same as adding its opposite, so every "
                 "subtraction can be turned into an addition.",
        "key_concepts": [
            {
                "text": "Two signs sitting next to each other collapse into one: subtracting "
                        "a negative becomes adding, and adding a negative becomes "
                        "subtracting.",
                "visual": {
                    "type": "rules",
                    "items": [
                        {"expr": "a - (-b)", "result": "+",
                         "note": "-5.21 - (-6.92) = -5.21 + 6.92"},
                        {"expr": "a + (-b)", "result": "-",
                         "note": "-2.75 + (-4.81) = -2.75 - 4.81"},
                    ],
                    "caption": "Rewrite the double sign first — then it's an ordinary "
                               "addition or subtraction.",
                },
            },
            "Same signs? Add the sizes and keep the sign: -2.75 + (-4.81) = -7.56.",
            "Different signs? Take the smaller size away from the bigger one and keep the "
            "sign of the bigger: 5.2 + (-3.9) = 1.3, but -7.83 + 1.61 = -6.22.",
            {
                "text": "Estimate before you calculate. -2.8 + (-4.3) is about -3 + (-4) = -7, "
                        "so an exact answer of -7.1 makes sense.",
                "visual": {
                    "type": "signline", "min": -8, "max": 2, "step": 1,
                    "points": [
                        {"v": -2.8, "label": "start -2.8", "color": "teal"},
                        {"v": -7.1, "label": "end -7.1", "color": "coral"},
                    ],
                    "caption": "Adding a negative moves you LEFT: start at -2.8, move 4.3 "
                               "further left, and you land on -7.1.",
                },
            },
        ],
        "examples": [
            {
                "prompt": "-2.75 + (-4.81) =",
                "steps": "Both numbers are negative, so add the sizes and keep the minus: "
                         "2.75 + 4.81 = 7.56, so the answer is -7.56.",
                "answer_display": "-7.56",
            },
            {
                "prompt": "-5.21 - (-6.92) =",
                "steps": "Subtracting a negative is adding: -5.21 + 6.92. The signs differ, "
                         "so subtract the sizes: 6.92 - 5.21 = 1.71. The bigger size came "
                         "from +6.92, so the answer is positive.",
                "answer_display": "1.71",
            },
            {
                "prompt": "2.47 - 3.1 =",
                "steps": "Rewrite as 2.47 + (-3.1). Different signs, so 3.1 - 2.47 = 0.63. "
                         "The bigger size came from -3.1, so the answer is -0.63.",
                "answer_display": "-0.63",
            },
        ],
    },
    {
        "id": "dec-mult",
        "title": "Multiplying & Dividing Decimals",
        "emoji": "✖️",
        "color": "#FF6B6B",
        "blurb": "For × and ÷ the sign rule is simple: same signs give a positive answer, "
                 "different signs give a negative one. Work out the sizes first and put the "
                 "sign on at the end — that way you only have one thing to think about at a "
                 "time.",
        "key_concepts": [
            {
                "text": "Same signs → positive. Different signs → negative. The rule is "
                        "identical for × and ÷.",
                "visual": {
                    "type": "rules",
                    "items": [
                        {"expr": "(+) × (+)", "result": "+", "note": "2.5 × 4 = 10"},
                        {"expr": "(-) × (-)", "result": "+",
                         "note": "(-0.6) × (-2.5) = 1.5"},
                        {"expr": "(+) × (-)", "result": "-", "note": "2.8 × (-0.2) = -0.56"},
                        {"expr": "(-) ÷ (-)", "result": "+",
                         "note": "(-9.2) ÷ (-0.01) = 920"},
                        {"expr": "(-) ÷ (+)", "result": "-", "note": "(-5.5) ÷ 1.1 = -5"},
                        {"expr": "(+) ÷ (-)", "result": "-", "note": "2.4 ÷ (-0.8) = -3"},
                    ],
                    "caption": "Multiplying several numbers? Count the minus signs: an even "
                               "number of them gives a positive answer, an odd number gives a "
                               "negative one.",
                },
            },
            "Count decimal places when you multiply: 0.3 × 0.07 has 1 + 2 = 3 decimal "
            "places, so 3 × 7 = 21 becomes 0.021.",
            "To divide by a decimal, shift BOTH numbers the same number of places until you "
            "are dividing by a whole number: 3.7 ÷ 0.2 becomes 37 ÷ 2 = 18.5.",
            "Dividing by a number smaller than 1 makes the answer BIGGER, not smaller: "
            "(-9.2) ÷ (-0.01) = 920.",
        ],
        "examples": [
            {
                "prompt": "2.8 × (-0.2) =",
                "steps": "The signs are different, so the answer is negative. Sizes: "
                         "2.8 × 0.2 = 0.56. So the answer is -0.56.",
                "answer_display": "-0.56",
            },
            {
                "prompt": "(-9.2) ÷ (-0.01) =",
                "steps": "Same signs, so the answer is positive. Shift both numbers two "
                         "places: 920 ÷ 1 = 920.",
                "answer_display": "920",
            },
            {
                "prompt": "(-14.4) ÷ 1.2 =",
                "steps": "Different signs, so the answer is negative. Sizes: shift both one "
                         "place to get 144 ÷ 12 = 12. So the answer is -12.",
                "answer_display": "-12",
            },
        ],
    },
    {
        "id": "frac-add",
        "title": "Adding & Subtracting Fractions",
        "emoji": "\U0001F967",
        "color": "#7EC8E3",
        "blurb": "Turn every mixed number into an improper fraction first — it saves you from "
                 "borrowing. Then find the LCM of the denominators, rewrite both fractions "
                 "with it, and combine the numerators. The sign travels with the numerator.",
        "key_concepts": [
            "Mixed number → improper fraction, sign included: -3 {4/5} = -(3 × 5 + 4)/5 "
            "= {-19/5}. Do this before anything else.",
            "Subtracting a negative flips to adding: {4/5} - ({-3/10}) = {4/5} + {3/10}.",
            {
                "text": "Rewrite both fractions over the LCM of the denominators, then add "
                        "or subtract the numerators. Only the top changes.",
                "visual": {
                    "type": "bars",
                    "rows": [
                        {"label": "{4/5}", "n": 4, "d": 5, "color": "teal",
                         "note": "4/5 of a bar..."},
                        {"label": "{8/10}", "n": 8, "d": 10, "color": "teal",
                         "note": "...is the same amount, just cut into smaller pieces:"},
                        {"label": "{3/10}", "n": 3, "d": 10, "color": "orange",
                         "note": "now both are in tenths, so they can be combined:"},
                    ],
                    "caption": "{4/5} - ({-3/10}) = {8/10} + {3/10} = {11/10}.",
                },
            },
            "Reduce at the end. In this unit a fully reduced improper fraction like {-81/20} "
            "is the expected answer — you don't have to convert it to a mixed number.",
        ],
        "examples": [
            {
                "prompt": "{4/5} - ({-3/10}) =",
                "steps": "Subtracting a negative is adding: 4/5 + 3/10. The LCM of 5 and 10 "
                         "is 10, so 4/5 = 8/10. Then 8/10 + 3/10 = 11/10. GCD(11, 10) = 1, "
                         "so 11/10 is fully reduced.",
                "answer_display": "11/10",
            },
            {
                "prompt": "{-1/4} + {1_5/6} =",
                "steps": "1 5/6 = 11/6. The LCM of 4 and 6 is 12, so -1/4 = -3/12 and "
                         "11/6 = 22/12. Then -3 + 22 = 19, giving 19/12.",
                "answer_display": "19/12",
            },
            {
                "prompt": "{1_2/3} + ({-2_1/2}) =",
                "steps": "1 2/3 = 5/3 and -2 1/2 = -5/2. The LCM of 3 and 2 is 6, so "
                         "5/3 = 10/6 and -5/2 = -15/6. Then 10 + (-15) = -5, giving -5/6.",
                "answer_display": "-5/6",
            },
        ],
    },
    {
        "id": "frac-mult",
        "title": "Multiplying & Dividing Fractions",
        "emoji": "\U0001F501",
        "color": "#A8E6CF",
        "blurb": "No common denominator needed here. Multiply straight across; to divide, "
                 "keep-change-flip. The sign rule is exactly the same as for decimals: same "
                 "signs give a positive answer, different signs give a negative one.",
        "key_concepts": [
            {
                "text": "Decide the sign first, then forget about it until the end.",
                "visual": {
                    "type": "rules",
                    "items": [
                        {"expr": "{5/7} × ({-2/3})", "result": "-"},
                        {"expr": "({-9/7}) × ({-7/6})", "result": "+"},
                        {"expr": "{3/4} ÷ ({-6/7})", "result": "-"},
                        {"expr": "({-4/9}) ÷ ({-3/5})", "result": "+"},
                    ],
                    "caption": "Same signs → positive, different signs → negative — for both "
                               "× and ÷.",
                },
            },
            "Multiply straight across: (top × top) over (bottom × bottom). No LCM, no "
            "common denominator.",
            "Keep-change-flip to divide: {3/4} ÷ ({-6/7}) = {3/4} × ({-7/6}). The flipped "
            "fraction keeps its minus sign.",
            "Whole numbers become fractions over 1 (-5 = {-5/1}), and mixed numbers become "
            "improper fractions first ({2_2/3} = {8/3}).",
        ],
        "examples": [
            {
                "prompt": "{5/7} × ({-2/3}) =",
                "steps": "Different signs, so the answer is negative. Multiply across: "
                         "(5 × 2)/(7 × 3) = 10/21. GCD(10, 21) = 1, so -10/21 is fully "
                         "reduced.",
                "answer_display": "-10/21",
            },
            {
                "prompt": "-5 × {2_2/3} =",
                "steps": "2 2/3 = 8/3 and -5 = -5/1. Different signs, so the answer is "
                         "negative. Multiply across: (5 × 8)/(1 × 3) = 40/3, so -40/3.",
                "answer_display": "-40/3",
            },
            {
                "prompt": "{3/4} ÷ ({-6/7}) =",
                "steps": "Keep-change-flip: 3/4 × (-7/6). Different signs, so negative. "
                         "Multiply across: 21/24, and GCD(21, 24) = 3, so -7/8.",
                "answer_display": "-7/8",
            },
        ],
    },
    {
        "id": "order-ops",
        "title": "Order of Operations",
        "emoji": "\U0001F9EE",
        "color": "#FFE66D",
        "blurb": "BEDMAS: Brackets, Exponents, then Division and Multiplication in the order "
                 "they appear left to right, then Addition and Subtraction in the order they "
                 "appear. Square roots count as exponents, and a fraction bar acts as a "
                 "bracket — work out the top and the bottom before you divide.",
        "key_concepts": [
            {
                "text": "Work down this ladder. Division and multiplication share one rung, "
                        "and so do addition and subtraction — on a shared rung, go left to "
                        "right.",
                "visual": {
                    "type": "rules",
                    "items": [
                        {"expr": "Brackets ( )", "result": "1"},
                        {"expr": "Exponents ² and √", "result": "2"},
                        {"expr": "Divide ÷ and Multiply ×", "result": "3",
                         "note": "same rung — in the order they appear"},
                        {"expr": "Add + and Subtract -", "result": "4",
                         "note": "same rung — in the order they appear"},
                    ],
                },
            },
            "A fraction bar groups everything above it and everything below it: "
            "((-7.2) + 7.6) ÷ (-0.2) means work out 0.4 first, then divide.",
            "A number written right beside a bracket means multiply: "
            "-0.2(4.8 - 5.6) = -0.2 × (-0.8).",
            "Watch the sign on exponents: (-3)² = 9 because the bracket squares the minus "
            "too, but -3² = -9.",
            "Square roots come out at the Exponents step: √0.36 = 0.6 and "
            "√(4/9) = {2/3}.",
        ],
        "examples": [
            {
                "prompt": "-0.2(4.8 - 5.6) =",
                "steps": "Brackets first: 4.8 - 5.6 = -0.8. The number against the bracket "
                         "means multiply: -0.2 × (-0.8) = 0.16 — two negatives make a "
                         "positive.",
                "answer_display": "0.16",
            },
            {
                "prompt": "2.4 + 1.8 × (-2) ÷ (-0.6) =",
                "steps": "No brackets or exponents. × and ÷ share a rung, so go left to "
                         "right: 1.8 × (-2) = -3.6, then -3.6 ÷ (-0.6) = 6. Finally "
                         "2.4 + 6 = 8.4.",
                "answer_display": "8.4",
            },
            {
                "prompt": "({3/8} - {7/4}) × ({-1/3}) =",
                "steps": "Brackets first: the LCM of 8 and 4 is 8, so 3/8 - 14/8 = -11/8. "
                         "Then multiply: (-11/8) × (-1/3) = 11/24 — same signs, positive.",
                "answer_display": "11/24",
            },
        ],
    },
]


# ===========================================================================
#   Write the files
# ===========================================================================

def main():
    here = Path(__file__).resolve().parent
    counts = {}
    for q in QUESTIONS:
        counts[q["section"]] = counts.get(q["section"], 0) + 1

    ids = [s["id"] for s in SECTIONS]
    assert set(counts) == set(ids), (sorted(counts), sorted(ids))
    # Number problems come first in each topic, then word problems — the page
    # shows a "word problems start here" banner at the changeover.
    for sid in ids:
        kinds = [q["kind"] for q in QUESTIONS if q["section"] == sid]
        assert kinds == sorted(kinds, key=lambda k: k != "number"), (sid, kinds)

    lessons = {
        "meta": {
            "grade": 9,
            "unit": "rational-numbers",
            "title": "Rational Numbers",
            "emoji": "±",
            "description": "Compare and order rational numbers, then add, subtract, multiply "
                           "and divide them in both decimal and fraction form — negatives "
                           "included — and finish with order of operations.",
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
        print(f"  {s['id']:<12} {counts[s['id']]:>3} questions")


if __name__ == "__main__":
    main()
