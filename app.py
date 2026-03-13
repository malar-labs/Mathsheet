from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from markupsafe import Markup
from pydantic import BaseModel
from typing import List
from groq import Groq
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv

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

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

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

# ===== CURRICULUM DATA =====
GRADE8_TOPICS = {
    "perfect_squares_cubes": {
        "name": "Perfect Squares & Cubes",
        "emoji": "🔢",
        "color": "#FF6B6B",
        "bg": "#FFF0F0",
        "description": "Square roots, cube roots, prime factorization",
        "examples": ["√(16/169) = ?", "∛125 = ?", "Estimate √30"],
        "subtopics": [
            "Identifying perfect squares and perfect cubes",
            "Finding square roots using prime factorization",
            "Finding cube roots (e.g., ∛125)",
            "Estimating square roots of non-perfect squares (e.g., √30)",
            "Using colour tiles and multi-link cubes"
        ]
    },
    "percents": {
        "name": "Percents",
        "emoji": "💯",
        "color": "#6C63FF",
        "bg": "#F0EEFF",
        "description": "Decimal & fractional percents, percent problems",
        "examples": ["½% of 1 billion", "122% salary increase", "3.25% population growth"],
        "subtopics": [
            "Decimal percents less than 1% and greater than 100%",
            "Fractional percents (e.g., ½%)",
            "Finding original values after percent change",
            "Percent increase and decrease in real-life contexts",
            "BC population and salary problems"
        ]
    },
    "proportional_reasoning": {
        "name": "Proportional Reasoning",
        "emoji": "⚖️",
        "color": "#4ECDC4",
        "bg": "#EDFAFA",
        "description": "Two & three-term ratios, rates, proportions",
        "examples": ["3:5:7 string ratio (105 cm)", "Unit rates", "Cedar drum proportions"],
        "subtopics": [
            "Two-term ratios in real-life contexts",
            "Three-term ratios and problem solving",
            "Rates and unit rates",
            "Setting up and solving proportions",
            "First Peoples proportional sharing contexts"
        ]
    },
    "fractions": {
        "name": "Operations with Fractions",
        "emoji": "½",
        "color": "#F9CA24",
        "bg": "#FFFBEA",
        "description": "All operations with order of operations (brackets)",
        "examples": ["½ ÷ 9/6 × (7 – 4/5)", "BEDMAS with fractions", "Mixed operations"],
        "subtopics": [
            "Adding and subtracting fractions and mixed numbers",
            "Multiplying fractions and mixed numbers",
            "Dividing fractions and mixed numbers",
            "Order of operations with brackets (no exponents)",
            "Drumming and song fraction contexts"
        ]
    },
    "linear_relations": {
        "name": "Discrete Linear Relations",
        "emoji": "📈",
        "color": "#A8E6CF",
        "bg": "#F0FFF7",
        "description": "Two-variable relations, four quadrants, graphs",
        "examples": ["Table of values", "Four-quadrant integer graphs", "Scale values on axes"],
        "subtopics": [
            "Two-variable discrete linear relations",
            "Writing expressions from relationships",
            "Building and analyzing tables of values",
            "Graphing in four quadrants with integer coordinates",
            "Scale values on axes (e.g., tick marks = 5 units)"
        ]
    },
    "expressions": {
        "name": "Expressions",
        "emoji": "✏️",
        "color": "#FF8B94",
        "bg": "#FFF0F2",
        "description": "Algebraic expressions and substitution",
        "examples": ["Evaluate 0.5n – 3n + 25 if n=14", "Write expressions", "Substitution"],
        "subtopics": [
            "Writing expressions to describe relationships",
            "Evaluating algebraic expressions by substitution",
            "Simplifying algebraic expressions",
            "Real-life contexts for expressions",
            "Spirit canoe journey calculations"
        ]
    },
    "equations": {
        "name": "Two-Step Equations",
        "emoji": "🔧",
        "color": "#7EC8E3",
        "bg": "#EDF7FF",
        "description": "Solving and verifying equations with integers",
        "examples": ["Solve 3x – 4 = –12", "Verify solutions", "Integer coefficients"],
        "subtopics": [
            "Solving two-step equations with integer coefficients",
            "Verifying solutions by substitution",
            "Modelling with algebra tiles and balance diagrams",
            "Integer constants and solutions",
            "Word problems leading to two-step equations"
        ]
    },
    "surface_area_volume": {
        "name": "Surface Area & Volume",
        "emoji": "📦",
        "color": "#FF9F43",
        "bg": "#FFF5E6",
        "description": "Right prisms and cylinders",
        "examples": ["SA of triangular prism", "Volume = base area × height", "Cylinder volume"],
        "subtopics": [
            "Surface area of rectangular right prisms",
            "Surface area of triangular right prisms",
            "Surface area of cylinders",
            "Volume using V = base area × height",
            "Volume of cylinders (V = πr²h)"
        ]
    },
    "pythagorean_theorem": {
        "name": "Pythagorean Theorem",
        "emoji": "📐",
        "color": "#10AC84",
        "bg": "#EDFFF8",
        "description": "Finding missing sides of right triangles",
        "examples": ["a² + b² = c²", "Find hypotenuse", "Canoe path problems"],
        "subtopics": [
            "Understanding and deriving a² + b² = c²",
            "Finding the hypotenuse given two legs",
            "Finding a missing leg given hypotenuse and one leg",
            "Real-life applications (canoe paths, First Peoples constellations)",
            "Verifying whether a triangle is a right triangle"
        ]
    },
    "3d_objects": {
        "name": "3D Objects & Nets",
        "emoji": "🎲",
        "color": "#EE5A24",
        "bg": "#FFF2EE",
        "description": "Views, nets, and construction of 3D objects",
        "examples": ["Match net to 3D shape", "Top/front/side views", "Bentwood boxes"],
        "subtopics": [
            "Top, front, and side views of 3D objects",
            "Matching nets to corresponding 3D objects",
            "Drawing orthographic views from different perspectives",
            "Constructing 3D objects from nets",
            "First Peoples contexts: bentwood boxes, lidded baskets"
        ]
    },
    "central_tendency": {
        "name": "Central Tendency",
        "emoji": "📊",
        "color": "#0652DD",
        "bg": "#EEF2FF",
        "description": "Mean, median, and mode",
        "examples": ["Calculate mean of dataset", "Find median", "Identify mode"],
        "subtopics": [
            "Calculating the mean of a data set",
            "Finding the median (odd and even number of values)",
            "Identifying the mode (single and multiple modes)",
            "Comparing and choosing appropriate measures",
            "Applying central tendency to real BC data"
        ]
    },
    "probability": {
        "name": "Theoretical Probability",
        "emoji": "🎯",
        "color": "#9980FA",
        "bg": "#F5F2FF",
        "description": "Two independent events and sample space",
        "examples": ["P(5 on die AND head) = 1/12", "Tree diagrams", "Fair spinners"],
        "subtopics": [
            "Theoretical probability of a single event",
            "Probability of two independent events (multiply)",
            "Sample space using tree diagrams",
            "Sample space using tables/graphic organizers",
            "Determining if a game or spinner is fair"
        ]
    },
    "financial_literacy": {
        "name": "Financial Literacy",
        "emoji": "💰",
        "color": "#FDA7DF",
        "bg": "#FFF5FB",
        "description": "Unit price, coupons, proportional reasoning",
        "examples": ["Best unit price", "Coupon savings", "Value comparison"],
        "subtopics": [
            "Calculating and comparing unit prices",
            "Applying proportional reasoning to financial decisions",
            "Using coupons and calculating discounts",
            "Comparing products and services by value",
            "Making best-value decisions with given quantities and prices"
        ]
    }
}

GRADE6_TOPICS = {
    "large_numbers": {
        "name": "Large Numbers & Place Value",
        "emoji": "🔢",
        "color": "#10AC84",
        "bg": "#EDFFF8",
        "description": "Place value from thousandths to billions",
        "examples": ["Compare 4.125 and 4.152", "Order from billions to thousandths", "Round to nearest million"],
        "subtopics": [
            "Place value from thousandths to billions",
            "Comparing and ordering numbers (thousandths to billions)",
            "Estimating with large and small numbers",
            "Numbers used in science, medicine, technology, and media",
            "Operations with thousandths to billions"
        ]
    },
    "multiplication_division_facts": {
        "name": "Multiplication & Division Facts",
        "emoji": "✖️",
        "color": "#FF6B6B",
        "bg": "#FFF0F0",
        "description": "Facts to 100 and mental math strategies",
        "examples": ["23 × 4 using double-double", "Mental math strategies", "Fluency drills"],
        "subtopics": [
            "Multiplication and division facts to 100",
            "Mental math strategies (e.g., double-double to multiply 23 × 4)",
            "Developing computational fluency",
            "Applying strategies to larger numbers"
        ]
    },
    "order_of_operations_g6": {
        "name": "Order of Operations",
        "emoji": "🔣",
        "color": "#6C63FF",
        "bg": "#F0EEFF",
        "description": "BEDMAS with brackets, whole numbers (no exponents)",
        "examples": ["(4 + 2) × 3 – 1", "18 ÷ (2 + 1) × 4", "Quotients as rational numbers"],
        "subtopics": [
            "Order of operations with whole numbers",
            "Use of brackets (no exponents)",
            "Quotients that are rational numbers",
            "Multi-step calculations with all four operations"
        ]
    },
    "factors_multiples": {
        "name": "Factors & Multiples",
        "emoji": "🌳",
        "color": "#FF9F43",
        "bg": "#FFF5E6",
        "description": "Prime/composite, GCF, LCM, factor trees",
        "examples": ["300 = 2² × 3 × 5²", "GCF of 24 and 36", "LCM using Venn diagram"],
        "subtopics": [
            "Prime and composite numbers",
            "Divisibility rules",
            "Factor trees and prime factor phrase (e.g., 300 = 2² × 3 × 5²)",
            "Greatest common factor (GCF)",
            "Least common multiple (LCM) using Venn diagrams"
        ]
    },
    "fractions_mixed_numbers": {
        "name": "Fractions & Mixed Numbers",
        "emoji": "½",
        "color": "#4ECDC4",
        "bg": "#EDFAFA",
        "description": "Improper fractions, mixed numbers, comparing & ordering",
        "examples": ["Convert 7/4 to 1¾", "Compare 3/5 and 5/8", "Order on number line"],
        "subtopics": [
            "Improper fractions and mixed numbers",
            "Comparing and ordering fractions using benchmarks and number lines",
            "Using common denominators to compare",
            "Using pattern blocks, fraction strips, and fraction circles",
            "Birchbark biting connections"
        ]
    },
    "ratios_g6": {
        "name": "Introduction to Ratios",
        "emoji": "⚖️",
        "color": "#FDA7DF",
        "bg": "#FFF5FB",
        "description": "Part-to-part and part-to-whole ratios, equivalent ratios",
        "examples": ["3:5 ratio of boys to girls", "Equivalent ratios", "Part-to-whole"],
        "subtopics": [
            "Comparing numbers and quantities using ratios",
            "Part-to-part ratios",
            "Part-to-whole ratios",
            "Equivalent ratios",
            "Connecting ratios to fractions and percents"
        ]
    },
    "percents_g6": {
        "name": "Whole-Number Percents",
        "emoji": "💯",
        "color": "#EE5A24",
        "bg": "#FFF2EE",
        "description": "Percent of a whole, discounts, 50% = ½ = 0.5",
        "examples": ["50% = ½ = 0.5 = 50:100", "25% discount on $80", "Find the whole given percent"],
        "subtopics": [
            "Representing whole-number percents using base 10 blocks and grids",
            "Finding missing part (whole or percentage)",
            "50% = 1/2 = 0.5 = 50:100 equivalency",
            "Percentage discounts",
            "Connecting percents to fractions and decimals"
        ]
    },
    "decimal_operations": {
        "name": "Decimal Operations",
        "emoji": "🔟",
        "color": "#7EC8E3",
        "bg": "#EDF7FF",
        "description": "Multiply and divide decimals (e.g., 0.125 × 3, 7.2 ÷ 9)",
        "examples": ["0.125 × 3 = 0.375", "7.2 ÷ 9 = 0.8", "Base 10 block arrays"],
        "subtopics": [
            "Multiplying decimals (e.g., 0.125 × 3)",
            "Dividing decimals (e.g., 7.2 ÷ 9)",
            "Using base 10 block arrays",
            "Estimating decimal products and quotients",
            "Real-life decimal contexts"
        ]
    },
    "patterns_g6": {
        "name": "Increasing & Decreasing Patterns",
        "emoji": "📈",
        "color": "#A8E6CF",
        "bg": "#F0FFF7",
        "description": "Expressions, tables, graphs in the first quadrant",
        "examples": ["3, 5, 7… → 2n+1", "Table of values", "Graph in first quadrant"],
        "subtopics": [
            "Increasing and decreasing patterns (first quadrant, discrete points)",
            "Describing patterns using expressions (e.g., 2n + 1)",
            "Tables of values and graphs as functional relationships",
            "Visual patterning with colour tiles",
            "Graphing First Peoples language data"
        ]
    },
    "one_step_equations": {
        "name": "One-Step Equations",
        "emoji": "✏️",
        "color": "#FF8B94",
        "bg": "#FFF0F2",
        "description": "Whole-number coefficients and solutions",
        "examples": ["3x = 12", "x + 5 = 11", "Balance model"],
        "subtopics": [
            "Solving one-step equations (e.g., 3x = 12, x + 5 = 11)",
            "Preservation of equality using a balance",
            "Using algebra tiles",
            "Whole-number coefficients and solutions",
            "Real-life one-step equation problems"
        ]
    },
    "perimeter_area": {
        "name": "Perimeter & Area",
        "emoji": "📐",
        "color": "#9980FA",
        "bg": "#F5F2FF",
        "description": "Complex shapes, triangles, parallelograms, trapezoids",
        "examples": ["Perimeter of an L-shape", "Area of a triangle: ½bh", "Area of trapezoid"],
        "subtopics": [
            "Perimeter of complex shapes (composed of rectangles)",
            "Area of triangles using A = ½ × b × h",
            "Area of parallelograms",
            "Area of trapezoids",
            "Deriving area formulas with grid paper"
        ]
    },
    "angles": {
        "name": "Angles & Polygons",
        "emoji": "📏",
        "color": "#0652DD",
        "bg": "#EEF2FF",
        "description": "Types of angles, measuring, polygon angles",
        "examples": ["Identify reflex angle", "Estimate using 90° reference", "Angles in a triangle"],
        "subtopics": [
            "Straight, acute, right, obtuse, and reflex angles",
            "Constructing and identifying angles",
            "Estimating angles using 45°, 90°, and 180° as references",
            "Angles of polygons",
            "Examples from local BC environment"
        ]
    },
    "volume_capacity": {
        "name": "Volume & Capacity",
        "emoji": "📦",
        "color": "#F9CA24",
        "bg": "#FFFBEA",
        "description": "3D objects, cm³, m³, mL, L",
        "examples": ["Volume using unit cubes", "cm³ vs mL relationship", "How many mL in 1 L"],
        "subtopics": [
            "Building 3D objects with cubes to find volume",
            "Referents and relationships between units (cm³, m³, mL, L)",
            "Volume vs capacity distinction",
            "Real-life capacity contexts (berry baskets, seaweed drying)",
            "Estimating and measuring volume"
        ]
    },
    "triangles_classification": {
        "name": "Triangle Classification",
        "emoji": "🔺",
        "color": "#10AC84",
        "bg": "#EDFFF8",
        "description": "Scalene, isosceles, equilateral; right, acute, obtuse",
        "examples": ["Classify by sides and angles", "Right isosceles triangle", "Draw acute scalene"],
        "subtopics": [
            "Scalene, isosceles, and equilateral triangles",
            "Right, acute, and obtuse triangles",
            "Classifying triangles regardless of orientation",
            "Constructing triangles with given properties",
            "Identifying triangles in real-world shapes"
        ]
    },
    "transformations_g6": {
        "name": "Transformations",
        "emoji": "🔄",
        "color": "#FF6B6B",
        "bg": "#FFF0F0",
        "description": "Translation, rotation, reflection in first quadrant",
        "examples": ["Translate shape 3 right, 2 up", "Reflect over y-axis", "Rotate 90°"],
        "subtopics": [
            "Plotting points on Cartesian plane (first quadrant, whole-number ordered pairs)",
            "Translation of a 2D shape",
            "Rotation of a 2D shape",
            "Reflection of a 2D shape",
            "First Peoples art: Inuit, Northwest coastal art, frieze work"
        ]
    },
    "line_graphs": {
        "name": "Line Graphs",
        "emoji": "📉",
        "color": "#6C63FF",
        "bg": "#F0EEFF",
        "description": "Creating and interpreting line graphs from data",
        "examples": ["Graph temperature over a week", "Interpret trend", "Table of values to graph"],
        "subtopics": [
            "Creating line graphs from tables of values",
            "Interpreting line graphs",
            "Identifying trends and patterns",
            "Graphing First Peoples language data",
            "Connecting tables, graphs, and data sets"
        ]
    },
    "probability_g6": {
        "name": "Single-Outcome Probability",
        "emoji": "🎯",
        "color": "#4ECDC4",
        "bg": "#EDFAFA",
        "description": "Theoretical and experimental probability",
        "examples": ["P(heads) = ½", "Roll a die: P(>4) = 2/6", "Compare experimental vs theoretical"],
        "subtopics": [
            "Single-outcome probability events (spinner, die, coin)",
            "Listing all possible outcomes",
            "Theoretical probability",
            "Experimental probability and multiple trials",
            "Comparing experimental results with theoretical expectation"
        ]
    },
    "financial_literacy_g6": {
        "name": "Financial Literacy",
        "emoji": "💰",
        "color": "#FDA7DF",
        "bg": "#FFF5FB",
        "description": "Saving, purchasing, simple budgeting",
        "examples": ["How many weeks to save for a $120 bike?", "Compare prices", "Simple budget"],
        "subtopics": [
            "Informed decision making on saving and purchasing",
            "Simple budgeting scenarios",
            "Consumer math (e.g., weeks of allowance to buy something)",
            "Comparing costs and value",
            "Planning purchases using math"
        ]
    }
}

GRADE7_TOPICS = {
    "computational_fluency": {
        "name": "Computational Fluency",
        "emoji": "🧮",
        "color": "#FF6B6B",
        "bg": "#FFF0F0",
        "description": "Multiplication/division facts, extending to larger numbers",
        "examples": ["214 × 5: multiply by 10, divide by 2", "Mental strategies", "Fluency to 100"],
        "subtopics": [
            "Multiplication and division facts to 100",
            "Mental math strategies for larger numbers (e.g., 214 × 5 = 214 × 10 ÷ 2)",
            "Extending whole-number strategies to multi-digit numbers",
            "Developing and explaining mental math strategies"
        ]
    },
    "integer_operations": {
        "name": "Integer Operations",
        "emoji": "➕",
        "color": "#6C63FF",
        "bg": "#F0EEFF",
        "description": "Add, subtract, multiply, divide integers with order of operations",
        "examples": ["9 – (–4) = 13", "(–3) × (–5) = 15", "–12 ÷ 4 = –3"],
        "subtopics": [
            "Adding and subtracting integers (e.g., 9 – (–4) = 13)",
            "Multiplying and dividing integers",
            "Order of operations with integers (brackets, no exponents)",
            "Using two-sided counters and number lines",
            "Real-life integer contexts (temperature, elevation)"
        ]
    },
    "decimal_operations_g7": {
        "name": "Decimal Operations",
        "emoji": "🔟",
        "color": "#4ECDC4",
        "bg": "#EDFAFA",
        "description": "All operations with decimals, BEDMAS with brackets",
        "examples": ["3.6 × (2.1 + 0.9) ÷ 3", "Order of operations", "Decimal estimation"],
        "subtopics": [
            "Addition, subtraction, multiplication, and division of decimals",
            "Order of operations with decimals (brackets, no exponents)",
            "Estimation strategies for decimals",
            "Connecting decimal operations to whole-number strategies",
            "Real-life decimal problem solving"
        ]
    },
    "fractions_decimals_percents": {
        "name": "Fractions, Decimals, Ratios & Percents",
        "emoji": "🔄",
        "color": "#FF9F43",
        "bg": "#FFF5E6",
        "description": "Conversions, equivalency, terminating vs repeating decimals",
        "examples": ["½ = 0.5 = 50% = 50:100", "Convert 1/3 = 0.333…", "Compare ¾ and 0.8"],
        "subtopics": [
            "Converting between fractions, decimals, ratios, and percents",
            "Terminating versus repeating decimals",
            "Comparing and ordering fractions and decimals on a number line",
            "Equivalency: ½ = 0.5 = 50% = 50:100",
            "Shoreline cleanup context problems"
        ]
    },
    "linear_relations_g7": {
        "name": "Discrete Linear Relations",
        "emoji": "📈",
        "color": "#A8E6CF",
        "bg": "#F0FFF7",
        "description": "Four quadrants, expressions, tables, and graphs",
        "examples": ["3n + 2 table of values", "Graph in four quadrants", "Derive relation from graph"],
        "subtopics": [
            "Two-variable discrete linear relations (four quadrants, integral coordinates)",
            "Writing expressions (e.g., 3n + 2: starts at 2, increases by 3)",
            "Building tables of values",
            "Graphing and interpreting linear relations",
            "Deriving the relation from a graph or table"
        ]
    },
    "two_step_equations_g7": {
        "name": "Two-Step Equations",
        "emoji": "🔧",
        "color": "#FF8B94",
        "bg": "#FFF0F2",
        "description": "Solving and verifying, whole-number coefficients",
        "examples": ["3x + 4 = 16", "Verify by substitution", "Algebra tiles model"],
        "subtopics": [
            "Solving two-step equations (e.g., 3x + 4 = 16)",
            "Verifying solutions by substitution",
            "Modelling preservation of equality (balance, algebra tiles)",
            "Whole-number coefficients, constants, and solutions",
            "Spirit canoe trip calculation contexts"
        ]
    },
    "circles": {
        "name": "Circumference & Area of Circles",
        "emoji": "⭕",
        "color": "#7EC8E3",
        "bg": "#EDF7FF",
        "description": "C = π × d and A = π × r² formulas",
        "examples": ["C = π × 6 cm", "A = π × 5² cm²", "Find radius given circumference"],
        "subtopics": [
            "Finding relationships between radius, diameter, and circumference",
            "Deriving and applying C = π × d",
            "Applying A = π × r² to find area given radius or diameter",
            "Constructing circles given radius, diameter, area, or circumference",
            "First Peoples contexts: drummaking, dreamcatcher making"
        ]
    },
    "volume_g7": {
        "name": "Volume of Prisms & Cylinders",
        "emoji": "📦",
        "color": "#10AC84",
        "bg": "#EDFFF8",
        "description": "V = base area × height for rectangular prisms and cylinders",
        "examples": ["V of rectangular prism 4×3×5", "V of cylinder r=3, h=8", "V = πr²h"],
        "subtopics": [
            "Volume = area of base × height",
            "Volume of rectangular prisms",
            "Volume of cylinders (V = π × r² × h)",
            "Solving for missing dimensions given volume",
            "Bentwood boxes and birch bark scroll contexts"
        ]
    },
    "cartesian_coordinates": {
        "name": "Cartesian Coordinates",
        "emoji": "🗺️",
        "color": "#EE5A24",
        "bg": "#FFF2EE",
        "description": "Four quadrants, integral coordinates, graphing",
        "examples": ["Plot (–3, 4)", "Identify quadrant", "Connect to linear relations"],
        "subtopics": [
            "Origin, four quadrants, and integral coordinates",
            "Plotting and reading points in all four quadrants",
            "Connecting coordinates to linear relations and transformations",
            "Overlaying coordinate plane on traditional maps and medicine wheels",
            "Beading on dreamcatcher coordinate contexts"
        ]
    },
    "transformations_g7": {
        "name": "Combinations of Transformations",
        "emoji": "🔄",
        "color": "#9980FA",
        "bg": "#F5F2FF",
        "description": "Translation, rotation, reflection in four quadrants; tessellations",
        "examples": ["Translate then reflect", "Tessellation with a shape", "Successive transformations"],
        "subtopics": [
            "Translation, rotation, and reflection in four quadrants",
            "Combinations of successive transformations on a 2D shape",
            "Tessellations",
            "First Peoples art: jewelry making, birchbark biting",
            "Describing transformation sequences"
        ]
    },
    "circle_graphs": {
        "name": "Circle Graphs",
        "emoji": "🥧",
        "color": "#0652DD",
        "bg": "#EEF2FF",
        "description": "Constructing, labelling, and interpreting circle graphs",
        "examples": ["40% of 360° = 144°", "Translate % to quantities", "Compare two circle graphs"],
        "subtopics": [
            "Constructing circle graphs from data",
            "Labelling and interpreting circle graphs",
            "Translating percentages to quantities and vice versa",
            "Visual representations of tidepools or traditional meals",
            "Connecting circle graphs to percent and fraction concepts"
        ]
    },
    "probability_g7": {
        "name": "Experimental Probability",
        "emoji": "🎲",
        "color": "#F9CA24",
        "bg": "#FFFBEA",
        "description": "Two independent events, multiple trials",
        "examples": ["Toss two coins: P(HH) = ¼", "Roll two dice", "Experimental vs theoretical"],
        "subtopics": [
            "Experimental probability with multiple trials",
            "Two independent events (e.g., toss two coins, roll two dice)",
            "Sample space for combined events",
            "Comparing experimental results with theoretical probability",
            "First Peoples dice games"
        ]
    },
    "financial_literacy_g7": {
        "name": "Financial Literacy",
        "emoji": "💰",
        "color": "#FDA7DF",
        "bg": "#FFF5FB",
        "description": "Sales tax, tips, discounts, sale price",
        "examples": ["12% tax on $45", "15% tip on $60", "Sale: 30% off $120"],
        "subtopics": [
            "Calculating sales tax (e.g., 12% of $45)",
            "Calculating tips (e.g., 15% of a restaurant bill)",
            "Finding discount amounts and sale prices",
            "Multi-step financial percentage problems",
            "Comparing costs with and without tax or discount"
        ]
    }
}

CURRICULUM = {
    6: GRADE6_TOPICS,
    7: GRADE7_TOPICS,
    8: GRADE8_TOPICS,
}


def build_system_prompt(grade: int) -> str:
    grade_contexts = {
        6: {
            "level": "Grade 6",
            "age": "11–12 years old",
            "topics": """BC GRADE 6 MATHEMATICS CURRICULUM TOPICS:
1. Large Numbers & Place Value — thousandths to billions, compare, order, estimate
2. Multiplication & Division Facts — to 100, mental math strategies (e.g., double-double)
3. Order of Operations — brackets with whole numbers, no exponents, quotients can be rational
4. Factors & Multiples — prime/composite, divisibility rules, factor trees, GCF, LCM, Venn diagrams
5. Fractions & Mixed Numbers — improper fractions, comparing/ordering, benchmarks, number line
6. Introduction to Ratios — part-to-part, part-to-whole, equivalent ratios
7. Whole-Number Percents — 50%=½=0.5, finding missing part, percentage discounts
8. Decimal Operations — multiply and divide decimals (e.g., 0.125×3, 7.2÷9)
9. Increasing & Decreasing Patterns — first quadrant, expressions (e.g., 2n+1), tables, graphs
10. One-Step Equations — whole-number coefficients/solutions (e.g., 3x=12, x+5=11), balance model
11. Perimeter & Area — complex shapes, triangles (½bh), parallelograms, trapezoids
12. Angles & Polygons — straight/acute/right/obtuse/reflex, constructing, polygon angles
13. Volume & Capacity — cubes, 3D objects, cm³, m³, mL, L relationships
14. Triangle Classification — scalene/isosceles/equilateral; right/acute/obtuse
15. Transformations — first quadrant, translation/rotation/reflection on a 2D shape
16. Line Graphs — creating and interpreting from tables of values
17. Single-Outcome Probability — theoretical and experimental, listing outcomes
18. Financial Literacy — saving, purchasing, simple budgeting, consumer math"""
        },
        7: {
            "level": "Grade 7",
            "age": "12–13 years old",
            "topics": """BC GRADE 7 MATHEMATICS CURRICULUM TOPICS:
1. Computational Fluency — multiplication/division facts to 100, extending strategies to larger numbers
2. Integer Operations — add/subtract/multiply/divide integers, order of operations (brackets, no exponents)
3. Decimal Operations — all operations with decimals, BEDMAS with brackets (no exponents)
4. Fractions, Decimals, Ratios & Percents — conversions, equivalency, terminating vs repeating decimals, comparing on number line
5. Discrete Linear Relations — four quadrants, integral coordinates, expressions, tables, graphs
6. Two-Step Equations — solving and verifying (e.g., 3x+4=16), whole-number coefficients/constants/solutions
7. Circumference & Area of Circles — C=π×d, A=π×r², constructing circles
8. Volume of Prisms & Cylinders — V=base area×height for rectangular prisms and cylinders
9. Cartesian Coordinates — four quadrants, integral coordinates, graphing
10. Combinations of Transformations — four quadrants, translation/rotation/reflection, tessellations
11. Circle Graphs — constructing, labelling, interpreting, translating % to quantities
12. Experimental Probability — two independent events, multiple trials, comparing experimental vs theoretical
13. Financial Literacy — sales tax, tips, discounts, sale price"""
        },
        8: {
            "level": "Grade 8",
            "age": "13–14 years old",
            "topics": """BC GRADE 8 MATHEMATICS CURRICULUM TOPICS:
1. Perfect Squares & Cubes — prime factorization, square roots (e.g., √(16/169)), cube roots (e.g., ∛125), estimating square roots (e.g., √30)
2. Percents — decimal percents (<1% and >100%), fractional percents (e.g., ½%), percent increase/decrease, finding original values
3. Proportional Reasoning — two-term and three-term ratios, rates, unit rates, proportions, proportional sharing
4. Operations with Fractions — all 4 operations, BEDMAS with brackets (NO exponents)
5. Discrete Linear Relations — two-variable, four quadrants, integer coordinates, expressions, tables, graphs
6. Expressions — writing and evaluating algebraic expressions, substitution
7. Two-Step Equations — integer coefficients/constants/solutions, solving and verifying
8. Surface Area & Volume — right prisms (rectangular and triangular) and cylinders
9. Pythagorean Theorem — a²+b²=c², finding missing hypotenuse or leg, applications
10. 3D Objects & Nets — top/front/side views, matching nets, drawing and interpreting views
11. Central Tendency — mean, median, mode; choosing appropriate measure
12. Theoretical Probability — two independent events, P(A and B)=P(A)×P(B), sample space
13. Financial Literacy — unit price, coupons, comparing products/services"""
        }
    }

    ctx = grade_contexts.get(grade, grade_contexts[8])
    return f"""You are an expert BC (British Columbia) {ctx['level']} Mathematics teacher and curriculum specialist. Your ONLY purpose is to generate high-quality, accurate math worksheets strictly aligned with the BC {ctx['level']} Mathematics curriculum.

CRITICAL RULES — FOLLOW THESE WITHOUT EXCEPTION:
1. ONLY generate content for BC {ctx['level']} Mathematics curriculum topics listed below.
2. NEVER generate worksheets for any other subject, grade level, or curriculum.
3. All mathematical calculations must be 100% accurate — double-check every answer.
4. Content must be age-appropriate for {ctx['level']} students (approximately {ctx['age']}).
5. Where appropriate, incorporate First Peoples perspectives and BC cultural contexts as required by the BC curriculum.
6. Use Canadian contexts: Canadian dollars (CAD), BC geography (Vancouver, Victoria, Fraser River, etc.).

{ctx['topics']}

OUTPUT FORMAT — CRITICAL:
Return ONLY a valid JSON object. No markdown. No code blocks. No extra text. Just the raw JSON.

JSON Structure:
{{
  "title": "worksheet title string",
  "grade": "{ctx['level']}",
  "topic": "topic name(s) string",
  "curriculum": "BC Mathematics Curriculum",
  "instructions": "brief student-facing instructions string",
  "estimated_time": "e.g. 30 minutes",
  "questions": [
    {{
      "number": 1,
      "question": "complete question text string",
      "type": "word OR number",
      "difficulty": "easy OR medium OR hard",
      "space_needed": "small OR medium OR large",
      "answer": "correct answer string",
      "solution_steps": "detailed step-by-step solution string"
    }}
  ]
}}"""


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
    if not GROQ_API_KEY:
        return JSONResponse({
            "success": False,
            "error": "Groq API key not configured. Add GROQ_API_KEY to your .env file. Get a free key at https://console.groq.com/keys"
        })

    try:
        client = Groq(api_key=GROQ_API_KEY)

        topics = body.topics
        grade = body.grade
        grade_topics = CURRICULUM.get(grade, GRADE8_TOPICS)
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

        prompt = f"""Create a BC Grade {grade} Mathematics worksheet with EXACTLY {num_questions} questions.

TOPICS TO COVER: {", ".join(topic_names)}
PROBLEM TYPES: {problem_type_desc}
DIFFICULTY: {difficulty_desc}
TOTAL QUESTIONS: Exactly {num_questions}

DISTRIBUTION: Spread questions across all {len(topic_names)} topic(s), approximately {per_topic} question(s) per topic. If uneven, add extras to the first topic.

QUESTION REQUIREMENTS:
- Every answer must be mathematically verified and correct
- Word problems: use BC contexts — Vancouver, Victoria, Fraser River, Pacific coast, First Peoples traditions (beading, drumming, cedar boxes, paddle making, canoe journeys, harvest sharing), Canadian dollars (CAD), BC wildlife, hockey
- Number problems: show clear numerical setup
- space_needed: "small" for one-line answers, "medium" for 3–5 lines of work, "large" for multi-step word problems or diagrams
- solution_steps: provide full step-by-step working, showing every intermediate calculation clearly

TOPIC-SPECIFIC NOTES:
- Perfect Squares/Cubes: include at least one estimation problem and one using prime factorization
- Percents: include both <1% and >100% problems where possible
- Fractions: ensure BEDMAS/order of operations is tested; use brackets; NO exponents
- Equations: use integer coefficients and constants; include verification step in solution
- Surface Area/Volume: state exact dimensions in the problem; specify the shape clearly
- Pythagorean Theorem: state which side is unknown; use realistic measurements
- Probability: show the sample space or ask students to construct it
- Linear Relations: specify whether a table, graph, or expression is required
"""
        if custom_prompt:
            prompt += f"\nSPECIAL INSTRUCTIONS FROM TEACHER/PARENT:\n{custom_prompt}\n"

        prompt += "\nReturn ONLY the raw JSON object. No markdown. No extra text."

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": build_system_prompt(grade)},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.65,
            max_tokens=8192,
        )

        worksheet_data = extract_json(response.choices[0].message.content)
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
        elif "JSON" in msg.upper() or "parse" in msg.lower():
            msg = "AI returned an unexpected format. Please try again."
        return JSONResponse({"success": False, "error": f"Generation error: {msg}"})


# ===== ENTRY POINT =====
if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  MathSheet Pro — BC Math Worksheet Generator (Grades 6–8)")
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
