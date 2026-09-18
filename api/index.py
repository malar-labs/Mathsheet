"""Vercel entry point.

Vercel runs the app as a serverless function and looks for an ASGI `app` in
this file; everything else still lives in app.py, which also stays runnable
locally with `python app.py`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402  (path set up above first)

__all__ = ["app"]
