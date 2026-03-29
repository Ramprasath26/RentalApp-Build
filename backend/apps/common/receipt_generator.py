"""
Rent Receipt PDF Generator
Generates a digitally-signed rent receipt PDF using ReportLab.
"""
import hashlib
import io
import os
from datetime import date, datetime

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

# Brand colours
PRIMARY   = colors.HexColor("#1a3c6b")   # navy
ACCENT    = colors.HexColor("#e07b2a")   # orange
LIGHT_BG  = colors.HexColor("#f4f7fc")
BORDER    = colors.HexColor("#cdd5e0")
GREEN     = colors.HexColor("#28a745")
GRAY      = colors.HexColor("#6c757d")
WHITE     = colors.white


def _qr_image(data: str, size_mm: float = 28) -> Image:
    """Return a QR code as a ReportLab Image flowable."""
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    buf = io.BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
    buf.seek(0)
    px = size_mm * mm
    return Image(buf, width=px, height=px)


def _sign_hash(data: str) -> str:
    """Generate a short verification hash for the receipt."""
    return hashlib.sha256(data.encode()).hexdigest()[:16].upper()


def generate_rent_receipt(
    receipt_number: str,
    receipt_date: date,
    tenant_name: str,
    tenant_phone: str,
    property_name: str,
    unit_code: str,
    period_month: int,
    period_year: int,
    rent_amount: float,
    paid_amount: float,
    payment_mode: str,
    transaction_id: str,
    owner_name: str,
    logo_path: str | None = None,
) -> bytes:
    """Generate a rent receipt PDF and return the bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
    )

    styles = getSampleStyleSheet()
    s_title   = ParagraphStyle("title",   fontSize=20, textColor=WHITE, alignment=TA_CENTER, fontName="Helvetica-Bold", leading=24)
    s_sub     = ParagraphStyle("sub",     fontSize=9,  textColor=WHITE, alignment=TA_CENTER, fontName="Helvetica")
    s_h2      = ParagraphStyle("h2",      fontSize=11, textColor=PRIMARY, fontName="Helvetica-Bold", spaceAfter=2)
    s_label   = ParagraphStyle("label",   fontSize=8,  textColor=GRAY,    fontName="Helvetica")
    s_value   = ParagraphStyle("value",   fontSize=10, textColor=PRIMARY,  fontName="Helvetica-Bold")
    s_small   = ParagraphStyle("small",   fontSize=7,  textColor=GRAY,    alignment=TA_CENTER)
    s_sign    = ParagraphStyle("sign",    fontSize=9,  textColor=PRIMARY,  fontName="Helvetica-Bold", alignment=TA_CENTER)
    s_hash    = ParagraphStyle("hash",    fontSize=7,  textColor=GRAY,    fontName="Courier", alignment=TA_CENTER)
    s_paid    = ParagraphStyle("paid",    fontSize=28, textColor=GREEN,    fontName="Helvetica-Bold", alignment=TA_CENTER)
    s_center  = ParagraphStyle("center",  fontSize=9,  textColor=PRIMARY,  alignment=TA_CENTER)
    s_footer  = ParagraphStyle("footer",  fontSize=7,  textColor=GRAY,    alignment=TA_CENTER)

    MONTH_NAMES = ["January","February","March","April","May","June",
                   "July","August","September","October","November","December"]
    period_str = f"{MONTH_NAMES[period_month - 1]} {period_year}"
    balance    = max(0, float(rent_amount) - float(paid_amount))

    # ── Verification hash ─────────────────────────────────
    raw_data = f"{receipt_number}|{tenant_name}|{period_str}|{paid_amount}|{receipt_date}"
    verify_hash = _sign_hash(raw_data)
    qr_data = (
        f"RentalApp-Build Receipt\n"
        f"No: {receipt_number}\n"
        f"Tenant: {tenant_name}\n"
        f"Period: {period_str}\n"
        f"Paid: ₹{paid_amount:,.2f}\n"
        f"Hash: {verify_hash}"
    )

    story = []

    # ── Header banner ─────────────────────────────────────
    header_data = [[""]]
    header_table = Table(header_data, colWidths=[174 * mm], rowHeights=[22 * mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("TOPPADDING",    (0, 0), (-1, -1), 6 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
    ]))

    # Logo + title row
    logo_cell = ""
    if logo_path and os.path.exists(logo_path):
        logo_cell = Image(logo_path, width=14 * mm, height=14 * mm)

    header_content = Table(
        [[logo_cell,
          [Paragraph("RentalApp-Build", s_title),
           Paragraph("Official Rent Receipt", s_sub)]]],
        colWidths=[18 * mm, 156 * mm],
    )
    header_content.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
    ]))
    story.append(header_content)
    story.append(Spacer(1, 4 * mm))

    # ── Receipt meta row ──────────────────────────────────
    meta_left  = Table([
        [Paragraph("Receipt No.", s_label), Paragraph(receipt_number, s_value)],
        [Paragraph("Date",        s_label), Paragraph(receipt_date.strftime("%d %B %Y"), s_value)],
        [Paragraph("Period",      s_label), Paragraph(period_str, s_value)],
    ], colWidths=[30 * mm, 60 * mm])
    meta_left.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING",(0,0),(-1,-1),1)]))

    meta_right = Table([
        [Paragraph("Transaction ID", s_label), Paragraph(str(transaction_id), s_value)],
        [Paragraph("Payment Mode",   s_label), Paragraph(payment_mode.title() if payment_mode else "—", s_value)],
    ], colWidths=[30 * mm, 54 * mm])
    meta_right.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING",(0,0),(-1,-1),1)]))

    meta_row = Table([[meta_left, meta_right]], colWidths=[92 * mm, 82 * mm])
    meta_row.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT_BG),
        ("BOX",        (0,0), (-1,-1), 0.5, BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 4 * mm),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4 * mm),
        ("LEFTPADDING",   (0,0), (-1,-1), 4 * mm),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4 * mm),
    ]))
    story.append(meta_row)
    story.append(Spacer(1, 4 * mm))

    # ── Tenant / Property ─────────────────────────────────
    tenant_block = Table([
        [Paragraph("Tenant",   s_h2)],
        [Paragraph(tenant_name,   s_value)],
        [Paragraph(tenant_phone or "—", s_label)],
    ], colWidths=[84 * mm])
    tenant_block.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 1), ("BOTTOMPADDING",(0,0),(-1,-1), 1),
    ]))

    property_block = Table([
        [Paragraph("Property / Unit",  s_h2)],
        [Paragraph(property_name,  s_value)],
        [Paragraph(f"Unit: {unit_code}", s_label)],
    ], colWidths=[82 * mm])
    property_block.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 1), ("BOTTOMPADDING",(0,0),(-1,-1), 1),
    ]))

    parties_row = Table([[tenant_block, property_block]], colWidths=[89 * mm, 85 * mm])
    parties_row.setStyle(TableStyle([
        ("BOX",     (0,0),(0,-1), 0.5, BORDER),
        ("BOX",     (1,0),(1,-1), 0.5, BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 3 * mm),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3 * mm),
        ("LEFTPADDING",   (0,0),(-1,-1), 4 * mm),
        ("RIGHTPADDING",  (0,0),(-1,-1), 4 * mm),
    ]))
    story.append(parties_row)
    story.append(Spacer(1, 4 * mm))

    # ── Amount summary table ──────────────────────────────
    amt_data = [
        [Paragraph("Description", s_h2),     Paragraph("Amount (₹)", s_h2)],
        ["Monthly Rent Due",                  f"₹ {float(rent_amount):,.2f}"],
        ["Amount Paid (this receipt)",        f"₹ {float(paid_amount):,.2f}"],
        ["Balance Remaining",                 f"₹ {balance:,.2f}"],
    ]
    amt_table = Table(amt_data, colWidths=[130 * mm, 44 * mm])
    amt_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1, 0),  PRIMARY),
        ("TEXTCOLOR",     (0,0), (-1, 0),  WHITE),
        ("FONTNAME",      (0,0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1),  9),
        ("ROWBACKGROUNDS",(0,1), (-1,-1),  [WHITE, LIGHT_BG]),
        ("GRID",          (0,0), (-1,-1),  0.5, BORDER),
        ("ALIGN",         (1,0), (1,-1),   "RIGHT"),
        ("TOPPADDING",    (0,0), (-1,-1),  4),
        ("BOTTOMPADDING", (0,0), (-1,-1),  4),
        ("LEFTPADDING",   (0,0), (0,-1),   6),
        ("RIGHTPADDING",  (1,0), (1,-1),   6),
        # Highlight paid row
        ("BACKGROUND",    (0,2), (-1,2),   colors.HexColor("#e6f4ea")),
        ("TEXTCOLOR",     (1,2), (1,2),    GREEN),
        ("FONTNAME",      (1,2), (1,2),    "Helvetica-Bold"),
    ]))
    story.append(amt_table)
    story.append(Spacer(1, 6 * mm))

    # ── PAID stamp + QR ──────────────────────────────────
    qr_img  = _qr_image(qr_data, 28)
    stamp_col = Table([
        [Paragraph("PAID", s_paid)],
        [Paragraph(f"₹ {float(paid_amount):,.2f}", ParagraphStyle("bigamt", fontSize=14, textColor=GREEN, fontName="Helvetica-Bold", alignment=TA_CENTER))],
    ])
    stamp_col.setStyle(TableStyle([
        ("BOX",           (0,0),(-1,-1), 2, GREEN),
        ("TOPPADDING",    (0,0),(-1,-1), 3 * mm),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3 * mm),
    ]))

    qr_col = Table([
        [qr_img],
        [Paragraph("Scan to verify", s_small)],
    ])
    qr_col.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER")]))

    sig_col = Table([
        [Paragraph(owner_name or "Property Owner", s_sign)],
        [HRFlowable(width=50*mm, color=PRIMARY, thickness=1)],
        [Paragraph("Authorised Signatory", s_label)],
        [Paragraph(f"Hash: {verify_hash}", s_hash)],
    ])
    sig_col.setStyle(TableStyle([
        ("ALIGN",  (0,0),(-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
    ]))

    bottom_row = Table([[stamp_col, qr_col, sig_col]], colWidths=[56*mm, 34*mm, 84*mm])
    bottom_row.setStyle(TableStyle([
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0),(-1,-1), 4*mm),
        ("RIGHTPADDING",  (0,0),(-1,-1), 4*mm),
    ]))
    story.append(bottom_row)
    story.append(Spacer(1, 6*mm))

    # ── Footer ────────────────────────────────────────────
    story.append(HRFlowable(width="100%", color=BORDER, thickness=0.5))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        f"This is a computer-generated receipt. Verification hash: <b>{verify_hash}</b> | "
        f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')} | RentalApp-Build",
        s_footer
    ))

    doc.build(story)
    return buf.getvalue()
