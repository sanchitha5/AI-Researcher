"""
FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.api import documents, research
from app.config import settings

app = FastAPI(
    title="AI Research Agent API",
    description="Research across uploaded documents and the live web, powered by LangGraph.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(research.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Never leak a raw Python traceback to the frontend."""
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred. Please try again."},
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "gemini_configured": settings.gemini_configured,
        "groq_configured": settings.groq_configured,
        "tavily_configured": settings.tavily_configured,
        "langsmith_enabled": settings.LANGCHAIN_TRACING_V2,
    }

