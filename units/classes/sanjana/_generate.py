"""
One-time content generator for Sanjana's class notes.

This script is NOT called by the running app. It writes the static lessons.json
and questions.json that ship with it; the app only ever reads those files, and
nothing here runs at request time or calls any AI/LLM API.

Re-run with `python _generate.py` from this folder after editing below.

The content is one tutoring session, taken from the class plan doc
"Sanjana — Class 1: Fractions". That plan is built in two halves, and they map
onto the app's two halves exactly:

    "We do" (solved together)  ->  the worked examples on each topic's lesson
    "You do" (Sanjana tries)   ->  the practice questions

So the app is the same lesson, with the half she was meant to try herself
turned into questions that mark themselves. Where the plan asks two things in
one breath ("Is each one proper, improper or mixed? 9/8, 4/9, 1 5/6") each one
becomes its own question, because each is its own decision.

Every answer is computed with Python's exact `fractions.Fraction`, so the key
can't drift from the arithmetic.
"""
import json
from fractions import Fraction as F
from pathlib import Path

GROUP = "Fractions"
GROUP_EMOJI = "🍕"

sections = []
questions = []


def tok(value, mixed=False):
    """A prompt token: {a/b} stacks, {w_a/b} is a mixed number."""
    if value.denominator == 1:
        return str(value.numerator)
    if not mixed or abs(value) < 1:
        return "{%d/%d}" % (value.numerator, value.denominator)
    whole, num = divmod(abs(value).numerator, value.denominator)
    return "{%d_%d/%d}" % (whole if value > 0 else -whole, num, value.denominator)


def mixed_display(value):
    """How Grade 8 writes a final answer: a mixed number, never improper."""
    if value.denominator == 1:
        return str(value.numerator)
    whole, num = divmod(abs(value).numerator, value.denominator)
    if whole == 0:
        return "%d/%d" % (value.numerator, value.denominator)
    return "%s%d %d/%d" % ("-" if value < 0 else "", whole, num, value.denominator)


def qid(section, n):
    return f"{section}-{n:02d}"


def add(section, n, qtype, difficulty, prompt, answer, steps, tip, **extra):
    questions.append({
        "id": qid(section, n), "section": section, "qtype": qtype,
        "difficulty": difficulty, "prompt": prompt,
        **extra, "answer": answer, "steps": steps, "tip": tip,
    })


def ask_fraction(section, n, difficulty, prompt, value, steps, tip):
    """The answer is a number, given as a mixed number the way Grade 8 wants it."""
    value = F(value)
    whole, num = divmod(abs(value).numerator, value.denominator)
    if value.denominator == 1:
        whole, num, den = value.numerator, 0, 1
    else:
        den = value.denominator
        if value < 0:
            whole = -whole
    add(section, n, "fraction", difficulty, prompt,
        {"num": num, "den": den, "whole": whole, "display": mixed_display(value)},
        steps, tip)


def ask_choice(section, n, difficulty, prompt, options, answer, steps, tip):
    assert answer in options, (section, n, answer)
    add(section, n, "choice", difficulty, prompt,
        {"choice": answer, "display": answer}, steps, tip, options=options)


def ask_compare(section, n, difficulty, prompt, left, right, steps, tip):
    symbol = "<" if left < right else (">" if left > right else "=")
    add(section, n, "compare", difficulty, prompt,
        {"symbol": symbol, "display": symbol}, steps, tip)


def ask_integer(section, n, difficulty, prompt, value, steps, tip):
    add(section, n, "integer", difficulty, prompt,
        {"value": value, "display": str(value)}, steps, tip)


def add_section(sid, title, emoji, color, blurb, key_concepts, examples,
                group=GROUP, group_emoji=GROUP_EMOJI):
    sections.append({
        "id": sid, "title": title, "emoji": emoji, "color": color,
        "group": group, "group_emoji": group_emoji,
        "blurb": blurb, "key_concepts": key_concepts, "examples": examples,
    })


# ===== 1. What is a fraction? ==============================================

TIP_TYPES = ("Compare the top with the bottom. Top smaller than bottom is proper; "
             "top the same or bigger is improper; a whole number sitting beside a "
             "fraction is mixed.")

ask_choice("what-is", 1, 1, "Is {9/8} proper, improper or mixed?",
           ["Proper", "Improper", "Mixed"], "Improper",
           "9 is bigger than 8, so there is more than one whole here. That makes "
           "9/8 improper.", TIP_TYPES)
ask_choice("what-is", 2, 1, "Is {4/9} proper, improper or mixed?",
           ["Proper", "Improper", "Mixed"], "Proper",
           "4 is smaller than 9, so this is less than one whole. That makes 4/9 "
           "proper.", TIP_TYPES)
ask_choice("what-is", 3, 1, "Is {1_5/6} proper, improper or mixed?",
           ["Proper", "Improper", "Mixed"], "Mixed",
           "There is a whole number, 1, written beside a proper fraction, 5/6. A "
           "whole plus a fraction is a mixed number.", TIP_TYPES)
ask_fraction("what-is", 4, 2, "Write {17/5} as a mixed number.", F(17, 5),
             "Divide the top by the bottom: 17 ÷ 5 = 3 remainder 2. The 3 is the "
             "whole number and the remainder 2 becomes the new top, over the same "
             "bottom: 3 2/5.",
             "Divide top by bottom. The answer is the whole number and the "
             "remainder is the new top, over the same bottom.")
ask_choice("what-is", 5, 2, "Write {3_2/7} as an improper fraction.",
           ["{23/7}", "{5/7}", "{17/7}", "{32/7}"], "{23/7}",
           "Whole × bottom + top, over the same bottom: 3 × 7 + 2 = 23, so "
           "3 2/7 = 23/7.",
           "Multiply the whole number by the bottom, add the top, and keep the "
           "same bottom.")

add_section(
    "what-is", "What Is a Fraction?", "🔢", "#FF6B6B",
    "A fraction is part of a whole. The bottom number says how many equal pieces "
    "the whole was cut into; the top says how many of those pieces you have. Once "
    "you have more pieces than make one whole, you can write the same amount two "
    "ways — as an improper fraction or as a mixed number.",
    [
        "In {3/4} the bottom, 4, is how many equal pieces the whole was cut into. "
        "The top, 3, is how many you have.",
        "Proper means the top is smaller than the bottom, so it is less than one "
        "whole: {3/4}, {2/5}, {7/10}.",
        "Improper means the top is the same as or bigger than the bottom, so it is "
        "one whole or more: {5/4}, {9/2}, {6/6}.",
        "Mixed means a whole number written beside a proper fraction: {1_1/4}, "
        "{4_1/2}. It is the same amount as an improper fraction, written the "
        "friendlier way round.",
        "Improper to mixed: divide top by bottom. The answer is the whole number "
        "and the remainder is the new top. {7/4} → 7 ÷ 4 = 1 remainder 3 → {1_3/4}.",
        "Mixed to improper: whole × bottom + top, over the same bottom. "
        "{1_3/4} → (1 × 4 + 3)/4 = {7/4}.",
    ],
    [
        {"prompt": "Is each one proper, improper or mixed? {3/5}, {7/4}, {2_1/3}",
         "steps": "3/5: 3 is less than 5, so proper. 7/4: 7 is more than 4, so "
                  "improper. 2 1/3: a whole number beside a fraction, so mixed.",
         "answer_display": "proper, improper, mixed"},
        {"prompt": "Write {11/4} as a mixed number.",
         "steps": "11 ÷ 4 = 2 remainder 3. The 2 is the whole number and the 3 is "
                  "the new top, over 4.",
         "answer_display": "2 3/4"},
        {"prompt": "Write {2_3/5} as an improper fraction.",
         "steps": "2 × 5 + 3 = 13, over the same bottom of 5.",
         "answer_display": "13/5"},
    ],
)


# ===== 2. Greater or smaller? ==============================================

TIP_COMPARE = ("Turn any improper fraction into a mixed number first. Compare the "
               "whole numbers; only if they match do you compare the fraction parts, "
               "and for that they need the same bottom.")

ask_compare("compare", 1, 2, "Which sign goes between {13/5} and {2_1/2}?  (< , > , or =)",
            F(13, 5), F(5, 2),
            "13 ÷ 5 = 2 remainder 3, so 13/5 = 2 3/5. Both have 2 wholes, so "
            "compare 3/5 and 1/2. Over a common bottom of 10 that is 6/10 against "
            "5/10, and 6/10 is bigger. So 13/5 > 2 1/2.", TIP_COMPARE)
ask_choice("compare", 2, 1, "{13/5} sits between which two whole numbers?",
           ["1 and 2", "2 and 3", "3 and 4", "4 and 5"], "2 and 3",
           "13 ÷ 5 = 2 remainder 3, so 13/5 = 2 3/5. That is more than 2 and less "
           "than 3.",
           "Divide the top by the bottom. The whole-number part is the lower one, "
           "and the next number up is the higher one.")
ask_compare("compare", 3, 2, "Which sign goes between 4 and {17/4}?  (< , > , or =)",
            F(4), F(17, 4),
            "17 ÷ 4 = 4 remainder 1, so 17/4 = 4 1/4. Both have 4 wholes, but "
            "17/4 has a quarter more. So 4 < 17/4.", TIP_COMPARE)
ask_choice("compare", 4, 1, "{17/4} sits between which two whole numbers?",
           ["2 and 3", "3 and 4", "4 and 5", "5 and 6"], "4 and 5",
           "17 ÷ 4 = 4 remainder 1, so 17/4 = 4 1/4. That is more than 4 and less "
           "than 5.",
           "Divide the top by the bottom. The whole-number part is the lower one, "
           "and the next number up is the higher one.")

add_section(
    "compare", "Greater or Smaller?", "⚖️", "#4ECDC4",
    "To compare numbers that have wholes in them, get them into the same shape "
    "first. Turn every improper fraction into a mixed number, then compare the "
    "whole numbers. Only when the wholes match do you have to look at the "
    "fraction parts — and those need a common bottom before they can be compared.",
    [
        "Say out loud which two whole numbers each one sits between. {7/3} = "
        "{2_1/3}, so it sits between 2 and 3. That alone settles most comparisons.",
        "Bigger whole number wins, whatever the fractions are doing: {3_1/8} is "
        "bigger than {2_7/8}.",
        "Same whole number? Now compare the fraction parts, and give them the same "
        "bottom first. {1/3} and {1/2} become {2/6} and {3/6}.",
        "The signs: > means greater than, < means less than, = means equal.",
    ],
    [
        {"prompt": "Compare {7/3} and {2_1/2}.",
         "steps": "7 ÷ 3 = 2 remainder 1, so 7/3 = 2 1/3, sitting between 2 and 3. "
                  "Both have 2 wholes, so compare 1/3 and 1/2. Over 6 that is 2/6 "
                  "against 3/6, and 2/6 is smaller.",
         "answer_display": "7/3 < 2 1/2"},
        {"prompt": "Compare {11/4} and 3.",
         "steps": "11/4 = 2 3/4, which sits between 2 and 3. Two wholes is less "
                  "than three wholes, so the fraction parts never come into it.",
         "answer_display": "11/4 < 3"},
    ],
)


# ===== 3. Multiplying fractions ============================================

TIP_MULT = ("Top times top, bottom times bottom — no common denominator needed. "
            "Turn mixed numbers into improper fractions before you start, and "
            "simplify at the end.")

ask_fraction("multiply", 1, 1, "{4/5} × {3/8} =", F(4, 5) * F(3, 8),
             "Multiply straight across: (4 × 3)/(5 × 8) = 12/40. Both 12 and 40 "
             "divide by 4, so 12/40 = 3/10.", TIP_MULT)
ask_fraction("multiply", 2, 2, "{1_1/3} × {3/8} =", F(4, 3) * F(3, 8),
             "First turn the mixed number into an improper fraction: 1 1/3 = 4/3. "
             "Then (4 × 3)/(3 × 8) = 12/24, which simplifies to 1/2.", TIP_MULT)

add_section(
    "multiply", "Multiplying Fractions", "✖️", "#6C63FF",
    "Multiplying is the easy one: top times top, bottom times bottom. There is no "
    "common denominator to find, because you are not counting pieces of the same "
    "size — you are taking a fraction OF a fraction.",
    [
        "{2/3} × {3/4} means two thirds OF three quarters. Multiply straight "
        "across: (2 × 3)/(3 × 4) = {6/12}, which is {1/2}.",
        "A mixed number has to become an improper fraction first, or the whole "
        "number gets left out of the multiplication.",
        "Simplify at the end — or cross-cancel before you multiply, which keeps "
        "the numbers small enough to do in your head.",
        "An improper answer gets written back as a mixed number.",
    ],
    [
        {"prompt": "{2/3} × {3/4} =",
         "steps": "(2 × 3)/(3 × 4) = 6/12. Both divide by 6, so the answer is 1/2.",
         "answer_display": "1/2"},
        {"prompt": "{2_1/2} × {4/5} =",
         "steps": "2 1/2 = 5/2. Then (5 × 4)/(2 × 5) = 20/10, which is 2.",
         "answer_display": "2"},
    ],
)


# ===== 4. Dividing fractions ===============================================

TIP_DIV = ("Keep, Change, Flip: keep the first fraction, change ÷ to ×, flip the "
           "second one upside down. Mixed numbers become improper fractions before "
           "anything gets flipped.")

ask_fraction("divide", 1, 1, "{2/3} ÷ {4/9} =", F(2, 3) / F(4, 9),
             "Keep 2/3, change ÷ to ×, flip 4/9 to 9/4: 2/3 × 9/4 = 18/12 = 3/2, "
             "which is 1 1/2.", TIP_DIV)
ask_fraction("divide", 2, 2, "{1_3/4} ÷ {2/3} =", F(7, 4) / F(2, 3),
             "1 3/4 = 7/4 first. Then keep 7/4, change to ×, flip 2/3 to 3/2: "
             "7/4 × 3/2 = 21/8, which is 2 5/8.", TIP_DIV)

add_section(
    "divide", "Dividing Fractions", "➗", "#FF9F43",
    "Dividing by a fraction is multiplying by it upside down. Keep the first "
    "fraction, change the ÷ to a ×, flip the second one — then it is an ordinary "
    "multiplication.",
    [
        "Keep, Change, Flip. {3/4} ÷ {1/2} becomes {3/4} × {2/1}.",
        "Only the SECOND fraction gets flipped. The first one is left exactly as "
        "it is.",
        "Mixed numbers become improper fractions before anything is flipped, or "
        "you flip the wrong thing.",
        "Dividing by a fraction smaller than 1 makes the answer BIGGER, which "
        "feels wrong until you see why: how many halves fit into three quarters?",
    ],
    [
        {"prompt": "{3/4} ÷ {1/2} =",
         "steps": "Keep 3/4, change to ×, flip 1/2 to 2/1. Then 3/4 × 2/1 = 6/4 = "
                  "3/2, which is 1 1/2.",
         "answer_display": "1 1/2"},
        {"prompt": "{2_1/2} ÷ {5/6} =",
         "steps": "2 1/2 = 5/2. Then 5/2 × 6/5 = 30/10, which is 3.",
         "answer_display": "3"},
    ],
)


# ===== 5. Adding and subtracting ===========================================

TIP_ADDSUB = ("The bottoms have to match before you add or subtract, and they are "
              "never added themselves. With mixed numbers, turning them into "
              "improper fractions first avoids all the borrowing.")

ask_fraction("add-sub", 1, 1, "{3/5} + {1/10} =", F(3, 5) + F(1, 10),
             "The LCM of 5 and 10 is 10, so 3/5 = 6/10. Then 6/10 + 1/10 = 7/10.",
             TIP_ADDSUB)
ask_fraction("add-sub", 2, 3, "{2_1/4} + {1_2/3} =", F(9, 4) + F(5, 3),
             "Turn both into improper fractions: 2 1/4 = 9/4 and 1 2/3 = 5/3. The "
             "LCM of 4 and 3 is 12, so 27/12 + 20/12 = 47/12, which is 3 11/12.",
             TIP_ADDSUB)
ask_fraction("add-sub", 3, 1, "{7/8} - {1/4} =", F(7, 8) - F(1, 4),
             "The LCM of 8 and 4 is 8, so 1/4 = 2/8. Then 7/8 - 2/8 = 5/8.",
             TIP_ADDSUB)
ask_fraction("add-sub", 4, 3, "{4_1/3} - {2_3/4} =", F(13, 3) - F(11, 4),
             "Turn both into improper fractions: 4 1/3 = 13/3 and 2 3/4 = 11/4. "
             "The LCM of 3 and 4 is 12, so 52/12 - 33/12 = 19/12, which is 1 7/12.",
             TIP_ADDSUB)

add_section(
    "add-sub", "Adding & Subtracting", "➕", "#10AC84",
    "Adding and subtracting need the pieces to be the same size, which is what a "
    "common denominator is for. Find the LCM of the bottoms, rewrite both "
    "fractions over it, then work on the tops only — the bottom is finished once "
    "it matches.",
    [
        "Unlike multiplying, the bottoms are NEVER added. {1/4} + {2/3} is not "
        "{3/7}; it is {3/12} + {8/12} = {11/12}.",
        "Four steps every time: find the LCM of the bottoms, rewrite both "
        "fractions over it, add or subtract the tops, then simplify.",
        "With mixed numbers, turn them into improper fractions first. It is one "
        "more line of writing and it removes borrowing entirely.",
        "Why borrowing is the trap: {3_1/4} - {1_1/2} asks you to take {2/4} from "
        "{1/4}, which you cannot do as it stands. As {13/4} - {6/4} it is easy.",
    ],
    [
        {"prompt": "{1/3} + {1/6} =",
         "steps": "The LCM of 3 and 6 is 6, so 1/3 = 2/6. Then 2/6 + 1/6 = 3/6, "
                  "which simplifies to 1/2.",
         "answer_display": "1/2"},
        {"prompt": "{1_1/2} + {2/3} =",
         "steps": "1 1/2 = 3/2. The LCM of 2 and 3 is 6, so 9/6 + 4/6 = 13/6, "
                  "which is 2 1/6.",
         "answer_display": "2 1/6"},
        {"prompt": "{5/6} - {1/3} =",
         "steps": "The LCM is 6, so 1/3 = 2/6. Then 5/6 - 2/6 = 3/6 = 1/2.",
         "answer_display": "1/2"},
        {"prompt": "{3_1/4} - {1_1/2} =",
         "steps": "3 1/4 = 13/4 and 1 1/2 = 3/2 = 6/4. Then 13/4 - 6/4 = 7/4, "
                  "which is 1 3/4. Taking 1/2 from 1/4 directly does not work, "
                  "which is exactly why improper fractions help here.",
         "answer_display": "1 3/4"},
    ],
)


# ===== 6. Order of operations ==============================================

TIP_BEDMAS = ("BEDMAS: Brackets, Exponents, then Divide and Multiply left to right, "
              "then Add and Subtract left to right. Division and multiplication "
              "share a step, and so do adding and subtracting.")

ask_integer("bedmas", 1, 2, "(5 + 3) × 2 - 10 ÷ 5 =", 14,
            "Brackets first: 5 + 3 = 8. Then × and ÷ before + and -: 8 × 2 = 16 "
            "and 10 ÷ 5 = 2. Finally 16 - 2 = 14.", TIP_BEDMAS)
ask_fraction("bedmas", 2, 3, "({1/2} + {1/3}) ÷ {5/6} =", (F(1, 2) + F(1, 3)) / F(5, 6),
             "Brackets first: the LCM of 2 and 3 is 6, so 3/6 + 2/6 = 5/6. Then "
             "5/6 ÷ 5/6, and anything divided by itself is 1.", TIP_BEDMAS)

add_section(
    "bedmas", "Order of Operations", "🧮", "#B39DDB",
    "When a question has more than one operation, the order you do them in "
    "changes the answer. Brackets first, then exponents, then × and ÷ left to "
    "right, then + and - left to right. The fraction work is the same as ever — "
    "the new skill is choosing what to do next.",
    [
        {
            "text": "Work down this ladder every time. Division and multiplication "
                    "share a rung, and so do adding and subtracting: on a shared "
                    "rung, go left to right.",
            "visual": {
                "type": "rules",
                "items": [
                    {"expr": "Brackets ( )", "result": "1"},
                    {"expr": "Exponents like 2²", "result": "2"},
                    {"expr": "Divide ÷ and Multiply ×", "result": "3",
                     "note": "same rung — in the order they appear"},
                    {"expr": "Add + and Subtract -", "result": "4",
                     "note": "same rung — in the order they appear"},
                ],
            },
        },
        "Try it on whole numbers first. 3 + 4 × 2 is 11, not 14: the multiplying "
        "goes first. Going left to right is the mistake this rule exists to stop.",
        "(8 - 2) × 3 + 2² is 22: brackets give 6, the exponent gives 4, then "
        "6 × 3 = 18, then 18 + 4 = 22.",
        "Exactly the same rules with fractions. {1/2} + {1/4} × {2/3}: multiply "
        "first to get {1/6}, then {3/6} + {1/6} = {4/6} = {2/3}.",
        "Rewrite the whole line after each step, not just the part you changed. "
        "That is what stops a term getting left behind.",
    ],
    [
        {"prompt": "20 - 3 × 4 + 6 ÷ 2 =",
         "steps": "× and ÷ come first: 3 × 4 = 12 and 6 ÷ 2 = 3. Then work left to "
                  "right: 20 - 12 = 8, and 8 + 3 = 11.",
         "answer_display": "11"},
        {"prompt": "{3/4} - {1/2} × {1/3} =",
         "steps": "Multiply first: 1/2 × 1/3 = 1/6. Then 3/4 - 1/6. The LCM of 4 "
                  "and 6 is 12, so 9/12 - 2/12 = 7/12.",
         "answer_display": "7/12"},
    ],
)



# ===========================================================================
#   INTEGERS — Class 2
# ===========================================================================
# The sign rules are one idea used four ways, so the list opens by asking only
# which operation was done. Reading "-8 and -2 became -10" and answering "that
# was adding" is the same thinking as working out the answer, minus the
# arithmetic — and it is the thing that goes wrong first when the four rules
# start blurring into each other.

IGROUP = "Integers"
IGROUP_EMOJI = "➖"

TIP_SYMBOL = ("Look at what happened to the size and the sign. Bigger and same "
              "sign usually means adding or multiplying; a result smaller than "
              "both numbers usually means dividing.")


def ask_symbol(n, difficulty, prompt, symbol, steps):
    ask_choice("which-symbol", n, difficulty, prompt,
               ["+", "-", "×", "÷"], symbol, steps, TIP_SYMBOL)


ask_symbol(1, 1, "7 ? 5 = 12", "+",
           "7 and 5 came together to make something bigger than both, so this "
           "is adding: 7 + 5 = 12.")
ask_symbol(2, 1, "4 ? 9 = -5", "-",
           "The answer went below zero from two positive numbers, which only "
           "happens when you take the bigger one away: 4 - 9 = -5.")
ask_symbol(3, 2, "-3 ? 6 = -18", "×",
           "18 is far bigger than either number, so they were multiplied. "
           "Different signs give a negative: -3 × 6 = -18.")
ask_symbol(4, 2, "-20 ? 4 = -5", "÷",
           "The answer is smaller than both numbers, which points to dividing. "
           "Different signs give a negative: -20 ÷ 4 = -5.")
ask_symbol(5, 2, "-8 ? -2 = 16", "×",
           "Two negatives make a positive, and 16 is bigger than both, so this "
           "is multiplying: -8 × -2 = 16.")
ask_symbol(6, 3, "-8 ? -2 = -6", "-",
           "Taking away a negative adds it back: -8 - (-2) = -8 + 2 = -6.")
ask_symbol(7, 2, "-8 ? -2 = -10", "+",
           "Both are negative, so adding them goes further below zero: "
           "-8 + -2 = -10.")
ask_symbol(8, 3, "-8 ? -2 = 4", "÷",
           "Two negatives make a positive, and the answer is small, so this is "
           "dividing: -8 ÷ -2 = 4.")
ask_symbol(9, 2, "5 ? -3 = 2", "+",
           "Adding a negative is the same as taking it away: 5 + -3 = 2.")
ask_symbol(10, 3, "6 ? -2 = -3", "÷",
           "The answer is smaller than both, so it is dividing, and the "
           "different signs make it negative: 6 ÷ -2 = -3.")

add_section(
    "which-symbol", "Which Symbol?", "❓", "#FF6B6B",
    "Before working an answer out, read one. Each question shows two numbers "
    "and what they turned into, and asks only which operation did it. Getting "
    "this right means the four sign rules are separate in your head rather "
    "than blurred together.",
    [
        "Adding two negatives goes further below zero: -8 + -2 = -10.",
        "Taking away a negative adds it back: -8 - (-2) = -6.",
        "Multiplying or dividing two numbers with the SAME sign gives a "
        "positive: -8 × -2 = 16 and -8 ÷ -2 = 4.",
        "Multiplying or dividing two numbers with DIFFERENT signs gives a "
        "negative: -3 × 6 = -18 and -20 ÷ 4 = -5.",
        "Size is the clue to which one. Multiplying makes numbers bigger, "
        "dividing makes them smaller, adding and subtracting move them a "
        "little.",
    ],
    [
        {"prompt": "10 ? 2 = 20", "steps": "20 is far bigger than either "
         "number, which is what multiplying does.",
         "answer_display": "×"},
        {"prompt": "-9 ? 3 = -3", "steps": "The answer is smaller than both "
         "numbers, so they were divided, and the different signs make it "
         "negative.", "answer_display": "÷"},
    ],
    group=IGROUP, group_emoji=IGROUP_EMOJI,
)


# ===== Adding integers ======================================================

TIP_IADD = ("Same signs: add the sizes and keep the sign. Different signs: take "
            "the smaller size from the bigger one and keep the sign of the "
            "bigger one.")

for n, (prompt, value, steps) in enumerate([
    ("-5 + 3 =", -2, "Different signs, so 5 - 3 = 2. The 5 was bigger and it was "
     "negative, so the answer is -2."),
    ("-7 + (-4) =", -11, "Both negative, so add the sizes and keep the minus: "
     "7 + 4 = 11, giving -11."),
    ("9 + (-12) =", -3, "Different signs, so 12 - 9 = 3. The 12 was bigger and "
     "negative, so the answer is -3."),
    ("-15 + 15 =", 0, "Same size, opposite signs. They cancel exactly: 0."),
    ("-6 + (-6) =", -12, "Both negative: 6 + 6 = 12, so -12."),
    ("14 + (-5) =", 9, "Different signs, so 14 - 5 = 9. The 14 was bigger and "
     "positive, so the answer stays positive."),
    ("-20 + 8 =", -12, "Different signs, so 20 - 8 = 12, and the 20 was the "
     "bigger one, so -12."),
    ("-3 + (-9) + 5 =", -7, "Left to right: -3 + -9 = -12, then -12 + 5 = -7."),
], start=1):
    ask_integer("int-add", n, 1 if n <= 4 else 2, prompt, value, steps, TIP_IADD)

add_section(
    "int-add", "Adding Integers", "➕", "#4ECDC4",
    "Adding a negative moves you further down the number line; adding a "
    "positive moves you up. When the two signs match you are going the same "
    "way twice, and when they differ you are going back on yourself.",
    [
        "Same signs: add the sizes and keep the sign. -7 + -4 = -11.",
        "Different signs: take the smaller size from the bigger, and keep the "
        "sign of the bigger one. 9 + -12 = -3, because 12 is bigger and it was "
        "the negative one.",
        "Adding a negative is the same as subtracting: 5 + -3 is 5 - 3.",
        "Two numbers the same size with opposite signs cancel to 0.",
    ],
    [
        {"prompt": "-2 + (-8) =", "steps": "Both negative: add the sizes, "
         "2 + 8 = 10, and keep the minus.", "answer_display": "-10"},
        {"prompt": "11 + (-4) =", "steps": "Different signs, so 11 - 4 = 7. The "
         "11 was bigger and positive, so the answer stays positive.",
         "answer_display": "7"},
    ],
    group=IGROUP, group_emoji=IGROUP_EMOJI,
)


# ===== Subtracting integers =================================================

TIP_ISUB = ("Change it into an addition first: subtracting is adding the "
            "opposite. 6 - (-3) becomes 6 + 3, and -4 - 7 becomes -4 + -7.")

for n, (prompt, value, steps) in enumerate([
    ("-4 - 7 =", -11, "Adding the opposite: -4 + -7. Both negative, so -11."),
    ("6 - (-3) =", 9, "Taking away a negative adds it back: 6 + 3 = 9."),
    ("-5 - (-8) =", 3, "-5 + 8. Different signs, 8 - 5 = 3, and the 8 was "
     "bigger and positive, so 3."),
    ("-10 - (-10) =", 0, "-10 + 10, which cancels to 0."),
    ("12 - 20 =", -8, "12 + -20. The 20 is bigger and negative, so -8."),
    ("-3 - 9 =", -12, "-3 + -9. Both negative, so -12."),
    ("7 - (-7) =", 14, "7 + 7 = 14. Taking away a negative always makes it "
     "bigger."),
    ("-15 - (-6) =", -9, "-15 + 6. The 15 is bigger and negative, so -9."),
], start=1):
    ask_integer("int-sub", n, 1 if n <= 4 else 2, prompt, value, steps, TIP_ISUB)

add_section(
    "int-sub", "Subtracting Integers", "➖", "#6C63FF",
    "There is only one rule here, and it turns every subtraction into an "
    "addition you already know how to do: subtracting is adding the opposite. "
    "Once it is an addition, the adding rules take over.",
    [
        "Subtracting is adding the opposite. -4 - 7 becomes -4 + -7.",
        "Taking away a negative adds it back, so the answer gets BIGGER: "
        "6 - (-3) = 6 + 3 = 9.",
        "Two minus signs together always become a plus. That is the one to "
        "watch for.",
        "Rewrite it as an addition before you work anything out. It is one "
        "extra line and it removes most of the mistakes.",
    ],
    [
        {"prompt": "-6 - (-2) =", "steps": "Taking away a negative adds it "
         "back: -6 + 2 = -4.", "answer_display": "-4"},
        {"prompt": "3 - 8 =", "steps": "Adding the opposite: 3 + -8. The 8 is "
         "bigger and negative, so the answer is -5.", "answer_display": "-5"},
    ],
    group=IGROUP, group_emoji=IGROUP_EMOJI,
)


# ===== Multiplying integers =================================================

TIP_IMUL = ("Multiply the sizes, then decide the sign: same signs give a "
            "positive, different signs give a negative.")

for n, (prompt, value, steps) in enumerate([
    ("-6 × 4 =", -24, "6 × 4 = 24. Different signs, so -24."),
    ("-5 × (-7) =", 35, "5 × 7 = 35. Same signs, so the answer is positive."),
    ("8 × (-3) =", -24, "8 × 3 = 24. Different signs, so -24."),
    ("-9 × 0 =", 0, "Anything times 0 is 0, sign or no sign."),
    ("-12 × (-2) =", 24, "12 × 2 = 24. Two negatives make a positive."),
    ("7 × (-6) =", -42, "7 × 6 = 42. Different signs, so -42."),
    ("-4 × (-4) =", 16, "4 × 4 = 16, and two negatives give a positive."),
    ("-3 × 5 × (-2) =", 30, "Left to right: -3 × 5 = -15, then -15 × -2 = 30. "
     "Two negatives in the whole line, so the answer is positive."),
], start=1):
    ask_integer("int-mul", n, 1 if n <= 4 else 2, prompt, value, steps, TIP_IMUL)

add_section(
    "int-mul", "Multiplying Integers", "✖️", "#FF9F43",
    "Do the multiplying as if there were no signs at all, then put the sign on "
    "at the end. Same signs give a positive, different signs give a negative — "
    "and that one rule covers every case.",
    [
        "Same signs give a positive: -5 × -7 = 35, and 5 × 7 = 35.",
        "Different signs give a negative: -6 × 4 = -24.",
        "Count the negatives in the whole line. An even number of them gives a "
        "positive; an odd number gives a negative.",
        "Anything times 0 is 0, whatever the signs are doing.",
    ],
    [
        {"prompt": "-2 × (-9) =", "steps": "2 × 9 = 18, and the signs match, "
         "so the answer is positive.", "answer_display": "18"},
        {"prompt": "-7 × 3 =", "steps": "7 × 3 = 21, and the signs differ, so "
         "the answer is negative.", "answer_display": "-21"},
    ],
    group=IGROUP, group_emoji=IGROUP_EMOJI,
)


# ===== Dividing integers ====================================================

TIP_IDIV = ("The sign rule is exactly the same as multiplying: same signs give "
            "a positive, different signs give a negative.")

for n, (prompt, value, steps) in enumerate([
    ("-24 ÷ 6 =", -4, "24 ÷ 6 = 4. Different signs, so -4."),
    ("-36 ÷ (-9) =", 4, "36 ÷ 9 = 4. Same signs, so the answer is positive."),
    ("45 ÷ (-5) =", -9, "45 ÷ 5 = 9. Different signs, so -9."),
    ("-100 ÷ 10 =", -10, "100 ÷ 10 = 10. Different signs, so -10."),
    ("-8 ÷ (-8) =", 1, "8 ÷ 8 = 1, and two negatives give a positive."),
    ("56 ÷ (-7) =", -8, "56 ÷ 7 = 8. Different signs, so -8."),
    ("-63 ÷ (-9) =", 7, "63 ÷ 9 = 7, and the signs match, so it is positive."),
    ("0 ÷ (-5) =", 0, "0 shared into any number of parts is still 0."),
], start=1):
    ask_integer("int-div", n, 1 if n <= 4 else 2, prompt, value, steps, TIP_IDIV)

add_section(
    "int-div", "Dividing Integers", "➗", "#10AC84",
    "Dividing uses the very same sign rule as multiplying, so there is nothing "
    "new to learn here — divide the sizes, then same signs give a positive and "
    "different signs give a negative.",
    [
        "Same signs give a positive: -36 ÷ -9 = 4.",
        "Different signs give a negative: -24 ÷ 6 = -4.",
        "It is the same rule as multiplying, because dividing undoes "
        "multiplying: if -4 × 6 = -24, then -24 ÷ 6 = -4.",
        "0 divided by anything is 0. Anything divided by 0 is not a number at "
        "all.",
    ],
    [
        {"prompt": "-18 ÷ (-3) =", "steps": "18 ÷ 3 = 6, and the signs match, "
         "so the answer is positive.", "answer_display": "6"},
        {"prompt": "30 ÷ (-6) =", "steps": "30 ÷ 6 = 5, and the signs differ, "
         "so the answer is negative.", "answer_display": "-5"},
    ],
    group=IGROUP, group_emoji=IGROUP_EMOJI,
)


# ===== write =================================================================

def main():
    here = Path(__file__).resolve().parent
    ids = [s["id"] for s in sections]
    assert len({q["id"] for q in questions}) == len(questions)
    assert {q["section"] for q in questions} == set(ids), (
        sorted({q["section"] for q in questions}), sorted(ids))

    counts = {sid: sum(1 for q in questions if q["section"] == sid) for sid in ids}
    lessons = {
        "meta": {
            "grade": None,
            "unit": "sanjana",
            "title": "Sanjana",
            "emoji": "🌸",
            "description": "Class notes and practice, one session at a time. "
                           "Class 1 covers fractions end to end; Class 2 starts "
                           "integers, beginning with reading which operation was "
                           "done before doing any.",
            "sections": [
                {"id": s["id"], "title": s["title"], "emoji": s["emoji"],
                 "group": s["group"], "question_count": counts[s["id"]]}
                for s in sections
            ],
        },
        "sections": sections,
    }

    (here / "lessons.json").write_text(
        json.dumps(lessons, indent=2, ensure_ascii=False), encoding="utf-8")
    (here / "questions.json").write_text(
        json.dumps({"questions": questions}, indent=2, ensure_ascii=False),
        encoding="utf-8")
    print(f"Wrote {len(sections)} topics and {len(questions)} questions:")
    for sid in ids:
        print(f"  {sid:<10} {counts[sid]:>3}")


if __name__ == "__main__":
    main()
