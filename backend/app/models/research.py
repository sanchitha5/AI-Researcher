"""Pydantic schemas for the /api/research endpoints."""

from typing import Literal

from pydantic import BaseModel, Field

ResearchMode = Literal["auto", "documents", "web"]
CitationType = Literal["document", "web"]


class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    mode: ResearchMode = "auto"
    document_ids: list[str] = Field(
        default_factory=list,
        description="Optional list of document IDs to restrict document search to. "
        "Empty list means 'search across all uploaded documents'.",
    )


class Citation(BaseModel):
    """A single piece of evidence used to build the answer."""

    index: int
    type: CitationType
    # Document citations
    filename: str | None = None
    page: int | None = None
    snippet: str | None = None
    # Web citations
    title: str | None = None
    url: str | None = None
    source: str | None = None


class ResearchResponse(BaseModel):
    answer: str
    citations: list[Citation]
    sources_used: list[str]
    retries: int
    mode_used: ResearchMode
