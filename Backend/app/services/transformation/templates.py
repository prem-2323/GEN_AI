"""Deterministic high-fidelity templates for UCKR transformation.

Used when local LLM is offline or in deterministic transformation mode.
Synthesizes structured outputs strictly from UCKR facts, metrics, entities, and actions.
"""
from __future__ import annotations

from typing import Any, Dict, List
from ...models.deliverable import TransformationConfig


def generate_deterministic_deliverable(
    dtype: str,
    uckr: Dict[str, Any],
    cfg: TransformationConfig,
) -> Dict[str, Any]:
    """Deterministically transforms UCKR into standard deliverable format without external LLM."""
    title = uckr.get("title", "Intelligence Knowledge Brief")
    summary = uckr.get("summary", "")
    facts = uckr.get("facts", [])
    entities = uckr.get("entities", [])
    events = uckr.get("events", [])
    metrics = uckr.get("metrics", [])
    actions = uckr.get("actions", [])
    claims = uckr.get("claims", [])

    all_fact_ids = [f.get("factId") for f in facts if f.get("factId")]
    orgs = [e.get("canonicalName") for e in entities if e.get("type") in ("ORGANIZATION", "ENTITY", "THREAT_ACTOR") and e.get("canonicalName")]
    primary_entity = orgs[0] if orgs else "Organization"

    if dtype == "linkedin":
        fact_lines = [f"• {f.get('statement')}" for f in facts[:5] if f.get("statement")]
        body_text = "\n\n".join([
            f"🚨 Executive Intelligence Update: {title}",
            summary or (facts[0].get("statement") if facts else "Key developments and findings summary."),
            "Key Observations:\n" + ("\n".join(fact_lines) if fact_lines else "• Comprehensive analysis conducted."),
            f"Recommended Next Steps: {actions[0].get('action') if actions else 'Review incident logs and maintain monitoring posture.'}",
            "Follow for more intelligence briefings and executive analysis."
        ])
        hashtags = ["#CyberSecurity", "#ThreatIntelligence", "#ExecutiveBriefing", "#RiskManagement"]
        return {
            "title": f"Executive Intelligence: {title}",
            "body": body_text,
            "hashtags": hashtags,
            "usedFactIds": all_fact_ids[:5],
            "citations": []
        }

    elif dtype == "x":
        posts = []
        # Tweet 1: Hook
        posts.append({
            "postNumber": 1,
            "text": f"🧵 1/3 Intelligence Brief: {title}\n\n{summary[:180] if summary else (facts[0].get('statement', '')[:180] if facts else '')}",
            "usedFactIds": all_fact_ids[:1]
        })
        # Tweet 2: Findings & Metrics
        metric_bullets = [f"• {m.get('value')} {m.get('unit')} ({m.get('context')})" for m in metrics[:2] if m.get("value")]
        fact_bullets = [f"• {f.get('statement')}" for f in facts[1:3] if f.get("statement")]
        body_bullets = metric_bullets or fact_bullets or ["• Technical telemetry and observations analyzed."]
        posts.append({
            "postNumber": 2,
            "text": f"2/3 Key Impact & Findings:\n" + "\n".join(body_bullets[:2]),
            "usedFactIds": all_fact_ids[1:3]
        })
        # Tweet 3: Actions
        action_text = actions[0].get("action") if actions else "Implement enhanced verification safeguards and review audit logs."
        posts.append({
            "postNumber": 3,
            "text": f"3/3 Strategic Actions:\n• {action_text}\n\n#ThreatIntel #Security",
            "usedFactIds": all_fact_ids[3:4]
        })
        return {
            "posts": posts,
            "citations": []
        }

    elif dtype == "executive_summary":
        findings = [f.get("statement") for f in facts[:4] if f.get("statement")] or ["No critical findings reported."]
        risks = []
        for ev in events[:2]:
            risks.append(f"Event identified: {ev.get('eventType')} — {ev.get('description')}")
        if not risks:
            risks = ["Operational disruption and targeted vulnerability exploitation risk."]

        rec_actions = [a.get("action") for a in actions[:3] if a.get("action")]
        if not rec_actions:
            rec_actions = ["Conduct immediate infrastructure and credential review."]

        return {
            "title": f"Executive Briefing: {title}",
            "summary": summary or (facts[0].get("statement") if facts else "Detailed strategic overview of findings."),
            "keyFindings": findings,
            "keyRisks": risks,
            "recommendedActions": rec_actions,
            "usedFactIds": all_fact_ids[:4],
            "citations": []
        }

    elif dtype == "advisory":
        affected = [e.get("canonicalName") for e in entities[:4] if e.get("canonicalName")]
        obs = [f.get("statement") for f in facts[:3] if f.get("statement")]
        recs = [a.get("action") for a in actions[:3] if a.get("action")] or ["Review systems and apply recommended patches."]
        refs = [c.get("statement") for c in claims[:2] if c.get("statement")] or ["Source Intelligence Document"]
        return {
            "title": f"Security Advisory: {title}",
            "severity": "HIGH" if events else "MEDIUM",
            "summary": summary or "Technical advisory outlining detected events, impact metrics, and remediation requirements.",
            "affectedEntities": affected,
            "observations": obs,
            "recommendations": recs,
            "references": refs,
            "usedFactIds": all_fact_ids[:3]
        }

    elif dtype == "infographic":
        sections = [
            {
                "heading": "Context & Discovery",
                "content": summary or (facts[0].get("statement") if facts else "Core context and telemetry.")
            },
            {
                "heading": "Observed Findings",
                "content": " ".join([f.get("statement", "") for f in facts[1:3] if f.get("statement")]) or "Telemetry validated."
            }
        ]
        key_numbers = []
        for m in metrics[:3]:
            key_numbers.append({
                "value": m.get("value"),
                "label": f"{m.get('unit')} {m.get('context')}".strip() or m.get("name", "Metric")
            })
        if not key_numbers:
            key_numbers.append({"value": len(facts), "label": "Key Facts Analyzed"})

        return {
            "title": f"Infographic Overview: {title}",
            "sections": sections,
            "keyNumbers": key_numbers,
            "usedFactIds": all_fact_ids[:3]
        }

    elif dtype == "presentation":
        slides = [
            {
                "slideNumber": 1,
                "title": f"Executive Overview: {title}",
                "bullets": [summary[:120] if summary else "Comprehensive intelligence briefing", f"Analyzed for: {cfg.audience} audience"],
                "usedFactIds": all_fact_ids[:1]
            },
            {
                "slideNumber": 2,
                "title": "Key Findings & Metrics",
                "bullets": [f.get("statement") for f in facts[:3] if f.get("statement")] or ["Telemetry recorded."],
                "usedFactIds": all_fact_ids[:3]
            },
            {
                "slideNumber": 3,
                "title": "Recommended Action Plan",
                "bullets": [a.get("action") for a in actions[:3] if a.get("action")] or ["Maintain proactive monitoring."],
                "usedFactIds": all_fact_ids[3:4]
            }
        ]
        return {
            "title": f"Presentation Deck: {title}",
            "slides": slides
        }

    elif dtype == "video_script":
        scenes = [
            {
                "sceneNumber": 1,
                "durationSeconds": 15,
                "narration": f"Welcome to this intelligence briefing on {title}. Here is what you need to know.",
                "visualDescription": "High-tech animated title card with threat radar animation and document metadata.",
                "usedFactIds": all_fact_ids[:1]
            },
            {
                "sceneNumber": 2,
                "durationSeconds": 25,
                "narration": " ".join([f.get("statement", "") for f in facts[:2] if f.get("statement")]) or "Key findings and metrics were recorded.",
                "visualDescription": "Motion graphics displaying impact numbers and timeline telemetry.",
                "usedFactIds": all_fact_ids[:2]
            },
            {
                "sceneNumber": 3,
                "durationSeconds": 20,
                "narration": f"In conclusion, the primary recommendation is to {actions[0].get('action') if actions else 'remain vigilant and conduct audit reviews'}.",
                "visualDescription": "Checklist animation of recommended actions followed by closing brand slide.",
                "usedFactIds": all_fact_ids[2:3]
            }
        ]
        return {
            "title": f"Explainer Video Script: {title}",
            "durationSeconds": 60,
            "scenes": scenes
        }

    # Fallback default
    return {
        "title": title,
        "summary": summary,
        "usedFactIds": all_fact_ids[:3]
    }
