"""Event extraction and participant linkage for UCKR Engine."""
from __future__ import annotations

from typing import Any, List
from ...models.uckr import Event


def process_events(
    raw_events: List[Any],
    known_entity_names: List[str],
) -> List[Event]:
    """Extracts structured events and maps participants to known entities."""
    events: List[Event] = []

    for idx, item in enumerate(raw_events, start=1):
        if isinstance(item, dict):
            name = (item.get("event") or item.get("name") or item.get("title") or "").strip()
            etype = item.get("type", "security_incident")
            date_str = item.get("date") or item.get("timestamp") or None
            loc = item.get("location")
            impact = item.get("impact", "")
            raw_actors = item.get("actors") or item.get("participants") or []
            conf = float(item.get("confidence", 0.95))
        else:
            name = str(item).strip()
            etype = "security_incident"
            date_str = None
            loc = None
            impact = ""
            raw_actors = []
            conf = 0.92

        if not name or len(name) < 3:
            continue

        # Link actors
        matched_participants = []
        for a in raw_actors:
            a_str = str(a).strip()
            if a_str:
                matched_participants.append(a_str)

        # Infer participants if empty
        if not matched_participants:
            for ent in known_entity_names:
                if ent.lower() in name.lower():
                    matched_participants.append(ent)

        eid = f"EVENT_{idx:03d}"
        ev = Event(
            id=eid,
            eventId=eid,
            name=name,
            title=name,
            type=etype,
            date=str(date_str) if date_str else None,
            timestamp=str(date_str) if date_str else None,
            location=loc,
            impact=impact,
            participants=list(set(matched_participants)),
            actors=list(set(matched_participants)),
            confidence=round(conf, 3),
            sourceRefs=[f"CIT_EV_{idx:03d}"],
        )
        events.append(ev)

    return events
