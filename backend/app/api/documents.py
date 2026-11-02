"""Document endpoints: upload, list, delete."""

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.models.documents import (
    DeleteDocumentResponse,
    DocumentListResponse,
    DocumentMetadata,
    DocumentUploadResponse,
)
from app.services.document_service import (
    ALLOWED_EXTENSIONS,
    delete_document_record,
    list_documents,
    process_upload,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was provided.")

    extension = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{extension}'. "
            f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    if len(file_bytes) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_MB}MB.",
        )

    record = process_upload(file.filename, file_bytes)

    if record["status"] == "failed":
        # Still return 200 with status="failed" so the frontend can show a
        # friendly inline error rather than a network-error toast.
        return DocumentUploadResponse(**{k: record[k] for k in ("id", "filename", "status", "chunks", "error")})

    return DocumentUploadResponse(**{k: record[k] for k in ("id", "filename", "status", "chunks", "error")})


@router.get("", response_model=DocumentListResponse)
async def get_documents() -> DocumentListResponse:
    records = list_documents()
    return DocumentListResponse(documents=[DocumentMetadata(**r) for r in records])


@router.delete("/{document_id}", response_model=DeleteDocumentResponse)
async def delete_document(document_id: str) -> DeleteDocumentResponse:
    deleted = delete_document_record(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DeleteDocumentResponse(id=document_id, deleted=True)
