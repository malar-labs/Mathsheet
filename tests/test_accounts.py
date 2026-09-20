"""
Learner accounts (username + 4-digit PIN) and cross-device progress.

Nothing here touches Supabase: store.py's network layer is faked, so these run
offline and in CI with no credentials. What's actually being pinned down is the
behaviour that would be expensive to get wrong — the PIN hash, the lockout, the
merge rule, and the promise that none of this ever gates the learning content.
"""
import os
import pytest
from fastapi.testclient import TestClient

os.environ["GEMINI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["OPENROUTER_API_KEY"] = ""

import app as app_module
import store
from app import app

client = TestClient(app)


@pytest.fixture
def anyio_backend():
    """Lets @pytest.mark.anyio run on anyio's pytest plugin, which ships with
    FastAPI's own dependencies — no extra test package needed."""
    return "asyncio"


# =============================================
#   PIN hashing
# =============================================

class TestPinHashing:
    def test_verifies_the_right_pin(self):
        assert store.verify_pin("4827", store.hash_pin("4827"))

    def test_rejects_the_wrong_pin(self):
        assert not store.verify_pin("1234", store.hash_pin("4827"))

    def test_same_pin_hashes_differently_each_time(self):
        # A per-PIN salt means two learners who both pick 1234 don't share a
        # hash, so cracking one doesn't crack the other.
        assert store.hash_pin("1234") != store.hash_pin("1234")

    def test_the_pin_is_not_recoverable_from_the_hash(self):
        assert "4827" not in store.hash_pin("4827")

    @pytest.mark.parametrize("stored", ["", "garbage", "pbkdf2_sha256$x$y", "a$b$c$d"])
    def test_malformed_hashes_fail_closed(self, stored):
        assert not store.verify_pin("4827", stored)


# =============================================
#   input rules
# =============================================

class TestValidation:
    @pytest.mark.parametrize("username", ["ava", "ava_9", "grade8-ana", "a" * 20])
    def test_accepts_sensible_usernames(self, username):
        assert store.username_problem(username) is None

    @pytest.mark.parametrize("username", ["", "ab", "a" * 21, "_ava", "ava!", "ava ban"])
    def test_rejects_bad_usernames(self, username):
        assert store.username_problem(username) is not None

    def test_usernames_are_case_insensitive(self):
        assert store.normalize_username("  AvA  ") == "ava"

    @pytest.mark.parametrize("pin", ["0000", "4827"])
    def test_accepts_four_digit_pins(self, pin):
        assert store.pin_problem(pin) is None

    @pytest.mark.parametrize("pin", ["", "123", "12345", "abcd", "12 4"])
    def test_rejects_anything_else(self, pin):
        assert store.pin_problem(pin) is not None


# =============================================
#   the merge rule
# =============================================

class FakeSupabase:
    """Stands in for store's HTTP layer, holding rows in a dict."""

    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.writes = []

    async def request(self, method, path, *, prefer=None, params=None, json=None):
        if path == "/progress" and method == "GET":
            return [dict(r) for r in self.rows]
        if path == "/progress" and method == "POST":
            self.writes.append(json)
            for row in json:
                self.rows = [r for r in self.rows if r["question_id"] != row["question_id"]]
                self.rows.append(row)
            return []
        raise AssertionError(f"unexpected {method} {path}")


@pytest.fixture
def fake(monkeypatch):
    stub = FakeSupabase()

    async def _request(method, path, *, prefer=None, **kwargs):
        class R:
            def json(self_inner):
                return self_inner.payload
        result = await stub.request(method, path, prefer=prefer,
                                    params=kwargs.get("params"), json=kwargs.get("json"))
        response = R()
        response.payload = result
        return response

    monkeypatch.setattr(store, "_request", _request)
    return stub


class TestProgressMerge:
    @pytest.mark.anyio
    async def test_a_new_answer_is_stored(self, fake):
        merged = await store.save_progress(1, "grade9_rational-numbers", {"q1": "correct"})
        assert merged == {"q1": "correct"}

    @pytest.mark.anyio
    async def test_a_better_answer_wins(self, fake):
        fake.rows = [{"question_id": "q1", "verdict": "wrong", "attempts": 1}]
        merged = await store.save_progress(1, "u", {"q1": "correct"})
        assert merged["q1"] == "correct"

    @pytest.mark.anyio
    async def test_a_worse_answer_does_not_overwrite_a_correct_one(self, fake):
        # The whole point of merging on "best" rather than "latest": getting it
        # right on the tablet then fumbling it on the laptop keeps the tick.
        fake.rows = [{"question_id": "q1", "verdict": "correct", "attempts": 2}]
        merged = await store.save_progress(1, "u", {"q1": "wrong"})
        assert merged["q1"] == "correct"

    @pytest.mark.anyio
    async def test_attempts_accumulate(self, fake):
        fake.rows = [{"question_id": "q1", "verdict": "wrong", "attempts": 3}]
        await store.save_progress(1, "u", {"q1": "close"})
        assert fake.writes[0][0]["attempts"] == 4

    @pytest.mark.anyio
    async def test_an_unchanged_answer_writes_nothing(self, fake):
        fake.rows = [{"question_id": "q1", "verdict": "correct", "attempts": 1}]
        await store.save_progress(1, "u", {"q1": "correct"})
        assert fake.writes == []

    @pytest.mark.anyio
    async def test_junk_verdicts_are_ignored(self, fake):
        merged = await store.save_progress(1, "u", {"q1": "brilliant", "q2": "correct"})
        assert merged == {"q2": "correct"}


# =============================================
#   lockout
# =============================================

class TestLockout:
    def test_an_open_account_has_no_wait(self):
        assert store.lockout_remaining({"locked_until": None}) == 0

    def test_an_expired_lock_has_no_wait(self):
        assert store.lockout_remaining({"locked_until": "2020-01-01T00:00:00+00:00"}) == 0

    def test_a_live_lock_reports_minutes_left(self):
        from datetime import datetime, timedelta, timezone
        until = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        assert 1 <= store.lockout_remaining({"locked_until": until}) <= 11

    def test_an_unparseable_lock_does_not_wedge_the_account(self):
        assert store.lockout_remaining({"locked_until": "not-a-date"}) == 0


# =============================================
#   routes
# =============================================

class TestAccountRoutes:
    def test_the_account_page_loads(self):
        assert client.get("/account").status_code == 200

    def test_signing_out_always_works(self):
        assert client.post("/api/account/logout").json()["success"] is True

    def test_progress_needs_a_session(self):
        assert client.get("/api/progress").status_code == 401
        assert client.post("/api/progress", json={"unit_key": "u", "verdicts": {}}).status_code == 401
        assert client.post("/api/progress/clear", json={"unit_key": "u", "question_ids": []}).status_code == 401

    def test_signup_is_refused_when_supabase_is_not_configured(self, monkeypatch):
        monkeypatch.setattr(store, "enabled", lambda: False)
        r = client.post("/api/account/signup", json={"username": "ava", "pin": "4827"})
        assert r.status_code == 503

    def test_a_bad_username_is_rejected_before_any_network_call(self, monkeypatch):
        monkeypatch.setattr(store, "enabled", lambda: True)

        async def explode(*args, **kwargs):
            raise AssertionError("should not have reached Supabase")

        monkeypatch.setattr(store, "find_learner", explode)
        r = client.post("/api/account/signup", json={"username": "a!", "pin": "4827"})
        assert r.status_code == 400

    def test_a_bad_pin_is_rejected_before_any_network_call(self, monkeypatch):
        monkeypatch.setattr(store, "enabled", lambda: True)

        async def explode(*args, **kwargs):
            raise AssertionError("should not have reached Supabase")

        monkeypatch.setattr(store, "find_learner", explode)
        r = client.post("/api/account/signup", json={"username": "ava", "pin": "12"})
        assert r.status_code == 400

    def test_an_unknown_user_and_a_wrong_pin_look_identical(self, monkeypatch):
        """Otherwise the sign-in form doubles as a way to discover usernames."""
        monkeypatch.setattr(store, "enabled", lambda: True)

        async def no_such_user(username):
            return None

        monkeypatch.setattr(store, "find_learner", no_such_user)
        missing = client.post("/api/account/login", json={"username": "nobody", "pin": "4827"})

        async def real_user(username):
            return {"id": 1, "username": "ava", "display_name": "Ava",
                    "pin_hash": store.hash_pin("1111"), "failed_attempts": 0, "locked_until": None}

        async def noop(learner):
            return 0

        monkeypatch.setattr(store, "find_learner", real_user)
        monkeypatch.setattr(store, "note_failed_attempt", noop)
        wrong_pin = client.post("/api/account/login", json={"username": "ava", "pin": "4827"})

        assert missing.status_code == wrong_pin.status_code == 401
        assert missing.json()["error"] == wrong_pin.json()["error"]

    def test_a_locked_account_is_turned_away_without_checking_the_pin(self, monkeypatch):
        monkeypatch.setattr(store, "enabled", lambda: True)
        from datetime import datetime, timedelta, timezone
        until = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

        async def locked_user(username):
            return {"id": 1, "username": "ava", "display_name": "Ava",
                    "pin_hash": store.hash_pin("4827"), "failed_attempts": 0, "locked_until": until}

        monkeypatch.setattr(store, "find_learner", locked_user)
        # Even the correct PIN bounces while the lockout is live.
        r = client.post("/api/account/login", json={"username": "ava", "pin": "4827"})
        assert r.status_code == 429


# =============================================
#   accounts never gate the learning content
# =============================================

class TestAdminPages:
    """Who can see the class-progress pages, and what they say.

    The access rule is the part worth being paranoid about: everything else on
    this page is a table, but getting this wrong hands one learner's record to
    another learner.
    """

    UNIT = "grade8_fractions"

    def as_learner(self, monkeypatch, learner_id=7, name="Teacher", admin=False):
        """Sign someone in for real, then say whether they are an admin."""
        monkeypatch.setattr(store, "enabled", lambda: True)

        async def find(username):
            return {"id": learner_id, "username": username, "display_name": name,
                    "pin_hash": store.hash_pin("1111"), "is_admin": admin}

        async def noop(*a, **k):
            return None

        monkeypatch.setattr(store, "find_learner", find)
        monkeypatch.setattr(store, "note_signed_in", noop)
        monkeypatch.setattr(store, "is_admin", lambda lid: _async(admin))
        assert client.post("/api/account/login",
                           json={"username": name.lower(), "pin": "1111"}).status_code == 200

    def test_a_signed_out_visitor_gets_nothing(self):
        client.post("/api/account/logout")
        assert client.get("/admin").status_code == 404
        assert client.get("/admin/learner/1").status_code == 404

    def test_an_ordinary_learner_gets_nothing(self, monkeypatch):
        self.as_learner(monkeypatch, admin=False)
        assert client.get("/admin").status_code == 404
        assert client.get("/admin/learner/1").status_code == 404

    def test_it_is_a_404_not_a_403(self, monkeypatch):
        """A 403 would confirm the page exists to anyone who pokes at it."""
        self.as_learner(monkeypatch, admin=False)
        response = client.get("/admin")
        assert response.status_code == 404
        assert "Class progress" not in response.text

    def test_the_username_admin_grants_nothing_by_itself(self, monkeypatch):
        """Being a teacher is granted in the database, not claimed by picking
        the right name — otherwise the first person to register `admin` owns
        everybody's data."""
        self.as_learner(monkeypatch, name="admin", admin=False)
        assert client.get("/admin").status_code == 404

    def test_an_admin_sees_the_roster(self, monkeypatch):
        self.as_learner(monkeypatch, admin=True)
        monkeypatch.setattr(store, "list_learners", lambda: _async([
            {"id": 1, "username": "ava", "display_name": "Ava", "grade": 8,
             "created_at": "2026-01-02T00:00:00Z", "last_seen": "2026-02-03T00:00:00Z",
             "is_admin": False},
            {"id": 2, "username": "ben", "display_name": "Ben", "grade": 9,
             "created_at": "2026-01-02T00:00:00Z", "last_seen": "2026-02-03T00:00:00Z",
             "is_admin": False},
        ]))
        monkeypatch.setattr(store, "progress_rows", lambda learner_id=None: _async([
            {"learner_id": 1, "unit_key": self.UNIT, "question_id": "add-01",
             "verdict": "correct", "updated_at": "2026-02-03T00:00:00Z"},
            {"learner_id": 1, "unit_key": self.UNIT, "question_id": "add-02",
             "verdict": "wrong", "updated_at": "2026-02-03T00:00:00Z"},
        ]))
        page = client.get("/admin")
        assert page.status_code == 200
        assert "Ava" in page.text and "Ben" in page.text
        # Ava answered two, one right: a score of 50.
        assert ">50<" in page.text.replace("</strong>", "<")

    def test_the_admin_flag_is_read_fresh_every_time(self, monkeypatch):
        """Taking admin away should take effect at once, not whenever that
        person next happens to sign out."""
        self.as_learner(monkeypatch, admin=True)
        monkeypatch.setattr(store, "list_learners", lambda: _async([]))
        monkeypatch.setattr(store, "progress_rows", lambda learner_id=None: _async([]))
        assert client.get("/admin").status_code == 200

        monkeypatch.setattr(store, "is_admin", lambda lid: _async(False))
        assert client.get("/admin").status_code == 404

    def test_an_unknown_learner_is_a_404(self, monkeypatch):
        self.as_learner(monkeypatch, admin=True)
        monkeypatch.setattr(store, "get_learner", lambda lid: _async(None))
        assert client.get("/admin/learner/999").status_code == 404

    def test_a_learner_page_breaks_progress_down_by_topic(self, monkeypatch):
        self.as_learner(monkeypatch, admin=True)
        monkeypatch.setattr(store, "get_learner", lambda lid: _async(
            {"id": 1, "username": "ava", "display_name": "Ava", "grade": 8,
             "created_at": "2026-01-02T00:00:00Z", "last_seen": "2026-02-03T00:00:00Z"}))
        monkeypatch.setattr(store, "progress_rows", lambda learner_id=None: _async([
            {"learner_id": 1, "unit_key": self.UNIT, "question_id": "add-01",
             "verdict": "correct", "updated_at": "2026-02-03T00:00:00Z"},
            {"learner_id": 1, "unit_key": self.UNIT, "question_id": "divide-01",
             "verdict": "wrong", "updated_at": "2026-02-03T00:00:00Z"},
        ]))
        page = client.get("/admin/learner/1")
        assert page.status_code == 200
        assert "Ava" in page.text
        # The two answers belong to different topics, and both are named.
        assert "Adding Fractions" in page.text
        assert "Dividing Fractions" in page.text
        # The wrong one is what "worth another look" is for.
        assert "Worth another look" in page.text

    def test_the_page_survives_the_progress_server_being_down(self, monkeypatch):
        """A teacher should get a message, not a stack trace."""
        self.as_learner(monkeypatch, admin=True)

        async def down(*a, **k):
            raise store.StoreError("nope")

        monkeypatch.setattr(store, "list_learners", down)
        monkeypatch.setattr(store, "progress_rows", down)
        page = client.get("/admin")
        assert page.status_code == 200
        # (the apostrophe in the real message comes back HTML-escaped)
        assert "reach the progress server" in page.text

    def test_admin_is_off_entirely_when_accounts_are_off(self, monkeypatch):
        """No Supabase means no accounts, so there is nobody to be an admin."""
        self.as_learner(monkeypatch, admin=True)
        monkeypatch.setattr(store, "enabled", lambda: False)
        assert client.get("/admin").status_code == 404


def _async(value):
    """A coroutine that just returns `value`, for stubbing store calls."""
    async def run():
        return value
    return run()


class TestLearningStaysOpen:
    def test_the_landing_page_works_signed_out(self):
        assert client.get("/").status_code == 200

    def test_a_unit_page_works_signed_out(self):
        assert client.get("/units/grade9/rational-numbers").status_code == 200

    def test_a_topic_page_works_signed_out(self):
        r = client.get("/units/grade9/rational-numbers/compare-order")
        assert r.status_code in (200, 404)  # 404 only if that topic id is renamed

    def test_a_unit_page_still_renders_when_supabase_is_down(self, monkeypatch):
        """A dead progress server must not take the lesson down with it."""
        monkeypatch.setattr(store, "enabled", lambda: True)
        monkeypatch.setattr(
            app_module, "current_learner",
            lambda request: {"id": 1, "username": "ava", "display_name": "Ava"},
        )

        async def down(*args, **kwargs):
            raise store.StoreError("connection refused")

        monkeypatch.setattr(store, "load_progress", down)
        r = client.get("/units/grade9/rational-numbers")
        assert r.status_code == 200
        assert "Rational" in r.text
