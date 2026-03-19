"""
PDF Report Generator for KrishiIntel AI
Generates clean, professional invoice analysis reports.
Uses only standard library + lightweight HTML-to-PDF approach.
"""

import os
import json
import tempfile
from typing import Dict, Any, Optional
from datetime import datetime


def _format_currency(value) -> str:
    """Format number as Indian currency."""
    if value is None:
        return "N/A"
    try:
        val = float(value)
        # Indian number formatting
        if val >= 10000000:
            return f"₹{val / 10000000:.2f} Cr"
        elif val >= 100000:
            return f"₹{val / 100000:.2f} L"
        else:
            return f"₹{val:,.0f}"
    except (ValueError, TypeError):
        return "N/A"


def generate_report_html(
    fields: Dict[str, Any],
    decision_support: Optional[Dict] = None,
    doc_id: str = "invoice",
) -> str:
    """
    Generate an HTML report for a single invoice analysis.
    Returns HTML string that can be rendered or saved.
    """
    ds = decision_support.get("decision_support", {}) if decision_support else {}
    emi_options = ds.get("emi_options", {})
    now = datetime.now().strftime("%d %B %Y, %I:%M %p")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KrishiIntel AI — Invoice Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f8fafc;
            color: #1e293b;
            padding: 40px;
            max-width: 800px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            padding-bottom: 24px;
            border-bottom: 3px solid #0ea5e9;
            margin-bottom: 32px;
        }}
        .header h1 {{
            font-size: 28px;
            font-weight: 800;
            color: #0369a1;
            letter-spacing: -0.5px;
        }}
        .header .subtitle {{
            font-size: 13px;
            color: #64748b;
            margin-top: 4px;
        }}
        .header .doc-id {{
            display: inline-block;
            margin-top: 12px;
            background: #e0f2fe;
            color: #0369a1;
            padding: 4px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        .section {{
            margin-bottom: 28px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 700;
            color: #0369a1;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e2e8f0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .field-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }}
        .field {{
            background: #f1f5f9;
            border-radius: 10px;
            padding: 14px 18px;
            border-left: 3px solid #0ea5e9;
        }}
        .field .label {{
            font-size: 10px;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 4px;
        }}
        .field .value {{
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
        }}
        .emi-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 12px;
        }}
        .emi-card {{
            background: #f1f5f9;
            border-radius: 10px;
            padding: 16px;
            text-align: center;
            border: 2px solid transparent;
        }}
        .emi-card.recommended {{
            border-color: #0ea5e9;
            background: #e0f2fe;
        }}
        .emi-card .tenure {{
            font-size: 11px;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .emi-card .amount {{
            font-size: 20px;
            font-weight: 700;
            color: #1e293b;
            margin: 6px 0 2px;
        }}
        .emi-card .per-month {{
            font-size: 10px;
            color: #94a3b8;
        }}
        .emi-card .badge {{
            display: inline-block;
            background: #0ea5e9;
            color: white;
            font-size: 9px;
            font-weight: 700;
            padding: 2px 10px;
            border-radius: 10px;
            margin-top: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .eligibility {{
            padding: 16px 20px;
            border-radius: 10px;
            margin-top: 12px;
        }}
        .eligibility.high {{ background: #ecfdf5; border-left: 4px solid #10b981; }}
        .eligibility.moderate {{ background: #fffbeb; border-left: 4px solid #f59e0b; }}
        .eligibility.review {{ background: #fef2f2; border-left: 4px solid #ef4444; }}
        .eligibility .status {{
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 6px;
        }}
        .eligibility.high .status {{ color: #059669; }}
        .eligibility.moderate .status {{ color: #d97706; }}
        .eligibility.review .status {{ color: #dc2626; }}
        .eligibility .reason {{
            font-size: 12px;
            color: #64748b;
            line-height: 1.5;
        }}
        .detection-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }}
        .detection {{
            background: #f1f5f9;
            border-radius: 10px;
            padding: 12px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .detection .label {{ font-size: 13px; font-weight: 600; }}
        .detection .badge-yes {{
            background: #dcfce7; color: #16a34a;
            padding: 3px 12px; border-radius: 12px;
            font-size: 11px; font-weight: 700;
        }}
        .detection .badge-no {{
            background: #f1f5f9; color: #94a3b8;
            padding: 3px 12px; border-radius: 12px;
            font-size: 11px; font-weight: 700;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            font-size: 11px;
            color: #94a3b8;
        }}
        .footer strong {{ color: #64748b; }}
        @media print {{
            body {{ padding: 20px; }}
            .section {{ page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>KrishiIntel AI</h1>
        <div class="subtitle">Invoice Analysis Report</div>
        <div class="doc-id">{doc_id}</div>
    </div>

    <div class="section">
        <div class="section-title">Extracted Invoice Fields</div>
        <div class="field-grid">
            <div class="field">
                <div class="label">Dealer Name</div>
                <div class="value">{fields.get('dealer_name', 'N/A')}</div>
            </div>
            <div class="field">
                <div class="label">Tractor Model</div>
                <div class="value">{fields.get('model_name', 'N/A')}</div>
            </div>
            <div class="field">
                <div class="label">Horse Power</div>
                <div class="value">{fields.get('horse_power', 'N/A')} HP</div>
            </div>
            <div class="field">
                <div class="label">Asset Cost</div>
                <div class="value">{_format_currency(fields.get('asset_cost'))}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Document Verification</div>
        <div class="detection-grid">
            <div class="detection">
                <span class="label">Signature</span>
                <span class="{'badge-yes' if fields.get('signature', {}).get('present') else 'badge-no'}">
                    {'✓ Detected' if fields.get('signature', {}).get('present') else '— Not Found'}
                </span>
            </div>
            <div class="detection">
                <span class="label">Stamp</span>
                <span class="{'badge-yes' if fields.get('stamp', {}).get('present') else 'badge-no'}">
                    {'✓ Detected' if fields.get('stamp', {}).get('present') else '— Not Found'}
                </span>
            </div>
        </div>
    </div>"""

    # EMI section (only if decision support data exists)
    if emi_options:
        recommended = ds.get("recommended_plan", "7_years")
        rate = ds.get("annual_interest_rate", 10.5)

        html += f"""
    <div class="section">
        <div class="section-title">EMI Options (@ {rate}% p.a.)</div>
        <div class="emi-grid">"""

        for key, emi_val in emi_options.items():
            label = key.replace("_", " ").title()
            is_rec = key == recommended
            card_class = "emi-card recommended" if is_rec else "emi-card"
            badge = '<div class="badge">★ Recommended</div>' if is_rec else ""
            html += f"""
            <div class="{card_class}">
                <div class="tenure">{label}</div>
                <div class="amount">{_format_currency(emi_val)}</div>
                <div class="per-month">per month</div>
                {badge}
            </div>"""

        html += """
        </div>
    </div>"""

    # Eligibility section
    if ds.get("eligibility"):
        status = ds["eligibility"]
        reason = ds.get("reason", "")
        css_class = "high" if "high" in status.lower() else ("moderate" if "moderate" in status.lower() else "review")
        html += f"""
    <div class="section">
        <div class="section-title">Eligibility Assessment</div>
        <div class="eligibility {css_class}">
            <div class="status">{status}</div>
            <div class="reason">{reason}</div>
        </div>
    </div>"""

    html += f"""
    <div class="footer">
        <p>Generated on {now}</p>
        <p><strong>KrishiIntel AI</strong> — Built by Team KrishiAIIntel</p>
    </div>
</body>
</html>"""

    return html


def save_report(
    fields: Dict[str, Any],
    decision_support: Optional[Dict] = None,
    doc_id: str = "invoice",
    output_dir: str = None,
) -> str:
    """
    Generate and save an HTML report. Returns absolute path to the file.
    """
    html = generate_report_html(fields, decision_support, doc_id)

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="krishiintel_report_")

    os.makedirs(output_dir, exist_ok=True)
    filename = f"KrishiIntel_Report_{doc_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filepath
