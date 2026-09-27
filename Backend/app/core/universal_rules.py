"""GEN TRANSFORM AI — Universal File & Media Rules (Phase 1-16 Enforcement Engine).

Implements programmatic enforcement of the 50 Universal Rules, Multimodal Provenance schemas,
Claim Validation categories, and Grounding Formulas.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


# ==============================================================================
# 1. Fact & Claim Classification Enums (Rules 17, 36)
# ==============================================================================

class FactClassification(str, Enum):
    SOURCE_FACT = "SOURCE_FACT"         # Directly supported by evidence
    DERIVED_FACT = "DERIVED_FACT"       # Logically derived from source information
    INFERENCE = "INFERENCE"             # Interpretation not explicitly stated
    UNCERTAIN = "UNCERTAIN"             # Evidence is insufficient or ambiguous
    CONFLICTING = "CONFLICTING"         # Conflicting values from source evidence


class ClaimValidationStatus(str, Enum):
    SUPPORTED = "SUPPORTED"             # Fully grounded in UCKR / source evidence
    DERIVED = "DERIVED"                 # Valid deductive derivation
    INFERENCE = "INFERENCE"             # Marked interpretive claim
    UNSUPPORTED = "UNSUPPORTED"         # No evidence in current source (Hallucination)
    CONTRADICTED = "CONTRADICTED"       # Directly contradicts source facts
    UNCERTAIN = "UNCERTAIN"             # Unverifiable or ambiguous


class OverallValidationStatus(str, Enum):
    PASS = "PASS"                       # No unsupported or contradictory claims
    PASS_WITH_REVIEW = "PASS_WITH_REVIEW" # Only clearly marked derived/inferred content
    REVIEW_REQUIRED = "REVIEW_REQUIRED" # Unsupported or uncertain claims detected
    FAILED = "FAILED"                   # Major contradiction or source contamination


class NumberSemanticCategory(str, Enum):
    IDENTIFIER = "IDENTIFIER"
    YEAR = "YEAR"
    DATE = "DATE"
    COUNT = "COUNT"
    MEASUREMENT = "MEASUREMENT"
    PERCENTAGE = "PERCENTAGE"
    CURRENCY = "CURRENCY"
    VERSION = "VERSION"
    RANK = "RANK"
    STATISTIC = "STATISTIC"
    UNKNOWN = "UNKNOWN"


# ==============================================================================
# 2. Universal Multimodal Provenance Schemas (Rules 4, 5, 7, 8, 9, 10, 18, 19)
# ==============================================================================

class PDFLocation(BaseModel):
    page: int
    paragraph: Optional[int] = None
    line: Optional[int] = None
    quote: Optional[str] = None


class PPTXLocation(BaseModel):
    slide: int
    shape: Optional[int] = None
    title: Optional[str] = None
    notes: Optional[str] = None


class ImageLocation(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    ocr_text: Optional[str] = None
    caption: Optional[str] = None
    region_id: Optional[str] = None


class VideoLocation(BaseModel):
    start: str                          # HH:MM:SS or SS.ms
    end: str
    scene: Optional[int] = None
    speaker: Optional[str] = None
    visual_event: Optional[str] = None


class AudioLocation(BaseModel):
    start: str                          # HH:MM:SS or SS.ms
    end: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None


class SpreadsheetLocation(BaseModel):
    sheet: str
    row: int
    column: Union[str, int]
    header: Optional[str] = None
    cell_value: Optional[str] = None


class TextLocation(BaseModel):
    section: Optional[str] = None
    heading: Optional[str] = None
    line: Optional[int] = None
    quote: Optional[str] = None


# Universal location container
UniversalSourceLocation = Union[
    PDFLocation,
    PPTXLocation,
    ImageLocation,
    VideoLocation,
    AudioLocation,
    SpreadsheetLocation,
    TextLocation,
    Dict[str, Any],
]


# ==============================================================================
# 3. Universal UCKR Fact Model (Rule 18)
# ==============================================================================

class UniversalUCKRFact(BaseModel):
    """Universal UCKR Fact model applicable across all source modalities."""
    fact_id: str
    source_id: str
    source_type: str                    # PDF, PPTX, IMAGE, VIDEO, AUDIO, DOCX, SPREADSHEET, TXT, MD, etc.
    source_location: UniversalSourceLocation
    fact_text: str
    fact_type: str = "SOURCE_FACT"      # SOURCE_FACT, DERIVED_FACT, INFERENCE, UNCERTAIN, CONFLICTING
    entities: List[str] = Field(default_factory=list)
    relationships: List[str] = Field(default_factory=list)
    numbers: List[Dict[str, Any]] = Field(default_factory=list)
    dates: List[str] = Field(default_factory=list)
    units: List[str] = Field(default_factory=list)
    evidence: str = ""
    confidence: float = 1.0
    status: str = "VERIFIED"            # VERIFIED, UNVERIFIED, SOURCE_CONFLICT, UNCERTAIN


# ==============================================================================
# 4. Claim Validation & Scoring (Rules 36, 37, 38, 40, 48)
# ==============================================================================

class ExtractedClaim(BaseModel):
    """Factual claim extracted from generated deliverable."""
    claim_id: str
    claim_text: str
    target_field: str                   # e.g., "slide_2.bullets[0]", "body.paragraph[1]"
    status: ClaimValidationStatus = ClaimValidationStatus.SUPPORTED
    provenance_fact_ids: List[str] = Field(default_factory=list)
    source_evidence: Optional[str] = None
    explanation: Optional[str] = None


class ValidationScoreReport(BaseModel):
    """Calculates ground truth metrics per Rules 37, 38, 40."""
    total_factual_claims: int = 0
    supported_claims: int = 0
    derived_claims: int = 0
    unsupported_claims: int = 0
    contradicted_claims: int = 0
    uncertain_claims: int = 0

    grounding_score: float = 100.0      # (supported_claims / total_factual_claims) * 100
    unsupported_claim_rate: float = 0.0 # (unsupported_claims / total_factual_claims) * 100
    completeness_score: float = 100.0
    overall_status: OverallValidationStatus = OverallValidationStatus.PASS

    @classmethod
    def calculate(
        cls,
        claims: List[ExtractedClaim],
        total_uckr_facts_count: int = 1,
    ) -> "ValidationScoreReport":
        total = len(claims)
        if total == 0:
            return cls(
                total_factual_claims=0,
                supported_claims=0,
                derived_claims=0,
                unsupported_claims=0,
                contradicted_claims=0,
                uncertain_claims=0,
                grounding_score=100.0,
                unsupported_claim_rate=0.0,
                completeness_score=100.0,
                overall_status=OverallValidationStatus.PASS,
            )

        supported = sum(1 for c in claims if c.status == ClaimValidationStatus.SUPPORTED)
        derived = sum(1 for c in claims if c.status == ClaimValidationStatus.DERIVED)
        unsupported = sum(1 for c in claims if c.status == ClaimValidationStatus.UNSUPPORTED)
        contradicted = sum(1 for c in claims if c.status == ClaimValidationStatus.CONTRADICTED)
        uncertain = sum(1 for c in claims if c.status == ClaimValidationStatus.UNCERTAIN)

        # Formula Rule 37: Grounding = Supported factual claims / Total factual claims * 100
        grounding = round(((supported + derived) / total) * 100.0, 2)
        # Formula Rule 38: Unsupported Claim Rate = Unsupported claims / Total factual claims * 100
        unsupported_rate = round((unsupported / total) * 100.0, 2)

        # Rule 46 & 47 Fail-closed status evaluation
        if contradicted > 0 or unsupported > 0:
            status = OverallValidationStatus.FAILED if contradicted > 0 else OverallValidationStatus.REVIEW_REQUIRED
        elif uncertain > 0:
            status = OverallValidationStatus.REVIEW_REQUIRED
        elif derived > 0:
            status = OverallValidationStatus.PASS_WITH_REVIEW
        else:
            status = OverallValidationStatus.PASS

        # Completeness: unique referenced UCKR facts / total source UCKR facts (Rule 40)
        used_fact_ids = set()
        for c in claims:
            used_fact_ids.update(c.provenance_fact_ids)
        completeness = round((len(used_fact_ids) / max(total_uckr_facts_count, 1)) * 100.0, 2)

        return cls(
            total_factual_claims=total,
            supported_claims=supported,
            derived_claims=derived,
            unsupported_claims=unsupported,
            contradicted_claims=contradicted,
            uncertain_claims=uncertain,
            grounding_score=grounding,
            unsupported_claim_rate=unsupported_rate,
            completeness_score=min(completeness, 100.0),
            overall_status=status,
        )


# ==============================================================================
# 5. Non-Negotiable System Prompt Guardrails (Rule 50 & Non-Negotiable Rules)
# ==============================================================================

UNIVERSAL_SYSTEM_PROMPT_CONSTRAINTS = """[UNIVERSAL SOURCE-GROUNDED TRANSFORMATION RULES]
1. SOURCE-FIRST AUTHORITY: Source material is primary truth. Do not replace source facts with external knowledge.
2. ZERO HALLUCINATIONS: Never invent statistics, metrics, dates, names, organizations, users, results, or benefits.
3. PRESERVE NUMBERS, UNITS & DATES: Exact numerical values and units (e.g. 11,000 tons/day, 66%, ₹500) must remain unaltered.
4. UNIVERSAL PROVENANCE: Every statement must trace to a specific UCKR fact_id.
5. NO UNSUPPORTED CLAIMS: If a capability was proposed, do NOT report it as an achieved metric.
6. UNCERTAINTY HANDLING: If unspecified in source, output "Not specified in the source." DO NOT GUESS.
7. FAIL-CLOSED PRINCIPLE: When verification fails, omit or flag the claim rather than inventing information.
"""
