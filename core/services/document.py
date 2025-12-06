"""
Document extraction service using Docling.

Handles extraction of text content from various document formats
including PDF, DOCX, PPTX, and plain text files.
"""

import logging
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".txt",
    ".md",
    ".html",
    ".htm",
}

# Extensions that need Docling processing
DOCLING_EXTENSIONS = {".pdf", ".docx", ".pptx", ".html", ".htm"}

# Plain text extensions (direct read)
TEXT_EXTENSIONS = {".txt", ".md"}


def extract_content(uploaded_file: UploadedFile) -> str:
    """
    Extract text content from an uploaded file.

    Args:
        uploaded_file: Django UploadedFile object

    Returns:
        Extracted text content as markdown string

    Raises:
        ValueError: If file type is not supported
        RuntimeError: If extraction fails
    """
    filename = uploaded_file.name or ""
    ext = Path(filename).suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {ext}. "
            f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if ext in TEXT_EXTENSIONS:
        return _extract_text_file(uploaded_file)
    elif ext in DOCLING_EXTENSIONS:
        return _extract_with_docling(uploaded_file, ext)
    else:
        raise ValueError(f"No extraction handler for: {ext}")


def _extract_text_file(uploaded_file: UploadedFile) -> str:
    """
    Extract content from plain text files (TXT, MD).

    Handles encoding detection with fallbacks.
    """
    content_bytes = uploaded_file.read()

    # Try common encodings
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

    for encoding in encodings:
        try:
            return content_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue

    # Last resort: decode with replacement
    logger.warning(
        f"Could not detect encoding for {uploaded_file.name}, using utf-8 with replacement"
    )
    return content_bytes.decode("utf-8", errors="replace")


def _extract_with_docling(uploaded_file: UploadedFile, ext: str) -> str:
    """
    Extract content using Docling for complex document formats.

    Writes file to temp location, processes with Docling, returns markdown.
    """
    # Import here to avoid loading Docling at module level (heavy dependency)
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as e:
        raise RuntimeError(
            "Docling is not installed. Run: pip install docling"
        ) from e

    # Write uploaded file to temp location (Docling needs file path)
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        try:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp.flush()

            # Process with Docling
            logger.info(f"Processing {uploaded_file.name} with Docling")
            converter = DocumentConverter()
            result = converter.convert(str(tmp_path))

            # Export to markdown
            content = result.document.export_to_markdown()

            if not content or not content.strip():
                logger.warning(
                    f"Docling extracted empty content from {uploaded_file.name}"
                )
                return "(No text content could be extracted from this document)"

            logger.info(
                f"Successfully extracted {len(content)} chars from {uploaded_file.name}"
            )
            return content

        except Exception as e:
            logger.error(f"Docling extraction failed for {uploaded_file.name}: {e}")
            raise RuntimeError(f"Failed to extract content from document: {e}") from e

        finally:
            # Clean up temp file
            try:
                tmp_path.unlink()
            except OSError:
                pass


def get_supported_extensions() -> list[str]:
    """Return list of supported file extensions for UI display."""
    return sorted(SUPPORTED_EXTENSIONS)


def is_supported(filename: str) -> bool:
    """Check if a filename has a supported extension."""
    ext = Path(filename).suffix.lower()
    return ext in SUPPORTED_EXTENSIONS
