from io import BytesIO
from fastapi import UploadFile
from app.documents import chunk_text

def test_chunk_text_has_overlap_safe_segments():
    chunks = chunk_text("a" * 3000, size=1000, overlap=100)
    assert len(chunks) == 4
    assert all(chunks)
