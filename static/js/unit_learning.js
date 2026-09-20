/* =============================================
   Grade-Wise Learning — shared engine for every unit
   Fully client-side: no AI, no network calls.
   All lesson content & questions come from UNIT_SECTIONS /
   UNIT_QUESTIONS (injected server-side from static JSON files).

   Question types (q.qtype):
     fraction  free text — fraction, mixed number or whole number
     decimal   free text — a decimal (a fraction is accepted too)
     integer   free text — a whole number
     compare   pick one of  <  =  >
     choice    pick one of q.options
     order     click q.options into the right sequence
     steps     fill in every line of the worked solution, one line at a time

   Pages: questions that carry the same q.page share a page, the way two
   problems share a line of a paper worksheet. A question with no q.page gets a
   page to itself, which is how every topic behaved before worked chains
   existed.
   ============================================= */
'use strict';

// ulState and the progress layer live in progress.js, loaded before this file.


// ===== math helpers =====
function gcd(a, b) { a = Math.abs(a); b = Math.abs(b); while (b) { [a, b] = [b, a % b]; } return a || 1; }

// A mixed number carries its sign on the whole part: "-1 3/4" means -(1 + 3/4),
// so the fraction part is subtracted, not added, when the whole part is negative.
function mixedValue(whole, num, den) {
    const w = whole || 0, n = num || 0, d = den || 1;
    return w < 0 ? w * d - n : w * d + n;
}

function answerValue(ans) {
    // ans = {whole, num, den, display, symbol?, value?}
    if (typeof ans.value === 'number') return { n: ans.value, d: 1 };
    const d = ans.den || 1;
    return { n: mixedValue(ans.whole, ans.num, d), d };
}

// Students may type a real minus sign or a dash instead of a hyphen.
function normalizeMinus(str) {
    return String(str).replace(/[−–—]/g, '-');
}

// Parse free-text fraction/mixed-number/whole-number input.
// Returns { whole, num, den } or null if unparseable.
function parseFractionInput(str) {
    if (!str) return null;
    const s = normalizeMinus(str).trim().replace(/\s+/g, ' ');
    let m;
    // mixed number: "1 3/4"
    m = s.match(/^(-?\d+)\s+(\d+)\s*\/\s*(\d+)$/);
    if (m) {
        const den = parseInt(m[3], 10);
        if (den === 0) return null;
        return { whole: parseInt(m[1], 10), num: parseInt(m[2], 10), den };
    }
    // simple fraction: "3/4" or "9/8"
    m = s.match(/^(-?\d+)\s*\/\s*(\d+)$/);
    if (m) {
        const den = parseInt(m[2], 10);
        if (den === 0) return null;
        return { whole: 0, num: parseInt(m[1], 10), den };
    }
    // whole number: "5"
    m = s.match(/^-?\d+$/);
    if (m) {
        return { whole: parseInt(s, 10), num: 0, den: 1 };
    }
    return null;
}

// ===== fraction token rendering =====
// Prompt text uses {a/b} for a fraction, {w_a/b} for a mixed number,
// {a/b}^2 for one raised to a power, and {n} for a plain number that should
// just print normally.
function renderMath(text) {
    if (!text) return '';
    const esc = escHTML(text);
    return esc.replace(/\{(-?\d+)\/(\d+)\}\^(\d+)/g, (_, n, d, power) =>
        // Brackets drawn here rather than typed into the prompt, so they can
        // grow with the fraction — a full-height fraction inside text-sized
        // brackets with a baseline "2" after it reads as (2/3)2, not squared.
        `<span class="ul-pow-group"><span class="ul-pow-paren">(</span>` +
        `<span class="ul-frac"><span class="ul-frac-stack"><span class="ul-frac-num">${n}</span><span class="ul-frac-den">${d}</span></span></span>` +
        `<span class="ul-pow-paren">)</span><sup class="ul-pow">${power}</sup></span>`
    ).replace(/\{(-?\d+)_(\d+)\/(\d+)\}/g, (_, w, n, d) =>
        `<span class="ul-frac"><span class="ul-frac-whole">${w}</span><span class="ul-frac-stack"><span class="ul-frac-num">${n}</span><span class="ul-frac-den">${d}</span></span></span>`
    ).replace(/\{(-?\d+)\/(\d+)\}/g, (_, n, d) =>
        `<span class="ul-frac"><span class="ul-frac-stack"><span class="ul-frac-num">${n}</span><span class="ul-frac-den">${d}</span></span></span>`
    ).replace(/\{(-?\d+)\}/g, (_, n) => `<strong>${n}</strong>`);
}

function escHTML(str) {
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

// ===== grading =====
// Returns { verdict: 'correct'|'close'|'wrong', message } — or { invalid: true, message }
// when the input can't be read, so a typo is never marked wrong.
function gradeFractionAnswer(userInput, answer) {
    const parsed = parseFractionInput(userInput);
    if (!parsed) {
        return { invalid: true, message: "That doesn't look like an answer yet. Try a whole number (5), a fraction (3/4), or a mixed number (1 1/2)." };
    }
    const correct = answerValue(answer);
    const userImproperNum = mixedValue(parsed.whole, parsed.num, parsed.den);
    const sameValue = userImproperNum * correct.d === correct.n * parsed.den;

    if (!sameValue) {
        return { verdict: 'wrong', message: `The correct answer is ${answer.display}.` };
    }

    // Value is right — now check the two mandatory checks: reduced? and improper→mixed?
    // Signs don't affect either check, so compare magnitudes.
    const fracNum = Math.abs(parsed.num), fracDen = parsed.den;
    const answerWhole = Math.abs(answer.whole || 0);
    const needsReduce = fracDen > 1 && fracNum !== 0 && gcd(fracNum, fracDen) !== 1;
    const typedAsPureImproper = parsed.whole === 0 && answerWhole > 0 && fracDen > 1 && fracNum >= fracDen;

    if (needsReduce || typedAsPureImproper) {
        let msg = `Right value! But always check: `;
        if (needsReduce) msg += `${fracNum}/${fracDen} can still be reduced. `;
        if (typedAsPureImproper) msg += `${fracNum}/${fracDen} is improper — convert it to the mixed number ${answer.display}. `;
        msg += `Fully simplified, the answer is ${answer.display}.`;
        return { verdict: 'close', message: msg };
    }

    return { verdict: 'correct', message: '' };
}

function gradeCompareAnswer(userSymbol, answer) {
    return userSymbol === answer.symbol
        ? { verdict: 'correct', message: '' }
        : { verdict: 'wrong', message: `The correct sign is "${answer.symbol}".` };
}

function gradeChoiceAnswer(userChoice, answer) {
    return userChoice === answer.choice
        ? { verdict: 'correct', message: '' }
        : { verdict: 'wrong', message: `The correct answer is "${answer.display}".` };
}

function gradeOrderAnswer(userOrder, answer) {
    const right = userOrder.length === answer.order.length
        && userOrder.every((value, i) => value === answer.order[i]);
    return right
        ? { verdict: 'correct', message: '' }
        : { verdict: 'wrong', message: `The correct order is ${answer.display}.` };
}

function gradeIntegerAnswer(userInput, answer) {
    const s = normalizeMinus(userInput || '').trim();
    if (!/^-?\d+$/.test(s)) return { invalid: true, message: 'Please type a whole number, like 12.' };
    return parseInt(s, 10) === answer.value
        ? { verdict: 'correct', message: '' }
        : { verdict: 'wrong', message: `The correct answer is ${answer.value}.` };
}

// A fraction written as text ("-2 7/12") turned back into a prompt token so it
// renders stacked. Returns null for anything that isn't a number.
function mathToken(text) {
    const s = normalizeMinus(String(text)).trim().replace(/\s+/g, ' ');
    let m = s.match(/^(-?\d+) (\d+)\s*\/\s*(\d+)$/);
    if (m) return `{${m[1]}_${m[2]}/${m[3]}}`;
    m = s.match(/^(-?\d+)\s*\/\s*(\d+)$/);
    if (m) return `{${m[1]}/${m[2]}}`;
    if (/^-?\d+$/.test(s)) return `{${s}}`;
    return null;
}

// A mixed number printed as plain text: HTML would collapse the space in
// "-1 1/4" and it would read as -11/4.
function answerText(display) {
    return escHTML(display).replace(/(\d) +(\d)/g, '$1&nbsp;$2');
}

function renderValue(text) {
    const token = mathToken(text);
    return token ? renderMath(token) : escHTML(text);
}

// "1 3/4" is a mixed number; "4" and "7/4" are not. A whole number typed beside
// a zero numerator ("2 0/1") is nobody's idea of a mixed number either.
function isMixedForm(parsed) {
    return (parsed.whole || 0) !== 0 && (parsed.num || 0) !== 0;
}

// Each line of a worked chain asks for one particular FORM, not just one value:
// the common-denominator line wants 20/30 and the simplify line wants 13/15,
// even though those are the same number. So a step is right only when the
// numerator, the denominator and the mixed-or-improper choice all match — with
// a separate, kinder message when the value was right but the form wasn't.
function gradeStepField(userInput, expect) {
    const user = parseFractionInput(userInput);
    if (!user) {
        return { invalid: true, message: "That doesn't look like an answer yet. Type a fraction like -3/4, or a mixed number like 1 1/2." };
    }
    const want = parseFractionInput(expect);
    const un = mixedValue(user.whole, user.num, user.den), ud = user.den;
    const wn = mixedValue(want.whole, want.num, want.den), wd = want.den;

    if (un === wn && ud === wd && isMixedForm(user) === isMixedForm(want)) {
        return { verdict: 'correct', message: '' };
    }
    if (un * wd === wn * ud) {
        let why;
        if (isMixedForm(want)) why = 'it still has to be written as a mixed number.';
        else if (isMixedForm(user)) why = 'this line wants one single fraction, not a mixed number.';
        else if (wd < ud) why = 'it is not fully reduced yet.';
        else if (wd > ud) why = `this line wants it written over ${wd}.`;
        else why = 'it is not in the form this line asks for.';
        return { verdict: 'wrong', form: true, why, message: `Right value — but ${why}` };
    }
    return { verdict: 'wrong', form: false, why: '', message: '' };
}

// Decimals are compared by value, so 0.50 and 0.5 both pass, and a student who
// works in fractions can type 3/4 for 0.75.
function parseDecimalInput(str) {
    if (!str) return null;
    const s = normalizeMinus(str).trim().replace(/[$\s]/g, '');
    if (/^-?(\d+\.?\d*|\.\d+)$/.test(s)) return parseFloat(s);
    const frac = parseFractionInput(str);
    return frac ? mixedValue(frac.whole, frac.num, frac.den) / frac.den : null;
}

function gradeDecimalAnswer(userInput, answer) {
    const value = parseDecimalInput(userInput);
    if (value === null) {
        return { invalid: true, message: "That doesn't look like a number yet. Try something like -7.56 or 12." };
    }
    return Math.abs(value - answer.value) < 1e-9
        ? { verdict: 'correct', message: '' }
        : { verdict: 'wrong', message: `The correct answer is ${answer.display}.` };
}

// ===== routing =====
//   /units/grade8/fractions               → unit overview (every topic)
//   /units/grade8/fractions/compare       → topic menu: learn or practise?
//   /units/grade8/fractions/compare#learn → the lesson
//   /units/grade8/fractions/compare#3     → question 3 (1-based)
//   /units/grade8/fractions/compare#done  → results
const FOCUS_SECTION = (typeof UNIT_FOCUS_SECTION !== 'undefined' && UNIT_FOCUS_SECTION) || null;

function pageHash(page) {
    if (page === 'done') return 'done';
    if (page === 'lesson') return 'learn';
    if (typeof page === 'number') return String(page + 1);
    return '';   // the topic menu
}

function topicUrl(sectionId, page) {
    const hash = pageHash(page);
    return `${UNIT_BASE_URL}/${sectionId}${hash ? `#${hash}` : ''}`;
}

function parsePage(sectionId) {
    const page = decodeURIComponent(location.hash.slice(1));
    if (page === 'done') return 'done';
    if (page === 'learn') return 'lesson';
    if (/^\d+$/.test(page)) {
        const i = parseInt(page, 10) - 1;
        if (i >= 0 && i < pagesFor(sectionId).length) return i;
    }
    return 'menu';
}

function ulGo(sectionId, page) {
    if (sectionId !== FOCUS_SECTION) {
        location.href = topicUrl(sectionId, page);
        return;
    }
    const hash = pageHash(page);
    if (location.hash.slice(1) === hash) ulRoute();
    else location.hash = hash;
}

function ulRoute() {
    const content = document.getElementById('ul-content');
    if (!FOCUS_SECTION) {
        // old tabbed links like /units/grade8/fractions#compare/3 → that topic's own page
        const [sid, page] = decodeURIComponent(location.hash.slice(1)).split('/');
        if (sid && UNIT_SECTIONS.some(s => s.id === sid)) {
            location.replace(`${UNIT_BASE_URL}/${sid}${page ? `#${page}` : ''}`);
            return;
        }
        content.innerHTML = overviewHTML();
        wireCommon(content);
        return;
    }
    const newPage = parsePage(FOCUS_SECTION);
    const pageChanged = newPage !== ulState.page;
    ulState.activeSection = FOCUS_SECTION;
    ulState.page = newPage;
    if (pageChanged) {
        ulState.lastResults = {};
        ulFocus = 'first';
    }
    renderTopic();
    if (pageChanged) window.scrollTo({ top: 0 });
}

function ulInit() {
    ulLoadProgress();
    UNIT_QUESTIONS.forEach(q => {
        (ulState.questionsBySection[q.section] = ulState.questionsBySection[q.section] || []).push(q);
    });
    window.addEventListener('hashchange', ulRoute);
    ulRoute();
}

// ===== shared bits =====
const KIND_LABELS = {
    number: { icon: '🔢', name: 'Number problem', plural: 'number problems', heading: 'Number problems' },
    word:   { icon: '📝', name: 'Word problem',   plural: 'word problems',   heading: 'Word problems' },
};
const STATUS_LABELS = { correct: '✓ Correct', close: '~ Almost', wrong: '✗ Review', skipped: '– Not answered' };

// Question types answered by clicking tiles rather than typing.
function usesTiles(q) { return q.qtype === 'compare' || q.qtype === 'choice' || q.qtype === 'order'; }

function kindOf(q) { return q.kind === 'word' ? 'word' : 'number'; }
function questionsFor(sectionId) { return ulState.questionsBySection[sectionId] || []; }

// Questions tagged with the same q.page share a page. Anything untagged gets a
// page of its own, so a topic that never heard of pages behaves as it always did.
function pagesFor(sectionId) {
    if (!ulState.pagesBySection[sectionId]) {
        const pages = [];
        questionsFor(sectionId).forEach(q => {
            const last = pages[pages.length - 1];
            if (q.page && last && last.key === q.page) last.questions.push(q);
            else pages.push({ key: q.page, questions: [q] });
        });
        ulState.pagesBySection[sectionId] = pages;
    }
    return ulState.pagesBySection[sectionId];
}

// "question" reads better than "page" where each page holds exactly one.
function pageWord(sectionId) {
    return pagesFor(sectionId).some(p => p.questions.length > 1) ? 'page' : 'question';
}

function pageIndexOf(sectionId, qid) {
    return pagesFor(sectionId).findIndex(p => p.questions.some(q => q.id === qid));
}

// A page is only as good as its worst answered question, and counts for nothing
// until every question on it has been answered.
function pageVerdict(page) {
    const verdicts = page.questions.map(q => ulState.progress[q.id]);
    if (verdicts.some(v => !v)) return '';
    if (verdicts.includes('wrong')) return 'wrong';
    return verdicts.includes('close') ? 'close' : 'correct';
}
function stars(n) { return '★'.repeat(n) + '☆'.repeat(3 - n); }

function sectionStats(sectionId) {
    const qs = questionsFor(sectionId);
    const st = { total: qs.length, answered: 0, correct: 0, close: 0, wrong: 0 };
    qs.forEach(q => {
        const v = ulState.progress[q.id];
        if (v) { st.answered++; st[v]++; }
    });
    st.score = st.total ? Math.round(((st.correct + st.close * 0.5) / st.total) * 100) : 0;
    // where "continue" goes: the first PAGE still holding an unanswered question
    st.firstOpen = pagesFor(sectionId)
        .findIndex(p => p.questions.some(q => !ulState.progress[q.id]));
    return st;
}

function practiceCta(st, sectionId) {
    if (st.answered === 0) return { label: 'Start practice', go: 0 };
    if (st.firstOpen === -1) return { label: 'See my results', go: 'done' };
    return { label: `Continue at ${pageWord(sectionId)} ${st.firstOpen + 1}`, go: st.firstOpen };
}

// "one per page" or "two to a page" — how the practice is laid out.
function layoutSummary(sectionId) {
    const most = pagesFor(sectionId).reduce((n, p) => Math.max(n, p.questions.length), 1);
    if (most === 1) return 'one per page';
    return most === 2 ? 'two to a page' : `up to ${most} to a page`;
}

function kindSummary(questions) {
    const counts = { number: 0, word: 0 };
    questions.forEach(q => counts[kindOf(q)]++);
    if (!counts.word) return `${counts.number} questions`;
    return `${counts.number} ${KIND_LABELS.number.plural}, then ${counts.word} ${KIND_LABELS.word.plural}`;
}

function progressBarHTML(done, total) {
    const pct = total ? Math.round((done / total) * 100) : 0;
    return `<div class="ul-bar" role="progressbar" aria-valuemin="0" aria-valuemax="${total}" aria-valuenow="${done}">
        <div class="ul-bar-fill" style="width:${pct}%"></div></div>`;
}

function scoreRingHTML(score, size = 'md') {
    const r = 42, c = 2 * Math.PI * r;
    return `<div class="ul-ring ul-ring-${size}" role="img" aria-label="Score ${score} out of 100">
        <svg viewBox="0 0 100 100" aria-hidden="true">
            <circle cx="50" cy="50" r="${r}" class="ul-ring-track"/>
            <circle cx="50" cy="50" r="${r}" class="ul-ring-fill" transform="rotate(-90 50 50)"
                stroke-dasharray="${(c * score / 100).toFixed(1)} ${c.toFixed(1)}"/>
        </svg>
        <div class="ul-ring-text"><span class="ul-ring-num">${score}</span><span class="ul-ring-label">score</span></div>
    </div>`;
}

// Splits a worked solution into short steps ("... is 24. Rewrite: ..." → two steps).
function solutionSteps(steps) {
    return String(steps || '').split(/\n|(?<=\.)\s+(?=[A-Z])/).map(s => s.trim()).filter(Boolean);
}

function topicListHTML(currentId) {
    const items = UNIT_SECTIONS.map(s => {
        const st = sectionStats(s.id);
        return `<li><a class="${s.id === currentId ? 'current' : ''}" href="${topicUrl(s.id)}">
            <span class="ul-tl-emoji">${s.emoji}</span>
            <span class="ul-tl-title">${escHTML(s.title)}</span>
            <span class="ul-tl-count">${st.answered}/${st.total}</span>
        </a></li>`;
    }).join('');
    return `<div class="ul-side-card">
        <div class="ul-side-title">📚 Topics in this unit</div>
        <ol class="ul-topic-list">${items}</ol>
    </div>`;
}

function wireCommon(root) {
    root.querySelectorAll('[data-go]').forEach(btn => {
        btn.addEventListener('click', () => {
            const go = btn.dataset.go;
            ulGo(btn.dataset.section || FOCUS_SECTION, /^\d+$/.test(go) ? parseInt(go, 10) : go);
        });
    });
    root.querySelectorAll('.js-restart').forEach(btn => {
        btn.addEventListener('click', () => {
            if (!window.confirm('Start this topic over? Your answers for this topic will be cleared.')) return;
            const cleared = questionsFor(FOCUS_SECTION).map(q => q.id);
            cleared.forEach(id => {
                delete ulState.progress[id];
                delete ulState.stepState[id];
                delete ulState.draft[id];
            });
            ulWriteLocal();
            ulClearProgress(cleared);
            ulState.streak = 0;
            ulGo(FOCUS_SECTION, 0);
        });
    });
}

// ===== unit overview =====
function overviewHTML() {
    const total = UNIT_QUESTIONS.length;
    const answered = UNIT_QUESTIONS.filter(q => ulState.progress[q.id]).length;
    const done = UNIT_SECTIONS.filter(s => sectionStats(s.id).firstOpen === -1).length;
    return `
        <div class="ul-ov-bar">
            <div class="ul-ov-stat"><span class="ul-ov-num">${UNIT_SECTIONS.length}</span><span>topics</span></div>
            <div class="ul-ov-stat"><span class="ul-ov-num">${total}</span><span>practice questions</span></div>
            <div class="ul-ov-stat"><span class="ul-ov-num">${answered}</span><span>answered</span></div>
            <div class="ul-ov-stat"><span class="ul-ov-num">${done}</span><span>topics finished</span></div>
            <div class="ul-ov-progress">${progressBarHTML(answered, total)}</div>
        </div>
        <div class="ul-topic-grid">${UNIT_SECTIONS.map(topicCardHTML).join('')}</div>`;
}

function topicCardHTML(section, i) {
    const qs = questionsFor(section.id);
    const st = sectionStats(section.id);
    const words = qs.filter(q => kindOf(q) === 'word').length;
    const status = st.answered === 0 ? ['not-started', 'Not started']
        : st.firstOpen === -1 ? ['finished', `Finished · score ${st.score}`]
        : ['in-progress', 'In progress'];
    const cta = st.answered === 0 ? 'Start' : st.firstOpen === -1 ? 'Review' : 'Continue';
    return `
        <a class="ul-topic-card" href="${topicUrl(section.id)}" style="--topic-color:${escHTML(section.color || '#6C63FF')}">
            <div class="ul-topic-head">
                <span class="ul-topic-code">${i + 1}</span>
                <span class="ul-topic-emoji">${section.emoji}</span>
                <div>
                    <div class="ul-topic-title">${escHTML(section.title)}</div>
                    <div class="ul-topic-meta">${qs.length} questions${words ? ` · ${words} word` : ''}</div>
                </div>
            </div>
            <div class="ul-topic-foot">
                <div class="ul-topic-progress">${progressBarHTML(st.answered, st.total)}<span>${st.answered}/${st.total}</span></div>
                <span class="ul-topic-status ul-status-${status[0]}">${status[1]}</span>
                <span class="ul-topic-cta">${cta} →</span>
            </div>
        </a>`;
}

// ===== topic pages =====
function renderTopic() {
    const section = UNIT_SECTIONS.find(s => s.id === FOCUS_SECTION);
    const content = document.getElementById('ul-content');
    if (!section) { content.innerHTML = ''; return; }
    const qs = questionsFor(section.id);
    const pages = pagesFor(section.id);
    const page = ulState.page;
    if (page === 'done') content.innerHTML = resultsPageHTML(section, qs);
    else if (typeof page === 'number') content.innerHTML = questionPageHTML(section, pages, page);
    else if (page === 'lesson') content.innerHTML = lessonPageHTML(section, qs);
    else content.innerHTML = menuPageHTML(section, qs);
    wireCommon(content);
    if (typeof page === 'number') wirePage(section, pages[page].questions);
}


// The landing page for a topic: read the lesson first, or go straight to the
// questions. The lesson itself lives one click away, under "Learn".
function menuPageHTML(section, qs) {
    const st = sectionStats(section.id);
    const cta = practiceCta(st, section.id);
    const concepts = section.key_concepts.length;
    const examples = section.examples.length;
    return `
        <div class="ul-layout">
            <div class="ul-layout-main">
                <div class="ul-choice-grid">
                    <button class="ul-choice" data-go="lesson">
                        <span class="ul-choice-emoji" aria-hidden="true">📖</span>
                        <span class="ul-choice-title">Learn</span>
                        <span class="ul-choice-desc">${concepts} key concept${concepts === 1 ? '' : 's'}
                            and ${examples} worked example${examples === 1 ? '' : 's'}, with pictures.</span>
                        <span class="ul-choice-cta">Read the lesson →</span>
                    </button>
                    <button class="ul-choice ul-choice-practice" data-go="${cta.go}">
                        <span class="ul-choice-emoji" aria-hidden="true">✏️</span>
                        <span class="ul-choice-title">Practice</span>
                        <span class="ul-choice-desc">${kindSummary(qs)}, ${layoutSummary(section.id)}, marked as you go.</span>
                        <span class="ul-choice-cta">${cta.label} →</span>
                    </button>
                </div>
            </div>
            <aside class="ul-layout-side"><div class="ul-side-sticky">
                <div class="ul-side-card">
                    <div class="ul-side-title">✏️ Your progress</div>
                    <div class="ul-score-row">
                        ${scoreRingHTML(st.score)}
                        <div><div class="ul-big-num">${st.answered}<span>/${st.total}</span></div><div class="ul-muted">answered</div></div>
                    </div>
                    ${st.answered ? '<button class="ul-side-link js-restart">🔄 Start over</button>' : ''}
                </div>
                ${topicListHTML(section.id)}
            </div></aside>
        </div>`;
}

function lessonPageHTML(section, qs) {
    const st = sectionStats(section.id);
    const cta = practiceCta(st, section.id);
    const concepts = section.key_concepts.map(k => (typeof k === 'string' ? { text: k } : k));
    const conceptCards = concepts.map((c, i) => `
        <article class="ul-concept ${c.visual ? 'has-visual' : ''}">
            <div class="ul-concept-text"><span class="ul-concept-num">${i + 1}</span><span>${renderMath(c.text)}</span></div>
            ${renderVisual(c.visual)}
        </article>`).join('');
    const examples = section.examples.map(ex => `
        <article class="ul-example-card">
            <div class="ul-example-label">Worked example</div>
            <div class="ul-example-prompt">${renderMath(ex.prompt)}</div>
            <ol class="ul-example-steps">${solutionSteps(ex.steps).map(s => `<li>${escHTML(s)}</li>`).join('')}</ol>
            <div class="ul-example-answer">Answer: ${escHTML(ex.answer_display)}</div>
        </article>`).join('');

    return `
        <div class="ul-layout">
            <div class="ul-layout-main">
                <button class="ul-back-link" data-go="menu">← Back to ${escHTML(section.title)}</button>
                <section class="ul-panel ul-intro-panel">
                    <div class="ul-kicker">📘 The big idea</div>
                    <p class="ul-lesson-blurb">${escHTML(section.blurb)}</p>
                </section>
                <h2 class="ul-h2">🔑 Key concepts</h2>
                <div class="ul-concept-grid">${conceptCards}</div>
                <h2 class="ul-h2">✍️ Worked examples</h2>
                <div class="ul-examples">${examples}</div>
                <div class="ul-lesson-end">
                    <div><strong>Ready to practise?</strong> ${kindSummary(qs)}, ${layoutSummary(section.id)}.</div>
                    <button class="ul-next-btn" data-go="${cta.go}">${cta.label} →</button>
                </div>
            </div>
            <aside class="ul-layout-side"><div class="ul-side-sticky">
                <div class="ul-side-card">
                    <div class="ul-side-title">✏️ Practice</div>
                    <div class="ul-score-row">
                        ${scoreRingHTML(st.score)}
                        <div><div class="ul-big-num">${st.answered}<span>/${st.total}</span></div><div class="ul-muted">answered</div></div>
                    </div>
                    <p class="ul-muted">${kindSummary(qs)}, ${layoutSummary(section.id)}.</p>
                    <button class="ul-next-btn ul-block" data-go="${cta.go}">${cta.label} →</button>
                    ${st.answered ? '<button class="ul-prev-btn ul-block" data-go="0">Start from question 1</button>' : ''}
                </div>
                ${topicListHTML(section.id)}
            </div></aside>
        </div>`;
}

// The filled-in example at the top of the page, exactly as question 1 is
// filled in for you at the top of each worksheet: the same chain the problems
// below ask for, with every blank already written in.
function sampleHTML(section, q) {
    const samples = (section.samples || []).filter(s => s.set === q.set);
    if (!samples.length) return '';
    const rows = samples.map(sample => {
        const steps = sample.steps.map(row => {
            const boxes = row.fields.map((value, f) => {
                const joiner = f ? `<span class="ul-chain-join">${escHTML(row.join || '')}</span>` : '';
                return `${joiner}<span class="ul-chain-value">${renderValue(value)}</span>`;
            }).join('');
            return `<span class="ul-chain-step">
                <span class="ul-chain-boxes">${boxes}</span>
                <span class="ul-chain-label">${escHTML(row.label)}</span>
            </span>`;
        }).join('<span class="ul-chain-eq" aria-hidden="true">=</span>');
        return `<div class="ul-chain ul-chain-sample">
            <span class="ul-chain-prompt">${renderMath(sample.prompt)}</span>${steps}
        </div>`;
    }).join('');
    return `<section class="ul-sample">
        <div class="ul-sample-label">✏️ Worked for you — fill in the same lines below</div>
        ${rows}
    </section>`;
}

function questionPageHTML(section, pages, idx) {
    const qs = questionsFor(section.id);
    const page = pages[idx];
    const prev = pages[idx - 1];
    const shared = page.questions.length > 1;
    const isLast = idx === pages.length - 1;
    const nextGo = isLast ? 'done' : idx + 1;
    const done = page.questions.every(q => ulState.progress[q.id]);
    const startsWordPart = kindOf(page.questions[0]) === 'word'
        && !!prev && kindOf(prev.questions[prev.questions.length - 1]) !== 'word';

    return `
        <div class="ul-layout">
            <div class="ul-layout-main">
                ${startsWordPart ? `<div class="ul-part-banner">📝 Word problems start here! Read the story carefully, find the numbers you need, then answer the question.</div>` : ''}
                ${shared ? `<div class="ul-page-label">Page ${idx + 1} of ${pages.length} · ${page.questions.length} problems</div>` : ''}
                ${sampleHTML(section, page.questions[0])}
                ${page.questions.map(q => questionCardHTML(q, qs, nextGo, isLast, shared)).join('')}
                ${shared ? `<div class="ul-page-foot">
                    ${done ? `<button class="ul-next-btn" data-go="${nextGo}">${isLast ? 'See my results' : 'Next page'} →</button>`
                           : '<button class="ul-check-btn-lg js-check-page">Check the whole page</button>'}
                </div>` : ''}
                <div class="ul-pager-nav">
                    <button class="ul-prev-btn" data-go="${idx === 0 ? 'lesson' : idx - 1}">← ${idx === 0 ? 'Lesson' : 'Previous'}</button>
                    ${done ? '' : `<button class="ul-skip-btn" data-go="${nextGo}">${isLast ? 'Skip to results' : 'Skip for now'} →</button>`}
                </div>
            </div>
            ${questionSidebarHTML(section, pages, idx)}
        </div>`;
}

// One problem, whether it has the page to itself or shares it with another.
// Everything inside is addressed by class and scoped to the card, so two of
// these can sit on the same page without fighting over element ids.
function questionCardHTML(q, qs, nextGo, isLast, shared) {
    const idx = qs.indexOf(q);
    const kind = kindOf(q);
    const sameKind = qs.filter(x => kindOf(x) === kind);
    const solved = ulState.progress[q.id];
    const last = ulState.lastResults[q.id] || null;
    const isTiles = usesTiles(q);
    const hintId = `ul-hint-${q.id}`;
    // A chain prints the problem at the head of its own row, so printing it
    // above as well would just be the same line twice.
    const chain = q.qtype === 'steps';
    return `
        <section class="ul-panel ul-q-panel ${shared ? 'ul-q-shared' : ''} ${solved ? `is-${solved}` : ''}" data-qid="${escHTML(q.id)}">
            ${shared ? `
            <div class="ul-q-top ul-q-top-slim">
                <span class="ul-q-num">${idx + 1}.</span>
                <span class="ul-q-stars" title="Difficulty ${q.difficulty} of 3" aria-label="Difficulty ${q.difficulty} of 3">${stars(q.difficulty)}</span>
            </div>` : `
            <div class="ul-q-top">
                <span class="ul-q-count">Question ${idx + 1}<span> of ${qs.length}</span></span>
                <span class="ul-chip">${KIND_LABELS[kind].icon} ${KIND_LABELS[kind].name} ${sameKind.indexOf(q) + 1} of ${sameKind.length}</span>
                <span class="ul-q-stars" title="Difficulty ${q.difficulty} of 3" aria-label="Difficulty ${q.difficulty} of 3">${stars(q.difficulty)}</span>
            </div>`}
            ${chain ? '' : `<div class="ul-q-prompt-lg">${renderMath(q.prompt)}</div>`}
            ${answerZoneHTML(q, solved, last)}
            <div class="ul-warn js-warn" hidden></div>
            ${solved ? feedbackPanelHTML(q, solved, last, nextGo, isLast, shared) : `
            <div class="ul-q-actions">
                <button class="ul-check-btn-lg js-check" ${isTiles ? 'disabled' : ''}>Check answer</button>
                <button class="ul-hint-btn js-hint-toggle" aria-expanded="false" aria-controls="${hintId}">💡 Need a hint?</button>
            </div>
            <div class="ul-hint-box js-hint" id="${hintId}" hidden>${escHTML(q.tip)}</div>`}
        </section>`;
}

// ===== worked chains =====
// The paper worksheet gives one long row per question — the problem, then a
// blank for each line of working, with the labels printed underneath — and the
// teacher marks every blank at once. So does this: the whole row is open from
// the start, one "Check answer" submits it, and each blank comes back ticked or
// crossed with a sentence saying what that line wanted.

function ulStepState(q) {
    if (!ulState.stepState[q.id]) {
        ulState.stepState[q.id] = {
            typed: {},        // "row:field" -> what is in that box
            marks: null,      // per row, per field: 'correct' | 'form' | 'wrong' | 'blank'
            attempts: 0,      // submissions so far
            warn: '',         // why the last submission wasn't accepted at all
        };
    }
    return ulState.stepState[q.id];
}

function stepValue(st, i, f) { return st.typed[`${i}:${f}`] || ''; }

// ===== grading =====
// A blank is graded on FORM, not just value: the common-denominator line wants
// 20/30 and the simplify line wants 13/15, even though those are one number. A
// right value in the wrong form is its own outcome, so the student is told which
// mistake they made rather than just "wrong".
function markStepField(typed, expect) {
    if (!String(typed).trim()) return 'blank';
    const result = gradeStepField(typed, expect);
    if (result.invalid) return 'wrong';
    if (result.verdict === 'correct') return 'correct';
    return result.form ? 'form' : 'wrong';
}

function markChain(q, st) {
    return q.answer.steps.map((row, i) =>
        row.fields.map((expect, f) => markStepField(stepValue(st, i, f), expect)));
}

function flatMarks(marks) { return marks.reduce((all, row) => all.concat(row), []); }

// Every blank right is correct; every blank at least the right NUMBER is almost;
// anything else is one to review. Same three outcomes as every other question
// type, so the score and the question map keep meaning what they meant.
function chainVerdict(marks) {
    const all = flatMarks(marks);
    if (all.every(m => m === 'correct')) return 'correct';
    return all.every(m => m === 'correct' || m === 'form') ? 'close' : 'wrong';
}

// What went wrong on one line, in words, for the review panel under the chain.
function stepFaults(q, st, i) {
    const row = q.answer.steps[i];
    const faults = [];
    row.fields.forEach((expect, f) => {
        const typed = stepValue(st, i, f).trim();
        const mark = markStepField(typed, expect);
        if (mark === 'correct') return;
        const where = row.fields.length > 1 ? `Box ${f + 1}: ` : '';
        if (mark === 'blank') {
            faults.push(`${where}left empty — this line needs ${expect}.`);
            return;
        }
        const result = gradeStepField(typed, expect);
        if (result.invalid) {
            faults.push(`${where}"${typed}" isn't a number I can read. This line needs ${expect}.`);
        } else if (result.form) {
            faults.push(`${where}you wrote ${typed}, which is the right value — but ${result.why} It should be ${expect}.`);
        } else {
            faults.push(`${where}you wrote ${typed}, but this line needs ${expect}.`);
        }
    });
    return faults;
}

// ===== the chain, laid out as the worksheet lays it out =====
function stepsZoneHTML(q, solved) {
    const st = ulStepState(q);
    const marks = solved && st.marks ? st.marks : null;
    const steps = q.answer.steps
        .map((row, i) => chainStepHTML(q, row, i, st, marks, solved))
        .join('<span class="ul-chain-eq" aria-hidden="true">=</span>');
    return `
        <div class="ul-chain">
            <span class="ul-chain-prompt">${renderMath(q.prompt)}</span>
            ${steps}
        </div>
        ${solved && marks ? chainReviewHTML(q, st, marks) : ''}`;
}

function chainStepHTML(q, row, i, st, marks, solved) {
    const rowMarks = marks ? marks[i] : null;
    const worst = rowMarks
        ? (rowMarks.every(m => m === 'correct') ? 'correct'
            : rowMarks.some(m => m === 'wrong' || m === 'blank') ? 'wrong' : 'form')
        : '';
    // No brackets round a negative box: the worksheets write the working lines
    // as "-12/5 + -23/6", and the sample above the page does the same.
    const boxes = row.fields.map((expect, f) => {
        const typed = stepValue(st, i, f);
        const mark = rowMarks ? rowMarks[f] : '';
        const box = solved
            ? `<span class="ul-chain-value is-${mark}">${typed.trim() ? renderValue(typed) : '—'}</span>`
            : `<input type="text" class="ul-chain-input" data-step="${i}" data-field="${f}"
                   autocomplete="off" spellcheck="false" placeholder="?"
                   aria-label="${escHTML(row.label)}${row.fields.length > 1 ? `, box ${f + 1}` : ''}"
                   value="${escHTML(typed)}">`;
        const joiner = f ? `<span class="ul-chain-join">${escHTML(row.join || '')}</span>` : '';
        return `${joiner}${box}`;
    }).join('');

    return `
        <span class="ul-chain-step ${worst ? `is-${worst}` : ''}" data-step="${i}">
            <span class="ul-chain-boxes">${boxes}</span>
            <span class="ul-chain-label">
                ${worst ? `<span class="ul-chain-mark">${worst === 'correct' ? '✓' : '✗'}</span>` : ''}${escHTML(row.label)}
            </span>
        </span>`;
}

// Under the chain: every line that wasn't right, and why. A line that was right
// says so in one word rather than explaining itself.
function chainReviewHTML(q, st, marks) {
    const rows = q.answer.steps.map((row, i) => {
        const faults = flatMarks([marks[i]]).every(m => m === 'correct') ? [] : stepFaults(q, st, i);
        if (!faults.length) return '';
        return `<li class="ul-chain-fault">
            <span class="ul-chain-fault-step">${escHTML(row.label)}</span>
            <span class="ul-chain-fault-why">${faults.map(escHTML).join(' ')}
                ${row.note ? `<em>Remember: ${escHTML(row.note)}.</em>` : ''}</span>
        </li>`;
    }).filter(Boolean).join('');
    if (!rows) return '';
    return `<ul class="ul-chain-faults">${rows}</ul>`;
}

// Grades the chain and locks the question in, the same way checking a
// single-box answer does. Returns false when there was nothing to grade, so the
// student gets a nudge instead of a question marked wrong for being untouched.
function submitChain(q) {
    const st = ulStepState(q);
    const marks = markChain(q, st);
    if (flatMarks(marks).every(m => m === 'blank')) {
        st.warn = 'Fill in the boxes first, then check your answer.';
        return false;
    }
    st.warn = '';
    st.marks = marks;
    st.attempts++;
    const verdict = chainVerdict(marks);
    ulState.progress[q.id] = verdict;
    ulSaveProgress({ [q.id]: verdict });
    ulState.streak = verdict === 'correct' ? ulState.streak + 1 : 0;
    ulState.lastResults[q.id] = { qid: q.id, verdict, message: '', picked: null, fresh: true };
    return true;
}

function wireChain(card, q) {
    const st = ulStepState(q);
    const warn = card.querySelector('.js-warn');
    const inputs = Array.from(card.querySelectorAll('.ul-chain-input'));

    inputs.forEach(input => {
        // written through to state on every keystroke, so checking another
        // problem on this page — which re-renders all of them — keeps this one
        input.addEventListener('input', () => {
            st.typed[`${input.dataset.step}:${input.dataset.field}`] = input.value;
            st.warn = '';
            warn.hidden = true;
        });
        input.addEventListener('keydown', e => {
            if (e.key !== 'Enter') return;
            // Enter moves to the next box and only submits from the last one,
            // so a half-filled row is never handed in by accident
            const next = inputs[inputs.indexOf(input) + 1];
            if (next) next.focus();
            else runCheck();
        });
    });

    function runCheck() {
        if (!submitChain(q)) {
            warn.textContent = st.warn;
            warn.hidden = false;
            return;
        }
        ulFocus = null;
        renderTopic();
    }
    card.querySelector('.js-check').addEventListener('click', runCheck);
}

const INPUT_HINTS = {
    fraction: ['e.g. -3/4 or 1 1/2', 'Type a fraction like -3/4, a mixed number like 1 1/2, or a whole number.'],
    decimal:  ['e.g. -7.56', 'Type the decimal, including the minus sign if the answer is negative.'],
    integer:  ['e.g. 12', 'Type a whole number.'],
};

// Ordering: the tiles are shown scrambled until the question is answered, then
// re-shown in the correct order so the student can see where each one belonged.
function orderZoneHTML(q, solved, last) {
    // After a reload the student's own sequence is gone, so only mark the tiles
    // when we still know it — except for a correct answer, where every tile was
    // in the right place by definition.
    const picked = last && Array.isArray(last.picked) ? last.picked : null;
    const sequence = solved ? q.answer.order : q.options;
    const tiles = sequence.map((opt, i) => {
        const cls = !solved ? ''
            : solved === 'correct' ? 'is-correct'
            : !picked ? ''
            : picked[i] === opt ? 'is-correct' : 'is-wrong';
        return `<button class="ul-tile ul-tile-order ${cls}" data-choice="${escHTML(opt)}" ${solved ? 'disabled' : ''}>
            <span class="ul-tile-rank">${solved ? i + 1 : ''}</span>
            <span class="ul-tile-face">${renderMath(opt)}</span>
        </button>`;
    }).join('');
    return `
        <div class="ul-tiles ul-tiles-order" role="group" aria-label="Put these in order">${tiles}</div>
        ${solved ? '' : '<div class="ul-input-help">Click the numbers one at a time, in order. Click one again to take it back out.</div>'}`;
}

function answerZoneHTML(q, solved, last) {
    if (q.qtype === 'steps') return stepsZoneHTML(q, solved);
    if (q.qtype === 'order') return orderZoneHTML(q, solved, last);
    if (q.qtype === 'compare' || q.qtype === 'choice') {
        const options = q.qtype === 'compare' ? ['<', '=', '>'] : q.options;
        const correct = q.qtype === 'compare' ? q.answer.symbol : q.answer.choice;
        const tiles = options.map(opt => {
            let cls = '';
            if (solved && opt === correct) cls = 'is-correct';
            else if (solved && last && last.picked === opt) cls = 'is-wrong';
            return `<button class="ul-tile ${cls}" data-choice="${escHTML(opt)}" ${solved ? 'disabled' : ''}>${renderMath(opt)}</button>`;
        }).join('');
        return `<div class="ul-tiles ${q.qtype === 'compare' ? 'ul-tiles-symbols' : ''}" role="group" aria-label="Answer choices">${tiles}</div>`;
    }
    const [placeholder, help] = INPUT_HINTS[q.qtype] || INPUT_HINTS.fraction;
    return `
        <div class="ul-input-row">
            <label class="ul-input-label" for="ul-answer-${escHTML(q.id)}">Your answer</label>
            <input type="text" class="ul-answer-input-lg js-answer" id="ul-answer-${escHTML(q.id)}" placeholder="${placeholder}"
                autocomplete="off" spellcheck="false"
                value="${escHTML(solved && last ? last.picked : (ulState.draft[q.id] || ''))}" ${solved ? 'disabled' : ''}>
        </div>
        ${solved ? '' : `<div class="ul-input-help">${help}</div>`}`;
}

function feedbackPanelHTML(q, verdict, last, nextGo, isLast, shared) {
    const chain = q.qtype === 'steps';
    const titles = chain ? {
        correct: '🎉 Every line right.',
        close: '👍 Every value right — but check how you wrote the marked lines.',
        wrong: '💭 Not quite — the crossed lines above say what each one needed.',
    } : {
        correct: '🎉 Correct! Great work.',
        close: '👍 Almost! The value is right.',
        wrong: "💭 Not quite — let's see how to solve it.",
    };
    const message = chain ? ''
        : verdict === 'close'
        ? (last ? last.message : `Always double-check reducing and improper → mixed. Fully simplified, the answer is ${q.answer.display}.`)
        : '';
    const steps = (verdict === 'correct' || chain) ? [] : solutionSteps(q.steps);
    return `
        <div class="ul-fb ul-fb-${verdict}" role="status">
            <div class="ul-fb-title">${titles[verdict]}</div>
            ${message ? `<p class="ul-fb-msg">${escHTML(message)}</p>` : ''}
            ${verdict === 'correct' && !chain ? '' : `<div class="ul-fb-answer">Answer: <strong>${answerText(q.answer.display)}</strong></div>`}
            ${steps.length ? `
            <div class="ul-fb-solution">
                <div class="ul-fb-sol-title">How to solve it</div>
                <ol>${steps.map(s => `<li>${escHTML(s)}</li>`).join('')}</ol>
            </div>` : ''}
            <div class="ul-fb-actions">
                ${shared ? '' : `<button class="ul-next-btn js-fb-next" data-go="${nextGo}">${isLast ? 'See my results' : 'Next question'} →</button>`}
                ${verdict === 'correct' ? '' : '<button class="ul-prev-btn js-retry">🔄 Try again</button>'}
            </div>
        </div>`;
}

function questionMapHTML(pages, currentIdx, sectionId) {
    const word = pageWord(sectionId);
    const hasWords = pages.some(p => kindOf(p.questions[0]) === 'word');
    return ['number', 'word'].map(kind => {
        const items = pages.map((p, i) => ({ p, i })).filter(({ p }) => kindOf(p.questions[0]) === kind);
        if (!items.length) return '';
        const dots = items.map(({ p, i }) => {
            const v = pageVerdict(p);
            return `<button class="ul-dot ${v ? `ul-dot-${v}` : ''} ${i === currentIdx ? 'current' : ''}"
                data-go="${i}" aria-label="${word} ${i + 1}${v ? `: ${v}` : ''}">${i + 1}</button>`;
        }).join('');
        return `<div class="ul-map-group">
            ${hasWords ? `<div class="ul-map-label">${KIND_LABELS[kind].icon} ${KIND_LABELS[kind].heading}</div>` : ''}
            <div class="ul-map">${dots}</div>
        </div>`;
    }).join('');
}

// Signed-out learners keep their answers in this browser only. A quiet nudge in
// the sidebar, not a banner in the way of the question.
function signInHintHTML() {
    if (ulSignedIn()) return '';
    const next = encodeURIComponent(location.pathname);
    return `<div class="ul-side-card ul-signin-hint">
                🔐 <a href="/account?next=${next}">Sign in</a> to save your progress and pick up on any device.
            </div>`;
}

function questionSidebarHTML(section, pages, currentIdx) {
    const st = sectionStats(section.id);
    return `
        <aside class="ul-layout-side"><div class="ul-side-sticky">
            <div class="ul-side-card">
                <div class="ul-stats">
                    <div class="ul-stat-tile"><div class="ul-stat-num">${st.answered}<span>/${st.total}</span></div><div class="ul-stat-label">Answered</div></div>
                    <div class="ul-stat-tile"><div class="ul-stat-num">${st.correct}</div><div class="ul-stat-label">Correct</div></div>
                    <div class="ul-stat-tile"><div class="ul-stat-num">${ulState.streak}${ulState.streak >= 3 ? '🔥' : ''}</div><div class="ul-stat-label">In a row</div></div>
                </div>
                <div class="ul-score-row">
                    ${scoreRingHTML(st.score)}
                    <p class="ul-muted">Every correct answer raises your score. Get them all right to reach 100!</p>
                </div>
            </div>
            <div class="ul-side-card">
                <div class="ul-side-title">🗺️ ${pageWord(section.id) === 'page' ? 'Page' : 'Question'} map</div>
                ${questionMapHTML(pages, currentIdx, section.id)}
                <div class="ul-legend">
                    <span><i class="ul-dot-correct"></i>Correct</span>
                    <span><i class="ul-dot-close"></i>Almost</span>
                    <span><i class="ul-dot-wrong"></i>Review</span>
                    <span><i></i>Not yet</span>
                </div>
            </div>
            ${signInHintHTML()}
            <div class="ul-side-card ul-side-links">
                <button class="ul-side-link" data-go="lesson">📖 Review the lesson</button>
                <button class="ul-side-link" data-go="done">📊 See results</button>
                <button class="ul-side-link js-restart">🔄 Start over</button>
            </div>
        </div></aside>`;
}

// Which box should have the caret after the next render: 'first' on arriving at
// a page, or a question id after one of its lines was marked.
let ulFocus = null;

function wirePage(section, questions) {
    const content = document.getElementById('ul-content');
    questions.forEach(q => {
        const card = content.querySelector(`.ul-q-panel[data-qid="${CSS.escape(q.id)}"]`);
        if (card) wireQuestionCard(card, q);
    });

    // Hand the whole page in at once. Problems already marked are left alone,
    // and one with nothing typed into it is skipped, not marked wrong.
    const checkPage = content.querySelector('.js-check-page');
    if (checkPage) {
        checkPage.addEventListener('click', () => {
            const graded = questions.filter(q => !ulState.progress[q.id] && submitChain(q));
            if (!graded.length) {
                const warn = content.querySelector('.js-warn');
                if (warn) {
                    warn.textContent = 'Fill in some boxes first, then check the page.';
                    warn.hidden = false;
                }
                return;
            }
            ulFocus = null;
            renderTopic();
        });
    }
    restoreFocus(content, questions);
}

// Phones get no autofocus: an on-screen keyboard covering the question is worse
// than one extra tap.
function restoreFocus(content, questions) {
    const target = ulFocus;
    ulFocus = null;
    if (!target || !window.matchMedia('(pointer: fine)').matches) return;
    const scope = target === 'first'
        ? content
        : content.querySelector(`.ul-q-panel[data-qid="${CSS.escape(target)}"]`);
    if (!scope) return;
    const boxes = Array.from(scope.querySelectorAll('.ul-chain-input, .js-answer'))
        .filter(box => !box.disabled);
    const box = boxes.find(b => b.classList.contains('is-wrong')) || boxes.find(b => !b.value) || boxes[0];
    if (box) {
        box.focus({ preventScroll: true });
        box.setSelectionRange(box.value.length, box.value.length);
    }
}

function wireQuestionCard(card, q) {
    if (ulState.progress[q.id]) {
        const retry = card.querySelector('.js-retry');
        if (retry) {
            retry.addEventListener('click', () => {
                delete ulState.progress[q.id];
                delete ulState.stepState[q.id];
                delete ulState.draft[q.id];
                ulWriteLocal();
                ulClearProgress([q.id]);
                delete ulState.lastResults[q.id];
                ulFocus = q.id;
                renderTopic();
            });
        }
        // just checked: bring the feedback into view and let Enter go to the next question
        const last = ulState.lastResults[q.id];
        if (last && last.fresh) {
            last.fresh = false;
            const fb = card.querySelector('.ul-fb');
            if (fb) fb.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            const next = card.querySelector('.js-fb-next');
            if (next) next.focus({ preventScroll: true });
        }
        return;
    }

    const hintBtn = card.querySelector('.js-hint-toggle');
    const hint = card.querySelector('.js-hint');
    hintBtn.addEventListener('click', () => {
        hint.hidden = !hint.hidden;
        hintBtn.setAttribute('aria-expanded', String(!hint.hidden));
        hintBtn.textContent = hint.hidden ? '💡 Need a hint?' : '🙈 Hide hint';
    });

    if (q.qtype === 'steps') { wireChain(card, q); return; }

    const check = card.querySelector('.js-check');
    const warn = card.querySelector('.js-warn');
    let picked = null;
    let grade;

    if (q.qtype === 'order') {
        const tiles = Array.from(card.querySelectorAll('.ul-tile-order'));
        const sequence = [];
        const relabel = () => {
            tiles.forEach(tile => {
                const at = sequence.indexOf(tile.dataset.choice);
                tile.classList.toggle('selected', at !== -1);
                tile.querySelector('.ul-tile-rank').textContent = at === -1 ? '' : String(at + 1);
            });
            check.disabled = sequence.length !== tiles.length;
        };
        tiles.forEach(tile => {
            tile.addEventListener('click', () => {
                const at = sequence.indexOf(tile.dataset.choice);
                if (at === -1) sequence.push(tile.dataset.choice);
                else sequence.splice(at, 1);
                relabel();
            });
        });
        grade = () => {
            picked = sequence.slice();
            return gradeOrderAnswer(sequence, q.answer);
        };
    } else if (q.qtype === 'compare' || q.qtype === 'choice') {
        card.querySelectorAll('.ul-tile').forEach(tile => {
            tile.addEventListener('click', () => {
                card.querySelectorAll('.ul-tile').forEach(t => t.classList.remove('selected'));
                tile.classList.add('selected');
                picked = tile.dataset.choice;
                check.disabled = false;
            });
        });
        grade = () => (q.qtype === 'choice' ? gradeChoiceAnswer(picked, q.answer) : gradeCompareAnswer(picked, q.answer));
    } else {
        const input = card.querySelector('.js-answer');
        const graders = { decimal: gradeDecimalAnswer, integer: gradeIntegerAnswer };
        grade = () => {
            picked = input.value;
            return (graders[q.qtype] || gradeFractionAnswer)(picked, q.answer);
        };
        input.addEventListener('keydown', e => { if (e.key === 'Enter') runCheck(); });
        input.addEventListener('input', () => {
            // held in state so a sibling question's check doesn't wipe it
            ulState.draft[q.id] = input.value;
            warn.hidden = true;
        });
    }

    function runCheck() {
        if (usesTiles(q) && check.disabled) return;
        const result = grade();
        if (result.invalid) {
            warn.textContent = result.message;
            warn.hidden = false;
            return;
        }
        ulState.progress[q.id] = result.verdict;
        ulSaveProgress({ [q.id]: result.verdict });
        ulState.streak = result.verdict === 'correct' ? ulState.streak + 1 : 0;
        ulState.lastResults[q.id] = { qid: q.id, verdict: result.verdict, message: result.message, picked, fresh: true };
        renderTopic();
    }
    if (check) check.addEventListener('click', runCheck);
}

function resultsPageHTML(section, qs) {
    const st = sectionStats(section.id);
    const skipped = st.total - st.answered;
    const emoji = st.score === 100 ? '🏆' : st.score >= 70 ? '🌟' : '💪';
    const headline = st.score === 100 ? 'Perfect score!' : skipped ? 'Almost there — a few questions left!' : 'Topic complete!';
    const sectionIdx = UNIT_SECTIONS.findIndex(s => s.id === section.id);
    const nextSection = UNIT_SECTIONS[sectionIdx + 1];

    const rows = qs.map((q, i) => {
        const v = ulState.progress[q.id] || 'skipped';
        return `
            <button class="ul-review-row" data-go="${pageIndexOf(section.id, q.id)}">
                <span class="ul-dot ${v === 'skipped' ? '' : `ul-dot-${v}`}">${i + 1}</span>
                <span class="ul-review-prompt">${renderMath(q.prompt)}</span>
                <span class="ul-review-answer">${v === 'skipped' ? '' : `Answer: <strong>${answerText(q.answer.display)}</strong>`}</span>
                <span class="ul-review-status ul-status-${v}">${STATUS_LABELS[v]}</span>
            </button>`;
    }).join('');

    return `
        <div class="ul-layout">
            <div class="ul-layout-main">
                <section class="ul-panel ul-results-hero">
                    ${scoreRingHTML(st.score, 'lg')}
                    <div class="ul-results-body">
                        <div class="ul-results-title">${emoji} ${headline}</div>
                        <div class="ul-results-chips">
                            <span class="ul-chip ul-status-correct">✓ ${st.correct} correct</span>
                            ${st.close ? `<span class="ul-chip ul-status-close">~ ${st.close} almost</span>` : ''}
                            ${st.wrong ? `<span class="ul-chip ul-status-wrong">✗ ${st.wrong} to review</span>` : ''}
                            ${skipped ? `<span class="ul-chip">– ${skipped} not answered</span>` : ''}
                        </div>
                        <div class="ul-fb-actions">
                            ${nextSection ? `<button class="ul-next-btn" data-section="${nextSection.id}" data-go="menu">Next topic: ${escHTML(nextSection.title)} →</button>` : ''}
                            <button class="ul-prev-btn" data-go="lesson">📖 Review the lesson</button>
                            <button class="ul-prev-btn js-restart">🔄 Start over</button>
                        </div>
                    </div>
                </section>
                <section class="ul-panel">
                    <h2 class="ul-h2 ul-h2-flush">🧾 Question review</h2>
                    <p class="ul-muted">Tap any question to go back to it.</p>
                    <div class="ul-review-list">${rows}</div>
                </section>
            </div>
            <aside class="ul-layout-side"><div class="ul-side-sticky">${topicListHTML(section.id)}</div></aside>
        </div>`;
}

// ===== key-concept visuals =====
// Described in lessons.json as { type: 'pizzas' | 'bars' | 'numberline', ..., caption }.
const VISUAL_COLORS = { purple: '#6C63FF', teal: '#2BB3A9', coral: '#FF6B6B', orange: '#FF9F43' };

function fracToken(n, d) { return `{${n}/${d}}`; }

function renderVisual(v) {
    if (!v) return '';
    let body;
    if (v.type === 'pizzas') body = pizzasVisualHTML(v);
    else if (v.type === 'bars') body = barsVisualHTML(v);
    else if (v.type === 'numberline') body = numberLineVisualHTML(v);
    else if (v.type === 'signline') body = signLineVisualHTML(v);
    else if (v.type === 'rules') body = rulesVisualHTML(v);
    else return '';
    // multi-line captions are step lists, which read better left-aligned
    const captionClass = v.caption && v.caption.includes('\n') ? 'ul-visual-caption ul-visual-caption-steps' : 'ul-visual-caption';
    return `<div class="ul-visual">${body}${v.caption ? `<div class="${captionClass}">${renderMath(v.caption)}</div>` : ''}</div>`;
}

function pizzaSVG(n, d) {
    const r = 44;
    const point = deg => [r * Math.cos(deg * Math.PI / 180), r * Math.sin(deg * Math.PI / 180)];
    let slices = '';
    for (let i = 0; i < d; i++) {
        const a0 = -90 + (i * 360) / d, a1 = -90 + ((i + 1) * 360) / d;
        const [x0, y0] = point(a0), [x1, y1] = point(a1);
        const on = i < n;
        const shape = d === 1
            ? `<circle r="${r}"`
            : `<path d="M0,0 L${x0.toFixed(2)},${y0.toFixed(2)} A${r},${r} 0 ${a1 - a0 > 180 ? 1 : 0} 1 ${x1.toFixed(2)},${y1.toFixed(2)} Z"`;
        slices += `${shape} class="${on ? 'ul-pz-on' : 'ul-pz-off'}"/>`;
        if (on) {
            const mid = (a0 + a1) / 2 * Math.PI / 180;
            const pr = d === 1 ? 0 : r * 0.58;
            slices += `<circle cx="${(pr * Math.cos(mid)).toFixed(2)}" cy="${(pr * Math.sin(mid)).toFixed(2)}" r="5" class="ul-pz-pepperoni"/>`;
        }
    }
    return `<svg class="ul-pizza" viewBox="-50 -50 100 100" role="img" aria-label="${n} of ${d} slices">
        <circle r="48" class="ul-pz-plate"/>${slices}<circle r="${r}" class="ul-pz-crust"/></svg>`;
}

// Either one comparison ({ items, sign }) or several steps ({ rows: [...] }), where a row
// is pizzas ({ note, items, sign }) or a text-only explanation ({ title, lines }).
function pizzasVisualHTML(v) {
    const rows = v.rows || [{ items: v.items, sign: v.sign }];
    return rows.map((row, i) => {
        const arrow = i > 0 ? '<div class="ul-vis-step-arrow" aria-hidden="true">⬇</div>' : '';
        if (!row.items) {
            return `${arrow}
                <div class="ul-vis-info">
                    ${row.title ? `<div class="ul-vis-info-title">${escHTML(row.title)}</div>` : ''}
                    ${(row.lines || []).map(line => `<div class="ul-vis-info-line">${renderMath(line)}</div>`).join('')}
                </div>`;
        }
        const items = row.items.map(it => `
            <div class="ul-vis-item">
                ${pizzaSVG(it.n, it.d)}
                <div class="ul-vis-label">${renderMath(fracToken(it.n, it.d))}</div>
                <div class="ul-vis-sub">${it.n} of ${it.d} slices</div>
            </div>`);
        const sign = row.sign === '?' ? `<div class="ul-vis-sign ul-vis-sign-unknown">?</div>` : `<div class="ul-vis-sign">${escHTML(row.sign)}</div>`;
        return `
            ${arrow}
            ${row.note ? `<div class="ul-vis-note">${renderMath(row.note)}</div>` : ''}
            <div class="ul-vis-row">${items.join(sign)}</div>`;
    }).join('');
}

function fractionBarHTML(n, d, color) {
    let segs = '';
    for (let i = 0; i < d; i++) {
        segs += `<span class="ul-vseg" ${i < n ? `style="background:${color}"` : ''}></span>`;
    }
    return `<div class="ul-vbar" role="img" aria-label="${n} of ${d} equal parts">${segs}</div>`;
}

function barsVisualHTML(v) {
    return `<div class="ul-vbars">${v.rows.map(row => `
        ${row.note ? `<div class="ul-vnote">${escHTML(row.note)}</div>` : ''}
        <div class="ul-vrow">
            <div class="ul-vlabel">${renderMath(row.label)}</div>
            ${fractionBarHTML(row.n, row.d, VISUAL_COLORS[row.color] || VISUAL_COLORS.purple)}
        </div>`).join('')}</div>`;
}

function numberLineVisualHTML(v) {
    const points = v.points.map(p => {
        const pct = Math.max(0, Math.min(1, p.n / p.d)) * 100;
        const color = VISUAL_COLORS[p.color] || VISUAL_COLORS.purple;
        return `<div class="ul-nl-point" style="left:${pct}%">
                    <div class="ul-nl-runner">${escHTML(p.icon || '')}</div>
                    <div class="ul-nl-label" style="border-color:${color}">${renderMath(fracToken(p.n, p.d))}</div>
                    <div class="ul-nl-dot" style="background:${color}"></div>
                </div>`;
    }).join('');
    return `<div class="ul-nl" role="img" aria-label="Number line from 0 to 1">
        <div class="ul-nl-track">
            <div class="ul-nl-tick" style="left:0%"><span>0</span></div>
            <div class="ul-nl-tick ul-nl-half" style="left:50%"><span>½</span></div>
            <div class="ul-nl-tick" style="left:100%"><span>1 whole 🏁</span></div>
            ${v.halfway ? `
            <div class="ul-nl-zone ul-nl-zone-less">⬅ less than ½</div>
            <div class="ul-nl-zone ul-nl-zone-more">more than ½ ➡</div>` : ''}
            ${points}
        </div>
    </div>`;
}

// A number line that spans negatives as well as positives — the one picture that
// makes "which of these is smaller?" obvious once negatives are in play.
function signLineVisualHTML(v) {
    const min = v.min, max = v.max, step = v.step || 1;
    const pos = value => ((value - min) / (max - min)) * 100;
    let ticks = '';
    // Rounded because repeatedly adding a step like 0.5 drifts off exact values.
    for (let t = min; t <= max + 1e-9; t += step) {
        const value = Math.round(t * 1e6) / 1e6;
        const isZero = value === 0;
        ticks += `<div class="ul-sl-tick ${isZero ? 'ul-sl-zero' : ''}" style="left:${pos(value)}%"><span>${value}</span></div>`;
    }
    const points = (v.points || []).map((p, i) => {
        const color = VISUAL_COLORS[p.color] || VISUAL_COLORS.purple;
        return `<div class="ul-sl-point ${i % 2 ? 'ul-sl-point-low' : ''}" style="left:${pos(p.v)}%">
                    <div class="ul-sl-label" style="border-color:${color}">${renderMath(p.label)}</div>
                    <div class="ul-sl-dot" style="background:${color}"></div>
                </div>`;
    }).join('');
    return `<div class="ul-sl" role="img" aria-label="Number line from ${min} to ${max}">
        <div class="ul-sl-track">
            ${v.zones === false ? '' : `
            <div class="ul-sl-zone ul-sl-zone-neg" style="width:${pos(0)}%">⬅ negative · smaller</div>
            <div class="ul-sl-zone ul-sl-zone-pos" style="left:${pos(0)}%">positive · bigger ➡</div>`}
            ${ticks}${points}
        </div>
    </div>`;
}

// The sign rules for +, −, × and ÷, as a grid of little "recipe" cards.
function rulesVisualHTML(v) {
    const cards = v.items.map(item => `
        <div class="ul-rule">
            <div class="ul-rule-expr">${renderMath(item.expr)}</div>
            <div class="ul-rule-arrow" aria-hidden="true">→</div>
            <div class="ul-rule-result ${item.result.trim() === '-' ? 'is-neg' : 'is-pos'}">${escHTML(item.result)}</div>
            ${item.note ? `<div class="ul-rule-note">${renderMath(item.note)}</div>` : ''}
        </div>`).join('');
    return `<div class="ul-rules">${cards}</div>`;
}

document.addEventListener('DOMContentLoaded', ulInit);
