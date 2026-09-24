import io
from pypdf import PdfReader
from docx import Document
import pymupdf


def extract_txt(file) -> str:
    """Extract text from uploaded TXT file safely."""
    file.file.seek(0)
    content = file.file.read()
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1", errors="ignore")


def extract_pdf(file) -> str:
    """Extract text from uploaded PDFs, with a fallback for difficult PDFs."""
    file.file.seek(0)
    pdf_bytes = file.file.read()

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join(
            page_text
            for page in reader.pages
            if (page_text := page.extract_text())
        ).strip()
        if text:
            return text
    except Exception:
        pass

    # PyMuPDF handles PDFs with unusual text encodings more consistently.
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as document:
        return "\n".join(
            page.get_text("text")
            for page in document
            if page.get_text("text")
        ).strip()


def extract_docx(file) -> str:
    """Extract text from uploaded DOCX file safely using BytesIO."""
    file.file.seek(0)
    docx_bytes = file.file.read()
    docx_stream = io.BytesIO(docx_bytes)

    document = Document(docx_stream)
    text = ""
    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            text += paragraph.text + "\n"
    return text

