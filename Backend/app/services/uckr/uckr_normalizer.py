"""Normalization and standard categorization engine for UCKR items."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
from ...models.uckr import Action, Claim, Event, Metric, SourceRef

_EVENT_TYPES = {
    "attack": "CYBER_ATTACK",
    "ransomware": "CYBER_ATTACK",
    "phishing": "CYBER_ATTACK",
    "breach": "INCIDENT",
    "incident": "INCIDENT",
    "detected": "DETECTION",
    "discovery": "DISCOVERY",
    "announced": "ANNOUNCEMENT",
    "launch": "LAUNCH",
    "policy": "POLICY_CHANGE",
    "response": "RESPONSE",
    "meeting": "MEETING",
    "research": "RESEARCH",
}


def normalize_events(
    raw_events: List[Any],
    source_id: str,
    page_texts: Dict[int, str],
) -> List[Event]:
    """Normalizes events into standardized event types with grounded citations."""
    events: List[Event] = []

    for idx, item in enumerate(raw_events, start=1):
        if isinstance(item, dict):
            desc = (item.get("description") or item.get("event") or item.get("title") or item.get("name") or "").strip()
            date_val = item.get("date") or item.get("timestamp") or None
            loc = item.get("location")
            impact = item.get("impact", "")
            actors = item.get("actors") or item.get("participants") or []
            conf = float(item.get("confidence", 0.95))
        else:
            desc = str(item).strip()
            date_val = None
            loc = None
            impact = ""
            actors = []
            conf = 0.92

        if not desc or len(desc) < 3:
            continue

        # Match event type
        ev_type = "INCIDENT"
        desc_lower = desc.lower()
        for k, v in _EVENT_TYPES.items():
            if k in desc_lower:
                ev_type = v
                break

        page_no = 1
        for pn, ptext in page_texts.items():
            if desc[:40] and desc[:40].lower() in ptext.lower():
                page_no = pn
                break

        eid = f"event_{idx:03d}"
        sref = SourceRef(
            sourceId=source_id,
            chunkId=f"chunk_{page_no:03d}",
            pageNumber=page_no,
            textQuote=desc[:150],
        )

        ev = Event(
            eventId=eid,
            id=eid,
            eventType=ev_type,
            description=desc,
            name=desc,
            title=desc,
            date=str(date_val) if date_val else None,
            timestamp=str(date_val) if date_val else None,
            location=loc,
            impact=impact,
            actors=[str(a) for a in actors],
            participants=[str(a) for a in actors],
            confidence=round(conf, 3),
            sourceRefs=[sref],
        )
        events.append(ev)

    return events


def normalize_metrics(
    raw_metrics: List[Any],
    source_id: str,
    page_texts: Dict[int, str],
) -> List[Metric]:
    """Extracts and standardizes numeric metrics with exact units and context."""
    metrics: List[Metric] = []

    for idx, item in enumerate(raw_metrics, start=1):
        if isinstance(item, dict):
            val = item.get("value", "")
            name = item.get("name") or item.get("context", "") or f"Metric {idx}"
            unit = item.get("unit", "")
            ctx = item.get("context", "")
            date_val = item.get("date")
            conf = float(item.get("confidence", 0.98))
        else:
            val = str(item)
            name = f"Metric {idx}"
            unit = ""
            ctx = str(item)
            date_val = None
            conf = 0.95

        # Extract unit if embedded
        if isinstance(val, str):
            u_match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z%]+)", val)
            if u_match and not unit:
                unit = u_match.group(2)

        page_no = 1
        for pn, ptext in page_texts.items():
            if ctx and ctx[:40].lower() in ptext.lower():
                page_no = pn
                break

        mid = f"metric_{idx:03d}"
        sref = SourceRef(
            sourceId=source_id,
            chunkId=f"chunk_{page_no:03d}",
            pageNumber=page_no,
            textQuote=f"{val} {unit}".strip(),
        )

        metrics.append(Metric(
            metricId=mid,
            id=mid,
            name=name[:120],
            value=val,
            unit=unit,
            context=ctx[:300],
            date=date_val,
            confidence=round(conf, 3),
            sourceRefs=[sref],
        ))

    return metrics


def normalize_claims(
    raw_claims: List[Any],
    source_id: str,
    page_texts: Dict[int, str],
) -> List[Claim]:
    """Separates verifiable facts from source claims and assertions."""
    claims: List[Claim] = []

    for idx, item in enumerate(raw_claims, start=1):
        if isinstance(item, dict):
            stmt = (item.get("statement") or item.get("claim") or item.get("text") or "").strip()
            ctype = item.get("claimType", "SOURCE_ASSERTION")
            attr = item.get("attribution", "")
            conf = float(item.get("confidence", 0.92))
        else:
            stmt = str(item).strip()
            ctype = "SOURCE_ASSERTION"
            attr = ""
            conf = 0.90

        if not stmt:
            continue

        page_no = 1
        for pn, ptext in page_texts.items():
            if stmt[:40].lower() in ptext.lower():
                page_no = pn
                break

        cid = f"claim_{idx:03d}"
        sref = SourceRef(
            sourceId=source_id,
            chunkId=f"chunk_{page_no:03d}",
            pageNumber=page_no,
            textQuote=stmt[:150],
        )

        claims.append(Claim(
            claimId=cid,
            id=cid,
            statement=stmt,
            text=stmt,
            claimType=ctype,
            attribution=attr,
            confidence=round(conf, 3),
            sourceRefs=[sref],
        ))

    return claims


def normalize_actions(
    raw_actions: List[Any],
    source_id: str,
    page_texts: Dict[int, str],
) -> List[Action]:
    """Standardizes recommended and mandatory operational actions."""
    actions: List[Action] = []

    for idx, item in enumerate(raw_actions, start=1):
        if isinstance(item, dict):
            act_text = (item.get("action") or item.get("text") or "").strip()
            actor = item.get("actor") or item.get("owner") or ""
            status = item.get("status", "RECOMMENDED")
            prio = item.get("priority", "P1 High")
            timeframe = item.get("timeframe", "")
        else:
            act_text = str(item).strip()
            actor = ""
            status = "RECOMMENDED"
            prio = "P1 High"
            timeframe = ""

        if not act_text:
            continue

        page_no = 1
        for pn, ptext in page_texts.items():
            if act_text[:40].lower() in ptext.lower():
                page_no = pn
                break

        aid = f"action_{idx:03d}"
        sref = SourceRef(
            sourceId=source_id,
            chunkId=f"chunk_{page_no:03d}",
            pageNumber=page_no,
            textQuote=act_text[:150],
        )

        actions.append(Action(
            actionId=aid,
            id=aid,
            action=act_text,
            text=act_text,
            actor=actor,
            status=status,
            priority=prio,
            timeframe=timeframe,
            owner=actor,
            sourceRefs=[sref],
        ))

    return actions
