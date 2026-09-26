"""Duration-based timeline extraction shared by AI provider fallbacks."""
from __future__ import annotations

import re

_DURATION_RE = re.compile(
    r"\b(?P<value>\d+(?:\.\d+)?|a|an|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)"
    r"\s+(?P<unit>years?|months?|weeks?|days?|hours?|minutes?)\b",
    re.I,
)
_NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}


def _clean_timeline_description(text: str) -> str:
    cleaned = re.sub(
        r"^(?:(?:will|would|shall|should)\s+)?(?:focus on|be used for|be devoted to|"
        r"be spent on|be allocated to|consist of|include|cover|involve|of|for|on)\s+",
        "",
        text.strip(),
        flags=re.I,
    )
    cleaned = re.sub(r"^(?:the\s+)?(?:first|next|final|last)\s+", "", cleaned, flags=re.I)
    cleaned = re.sub(r"[\s,;:.]+$", "", cleaned)
    cleaned = re.sub(r"^(?:and\s+)?", "", cleaned, flags=re.I)
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned[:180]


def extract_timeline_deterministic(text: str) -> list[dict]:
    """Extract duration-bearing timeline items with exact source sentence evidence."""
    nodes: list[dict] = []
    total_nodes: list[dict] = []
    phase_nodes: list[dict] = []
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if s.strip()]

    for sentence in sentences:
        matches = list(_DURATION_RE.finditer(sentence))
        if not matches:
            continue

        for idx, match in enumerate(matches):
            raw_value = match.group("value").lower()
            value = float(raw_value) if re.fullmatch(r"\d+(?:\.\d+)?", raw_value) else float(_NUMBER_WORDS[raw_value])
            unit = match.group("unit").lower()
            unit = unit if unit.endswith("s") else f"{unit}s"
            before = sentence[:match.start()]
            after_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(sentence)
            after = sentence[match.end():after_end]

            total_match = re.search(
                r"(?P<subject>[A-Za-z][A-Za-z -]{0,60}?)\s+(?:is estimated to take|is expected to take|"
                r"will take|takes|requires|has a duration of|duration of)\s*$",
                before,
                re.I,
            )
            if total_match:
                subject = re.sub(r"^(?:the|a|an)\s+", "", total_match.group("subject").strip(), flags=re.I)
                total_nodes.append({
                    "description": f"Total {subject or 'duration'}".strip(),
                    "duration_value": value,
                    "duration_unit": unit,
                    "kind": "total",
                    "source_text": sentence,
                })
                continue

            after = re.split(r",?\s+(?:followed by|then|after that|subsequently)\s+", after, maxsplit=1, flags=re.I)[0]
            description = _clean_timeline_description(after)
            if not description:
                continue
            phase_nodes.append({
                "description": description,
                "duration_value": value,
                "duration_unit": unit,
                "kind": "phase",
                "source_text": sentence,
            })

    nodes.extend(total_nodes)
    nodes.extend(phase_nodes)
    for sequence, node in enumerate(nodes, start=1):
        node["sequence"] = sequence
    return nodes