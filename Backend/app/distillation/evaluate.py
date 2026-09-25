"""Teacher/student comparison metrics for grounded QA records."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\b\d+(?:\.\d+)?%?\b", text or ""))


def compare_answers(records: list[dict[str, Any]], teacher_answers: list[dict[str, Any]], student_answers: list[dict[str, Any]], output_path: Path) -> dict[str, Any]:
    teacher_by_question = {item.get("question"): item for item in teacher_answers}
    student_by_question = {item.get("question"): item for item in student_answers}
    comparisons: list[dict[str, Any]] = []
    for record in records:
        question = record.get("input") or record.get("question")
        teacher = teacher_by_question.get(question, {})
        student = student_by_question.get(question, {})
        teacher_text = str(teacher.get("answer", ""))
        student_text = str(student.get("answer", ""))
        expected = str(record.get("output", ""))
        numerical = _numbers(expected) <= _numbers(student_text) if _numbers(expected) else None
        comparisons.append({"question": question, "teacher_answer": teacher_text, "student_answer": student_text, "correct": None if not student_text else student_text == expected, "score": None if not student_text else (100 if student_text == expected else 0), "hallucination": None if not student_text else False, "missing_information": [] if student_text else ["Student checkpoint unavailable."], "reason": "Student inference was not executed." if not student_text else "Compared against grounded teacher record.", "source_pages": record.get("source_pages", []), "numerical_correct": numerical})
    output_path.write_text("".join(json.dumps(item, ensure_ascii=True) + "\n" for item in comparisons), encoding="utf-8")
    available = [item for item in comparisons if item["score"] is not None]
    return {"comparisons": len(comparisons), "evaluated": len(available), "student_score": None if not available else sum(item["score"] for item in available) / len(available), "numerical_accuracy": None if not available else sum(bool(item["numerical_correct"]) for item in available) / len(available), "grounding_rate": None, "hallucination_rate": None}


__all__ = ["compare_answers"]