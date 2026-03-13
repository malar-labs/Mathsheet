# =============================================
#   MathSheet Pro — BC Math Curriculum Data
#   All grade topic dicts + build_system_prompt
# =============================================

# ===== GRADE KG (0) =====
GRADE_KG_TOPICS = {
    "counting_numbers": {
        "name": "Counting & Numbers to 10",
        "emoji": "🔢",
        "color": "#FF6B6B",
        "bg": "#FFF0F0",
        "description": "One-to-one correspondence, cardinality, subitizing, sequencing 1-10",
        "examples": ["Count 7 objects", "Which group has more?", "Subitize dot patterns"],
        "subtopics": ["One-to-one correspondence","Conservation and cardinality","Stable order counting 1–10","Subitizing (perceptual and conceptual)","Counting in First Peoples languages","Linking sets to numerals"]
    },
    "ways_to_make_5": {
        "name": "Ways to Make 5",
        "emoji": "🖐️",
        "color": "#6C63FF",
        "bg": "#F0EEFF",
        "description": "Benchmarks of 5, part-part-whole with concrete materials",
        "examples": ["Show 2 ways to make 5", "3 + ? = 5", "5 fingers: 4 and 1"],
        "subtopics": ["Benchmark of 5","Part-part-whole thinking","Using concrete materials","Traditional finger counting (groups of 5)","Decomposing quantities to 5"]
    },
    "ways_to_make_10": {
        "name": "Ways to Make 10",
        "emoji": "🔟",
        "color": "#4ECDC4",
        "bg": "#EDFAFA",
        "description": "Decomposing and recomposing to 10, making 10 benchmark",
        "examples": ["6 + 4 = 10", "Show all pairs that make 10", "Ten-frame fill"],
        "subtopics": ["Benchmark of 10","Making 10 with ten-frames","Decomposing 10 into parts","Part-part-whole thinking to 10","Whole-class number talks"]
    },
    "repeating_patterns": {
        "name": "Repeating Patterns",
        "emoji": "🎨",
        "color": "#F9CA24",
        "bg": "#FFFBEA",
        "description": "2-3 element repeating patterns, identifying the core",
        "examples": ["AB AB AB pattern", "What comes next: 🔴🔵🔴🔵?", "Pattern in beadwork"],
        "subtopics": ["Repeating patterns with 2–3 elements","Identifying the core of a pattern","Representing patterns in various ways","First Peoples art patterns (beadwork, frieze work)","Noticing patterns in textiles"]
    },
    "change_in_quantity": {
        "name": "Change in Quantity to 10",
        "emoji": "➕",
        "color": "#A8E6CF",
        "bg": "#F0FFF7",
        "description": "Adding 1 or 2, build-and-change tasks with concrete materials",
        "examples": ["Start with 4, add 2. How many now?", "Change 6 to 3. What did you do?", "Add 1 cube"],
        "subtopics": ["Generalizing change by adding 1 or 2","Build-and-change tasks","Modeling number relationships","Using concrete materials","Fish drying and sharing contexts"]
    },
    "equality_balance": {
        "name": "Equality & Inequality",
        "emoji": "⚖️",
        "color": "#FF8B94",
        "bg": "#FFF0F2",
        "description": "Balance model: equal vs not equal using concrete materials",
        "examples": ["3 = 3 (balanced pan)", "4 ≠ 2 (unbalanced)", "Show equal using cubes"],
        "subtopics": ["Modeling equality as balanced","Modeling inequality as imbalanced","Pan balance with cubes","Visual and concrete models","Fish drying and sharing context"]
    },
    "direct_measurement": {
        "name": "Direct Comparative Measurement",
        "emoji": "📏",
        "color": "#FF9F43",
        "bg": "#FFF5E6",
        "description": "Linear, mass, and capacity comparisons (longer, heavier, holds more)",
        "examples": ["Which pencil is longer?", "Which bag is heavier?", "Which cup holds more?"],
        "subtopics": ["Linear: height, width, length (longer/shorter/taller/wider)","Mass: heavier, lighter, same","Capacity: holds more/less","Importance of baseline for linear comparison","Comparative language"]
    },
    "shapes_objects": {
        "name": "2D Shapes & 3D Objects",
        "emoji": "🔷",
        "color": "#7EC8E3",
        "bg": "#EDF7FF",
        "description": "Sorting 2D shapes and 3D objects, positional language",
        "examples": ["Sort by shape", "Build with blocks: shaped like a can", "Beside, on top of, under"],
        "subtopics": ["Sorting 2D shapes and 3D objects by a single attribute","Building and describing 3D objects","Exploring 2D shapes","Positional language (beside, on top, under, in front)","No specific math terminology required at this level"]
    },
    "graphs_data": {
        "name": "Concrete & Pictorial Graphs",
        "emoji": "📊",
        "color": "#9980FA",
        "bg": "#F5F2FF",
        "description": "Creating concrete and pictorial graphs to represent data",
        "examples": ["Graph how students came to school", "Which bar is tallest?", "What does the graph tell us?"],
        "subtopics": ["Creating concrete graphs","Creating pictorial graphs","Interpreting simple graphs","Mathematical discussions about data","Survey and represent class data"]
    },
    "probability_kg": {
        "name": "Likelihood of Events",
        "emoji": "🎯",
        "color": "#10AC84",
        "bg": "#EDFFF8",
        "description": "Language of probability: likely, unlikely for familiar events",
        "examples": ["Is it likely to snow tomorrow?", "Will the sun rise?", "Likely or unlikely?"],
        "subtopics": ["Using language: likely, unlikely","Familiar life events","Discussing probability informally","Connecting to daily experience"]
    },
    "financial_literacy_kg": {
        "name": "Financial Literacy",
        "emoji": "💰",
        "color": "#FDA7DF",
        "bg": "#FFF5FB",
        "description": "Canadian coins, role-playing transactions, wants and needs",
        "examples": ["Name the coin: loonie", "A muffin is $2, juice is $1. Total?", "Want vs need"],
        "subtopics": ["Noticing attributes of Canadian coins","Identifying coin names","Role-playing transactions (restaurant, bakery, store)","Combining whole-number purchases","Wants and needs","Token value and trade (wampum)"]
    },
}

# ===== GRADE 1 =====
GRADE1_TOPICS = {
    "numbers_to_20": {
        "name": "Numbers to 20",
        "emoji": "🔢",
        "color": "#FF6B6B",
        "bg": "#FFF0F0",
        "description": "Counting on/back, skip-counting, sequencing, comparing to 20",
        "examples": ["Skip-count by 2s to 20", "Order: 14, 7, 19, 3", "Count on from 13"],
        "subtopics": ["Counting on and counting back","Skip-counting by 2 and 5","Sequencing numbers to 20","Comparing and ordering numbers to 20","Subitizing","Base 10: 10 and some more"]
    },
    "ways_to_make_10_g1": {
        "name": "Ways to Make 10",
        "emoji": "🔟",
        "color": "#6C63FF",
        "bg": "#F0EEFF",
        "description": "Decomposing 10 into parts, benchmarks of 10 and 20",
        "examples": ["7 + ? = 10", "Decompose 10: 4 + 6", "Number bonds for 10"],
        "subtopics": ["Decomposing 10 into parts","Benchmark of 10 and 20","Numbers to 10 arranged and recognized","Traditional counting songs/singing"]
    },
    "addition_subtraction_to_20": {
        "name": "Addition & Subtraction to 20",
        "emoji": "➕",
        "color": "#4ECDC4",
        "bg": "#EDFAFA",
        "description": "Mental math strategies: counting on, making 10, doubles",
        "examples": ["8 + 6 = ? (make 10: 8+2+4)", "15 – 7 = ?", "6 + 6 = 12 (doubles)"],
        "subtopics": ["Decomposing 20 into parts","Counting on strategy","Making 10 strategy","Doubles strategy","Addition and subtraction are related","Whole-class number talks"]
    },
    "repeating_patterns_g1": {
        "name": "Repeating Patterns",
        "emoji": "🎨",
        "color": "#F9CA24",
        "bg": "#FFFBEA",
        "description": "Multiple elements/attributes, translating and predicting patterns",
        "examples": ["AABB AABB pattern", "Translate circle-square to red-blue", "What is the 10th element?"],
        "subtopics": ["Repeating patterns with multiple elements/attributes","Translating patterns between representations","Letter coding of patterns (AAB, ABC)","Predicting elements using strategies","Beading with 3–5 colours","Numerical patterns on hundred charts"]
    },
    "change_in_quantity_g1": {
        "name": "Change in Quantity to 20",
        "emoji": "➕",
        "color": "#A8E6CF",
        "bg": "#F0FFF7",
        "description": "Verbally describing changes in quantity, concretely and verbally",
        "examples": ["I can build 7 and make 10 by adding 3", "Change 15 to 12. What did you do?"],
        "subtopics": ["Verbally describing change","Concretely and verbally representing change","Building and changing quantities to 20","Connecting to addition and subtraction"]
    },
    "equality_inequality_g1": {
        "name": "Equality & Inequality",
        "emoji": "⚖️",
        "color": "#FF8B94",
        "bg": "#FFF0F2",
        "description": "Meaning of = and ≠, recording equations symbolically",
        "examples": ["7 + 3 = 10", "8 ≠ 5", "Is 4 + 6 = 3 + 7?"],
        "subtopics": ["Demonstrating and explaining equality","Demonstrating inequality","Recording equations symbolically using = and ≠","Connecting to balance model"]
    },
    "measurement_non_standard": {
        "name": "Measurement with Non-Standard Units",
        "emoji": "📏",
        "color": "#FF9F43",
        "bg": "#FFF5E6",
        "description": "Measuring with non-uniform (hands) and uniform (cubes) units",
        "examples": ["How many cubes long is the book?", "Measure with hand spans", "Tile the area"],
        "subtopics": ["Uniform vs non-uniform units","Iterating a single unit","Multiple copies of a unit","Tiling an area","Using body parts to measure","Hand/foot tracing for mitten/moccasin making"]
    },
    "geometry_g1": {
        "name": "2D Shapes & 3D Objects",
        "emoji": "🔷",
        "color": "#7EC8E3",
        "bg": "#EDF7FF",
        "description": "Sorting, comparing, positional language, composite shapes",
        "examples": ["Sort by one attribute", "Two triangles make a square", "Up/down, in/out"],
        "subtopics": ["Sorting 3D objects and 2D shapes by one attribute","Comparing 2D shapes and 3D objects","Relative positions (up/down, in/out)","Replicating composite 2D shapes","Describing shapes in the environment"]
    },
    "data_graphs_g1": {
        "name": "Concrete Graphs",
        "emoji": "📊",
        "color": "#9980FA",
        "bg": "#F5F2FF",
        "description": "Creating, describing, and comparing concrete graphs (one-to-one)",
        "examples": ["Graph favourite colours", "Which has the most? least?", "Compare two graphs"],
        "subtopics": ["Creating concrete graphs","Describing graphs","Comparing concrete graphs","One-to-one correspondence","Mathematical discussions about data"]
    },
    "probability_g1": {
        "name": "Likelihood of Events",
        "emoji": "🎯",
        "color": "#10AC84",
        "bg": "#EDFFF8",
        "description": "Never, sometimes, always, more/less likely",
        "examples": ["Will it rain in summer? (sometimes)", "Will you grow taller? (likely)", "Never vs always"],
        "subtopics": ["Language: never, sometimes, always","More likely, less likely","Familiar life events","Cycles (Elder perspectives on ceremonies)","Comparative language"]
    },
    "financial_literacy_g1": {
        "name": "Financial Literacy",
        "emoji": "💰",
        "color": "#FDA7DF",
        "bg": "#FFF5FB",
        "description": "Coin values (nickels, dimes, quarters, loonies, toonies), monetary exchanges",
        "examples": ["Value of a quarter = 25¢", "Count 3 dimes = 30¢", "Role-play buying an item"],
        "subtopics": ["Identifying values of coins","Counting multiples of same denomination","Money as a medium of exchange","Role-playing transactions","Trade games with variable value objects"]
    },
}

# ===== GRADE 2 =====
GRADE2_TOPICS = {
    "numbers_to_100": {
        "name": "Numbers to 100",
        "emoji": "💯",
        "color": "#FF6B6B",
        "bg": "#FFF0F0",
        "description": "Skip-counting, place value (10s and 1s), benchmarks 25/50/100, even/odd",
        "examples": ["Skip-count by 5s from 35", "What is the value of the 4 in 47?", "Even or odd: 38?"],
        "subtopics": ["Skip-counting by 2, 5, and 10 from different starting points","Comparing and ordering numbers to 100","Place value: 10s and 1s","Benchmarks of 25, 50, and 100","Even and odd numbers","Decomposing two-digit numbers"]
    },
    "addition_subtraction_to_100": {
        "name": "Addition & Subtraction to 100",
        "emoji": "➕",
        "color": "#6C63FF",
        "bg": "#F0EEFF",
        "description": "Flexible strategies, estimating, making 10, friendly numbers",
        "examples": ["48 + 37 = ? (bridge 10)", "Estimate: 61 – 28 ≈ ?", "65 – 38 using open number line"],
        "subtopics": ["Fluency with addition/subtraction to 20","Estimating sums/differences to 100","Making 10 and bridging 10","Friendly numbers strategy","Decomposing into 10s and 1s","Open number line and hundred chart"]
    },
    "patterns_g2": {
        "name": "Repeating & Increasing Patterns",
        "emoji": "📈",
        "color": "#4ECDC4",
        "bg": "#EDFAFA",
        "description": "Complex repeating patterns, increasing patterns to 100",
        "examples": ["Pattern: 2, 4, 6, 8…", "Identify core of AABC AABC", "Métis finger weaving"],
        "subtopics": ["Complex repeating patterns (positional, circular)","Identifying the core","Increasing patterns using manipulatives to 100","Letters, sounds, actions, and numbers","Métis finger weaving patterns","First Peoples headband patterning"]
    },
    "change_in_quantity_g2": {
        "name": "Change in Quantity",
        "emoji": "➕",
        "color": "#F9CA24",
        "bg": "#FFFBEA",
        "description": "Numerically describing change using pictorial/symbolic representation",
        "examples": ["6 + n = 10: use ten-frame to find n", "Show change on hundred chart"],
        "subtopics": ["Numerically describing change","Pictorial and symbolic representation","Using ten-frames and hundred charts","Connecting to addition and subtraction"]
    },
    "symbolic_equality_g2": {
        "name": "Equality & Inequality",
        "emoji": "⚖️",
        "color": "#FF8B94",
        "bg": "#FFF0F2",
        "description": "Symbolic representation using = and ≠",
        "examples": ["25 + 15 = 40", "30 ≠ 28", "Is 17 + 5 = 4 × 6?"],
        "subtopics": ["Symbolic representation of equality","Symbolic representation of inequality","Recording equations with = and ≠","Connecting to balance and concrete models"]
    },
    "standard_measurement_g2": {
        "name": "Linear Measurement (Standard Units)",
        "emoji": "📏",
        "color": "#FF9F43",
        "bg": "#FFF5E6",
        "description": "Centimetres and metres; estimating and measuring length, height, width",
        "examples": ["Measure desk in cm", "Estimate: is the door closer to 1 m or 2 m?", "Record in cm"],
        "subtopics": ["Centimetres and metres","Estimating length","Measuring and recording length/height/width","Using standard metric units","Introducing standard measurement"]
    },
    "geometry_g2": {
        "name": "2D Shapes & 3D Objects",
        "emoji": "🔷",
        "color": "#7EC8E3",
        "bg": "#EDF7FF",
        "description": "Sorting by two attributes, describing triangles/squares/rectangles/circles",
        "examples": ["Sort by colour AND shape", "Describe a rectangle: 4 sides, 2 pairs equal", "3D in 2D faces"],
        "subtopics": ["Sorting 2D/3D using two attributes","Describing/comparing/constructing triangles, squares, rectangles, circles","Identifying 2D shapes as faces of 3D objects","Northwest Coast shapes (ovoids, U, split U)"]
    },
    "data_graphs_g2": {
        "name": "Pictorial Graphs",
        "emoji": "📊",
        "color": "#9980FA",
        "bg": "#F5F2FF",
        "description": "Collecting data, concrete graphs, pictorial representation",
        "examples": ["Draw a stamp graph", "How many more chose soccer than swimming?", "One-to-one correspondence"],
        "subtopics": ["Collecting data","Creating concrete graphs","Representing data pictorially (grids, stamps, drawings)","One-to-one correspondence","Mathematical discussions"]
    },
    "probability_g2": {
        "name": "Likelihood of Events",
        "emoji": "🎯",
        "color": "#10AC84",
        "bg": "#EDFFF8",
        "description": "Certain, uncertain; more, less, equally likely",
        "examples": ["Certain: the sun will set tonight", "Equally likely: flipping a coin", "More likely to pick red?"],
        "subtopics": ["Language: certain, uncertain","More, less, or equally likely","Comparing likelihood of events","Connecting to everyday contexts"]
    },
    "financial_literacy_g2": {
        "name": "Financial Literacy",
        "emoji": "💰",
        "color": "#FDA7DF",
        "bg": "#FFF5FB",
        "description": "Coin combinations to 100¢, spending and saving",
        "examples": ["Make 75¢ two ways", "Count mixed coins", "Save vs spend decision"],
        "subtopics": ["Mixed coin combinations to 100 cents","Spending and saving concepts","Wants and needs","Role-playing transactions with bills and coins"]
    },
}

# ===== GRADE 3 =====
GRADE3_TOPICS = {
    "numbers_to_1000": {
        "name": "Numbers to 1000",
        "emoji": "🔢",
        "color": "#FF6B6B",
        "bg": "#FFF0F0",
        "description": "Place value (100s/10s/1s), comparing/ordering, estimating large quantities",
        "examples": ["Skip-count by 25s from 150", "What is the value of the 4 in 342?", "Order: 287, 728, 278"],
        "subtopics": ["Skip-counting by any number from any starting point","Comparing and ordering numbers to 1000","Place value: 100s, 10s, 1s","Role of zero as placeholder (e.g., 408)","Estimating large quantities","Place-value based counting patterns"]
    },
    "fractions_g3": {
        "name": "Fraction Concepts",
        "emoji": "½",
        "color": "#6C63FF",
        "bg": "#F0EEFF",
        "description": "Fractions as parts of region, set, or linear model; equal partitioning",
        "examples": ["Colour 3/4 of a shape", "3 out of 8 = 3/8", "Divide a strip into equal parts"],
        "subtopics": ["Fractions as parts of a region, set, or linear model","Equal shares/portions of a whole","Equal partitioning","Recording pictorial representations","Connecting to symbolic notation","Pole ratios and medicine wheel contexts"]
    },
    "addition_subtraction_g3": {
        "name": "Addition & Subtraction to 1000",
        "emoji": "➕",
        "color": "#4ECDC4",
        "bg": "#EDFAFA",
        "description": "Flexible computation strategies, estimating, regrouping",
        "examples": ["348 + 275 = ? (decompose)", "Estimate: 489 – 123 ≈ ?", "Regroup to subtract"],
        "subtopics": ["Flexible computation: decompose, friendly numbers, compensate","Estimating sums and differences to 1000","Regrouping","Using addition/subtraction in real-life contexts","Whole-class number talks"]
    },
    "addition_subtraction_facts": {
        "name": "Addition & Subtraction Facts to 20",
        "emoji": "✏️",
        "color": "#FF8B94",
        "bg": "#FFF0F2",
        "description": "Emerging computational fluency: decomposing, doubles, making 10",
        "examples": ["8 + 7 = 15 (doubles + 1)", "15 – 8 = ? (think addition)", "6 + 4 + 3 = ?"],
        "subtopics": ["Decomposing and bridging 10","Doubles and related doubles","Commutative property","Addition and subtraction are related","Students should recall addition facts to 20 by end of Grade 3"]
    },
    "multiplication_division_g3": {
        "name": "Multiplication & Division Concepts",
        "emoji": "✖️",
        "color": "#F9CA24",
        "bg": "#FFFBEA",
        "description": "Groups of, arrays, repeated addition/subtraction; sharing and grouping",
        "examples": ["3 groups of 4 = 12", "12 ÷ 4 = 3 (sharing)", "Arrays on grid paper"],
        "subtopics": ["Multiplication as groups of/arrays/repeated addition","Division as sharing/grouping/repeated subtraction","Multiplication and division are related","Looking for patterns in hundred chart","Fish drying and sharing contexts","Memorization not expected"]
    },
    "patterns_g3": {
        "name": "Increasing & Decreasing Patterns",
        "emoji": "📈",
        "color": "#A8E6CF",
        "bg": "#F0FFF7",
        "description": "Concrete, pictorial, numerical; describing and generalizing pattern rules",
        "examples": ["3, 6, 9, 12… (add 3)", "Doubling pattern: 1, 2, 4, 8", "Describe rule in words"],
        "subtopics": ["Creating patterns using concrete/pictorial/numerical","Representing in multiple ways","Generalizing what makes pattern increase/decrease","Pattern rules using words and numbers","Predictability in song rhythm"]
    },
    "one_step_equations_g3": {
        "name": "One-Step Equations",
        "emoji": "🔧",
        "color": "#7EC8E3",
        "bg": "#EDF7FF",
        "description": "Start/change/result unknown with an unknown number",
        "examples": ["n + 15 = 20", "12 + n = 20", "6 + 13 = n"],
        "subtopics": ["Start unknown: n + 15 = 20","Change unknown: 12 + n = 20","Result unknown: 6 + 13 = n","Investigating even and odd numbers","Connecting to addition and subtraction"]
    },
    "standard_measurement_g3": {
        "name": "Measurement (Standard Units)",
        "emoji": "📏",
        "color": "#FF9F43",
        "bg": "#FFF5E6",
        "description": "Linear (cm, m, km), capacity (mL, L), area (sq units), mass (g, kg)",
        "examples": ["Measure in cm and m", "Estimate: holds 500 mL or 2 L?", "Area in square units"],
        "subtopics": ["Linear: centimetre, metre, kilometre","Capacity: millilitre, litre","Area using square units (standard and non-standard)","Mass: gram, kilogram","Estimation using standard referents","Perimeter and area concepts (no formulas)"]
    },
    "time_g3": {
        "name": "Time Concepts",
        "emoji": "⏰",
        "color": "#EE5A24",
        "bg": "#FFF2EE",
        "description": "Second, minute, hour, day, week, month, year; estimating time",
        "examples": ["How many minutes in an hour?", "Estimate: how long to eat lunch?", "Days in a week"],
        "subtopics": ["Units of time: second, minute, hour, day, week, month, year","Relationships between units","Estimating time","Environmental and seasonal references","Traditional calendar contexts","Telling time NOT expected at this level"]
    },
    "geometry_3d_g3": {
        "name": "3D Objects",
        "emoji": "🎲",
        "color": "#9980FA",
        "bg": "#F5F2FF",
        "description": "Identifying by 2D faces, edges, vertices; comparing and constructing",
        "examples": ["A cube has 6 square faces", "Prism vs pyramid: how are they different?", "Build from net"],
        "subtopics": ["Identifying 3D objects by 2D faces and number of edges/vertices","Describing attributes (faces, edges, vertices)","Mathematical terms (sphere, cube, prism, cone, cylinder)","Comparing 3D objects","Preservation of shape regardless of orientation","Jingle dress bells, bentwood box, birch bark baskets"]
    },
    "data_graphs_g3": {
        "name": "Graphs & Data",
        "emoji": "📊",
        "color": "#0652DD",
        "bg": "#EEF2FF",
        "description": "Bar graphs, pictographs, charts, and tables",
        "examples": ["Read a bar graph", "Create a pictograph from tally data", "Describe and discuss results"],
        "subtopics": ["Collecting data","Creating bar graphs, pictographs, charts, tables","Describing, comparing, and discussing results","Choosing a suitable representation","One-to-one correspondence"]
    },
    "probability_g3": {
        "name": "Probability of Simulated Events",
        "emoji": "🎲",
        "color": "#10AC84",
        "bg": "#EDFFF8",
        "description": "Certain/uncertain, more/less/equally likely; coins, dice, spinners",
        "examples": ["P(heads) on a coin: equally likely", "Roll a die: more likely to get even or odd?", "Spinner experiment"],
        "subtopics": ["Certain, uncertain","More, less, or equally likely","Tossing coins, rolling dice, using spinners","Understanding chance","50-50 chance","Snowsnake game context"]
    },
    "financial_literacy_g3": {
        "name": "Financial Literacy",
        "emoji": "💰",
        "color": "#FDA7DF",
        "bg": "#FFF5FB",
        "description": "Coin/bill combinations to $100, earning and payment",
        "examples": ["Make $47.50 two ways", "How many $5 bills in $35?", "Ways to earn money"],
        "subtopics": ["Totalling mixed coins and bills","Different combinations for same amount","Flexible payment methods (cash, cheque, electronic)","Ways of earning money","First Peoples trade items (dentalium shells, dried fish)"]
    },
}

# ===== GRADE 4 =====
GRADE4_TOPICS = {
    "numbers_to_10000": {
        "name": "Numbers to 10 000",
        "emoji": "🔢",
        "color": "#FF6B6B",
        "bg": "#FFF0F0",
        "description": "Place value to 10 000, comparing/ordering, multiples, benchmarks",
        "examples": ["Value of 4 in 4 372?", "Order: 3 405, 3 054, 3 540", "Skip-count by 25 from 0"],
        "subtopics": ["Multiples and flexible counting strategies","Comparing and ordering numbers to 10 000","Place value: 1000s, 100s, 10s, 1s","Whole-number benchmarks","Estimating large quantities"]
    },
    "decimals_hundredths_g4": {
        "name": "Decimals to Hundredths",
        "emoji": "🔟",
        "color": "#6C63FF",
        "bg": "#F0EEFF",
        "description": "Fractions and decimals as amounts; ordering, comparing, benchmarks",
        "examples": ["0.75 = 3/4", "Compare 0.4 and 0.39", "Order: 0.25, 0.5, 0.75"],
        "subtopics": ["Relationship between fractions and decimals","Ordering and comparing fractions with common denominators","Estimating fractions with benchmarks (0, ½, 1)","Using concrete and visual models","Equal partitioning"]
    },
    "addition_subtraction_g4": {
        "name": "Addition & Subtraction to 10 000",
        "emoji": "➕",
        "color": "#4ECDC4",
        "bg": "#EDFAFA",
        "description": "Flexible strategies, estimation, regrouping to 10 000",
        "examples": ["3 456 + 2 784 = ?", "Estimate: 5 231 – 1 876 ≈ ?", "Regroup thousands"],
        "subtopics": ["Flexible computation: decompose, friendly numbers, compensate","Estimating sums and differences to 10 000","Regrouping","Real-life contexts and problem-based situations","Whole-class number talks"]
    },
    "multiplication_division_g4": {
        "name": "Multiplication & Division",
        "emoji": "✖️",
        "color": "#FF9F43",
        "bg": "#FFF5E6",
        "description": "2-3 digit × 1 digit; relationships between operations",
        "examples": ["47 × 6 = ? (decompose: 40×6 + 7×6)", "96 ÷ 8 = ?", "Use multiplication to check division"],
        "subtopics": ["Relationship between multiplication and division","Flexible strategies: decompose, distributive, commutative","2- or 3-digit × 1-digit","Multiplication and division in real-life contexts","Whole-class number talks"]
    },
    "decimal_operations_g4": {
        "name": "Decimal Operations",
        "emoji": "💲",
        "color": "#F9CA24",
        "bg": "#FFFBEA",
        "description": "Adding and subtracting decimals to hundredths",
        "examples": ["$12.45 + $7.38 = ?", "Estimate: 4.7 – 1.95 ≈ ?", "Base 10 block addition"],
        "subtopics": ["Estimating decimal sums and differences","Visual models: base 10 blocks, grid paper, number lines","Addition and subtraction in real-life (money) contexts","Whole-class number talks"]
    },
    "multiplication_facts_g4": {
        "name": "Multiplication & Division Facts",
        "emoji": "🧮",
        "color": "#FF8B94",
        "bg": "#FFF0F2",
        "description": "Facts to 100; students recall 2s, 5s, 10s by end of Grade 4",
        "examples": ["7 × 8 = ?", "54 ÷ 9 = ?", "Double 24 to find 24 × 2"],
        "subtopics": ["Building computational fluency to 100","Mental math: doubling, halving","Students recall 2s, 5s, 10s facts by end of Grade 4","Games for authentic practice","Connecting to skip-counting and arrays"]
    },
    "patterns_g4": {
        "name": "Increasing & Decreasing Patterns",
        "emoji": "📈",
        "color": "#A8E6CF",
        "bg": "#F0FFF7",
        "description": "Patterns in tables and charts; describing rules in words and numbers",
        "examples": ["Fish stock: 200, 180, 160… what's the rule?", "Extend a pattern in a table", "Graph the pattern"],
        "subtopics": ["Using words and numbers to describe patterns","Patterns in tables and charts","Fish stocks and life expectancy contexts","Representing pattern relationships"]
    },
    "equations_g4": {
        "name": "One-Step Equations",
        "emoji": "🔧",
        "color": "#7EC8E3",
        "bg": "#EDF7FF",
        "description": "All operations with an unknown; start/change/result unknown",
        "examples": ["___ + 4 = 15", "15 – □ = 11", "n × 6 = 48"],
        "subtopics": ["One-step equations for all operations","Start unknown: n + 15 = 20","Change unknown: 12 + n = 20","Result unknown: 6 + 13 = __","Describing pattern rules with words and numbers"]
    },
    "time_g4": {
        "name": "Telling Time",
        "emoji": "⏰",
        "color": "#EE5A24",
        "bg": "#FFF2EE",
        "description": "Analog and digital clocks, 12/24-hour, a.m./p.m., minutes",
        "examples": ["Read: quarter past 3", "Write 2:45 p.m. in 24-hour time", "Elapsed time from 10:15 to 11:30"],
        "subtopics": ["Analog and digital clocks","12-hour and 24-hour clocks","a.m. and p.m.","Minutes in an hour","Quarter past, half past, quarter to","Telling time to the nearest minute","First Peoples seasonal and moon cycles"]
    },
    "polygons_g4": {
        "name": "Regular & Irregular Polygons",
        "emoji": "🔷",
        "color": "#9980FA",
        "bg": "#F5F2FF",
        "description": "Describing and sorting polygons; regular vs irregular",
        "examples": ["Regular hexagon vs irregular hexagon", "Is a circle a polygon? Why not?", "Sort by number of sides"],
        "subtopics": ["Describing and sorting regular and irregular polygons","Multiple attributes","Investigating closed shapes","Yup'ik border patterns"]
    },
    "perimeter_g4": {
        "name": "Perimeter",
        "emoji": "📐",
        "color": "#FF6B6B",
        "bg": "#FFF0F0",
        "description": "Measuring and calculating perimeter of regular and irregular shapes",
        "examples": ["Perimeter of rectangle 4 cm × 7 cm", "Find missing side given perimeter", "Geoboard shapes"],
        "subtopics": ["Using geoboards and grids","Creating and measuring shapes","Calculating perimeter of regular shapes","Calculating perimeter of irregular shapes","Real-life perimeter contexts"]
    },
    "symmetry_g4": {
        "name": "Line Symmetry",
        "emoji": "🔄",
        "color": "#10AC84",
        "bg": "#EDFFF8",
        "description": "Designs with a mirror image; lines of symmetry in shapes",
        "examples": ["How many lines of symmetry in a rectangle?", "Draw the mirror image", "Is this shape symmetric?"],
        "subtopics": ["Lines of symmetry","Creating symmetric designs with pattern blocks","Mirror images","First Peoples art, borders, birchbark biting, canoe building"]
    },
    "data_probability_g4": {
        "name": "Probability Experiments",
        "emoji": "🎲",
        "color": "#FDA7DF",
        "bg": "#FFF5FB",
        "description": "Predicting single outcomes; spinners, dice, bags; recording with tallies",
        "examples": ["Spin 20 times. Record results. Compare to prediction.", "P(red) from bag of 3 red, 2 blue", "Tally chart"],
        "subtopics": ["Predicting single outcomes","Using spinners, rolling dice, pulling from a bag","Recording results using tallies","Bar graphs and pictographs (many-to-one correspondence)","Dene/Kaska hand games, Lahal stick games"]
    },
    "financial_literacy_g4": {
        "name": "Financial Literacy",
        "emoji": "💰",
        "color": "#F9CA24",
        "bg": "#FFFBEA",
        "description": "Monetary calculations to $100, making change, simple financial decisions",
        "examples": ["Buy $3.75 + $1.50. Pay $10. Change = ?", "Best deal comparison", "Earning and saving plan"],
        "subtopics": ["Monetary calculations with decimal notation","Counting up/back and decomposing to calculate totals","Making change with amounts to $100","Simple decisions: earning, spending, saving, giving","Equitable trade rules"]
    },
}

# ===== GRADE 5 =====
GRADE5_TOPICS = {
    "numbers_to_million": {
        "name": "Numbers to 1 000 000",
        "emoji": "🔢",
        "color": "#FF6B6B",
        "bg": "#FFF0F0",
        "description": "Place value to millions, comparing/ordering, estimating large quantities",
        "examples": ["Value of 6 in 6 425 000?", "Order: 3 456 120, 3 546 021, 3 456 210", "Round to nearest 100 000"],
        "subtopics": ["Multiples and flexible counting","Comparing and ordering to 1 000 000","Place value: 100 000s to 1s","Estimating large quantities","First Peoples counting systems (Tsimshian three systems, Tlingit)"]
    },
    "decimals_thousandths_g5": {
        "name": "Decimals to Thousandths",
        "emoji": "🔟",
        "color": "#6C63FF",
        "bg": "#F0EEFF",
        "description": "Comparing, ordering, benchmarks for fractions and decimals",
        "examples": ["Compare 0.125 and 0.25", "Order: 0.5, 0.375, 0.625", "Benchmark: is 0.4 closer to 0 or ½?"],
        "subtopics": ["Decimals to thousandths","Equivalent fractions","Whole-number, fraction, and decimal benchmarks","Comparing and ordering fractions and decimals","Equal partitioning"]
    },
    "addition_subtraction_large": {
        "name": "Addition & Subtraction to 1 000 000",
        "emoji": "➕",
        "color": "#4ECDC4",
        "bg": "#EDFAFA",
        "description": "Flexible strategies, estimating sums and differences",
        "examples": ["234 567 + 345 678 = ?", "Estimate: 876 543 – 234 000 ≈ ?", "Use decomposition"],
        "subtopics": ["Flexible computation: decompose, friendly numbers, compensate","Estimating sums and differences to 10 000","Regrouping","Real-life contexts","Whole-class number talks"]
    },
    "multiplication_division_g5": {
        "name": "Multiplication & Division",
        "emoji": "✖️",
        "color": "#FF9F43",
        "bg": "#FFF5E6",
        "description": "3-digit numbers, division with remainders, flexible strategies",
        "examples": ["213 × 34 = ?", "875 ÷ 7 = ? remainder ?", "Decompose: 215 × 6"],
        "subtopics": ["Multiplication to three digits","Division with remainders","Flexible strategies: decompose, distributive, commutative","Repeated addition/subtraction","Real-life contexts"]
    },
    "decimal_operations_g5": {
        "name": "Decimal Operations",
        "emoji": "💲",
        "color": "#F9CA24",
        "bg": "#FFFBEA",
        "description": "Adding and subtracting decimals to thousandths",
        "examples": ["4.125 + 2.875 = ?", "Estimate: 8.4 – 3.625 ≈ ?", "Grid paper addition"],
        "subtopics": ["Estimating decimal sums and differences","Visual models: base 10 blocks, grid paper, number lines","Real-life contexts","Whole-class number talks"]
    },
    "multiplication_facts_g5": {
        "name": "Multiplication & Division Facts to 100",
        "emoji": "🧮",
        "color": "#FF8B94",
        "bg": "#FFF0F2",
        "description": "Emerging fluency; students recall 2s, 3s, 4s, 5s, 10s by end of Grade 5",
        "examples": ["9 × 7 = ?", "63 ÷ 9 = ?", "Use doubling: 8 × 6 = double(4 × 6)"],
        "subtopics": ["Building fluency with facts to 100","Mental strategies: doubling, halving, annexing, distributive property","Students recall 2s, 3s, 4s, 5s, 10s by end of Grade 5","Games for authentic practice"]
    },
    "patterns_algebra_g5": {
        "name": "Patterns & Algebra",
        "emoji": "📈",
        "color": "#A8E6CF",
        "bg": "#F0FFF7",
        "description": "Increasing/decreasing rules with words, numbers, symbols, variables",
        "examples": ["3, 7, 11…: rule is +4, expression is 4n–1", "Solve: 4 + X = 15", "Table to expression"],
        "subtopics": ["Rules with words, numbers, symbols, and variables","One-step equations with variables","Expressing problems as equations (e.g., 4 + X = 15)","Solving one-step equations"]
    },
    "area_perimeter_g5": {
        "name": "Area & Perimeter",
        "emoji": "📐",
        "color": "#7EC8E3",
        "bg": "#EDF7FF",
        "description": "Area of squares/rectangles; relationship between area and perimeter",
        "examples": ["Area of rectangle 6 m × 4 m = 24 m²", "Same area, different perimeter?", "Tile a floor"],
        "subtopics": ["Area of squares and rectangles using tiles/geoboards/grid","Perimeter of rectangles","Relationship: area and perimeter not dependent on each other","Traditional dwellings contexts","Elder knowledge on estimating and measuring"]
    },
    "time_duration_g5": {
        "name": "Duration & Elapsed Time",
        "emoji": "⏰",
        "color": "#EE5A24",
        "bg": "#FFF2EE",
        "description": "Understanding elapsed time, applying time concepts in real life",
        "examples": ["Movie starts at 2:15 and ends at 4:05. How long?", "Daily and seasonal cycles", "Elapsed time on number line"],
        "subtopics": ["Elapsed time and duration","Applying time in real-life contexts","Daily and seasonal cycles","Moon cycles, tides, journeys, events"]
    },
    "geometry_g5": {
        "name": "3D Objects & 2D Shapes",
        "emoji": "🎲",
        "color": "#9980FA",
        "bg": "#F5F2FF",
        "description": "Classifying prisms and pyramids, quadrilaterals",
        "examples": ["Rectangle vs parallelogram: similarities?", "Triangular prism vs pyramid", "Name from net"],
        "subtopics": ["Investigating 3D objects and 2D shapes using multiple attributes","Describing and sorting quadrilaterals","Rectangular and triangular prisms","Pyramids","Identifying prisms in the environment"]
    },
    "transformations_g5": {
        "name": "Single Transformations",
        "emoji": "🔄",
        "color": "#FDA7DF",
        "bg": "#FFF5FB",
        "description": "Translation, reflection, and rotation using concrete materials",
        "examples": ["Slide the shape 4 units right", "Flip over horizontal line", "Rotate 90° clockwise"],
        "subtopics": ["Translation (slide)","Reflection (flip)","Rotation (turn)","Focus on motion of transformations","Weaving, cedar baskets, designs contexts"]
    },
    "data_graphs_g5": {
        "name": "Double Bar Graphs",
        "emoji": "📊",
        "color": "#10AC84",
        "bg": "#EDFFF8",
        "description": "One-to-one and many-to-one correspondence with double bar graphs",
        "examples": ["Compare boys/girls preferences in double bar graph", "One square = 5 students", "Interpret data"],
        "subtopics": ["One-to-one correspondence","Many-to-one correspondence (1 symbol = group/value)","Creating double bar graphs","Interpreting double bar graphs","Comparing data sets"]
    },
    "probability_g5": {
        "name": "Probability of Single Events",
        "emoji": "🎲",
        "color": "#0652DD",
        "bg": "#EEF2FF",
        "description": "Predicting outcomes, representing probability as fractions",
        "examples": ["P(red) = 3/8 from a bag", "Is this spinner fair?", "Record 50 spins and compare"],
        "subtopics": ["Predicting single-outcome events","Using spinners, dice, bags","Representing probability as fractions","Experimental probability","Comparing experimental and theoretical"]
    },
    "financial_literacy_g5": {
        "name": "Financial Literacy",
        "emoji": "💰",
        "color": "#FF6B6B",
        "bg": "#FFF0F0",
        "description": "Monetary calculations to $1000, making change, simple financial plans",
        "examples": ["Buy $234.50 items. Pay $300. Change = ?", "Plan: save $15/week for a $120 item", "Budget for a trip"],
        "subtopics": ["Monetary calculations to $1000","Making change","Simple financial plans to meet a goal","Budget with income and expenses","Developing savings plans"]
    },
}

# ===== GRADE 6 =====
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

# ===== GRADE 7 =====
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

# ===== GRADE 8 =====
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

# ===== GRADE 9 =====
GRADE9_TOPICS = {
    "rational_number_operations": {
        "name": "Rational Number Operations",
        "emoji": "🔢",
        "color": "#FF6B6B",
        "bg": "#FFF0F0",
        "description": "Add, subtract, multiply, divide rational numbers with order of operations",
        "examples": ["(–3/4) ÷ 1/5 + ((–1/3) × (–5/2))", "1 – 2 × (4/5)²", "Order of operations with negatives"],
        "subtopics": ["Addition, subtraction, multiplication, division of rational numbers","Order of operations with rational numbers (brackets and exponents)","Simplifying complex expressions","Paddle making contexts","Negative fractions and mixed numbers"]
    },
    "exponents": {
        "name": "Exponents & Exponent Laws",
        "emoji": "⬆️",
        "color": "#6C63FF",
        "bg": "#F0EEFF",
        "description": "Exponent laws with whole-number exponents; variable bases",
        "examples": ["n⁵ × n³ = n⁸", "y⁷ ÷ y³ = y⁴", "(5n)³ = 125n³", "6⁰ = 1"],
        "subtopics": ["Exponent notation (e.g., 2⁷ = 128)","Variable bases (e.g., n⁴)","Laws: product, quotient, power of a power, power of a product","Zero exponent: 6⁰ = 1","Limited to whole-number exponents and outcomes","(–3)² ≠ –3²"]
    },
    "polynomials": {
        "name": "Operations with Polynomials",
        "emoji": "✏️",
        "color": "#4ECDC4",
        "bg": "#EDFAFA",
        "description": "Add, subtract, multiply, divide polynomials of degree ≤ 2",
        "examples": ["(x² + 2x – 4) + (2x² – 3x – 4)", "(5x – 7) – (2x + 3)", "2n(n + 7)", "(15k² – 10k) ÷ (5k)"],
        "subtopics": ["Variables, degree, number of terms, coefficients","Constant term","Adding polynomials","Subtracting polynomials","Multiplying monomial by polynomial","Dividing polynomial by monomial","Using algebra tiles"]
    },
    "linear_relations_g9": {
        "name": "Two-Variable Linear Relations",
        "emoji": "📈",
        "color": "#F9CA24",
        "bg": "#FFFBEA",
        "description": "Continuous linear relations, graphing, interpolating, extrapolating",
        "examples": ["Graph y = 2x – 3", "Interpolate: what is y when x = 2.5?", "Horizontal/vertical lines"],
        "subtopics": ["Two-variable continuous linear relations","Rational coordinates","Horizontal and vertical lines","Graphing and analyzing","Interpolating approximate values","Extrapolating approximate values","Spirit canoe journey predictions"]
    },
    "linear_equations_g9": {
        "name": "Multi-Step Linear Equations",
        "emoji": "🔧",
        "color": "#A8E6CF",
        "bg": "#F0FFF7",
        "description": "Distribution, variables on both sides, rational coefficients; verify solutions",
        "examples": ["1 + 2x = 3 – 2/3(x + 6)", "3(x – 4) = 2x + 1", "Solve and verify with substitution"],
        "subtopics": ["Distribution","Variables on both sides","Collecting like terms","Rational coefficients, constants, and solutions","Solving symbolically and pictorially","Verifying solutions"]
    },
    "proportional_reasoning_g9": {
        "name": "Spatial Proportional Reasoning",
        "emoji": "⚖️",
        "color": "#FF9F43",
        "bg": "#FFF5E6",
        "description": "Scale diagrams, similar triangles/polygons, linear unit conversions (metric)",
        "examples": ["Draw a scale diagram (1 cm : 5 m)", "Find missing side in similar triangles", "Convert 3.5 km to m"],
        "subtopics": ["Scale diagrams: enlargement and reduction of 2D shapes","Similar triangles and polygons","Applying properties of similar triangles","Linear unit conversions (metric only)","First Peoples mural work","Traditional design in fashion","Longhouse models using similar triangles"]
    },
    "statistics_g9": {
        "name": "Statistics",
        "emoji": "📊",
        "color": "#7EC8E3",
        "bg": "#EDF7FF",
        "description": "Population vs sample, bias, ethics, sampling techniques, misleading stats",
        "examples": ["Is this sample biased? Why?", "Identify misleading graph technique", "Analyze water quality data"],
        "subtopics": ["Population versus sample","Bias in data collection","Ethics and cultural sensitivity","Sampling techniques","Misleading statistics","Analyzing data representations for problems","First Peoples water quality data","Statistics Canada income/health/housing data"]
    },
    "financial_literacy_g9": {
        "name": "Financial Literacy",
        "emoji": "💰",
        "color": "#FDA7DF",
        "bg": "#FFF5FB",
        "description": "Banking, simple interest, savings, planned purchases, budgets",
        "examples": ["Simple interest: I = Prt with P=$500, r=3%, t=2 years", "Plan a budget", "Compare savings accounts"],
        "subtopics": ["Banking basics","Simple interest formula: I = Prt","Savings planning","Planned purchases","Creating a budget/plan","Hosting a First Peoples event budget","Simple transactions"]
    },
}

# ===== CURRICULUM DICT =====
CURRICULUM = {
    0: GRADE_KG_TOPICS,
    1: GRADE1_TOPICS,
    2: GRADE2_TOPICS,
    3: GRADE3_TOPICS,
    4: GRADE4_TOPICS,
    5: GRADE5_TOPICS,
    6: GRADE6_TOPICS,
    7: GRADE7_TOPICS,
    8: GRADE8_TOPICS,
    9: GRADE9_TOPICS,
}


# ===== BUILD SYSTEM PROMPT =====
def build_system_prompt(grade: int) -> str:
    grade_contexts = {
        0: {
            "level": "Kindergarten",
            "age": "5–6 years old",
            "topics": """BC KINDERGARTEN MATHEMATICS CURRICULUM TOPICS:
1. Counting & Numbers to 10 — one-to-one correspondence, cardinality, subitizing, sequencing 1–10
2. Ways to Make 5 — benchmarks of 5, part-part-whole with concrete materials
3. Ways to Make 10 — decomposing and recomposing to 10, ten-frames
4. Repeating Patterns — 2–3 element repeating patterns, identifying the core
5. Change in Quantity to 10 — adding 1 or 2, build-and-change tasks
6. Equality & Inequality — balance model: equal vs not equal using concrete materials
7. Direct Comparative Measurement — linear, mass, and capacity comparisons (longer, heavier, holds more)
8. 2D Shapes & 3D Objects — sorting by a single attribute, positional language
9. Concrete & Pictorial Graphs — creating and interpreting simple graphs
10. Likelihood of Events — likely, unlikely for familiar events
11. Financial Literacy — Canadian coins, role-playing transactions, wants and needs"""
        },
        1: {
            "level": "Grade 1",
            "age": "6–7 years old",
            "topics": """BC GRADE 1 MATHEMATICS CURRICULUM TOPICS:
1. Numbers to 20 — counting on/back, skip-counting by 2 and 5, sequencing, comparing
2. Ways to Make 10 — decomposing 10 into parts, benchmarks of 10 and 20
3. Addition & Subtraction to 20 — counting on, making 10, doubles strategies
4. Repeating Patterns — multiple elements/attributes, translating and predicting patterns
5. Change in Quantity to 20 — verbally describing changes concretely and symbolically
6. Equality & Inequality — meaning of = and ≠, recording equations symbolically
7. Measurement with Non-Standard Units — uniform vs non-uniform units, iterating, tiling area
8. 2D Shapes & 3D Objects — sorting by one attribute, positional language, composite shapes
9. Concrete Graphs — creating, describing, and comparing concrete graphs (one-to-one)
10. Likelihood of Events — never, sometimes, always, more/less likely
11. Financial Literacy — coin values (nickels, dimes, quarters, loonies, toonies), monetary exchanges"""
        },
        2: {
            "level": "Grade 2",
            "age": "7–8 years old",
            "topics": """BC GRADE 2 MATHEMATICS CURRICULUM TOPICS:
1. Numbers to 100 — skip-counting, place value (10s and 1s), benchmarks 25/50/100, even/odd
2. Addition & Subtraction to 100 — flexible strategies, estimating, making 10, friendly numbers
3. Repeating & Increasing Patterns — complex repeating patterns, increasing patterns to 100
4. Change in Quantity — numerically describing change using pictorial/symbolic representation
5. Equality & Inequality — symbolic representation using = and ≠
6. Linear Measurement (Standard Units) — centimetres and metres; estimating and measuring
7. 2D Shapes & 3D Objects — sorting by two attributes, describing triangles/squares/rectangles/circles
8. Pictorial Graphs — collecting data, concrete and pictorial representation
9. Likelihood of Events — certain, uncertain; more, less, equally likely
10. Financial Literacy — coin combinations to 100¢, spending and saving"""
        },
        3: {
            "level": "Grade 3",
            "age": "8–9 years old",
            "topics": """BC GRADE 3 MATHEMATICS CURRICULUM TOPICS:
1. Numbers to 1000 — place value (100s/10s/1s), comparing/ordering, estimating large quantities
2. Fraction Concepts — fractions as parts of region, set, or linear model; equal partitioning
3. Addition & Subtraction to 1000 — flexible computation strategies, estimating, regrouping
4. Addition & Subtraction Facts to 20 — emerging fluency: decomposing, doubles, making 10
5. Multiplication & Division Concepts — groups of, arrays, repeated addition/subtraction; sharing and grouping
6. Increasing & Decreasing Patterns — concrete, pictorial, numerical; generalizing pattern rules
7. One-Step Equations — start/change/result unknown with an unknown number
8. Measurement (Standard Units) — linear (cm, m, km), capacity (mL, L), area (sq units), mass (g, kg)
9. Time Concepts — second, minute, hour, day, week, month, year; estimating time
10. 3D Objects — identifying by 2D faces, edges, vertices; comparing and constructing
11. Graphs & Data — bar graphs, pictographs, charts, and tables
12. Probability of Simulated Events — certain/uncertain, more/less/equally likely; coins, dice, spinners
13. Financial Literacy — coin/bill combinations to $100, earning and payment"""
        },
        4: {
            "level": "Grade 4",
            "age": "9–10 years old",
            "topics": """BC GRADE 4 MATHEMATICS CURRICULUM TOPICS:
1. Numbers to 10 000 — place value, comparing/ordering, multiples, benchmarks
2. Decimals to Hundredths — fractions and decimals as amounts; ordering, comparing, benchmarks
3. Addition & Subtraction to 10 000 — flexible strategies, estimation, regrouping
4. Multiplication & Division — 2-3 digit × 1 digit; relationships between operations
5. Decimal Operations — adding and subtracting decimals to hundredths
6. Multiplication & Division Facts — facts to 100; recall 2s, 5s, 10s by end of Grade 4
7. Increasing & Decreasing Patterns — patterns in tables and charts; rules in words and numbers
8. One-Step Equations — all operations with an unknown; start/change/result unknown
9. Telling Time — analog and digital clocks, 12/24-hour, a.m./p.m., minutes
10. Regular & Irregular Polygons — describing and sorting polygons; regular vs irregular
11. Perimeter — measuring and calculating perimeter of regular and irregular shapes
12. Line Symmetry — designs with a mirror image; lines of symmetry in shapes
13. Probability Experiments — predicting single outcomes; spinners, dice, bags; recording with tallies
14. Financial Literacy — monetary calculations to $100, making change, simple financial decisions"""
        },
        5: {
            "level": "Grade 5",
            "age": "10–11 years old",
            "topics": """BC GRADE 5 MATHEMATICS CURRICULUM TOPICS:
1. Numbers to 1 000 000 — place value to millions, comparing/ordering, estimating large quantities
2. Decimals to Thousandths — comparing, ordering, benchmarks for fractions and decimals
3. Addition & Subtraction to 1 000 000 — flexible strategies, estimating sums and differences
4. Multiplication & Division — 3-digit numbers, division with remainders, flexible strategies
5. Decimal Operations — adding and subtracting decimals to thousandths
6. Multiplication & Division Facts to 100 — recall 2s, 3s, 4s, 5s, 10s by end of Grade 5
7. Patterns & Algebra — increasing/decreasing rules with words, numbers, symbols, variables
8. Area & Perimeter — area of squares/rectangles; relationship between area and perimeter
9. Duration & Elapsed Time — understanding elapsed time, applying time concepts in real life
10. 3D Objects & 2D Shapes — classifying prisms and pyramids, quadrilaterals
11. Single Transformations — translation, reflection, and rotation using concrete materials
12. Double Bar Graphs — one-to-one and many-to-one correspondence
13. Probability of Single Events — predicting outcomes, representing probability as fractions
14. Financial Literacy — monetary calculations to $1000, making change, simple financial plans"""
        },
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
        },
        9: {
            "level": "Grade 9",
            "age": "14–15 years old",
            "topics": """BC GRADE 9 MATHEMATICS CURRICULUM TOPICS:
1. Rational Number Operations — add/subtract/multiply/divide rational numbers, order of operations (brackets and exponents)
2. Exponents & Exponent Laws — product, quotient, power of a power, power of a product, zero exponent; whole-number exponents
3. Operations with Polynomials — add, subtract, multiply (monomial × polynomial), divide (polynomial ÷ monomial); degree ≤ 2
4. Two-Variable Linear Relations — continuous linear relations, rational coordinates, horizontal/vertical lines, graphing, interpolating, extrapolating
5. Multi-Step Linear Equations — distribution, variables on both sides, collecting like terms, rational coefficients, verifying solutions
6. Spatial Proportional Reasoning — scale diagrams, similar triangles and polygons, linear unit conversions (metric)
7. Statistics — population vs sample, bias, ethics, sampling techniques, misleading statistics
8. Financial Literacy — banking, simple interest (I=Prt), savings planning, budgets"""
        },
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
