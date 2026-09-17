/* =============================================
   Sign in / sign up for a learner account.
   Username + 4-digit PIN, posted to /api/account/*.
   ============================================= */
'use strict';

(function () {
    const signOut = document.getElementById('ul-signout');
    if (signOut) {
        signOut.addEventListener('click', async () => {
            signOut.disabled = true;
            await fetch('/api/account/logout', { method: 'POST' });
            // Progress stays in localStorage, so signing out on a shared device
            // would leave it on screen for the next person. Clear the local copy
            // and let the next sign-in pull it back down from the server.
            try {
                Object.keys(localStorage)
                    .filter(k => k.startsWith('mathsheet_unit_progress_'))
                    .forEach(k => localStorage.removeItem(k));
            } catch (e) { /* storage blocked — nothing cached to clear */ }
            window.location.href = '/';
        });
        return;
    }

    const tabs = document.querySelectorAll('[data-tab]');
    const forms = {
        signin: document.getElementById('ul-form-signin'),
        signup: document.getElementById('ul-form-signup'),
    };
    if (!forms.signin || !forms.signup) return;

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const which = tab.dataset.tab;
            tabs.forEach(t => {
                const on = t === tab;
                t.classList.toggle('is-active', on);
                t.setAttribute('aria-selected', on ? 'true' : 'false');
            });
            Object.entries(forms).forEach(([name, form]) => { form.hidden = name !== which; });
            forms[which].querySelector('input').focus();
        });
    });

    function wire(which, endpoint) {
        const form = forms[which];
        const error = document.getElementById(`ul-error-${which}`);
        const button = form.querySelector('button[type="submit"]');
        const label = button.textContent;

        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            error.hidden = true;
            button.disabled = true;
            button.textContent = 'One moment…';

            const data = new FormData(form);
            let payload;
            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        username: (data.get('username') || '').trim(),
                        pin: (data.get('pin') || '').trim(),
                    }),
                });
                payload = await response.json();
            } catch (e) {
                payload = { success: false, error: "Couldn't reach the server — check your connection." };
            }

            if (payload.success) {
                window.location.href = ACCOUNT_NEXT || '/';
                return;
            }
            error.textContent = payload.error || 'Something went wrong.';
            error.hidden = false;
            button.disabled = false;
            button.textContent = label;
        });
    }

    wire('signin', '/api/account/login');
    wire('signup', '/api/account/signup');
}());
