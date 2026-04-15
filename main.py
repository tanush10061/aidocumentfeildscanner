"""FastAPI backend for LLM-based Invoice OCR.

Workflow:
1) Accept upload (PDF or image)
2) Convert PDF pages to images (pdf2image + poppler) or pass through images
3) Extract data with either paid LLM (Together AI) or open-source OCR
4) Aggregate/validate and return structured JSON

Notes:
- On Windows, set environment variable POPPLER_PATH to your Poppler bin if not using the default path.
- Converted page images are saved under IMAGE_OUTPUT_DIR for inspection.
"""

import os
import base64
import uuid
import tempfile
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pdf2image import convert_from_path
from typing import List, Dict

from .together_api import extract_invoice_with_together
from .open_source_mode import extract_with_ocr
from .parser import aggregate_results, validate_invoice_json

IMAGE_OUTPUT_DIR = "converted_invoices"
os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)

app = FastAPI(title="LLM Invoice OCR Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health endpoint for quick sanity checks."""
    return {"message": "LLM Invoice OCR Backend is running!", "status": "healthy"}


def save_upload_tmp(upload_file: UploadFile) -> str:
    """Persist the incoming UploadFile to a temporary file and return its path."""
    suffix = Path(upload_file.filename).suffix if upload_file.filename else ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(upload_file.file.read())
        return tmp.name


@app.post("/extract_invoice/")
async def extract_invoice(file: UploadFile = File(...), mode: str = Form("paid")):
    """Upload a PDF/image -> Convert to images -> Use Together AI or OCR -> Return structured JSON.

    Parameters
    - file: PDF or image (png/jpg/jpeg)
    - mode: "paid" (Together AI) or "open_source" (Tesseract-based)
    """
    try:
        print(f"Received request: file={file.filename}, mode={mode}")
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")
        # Save uploaded file temporarily
        suffix = Path(file.filename).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_pdf:
            content = await file.read()
            tmp_pdf.write(content)
            tmp_pdf_path = tmp_pdf.name

        # Convert PDF to images (if pdf) or treat uploaded image as single page
        image_paths: List[str] = []
        if suffix == ".pdf":
            # Poppler path (Windows). Prefer env var POPPLER_PATH; fallback to common default.
            poppler_path = os.getenv("POPPLER_PATH", r"C:\\poppler\\poppler-23.08.0\\Library\\bin")
            pages = convert_from_path(tmp_pdf_path, dpi=300, poppler_path=poppler_path if os.name == 'nt' else None)
            for i, img in enumerate(pages):
                img_name = f"{uuid.uuid4()}_page_{i+1}.png"
                img_path = os.path.join(IMAGE_OUTPUT_DIR, img_name)
                img.save(img_path, "PNG")
                image_paths.append(img_path)
        else:
            # Assume it's an image file already
            out_name = f"{uuid.uuid4()}_page_1{suffix}"
            out_path = os.path.join(IMAGE_OUTPUT_DIR, out_name)
            shutil.copy(tmp_pdf_path, out_path)
            image_paths.append(out_path)

        results = []
        if mode == "open_source":
            # Use pytesseract-based fallback on each image
            for img in image_paths:
                results.append(extract_with_ocr(img))
        else:
            # Use Together AI for each page (paid mode)
            for img in image_paths:
                # extract_invoice_with_together should return dict for page
                results.append(extract_invoice_with_together(img))

        final = aggregate_results(results)
        validate_invoice_json(final)
        return {"invoice_data": final, "pages": len(image_paths)}
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    finally:
        # cleanup: remove temporary uploaded file (keep converted images for inspection)
        try:
            if 'tmp_pdf_path' in locals():
                os.remove(tmp_pdf_path)
        except Exception:
            pass
