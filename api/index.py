"""Vercel serverless entry point.

The whole SignGuard Layer 2 application (REST + dashboard pages) is exposed
through this single function; vercel.json rewrites every path onto it, so the
routes behave exactly like `uvicorn app.main:app` on the laptop.
"""
from app.main import app  # noqa: F401
