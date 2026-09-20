"""Learner accounts and saved progress, kept in Supabase.

We talk to Supabase over its PostgREST API rather than opening a Postgres
connection: no database driver, no connection pool and no IPv6 requirement, so
deploying is two environment variables and nothing else.

Everything here degrades to a no-op when SUPABASE_URL and SUPABASE_SECRET_KEY
are unset. The app then behaves exactly as it did before accounts existed —
progress lives in the browser, every page still works, and the test suite needs
no credentials. Signing in is an extra that carries progress between devices; it
is never a gate in front of the learning content.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

import httpx

def _config() -> tuple[str, str]:
    """Read the environment on every call, never at import time.

    app.py imports this module before it calls load_dotenv(), so anything
    captured at import would be blank on a machine configured through .env —
    accounts would then be silently off with no error to explain why.
    """
    return (
        os.environ.get("SUPABASE_URL", "").rstrip("/"),
        os.environ.get("SUPABASE_SECRET_KEY", ""),
    )

# Five wrong PINs parks the account for a quarter of an hour. This — not the
# hash — is what stops someone walking through all 10,000 four-digit PINs on a
# classmate's username.
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,19}$")
PIN_RE = re.compile(r"^\d{4}$")

# Ranked so a merge can keep the best answer a learner has ever given.
VERDICT_RANK = {"wrong": 1, "close": 2, "correct": 3}


class StoreError(RuntimeError):
    """Supabase said no. The caller turns this into a friendly message."""


class UsernameTaken(StoreError):
    pass


def enabled() -> bool:
    """False when Supabase isn't configured, which puts the app in local-only mode."""
    url, key = _config()
    return bool(url and key)


# ===== validation =====

def normalize_username(raw: str) -> str:
    return (raw or "").strip().lower()


def username_problem(username: str) -> str | None:
    """A message to show the learner, or None when the name is fine."""
    if not username:
        return "Pick a username."
    if not USERNAME_RE.match(username):
        return ("Usernames are 3–20 characters: letters, numbers, - and _ only, "
                "starting with a letter or number.")
    return None


def pin_problem(pin: str) -> str | None:
    if not PIN_RE.match(pin or ""):
        return "Your PIN must be exactly 4 digits."
    return None


# ===== PIN hashing =====
# pbkdf2 is in the standard library, so accounts add no dependency. A 4-digit
# PIN falls to an offline brute force whatever we hash it with; the point of
# hashing is that a database leak doesn't hand over PINs that learners have
# reused elsewhere.

PIN_ITERATIONS = 200_000


def hash_pin(pin: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, PIN_ITERATIONS)
    return f"pbkdf2_sha256${PIN_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_pin(pin: str, stored: str) -> bool:
    try:
        algo, iterations, salt_hex, digest_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", pin.encode(), bytes.fromhex(salt_hex), int(iterations)
        )
    except (AttributeError, ValueError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


# ===== HTTP plumbing =====

_client: httpx.AsyncClient | None = None
_client_config: tuple[str, str] | None = None


def _get_client() -> httpx.AsyncClient:
    """One shared client, so a progress sync doesn't pay for a TLS handshake.

    Rebuilt if the credentials change underneath it, which is what lets a test
    point the module at a different project without a stale client in the way.
    """
    global _client, _client_config
    url, key = _config()
    if not (url and key):
        raise StoreError("Supabase isn't configured on this server.")
    if _client is None or _client_config != (url, key):
        _client = httpx.AsyncClient(
            base_url=f"{url}/rest/v1",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )
        _client_config = (url, key)
    return _client


async def aclose() -> None:
    global _client, _client_config
    if _client is not None:
        await _client.aclose()
        _client = None
        _client_config = None


async def _request(method: str, path: str, *, prefer: str | None = None, **kwargs) -> httpx.Response:
    headers = {"Prefer": prefer} if prefer else None
    try:
        response = await _get_client().request(method, path, headers=headers, **kwargs)
    except httpx.HTTPError as exc:
        raise StoreError(f"Could not reach the progress server: {exc}") from exc
    if response.status_code >= 400:
        # 23505 is Postgres' unique-violation, i.e. the username is taken.
        if response.status_code == 409 or '"23505"' in response.text:
            raise UsernameTaken("That username is taken — try another.")
        raise StoreError(f"Progress server error {response.status_code}: {response.text[:200]}")
    return response


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# PostgREST answers with at most its configured maximum rows — 1000 by default
# — and says nothing when it truncates. A silent truncation here would quietly
# under-report a whole class, so anything that reads a table in full walks the
# pages until one comes back short.
PAGE_SIZE = 1000


async def _get_all(path: str, params: dict) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        page = (await _request("GET", path, params={
            **params, "limit": str(PAGE_SIZE), "offset": str(offset)})).json()
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            return rows
        offset += PAGE_SIZE


# ===== learners =====

async def find_learner(username: str) -> dict | None:
    response = await _request(
        "GET", "/learners", params={"username": f"eq.{username}", "select": "*", "limit": "1"}
    )
    rows = response.json()
    return rows[0] if rows else None


async def get_learner(learner_id: int) -> dict | None:
    response = await _request(
        "GET", "/learners", params={"id": f"eq.{learner_id}", "select": "*", "limit": "1"}
    )
    rows = response.json()
    return rows[0] if rows else None


async def list_learners() -> list[dict]:
    """Everyone, most recently seen first — the teacher's roster."""
    return await _get_all("/learners", {
        "select": "id,username,display_name,grade,created_at,last_seen,is_admin",
        "order": "last_seen.desc",
    })


async def is_admin(learner_id: int) -> bool:
    """Read the flag fresh on every check.

    Caching it in the session would mean taking admin away from someone only
    took effect once they happened to sign out, which is not what anyone
    revoking access expects.
    """
    learner = await get_learner(learner_id)
    return bool(learner and learner.get("is_admin"))


async def create_learner(username: str, display_name: str, pin: str, grade: int | None) -> dict:
    response = await _request(
        "POST",
        "/learners",
        prefer="return=representation",
        json={
            "username": username,
            "display_name": display_name,
            "pin_hash": hash_pin(pin),
            "grade": grade,
        },
    )
    return response.json()[0]


async def _patch_learner(learner_id: int, fields: dict) -> None:
    await _request(
        "PATCH", "/learners", params={"id": f"eq.{learner_id}"}, prefer="return=minimal", json=fields
    )


def lockout_remaining(learner: dict) -> int:
    """Whole minutes still to wait, or 0 when the account is open."""
    locked_until = learner.get("locked_until")
    if not locked_until:
        return 0
    try:
        until = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))
    except ValueError:
        return 0
    remaining = (until - datetime.now(timezone.utc)).total_seconds()
    return max(0, int(remaining // 60) + 1) if remaining > 0 else 0


async def note_failed_attempt(learner: dict) -> int:
    """Count a wrong PIN. Returns minutes locked out, 0 if there's still room."""
    failed = (learner.get("failed_attempts") or 0) + 1
    fields: dict = {"failed_attempts": failed}
    if failed >= MAX_FAILED_ATTEMPTS:
        fields["locked_until"] = (
            datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
        ).isoformat()
        fields["failed_attempts"] = 0
    await _patch_learner(learner["id"], fields)
    return LOCKOUT_MINUTES if failed >= MAX_FAILED_ATTEMPTS else 0


async def note_signed_in(learner_id: int) -> None:
    await _patch_learner(
        learner_id, {"failed_attempts": 0, "locked_until": None, "last_seen": _now()}
    )


# ===== progress =====

async def load_progress(learner_id: int, unit_key: str | None = None) -> dict[str, dict[str, str]]:
    """{unit_key: {question_id: verdict}} for one unit, or for every unit."""
    params = {"learner_id": f"eq.{learner_id}", "select": "unit_key,question_id,verdict"}
    if unit_key:
        params["unit_key"] = f"eq.{unit_key}"
    rows = (await _request("GET", "/progress", params=params)).json()
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        out.setdefault(row["unit_key"], {})[row["question_id"]] = row["verdict"]
    return out


async def progress_rows(learner_id: int | None = None) -> list[dict]:
    """Raw answers — one learner's, or the whole school's, for the admin pages.

    Returned as rows rather than the nested shape load_progress() gives, because
    the roster needs to count across units and the detail page needs to know
    which question each verdict belongs to.
    """
    params = {"select": "learner_id,unit_key,question_id,verdict,updated_at"}
    if learner_id is not None:
        params["learner_id"] = f"eq.{learner_id}"
    return await _get_all("/progress", params)


async def save_progress(learner_id: int, unit_key: str, verdicts: dict[str, str]) -> dict[str, str]:
    """Merge answers into the stored set and return the unit's merged state.

    Best verdict wins rather than last write wins: a learner who got a question
    right on the tablet shouldn't lose the tick because they fumbled it on the
    laptop afterwards. Clearing a topic goes through clear_progress(), which
    deletes rows, so "start over" still works.
    """
    rows = (await _request(
        "GET",
        "/progress",
        params={
            "learner_id": f"eq.{learner_id}",
            "unit_key": f"eq.{unit_key}",
            "select": "question_id,verdict,attempts",
        },
    )).json()
    existing = {row["question_id"]: row for row in rows}

    changed = []
    merged = {qid: row["verdict"] for qid, row in existing.items()}
    for question_id, verdict in verdicts.items():
        if verdict not in VERDICT_RANK:
            continue
        old = existing.get(question_id)
        best = verdict
        if old and VERDICT_RANK[old["verdict"]] >= VERDICT_RANK[verdict]:
            best = old["verdict"]
        if old and old["verdict"] == verdict:
            continue  # nothing new to record
        merged[question_id] = best
        changed.append({
            "learner_id": learner_id,
            "unit_key": unit_key,
            "question_id": question_id,
            "verdict": best,
            "attempts": (old["attempts"] if old else 0) + 1,
            "updated_at": _now(),
        })

    if changed:
        await _request(
            "POST",
            "/progress",
            params={"on_conflict": "learner_id,unit_key,question_id"},
            prefer="resolution=merge-duplicates,return=minimal",
            json=changed,
        )
    return merged


async def clear_progress(learner_id: int, unit_key: str, question_ids: list[str]) -> None:
    """Forget these answers — what "start this topic over" does server-side."""
    if not question_ids:
        return
    quoted = ",".join(f'"{qid}"' for qid in question_ids)
    await _request(
        "DELETE",
        "/progress",
        params={
            "learner_id": f"eq.{learner_id}",
            "unit_key": f"eq.{unit_key}",
            "question_id": f"in.({quoted})",
        },
        prefer="return=minimal",
    )
