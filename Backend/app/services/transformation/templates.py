from __future__ import annotations

import re
from typing import Any, Dict, List
from ...models.deliverable import TransformationConfig


def _detect_domain(text: str) -> str:
    low = text.lower()
    if any(w in low for w in ("student", "teacher", "learn", "curriculum", "school", "academic", "education", "lesson", "grade")):
        return "education"
    if any(w in low for w in ("vulnerability", "cve-", "malware", "ransomware", "threat actor", "phishing", "exploit", "breach")):
        return "cybersecurity"
    if any(w in low for w in ("patient", "clinical", "diagnosis", "therapy", "medical", "hospital")):
        return "healthcare"
    if any(w in low for w in ("revenue", "ebitda", "fiscal", "portfolio", "banking", "shares", "dividend")):
        return "finance"
    if any(w in low for w in ("software", "api", "database", "cloud", "backend", "frontend", "architecture")):
        return "technology"
    return "general"


def generate_deterministic_deliverable(
    dtype: str,
    uckr: Dict[str, Any],
    cfg: TransformationConfig,
) -> Dict[str, Any]:
    """Deterministically transforms UCKR into standard deliverable format without external LLM."""
    title = uckr.get("title", "Strategic Briefing")
    summary = uckr.get("summary", "")
    facts = uckr.get("facts", [])
    entities = uckr.get("entities", [])
    events = uckr.get("events", [])
    metrics = uckr.get("metrics", [])
    actions = uckr.get("actions", [])
    claims = uckr.get("claims", [])

    all_fact_ids = [f.get("factId") for f in facts if f.get("factId")]
    combined_text = f"{title} {summary} " + " ".join([f.get("statement", "") for f in facts])
    domain = _detect_domain(combined_text)

    if dtype == "linkedin":
        fact_lines = [f"• {f.get('statement')}" for f in facts[:6] if f.get("statement")]
        rec_text = actions[0].get('action') if actions else 'Adopt responsible integration practices and maintain strategic oversight.'
        body_text = "\n\n".join([
            f"🚨 Strategic Update: {title}",
            summary or (facts[0].get("statement") if facts else "Key developments and findings summary."),
            "Key Insights:\n" + ("\n".join(fact_lines) if fact_lines else "• Comprehensive analysis conducted."),
            f"Recommended Next Steps: {rec_text}",
            "How is your team navigating this transition? Share your perspectives below."
        ])
        if domain == "education":
            hashtags = ["#AI", "#EdTech", "#FutureOfLearning", "#EducationLeadership", "#Innovation"]
        elif domain == "cybersecurity":
            hashtags = ["#CyberSecurity", "#ThreatIntelligence", "#ExecutiveBriefing", "#RiskManagement"]
        else:
            hashtags = ["#ArtificialIntelligence", "#Leadership", "#Innovation", "#StrategicPlanning"]

        return {
            "title": f"Strategic Analysis: {title}",
            "body": body_text,
            "hashtags": hashtags,
            "usedFactIds": all_fact_ids[:6],
            "citations": []
        }

    elif dtype == "x":
        posts = []
        posts.append({
            "postNumber": 1,
            "text": f"🧵 1/3 Overview: {title}\n\n{summary[:180] if summary else (facts[0].get('statement', '')[:180] if facts else '')}",
            "usedFactIds": all_fact_ids[:1]
        })
        metric_bullets = [f"• {m.get('value')} {m.get('unit')} ({m.get('context')})" for m in metrics[:2] if m.get("value")]
        fact_bullets = [f"• {f.get('statement')}" for f in facts[1:4] if f.get("statement")]
        body_bullets = metric_bullets or fact_bullets or ["• Core observations and factual claims analyzed."]
        posts.append({
            "postNumber": 2,
            "text": f"2/3 Key Insights & Capabilities:\n" + "\n".join(body_bullets[:2]),
            "usedFactIds": all_fact_ids[1:3]
        })
        action_text = actions[0].get("action") if actions else "Implement structured guidance and preserve core human competencies."
        tag_suffix = "#EdTech #AI" if domain == "education" else "#AI #Innovation"
        posts.append({
            "postNumber": 3,
            "text": f"3/3 Strategic Next Steps:\n• {action_text}\n\n{tag_suffix}",
            "usedFactIds": all_fact_ids[3:5]
        })
        return {
            "posts": posts,
            "citations": []
        }

    elif dtype == "executive_summary":
        findings = [f.get("statement") for f in facts[:5] if f.get("statement")] or ["No critical findings reported."]
        risks = []
        for f in facts:
            if re.search(r"\b(risk|depend|over-relian|threat|loss|fail)\b", f.get("statement", ""), re.I):
                risks.append(f.get("statement"))
        if not risks:
            risks = ["Ensure responsible adoption and avoid total dependency on automated systems."]

        rec_actions = [a.get("action") for a in actions[:3] if a.get("action")]
        if not rec_actions:
            rec_actions = ["Establish clear institutional policies and support human stakeholders."]

        return {
            "title": f"Executive Briefing: {title}",
            "summary": summary or (facts[0].get("statement") if facts else "Detailed strategic overview of findings."),
            "keyFindings": findings,
            "keyRisks": risks,
            "recommendedActions": rec_actions,
            "usedFactIds": all_fact_ids[:5],
            "citations": []
        }

    elif dtype == "advisory":
        affected = [e.get("canonicalName") for e in entities[:4] if e.get("canonicalName")]
        obs = [f.get("statement") for f in facts[:4] if f.get("statement")]
        recs = [a.get("action") for a in actions[:3] if a.get("action")] or ["Adopt recommended guidelines and maintain responsible oversight."]
        refs = [c.get("statement") for c in claims[:2] if c.get("statement")] or ["Institutional Governance Standards", "Responsible AI Framework"]
        
        advisory_title = f"Advisory Brief: {title}" if domain != "cybersecurity" else f"Security Advisory: {title}"
        return {
            "title": advisory_title,
            "domain": domain,
            "severity": "MEDIUM",
            "summary": summary or "Strategic advisory outlining key observations, responsible considerations, and recommended actions.",
            "affectedEntities": affected,
            "observations": obs,
            "recommendations": recs,
            "references": refs,
            "usedFactIds": all_fact_ids[:4]
        }

    elif dtype == "infographic":
        sections = [
            {
                "heading": "Context & Overview",
                "content": summary or (facts[0].get("statement") if facts else "Core context and analysis.")
            },
            {
                "heading": "Key Capabilities & Observations",
                "content": " ".join([f.get("statement", "") for f in facts[1:4] if f.get("statement")]) or "Verified claims analyzed."
            }
        ]
        key_numbers = []
        for m in metrics[:3]:
            if m.get("value"):
                key_numbers.append({
                    "value": m.get("value"),
                    "label": f"{m.get('unit')} {m.get('context')}".strip() or m.get("name", "Metric")
                })
        if not key_numbers:
            key_numbers.append({"value": str(len(facts)), "label": "Key Claims Mapped"})
            key_numbers.append({"value": "100%", "label": "Source Grounding"})

        return {
            "title": f"Infographic Overview: {title}",
            "sections": sections,
            "keyNumbers": key_numbers,
            "usedFactIds": all_fact_ids[:4]
        }

    elif dtype == "presentation":
        slides = [
            {
                "slideNumber": 1,
                "title": f"Strategic Overview: {title}",
                "bullets": [summary[:120] if summary else "Comprehensive briefing", f"Audience: {cfg.audience} • Tone: {cfg.tone}"],
                "usedFactIds": all_fact_ids[:1]
            },
            {
                "slideNumber": 2,
                "title": "Core Capabilities & Student Impact",
                "bullets": [f.get("statement") for f in facts[1:4] if f.get("statement")] or ["Key learning capabilities highlighted."],
                "usedFactIds": all_fact_ids[1:4]
            },
            {
                "slideNumber": 3,
                "title": "Teacher Augmentation & Efficiency",
                "bullets": [f.get("statement") for f in facts[4:7] if f.get("statement")] or ["Educator workflows augmented."],
                "usedFactIds": all_fact_ids[4:7]
            },
            {
                "slideNumber": 4,
                "title": "Responsible AI & Human Competencies",
                "bullets": [a.get("action") for a in actions[:3] if a.get("action")] or ["Ensure balanced usage and preserve human mentorship."],
                "usedFactIds": all_fact_ids[7:9]
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
                "durationSeconds": 20,
                "narration": f"Welcome to this briefing on {title}. Here is what you need to know.",
                "visualDescription": "Dynamic animated title card with topic overview and key metadata.",
                "usedFactIds": all_fact_ids[:1]
            },
            {
                "sceneNumber": 2,
                "durationSeconds": 25,
                "narration": " ".join([f.get("statement", "") for f in facts[1:4] if f.get("statement")]) or "Key findings and capabilities are presented.",
                "visualDescription": "Motion graphics showcasing core benefits and operational insights.",
                "usedFactIds": all_fact_ids[1:4]
            },
            {
                "sceneNumber": 3,
                "durationSeconds": 15,
                "narration": f"In conclusion, the priority is to {actions[0].get('action') if actions else 'implement responsible adoption and preserve critical skills'}.",
                "visualDescription": "Summary checklist animation followed by closing call to action.",
                "usedFactIds": all_fact_ids[4:6]
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
        "usedFactIds": all_fact_ids[:4]
    }
