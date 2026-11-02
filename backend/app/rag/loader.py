"""
Document loading.

Turns an uploaded file on disk into a list of LangChain `Document`
objects, one per page (for PDFs) or one per file (for plain text
formats). Each Document carries a `page` number in its metadata so
we can build accurate citations later ("paper.pdf — Page 4").
"""

from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


class UnsupportedFileTypeError(Exception):
    pass


class EmptyDocumentError(Exception):
    pass


def load_document(file_path: Path, original_filename: str) -> list[Document]:
    """Load a file from disk into a list of page-level Documents."""
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        docs = _load_pdf(file_path, original_filename)
    elif extension in (".txt", ".md"):
        docs = _load_text(file_path, original_filename)
    elif extension == ".docx":
        docs = _load_docx(file_path, original_filename)
    else:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{extension}'. "
            f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    # Drop pages/sections with no real text content.
    docs = [d for d in docs if d.page_content and d.page_content.strip()]

    if not docs:
        raise EmptyDocumentError(
            "No extractable text was found in this document. "
            "It may be empty, image-only, or corrupted."
        )

    return docs


def _load_pdf(file_path: Path, filename: str) -> list[Document]:
    try:
        reader = PdfReader(str(file_path))
    except Exception as exc:  # noqa: BLE001 - surfaced to the user as a friendly error
        raise EmptyDocumentError(f"Could not read PDF file: {exc}") from exc

    docs = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        docs.append(
            Document(
                page_content=text,
                metadata={"filename": filename, "page": page_number},
            )
        )
    return docs


def _load_text(file_path: Path, filename: str) -> list[Document]:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    return [Document(page_content=text, metadata={"filename": filename, "page": 1})]


def _load_docx(file_path: Path, filename: str) -> list[Document]:
    from docx import Document as DocxDocument

    docx_file = DocxDocument(str(file_path))
    text = "\n".join(p.text for p in docx_file.paragraphs)
    return [Document(page_content=text, metadata={"filename": filename, "page": 1})]
