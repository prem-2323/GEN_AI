"""PDF Document Exporter using ReportLab (Phase 10)."""
from __future__ import annotations

import io
from typing import Any, Dict, Optional, Tuple
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER

from .base_exporter import BaseExporter
from .schemas import MIME_TYPES


class PDFExporter(BaseExporter):
    """Generates high-resolution PDF documents from deliverable content using ReportLab."""

    async def export(
        self,
        deliverable: Dict[str, Any],
        uckr: Optional[Dict[str, Any]] = None,
        custom_title: Optional[str] = None,
    ) -> Tuple[bytes, str, str]:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            rightMargin=45,
            leftMargin=45,
            topMargin=45,
            bottomMargin=45,
        )

        dtype = deliverable.get("type", "executive_summary").replace("_", " ").title()
        title = custom_title or deliverable.get("title") or f"{dtype} Report"
        content = deliverable.get("content", {})
        deliv_id = deliverable.get("deliverableId") or deliverable.get("id") or "export"

        styles = getSampleStyleSheet()
        
        # Custom styles
        header_style = ParagraphStyle(
            "BrandHeader",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748b"),
            alignment=TA_RIGHT,
        )
        title_style = ParagraphStyle(
            "MainTitle",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            "SubTitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
            spaceAfter=12,
        )
        section_style = ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=12,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
        )
        bullet_style = ParagraphStyle(
            "Bullet",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#334155"),
            leftIndent=15,
            spaceAfter=3,
        )

        elements = []

        # 1. Branding Header
        elements.append(Paragraph("CONTENTFORGE AI  |  ENTERPRISE KNOWLEDGE TRANSFORMATION", header_style))
        elements.append(Spacer(1, 10))

        # 2. Title & Metadata
        elements.append(Paragraph(title, title_style))
        elements.append(Paragraph(f"Deliverable Type: <b>{dtype}</b>  •  Artifact ID: <font face='Courier'>{deliv_id}</font>", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=14))

        # 3. Content
        if isinstance(content, dict):
            for key, val in content.items():
                sec_name = str(key).replace("_", " ").title()
                elements.append(Paragraph(sec_name, section_style))
                
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict):
                            txt = " &bull; " + ", ".join(f"<b>{k}:</b> {v}" for k, v in item.items())
                            elements.append(Paragraph(txt, bullet_style))
                        else:
                            elements.append(Paragraph(f"&bull; {item}", bullet_style))
                elif isinstance(val, dict):
                    for subk, subv in val.items():
                        elements.append(Paragraph(f"<b>{str(subk).title()}:</b> {subv}", body_style))
                else:
                    elements.append(Paragraph(str(val), body_style))
                elements.append(Spacer(1, 4))
        elif isinstance(content, list):
            for item in content:
                elements.append(Paragraph(f"&bull; {item}", bullet_style))
        else:
            elements.append(Paragraph(str(content), body_style))

        # 4. UCKR Grounding Table
        if uckr and uckr.get("facts"):
            elements.append(Spacer(1, 14))
            elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=10))
            elements.append(Paragraph("Verified UCKR Grounding & Evidence", section_style))
            
            table_data = [["Fact ID", "Verified Knowledge Fact", "Confidence"]]
            for f in (uckr.get("facts") or [])[:8]:
                fid = str(f.get("factId") or f.get("id", "fact"))
                val = str(f.get("value") or f.get("text", ""))[:120]
                conf = f"{float(f.get('confidence', 0.98))*100:.0f}%"
                table_data.append([
                    Paragraph(f"<font face='Courier' size=8>{fid}</font>", body_style),
                    Paragraph(val, ParagraphStyle("TblBody", parent=body_style, fontSize=8.5, leading=11)),
                    Paragraph(conf, ParagraphStyle("TblConf", parent=body_style, fontSize=8.5, alignment=TA_CENTER)),
                ])

            t = Table(table_data, colWidths=[70, 380, 70])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ]))
            elements.append(t)

        doc.build(elements)
        data = buf.getvalue()
        mime = MIME_TYPES["pdf"]
        filename = f"{deliv_id}.pdf"

        return data, mime, filename
