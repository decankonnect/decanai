from io import BytesIO
from pypdf import PdfReader
from fastapi import HTTPException, UploadFile
from .config import get_settings

async def extract_pdf(file: UploadFile) -> tuple[str, list[dict[str, int]]]:
    settings = get_settings()
    if file.content_type != "application/pdf":
        raise HTTPException(415, "Only PDF files are supported")
    raw = await file.read()
    if len(raw) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(413, "The uploaded file exceeds the allowed size")
    try:
        reader = PdfReader(BytesIO(raw))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
    except Exception as exc:
        raise HTTPException(400, "The PDF could not be read") from exc
    text = "\n\n".join(f"[Page {index + 1}]\n{page}" for index, page in enumerate(pages) if page)
    if not text:
        raise HTTPException(422, "This PDF has no readable text; OCR is not enabled")
    return text, [{"page_number": index + 1} for index, page in enumerate(pages) if page]

def chunk_text(text: str, size: int = 1600, overlap: int = 200) -> list[str]:
    cleaned = " ".join(text.split())
    return [cleaned[start:start + size] for start in range(0, len(cleaned), max(1, size - overlap)) if cleaned[start:start + size]]
