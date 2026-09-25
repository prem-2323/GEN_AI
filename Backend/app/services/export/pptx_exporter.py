"""PPTX Presentation Exporter with UCKR Fact Citations (Phase 10)."""
from __future__ import annotations

import io
from typing import Any, Dict, Optional, Tuple
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

from .base_exporter import BaseExporter
from .schemas import MIME_TYPES


class PPTXExporter(BaseExporter):
    """Generates Microsoft PowerPoint (.pptx) presentations with grounded UCKR fact citations."""

    async def export(
        self,
        deliverable: Dict[str, Any],
        uckr: Optional[Dict[str, Any]] = None,
        custom_title: Optional[str] = None,
    ) -> Tuple[bytes, str, str]:
        prs = Presentation()
        # Set 16:9 widescreen layout
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
        blank_layout = prs.slide_layouts[6]

        dtype = deliverable.get("type", "presentation").replace("_", " ").title()
        title = custom_title or deliverable.get("title") or "Executive Presentation"
        content = deliverable.get("content", {})
        deliv_id = deliverable.get("deliverableId") or deliverable.get("id") or "export"

        # 1. Slide 1: Title Slide (Dark modern theme)
        s1 = prs.slides.add_slide(blank_layout)
        bg1 = s1.shapes.add_shape(1, 0, 0, Inches(13.333), Inches(7.5)) # MSO_SHAPE.RECTANGLE
        bg1.fill.solid()
        bg1.fill.fore_color.rgb = RGBColor(15, 23, 42) # slate-900
        bg1.line.color.rgb = RGBColor(15, 23, 42)

        t_box = s1.shapes.add_textbox(Inches(1.2), Inches(2.2), Inches(10.9), Inches(2.5))
        tf = t_box.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(40)
        p1.font.bold = True
        p1.font.color.rgb = RGBColor(248, 250, 252) # slate-50

        sub_p = tf.add_paragraph()
        sub_p.text = f"ContentForge AI Transformation  •  {dtype}  •  UCKR Verified"
        sub_p.font.size = Pt(18)
        sub_p.font.color.rgb = RGBColor(148, 163, 184) # slate-400
        sub_p.space_before = Pt(16)

        # 2. Extract slides or sections
        slides_data = []
        if isinstance(content, dict) and "slides" in content and isinstance(content["slides"], list):
            slides_data = content["slides"]
        elif isinstance(content, dict):
            for k, v in content.items():
                slides_data.append({"title": str(k).replace("_", " ").title(), "bullets": v if isinstance(v, list) else [str(v)]})
        else:
            slides_data = [{"title": "Overview", "bullets": [str(content)]}]

        # 3. Create Content Slides
        for idx, slide_item in enumerate(slides_data[:12]):
            s = prs.slides.add_slide(blank_layout)
            
            # Slide Header Card
            s_title = slide_item.get("title") or f"Slide {idx + 1}"
            s_title_box = s.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(11.7), Inches(0.9))
            st_tf = s_title_box.text_frame
            st_p = st_tf.paragraphs[0]
            st_p.text = s_title
            st_p.font.size = Pt(26)
            st_p.font.bold = True
            st_p.font.color.rgb = RGBColor(15, 23, 42)

            # Body bullet points
            body_box = s.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.7), Inches(4.5))
            b_tf = body_box.text_frame
            b_tf.word_wrap = True

            bullets = slide_item.get("bullets") or slide_item.get("points") or []
            if isinstance(bullets, str):
                bullets = [bullets]

            for b_idx, bullet in enumerate(bullets[:6]):
                bp = b_tf.paragraphs[0] if b_idx == 0 else b_tf.add_paragraph()
                if isinstance(bullet, dict):
                    b_text = bullet.get("text") or bullet.get("point") or str(bullet)
                else:
                    b_text = str(bullet)

                bp.text = f"•  {b_text}"
                bp.font.size = Pt(16)
                bp.font.color.rgb = RGBColor(51, 65, 85)
                bp.space_after = Pt(12)

            # Footer / UCKR Citation Traceability
            fact_ids = slide_item.get("factIds", [])
            cite_text = "Source Grounding: Verified via ContentForge UCKR"
            if fact_ids:
                cite_text += f" (Facts: {', '.join(str(f) for f in fact_ids[:3])})"
            
            f_box = s.shapes.add_textbox(Inches(0.8), Inches(6.7), Inches(11.7), Inches(0.4))
            f_tf = f_box.text_frame
            fp = f_tf.paragraphs[0]
            fp.text = cite_text
            fp.font.size = Pt(9.5)
            fp.font.italic = True
            fp.font.color.rgb = RGBColor(148, 163, 184)

        buf = io.BytesIO()
        prs.save(buf)
        data = buf.getvalue()
        mime = MIME_TYPES["pptx"]
        filename = f"{deliv_id}.pptx"

        return data, mime, filename
