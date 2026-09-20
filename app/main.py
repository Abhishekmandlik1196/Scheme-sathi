"""Scheme Saathi — FastAPI application entry point."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .core import config

BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "frontend"))

app = FastAPI(
    title="Scheme Saathi",
    description="Conversational AI that matches citizens to eligible government schemes",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.middleware("http")
async def no_cache_static(request, call_next):
    """Always revalidate the UI: Chrome otherwise caches index.html/app.js
    heuristically and users see stale interfaces after updates. ETags still
    make repeat loads fast (304), but content is never stale."""
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "llm_enabled": config.LLM_ENABLED,
        "service": "scheme-saathi",
    }
