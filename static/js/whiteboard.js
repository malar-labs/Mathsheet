/* =============================================
   Live whiteboard

   One board shared by a teacher and a learner. Every line is a "stroke":
   a list of points in board units (the board is always 1000 units wide, so a
   line lands in the same place on an iPad and on a laptop). Strokes travel
   between browsers over a Supabase Realtime broadcast channel; nothing is
   stored on a server. Each browser also keeps its own copy in localStorage, so
   a reload doesn't wipe the board.

   Input:
     pen    (Apple Pencil, stylus)  always draws, with pressure
     mouse                          always draws
     touch  (finger)                draws, or scrolls the page once a pen has
                                    been used — so a resting palm never leaves
                                    marks. The 👆 button switches it by hand.

   Set by the template: WB_ROLE, WB_ROOM, WB_NAME, WB_STUDENT, WB_REALTIME,
   WB_START_PROBLEM.
   ============================================= */
'use strict';

(function () {
    const W = 1000;               // board width in board units
    const START_HEIGHT = 1400;    // about two iPad screens
    const GROW_BY = 700;
    const SEND_EVERY_MS = 40;     // points are batched, ~25 messages a second
    const STATE_CHUNK = 40;       // strokes per message when catching someone up
    const IS_TEACHER = WB_ROLE === 'teacher';

    const canvas = document.getElementById('wb-canvas');
    const stage = document.getElementById('wb-stage');
    const ctx = canvas.getContext('2d');
    const statusEl = document.getElementById('wb-status');
    const problemEl = document.getElementById('wb-problem');

    const myId = Math.random().toString(36).slice(2, 10);
    const strokes = new Map();       // id -> stroke, in drawing order
    const removed = new Set();       // ids erased here, so a late catch-up can't bring them back
    const myStack = [];              // my own stroke ids, for undo
    let height = START_HEIGHT;
    let problem = '';
    let clearedAt = 0;

    let tool = 'pen';
    let color = '#1f2a44';
    let size = 3.5;
    let penSeen = false;
    let fingerScrolls = false;

    // ===================== saving in this browser =====================
    const storeKey = 'wb:' + WB_ROOM;
    let saveTimer = null;

    function saveLocal() {
        clearTimeout(saveTimer);
        saveTimer = setTimeout(() => {
            try {
                localStorage.setItem(storeKey, JSON.stringify({
                    strokes: [...strokes.values()].filter(s => s.done !== false),
                    height, problem, clearedAt,
                }));
            } catch (e) { /* private mode or full: the board still works */ }
        }, 400);
    }

    function loadLocal() {
        try {
            const saved = JSON.parse(localStorage.getItem(storeKey) || 'null');
            if (!saved) return;
            (saved.strokes || []).forEach(s => { s.done = true; strokes.set(s.id, s); });
            height = Math.max(START_HEIGHT, saved.height || 0);
            problem = saved.problem || '';
            clearedAt = saved.clearedAt || 0;
        } catch (e) { /* ignore a damaged copy */ }
    }

    // ===================== drawing =====================
    let scale = 1;
    let redrawQueued = false;

    function layout() {
        const cssWidth = canvas.clientWidth || stage.clientWidth;
        scale = cssWidth / W;
        const dpr = Math.min(window.devicePixelRatio || 1, 3);
        canvas.style.height = Math.round(height * scale) + 'px';
        canvas.width = Math.round(cssWidth * dpr);
        canvas.height = Math.round(height * scale * dpr);
        canvas.style.backgroundSize = (32 * scale) + 'px ' + (32 * scale) + 'px';
        ctx.setTransform(dpr * scale, 0, 0, dpr * scale, 0, 0);
        redraw();
    }

    function queueRedraw() {
        if (redrawQueued) return;
        redrawQueued = true;
        requestAnimationFrame(() => { redrawQueued = false; redraw(); });
    }

    function penWidth(s, p) {
        return s.size * (0.55 + (p == null ? 0.5 : p) * 0.9);
    }

    function drawStroke(c, s) {
        const pts = s.pts;
        if (!pts.length) return;
        c.lineCap = 'round';
        c.lineJoin = 'round';
        c.strokeStyle = s.color;
        c.fillStyle = s.color;

        if (s.tool === 'hl') {
            // One path, so overlapping parts of the same line don't get darker.
            c.globalAlpha = 0.3;
            c.lineWidth = s.size * 5;
            c.beginPath();
            c.moveTo(pts[0][0], pts[0][1]);
            for (let i = 1; i < pts.length; i++) c.lineTo(pts[i][0], pts[i][1]);
            if (pts.length === 1) c.lineTo(pts[0][0] + 0.1, pts[0][1]);
            c.stroke();
            c.globalAlpha = 1;
            return;
        }

        if (pts.length === 1) {
            c.beginPath();
            c.arc(pts[0][0], pts[0][1], penWidth(s, pts[0][2]) / 2, 0, Math.PI * 2);
            c.fill();
            return;
        }
        // Smooth curve through the midpoints; width follows the pen pressure.
        for (let i = 1; i < pts.length; i++) {
            const a = pts[i - 1], b = pts[i];
            const prev = pts[i - 2] || a;
            const startX = (prev[0] + a[0]) / 2, startY = (prev[1] + a[1]) / 2;
            const endX = (a[0] + b[0]) / 2, endY = (a[1] + b[1]) / 2;
            c.lineWidth = penWidth(s, a[2]);
            c.beginPath();
            c.moveTo(i === 1 ? a[0] : startX, i === 1 ? a[1] : startY);
            c.quadraticCurveTo(a[0], a[1], endX, endY);
            if (i === pts.length - 1) c.lineTo(b[0], b[1]);
            c.stroke();
        }
    }

    function redraw() {
        ctx.save();
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.restore();
        for (const s of strokes.values()) drawStroke(ctx, s);
    }

    function setHeight(h, broadcast) {
        if (h <= height) return;
        height = Math.min(h, 20000);
        layout();
        saveLocal();
        if (broadcast) send({ t: 'h', h: height });
    }

    // ===================== the problem strip =====================
    function escHTML(s) {
        return String(s).replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
    }

    function fracHTML(n, d) {
        return `<span class="wb-frac"><span>${n}</span><span>${d}</span></span>`;
    }

    // "2 1/2 ÷ 5/6" -> the fractions drawn stacked, the way they're written by hand.
    function renderProblem(text) {
        let html = escHTML(text).replace(/\s\*\s|\s[xX]\s/g, ' × ');
        html = html.replace(/(\d+)\s+(\d+)\/(\d+)|(\d+)\/(\d+)/g, (m, w, n1, d1, n2, d2) =>
            w ? `<span class="wb-whole">${w}</span>${fracHTML(n1, d1)}` : fracHTML(n2, d2));
        return html;
    }

    function setProblem(text, broadcast) {
        problem = (text || '').trim().slice(0, 300);
        problemEl.hidden = !problem;
        problemEl.innerHTML = problem ? renderProblem(problem) : '';
        const input = document.getElementById('wb-problem-input');
        if (input && document.activeElement !== input) input.value = problem;
        saveLocal();
        if (broadcast) send({ t: 'prob', text: problem });
    }

    // ===================== changing the board =====================
    function newStroke(fields) {
        return {
            id: fields.id,
            by: fields.by,
            tool: fields.tool === 'hl' ? 'hl' : 'pen',
            color: /^#[0-9a-f]{6}$/i.test(fields.color || '') ? fields.color : '#1f2a44',
            size: Math.min(Math.max(Number(fields.size) || 3.5, 1), 12),
            t: fields.t || Date.now(),
            pts: [],
            done: false,
        };
    }

    function cleanPoints(pts) {
        if (!Array.isArray(pts)) return [];
        return pts.filter(p => Array.isArray(p) && isFinite(p[0]) && isFinite(p[1]))
                  .map(p => [+p[0], +p[1], p[2] == null ? 0.5 : +p[2]]);
    }

    function removeStrokes(ids, broadcast) {
        let changed = false;
        ids.forEach(id => {
            removed.add(id);
            if (strokes.delete(id)) changed = true;
        });
        if (!changed) return;
        queueRedraw();
        saveLocal();
        if (broadcast) send({ t: 'rm', ids });
    }

    function clearBoard(broadcast) {
        strokes.forEach((s, id) => removed.add(id));
        strokes.clear();
        myStack.length = 0;
        clearedAt = Date.now();
        queueRedraw();
        saveLocal();
        if (broadcast) send({ t: 'clear', at: clearedAt });
    }

    // Only the teacher can rub out someone else's work.
    function mayErase(s) {
        return IS_TEACHER || s.by === myId;
    }

    function distToSegment(px, py, a, b) {
        const dx = b[0] - a[0], dy = b[1] - a[1];
        const len = dx * dx + dy * dy;
        let t = len ? ((px - a[0]) * dx + (py - a[1]) * dy) / len : 0;
        t = Math.max(0, Math.min(1, t));
        const x = a[0] + t * dx, y = a[1] + t * dy;
        return Math.hypot(px - x, py - y);
    }

    function eraseAt(x, y) {
        const hits = [];
        for (const s of strokes.values()) {
            if (!mayErase(s)) continue;
            const reach = 10 + (s.tool === 'hl' ? s.size * 2.5 : s.size);
            const pts = s.pts;
            for (let i = 0; i < pts.length; i++) {
                const d = distToSegment(x, y, pts[i], pts[i + 1] || pts[i]);
                if (d <= reach) { hits.push(s.id); break; }
            }
        }
        if (hits.length) removeStrokes(hits, true);
    }

    function undo() {
        while (myStack.length) {
            const id = myStack.pop();
            if (strokes.has(id)) { removeStrokes([id], true); return; }
        }
    }

    // ===================== pointer input =====================
    let drawing = null;          // {pointerId, stroke}
    let scrolling = null;        // {pointerId, lastY}
    const outgoing = new Map();  // stroke id -> points not yet sent

    function boardPoint(e) {
        const r = canvas.getBoundingClientRect();
        const k = W / r.width;
        const x = Math.round((e.clientX - r.left) * k * 10) / 10;
        const y = Math.round((e.clientY - r.top) * k * 10) / 10;
        const p = e.pointerType === 'pen' && e.pressure > 0 ? Math.round(e.pressure * 100) / 100 : 0.5;
        return [x, y, p];
    }

    function notePen() {
        if (penSeen) return;
        penSeen = true;
        setFingerScrolls(true);
    }

    canvas.addEventListener('pointerdown', e => {
        if (e.pointerType === 'pen') notePen();
        if (e.pointerType === 'touch' && fingerScrolls) {
            if (!scrolling) scrolling = { pointerId: e.pointerId, lastY: e.clientY };
            return;
        }
        if (drawing) return;               // one line at a time
        if (e.button > 0) return;          // right-click etc.
        e.preventDefault();
        try { canvas.setPointerCapture(e.pointerId); } catch (err) { /* synthetic or already gone */ }
        const pt = boardPoint(e);

        if (tool === 'eraser') {
            drawing = { pointerId: e.pointerId, erasing: true };
            eraseAt(pt[0], pt[1]);
            return;
        }
        const s = newStroke({ id: myId + '-' + Date.now().toString(36) + Math.random().toString(36).slice(2, 5),
                              by: myId, tool, color, size });
        s.pts.push(pt);
        strokes.set(s.id, s);
        drawing = { pointerId: e.pointerId, stroke: s };
        outgoing.set(s.id, [pt]);
        queueRedraw();
    });

    canvas.addEventListener('pointermove', e => {
        if (scrolling && e.pointerId === scrolling.pointerId) {
            window.scrollBy(0, scrolling.lastY - e.clientY);
            scrolling.lastY = e.clientY;
            return;
        }
        if (!drawing || e.pointerId !== drawing.pointerId) return;
        e.preventDefault();
        const events = e.getCoalescedEvents ? e.getCoalescedEvents() : [e];
        const list = events.length ? events : [e];

        if (drawing.erasing) {
            list.forEach(ev => { const p = boardPoint(ev); eraseAt(p[0], p[1]); });
            return;
        }
        const s = drawing.stroke;
        const queue = outgoing.get(s.id) || [];
        list.forEach(ev => {
            const pt = boardPoint(ev);
            const last = s.pts[s.pts.length - 1];
            if (Math.hypot(pt[0] - last[0], pt[1] - last[1]) < 0.8) return;
            s.pts.push(pt);
            queue.push(pt);
        });
        outgoing.set(s.id, queue);
        const lastPt = s.pts[s.pts.length - 1];
        if (lastPt[1] > height - 120) setHeight(height + GROW_BY, true);
        queueRedraw();
    });

    function finish(e) {
        if (scrolling && e.pointerId === scrolling.pointerId) { scrolling = null; return; }
        if (!drawing || e.pointerId !== drawing.pointerId) return;
        const s = drawing.stroke;
        drawing = null;
        if (!s) return;          // an eraser drag
        s.done = true;
        myStack.push(s.id);
        flush();
        send({ t: 'end', id: s.id });
        saveLocal();
    }
    canvas.addEventListener('pointerup', finish);
    canvas.addEventListener('pointercancel', finish);
    canvas.addEventListener('lostpointercapture', finish);
    canvas.addEventListener('contextmenu', e => e.preventDefault());

    function flush() {
        if (!outgoing.size) return;
        outgoing.forEach((pts, id) => {
            const s = strokes.get(id);
            if (!s || !pts.length) return;
            send({ t: 'pts', id, by: s.by, tool: s.tool, color: s.color, size: s.size, st: s.t, pts });
        });
        outgoing.clear();
    }
    setInterval(flush, SEND_EVERY_MS);

    // ===================== toolbar =====================
    function pick(selector, el) {
        document.querySelectorAll(selector).forEach(b => {
            const on = b === el;
            b.classList.toggle('is-active', on);
            b.setAttribute('aria-pressed', on ? 'true' : 'false');
        });
    }

    document.querySelectorAll('.wb-tool[data-tool]').forEach(b => b.addEventListener('click', () => {
        tool = b.dataset.tool;
        pick('.wb-tool[data-tool]', b);
        canvas.classList.toggle('is-erasing', tool === 'eraser');
    }));
    document.querySelectorAll('.wb-color').forEach(b => b.addEventListener('click', () => {
        color = b.dataset.color;
        pick('.wb-color', b);
        if (tool === 'eraser') document.querySelector('.wb-tool[data-tool="pen"]').click();
    }));
    document.querySelectorAll('.wb-size').forEach(b => b.addEventListener('click', () => {
        size = parseFloat(b.dataset.size);
        pick('.wb-size', b);
    }));

    function setFingerScrolls(on) {
        fingerScrolls = on;
        const btn = document.getElementById('wb-finger');
        btn.setAttribute('aria-pressed', on ? 'true' : 'false');
        btn.classList.toggle('is-active', on);
        document.getElementById('wb-finger-label').textContent = on ? 'Finger scrolls' : 'Finger draws';
    }
    document.getElementById('wb-finger').addEventListener('click', () => setFingerScrolls(!fingerScrolls));

    document.getElementById('wb-undo').addEventListener('click', undo);
    document.getElementById('wb-more').addEventListener('click', () => {
        setHeight(height + GROW_BY, true);
        window.scrollBy({ top: GROW_BY * scale * 0.8, behavior: 'smooth' });
    });
    document.addEventListener('keydown', e => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z' && !e.target.closest('input')) {
            e.preventDefault();
            undo();
        }
    });

    // Clearing wipes everyone's screen, so only the teacher has the button,
    // and it asks first.
    const clearBtn = document.getElementById('wb-clear');
    const confirmBox = document.getElementById('wb-confirm');
    if (!IS_TEACHER) clearBtn.hidden = true;
    clearBtn.addEventListener('click', () => { confirmBox.hidden = false; });
    document.getElementById('wb-confirm-no').addEventListener('click', () => { confirmBox.hidden = true; });
    document.getElementById('wb-confirm-yes').addEventListener('click', () => {
        confirmBox.hidden = true;
        clearBoard(true);
    });

    document.getElementById('wb-save').addEventListener('click', () => {
        const out = document.createElement('canvas');
        const k = 1.5;
        out.width = W * k;
        out.height = height * k;
        const c = out.getContext('2d');
        c.fillStyle = '#fff';
        c.fillRect(0, 0, out.width, out.height);
        c.scale(k, k);
        for (const s of strokes.values()) drawStroke(c, s);
        const a = document.createElement('a');
        const day = new Date().toISOString().slice(0, 10);
        a.download = `whiteboard-${(WB_STUDENT || 'class').replace(/\s+/g, '-')}-${day}.png`;
        a.href = out.toDataURL('image/png');
        document.body.appendChild(a);
        a.click();
        a.remove();
    });

    const problemForm = document.getElementById('wb-problem-form');
    if (problemForm) {
        problemForm.addEventListener('submit', e => {
            e.preventDefault();
            setProblem(document.getElementById('wb-problem-input').value, true);
        });
    }

    const shareInput = document.getElementById('wb-share-url');
    if (shareInput && shareInput.value.startsWith('/')) shareInput.value = location.origin + shareInput.value;

    const copyBtn = document.getElementById('wb-copy');
    if (copyBtn) {
        copyBtn.addEventListener('click', async () => {
            const input = document.getElementById('wb-share-url');
            try {
                await navigator.clipboard.writeText(input.value);
            } catch (e) {
                input.select();
                document.execCommand && document.execCommand('copy');
            }
            copyBtn.textContent = 'Copied!';
            setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1800);
        });
    }

    // ===================== live sharing =====================
    let channel = null;
    let live = false;

    function setStatus(text, kind) {
        statusEl.textContent = text;
        statusEl.classList.toggle('is-live', kind === 'live');
        statusEl.classList.toggle('is-off', kind === 'off');
    }

    function send(msg) {
        if (!channel || !live) return;
        msg.from = myId;
        channel.send({ type: 'broadcast', event: 'm', payload: msg });
    }

    function sendState() {
        const done = [...strokes.values()].filter(s => s.done !== false);
        send({ t: 'meta', h: height, prob: problem, clearedAt });
        for (let i = 0; i < done.length; i += STATE_CHUNK) {
            send({ t: 'state', strokes: done.slice(i, i + STATE_CHUNK) });
        }
    }

    function receive(m) {
        if (!m || m.from === myId) return;
        switch (m.t) {
        case 'pts': {
            if (removed.has(m.id) || (m.st && m.st < clearedAt)) return;
            let s = strokes.get(m.id);
            if (!s) {
                s = newStroke({ id: m.id, by: m.by, tool: m.tool, color: m.color, size: m.size, t: m.st });
                strokes.set(s.id, s);
            }
            s.pts.push(...cleanPoints(m.pts));
            queueRedraw();
            break;
        }
        case 'end': {
            const s = strokes.get(m.id);
            if (s) { s.done = true; saveLocal(); }
            break;
        }
        case 'rm':
            if (Array.isArray(m.ids)) removeStrokes(m.ids, false);
            break;
        case 'clear':
            clearBoard(false);
            break;
        case 'prob':
            setProblem(m.text, false);
            break;
        case 'h':
            setHeight(+m.h || 0, false);
            break;
        case 'hello':
            // Someone just arrived (or reloaded): hand them what's on the board.
            setTimeout(sendState, 150 + Math.random() * 300);
            break;
        case 'meta':
            if (m.clearedAt > clearedAt) clearBoard(false), clearedAt = m.clearedAt;
            setHeight(+m.h || 0, false);
            if (m.prob && !problem) setProblem(m.prob, false);
            break;
        case 'state':
            (m.strokes || []).forEach(raw => {
                if (!raw || strokes.has(raw.id) || removed.has(raw.id)) return;
                if (raw.t && raw.t < clearedAt) return;
                const s = newStroke(raw);
                s.pts = cleanPoints(raw.pts);
                s.done = true;
                strokes.set(s.id, s);
            });
            queueRedraw();
            saveLocal();
            break;
        }
    }

    function showPresence() {
        if (!channel) return;
        const people = Object.values(channel.presenceState()).flat();
        const others = people.filter(p => p.id !== myId);
        const who = others.map(p => p.name).filter(Boolean);
        if (IS_TEACHER) {
            setStatus(who.length ? `Live · ${who.join(', ')} is here` : `Live · waiting for ${WB_STUDENT || 'your student'}`, 'live');
        } else {
            const teacher = others.some(p => p.role === 'teacher');
            setStatus(teacher ? 'Live · your teacher is here' : 'Live · waiting for your teacher', 'live');
        }
    }

    function connect() {
        if (!WB_REALTIME || !window.supabase || !WB_ROOM) {
            setStatus(WB_REALTIME ? 'Live sharing unavailable' : 'This screen only', 'off');
            return;
        }
        const client = window.supabase.createClient(WB_REALTIME.url, WB_REALTIME.key, {
            auth: { persistSession: false, autoRefreshToken: false },
            realtime: { params: { eventsPerSecond: 40 } },
        });
        channel = client.channel('wb-' + WB_ROOM, {
            config: { broadcast: { self: false, ack: false }, presence: { key: myId } },
        });
        channel.on('broadcast', { event: 'm' }, ({ payload }) => receive(payload));
        channel.on('presence', { event: 'sync' }, showPresence);
        channel.subscribe(status => {
            if (status === 'SUBSCRIBED') {
                live = true;
                channel.track({ id: myId, name: WB_NAME, role: WB_ROLE });
                send({ t: 'hello' });
                showPresence();
            } else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT' || status === 'CLOSED') {
                live = false;
                setStatus('Reconnecting…', 'off');
            }
        });
    }

    // ===================== start =====================
    loadLocal();
    if (WB_START_PROBLEM) problem = WB_START_PROBLEM;
    setProblem(problem, false);
    layout();
    if (window.ResizeObserver) new ResizeObserver(() => layout()).observe(stage);
    else window.addEventListener('resize', layout);
    connect();
    if (IS_TEACHER && WB_START_PROBLEM) {
        // Sent once the channel is up, so a learner already waiting sees it.
        const wait = setInterval(() => { if (live) { clearInterval(wait); send({ t: 'prob', text: problem }); } }, 300);
        setTimeout(() => clearInterval(wait), 15000);
    }

    // Test hook: lets the automated browser tests look inside without a UI.
    window.__wb = { strokes, receive, get height() { return height; }, get problem() { return problem; } };
})();
