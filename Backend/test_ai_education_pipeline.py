"""Automated full-project test using AI in Education source text.

Generates:
1. LinkedIn Post
2. X (Twitter) Thread
3. Advisory
4. Infographic Summary
5. Executive Summary
6. Presentation Deck & PPTX Export
7. Video Production (Script & Neural Audio)
8. Consistency Engine Audit Validation
"""
import asyncio
import json
import os
import sys
import uuid

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app
from app.services.pptx_generator import create_pptx_presentation
from app.services.tts_service import generate_audio

client = TestClient(app)

SOURCE_TEXT = (
    "Artificial Intelligence (AI) is changing the way students learn and teachers teach. "
    "AI-powered tools can provide personalized learning experiences based on a student's strengths and weaknesses. "
    "They can also help students understand difficult topics, answer questions, and practice lessons. "
    "Teachers can use AI to create learning materials, evaluate assignments, and identify areas where students need additional support. "
    "AI can save time and make education more accessible. "
    "However, AI should be used responsibly. "
    "Students should not depend completely on AI for their studies. "
    "Human teachers, critical thinking, creativity, and communication skills remain important."
)

USER_UID = f"test-user-{uuid.uuid4().hex[:6]}"
PROJECT_ID = f"proj-edu-{uuid.uuid4().hex[:6]}"
SOURCE_ID = f"src-edu-{uuid.uuid4().hex[:6]}"


def main():
    print("================================================================================")
    print("   GEN-TRANSFORM-AI: FULL PROJECT END-TO-END PIPELINE TEST")
    print("================================================================================\n")
    print(f"Source Text Input:\n{SOURCE_TEXT}\n")

    # 1. Health check
    res = client.get("/health")
    print(f"[Step 1] System Health: {res.json()}")

    # 2. Project Creation
    res = client.post(
        "/api/projects",
        headers={"X-User-Uid": USER_UID},
        json={
            "id": PROJECT_ID,
            "name": "AI in Education Transformation Project",
            "description": "Multi-channel content generation on AI in Education",
            "status": "created",
        },
    )
    print(f"[Step 2] Project Created: ID={PROJECT_ID} (HTTP {res.status_code})")

    # 3. Register Source Document
    res = client.post(
        f"/api/projects/{PROJECT_ID}/sources",
        headers={"X-User-Uid": USER_UID},
        json={
            "id": SOURCE_ID,
            "filename": "AI_in_Education_Overview.txt",
            "extractedText": SOURCE_TEXT,
            "status": "ready",
            "pages": 1,
            "chunks": [
                {
                    "chunkId": "chunk_001",
                    "pageNumber": 1,
                    "text": SOURCE_TEXT,
                }
            ],
        },
    )
    print(f"[Step 3] Source Document Ingested: ID={SOURCE_ID} (HTTP {res.status_code})")

    # 4. Run AI Analysis
    res = client.post(
        f"/api/projects/{PROJECT_ID}/sources/{SOURCE_ID}/analysis",
        headers={"X-User-Uid": USER_UID},
        json={"mode": "deterministic"},
    )
    print(f"[Step 4] Source Analysis Done (HTTP {res.status_code})")

    # 5. Build Canonical UCKR
    res = client.post(
        f"/api/projects/{PROJECT_ID}/sources/{SOURCE_ID}/uckr",
        headers={"X-User-Uid": USER_UID},
    )
    uckr_data = res.json().get("uckr", {})
    print(f"[Step 5] Canonical UCKR Constructed (v{uckr_data.get('version')}):")
    print(f"  • Summary: {uckr_data.get('summary')}")
    print(f"  • Facts Extracted: {len(uckr_data.get('facts', []))}")
    print(f"  • Entities: {[e.get('canonicalName') or e.get('name') for e in uckr_data.get('entities', [])]}")
    print(f"  • Metrics: {len(uckr_data.get('metrics', []))}")
    print(f"  • Actions: {[a.get('action') for a in uckr_data.get('actions', [])]}\n")

    # 6. Transform into requested deliverables:
    # linkedin, x (twitter), advisory, infographic, executive_summary, presentation, video_script
    target_types = ["linkedin", "x", "advisory", "infographic", "executive_summary", "presentation", "video_script"]
    res = client.post(
        f"/api/projects/{PROJECT_ID}/transform",
        headers={"X-User-Uid": USER_UID},
        json={
            "sourceId": SOURCE_ID,
            "uckrVersion": 1,
            "outputTypes": target_types,
            "configuration": {
                "audience": "general",
                "tone": "informative",
                "language": "English",
                "detailLevel": "medium",
                "objective": "education",
            },
        },
    )
    print(f"[Step 6] Transformation Complete (HTTP {res.status_code}):")
    deliverables = res.json().get("deliverables", [])
    deliv_by_type = {d["type"]: d for d in deliverables}

    # 7. Run Consistency Engine Validation
    val_res = client.post(
        f"/api/projects/{PROJECT_ID}/sources/{SOURCE_ID}/validate",
        headers={"X-User-Uid": USER_UID},
        json={"uckrVersion": 1},
    )
    val_report = val_res.json()
    scores = val_report.get("scores", {})

    print(f"[Step 7] Consistency Validation Audit:")
    print(f"  • Overall Status: {val_report.get('overallStatus')}")
    print(f"  • Consistency Score: {scores.get('consistency')}%")
    print(f"  • Fact Preservation: {scores.get('factPreservation')}%")
    print(f"  • Citation Coverage: {scores.get('citationCoverage')}%")
    print(f"  • Contradictions Detected: {len(val_report.get('contradictions', []))}")
    print(f"  • Unsupported Claims: {scores.get('unsupportedClaims')}\n")

    # 8. PPTX Generation Test
    pres_content = deliv_by_type.get("presentation", {}).get("content", {})
    pptx_slides = []
    if "slides" in pres_content:
        for s in pres_content["slides"]:
            pptx_slides.append({
                "slide_number": s.get("slideNumber", 1),
                "title": s.get("title", "Slide"),
                "layout": "bullet_points",
                "content": s.get("bullets", []),
                "speaker_notes": "Key educational takeaway on AI integration.",
            })
    deck_data = {
        "presentation_title": pres_content.get("title", "AI in Education"),
        "subtitle": "Personalized Learning & Responsible AI Implementation",
        "theme": "spotify_emerald",
        "slides": pptx_slides or [
            {
                "slide_number": 1,
                "title": "AI in Education",
                "layout": "title",
                "subtitle": "Transforming Learning and Teaching",
                "content": [],
            }
        ]
    }
    pptx_stream = create_pptx_presentation(deck_data, theme_name="spotify_emerald")
    os.makedirs("outputs", exist_ok=True)
    pptx_path = os.path.join("outputs", "AI_in_Education_Presentation.pptx")
    with open(pptx_path, "wb") as f:
        f.write(pptx_stream.getvalue())
    print(f"[Step 8] PPTX Presentation Deck Exported -> {pptx_path} ({len(pptx_stream.getvalue())} bytes)")

    # 9. Video Audio TTS Production Test
    video_content = deliv_by_type.get("video_script", {}).get("content", {})
    audio_path = os.path.join("outputs", "AI_in_Education_Narration.mp3")
    narration_lines = []
    for scene in video_content.get("scenes", []):
        if scene.get("narration"):
            narration_lines.append(scene["narration"])
    full_narration = " ".join(narration_lines) or SOURCE_TEXT

    asyncio.run(generate_audio(
        text=full_narration,
        output_file=audio_path,
        voice="en-US-JennyNeural"
    ))
    audio_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
    print(f"[Step 9] Video Narration Audio Exported -> {audio_path} ({audio_size} bytes)\n")

    # Output detailed results JSON to inspect
    result_dump = {
        "sourceText": SOURCE_TEXT,
        "uckr": uckr_data,
        "deliverables": deliv_by_type,
        "validation": val_report,
        "exports": {
            "pptx": pptx_path,
            "audio": audio_path,
        }
    }
    dump_path = os.path.join("outputs", "full_test_results.json")
    with open(dump_path, "w", encoding="utf-8") as f:
        json.dump(result_dump, f, indent=2, ensure_ascii=False)
    print(f"Full result JSON written to {dump_path}")


if __name__ == "__main__":
    main()
