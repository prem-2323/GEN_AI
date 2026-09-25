"""Phase 13 Validation Engine — Claim Extraction & Validator.

Extracts factual claims from generated transformation deliverables, identifying
subjects, predicates, objects, numbers, dates, locations, and citations.
"""

from __future__ import annotations

import re
import logging
from typing import List, Optional
from .schemas import ClaimItem, ValidationContext

log = logging.getLogger("gen-transform.validation.claim_validator")


class ClaimExtractor:
    """Extracts structured claims from transformation text or structured sections."""

    def extract_claims(self, context: ValidationContext) -> List[ClaimItem]:
        """Extract structured ClaimItem list from ValidationContext text."""
        claims: List[ClaimItem] = []
        text = context.transformation_output or ""
        lines = text.split("\n")

        # 1. Regex patterns for dates, numbers, entity claims
        date_pattern = r"\b(?:\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}|\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4})\b"
        number_pattern = r"\b(?:\d+(?:\.\d+)?%|\$\d+(?:\.\d+)?(?:\s*million|\s*billion)?|\d+\s*million|\d+\s*billion|\d+)\b"

        for line_num, line in enumerate(lines, start=1):
            line_str = line.strip()
            # Ignore headers or empty lines
            if not line_str or line_str.startswith("#"):
                continue

            # Extract inline citation tags
            citations = re.findall(r"\[\d+\]", line_str)

            # Find dates and numbers in line
            dates = re.findall(date_pattern, line_str, re.IGNORECASE)
            numbers = re.findall(number_pattern, line_str, re.IGNORECASE)

            # Split line into sentences
            sentences = [s.strip() for s in re.split(r"[.!?]", line_str) if s.strip()]
            for sent in sentences:
                sent_dates = re.findall(date_pattern, sent, re.IGNORECASE)
                sent_numbers = re.findall(number_pattern, sent, re.IGNORECASE)
                sent_cits = re.findall(r"\[\d+\]", sent)

                claims.append(
                    ClaimItem(
                        text=sent,
                        date_val=sent_dates[0] if sent_dates else (dates[0] if dates else None),
                        number_val=sent_numbers[0] if sent_numbers else (numbers[0] if numbers else None),
                        citation_ids=sent_cits or citations,
                    )
                )

        if not claims and text.strip():
            claims.append(ClaimItem(text=text.strip()[:200]))

        return claims


__all__ = ["ClaimExtractor"]
