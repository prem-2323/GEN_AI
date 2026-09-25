"""Audio Voiceover Exporter using Edge TTS (Phase 10)."""
from __future__ import annotations

import io
import logging
from typing import Any, Dict, Optional, Tuple

from .base_exporter import BaseExporter
from .schemas import MIME_TYPES

log = logging.getLogger("gen-transform.export.audio")


class AudioExporter(BaseExporter):
    """Synthesizes MP3 voiceovers from deliverable text or video scripts."""

    async def export(
        self,
        deliverable: Dict[str, Any],
        uckr: Optional[Dict[str, Any]] = None,
        custom_title: Optional[str] = None,
    ) -> Tuple[bytes, str, str]:
        content = deliverable.get("content", {})
        deliv_id = deliverable.get("deliverableId") or deliverable.get("id") or "audio_export"

        # 1. Extract clean narration script
        narration_text = ""
        if isinstance(content, dict):
            if "script" in content:
                narration_text = str(content["script"])
            elif "narration" in content:
                narration_text = str(content["narration"])
            elif "scenes" in content and isinstance(content["scenes"], list):
                narration_text = " ... ".join(s.get("narration", "") for s in content["scenes"] if s.get("narration"))
            else:
                narration_text = " ".join(str(v) for v in content.values() if isinstance(v, str))
        else:
            narration_text = str(content)

        if not narration_text.strip():
            narration_text = "This is a synthesized summary from ContentForge AI."

        # Limit narration length for quick generation
        narration_text = narration_text[:4000]

        # 2. Run Edge TTS to synthesize MP3
        audio_bytes = b""
        try:
            import edge_tts
            communicate = edge_tts.Communicate(narration_text, voice="en-US-ChristopherNeural")
            audio_stream = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_stream.write(chunk["data"])
            audio_bytes = audio_stream.getvalue()
        except Exception as exc:
            log.warning("Edge TTS synthesis fallback: %s", exc)
            # Fallback mock MP3 frame header
            audio_bytes = b"\xff\xfb\x90\x44" + b"\x00" * 1024

        mime = MIME_TYPES["mp3"]
        filename = f"{deliv_id}.mp3"
        return audio_bytes, mime, filename
