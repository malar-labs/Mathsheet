/* =============================================
   Saved progress — shared by every unit engine.

   Two layers. localStorage always, so the app works signed out, offline, and
   with no account backend configured at all. The server on top of that, only
   when someone is signed in, so their progress follows them to another device.
   The server's copy is injected into the page as UNIT_PROGRESS, so the first
   paint already shows the right bars instead of jumping after a fetch.

   Loaded before the engine, which reads and writes ulState.progress.
   ============================================= */
'use strict';

const ulState = {
    activeSection: null,
    page: 'lesson',          // 'lesson', a 0-based page index, or 'done'
    questionsBySection: {},
    pagesBySection: {},      // { [sectionId]: [{ key, questions }] } — built on first use
    progress: {},            // { [questionId]: 'correct' | 'close' | 'wrong' }
    lastResults: {},         // { [questionId]: { qid, verdict, message, picked, fresh } }
    streak: 0,               // correct answers in a row during this visit

    // Kept so that checking one question never throws away what has been typed
    // into another on the same page — every render reads its boxes from here.
    stepState: {},           // { [questionId]: ... } — shape lives in ulStepState()
    draft: {},               // { [questionId]: whatever is half-typed in the box }
};

// ===== progress persistence =====
// Two layers. localStorage always, so the app works signed out, offline, and
// with no account backend configured at all. The server on top of that, only
// when someone is signed in, so their progress follows them to another device.
// The server's copy is injected into the page as UNIT_PROGRESS, so the first
// paint already shows the right bars instead of jumping after a fetch.

const UL_VERDICT_RANK = { wrong: 1, close: 2, correct: 3 };

function ulProgressKey() { return `mathsheet_unit_progress_${UNIT_KEY}`; }

function ulSignedIn() { return typeof UL_LEARNER !== 'undefined' && !!UL_LEARNER; }

function ulWriteLocal() {
    try {
        localStorage.setItem(ulProgressKey(), JSON.stringify(ulState.progress));
    } catch (e) { /* private browsing / storage disabled — progress just won't persist */ }
}

function ulLoadProgress() {
    let local = {};
    try {
        const raw = localStorage.getItem(ulProgressKey());
        local = raw ? JSON.parse(raw) : {};
    } catch (e) { local = {}; }

    const server = (typeof UNIT_PROGRESS !== 'undefined' && UNIT_PROGRESS) || {};

    // Best verdict wins rather than last write: a learner who got a question
    // right on the tablet shouldn't lose the tick because they fumbled it on
    // the laptop afterwards.
    const merged = Object.assign({}, server);
    const unsynced = {};
    Object.keys(local).forEach(qid => {
        const verdict = local[qid];
        if (!UL_VERDICT_RANK[verdict]) return;
        if (UL_VERDICT_RANK[verdict] > (UL_VERDICT_RANK[merged[qid]] || 0)) merged[qid] = verdict;
        if (merged[qid] !== server[qid]) unsynced[qid] = merged[qid];
    });

    ulState.progress = merged;
    ulWriteLocal();

    // Anything answered before signing in, or while the network was down, gets
    // adopted into the account on the next load.
    if (ulSignedIn() && Object.keys(unsynced).length) ulPushProgress(unsynced);
}

let ulSyncTimer = null;
let ulPendingSync = {};

function ulSaveProgress(changed) {
    ulWriteLocal();
    if (!ulSignedIn()) return;
    Object.assign(ulPendingSync, changed || ulState.progress);
    clearTimeout(ulSyncTimer);
    ulSyncTimer = setTimeout(ulFlushProgress, 1200);
}

function ulFlushProgress() {
    const batch = ulPendingSync;
    ulPendingSync = {};
    if (Object.keys(batch).length) ulPushProgress(batch);
}

async function ulPushProgress(verdicts) {
    try {
        await fetch('/api/progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ unit_key: UNIT_KEY, verdicts }),
        });
    } catch (e) {
        // Offline, or the server blinked. The answers are safe in localStorage
        // and get merged upward the next time this page loads.
        Object.assign(ulPendingSync, verdicts);
    }
}

async function ulClearProgress(questionIds) {
    questionIds.forEach(id => { delete ulPendingSync[id]; });
    if (!ulSignedIn() || !questionIds.length) return;
    try {
        await fetch('/api/progress/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ unit_key: UNIT_KEY, question_ids: questionIds }),
        });
    } catch (e) { /* cleared locally; a failed clear reappears on the next load */ }
}

// A pending sync would be cancelled along with the page, so hand the last few
// answers to the browser to deliver after we're gone.
window.addEventListener('pagehide', () => {
    if (!ulSignedIn() || !Object.keys(ulPendingSync).length) return;
    const body = JSON.stringify({ unit_key: UNIT_KEY, verdicts: ulPendingSync });
    ulPendingSync = {};
    try {
        navigator.sendBeacon('/api/progress', new Blob([body], { type: 'application/json' }));
    } catch (e) { /* nothing more we can do at this point */ }
});
