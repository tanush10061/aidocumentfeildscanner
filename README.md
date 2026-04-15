

# LLM-based Invoice OCR 

An hybrid Invoice OCR pipeline that extracts structured JSON data from invoices. This project demonstrates an end-to-end intelligent document processing pipeline.

## 🎬 Demo

📹 **(https://drive.google.com/file/d/17MpFdzs3mrm-jd801CzsPZ-NdsQOmw6s/view?usp=drive_link)**



---

## Features
- Accepts PDF or image uploads (pdf2image used to convert PDFs).
- Multi-page PDFs supported (each page converted to an image and processed).
- Extract structured data (invoice_number, vendor_name, invoice_date, line_items, grand_total, etc.).
- Switch between **Paid API** and **Open-source OCR**.
- Returns structured JSON.
- Sample invoices included for testing/demo.

---

## Tech Stack
- **Backend**: FastAPI
- **Frontend**: Gradio
- **OCR**: pdf2image + Tesseract (open-source) OR Together AI API
- **Language Model (API)**: Qwen2.5-VL-72B-Instruct (Together AI)

**Modes**:
- **paid**: Uses Together AI (Qwen2.5-VL-72B-Instruct) to extract structured JSON from invoice images.
- **open_source**: Uses `pytesseract` OCR + heuristics for a free fallback option.

## Quickstart

### 1) Create a virtual environment and install dependencies
On Windows PowerShell:
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

On macOS/Linux (bash/zsh):
```
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2) Install prerequisites
- Poppler (required for PDF → image conversion via pdf2image)
	- Windows: Download a Poppler build (e.g., from https://github.com/oschwartz10612/poppler-windows/releases), unzip to `C:\poppler\poppler-23.08.0`, and ensure the `Library\bin` folder exists.
	- macOS: `brew install poppler`
	- Ubuntu/Debian: `sudo apt install poppler-utils`

- Tesseract (recommended for open-source OCR mode)
	- Windows: Install from https://github.com/tesseract-ocr/tesseract (ensure the installer adds Tesseract to PATH, or note the install path, e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`).
	- macOS: `brew install tesseract`
	- Ubuntu/Debian: `sudo apt install tesseract-ocr`

### 3) Configure environment variables
Copy `.env.example` to `.env` and set values as needed (only the API key is required for paid mode):
```
TOGETHER_API_KEY="your_api_key_here"
TOGETHER_MODEL="Qwen/Qwen2.5-VL-72B-Instruct"
TOGETHER_INFERENCE_URL="https://api.together.xyz/v1/chat/completions"
```

Windows-specific optional settings:
- Set `POPPLER_PATH` if Poppler is not on PATH. The backend uses this for PDF conversion on Windows and defaults to `C:\\poppler\\poppler-23.08.0\\Library\\bin` if not set.
	- PowerShell (current session):
		```
		$env:POPPLER_PATH = "C:\\poppler\\poppler-23.08.0\\Library\\bin"
		```
	- Or set permanently via System Properties → Environment Variables.

- Ensure Tesseract is on PATH for `open_source` mode. If not, either add it to PATH or configure `pytesseract.pytesseract.tesseract_cmd` in code to the full path, e.g. `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`.

### 4) Run the backend (FastAPI)
PowerShell:
```
uvicorn src.backend.main:app --reload
```

### 5) Run the frontend (Gradio)
In a second terminal (with the same venv activated):
```
python src/frontend/gradio_app.py
```

Open the Gradio UI at the URL printed in the terminal (typically `http://127.0.0.1:7860`, may vary). Try files from `sample_invoices/`.

---

---

## Windows notes and troubleshooting
- Poppler not found / 500 error converting PDFs:
	- Ensure Poppler is installed and `POPPLER_PATH` points to its `Library\bin` folder (Windows). The backend uses this path when converting PDFs via `pdf2image`.

- Tesseract not found in `open_source` mode:
	- Add Tesseract to PATH or set `pytesseract.pytesseract.tesseract_cmd` to its full path.

- 401/403 errors in paid mode:
	- Verify `TOGETHER_API_KEY` in `.env`. Restart the backend after changes.

- Connection failed between frontend and backend:
	- Confirm backend at `http://127.0.0.1:8000` is running before starting the frontend. The frontend posts to that URL.

- Poor OCR quality (open_source):
	- Try higher DPI for PDFs or better scans. Our backend uses 300 DPI for PDF conversion by default.

- Multi-page PDFs:
	- Each page is processed and aggregated. The response includes `pages` to confirm count.


---
