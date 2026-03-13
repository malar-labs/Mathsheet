/* =============================================
   MathSheet Pro — BC Grade 8 Math
   Main Application JavaScript
   ============================================= */

'use strict';

// ===== STATE =====
let state = {
    user: null,
    isGuest: true,
    selectedGrade: 8,
    selectedTopics: new Set(),
    worksheetData: null,
    funFactInterval: null,
    _loadingMsgInterval: null,
    _autoAdvanceTimer: null
};

// ===== MATH BACKGROUND SYMBOLS =====
const MATH_SYMBOLS = [
    'π', '∑', '√', '∞', '÷', '×', '±', '≠', '≤', '≥', '∈', 'Δ',
    'a²', 'b²', 'c²', '²', '³', '½', '¼', '⅓', '%', '=', '+',
    'x', 'y', 'n', 'θ', '∠', '⊥', '∥', '∝', 'f(x)', '∫', 'Σ',
    '12', '36', '144', '√2', '3.14', '2π', 'sin', 'cos', 'tan',
    '∛', '∜', '∩', '∪', '⊂', '⊃', '∀', '∃', '∴', '∵'
];

function createMathBackground() {
    const bg = document.getElementById('math-bg');
    const count = Math.min(40, Math.floor(window.innerWidth / 30));
    for (let i = 0; i < count; i++) {
        const el = document.createElement('span');
        el.className = 'math-symbol';
        el.textContent = MATH_SYMBOLS[Math.floor(Math.random() * MATH_SYMBOLS.length)];
        el.style.left = `${Math.random() * 100}%`;
        el.style.animationDuration = `${12 + Math.random() * 18}s`;
        el.style.animationDelay = `${Math.random() * -25}s`;
        el.style.fontSize = `${0.9 + Math.random() * 1.4}rem`;
        bg.appendChild(el);
    }
}

// ===== FUN MATH FACTS =====
const FUN_FACTS = [
    'The Pythagorean theorem has over 370 different known proofs!',
    'Zero is the only number that cannot be represented in Roman numerals.',
    'A "googol" is the number 1 followed by 100 zeros.',
    'The word "percent" comes from the Latin "per centum", meaning "by the hundred".',
    'The ratio of a circle\'s circumference to its diameter is always π ≈ 3.14159...',
    'Every even number greater than 2 can be expressed as the sum of two prime numbers (Goldbach\'s conjecture).',
    'The Fibonacci sequence appears in nature: sunflower seeds, spiral shells, and pine cones!',
    'In BC, the Fraser River spans about 1,375 km — that\'s a lot of Pythagorean theorem applications!',
    'Negative numbers were controversial when first introduced — some called them "absurd" or "fictitious"!',
    'The word "algebra" comes from the Arabic "al-jabr", introduced by the mathematician Al-Khwarizmi.',
    'A perfect number equals the sum of its proper divisors. 28 = 1+2+4+7+14!',
    'The square root of 2 is irrational — it goes on forever without repeating: 1.41421356...',
    '12² = 144 and 21² = 441 — a fun number reversal!',
    'Ancient Egyptians used unit fractions (with numerator 1) for all calculations.',
    'The probability of flipping 10 heads in a row with a fair coin is (½)¹⁰ = 1/1024.',
    'First Peoples mathematicians used base-10 counting long before European contact.',
    'Proportional reasoning is used in traditional Coast Salish weaving patterns.',
    'Vancouver\'s population has grown proportionally by about 3% per year for decades.',
    'The Great Pyramid of Giza uses the golden ratio, approximately 1.618 — close to 8/5!',
    'Did you know? The mean, median, and mode can all be different values in the same dataset!'
];

function startFunFacts() {
    const el = document.getElementById('fun-fact-text');
    let idx = Math.floor(Math.random() * FUN_FACTS.length);
    el.textContent = FUN_FACTS[idx];
    if (state.funFactInterval) clearInterval(state.funFactInterval);
    state.funFactInterval = setInterval(() => {
        idx = (idx + 1) % FUN_FACTS.length;
        el.style.opacity = '0';
        setTimeout(() => {
            el.textContent = FUN_FACTS[idx];
            el.style.transition = 'opacity 0.5s';
            el.style.opacity = '1';
        }, 300);
    }, 4000);
}

function stopFunFacts() {
    if (state.funFactInterval) {
        clearInterval(state.funFactInterval);
        state.funFactInterval = null;
    }
}

// ===== SECTION NAVIGATION =====
function showSection(id) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    const target = document.getElementById(id + '-section');
    if (target) target.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateProgress(step) {
    const bar = document.getElementById('progress-bar');
    if (step === 0) { bar.style.display = 'none'; return; }
    bar.style.display = 'block';
    [1, 2, 3].forEach(n => {
        const el = document.getElementById('prog-' + n);
        el.classList.remove('active', 'done');
        if (n < step) el.classList.add('done');
        else if (n === step) el.classList.add('active');
    });
    [1, 2].forEach(n => {
        const line = document.getElementById('pline-' + n);
        if (line) line.classList.toggle('done', n < step);
    });
}

// ===== LOGIN MODAL =====
function openLoginModal() {
    document.getElementById('login-modal-overlay').classList.remove('hidden');
    setTimeout(() => document.getElementById('login-name').focus(), 80);
}

function closeLoginModal(e) {
    // Close when clicking the overlay backdrop (not the box itself)
    if (e && e.target !== document.getElementById('login-modal-overlay')) return;
    document.getElementById('login-modal-overlay').classList.add('hidden');
    document.getElementById('login-name').value = '';
}

// ===== AUTH =====
function login() {
    const name = (document.getElementById('login-name').value || '').trim();
    if (!name || name.length < 2) {
        showToast('Please enter your name (at least 2 characters)', 'error');
        document.getElementById('login-name').focus();
        return;
    }
    fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: name })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            setUser(data.username, false);
            document.getElementById('login-modal-overlay').classList.add('hidden');
            document.getElementById('login-name').value = '';
            showToast(`Welcome, ${data.username}! 🎉`, 'success');
        } else {
            showToast(data.error || 'Login failed', 'error');
        }
    })
    .catch(() => showToast('Connection error. Please try again.', 'error'));
}

function logout() {
    fetch('/api/logout', { method: 'POST' })
    .then(() => {
        state.user = null;
        state.isGuest = true;
        document.getElementById('user-badge').classList.add('hidden');
        document.getElementById('login-btn').classList.remove('hidden');
        showToast('Signed out. See you next time!', 'info');
    });
}

function setUser(username, isGuest) {
    state.user = username;
    state.isGuest = isGuest;
    document.getElementById('username-display').textContent = username;
    document.getElementById('user-avatar').textContent = username.charAt(0).toUpperCase();
    document.getElementById('user-badge').classList.remove('hidden');
    document.getElementById('login-btn').classList.add('hidden');
}

// ===== GRADE SELECTOR =====
function selectGrade(grade) {
    if (state._autoAdvanceTimer) { clearTimeout(state._autoAdvanceTimer); state._autoAdvanceTimer = null; }
    state.selectedGrade = grade;
    state.selectedTopics.clear();
    // Update button active state
    document.querySelectorAll('.grade-btn').forEach(btn => {
        btn.classList.toggle('active', parseInt(btn.dataset.grade) === grade);
    });
    // Update subtitle
    const label = document.getElementById('grade-label');
    if (label) label.textContent = grade === 0 ? 'Kindergarten' : `Grade ${grade}`;
    // Rebuild topic cards for this grade
    buildTopicCards();
    updateSelCount();
}

// ===== TOPIC SECTION =====
function goToTopics() {
    showSection('topics');
    updateProgress(1);
}

function goToTopicsFromWorksheet() {
    state.worksheetData = null;
    document.getElementById('worksheet-content').innerHTML = '';
    showSection('topics');
    updateProgress(1);
}

function buildTopicCards() {
    const grid = document.getElementById('topics-grid');
    grid.innerHTML = '';
    const topics = CURRICULUM_DATA[state.selectedGrade] || {};
    Object.entries(topics).forEach(([id, topic]) => {
        const card = document.createElement('div');
        card.className = 'topic-card';
        card.dataset.id = id;
        card.style.setProperty('--topic-color', topic.color);
        card.style.setProperty('--topic-bg', topic.bg);
        card.addEventListener('click', () => toggleTopic(id, card));

        const exTags = (topic.examples || []).slice(0, 2)
            .map(e => `<span class="topic-ex-tag">${e}</span>`).join('');

        card.innerHTML = `
            <div class="topic-check">✓</div>
            <div class="topic-emoji">${topic.emoji}</div>
            <div class="topic-name">${topic.name}</div>
            <div class="topic-desc">${topic.description}</div>
            <div class="topic-examples">${exTags}</div>
        `;
        grid.appendChild(card);
    });
}

function toggleTopic(id, card) {
    // Cancel any pending auto-advance
    if (state._autoAdvanceTimer) {
        clearTimeout(state._autoAdvanceTimer);
        state._autoAdvanceTimer = null;
    }

    if (state.selectedTopics.has(id)) {
        state.selectedTopics.delete(id);
        card.classList.remove('selected');
    } else {
        state.selectedTopics.add(id);
        card.classList.add('selected');
    }
    updateSelCount();

    // Auto-advance after 700ms if at least one topic is selected.
    // Clicking another topic resets the timer, giving time to multi-select.
    if (state.selectedTopics.size > 0) {
        const countEl = document.getElementById('sel-count');
        countEl.textContent = `Going to options in a moment…`;
        state._autoAdvanceTimer = setTimeout(() => {
            state._autoAdvanceTimer = null;
            updateSelCount(); // restore count text
            goToOptions();
        }, 700);
    }
}

function updateSelCount() {
    const n = state.selectedTopics.size;
    document.getElementById('sel-count').textContent =
        n === 0 ? '0 topics selected' :
        n === 1 ? '1 topic selected' :
        `${n} topics selected`;
}

function selectAllTopics() {
    if (state._autoAdvanceTimer) { clearTimeout(state._autoAdvanceTimer); state._autoAdvanceTimer = null; }
    document.querySelectorAll('.topic-card').forEach(card => {
        state.selectedTopics.add(card.dataset.id);
        card.classList.add('selected');
    });
    updateSelCount();
}

function clearTopics() {
    if (state._autoAdvanceTimer) { clearTimeout(state._autoAdvanceTimer); state._autoAdvanceTimer = null; }
    document.querySelectorAll('.topic-card').forEach(card => card.classList.remove('selected'));
    state.selectedTopics.clear();
    updateSelCount();
}

function goToOptions() {
    if (state.selectedTopics.size === 0) {
        showToast('Please select at least one topic! 📚', 'error');
        return;
    }
    showSection('options');
    updateProgress(2);
}

// ===== RADIO CARD SELECTION =====
function initRadioCards() {
    document.querySelectorAll('.radio-card').forEach(card => {
        card.addEventListener('click', () => {
            const group = card.dataset.group;
            document.querySelectorAll(`.radio-card[data-group="${group}"]`).forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            const input = card.querySelector('input[type="radio"]');
            if (input) input.checked = true;
        });
    });
}

// ===== GENERATE WORKSHEET =====
function getFormValues() {
    const problemType = document.querySelector('input[name="problem_type"]:checked');
    const difficulty   = document.querySelector('input[name="difficulty"]:checked');
    const numQ         = document.querySelector('input[name="num_questions"]:checked');
    return {
        topics:          Array.from(state.selectedTopics),
        grade:           state.selectedGrade,
        student_name:    (document.getElementById('student-name').value || '').trim(),
        problem_type:    problemType ? problemType.value : 'mixed',
        difficulty:      difficulty  ? difficulty.value  : 'mixed',
        num_questions:   numQ        ? parseInt(numQ.value) : 10,
        include_answers: document.getElementById('include-answers').checked,
        custom_prompt:   (document.getElementById('custom-prompt').value || '').trim()
    };
}

function generateWorksheet() {
    const values = getFormValues();
    showSection('loading');
    updateProgress(3);
    startFunFacts();
    setLoadingMessages();

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 min timeout

    fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
        signal: controller.signal
    })
    .then(r => r.json())
    .then(data => {
        clearTimeout(timeoutId);
        stopFunFacts();
        if (data.success) {
            state.worksheetData = data.worksheet;
            renderWorksheet(data.worksheet);
            showSection('worksheet');
            resetGradingUI();
            showToast('Worksheet ready! Fill in your answers and check them 🎉', 'success');
        } else {
            showSection('options');
            updateProgress(2);
            showToast(data.error || 'Generation failed. Please try again.', 'error');
        }
    })
    .catch(err => {
        clearTimeout(timeoutId);
        stopFunFacts();
        showSection('options');
        updateProgress(2);
        if (err.name === 'AbortError') {
            showToast('Request timed out — the AI is busy. Please try again in a moment.', 'error');
        } else {
            showToast('Connection error. Please check your internet and try again.', 'error');
        }
        console.error(err);
    });
}

function setLoadingMessages() {
    const msgs = ['Generating your questions...', 'Applying BC curriculum standards...', 'Verifying math accuracy...', 'Adding BC cultural contexts...', 'Formatting your worksheet...'];
    const subs  = ['Our AI is crafting personalized BC math problems just for you!', 'Ensuring alignment with British Columbia mathematics outcomes...', 'Double-checking every answer for accuracy...', 'Incorporating First Peoples and BC contexts...', 'Almost ready — putting the finishing touches on your worksheet!'];
    let i = 0;
    const msgEl = document.getElementById('loading-msg');
    const subEl = document.getElementById('loading-sub');
    msgEl.textContent = msgs[0];
    subEl.textContent = subs[0];
    if (state._loadingMsgInterval) clearInterval(state._loadingMsgInterval);
    state._loadingMsgInterval = setInterval(() => {
        i = (i + 1) % msgs.length;
        msgEl.textContent = msgs[i];
        subEl.textContent = subs[i];
    }, 3000);
}

// ===== RENDER WORKSHEET =====
function renderWorksheet(ws) {
    if (state._loadingMsgInterval) { clearInterval(state._loadingMsgInterval); state._loadingMsgInterval = null; }

    const studentName = ws.student_name || '';
    const date = ws.date || new Date().toLocaleDateString('en-CA', { year: 'numeric', month: 'long', day: 'numeric' });
    const qCount = (ws.questions || []).length;
    const questionsHTML = (ws.questions || []).map(q => buildQuestionHTML(q)).join('');
    const answerKeyHTML = ws.include_answers ? buildAnswerKeyHTML(ws) : '';

    document.getElementById('worksheet-content').innerHTML = `
        <div class="ws-header-banner">
            <div class="ws-banner-left">
                <h1>BC Mathematics Curriculum</h1>
                <h2>${escHTML(ws.title || 'Grade 8 Math Worksheet')}</h2>
                <div class="ws-curriculum">Grade 8 · ${escHTML(ws.topic || '')} · ${escHTML(ws.curriculum || 'BC Mathematics')}</div>
            </div>
            <div class="ws-banner-right">
                <div class="ws-info-line">
                    <span class="label">Name:</span>
                    <span class="value">${studentName ? escHTML(studentName) : '___________________'}</span>
                </div>
                <div class="ws-info-line">
                    <span class="label">Date:</span>
                    <span class="value">${escHTML(date)}</span>
                </div>
                <div class="ws-info-line">
                    <span class="label">Score:</span>
                    <span class="value" id="header-score">______ / ${qCount}</span>
                </div>
            </div>
        </div>

        <div class="ws-body">
            <div class="ws-instructions-bar">
                <span class="instr-icon">📋</span>
                <p><strong>Instructions:</strong> ${escHTML(ws.instructions || 'Show all your work clearly. Write your final answer in the answer box.')}</p>
            </div>
            <div class="ws-meta-row">
                <span>⏱ Estimated time: <strong>${escHTML(ws.estimated_time || '30 minutes')}</strong></span>
                <span>📝 Total questions: <strong>${qCount}</strong></span>
            </div>

            <!-- Score banner (shown after submission) -->
            <div id="score-banner" class="score-banner hidden">
                <div class="score-left">
                    <div class="score-number" id="score-number">0 / 0</div>
                    <div class="score-label">Your Score</div>
                </div>
                <div class="score-right">
                    <div class="score-percent" id="score-percent">0%</div>
                    <div class="score-msg" id="score-msg"></div>
                </div>
            </div>

            <div class="ws-questions">
                ${questionsHTML}
            </div>

            ${answerKeyHTML}

            <div class="ws-footer">
                <span>📐 MathSheet Pro — BC Grade 8 Mathematics</span>
                <span>${escHTML(ws.topic || '')} Worksheet · ${escHTML(date)}</span>
                <span>Generated with AI · BC Curriculum</span>
            </div>
        </div>
    `;

    // Allow pressing Enter in single-line answer inputs to move to the next
    document.querySelectorAll('.answer-input').forEach(input => {
        input.addEventListener('keydown', e => {
            if (e.key === 'Enter') {
                const num = parseInt(input.dataset.q);
                const next = document.getElementById(`ans-${num + 1}`);
                if (next) next.focus();
            }
        });
    });
}

// ===== BUILD QUESTION (interactive) =====
function buildQuestionHTML(q) {
    const typeClass  = (q.type || 'number').toLowerCase();
    const typeLabel  = typeClass === 'word' ? 'Word Problem' : 'Number Problem';
    const diffClass  = (q.difficulty || 'medium').toLowerCase();
    const diffLabel  = diffClass.charAt(0).toUpperCase() + diffClass.slice(1);
    const workRows   = { small: 2, medium: 4, large: 5 }[(q.space_needed || 'medium').toLowerCase()] || 4;
    const printLines = Array(workRows).fill('<div class="answer-line"></div>').join('');

    return `
        <div class="ws-question" id="wsq-${q.number}" data-num="${q.number}">
            <div class="ws-q-header">
                <div class="ws-q-num">${q.number}</div>
                <span class="ws-q-type-badge ${typeClass}">${typeLabel}</span>
                <span class="ws-q-diff-badge ${diffClass}">${diffLabel}</span>
                <div class="ws-q-result hidden" id="result-${q.number}"></div>
                <span class="ws-q-pts">/ 1 pt</span>
            </div>
            <div class="ws-q-body">
                <div class="ws-q-text">${escHTML(q.question || '')}</div>

                <!-- INTERACTIVE zone — shown on screen, hidden when printing -->
                <div class="ws-answer-zone no-print">
                    <div class="work-area-wrap">
                        <label class="ws-field-label">✏️ Show your work</label>
                        <textarea class="work-textarea" rows="${workRows}"
                            placeholder="Write your calculations here..."></textarea>
                    </div>
                    <div class="final-answer-wrap">
                        <label class="ws-field-label">🎯 Final Answer</label>
                        <div class="answer-input-row">
                            <input type="text" class="answer-input"
                                   id="ans-${q.number}"
                                   data-q="${q.number}"
                                   placeholder="Type your answer…"
                                   autocomplete="off" spellcheck="false">
                            <span class="answer-icon hidden" id="icon-${q.number}"></span>
                        </div>
                        <div class="answer-feedback hidden" id="fb-${q.number}"></div>
                    </div>
                </div>

                <!-- PRINT zone — blank lines for pen/pencil, hidden on screen -->
                <div class="ws-print-space print-only">
                    <div class="ws-answer-label">Show your work &amp; write your answer below</div>
                    ${printLines}
                </div>
            </div>
        </div>
    `;
}

// ===== ANSWER CHECKING =====
function checkAnswer(userRaw, correctRaw) {
    if (!userRaw || !userRaw.trim()) return false;

    // Normalise: lowercase, trim, collapse spaces, strip common units & symbols
    const norm = s => s.toString().toLowerCase().trim()
        .replace(/\s+/g, ' ')
        .replace(/,/g, '')          // 1,024 → 1024
        .replace(/\$/g, '')         // dollar signs
        .replace(/°/g, '')          // degrees
        .replace(/\bcm\b/g, '')
        .replace(/\bm\b/g, '')
        .replace(/\bkm\b/g, '')
        .replace(/\bkg\b/g, '')
        .replace(/\bg\b/g, '')
        .replace(/\bcad\b/g, '')
        .replace(/\bunits?\b/g, '')
        .replace(/\s+/g, ' ').trim();

    const u = norm(userRaw);
    const c = norm(correctRaw);

    // Exact match after normalisation
    if (u === c) return true;

    // Numeric comparison — handles decimals within 0.01 tolerance
    const uNum = parseFloat(u.replace(/[^0-9.-]/g, ''));
    const cNum = parseFloat(c.replace(/[^0-9.-]/g, ''));
    if (!isNaN(uNum) && !isNaN(cNum) && Math.abs(uNum - cNum) <= 0.01) return true;

    // Fraction match: user "13/4" vs correct "3.25" or "13/4"
    const parseFraction = s => {
        const m = s.match(/^(-?\d+)\s*\/\s*(-?\d+)$/);
        return m ? parseFloat(m[1]) / parseFloat(m[2]) : NaN;
    };
    const uFrac = parseFraction(u), cFrac = parseFraction(c);
    if (!isNaN(uFrac) && !isNaN(cNum)  && Math.abs(uFrac - cNum)  <= 0.01) return true;
    if (!isNaN(cFrac) && !isNaN(uNum)  && Math.abs(cFrac - uNum)  <= 0.01) return true;
    if (!isNaN(uFrac) && !isNaN(cFrac) && Math.abs(uFrac - cFrac) <= 0.01) return true;

    // Substring match: correct answer contains user's key value (e.g. "76500" inside "$76,500")
    if (u.length >= 2 && c.includes(u)) return true;
    if (c.length >= 2 && u.includes(c)) return true;

    return false;
}

// ===== SUBMIT / GRADE =====
function submitAnswers() {
    const questions = state.worksheetData?.questions || [];
    if (!questions.length) { showToast('No worksheet loaded', 'error'); return; }

    // Check that at least one answer is filled in
    const anyFilled = questions.some(q => {
        const el = document.getElementById(`ans-${q.number}`);
        return el && el.value.trim().length > 0;
    });
    if (!anyFilled) {
        showToast('Please answer at least one question before submitting!', 'error');
        return;
    }

    let correct = 0;

    questions.forEach(q => {
        const inputEl    = document.getElementById(`ans-${q.number}`);
        const iconEl     = document.getElementById(`icon-${q.number}`);
        const fbEl       = document.getElementById(`fb-${q.number}`);
        const questionEl = document.getElementById(`wsq-${q.number}`);
        const resultEl   = document.getElementById(`result-${q.number}`);
        if (!inputEl) return;

        const userAnswer = inputEl.value.trim();
        const isCorrect  = checkAnswer(userAnswer, q.answer || '');
        const skipped    = !userAnswer;

        // Apply visual state
        questionEl.classList.remove('graded-correct', 'graded-wrong', 'graded-skip');
        questionEl.classList.add('graded', skipped ? 'graded-skip' : isCorrect ? 'graded-correct' : 'graded-wrong');

        // Icon in input row
        iconEl.textContent = skipped ? '⬜' : isCorrect ? '✅' : '❌';
        iconEl.classList.remove('hidden');

        // Result badge in header
        resultEl.textContent = skipped ? '—' : isCorrect ? '✓' : '✗';
        resultEl.className   = `ws-q-result ${skipped ? 'result-skip' : isCorrect ? 'result-correct' : 'result-wrong'}`;

        // Feedback area
        if (isCorrect) {
            correct++;
            fbEl.innerHTML = `<span class="fb-correct-label">✓ Correct!</span>`;
        } else {
            const stepsHTML = q.solution_steps
                ? `<div class="fb-steps"><span class="fb-steps-label">Solution:</span> ${escHTML(q.solution_steps)}</div>`
                : '';
            fbEl.innerHTML = `
                <span class="fb-wrong-label">${skipped ? '⚠ Not answered' : '✗ Not quite right'}</span>
                <div class="fb-correct-ans">
                    <span class="fb-ans-label">Correct answer:</span>
                    <strong>${escHTML(q.answer || '')}</strong>
                </div>
                ${stepsHTML}
            `;
        }
        fbEl.classList.remove('hidden');

        // Disable input after grading
        inputEl.disabled = true;
    });

    // Update score in worksheet header
    const headerScore = document.getElementById('header-score');
    if (headerScore) headerScore.textContent = `${correct} / ${questions.length}`;

    showScoreBanner(correct, questions.length);

    // Toggle buttons
    document.getElementById('submit-btn').classList.add('hidden');
    document.getElementById('reset-btn').classList.remove('hidden');

    showToast(`Graded! You got ${correct} out of ${questions.length} correct.`, correct === questions.length ? 'success' : 'info');
}

function showScoreBanner(correct, total) {
    const pct = total > 0 ? Math.round((correct / total) * 100) : 0;
    const msg =
        pct === 100 ? '🌟 Perfect score! Outstanding work!' :
        pct >= 80   ? '🎉 Excellent! Almost perfect!' :
        pct >= 60   ? '👍 Good job! Keep practicing!' :
        pct >= 40   ? '💪 Keep trying! You\'re getting there!' :
                      '📚 Review the topic and try again!';

    document.getElementById('score-number').textContent  = `${correct} / ${total}`;
    document.getElementById('score-percent').textContent = `${pct}%`;
    document.getElementById('score-msg').textContent     = msg;

    const banner = document.getElementById('score-banner');
    banner.className = `score-banner score-${pct === 100 ? 'perfect' : pct >= 80 ? 'great' : pct >= 60 ? 'good' : pct >= 40 ? 'ok' : 'low'}`;
    banner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function resetAnswers() {
    const questions = state.worksheetData?.questions || [];
    questions.forEach(q => {
        const inputEl    = document.getElementById(`ans-${q.number}`);
        const iconEl     = document.getElementById(`icon-${q.number}`);
        const fbEl       = document.getElementById(`fb-${q.number}`);
        const questionEl = document.getElementById(`wsq-${q.number}`);
        const resultEl   = document.getElementById(`result-${q.number}`);
        const workEl     = questionEl?.querySelector('.work-textarea');

        if (inputEl)    { inputEl.value = ''; inputEl.disabled = false; }
        if (iconEl)     { iconEl.textContent = ''; iconEl.classList.add('hidden'); }
        if (fbEl)       { fbEl.innerHTML = ''; fbEl.classList.add('hidden'); }
        if (workEl)     { workEl.value = ''; }
        if (questionEl) questionEl.classList.remove('graded', 'graded-correct', 'graded-wrong', 'graded-skip');
        if (resultEl)   { resultEl.textContent = ''; resultEl.className = 'ws-q-result hidden'; }
    });

    const headerScore = document.getElementById('header-score');
    const total = questions.length;
    if (headerScore) headerScore.textContent = `______ / ${total}`;

    const banner = document.getElementById('score-banner');
    if (banner) banner.className = 'score-banner hidden';

    document.getElementById('reset-btn').classList.add('hidden');
    document.getElementById('submit-btn').classList.remove('hidden');

    showToast('Answers cleared — give it another try! 💪', 'info');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function resetGradingUI() {
    document.getElementById('submit-btn')?.classList.remove('hidden');
    document.getElementById('reset-btn')?.classList.add('hidden');
}

// ===== WORKSHEET ACTIONS =====
function generateAnother() {
    state.worksheetData = null;
    document.getElementById('worksheet-content').innerHTML = '';
    showSection('topics');
    updateProgress(1);
}

function downloadHTML() {
    const ws = state.worksheetData;
    if (!ws) { showToast('No worksheet to download', 'error'); return; }

    const content = document.getElementById('worksheet-content').innerHTML;
    const styles  = document.querySelector('link[href*="style.css"]')?.href || '';

    const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${escHTML(ws.title || 'BC Grade 8 Math Worksheet')}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800;900&family=Nunito:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="${styles}">
<style>
body { background: white; padding: 0; margin: 0; font-family: 'Nunito', sans-serif; }
.worksheet-render { box-shadow: none; border-radius: 0; }
.no-print { display: none !important; }
.print-only { display: block !important; }
</style>
</head>
<body>
<div class="worksheet-render">${content}</div>
</body>
</html>`;

    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url;
    a.download = `bc_grade8_${(ws.title || 'worksheet').replace(/[^a-z0-9]/gi, '_').toLowerCase()}.html`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Worksheet downloaded! 📄', 'success');
}

// ===== TOAST =====
function showToast(msg, type = 'info') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = `toast ${type} show`;
    setTimeout(() => t.classList.remove('show'), 3500);
}

// ===== UTILITIES =====
function escHTML(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// ===== INIT =====
function init() {
    createMathBackground();
    buildTopicCards();
    initRadioCards();
    updateProgress(1);

    // Escape key closes modal
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            document.getElementById('login-modal-overlay').classList.add('hidden');
        }
    });

    // Enter key in modal login input
    document.getElementById('login-name').addEventListener('keydown', e => {
        if (e.key === 'Enter') login();
    });
}

document.addEventListener('DOMContentLoaded', init);
