/* =============================================
   Times Tables — the drill engine.

   Deliberately not the lesson engine. There is no lesson to read and no
   menu to pick from: you open a level and you are answering. A whole set of
   5-6 questions is on screen at once, the way a Kumon worksheet page is, so
   a child builds a rhythm instead of waiting for a new page after every fact.

   A level runs three passes, easiest first. The first is a ladder with rungs
   missing, running whichever way the unit needs: "skip" counts up in the table,
   which is where the chain gets into a child's head and the bridge to
   multiplication, since the 3rd rung IS 7 x 3; "back" counts down from the
   whole amount to 0, because dividing is taking away until nothing is left and
   the number of jumps is the answer. Then "pick" offers four options, which is
   recognition, and "type" offers nothing, which is recall.

   Progress lives in ulState.progress via progress.js, shared with the lesson
   engine, so a signed-in learner's drill carries between devices too.

   Routing:
     /units/grade3/times-tables           -> every level
     /units/grade3/times-tables/t7        -> level 7, first unfinished set
     /units/grade3/times-tables/t7#2      -> level 7, set 2
     /units/grade3/times-tables/t7#done   -> level 7 summary
   ============================================= */
'use strict';

const ttRoot = document.getElementById('ul-content');
const TT_FOCUS = typeof UNIT_FOCUS_SECTION !== 'undefined' ? UNIT_FOCUS_SECTION : null;

// Answers typed or picked in the set currently on screen, before it's checked.
let ttDraft = {};
let ttChecked = false;
// Which page we're on. Held rather than recomputed: once a page is checked its
// questions count as answered, so asking for "the first unfinished page" again
// would skip to the next one mid-render and score the wrong set.
let ttCurrentSet = null;

function ttEsc(str) {
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

function ttQuestions(levelId) {
    return UNIT_QUESTIONS.filter(q => q.section === levelId);
}

function ttSets(levelId) {
    const sets = new Map();
    ttQuestions(levelId).forEach(q => {
        if (!sets.has(q.set)) sets.set(q.set, []);
        sets.get(q.set).push(q);
    });
    return [...sets.entries()].sort((a, b) => a[0] - b[0]).map(([number, questions]) => ({
        number, questions, mode: questions[0].mode,
    }));
}

function ttLevelStats(levelId) {
    const questions = ttQuestions(levelId);
    const answered = questions.filter(q => ulState.progress[q.id]);
    const correct = questions.filter(q => ulState.progress[q.id] === 'correct');
    return {
        total: questions.length,
        answered: answered.length,
        correct: correct.length,
        done: answered.length === questions.length,
        sets: ttSets(levelId),
    };
}

/** The set to drop someone into: the first with an unanswered question. */
function ttFirstUnfinishedSet(levelId) {
    const sets = ttSets(levelId);
    const open = sets.find(s => s.questions.some(q => !ulState.progress[q.id]));
    return open ? open.number : sets[sets.length - 1].number;
}

// ===== every level =====

/** Levels bundled under their group heading, in the order they are declared.
 *  Thirteen level tiles in one grid is a wall; the heading says what they are
 *  and leaves an obvious seam for a second group to land under later. */
function ttGroupedLevels() {
    const groups = [];
    UNIT_SECTIONS.forEach(level => {
        const name = level.group || null;
        if (!groups.length || groups[groups.length - 1].name !== name) {
            groups.push({ name, emoji: level.group_emoji, levels: [] });
        }
        groups[groups.length - 1].levels.push(level);
    });
    return groups;
}

function ttOverviewHTML() {
    const total = UNIT_QUESTIONS.length;
    const answered = UNIT_QUESTIONS.filter(q => ulState.progress[q.id]).length;
    const levelsDone = UNIT_SECTIONS.filter(l => ttLevelStats(l.id).done).length;

    // One tile per group, listing its levels as links. A grid of thirteen
    // tiles buried what the group actually was; a single named tile says it
    // once and lets the levels be a list you can scan.
    const tiles = ttGroupedLevels().map(group => {
        const items = group.levels.map(level => {
            const st = ttLevelStats(level.id);
            const state = st.done ? 'is-done' : st.answered ? 'is-going' : '';
            const mark = st.done ? '✓' : st.answered ? '·' : '';
            return `
                <li class="${state}">
                    <a href="${UNIT_BASE_URL}/${level.id}">
                        <span class="tt-item-emoji" aria-hidden="true">${ttEsc(level.emoji)}</span>
                        <span class="tt-item-title">${ttEsc(level.title)}</span>
                        <span class="tt-item-meta">${st.sets.length} pages · ${st.total} questions</span>
                        <span class="tt-item-mark" aria-hidden="true">${mark}</span>
                    </a>
                </li>`;
        }).join('');

        const groupTotal = group.levels.reduce((n, l) => n + ttLevelStats(l.id).total, 0);
        const groupDone = group.levels.reduce((n, l) => n + ttLevelStats(l.id).answered, 0);
        const pct = groupTotal ? Math.round((groupDone / groupTotal) * 100) : 0;

        return `
            <section class="tt-tile">
                <header class="tt-tile-head">
                    <span class="tt-tile-emoji" aria-hidden="true">${ttEsc(group.emoji || '✖️')}</span>
                    <span>
                        <span class="tt-tile-kicker">Unit</span>
                        <h2 class="tt-tile-title">${ttEsc(group.name || UNIT_TITLE)}</h2>
                    </span>
                </header>
                <div class="tt-tile-meta">
                    ${group.levels.length} levels · ${groupTotal} questions
                    <span class="tt-bar"><span class="tt-bar-fill" style="width:${pct}%"></span></span>
                </div>
                <ol class="tt-item-list">${items}</ol>
            </section>`;
    }).join('');

    return `
        <div class="tt-summary">
            <div class="tt-stat"><b>${UNIT_SECTIONS.length}</b><span>levels</span></div>
            <div class="tt-stat"><b>${total}</b><span>questions</span></div>
            <div class="tt-stat"><b>${answered}</b><span>answered</span></div>
            <div class="tt-stat"><b>${levelsDone}</b><span>levels finished</span></div>
        </div>
        <div class="tt-tiles">${tiles}</div>`;
}

// ===== one set of questions =====

function ttQuestionHTML(q, index) {
    const solved = ulState.progress[q.id];
    const draft = ttDraft[q.id];
    const marked = ttChecked && draft !== undefined;
    const right = marked && ttIsRight(q, draft);
    const mark = !marked ? '' : right ? 'tt-q-right' : 'tt-q-wrong';

    let input;
    if (q.mode === 'pick') {
        input = `<div class="tt-options" role="group" aria-label="${ttEsc(q.prompt)}">` +
            q.options.map(option => {
                const chosen = draft === option;
                const classes = ['tt-option'];
                if (chosen) classes.push('is-chosen');
                if (marked && chosen && !right) classes.push('is-wrong');
                if (marked && option === q.answer.choice) classes.push('is-answer');
                return `<button type="button" class="${classes.join(' ')}"
                          data-qid="${ttEsc(q.id)}" data-value="${ttEsc(option)}"
                          ${ttChecked ? 'disabled' : ''}>${ttEsc(option)}</button>`;
            }).join('') + `</div>`;
    } else {
        input = `<input class="tt-input" type="text" inputmode="numeric"
                    aria-label="${ttEsc(q.prompt)}" data-qid="${ttEsc(q.id)}"
                    value="${draft === undefined ? '' : ttEsc(draft)}"
                    ${ttChecked ? 'disabled' : ''} autocomplete="off">`;
    }

    // Only a wrong answer gets the strategy: it's the one moment a child is
    // actually asking how the fact works.
    const help = marked && !right
        ? `<div class="tt-q-help"><b>${ttEsc(q.answer.display)}</b> — ${ttEsc(q.steps)}</div>`
        : '';

    return `
        <li class="tt-q ${mark}" data-qid="${ttEsc(q.id)}">
            <span class="tt-q-num">${index + 1}</span>
            <span class="tt-q-prompt">${ttEsc(q.prompt)}</span>
            ${input}
            <span class="tt-q-mark" aria-hidden="true">${marked ? (right ? '✓' : '✗') : (solved === 'correct' ? '·' : '')}</span>
            ${help}
        </li>`;
}

/** The ladder: every rung shown, the blank ones as inputs.
 *
 *  Drawn whole rather than as a list of separate questions, because seeing the
 *  chain is the point — a child reads along it to work out the next rung.
 *
 *  It runs in whichever direction the unit needs. Multiplication counts up in
 *  the table, which is how the chain gets learned. Division counts back from
 *  the whole amount to 0, because dividing is taking away until nothing is
 *  left, and the number of jumps is the answer. */
function ttChainHTML(level, set) {
    const ladder = level.ladder || {};
    const chain = ladder.chain || [];
    const back = ladder.mode === 'back';
    const byStep = new Map(set.questions.map(q => [q.step, q]));

    const rungs = chain.map((value, i) => {
        const step = i + 1;
        const q = byStep.get(step);
        if (!q) return `<span class="tt-rung is-given">${value}</span>`;

        const draft = ttDraft[q.id];
        const marked = ttChecked && draft !== undefined;
        const right = marked && ttIsRight(q, draft);
        const state = !marked ? '' : right ? ' is-right' : ' is-wrong';
        const reveal = marked && !right
            ? `<span class="tt-rung-answer">${ttEsc(q.answer.display)}</span>` : '';
        return `<span class="tt-rung is-blank${state}">
                    <input class="tt-input tt-rung-input" type="text" inputmode="numeric"
                           aria-label="${ttEsc(q.prompt)}" data-qid="${ttEsc(q.id)}"
                           value="${draft === undefined ? '' : ttEsc(draft)}"
                           ${ttChecked ? 'disabled' : ''} autocomplete="off">
                    ${reveal}
                </span>`;
    }).join(back
        ? `<span class="tt-rung-link is-minus" aria-hidden="true">−${ladder.step}</span>`
        : '<span class="tt-rung-link" aria-hidden="true">→</span>');

    const intro = back
        ? `Start at <b>${chain[0]}</b> and keep taking away <b>${ladder.step}</b> until
           you reach 0. Fill in the gaps — and count the jumps, because that is the
           answer to ${chain[0]} ÷ ${ladder.step}.`
        : `Start at <b>${ladder.step}</b> and keep adding <b>${ladder.step}</b>.
           Fill in the gaps.`;

    return `
        <div class="tt-chain-intro">${intro}</div>
        <div class="tt-chain">${rungs}</div>`;
}

function ttIsRight(q, value) {
    if (q.mode === 'pick') return value === q.answer.choice;
    const typed = String(value === undefined ? '' : value).trim();
    return /^\d+$/.test(typed) && parseInt(typed, 10) === q.answer.value;
}

function ttSetHTML(level, set, sets) {
    const position = sets.findIndex(s => s.number === set.number);
    const isLast = position === sets.length - 1;
    const answeredAll = set.questions.every(q => ttDraft[q.id] !== undefined && ttDraft[q.id] !== '');
    const score = ttChecked
        ? set.questions.filter(q => ttIsRight(q, ttDraft[q.id])).length : 0;

    const dots = sets.map(s => {
        const done = s.questions.every(q => ulState.progress[q.id]);
        const here = s.number === set.number;
        return `<a class="tt-dot${here ? ' is-here' : ''}${done ? ' is-done' : ''}"
                   href="#${s.number}" aria-label="Page ${s.number}"
                   ${here ? 'aria-current="true"' : ''}>${s.number}</a>`;
    }).join('');

    const step = (level.ladder || {}).step;
    const banner = set.mode === 'skip'
        ? `<div class="tt-mode tt-mode-skip">🪜 Skip counting — count up in ${step}s</div>`
        : set.mode === 'back'
        ? `<div class="tt-mode tt-mode-back">➖ Repeated subtraction — take away ${step} each time</div>`
        : set.mode === 'pick'
        ? `<div class="tt-mode tt-mode-pick">👆 Pick the right answer</div>`
        : `<div class="tt-mode tt-mode-type">⌨️ Type the answer — no options this time</div>`;

    const body = (set.mode === 'skip' || set.mode === 'back')
        ? ttChainHTML(level, set)
        : `<ol class="tt-list">${set.questions.map(ttQuestionHTML).join('')}</ol>`;

    const footer = ttChecked
        ? `<div class="tt-result ${score === set.questions.length ? 'is-perfect' : ''}">
               ${score === set.questions.length
                   ? '<span class="tt-cheer" aria-hidden="true">🎉</span>' : ''}
               <span class="tt-score">${score} / ${set.questions.length}</span>
               <span class="tt-result-msg">${score === set.questions.length
                   ? 'Perfect page!' : 'Look at the ones marked ✗, then carry on.'}</span>
               <span class="tt-result-actions">
                   <button type="button" class="tt-btn tt-btn-ghost" id="tt-redo">🔄 Try this page again</button>
                   ${isLast
                       ? `<a class="tt-btn" href="#done">See level summary →</a>`
                       : `<a class="tt-btn" href="#${sets[position + 1].number}">Next page →</a>`}
               </span>
           </div>`
        : `<div class="tt-check-row">
               <button type="button" class="tt-btn" id="tt-check" ${answeredAll ? '' : 'disabled'}>
                   Check my answers
               </button>
               <span class="tt-check-hint">${answeredAll ? 'All done — check them!' : 'Answer all of them, then check.'}</span>
           </div>`;

    return `
        <div class="tt-setbar">
            <a class="tt-back" href="${UNIT_BASE_URL}">← All levels</a>
            <span class="tt-pages">${dots}</span>
        </div>
        ${banner}
        ${body}
        ${footer}`;
}

// ===== level summary =====

function ttDoneHTML(level) {
    const st = ttLevelStats(level.id);
    const pct = st.total ? Math.round((st.correct / st.total) * 100) : 0;
    const index = UNIT_SECTIONS.findIndex(l => l.id === level.id);
    const next = UNIT_SECTIONS[index + 1];
    const emoji = pct === 100 ? '🏆' : pct >= 80 ? '🌟' : '💪';

    const weak = ttQuestions(level.id)
        .filter(q => ulState.progress[q.id] && ulState.progress[q.id] !== 'correct')
        .map(q => q.prompt.replace(' = ?', ''));
    const unique = [...new Set(weak)];

    return `
        <div class="tt-done">
            <div class="tt-done-emoji">${emoji}</div>
            <h2>${ttEsc(level.title)}</h2>
            <p class="tt-done-score">${st.correct} of ${st.total} right${st.answered < st.total
                ? ` · ${st.total - st.answered} still to do` : ''}</p>
            ${unique.length ? `<div class="tt-done-weak">
                <b>Worth another lap:</b> ${unique.slice(0, 12).map(ttEsc).join(' · ')}
            </div>` : ''}
            <div class="tt-done-actions">
                <button type="button" class="tt-btn tt-btn-ghost" id="tt-restart">🔄 Start this level over</button>
                ${next ? `<a class="tt-btn" href="${UNIT_BASE_URL}/${next.id}">Next: ${ttEsc(next.title)} →</a>`
                       : `<a class="tt-btn" href="${UNIT_BASE_URL}">All levels →</a>`}
            </div>
        </div>`;
}

// ===== wiring =====

function ttWire(level, set, sets) {
    ttRoot.querySelectorAll('.tt-option').forEach(button => {
        button.addEventListener('click', () => {
            ttDraft[button.dataset.qid] = button.dataset.value;
            ttRender();
        });
    });

    ttRoot.querySelectorAll('.tt-input').forEach(input => {
        input.addEventListener('input', () => {
            // Keep digits only: a stray letter would just fail the check later.
            input.value = input.value.replace(/[^\d]/g, '');
            ttDraft[input.dataset.qid] = input.value;
            const check = document.getElementById('tt-check');
            const ready = set.questions.every(q => (ttDraft[q.id] || '') !== '');
            if (check) check.disabled = !ready;
        });
        // Enter moves to the next box, so a whole page can be typed without
        // reaching for the mouse.
        input.addEventListener('keydown', event => {
            if (event.key !== 'Enter') return;
            event.preventDefault();
            const boxes = [...ttRoot.querySelectorAll('.tt-input')];
            const next = boxes[boxes.indexOf(input) + 1];
            if (next) next.focus();
            else document.getElementById('tt-check')?.click();
        });
    });

    const check = document.getElementById('tt-check');
    if (check) check.addEventListener('click', () => {
        const verdicts = {};
        set.questions.forEach(q => {
            verdicts[q.id] = ttIsRight(q, ttDraft[q.id]) ? 'correct' : 'wrong';
            ulState.progress[q.id] = verdicts[q.id];
        });
        ulSaveProgress(verdicts);
        ttChecked = true;
        ttRender();
        ttRoot.querySelector('.tt-result')?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        if (set.questions.every(q => ttIsRight(q, ttDraft[q.id]))) ttCelebrate();
    });

    document.getElementById('tt-redo')?.addEventListener('click', () => {
        ulClearProgress(set.questions.map(q => q.id));
        set.questions.forEach(q => { delete ulState.progress[q.id]; });
        ulWriteLocal();
        ttDraft = {};
        ttChecked = false;
        ttRender();
    });

    document.getElementById('tt-restart')?.addEventListener('click', () => {
        if (!window.confirm(`Start ${level.title} over? Your answers for this level will be cleared.`)) return;
        const ids = ttQuestions(level.id).map(q => q.id);
        ulClearProgress(ids);
        ids.forEach(id => { delete ulState.progress[id]; });
        ulWriteLocal();
        ttDraft = {};
        ttChecked = false;
        location.hash = '';
        ttRender();
    });
}

const TT_CONFETTI_COLOURS = ['#6C63FF', '#4ECDC4', '#FF6B6B', '#FFE66D', '#FF9F43', '#10AC84'];

/** A short burst of confetti over a clean page.
 *
 *  Built from plain spans rather than a library: it runs once, lasts a second
 *  and never needs to know anything about the page, so a canvas and a
 *  dependency would both be more machinery than the moment is worth.
 *
 *  Skipped entirely for anyone who asked for reduced motion — they still get
 *  the badge and the score, which is where the actual information is. */
function ttCelebrate() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const anchor = ttRoot.querySelector('.tt-result');
    if (!anchor) return;
    const box = anchor.getBoundingClientRect();
    const originX = box.left + box.width / 2;
    const originY = box.top + box.height / 2;

    const layer = document.createElement('div');
    layer.className = 'tt-confetti';

    for (let i = 0; i < 26; i++) {
        const piece = document.createElement('i');
        // Fan the pieces upward and out, then let them fall past the anchor.
        const angle = (-160 + Math.random() * 140) * (Math.PI / 180);
        const reach = 90 + Math.random() * 160;
        piece.style.left = `${originX}px`;
        piece.style.top = `${originY}px`;
        piece.style.setProperty('--dx', `${Math.cos(angle) * reach}px`);
        piece.style.setProperty('--up', `${Math.sin(angle) * reach}px`);
        piece.style.setProperty('--dy', `${140 + Math.random() * 180}px`);
        piece.style.setProperty('--rot', `${-540 + Math.random() * 1080}deg`);
        piece.style.setProperty('--delay', `${Math.random() * 140}ms`);
        piece.style.background = TT_CONFETTI_COLOURS[i % TT_CONFETTI_COLOURS.length];
        if (i % 3 === 0) piece.classList.add('is-round');
        layer.appendChild(piece);
    }

    document.body.appendChild(layer);
    setTimeout(() => layer.remove(), 1600);
}

function ttRender() {
    if (!TT_FOCUS) {
        ttRoot.innerHTML = ttOverviewHTML();
        return;
    }

    const level = UNIT_SECTIONS.find(l => l.id === TT_FOCUS);
    if (!level) { ttRoot.innerHTML = ttOverviewHTML(); return; }

    const sets = ttSets(level.id);
    const hash = location.hash.replace('#', '');

    if (hash === 'done') {
        ttRoot.innerHTML = ttDoneHTML(level);
        ttWire(level, null, sets);
        return;
    }

    const wanted = /^\d+$/.test(hash) ? parseInt(hash, 10)
        : ttCurrentSet !== null ? ttCurrentSet
        : ttFirstUnfinishedSet(level.id);
    const set = sets.find(s => s.number === wanted) || sets[0];
    ttCurrentSet = set.number;
    ttRoot.innerHTML = ttSetHTML(level, set, sets);
    ttWire(level, set, sets);
    const first = ttRoot.querySelector('.tt-input');
    if (first && window.matchMedia('(pointer: fine)').matches) first.focus({ preventScroll: true });
}

window.addEventListener('hashchange', () => {
    // A new page means a clean slate; the previous page's answers are saved.
    ttDraft = {};
    ttChecked = false;
    ttCurrentSet = null;   // the hash decides now
    ttRender();
});

ulLoadProgress();
ttRender();
