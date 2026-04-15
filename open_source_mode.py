"""Open-source OCR mode using pytesseract + simple regex heuristics.

This is a baseline extractor for environments without paid LLM access. It uses:
- pytesseract to OCR an image
- a few regex patterns to locate common invoice fields

Notes:
- On Windows, ensure Tesseract is installed and update the path below if needed.
"""

import re
from typing import Dict
from PIL import Image
import pytesseract
import os

# Configure Tesseract path for Windows
if os.name == 'nt':  # Windows
    tesseract_path = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path


def extract_with_ocr(image_path: str) -> Dict:
    """Simple OCR extraction using pytesseract and regex heuristics.

    Returns a dict matching the invoice schema used across the project.
    """
    text = pytesseract.image_to_string(Image.open(image_path))

    # Heuristics/regexes (improve as needed)
    invoice_number = _search_first(r"Invoice\s*[#:\s]*([A-Za-z0-9-]+)", text)
    date = _search_first(r"Date[:\s]*([0-9/\-\.]+)", text)
    total = _search_first(r"Total\s*[:\-]?\s*\$?\s*([0-9,]+\.?[0-9]{0,2})", text)
    vendor = _search_first(r"^([A-Z][A-Za-z0-9 &,-]{2,})", text, flags=re.M)

    # naive line items extraction: lines containing a price at end
    lines = text.splitlines()
    line_items = []
    for line in lines:
        if re.search(r"\d+\.?\d{0,2}$", line.strip()):
            parts = line.strip().rsplit(None, 1)
            desc = parts[0]
            price = parts[1] if len(parts)>1 else ""
            line_items.append({"description": desc, "quantity": "", "unit_price": "", "total_price": price})

    return {
        "vendor_name": vendor or "",
        "invoice_number": invoice_number or "",
        "invoice_date": date or "",
        "due_date": "",
        "bill_to": "",
        "line_items": line_items,
        "subtotal": "",
        "tax": "",
        "grand_total": total or "",
        "payment_info": "",
        "raw_text": text
    }


def _search_first(pattern, text, flags=0):
    """Return first regex group or None."""
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None
