"""Pydantic schemas for document upload / listing endpoints."""

from typing import Literal

from pydantic import BaseModel, Field

DocumentStatus = Literal["processing", "ready", "failed"]


class DocumentMetadata(BaseModel):
    """A single uploaded document, as tracked by the backend."""

    id: str
    filename: str
    status: DocumentStatus
    chunks: int = 0
    file_type: str
    size_bytes: int
    error: str | None = None
    created_at: str


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    status: DocumentStatus
    chunks: int
    error: str | None = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentMetadata]


class DeleteDocumentResponse(BaseModel):
    id: str
    deleted: bool = Field(description="Whether the document was found and removed")
