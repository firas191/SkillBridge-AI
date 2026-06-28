"""Tests for offline document parsing (text, docx, image OCR)."""
from __future__ import annotations

import io

import pytest

from app.services.extraction import ParsedDocument, extract_text


def test_extract_txt():
    doc = extract_text(b"Hello, I know Python and SQL.", "notes.txt")
    assert isinstance(doc, ParsedDocument)
    assert doc.method == "text"
    assert "Python" in doc.text
    assert doc.char_count == len(doc.text)


def test_extract_md():
    doc = extract_text(b"# CV\nSkills: React, TypeScript", "cv.md")
    assert doc.method == "text"
    assert "React" in doc.text


def test_unsupported_type_raises():
    with pytest.raises(ValueError):
        extract_text(b"data", "archive.zip")


def test_extract_docx():
    docx = pytest.importorskip("docx")  # python-docx
    document = docx.Document()
    document.add_paragraph("Experienced Java engineer with Spring Boot.")
    buf = io.BytesIO()
    document.save(buf)
    doc = extract_text(buf.getvalue(), "resume.docx")
    assert doc.method == "docx"
    assert "Java" in doc.text


def test_image_ocr_pipeline_runs():
    """Smoke-test the real offline OCR path (skipped if engine not installed)."""
    pytest.importorskip("rapidocr_onnxruntime")
    PIL = pytest.importorskip("PIL")  # noqa: N806
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (640, 180), "white")
    ImageDraw.Draw(img).text((20, 60), "PYTHON DEVELOPER", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    doc = extract_text(buf.getvalue(), "scan.png")
    assert doc.method == "image-ocr"
    assert isinstance(doc.text, str)  # recognition quality varies by font; wiring works
