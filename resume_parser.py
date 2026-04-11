"""
Resume Parser — Extract text from PDF and DOCX files.
Handles file validation, error recovery, and logging.
"""

import io
import os
import pdfplumber
from docx import Document

from config import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB, MAX_PDF_PAGES
from logger import get_logger

logger = get_logger(__name__)


class ResumeParseError(Exception):
    """Custom exception for resume parsing errors."""
    pass


def validate_file_size(file) -> None:
    """
    Validate that the uploaded file does not exceed the size limit.

    Args:
        file: Uploaded file object (Streamlit UploadedFile).

    Raises:
        ResumeParseError: If the file exceeds the size limit.
    """
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)     # Reset to beginning

    if size > MAX_FILE_SIZE_BYTES:
        size_mb = round(size / (1024 * 1024), 1)
        raise ResumeParseError(
            f"File size ({size_mb} MB) exceeds the {MAX_FILE_SIZE_MB} MB limit. "
            "Please upload a smaller file."
        )
    logger.debug(f"File size validated: {round(size / 1024, 1)} KB")


def extract_text_from_pdf(file) -> str:
    """
    Extract text from an uploaded PDF file.
    Uses pdfplumber as primary extractor, falls back to PyMuPDF (fitz)
    if pdfplumber finds no text.

    Args:
        file: Uploaded PDF file object.

    Returns:
        Extracted text content as a string.

    Raises:
        ResumeParseError: If the PDF cannot be read or parsed.
    """
    validate_file_size(file)

    # Read file bytes once for both engines
    file_bytes = file.read()
    file.seek(0)

    # ── Attempt 1: pdfplumber ────────────────────────────────────────────
    text_parts = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"Parsing PDF with pdfplumber: {total_pages} page(s)")

            if total_pages > MAX_PDF_PAGES:
                logger.warning(
                    f"PDF has {total_pages} pages (limit: {MAX_PDF_PAGES}). "
                    f"Only first {MAX_PDF_PAGES} pages will be processed."
                )

            pages_to_process = min(total_pages, MAX_PDF_PAGES)
            for i, page in enumerate(pdf.pages[:pages_to_process]):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                else:
                    logger.debug(f"Page {i + 1}: no text via pdfplumber")

    except Exception as e:
        logger.warning(f"pdfplumber failed: {type(e).__name__}: {e}")

    if text_parts:
        result = "\n".join(text_parts).strip()
        logger.info(f"PDF parsed via pdfplumber: {len(result)} chars extracted")
        return result

    # ── Attempt 2: PyMuPDF (fitz) text extraction ───────────────────────
    logger.info("pdfplumber found no text, trying PyMuPDF fallback...")
    fitz_doc = None
    try:
        import fitz  # PyMuPDF

        fitz_doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages_to_process = min(len(fitz_doc), MAX_PDF_PAGES)

        for i in range(pages_to_process):
            page = fitz_doc[i]
            page_text = page.get_text("text")
            if page_text and page_text.strip():
                text_parts.append(page_text.strip())

    except ImportError:
        logger.warning("PyMuPDF not installed. Install with: pip install PyMuPDF")
    except Exception as e:
        logger.warning(f"PyMuPDF text extraction failed: {type(e).__name__}: {e}")

    if text_parts:
        if fitz_doc:
            fitz_doc.close()
        result = "\n".join(text_parts).strip()
        logger.info(f"PDF parsed via PyMuPDF: {len(result)} chars extracted")
        return result

    # ── Attempt 3: OCR via PyMuPDF + pytesseract (scanned PDFs) ──────
    logger.info("No text layer found, attempting OCR on scanned pages...")
    try:
        import pytesseract
        from PIL import Image

        # Auto-detect Tesseract on Windows
        _TESSERACT_PATHS = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        for tpath in _TESSERACT_PATHS:
            if os.path.exists(tpath):
                pytesseract.pytesseract.tesseract_cmd = tpath
                break

        if fitz_doc is None:
            import fitz
            fitz_doc = fitz.open(stream=file_bytes, filetype="pdf")

        pages_to_process = min(len(fitz_doc), MAX_PDF_PAGES)

        for i in range(pages_to_process):
            page = fitz_doc[i]
            # Render page as high-res image (300 DPI)
            mat = fitz.Matrix(300 / 72, 300 / 72)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            # OCR the image
            ocr_text = pytesseract.image_to_string(img, lang="eng")
            if ocr_text and ocr_text.strip():
                text_parts.append(ocr_text.strip())
                logger.debug(f"Page {i + 1}: OCR extracted {len(ocr_text)} chars")

        fitz_doc.close()
        fitz_doc = None

    except ImportError:
        logger.info("pytesseract not available for OCR")
    except Exception as e:
        logger.warning(f"OCR fallback failed: {type(e).__name__}: {e}")

    if fitz_doc:
        fitz_doc.close()

    if text_parts:
        result = "\n".join(text_parts).strip()
        logger.info(f"PDF parsed via OCR: {len(result)} chars extracted")
        return result

    # ── All engines failed ───────────────────────────────────────────────
    raise ResumeParseError(
        "No text could be extracted from the PDF.\n\n"
        "**Your PDF appears to be a scanned image** (no selectable text).\n\n"
        "Options:\n"
        "- Upload a **DOCX** file instead (recommended)\n"
        "- Upload a text-based PDF (where you can select/copy text)\n"
        "- Install Tesseract OCR for scanned PDF support:\n"
        "  Download from: https://github.com/tesseract-ocr/tesseract/releases"
    )


def extract_text_from_docx(file) -> str:
    """
    Extract text from an uploaded DOCX file.

    Args:
        file: Uploaded DOCX file object.

    Returns:
        Extracted text content as a string.

    Raises:
        ResumeParseError: If the DOCX cannot be read or parsed.
    """
    validate_file_size(file)

    try:
        doc = Document(io.BytesIO(file.read()))
        paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]

        if not paragraphs:
            raise ResumeParseError(
                "No text content found in the DOCX file. "
                "The document may be empty or contain only images."
            )

        result = "\n".join(paragraphs)
        logger.info(f"DOCX parsed successfully: {len(result)} characters extracted")
        return result

    except ResumeParseError:
        raise
    except Exception as e:
        logger.error(f"Failed to parse DOCX: {type(e).__name__}: {e}")
        raise ResumeParseError(
            f"Failed to read the DOCX file: {str(e)}. "
            "The file may be corrupted or in an unsupported format."
        )


def parse_resume(file, filename: str) -> str:
    """
    Parse a resume file (PDF or DOCX) and return extracted text.

    Args:
        file: Uploaded file object.
        filename: Original filename with extension.

    Returns:
        Extracted text content.

    Raises:
        ResumeParseError: If the file format is unsupported or parsing fails.
    """
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "pdf":
        return extract_text_from_pdf(file)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(file)
    else:
        raise ResumeParseError(
            f"Unsupported file format: .{ext}. "
            "Please upload a PDF or DOCX file."
        )
