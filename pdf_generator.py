"""
PDF Report Generator for KrishiIntel AI
Generates clean, professional PDF reports using reportlab.
Supports single invoice PDF and batch PDF (merged with PyPDF2).
"""

import io
import os
import tempfile
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("⚠️  reportlab not installed — PDF generation disabled. Install with: pip install reportlab")

try:
    from PyPDF2 import PdfMerger
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    print("⚠️  PyPDF2 not installed — batch PDF merge disabled. Install with: pip install PyPDF2")


def _format_currency(value) -> str:
    """Format number as Indian currency."""
    if value is None:
        return "N/A"
    try:
        val = float(value)
        if val >= 10_000_000:
            return f"₹{val / 10_000_000:.2f} Cr"
        elif val >= 100_000:
            return f"₹{val / 100_000:.2f} L"
        else:
            return f"₹{val:,.0f}"
    except (ValueError, TypeError):
        return "N/A"


def generate_single_pdf(
    fields: Dict[str, Any],
    decision_support: Optional[Dict] = None,
    doc_id: str = "invoice",
) -> bytes:
    """
    Generate a PDF report for a single invoice.
    Returns PDF content as bytes.

    Raises RuntimeError if reportlab is not installed.
    """
    if not HAS_REPORTLAB:
        raise RuntimeError("reportlab is not installed. Run: pip install reportlab")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#0369a1"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "CustomSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#0369a1"),
        spaceBefore=16,
        spaceAfter=8,
        borderWidth=0,
    )
    normal_style = ParagraphStyle(
        "CustomNormal",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
    )
    footer_style = ParagraphStyle(
        "FooterStyle",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#94a3b8"),
        alignment=TA_CENTER,
        spaceBefore=20,
    )

    elements = []

    # ─── Header ──────────────────────────────────────────────────────
    elements.append(Paragraph("KrishiIntel AI", title_style))
    elements.append(Paragraph("Invoice Analysis Report", subtitle_style))
    elements.append(Paragraph(f"Document: {doc_id}", subtitle_style))
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#0ea5e9"), thickness=2))
    elements.append(Spacer(1, 12))

    # ─── Extracted Fields ────────────────────────────────────────────
    elements.append(Paragraph("Extracted Invoice Fields", section_style))

    field_data = [
        ["Field", "Value"],
        ["Dealer Name", str(fields.get("dealer_name", "N/A"))],
        ["Tractor Model", str(fields.get("model_name", "N/A"))],
        ["Horse Power", f"{fields.get('horse_power', 'N/A')} HP"],
        ["Asset Cost", _format_currency(fields.get("asset_cost"))],
    ]

    if fields.get("region"):
        field_data.append(["Region", str(fields["region"])])
    if fields.get("invoice_date"):
        field_data.append(["Invoice Date", str(fields["invoice_date"])])

    field_table = Table(field_data, colWidths=[150, 320])
    field_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0ea5e9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f1f5f9")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#f1f5f9")]),
    ]))
    elements.append(field_table)
    elements.append(Spacer(1, 12))

    # ─── Document Verification ───────────────────────────────────────
    sig_present = fields.get("signature", {}).get("present", False)
    stamp_present = fields.get("stamp", {}).get("present", False)

    elements.append(Paragraph("Document Verification", section_style))
    verify_data = [
        ["Check", "Status"],
        ["Signature", "✓ Detected" if sig_present else "— Not Found"],
        ["Stamp", "✓ Detected" if stamp_present else "— Not Found"],
    ]
    verify_table = Table(verify_data, colWidths=[150, 320])
    verify_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0ea5e9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f1f5f9")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(verify_table)
    elements.append(Spacer(1, 12))

    # ─── EMI Section (if decision support exists) ────────────────────
    ds = decision_support if decision_support else {}
    if "decision_support" in ds:
        ds = ds["decision_support"]
    emi_options = ds.get("emi_options", {})

    if emi_options:
        recommended = ds.get("recommended_plan", "7_years")
        rate = ds.get("annual_interest_rate", 10.5)

        elements.append(Paragraph(f"EMI Options (@ {rate}% p.a.)", section_style))

        emi_data = [["Tenure", "Monthly EMI", "Note"]]
        for key, emi_val in emi_options.items():
            label = key.replace("_", " ").title()
            note = "★ Recommended" if key == recommended else ""
            emi_data.append([label, _format_currency(emi_val), note])

        emi_table = Table(emi_data, colWidths=[120, 200, 150])
        emi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0ea5e9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f1f5f9")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#f1f5f9")]),
        ]))
        elements.append(emi_table)
        elements.append(Spacer(1, 12))

    # ─── Eligibility ─────────────────────────────────────────────────
    if ds.get("eligibility"):
        elements.append(Paragraph("Eligibility Assessment", section_style))
        status = ds["eligibility"]
        reason = ds.get("reason", "")

        if "high" in status.lower():
            status_color = colors.HexColor("#059669")
        elif "moderate" in status.lower():
            status_color = colors.HexColor("#d97706")
        else:
            status_color = colors.HexColor("#dc2626")

        status_style = ParagraphStyle(
            "StatusStyle", parent=normal_style,
            textColor=status_color, fontSize=12, fontName="Helvetica-Bold",
        )
        elements.append(Paragraph(status, status_style))
        elements.append(Paragraph(reason, normal_style))
        elements.append(Spacer(1, 12))

    # ─── Footer ──────────────────────────────────────────────────────
    now = datetime.now().strftime("%d %B %Y, %I:%M %p")
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0"), thickness=0.5))
    elements.append(Paragraph(f"Generated on {now}", footer_style))
    elements.append(Paragraph("KrishiIntel AI — Built by Team KrishiAIIntel", footer_style))

    # Build PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_batch_pdf(invoice_list: List[Dict]) -> bytes:
    """
    Generate a batch PDF by creating individual invoice PDFs and merging them.

    Args:
        invoice_list: list of dicts, each with 'fields', 'decision_support' (optional), 'doc_id'

    Returns PDF content as bytes.
    Raises RuntimeError if dependencies are missing.
    """
    if not HAS_REPORTLAB:
        raise RuntimeError("reportlab is not installed. Run: pip install reportlab")
    if not HAS_PYPDF2:
        raise RuntimeError("PyPDF2 is not installed. Run: pip install PyPDF2")

    if not invoice_list:
        raise ValueError("No invoices provided for batch PDF generation.")

    merger = PdfMerger()

    for item in invoice_list:
        fields = item.get("fields", {})
        ds = item.get("decision_support")
        doc_id = item.get("doc_id", "invoice")

        try:
            pdf_bytes = generate_single_pdf(fields, ds, doc_id)
            merger.append(io.BytesIO(pdf_bytes))
        except Exception as e:
            print(f"⚠️  Failed to generate PDF for '{doc_id}': {e}")
            continue

    output_buffer = io.BytesIO()
    merger.write(output_buffer)
    merger.close()

    result = output_buffer.getvalue()
    output_buffer.close()
    return result
