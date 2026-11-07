"""Extract resume text from files uploaded to the local web app."""

import os
from pathlib import Path


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def extract_resume_text(file_path: str) -> str:
    """Return readable text from a PDF, DOCX, or plain-text resume."""
    suffix = Path(file_path).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported resume format. Upload a PDF, DOCX, or TXT file.")

    if suffix == ".txt":
        text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF parsing requires pypdf. Install the project requirements and try again.") from exc
        reader = PdfReader(file_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("DOCX parsing requires python-docx. Install the project requirements and try again.") from exc
        document = Document(file_path)
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)

    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if len(normalized) < 40:
        raise ValueError("The uploaded resume did not contain enough readable text.")
    return normalized


def upload_extension(filename: str) -> str:
    return os.path.splitext(filename or "")[1].lower()
