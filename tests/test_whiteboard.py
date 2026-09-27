"""
The live whiteboard: who can open which board, and the room codes behind the links.

Drawing and live sync happen entirely in the browser (static/js/whiteboard.js)
and pass through Supabase Realtime, so nothing here needs a network. What's
pinned down is the part that would be expensive to get wrong: only an admin
opens the teacher's board, a learner's link keeps working from class to class,
and no two learners ever land in the same room.
"""
import os

from fastapi.testclient import TestClient

os.environ["GEMINI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["OPENROUTER_API_KEY"] = ""

import store
import whiteboard
from app import app

client = TestClient(app)


def _async(value):
    async def run():
        return value
    return run()


def sign_in(monkeypatch, admin, learner_id=7, name="Teacher"):
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


# =============================================
#   room codes
# =============================================

class TestRoomCodes:
    def test_the_same_student_always_gets_the_same_room(self):
        # The link Sanjana bookmarks after the first class has to still work
        # at the second one.
        assert whiteboard.room_code("Sanjana") == whiteboard.room_code("Sanjana")

    def test_spacing_and_capitals_dont_change_the_room(self):
        assert whiteboard.room_code("sanjana") == whiteboard.room_code("  SANJANA ")

    def test_different_students_get_different_rooms(self):
        assert whiteboard.room_code("Sanjana") != whiteboard.room_code("Maya")

    def test_codes_have_the_shape_the_learner_page_accepts(self):
        assert whiteboard.CODE_RE.match(whiteboard.room_code("Sanjana"))

    def test_the_code_depends_on_the_secret(self, monkeypatch):
        # Otherwise anyone who knows a student's name could work out the link.
        monkeypatch.setenv("WHITEBOARD_SECRET", "one")
        first = whiteboard.room_code("Sanjana")
        monkeypatch.setenv("WHITEBOARD_SECRET", "two")
        assert whiteboard.room_code("Sanjana") != first

    def test_names_are_cleaned_before_they_reach_a_page(self):
        assert whiteboard.clean_name("  <b>Sanjana</b>  ") == "bSanjanab"
        assert len(whiteboard.clean_name("x" * 200)) <= whiteboard.NAME_MAX


# =============================================
#   who can open which board
# =============================================

class TestTeacherBoard:
    def test_a_signed_out_visitor_gets_nothing(self):
        client.post("/api/account/logout")
        assert client.get("/whiteboard").status_code == 404
        assert client.get("/whiteboard?student=Sanjana").status_code == 404

    def test_an_ordinary_learner_gets_nothing(self, monkeypatch):
        sign_in(monkeypatch, admin=False)
        assert client.get("/whiteboard?student=Sanjana").status_code == 404

    def test_an_admin_is_asked_who_the_board_is_for(self, monkeypatch):
        sign_in(monkeypatch, admin=True)
        page = client.get("/whiteboard")
        assert page.status_code == 200
        assert "Start a whiteboard" in page.text
        assert "wb-canvas" not in page.text

    def test_an_admin_gets_the_board_and_the_link_to_send(self, monkeypatch):
        sign_in(monkeypatch, admin=True)
        monkeypatch.setenv("SUPABASE_URL", "https://demo.supabase.co")
        monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_demo")
        page = client.get("/whiteboard?student=Sanjana&problem=2%201/2%20%C3%B7%205/6")
        assert page.status_code == 200
        assert "wb-canvas" in page.text
        assert f"/board/{whiteboard.room_code('Sanjana')}" in page.text
        assert "2 1/2 ÷ 5/6" in page.text

    def test_the_secret_key_never_reaches_the_page(self, monkeypatch):
        sign_in(monkeypatch, admin=True)
        monkeypatch.setenv("SUPABASE_URL", "https://demo.supabase.co")
        monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_secret_do_not_leak")
        monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_demo")
        page = client.get("/whiteboard?student=Sanjana")
        assert "sb_secret_do_not_leak" not in page.text
        assert "sb_publishable_demo" in page.text

    def test_without_the_publishable_key_the_board_says_to_share_the_screen(self, monkeypatch):
        sign_in(monkeypatch, admin=True)
        monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY", raising=False)
        page = client.get("/whiteboard?student=Sanjana")
        assert page.status_code == 200
        assert "Share your screen" in page.text
        assert "supabase-js" not in page.text

    def test_admin_is_rechecked_every_time(self, monkeypatch):
        sign_in(monkeypatch, admin=True)
        assert client.get("/whiteboard?student=Sanjana").status_code == 200
        monkeypatch.setattr(store, "is_admin", lambda lid: _async(False))
        assert client.get("/whiteboard?student=Sanjana").status_code == 404


class TestLearnerBoard:
    def test_the_link_works_without_an_account(self):
        client.post("/api/account/logout")
        code = whiteboard.room_code("Sanjana")
        page = client.get(f"/board/{code}?name=Sanjana")
        assert page.status_code == 200
        assert "wb-canvas" in page.text
        # The learner's board has no teacher controls.
        assert "wb-share-url" not in page.text
        assert "wb-problem-input" not in page.text

    def test_a_made_up_code_is_not_found(self):
        assert client.get("/board/not-a-room").status_code == 404
        assert client.get("/board/ABCDEF123456").status_code == 404
