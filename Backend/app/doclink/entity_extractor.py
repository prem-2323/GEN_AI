"""DocLink entity extraction (Phase 4).

Pipeline position::

    ExtractedDocument -> chunk -> [this module] -> entities with evidence

Two cooperating strategies:

* **LLM strategy** — a structured-JSON prompt routed through ``DocLinkLLM``
  (Ollama / Gemini / any injected provider). Never a hard-coded provider call.
* **Deterministic strategy** — lexicon, gazetteer and pattern based recognition
  that always runs, so DocLink still produces entities when no model is
  available (offline, CI, deterministic test suites).

Results from both strategies are validated and merged (deduplicated by surface
form) by :func:`extract_entities`.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence, Tuple

from . import prompts
from .model_interface import DocLinkLLM
from .normalizer import normalize_surface, surface_key
from .schemas import RawEntity
from .validator import validate_raw_entities

# ---------------------------------------------------------------------------
# Lexicons & gazetteers (small, curated, extensible)
# ---------------------------------------------------------------------------
COUNTRIES = {
    "united states", "usa", "u.s.", "uk", "united kingdom", "canada", "germany", "france",
    "spain", "italy", "netherlands", "belgium", "sweden", "norway", "denmark", "finland",
    "ireland", "poland", "portugal", "switzerland", "austria", "greece", "turkey", "russia",
    "ukraine", "china", "japan", "south korea", "korea", "india", "pakistan", "bangladesh",
    "indonesia", "malaysia", "singapore", "thailand", "vietnam", "philippines", "australia",
    "new zealand", "brazil", "argentina", "chile", "colombia", "mexico", "peru", "egypt",
    "nigeria", "kenya", "south africa", "ghana", "morocco", "saudi arabia", "israel",
    "united arab emirates", "uae", "qatar", "iran", "iraq", "afghanistan", "sri lanka",
    "nepal", "ethiopia", "tanzania", "uganda", "zimbabwe", "romania", "hungary", "czechia",
}

CITIES = {
    "san francisco", "new york", "los angeles", "chicago", "boston", "seattle", "austin",
    "denver", "atlanta", "miami", "dallas", "houston", "phoenix", "portland", "san diego",
    "san jose", "palo alto", "mountain view", "silicon valley", "washington", "washington dc",
    "london", "manchester", "birmingham", "dublin", "paris", "lyon", "berlin", "munich",
    "hamburg", "frankfurt", "amsterdam", "rotterdam", "brussels", "madrid", "barcelona",
    "rome", "milan", "zurich", "geneva", "vienna", "stockholm", "oslo", "copenhagen",
    "helsinki", "warsaw", "prague", "budapest", "athens", "istanbul", "moscow", "kyiv",
    "beijing", "shanghai", "shenzhen", "hong kong", "tokyo", "osaka", "seoul",
    "mumbai", "delhi", "new delhi", "bengaluru", "bangalore", "hyderabad", "chennai", "pune",
    "dubai", "abu dhabi", "tel aviv", "jerusalem", "cairo", "lagos", "nairobi", "cape town",
    "johannesburg", "sao paulo", "são paulo", "rio de janeiro", "buenos aires", "santiago",
    "lima", "bogota", "bogotá", "toronto", "vancouver", "montreal", "ottawa", "sydney",
    "melbourne", "canberra", "auckland", "wellington",
}


TECHNOLOGY_TERMS = {
    "python", "pytorch", "tensorflow", "keras", "jax", "scikit-learn", "numpy", "pandas",
    "hugging face", "transformers", "onnx", "cuda", "docker", "kubernetes", "openshift",
    "terraform", "ansible", "jenkins", "kafka", "rabbitmq", "redis", "postgresql", "postgres",
    "mysql", "mariadb", "mongodb", "neo4j", "elasticsearch", "opensearch", "snowflake",
    "databricks", "spark", "airflow", "dbt", "fastapi", "django", "flask", "node.js",
    "react", "next.js", "typescript", "javascript", "rust", "golang", "java", "kotlin",
    "swift", "ollama", "qwen", "gemma", "llama", "mistral", "claude", "gpt", "gpt-4",
    "gpt-4o", "chatgpt", "bert", "roberta", "transformer", "diffusion", "rag", "llm", "llms",
    "nlp", "vector database", "embedding", "embeddings", "fine-tuning", "distillation",
    "quantization", "blockchain", "ethereum", "solidity", "oauth", "saml", "oidc", "jwt",
    "tls", "mtls", "ssl", "https", "tcp", "udp", "dns", "grpc", "graphql", "container",
    "serverless", "edge computing", "5g", "6g", "zero trust", "ebpf", "wireshark",
    "metasploit", "nmap", "splunk", "crowdstrike", "okta", "auth0", "keycloak",
}

ORG_CUE_WORDS = {
    "inc", "incorporated", "corp", "corporation", "company", "co", "ltd", "limited", "llc",
    "llp", "plc", "gmbh", "ag", "sa", "sas", "nv", "bv", "pty", "university", "college",
    "institute", "institution", "school", "ministry", "department", "agency", "authority",
    "bureau", "commission", "committee", "council", "foundation", "association", "federation",
    "union", "alliance", "coalition", "bank", "group", "holdings", "labs", "laboratory",
    "laboratories", "center", "centre", "hospital", "clinic", "firm", "partners", "network",
    "organization", "organisation", "systems", "solutions", "technologies", "services",
    "ventures", "capital", "industries", "enterprises",
}

ORG_VERB_CUES = {
    "announced", "announces", "released", "releases", "launched", "launches", "unveiled",
    "partnered", "partners", "acquired", "acquires", "reported", "reports", "said", "says",
    "detected", "detects", "developed", "develops", "built", "created", "published",
    "confirmed", "denied", "warned", "disclosed", "hired", "appointed", "signed", "deployed",
    "operates", "provides", "offers", "specializes", "invests", "funded", "raised",
}

KNOWN_ORGANIZATIONS = {
    "openai", "microsoft", "google", "alphabet", "meta", "facebook", "amazon", "aws", "apple",
    "nvidia", "intel", "amd", "ibm", "oracle", "sap", "salesforce", "adobe", "cisco", "dell",
    "vmware", "red hat", "canonical", "suse", "anthropic", "deepmind", "tesla", "samsung",
    "huawei", "xiaomi", "tencent", "alibaba", "baidu", "bytedance", "tiktok", "twitter",
    "linkedin", "netflix", "uber", "airbnb", "stripe", "paypal", "visa", "mastercard",
    "jpmorgan", "goldman sachs", "morgan stanley", "blackrock", "deloitte", "pwc", "kpmg",
    "accenture", "infosys", "tcs", "wipro", "cognizant", "capgemini", "united nations",
    "world bank", "imf", "who", "nato", "european union", "interpol", "fbi", "cia", "nsa",
    "cisa", "ncsc", "mitre", "owasp", "nist", "ieee", "w3c", "mit", "stanford university",
    "harvard university", "oxford university", "cambridge university", "organization x",
    "company x",
}

PERSON_TITLES = {
    "mr", "mrs", "ms", "miss", "dr", "prof", "professor", "sen", "rep", "governor",
    "president", "prime minister", "ceo", "cto", "cfo", "coo", "ciso", "chairman",
    "chairwoman", "director", "engineer", "analyst", "researcher", "scientist", "officer",
    "secretary",
}

PERSON_REPORTING_VERBS = {
    "said", "says", "stated", "reported", "noted", "added", "told", "wrote", "commented",
    "explained", "confirmed", "warned", "claimed", "testified", "published",
}

LAW_CUES = {
    "act", "law", "regulation", "regulations", "directive", "statute", "treaty", "convention",
    "code", "amendment", "ordinance", "decree", "gdpr", "ccpa", "hipaa", "sox", "pci dss",
    "nist sp 800-53", "nist csf", "dora", "nis2", "ai act", "cyber resilience act",
    "data protection act", "privacy act",
}

POLICY_CUES = {
    "policy", "policies", "framework", "standard", "standards", "guideline", "guidelines",
    "procedure", "procedures", "protocol", "protocols", "strategy", "roadmap", "charter",
    "mandate", "requirement", "requirements", "rule", "rules", "baseline", "playbook",
}

DOCUMENT_CUES = {
    "report", "whitepaper", "white paper", "advisory", "bulletin", "notice", "memo",
    "memorandum", "manual", "guide", "specification", "brief", "briefing", "dossier",
    "assessment", "analysis", "study", "survey", "review", "proposal", "contract",
    "agreement", "letter", "presentation", "transcript", "log", "record",
}

EVENT_CUES = {
    "summit", "conference", "convention", "workshop", "webinar", "seminar", "symposium",
    "meeting", "hearing", "trial", "election", "exercise", "drill", "campaign", "incident",
    "breach", "outage", "attack", "operation", "initiative", "program", "programme",
    "evaluation", "audit",
}



# ---------------------------------------------------------------------------
# Recognition patterns
# ---------------------------------------------------------------------------
IDENTIFIER_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.I),
    re.compile(r"\bCWE-\d{1,4}\b", re.I),
    re.compile(r"\bRFC[\s-]?\d{3,5}\b", re.I),
    re.compile(r"\b(?:ISO|IEC)[\s/]?\d{3,5}(?:-\d{1,3})?\b", re.I),
    re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
    re.compile(r"\b[A-Fa-f0-9]{32,64}\b"),
    re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b"),
    re.compile(r"\bhttps?://[^\s)\]]+", re.I),
    re.compile(r"\b[A-Z]{2,10}-\d{2,6}\b"),
]

DATE_PATTERNS: List[re.Pattern] = [
    re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b",
        re.I,
    ),
    re.compile(
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{4}\b",
        re.I,
    ),
    re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
        re.I,
    ),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
    re.compile(r"\bQ[1-4]\s+\d{4}\b"),
    re.compile(r"\b(?:FY|H[12])\s?\d{4}\b", re.I),
]

TIME_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\s?(?:AM|PM|UTC|GMT|CET|IST)?\b", re.I),
    re.compile(r"\b\d{1,2}\s?(?:AM|PM)\b", re.I),
]

AMOUNT_PATTERNS: List[re.Pattern] = [
    re.compile(r"[$€£¥₹]\s?\d[\d,\.]*\s?(?:million|billion|trillion|thousand|k|m|bn)?\b", re.I),
    re.compile(r"\b\d[\d,\.]*\s?(?:million|billion|trillion|thousand)\s?(?:dollars?|usd|eur|gbp|users?|records?|people)?\b", re.I),
    re.compile(r"\b\d+(?:\.\d+)?\s?%"),
    re.compile(r"\b\d+(?:\.\d+)?\s?(?:percent|percentage points)\b", re.I),
]

PROPER_NOUN_RE = re.compile(
    r"\b([A-Z][A-Za-z0-9&.'’\-]*(?:\s+(?:of|for|and|the|de|del|van|von)?\s*[A-Z][A-Za-z0-9&.'’\-]*){0,4})"
)
ORGANIZATION_X_RE = re.compile(
    r"\b(Organization|Organisation|Company|Agency|Group|Team|Corp|Firm)\s+[A-Z0-9]{1,4}\b",
)
MODEL_NAME_RE = re.compile(r"\bModel\s+[A-Z][A-Za-z0-9.\-]*\b")
_TRAILING_FUNCTION_WORD_RE = re.compile(r"\s+(?:of|for|and|the|in|on|with|to|from|a|an)$", re.I)

STOP_PHRASES = {
    "the", "this", "that", "these", "those", "it", "they", "we", "you", "i", "a", "an",
    "however", "therefore", "moreover", "furthermore", "in", "on", "at", "by", "for",
    "with", "and", "or", "but", "if", "then", "when", "where", "which", "who", "what",
    "why", "how", "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "monday", "tuesday", "wednesday",
    "thursday", "friday", "saturday", "sunday",
}



# ---------------------------------------------------------------------------
# Priority table — higher wins when two recognisers claim the same span
# ---------------------------------------------------------------------------
ENTITY_PRIORITY: Dict[str, int] = {
    "IDENTIFIER": 100,
    "DATE": 95,
    "AMOUNT": 90,
    "TIME": 85,
    "ORGANIZATION": 70,
    "PERSON": 68,
    "CITY": 65,
    "COUNTRY": 65,
    "LOCATION": 60,
    "TECHNOLOGY": 55,
    "PRODUCT": 54,
    "LAW": 50,
    "POLICY": 48,
    "DOCUMENT": 46,
    "EVENT": 44,
}

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")


def _build_alternation(values: Sequence[str]) -> re.Pattern:
    ordered = sorted({v for v in values if v}, key=len, reverse=True)
    return re.compile(r"(?<![\w-])(" + "|".join(re.escape(v) for v in ordered) + r")(?![\w-])", re.I)


CITY_RE = _build_alternation(sorted(CITIES))
COUNTRY_RE = _build_alternation(sorted(COUNTRIES))
TECHNOLOGY_RE = _build_alternation(sorted(TECHNOLOGY_TERMS))
KNOWN_ORG_RE = _build_alternation(sorted(KNOWN_ORGANIZATIONS))
ORG_VERB_RE = _build_alternation(sorted(ORG_VERB_CUES))


def _iter_sentences(text: str) -> List[Tuple[int, int, str]]:
    """Return (start, end, sentence) tuples covering the whole chunk text."""
    spans: List[Tuple[int, int, str]] = []
    cursor = 0
    for part in _SENT_SPLIT.split(text):
        if not part:
            continue
        start = text.find(part, cursor)
        if start < 0:  # pragma: no cover - defensive
            start = cursor
        end = start + len(part)
        spans.append((start, end, part))
        cursor = end
    if not spans and text.strip():
        spans.append((0, len(text), text))
    return spans


def _sentence_at(offset: int, sentences: Sequence[Tuple[int, int, str]]) -> str:
    for start, end, sentence in sentences:
        if start <= offset < end:
            return sentence
    return ""


def _clean_phrase(phrase: str) -> str:
    cleaned = normalize_surface(phrase)
    while _TRAILING_FUNCTION_WORD_RE.search(cleaned):
        cleaned = _TRAILING_FUNCTION_WORD_RE.sub("", cleaned).strip()
    return cleaned


def _classify_phrase(
    phrase: str,
    sentence: str,
    *,
    org_verb_present: bool,
    subject_position: bool,
) -> Optional[Tuple[str, float]]:
    """Classify a capitalised phrase; ``None`` means "not enough evidence, drop it"."""
    lowered = phrase.lower()
    tokens = [t.strip(".,;:()").lower() for t in phrase.split() if t.strip(".,;:()")]
    if not tokens:
        return None
    if lowered in STOP_PHRASES or len(phrase) < 2:
        return None
    if lowered in KNOWN_ORGANIZATIONS:
        return "ORGANIZATION", 0.95
    if any(t.isdigit() for t in tokens) and not any(t in ORG_CUE_WORDS for t in tokens):
        return None  # bare numbers belong to DATE / AMOUNT recognisers

    last = tokens[-1]
    if last in ORG_CUE_WORDS:
        return "ORGANIZATION", 0.9
    if any(t in LAW_CUES for t in tokens):
        return "LAW", 0.85
    if last in POLICY_CUES:
        return "POLICY", 0.82
    if last in DOCUMENT_CUES:
        return "DOCUMENT", 0.82
    if last in EVENT_CUES:
        return "EVENT", 0.78
    if lowered in TECHNOLOGY_TERMS:
        return "TECHNOLOGY", 0.92
    if "model" in tokens and len(tokens) > 1:
        return "PRODUCT", 0.8

    sentence_lower = sentence.lower()
    position = sentence_lower.find(lowered)
    before = sentence_lower[:position].strip() if position > 0 else ""
    after = sentence_lower[position + len(lowered):].strip() if position >= 0 else ""

    previous_word = before.split()[-1].strip(".,;:()") if before else ""
    next_word = after.split()[0].strip(".,;:()") if after else ""
    if previous_word in PERSON_TITLES:
        return "PERSON", 0.85
    if next_word in PERSON_REPORTING_VERBS and 1 < len(tokens) <= 3:
        return "PERSON", 0.8
    if org_verb_present:
        if subject_position or previous_word in {"with", "and", "at", "for", "from", "by", "of"}:
            return "ORGANIZATION", 0.72 if subject_position else 0.65
    return None


def _collect_spans(
    candidates: List[Dict[str, object]],
    pattern: re.Pattern,
    text: str,
    entity_type: str,
    confidence: float,
) -> None:
    for match in pattern.finditer(text):
        candidates.append(
            {
                "start": match.start(),
                "end": match.end(),
                "surface": match.group(0),
                "type": entity_type,
                "confidence": confidence,
                "priority": ENTITY_PRIORITY.get(entity_type, 10),
            }
        )



# ---------------------------------------------------------------------------
# Deterministic extraction
# ---------------------------------------------------------------------------
def extract_entities_deterministic(chunk_text: str) -> List[RawEntity]:
    """Lexicon / gazetteer / pattern based entity recognition (always available)."""
    text = chunk_text or ""
    if not text.strip():
        return []

    sentences = _iter_sentences(text)
    org_verb_present = any(ORG_VERB_RE.search(sentence) for _, _, sentence in sentences)

    candidates: List[Dict[str, object]] = []
    for pattern in IDENTIFIER_PATTERNS:
        _collect_spans(candidates, pattern, text, "IDENTIFIER", 0.95)
    for pattern in DATE_PATTERNS:
        _collect_spans(candidates, pattern, text, "DATE", 0.95)
    for pattern in AMOUNT_PATTERNS:
        _collect_spans(candidates, pattern, text, "AMOUNT", 0.9)
    for pattern in TIME_PATTERNS:
        _collect_spans(candidates, pattern, text, "TIME", 0.85)
    _collect_spans(candidates, CITY_RE, text, "CITY", 0.9)
    _collect_spans(candidates, COUNTRY_RE, text, "COUNTRY", 0.9)
    _collect_spans(candidates, KNOWN_ORG_RE, text, "ORGANIZATION", 0.95)
    _collect_spans(candidates, TECHNOLOGY_RE, text, "TECHNOLOGY", 0.9)
    _collect_spans(candidates, ORGANIZATION_X_RE, text, "ORGANIZATION", 0.85)
    _collect_spans(candidates, MODEL_NAME_RE, text, "PRODUCT", 0.8)

    for match in PROPER_NOUN_RE.finditer(text):
        surface = _clean_phrase(match.group(0))
        if not surface:
            continue
        start = match.start()
        sentence = _sentence_at(start, sentences)
        subject_position = bool(sentence) and sentence.strip().startswith(surface[:12])
        classified = _classify_phrase(
            surface,
            sentence or text,
            org_verb_present=org_verb_present,
            subject_position=subject_position,
        )
        if not classified:
            continue
        entity_type, confidence = classified
        candidates.append(
            {
                "start": start,
                "end": start + len(surface),
                "surface": surface,
                "type": entity_type,
                "confidence": confidence,
                "priority": ENTITY_PRIORITY.get(entity_type, 10),
            }
        )

    # Greedy non-overlapping resolution: strongest recogniser wins each span.
    candidates.sort(key=lambda c: (-int(c["priority"]), int(c["start"]), -(int(c["end"]) - int(c["start"]))))
    accepted: List[Dict[str, object]] = []
    occupied: List[Tuple[int, int]] = []
    for candidate in candidates:
        start, end = int(candidate["start"]), int(candidate["end"])
        if any(not (end <= s or start >= e) for s, e in occupied):
            continue
        occupied.append((start, end))
        accepted.append(candidate)

    accepted.sort(key=lambda c: int(c["start"]))
    entities: List[RawEntity] = []
    for candidate in accepted:
        sentence = _sentence_at(int(candidate["start"]), sentences) or str(candidate["surface"])
        entities.append(
            RawEntity(
                text=str(candidate["surface"]),
                name=str(candidate["surface"]),
                type=str(candidate["type"]),
                canonical_name=str(candidate["surface"]),
                confidence=float(candidate["confidence"]),
                quote=sentence[:240],
                aliases=[],
            )
        )
    return entities



# ---------------------------------------------------------------------------
# LLM-assisted extraction
# ---------------------------------------------------------------------------
def extract_entities_with_llm(
    chunk_text: str,
    llm: Optional[DocLinkLLM],
    *,
    chunk_id: str = "chunk_001",
    page: int = 1,
    section: str = "",
    max_items: int = 40,
) -> Optional[List[RawEntity]]:
    """Ask the configured provider for structured entities (``None`` on failure)."""
    if llm is None or not getattr(llm, "is_available", lambda: False)():
        return None
    payload = llm.generate_json(
        prompts.ENTITY_SYSTEM_PROMPT,
        prompts.build_entity_prompt(chunk_text, chunk_id, page, section, max_items),
    )
    if not payload:
        return None
    raw_items = payload.get("entities") if isinstance(payload.get("entities"), list) else None
    if raw_items is None:
        # Some models return a bare list of entities.
        raw_items = payload if isinstance(payload, list) else []
    accepted, _rejected = validate_raw_entities(raw_items)
    return accepted


def merge_entity_candidates(
    llm_entities: Sequence[RawEntity],
    deterministic_entities: Sequence[RawEntity],
) -> List[RawEntity]:
    """Merge LLM + deterministic candidates, keeping occurrences as mentions."""
    merged: List[RawEntity] = list(llm_entities)
    llm_keys = {surface_key(e.text) for e in llm_entities}
    for entity in deterministic_entities:
        if surface_key(entity.text) in llm_keys:
            continue  # already found by the model (better typing/aliases)
        merged.append(entity)
    return merged


def extract_entities(
    chunk_text: str,
    *,
    llm: Optional[DocLinkLLM] = None,
    chunk_id: str = "chunk_001",
    page: int = 1,
    section: str = "",
    use_llm: bool = True,
    max_items: int = 40,
) -> Tuple[List[RawEntity], List[str], str]:
    """Extract entities from one chunk.

    Returns ``(entities, rejected, provider)`` where ``provider`` is the label of
    the strategy that contributed the model-based results.
    """
    rejected: List[str] = []
    deterministic_entities = extract_entities_deterministic(chunk_text)

    llm_entities: List[RawEntity] = []
    provider = "deterministic"
    if use_llm:
        llm_result = extract_entities_with_llm(
            chunk_text, llm, chunk_id=chunk_id, page=page, section=section, max_items=max_items
        )
        if llm_result is not None:
            llm_entities = llm_result
            provider = getattr(llm, "name", "llm")

    merged = merge_entity_candidates(llm_entities, deterministic_entities)
    accepted, raw_rejected = validate_raw_entities(merged)
    rejected.extend(raw_rejected)
    return accepted, rejected, provider


__all__ = [
    "extract_entities",
    "extract_entities_deterministic",
    "extract_entities_with_llm",
    "merge_entity_candidates",
    "KNOWN_ORGANIZATIONS",
    "TECHNOLOGY_TERMS",
    "COUNTRIES",
    "CITIES",
]

