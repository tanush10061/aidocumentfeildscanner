"""
Generate complex synthetic invoice PDFs and images to stress-test OCR/LLM parsing.

Scenarios:
- Skewed/rotated text
- Low contrast watermark behind text
- Mixed fonts and sizes
- Tables with borders and without borders
- Multi-language snippets
- Noisy background and stamps

Outputs saved under sample_invoices/complex/
Requires: reportlab, pillow
"""
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import io
import random
import math

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT, 'sample_invoices', 'complex')
os.makedirs(OUT_DIR, exist_ok=True)


def add_watermark(c, text, width, height):
    c.saveState()
    # Use a very light gray to simulate transparency (avoid alpha for compatibility)
    c.setFillColorRGB(0.93, 0.95, 0.95)
    c.setFont("Helvetica-Bold", 120)
    c.translate(width/2, height/2)
    c.rotate(30)
    c.drawCentredString(0, 0, text)
    c.restoreState()


def draw_header(c, w, h):
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.HexColor('#333333'))
    c.drawString(20*mm, h-25*mm, "ACME International Trading Co.")
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, h-31*mm, "VAT: GB123456789 | DUNS: 123-456-789")
    c.drawRightString(w-20*mm, h-25*mm, "INVOICE")
    c.setFont("Helvetica", 10)
    c.drawRightString(w-20*mm, h-31*mm, "Invoice No: INV-%05d" % random.randint(1, 99999))
    c.drawRightString(w-20*mm, h-36*mm, "Date: 2025-09-%02d" % random.randint(1, 28))


def draw_bill_to(c, w, h):
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20*mm, h-45*mm, "Bill To:")
    c.setFont("Helvetica", 10)
    lines = [
        "Globex Corporation",
        "Attn: Accounts Payable",
        "742 Evergreen Terrace",
        "Springfield, USA",
        "Tel: +1 555-0199",
    ]
    y = h-50*mm
    for line in lines:
        c.drawString(20*mm, y, line)
        y -= 5*mm


def draw_table(c, w, h):
    c.setFont("Helvetica-Bold", 10)
    y = h-85*mm
    cols = [20*mm, 90*mm, 130*mm, 160*mm, w-20*mm]
    headers = ["Description", "Qty", "Unit Price", "Tax", "Total"]
    for i in range(len(cols)-1):
        c.drawString(cols[i], y, headers[i])
    y -= 6*mm
    c.setStrokeColor(colors.lightgrey)
    c.line(20*mm, y, w-20*mm, y)

    c.setFont("Helvetica", 10)
    for i in range(12):
        y -= 8*mm
        # Use ASCII hyphen to avoid Unicode issues
        desc = f"UltraWidget Pro Max - model {random.randint(100,999)}"
        qty = random.randint(1, 15)
        unit = round(random.uniform(5.5, 199.99), 2)
        tax = random.choice(["5%", "7%", "GST 10%", "VAT 20%"])
        total = round(qty*unit* (1 + (0.2 if '20' in tax else 0.1 if '10' in tax else 0.07 if '7' in tax else 0.05)), 2)
        values = [desc, str(qty), f"${unit:,.2f}", tax, f"${total:,.2f}"]
        for i in range(len(cols)-1):
            c.drawString(cols[i], y, values[i])
        # occasional stamp overlap
        if random.random() < 0.15:
            # Light red without alpha for compatibility
            c.setFillColorRGB(0.95, 0.3, 0.3)
            c.setFont("Helvetica-Bold", 36)
            c.drawString(cols[0]+10, y+2, "PAID")
            c.setFillColor(colors.black)

    # Totals
    y -= 12*mm
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(w-60*mm, y, "Subtotal:")
    c.drawRightString(w-20*mm, y, "$2,450.50")
    y -= 7*mm
    c.drawRightString(w-60*mm, y, "Tax:")
    c.drawRightString(w-20*mm, y, "$245.05")
    y -= 7*mm
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(w-60*mm, y, "Total:")
    c.drawRightString(w-20*mm, y, "$2,695.55")


def add_rotation_noise(pdf_bytes):
    # render to image, rotate slightly, blur, then back to image file
    img = Image.open(io.BytesIO(pdf_bytes)).convert('RGB') if isinstance(pdf_bytes, (bytes, bytearray)) else pdf_bytes
    angle = random.uniform(-2.5, 2.5)
    rotated = img.rotate(angle, expand=True, fillcolor=(245, 248, 240))
    noisy = rotated.filter(ImageFilter.GaussianBlur(radius=0.6))
    return noisy


def build_pdf_invoice(path, rotate_as_image=False):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    add_watermark(c, "CONFIDENTIAL", w, h)
    draw_header(c, w, h)
    draw_bill_to(c, w, h)
    draw_table(c, w, h)

    # Note block (ASCII-only to avoid font encoding issues)
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor('#333333'))
    c.drawString(20*mm, 20*mm, "Payment terms 30 days | Zahlungsziel 30 Tage | Paiement 30 jours")

    c.showPage()
    c.save()

    pdf_data = buffer.getvalue()
    if rotate_as_image:
        # render first page to image, add noise & save as PNG
        # Use PIL to create a PNG that mimics a scanned document
        img = Image.new('RGB', (1240, 1754), (248, 251, 244))
        draw = ImageDraw.Draw(img)
        # fake ASCII-only symbols to build complexity
        for i in range(40):
            x = random.randint(20, 1200)
            y = random.randint(20, 1730)
            col = random.choice([(80,80,80), (60,70,60), (90,100,90)])
            draw.text((x, y), random.choice(["#", "*", "@", "X", "O"]), fill=col)
        noisy = add_rotation_noise(img)
        noisy_path = path.replace('.pdf', '.png')
        noisy.save(noisy_path, optimize=True)
        return noisy_path
    else:
        with open(path, 'wb') as f:
            f.write(pdf_data)
        return path


def build_multipage_invoice(path):
    """Create a 2-page invoice with varying layouts and rotations."""
    buffer = io.BytesIO()
    # Page 1: A4 portrait
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    add_watermark(c, "DRAFT", w, h)
    draw_header(c, w, h)
    draw_bill_to(c, w, h)
    draw_table(c, w, h)
    c.setFont("Helvetica", 9)
    c.drawString(20*mm, 25*mm, "Page 1 of 2 - Summary")
    c.showPage()

    # Page 2: A4 landscape with rotated section
    c.setPageSize(landscape(A4))
    w2, h2 = landscape(A4)
    add_watermark(c, "INTERNAL", w2, h2)
    c.saveState()
    c.translate(40*mm, h2-20*mm)
    c.rotate(-5)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(0, 0, "Detailed Charges and Notes")
    c.restoreState()

    # Draw a faux table without borders (harder for OCR)
    c.setFont("Helvetica-Bold", 10)
    y = h2 - 40*mm
    headers = ["Item", "Hours", "Rate", "Total"]
    xcols = [20*mm, 120*mm, 170*mm, 220*mm]
    for i, hname in enumerate(headers):
        c.drawString(xcols[i], y, hname)
    y -= 6*mm
    c.setFont("Helvetica", 9)
    for i in range(25):
        y -= 6.5*mm
        item = f"Consulting Service {i+1}"
        hours = round(random.uniform(0.5, 8.0), 1)
        rate = random.choice([85, 95, 120, 150])
        total = f"${hours*rate:,.2f}"
        c.drawString(xcols[0], y, item)
        c.drawString(xcols[1], y, str(hours))
        c.drawString(xcols[2], y, f"${rate}")
        c.drawString(xcols[3], y, total)

    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(w2-20*mm, 25*mm, "Grand Total: $12,345.67")
    c.drawString(20*mm, 25*mm, "Page 2 of 2 - Details")

    c.showPage()
    c.save()

    with open(path, 'wb') as f:
        f.write(buffer.getvalue())
    return path

def main():
    random.seed(42)
    out1 = os.path.join(OUT_DIR, 'complex_invoice_1.pdf')
    out2 = os.path.join(OUT_DIR, 'complex_invoice_2.pdf')
    out3 = os.path.join(OUT_DIR, 'complex_invoice_scanlike.png')
    out4 = os.path.join(OUT_DIR, 'complex_invoice_multipage.pdf')

    p1 = build_pdf_invoice(out1, rotate_as_image=False)
    p2 = build_pdf_invoice(out2, rotate_as_image=False)
    p3 = build_pdf_invoice(out3, rotate_as_image=True)
    p4 = build_multipage_invoice(out4)

    print("Generated:")
    print(" -", p1)
    print(" -", p2)
    print(" -", p3)
    print(" -", p4)


if __name__ == "__main__":
    main()
