"""RFTC Prompt Builder for UCKR to Deliverables Transformation.

Enforces:
ROLE: Specialist content creator / analyst
TASK: Transform canonical UCKR into target output format
REFERENCE: Strictly the provided UCKR knowledge base
TONE: Configured tone
FORMAT: Valid JSON adhering to target schema
CONSTRAINTS: Zero hallucination, no modified numbers/dates, attach usedFactIds.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List
from ...models.deliverable import TransformationConfig


def format_uckr_context(uckr: Dict[str, Any]) -> str:
    """Renders UCKR knowledge items into a compact, structured representation."""
    lines: List[str] = []
    lines.append(f"TITLE: {uckr.get('title', 'Knowledge Brief')}")
    if uckr.get("summary"):
        lines.append(f"SUMMARY: {uckr.get('summary')}")
    lines.append("")

    # Facts
    facts = uckr.get("facts", [])
    lines.append(f"FACTS ({len(facts)} items):")
    for idx, f in enumerate(facts, 1):
        fid = f.get("factId", f"fact_{idx:03d}")
        stmt = f.get("statement", "")
        ftype = f.get("type", "fact")
        lines.append(f"  [{fid}] ({ftype}): {stmt}")
    lines.append("")

    # Entities
    entities = uckr.get("entities", [])
    lines.append(f"ENTITIES ({len(entities)} items):")
    for idx, e in enumerate(entities, 1):
        eid = e.get("entityId", f"entity_{idx:03d}")
        name = e.get("canonicalName", "")
        etype = e.get("type", "ENTITY")
        aliases = e.get("aliases", [])
        alias_str = f" (Aliases: {', '.join(aliases)})" if aliases else ""
        lines.append(f"  [{eid}] {name} ({etype}){alias_str}")
    lines.append("")

    # Events
    events = uckr.get("events", [])
    if events:
        lines.append(f"EVENTS ({len(events)} items):")
        for idx, ev in enumerate(events, 1):
            evid = ev.get("eventId", f"event_{idx:03d}")
            evtype = ev.get("eventType", "EVENT")
            desc = ev.get("description", "")
            date = ev.get("date", "N/A")
            lines.append(f"  [{evid}] {evtype}: {desc} (Date: {date})")
        lines.append("")

    # Metrics
    metrics = uckr.get("metrics", [])
    if metrics:
        lines.append(f"METRICS ({len(metrics)} items):")
        for idx, m in enumerate(metrics, 1):
            mid = m.get("metricId", f"metric_{idx:03d}")
            val = m.get("value", "")
            unit = m.get("unit", "")
            ctx = m.get("context", "")
            lines.append(f"  [{mid}] {val} {unit} — Context: {ctx}")
        lines.append("")

    # Claims
    claims = uckr.get("claims", [])
    if claims:
        lines.append(f"CLAIMS ({len(claims)} items):")
        for idx, c in enumerate(claims, 1):
            cid = c.get("claimId", f"claim_{idx:03d}")
            stmt = c.get("statement", "")
            attr = c.get("attribution", "Source")
            lines.append(f"  [{cid}] {stmt} (Attribution: {attr})")
        lines.append("")

    # Actions
    actions = uckr.get("actions", [])
    if actions:
        lines.append(f"ACTIONS ({len(actions)} items):")
        for idx, a in enumerate(actions, 1):
            aid = a.get("actionId", f"action_{idx:03d}")
            act = a.get("action", "")
            actor = a.get("actor", "")
            status = a.get("status", "RECOMMENDED")
            lines.append(f"  [{aid}] {act} (Actor: {actor}, Status: {status})")
        lines.append("")

    # Relationships
    relationships = uckr.get("relationships", [])
    if relationships:
        lines.append(f"RELATIONSHIPS ({len(relationships)} items):")
        for idx, r in enumerate(relationships, 1):
            rid = r.get("relationshipId", f"rel_{idx:03d}")
            src = r.get("sourceEntityId", "")
            rel = r.get("relationshipType", "RELATED_TO")
            tgt = r.get("targetEntityId", "")
            lines.append(f"  [{rid}] {src} -> {rel} -> {tgt}")
        lines.append("")

    return "\n".join(lines)


def get_schema_for_type(dtype: str) -> str:
    """Returns the JSON schema specification for the given deliverable type."""
    if dtype == "linkedin":
        return json.dumps({
            "title": "Concise post headline",
            "body": "Multi-paragraph post formatted for LinkedIn with spacing and bullet points",
            "hashtags": ["#CyberSecurity", "#ThreatIntel"],
            "usedFactIds": ["fact_001", "fact_002"]
        }, indent=2)
    elif dtype == "x":
        return json.dumps({
            "posts": [
                {
                    "postNumber": 1,
                    "text": "1/3 First tweet in thread containing key hook and findings...",
                    "usedFactIds": ["fact_001"]
                },
                {
                    "postNumber": 2,
                    "text": "2/3 Second tweet detailing impact metrics...",
                    "usedFactIds": ["fact_002"]
                },
                {
                    "postNumber": 3,
                    "text": "3/3 Concluding takeaways and recommendations...",
                    "usedFactIds": []
                }
            ]
        }, indent=2)
    elif dtype == "executive_summary":
        return json.dumps({
            "title": "Executive Summary Title",
            "summary": "High-level strategic briefing paragraph",
            "keyFindings": ["Finding 1 with exact numbers", "Finding 2"],
            "keyRisks": ["Strategic risk 1", "Operational risk 2"],
            "recommendedActions": ["Immediate mitigation step 1", "Strategic policy change 2"],
            "usedFactIds": ["fact_001", "fact_002"]
        }, indent=2)
    elif dtype == "advisory":
        return json.dumps({
            "title": "Security / Technical Advisory Title",
            "severity": "HIGH",  # CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN
            "summary": "Technical overview of the advisory",
            "affectedEntities": ["System A", "Product B"],
            "observations": ["Technical observation 1", "Technical observation 2"],
            "recommendations": ["Remediation step 1", "Patch requirement 2"],
            "references": ["CVE-2026-4418", "Source Document Ref"],
            "usedFactIds": ["fact_001", "fact_002"]
        }, indent=2)
    elif dtype == "infographic":
        return json.dumps({
            "title": "Infographic Title",
            "sections": [
                {"heading": "Incident Overview", "content": "Key context..."},
                {"heading": "Impact Assessment", "content": "Detailed impact metrics..."}
            ],
            "keyNumbers": [
                {"value": 240, "label": "Employees targeted"},
                {"value": "100%", "label": "Containment rate"}
            ],
            "usedFactIds": ["fact_001", "fact_002"]
        }, indent=2)
    elif dtype == "presentation":
        return json.dumps({
            "title": "Presentation Deck Title",
            "slides": [
                {
                    "slideNumber": 1,
                    "title": "Executive Overview",
                    "bullets": ["Point 1", "Point 2"],
                    "usedFactIds": ["fact_001"]
                },
                {
                    "slideNumber": 2,
                    "title": "Key Findings & Metrics",
                    "bullets": ["Finding 1", "Finding 2"],
                    "usedFactIds": ["fact_002"]
                },
                {
                    "slideNumber": 3,
                    "title": "Recommended Action Plan",
                    "bullets": ["Action 1", "Action 2"],
                    "usedFactIds": []
                }
            ]
        }, indent=2)
    elif dtype == "video_script":
        return json.dumps({
            "title": "Video Explainer Script Title",
            "durationSeconds": 60,
            "scenes": [
                {
                    "sceneNumber": 1,
                    "durationSeconds": 15,
                    "narration": "Spoken dialogue for scene 1...",
                    "visualDescription": "Motion graphic showing threat landscape and stats...",
                    "usedFactIds": ["fact_001"]
                },
                {
                    "sceneNumber": 2,
                    "durationSeconds": 25,
                    "narration": "Spoken dialogue for scene 2...",
                    "visualDescription": "Infographic callout highlighting 240 affected accounts...",
                    "usedFactIds": ["fact_002"]
                },
                {
                    "sceneNumber": 3,
                    "durationSeconds": 20,
                    "narration": "Concluding call to action...",
                    "visualDescription": "Closing title slide with advisory links...",
                    "usedFactIds": []
                }
            ]
        }, indent=2)
    return "{}"


def build_transformation_prompt(
    dtype: str,
    uckr: Dict[str, Any],
    cfg: TransformationConfig,
) -> str:
    """Builds a complete, rigorous RFTC prompt for the LLM."""
    context = format_uckr_context(uckr)
    schema = get_schema_for_type(dtype)

    prompt = f"""[ROLE]
You are a senior communications and intelligence transformation specialist. Your mission is to generate professional {dtype.upper()} deliverables derived EXCLUSIVELY from the canonical Unified Content Knowledge Representation (UCKR) provided below.

[TASK]
Generate a complete, high-quality '{dtype}' output matching the user's configuration parameters:
- Audience: {cfg.audience}
- Tone: {cfg.tone}
- Language: {cfg.language}
- Detail Level: {cfg.detailLevel}
- Objective: {cfg.objective}

[REFERENCE KNOWLEDGE (CANONICAL UCKR)]
{context}

[CONSTRAINTS]
1. ZERO HALLUCINATIONS: Use ONLY facts, entities, events, metrics, claims, and actions explicitly stated in the UCKR above. Do not extrapolate, assume, or invent details.
2. PRESERVE NUMBERS & DATES: Do not change 240 into 'over 200' or alter dates/version numbers.
3. GROUNDED PROVENANCE: Every fact used MUST include its exact fact ID (e.g. "fact_001", "fact_002") in the `usedFactIds` list.
4. JSON FORMAT ONLY: Output ONLY valid, parsable JSON matching the schema below. Do not wrap in conversational preamble.

[TARGET JSON SCHEMA]
```json
{schema}
```
"""
    return prompt
