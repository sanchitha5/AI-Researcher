"""
Document service.

Handles everything around an uploaded file's lifecycle:

    save to disk -> extract text -> chunk -> embed -> store in Chroma
                                                          |
                                                          v
                                          record metadata in documents.json

We deliberately avoid a real database here (per the workshop's
"no database server" rule) and instead keep a tiny JSON file as the
source of truth for "which documents exist and what's their status".
ChromaDB remains the source of truth for the actual chunks/vectors.
"""

import json
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import DOCUMENTS_METADATA_FILE, UPLOADS_DIR
from app.rag.embeddings import GeminiNotConfiguredError
from app.rag.loader import EmptyDocumentError, UnsupportedFileTypeError, load_document
from app.rag.splitter import split_documents
from app.rag.vectorstore import add_chunks, delete_document as delete_from_vectorstore

_LOCK = threading.Lock()

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


class DocumentProcessingError(Exception):
    """Raised for any user-facing document processing failure."""


def _sanitize_filename(filename: str) -> str:
    """Strip path components and unsafe characters from a filename."""
    name = Path(filename).name  # drop any directory components
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return name or "upload"


def _read_all_metadata() -> list[dict]:
    if not DOCUMENTS_METADATA_FILE.exists():
        return []
    with open(DOCUMENTS_METADATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def _write_all_metadata(records: list[dict]) -> None:
    DOCUMENTS_METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DOCUMENTS_METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def list_documents() -> list[dict]:
    with _LOCK:
        return _read_all_metadata()


def get_document(document_id: str) -> dict | None:
    with _LOCK:
        for record in _read_all_metadata():
            if record["id"] == document_id:
                return record
    return None


def get_ready_document_ids() -> list[str]:
    """IDs of all documents that finished processing successfully."""
    return [d["id"] for d in list_documents() if d["status"] == "ready"]


def delete_document_record(document_id: str) -> bool:
    with _LOCK:
        records = _read_all_metadata()
        remaining = [r for r in records if r["id"] != document_id]
        found = len(remaining) != len(records)
        if found:
            _write_all_metadata(remaining)

    if found:
        delete_from_vectorstore(document_id)
        # Best-effort cleanup of the original uploaded file.
        for path in UPLOADS_DIR.glob(f"{document_id}_*"):
            path.unlink(missing_ok=True)

    return found


def process_upload(raw_filename: str, file_bytes: bytes) -> dict:
    """
    Save an uploaded file, extract/chunk/embed it, and record its
    metadata. Returns the final metadata record (status "ready" or
    "failed").
    """
    document_id = str(uuid.uuid4())
    safe_name = _sanitize_filename(raw_filename)
    extension = Path(safe_name).suffix.lower()

    record = {
        "id": document_id,
        "filename": safe_name,
        "status": "processing",
        "chunks": 0,
        "file_type": extension.lstrip("."),
        "size_bytes": len(file_bytes),
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if extension not in ALLOWED_EXTENSIONS:
        record["status"] = "failed"
        record["error"] = (
            f"Unsupported file type '{extension}'. "
            f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
        _append_record(record)
        return record

    saved_path = UPLOADS_DIR / f"{document_id}_{safe_name}"

    try:
        saved_path.write_bytes(file_bytes)

        pages = load_document(saved_path, safe_name)
        chunks = split_documents(pages, document_id)

        if not chunks:
            raise EmptyDocumentError("Document produced no usable text chunks.")

        add_chunks(chunks)

        record["status"] = "ready"
        record["chunks"] = len(chunks)

    except (UnsupportedFileTypeError, EmptyDocumentError) as exc:
        record["status"] = "failed"
        record["error"] = str(exc)
    except GeminiNotConfiguredError as exc:
        record["status"] = "failed"
        record["error"] = str(exc)
    except Exception as exc:  # noqa: BLE001 - convert any unexpected error to a friendly one
        record["status"] = "failed"
        record["error"] = "An unexpected error occurred while processing the document."
        print(f"[document_service] Unexpected error processing {safe_name}: {exc}")
    finally:
        _append_record(record)

    return record


def _append_record(record: dict) -> None:
    with _LOCK:
        records = _read_all_metadata()
        records.append(record)
        _write_all_metadata(records)
