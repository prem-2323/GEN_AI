"""Prompts used by the document-grounded teacher and student evaluators."""
from __future__ import annotations

TEACHER_SYSTEM_PROMPT = """You are the teacher model for a grounded research-paper QA dataset.
Answer only from the supplied evidence. Preserve numbers exactly. If the evidence does not answer
the question, answer exactly: Not specified in the paper.
Return JSON with keys answer, source_pages, source_section, evidence.
Do not add outside knowledge or invent citations."""

STUDENT_SYSTEM_PROMPT = """You are a distilled student model answering from retrieved paper evidence.
Use only the supplied evidence. Preserve numerical values exactly. If evidence is insufficient,
answer exactly: Not specified in the paper."""


def teacher_prompt(question: str, evidence: str, pages: list[int]) -> str:
    return (
        f"{TEACHER_SYSTEM_PROMPT}\n\nQuestion: {question}\n"
        f"Source pages: {pages}\nEvidence:\n{evidence[:5000]}"
    )


def student_prompt(question: str, evidence: str) -> str:
    return f"{STUDENT_SYSTEM_PROMPT}\n\nQuestion: {question}\nEvidence:\n{evidence[:4000]}"


__all__ = ["TEACHER_SYSTEM_PROMPT", "STUDENT_SYSTEM_PROMPT", "teacher_prompt", "student_prompt"]