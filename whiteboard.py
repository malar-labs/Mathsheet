"""The live whiteboard — a teacher writes, a learner watches (and writes back).

Two pages:

    /whiteboard?student=<name>   the teacher's board. Admin only; anyone else
                                 gets the same 404 as every other admin page.
    /board/<code>                the learner's board. No account needed — the
                                 unguessable code in the link is the key.

Strokes travel between the two browsers over Supabase Realtime "broadcast"
channels, which pass messages straight from browser to browser and store
nothing — no table, no rows, no learner data. That needs the project's
publishable key in the page, which is safe: that key is designed to be public,
and the schema's row-level security already stops it reading any table.

Without SUPABASE_PUBLISHABLE_KEY the board still works as a plain whiteboard on
one screen, and the page says to share the screen in the video call instead.

Kept out of app.py on purpose: app.py hands this module the few things it
needs (templates, the admin check, the not-found page) and mounts the router.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
from typing import Awaitable, Callable

from urllib.parse import quote

from fastapi import APIRouter, Request

# A room code is the first 12 hex characters of an HMAC — 48 bits, far too many
# to guess, and the same every time for the same student so the link Sanjana
# bookmarks keeps working from one class to the next.
CODE_LENGTH = 12
CODE_RE = re.compile(rf"^[0-9a-f]{{{CODE_LENGTH}}}$")
NAME_MAX = 40


def _secret() -> str:
    # Read on every call, like store._config(): app.py loads .env after imports.
    return (os.environ.get("WHITEBOARD_SECRET")
            or os.environ.get("SECRET_KEY")
            or "mathsheet-bc-grade8-secret-2024")


def clean_name(raw: str | None) -> str:
    """A display name safe to put in a page title and a link."""
    name = re.sub(r"\s+", " ", (raw or "").strip())
    name = re.sub(r"[^\w .'-]", "", name)
    return name[:NAME_MAX].strip()


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def room_code(name: str) -> str:
    """The same student always gets the same room; different students never share one."""
    key = _secret().encode()
    return hmac.new(key, f"whiteboard:{slug(name)}".encode(), hashlib.sha256).hexdigest()[:CODE_LENGTH]


def realtime_config() -> dict | None:
    """What the browser needs to join a live channel, or None when live sharing is off."""
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
    if not url or not key:
        return None
    return {"url": url, "key": key}


def build_router(
    templates,
    require_admin: Callable[[Request], Awaitable[dict | None]],
    not_found: Callable[[Request], object],
) -> APIRouter:
    router = APIRouter()

    @router.get("/whiteboard")
    async def teacher_board(request: Request, student: str = "", problem: str = ""):
        admin = await require_admin(request)
        if not admin:
            return not_found(request)

        name = clean_name(student)
        code = room_code(name) if name else None
        # A path, not a full URL: behind Vercel's proxy the server can't be sure
        # of its own public address, so the page adds location.origin itself.
        share_url = f"/board/{code}?name={quote(name)}" if code else None
        return templates.TemplateResponse(
            request,
            "whiteboard.html",
            {
                "learner": admin,
                "role": "teacher",
                "student": name,
                "room": code,
                "share_url": share_url,
                "problem": problem[:300],
                "realtime": realtime_config(),
            },
        )

    @router.get("/board/{code}")
    async def student_board(request: Request, code: str, name: str = ""):
        if not CODE_RE.match(code):
            return not_found(request)
        return templates.TemplateResponse(
            request,
            "whiteboard.html",
            {
                "learner": None,
                "role": "student",
                "student": clean_name(name) or "Student",
                "room": code,
                "share_url": None,
                "problem": "",
                "realtime": realtime_config(),
            },
        )

    return router
