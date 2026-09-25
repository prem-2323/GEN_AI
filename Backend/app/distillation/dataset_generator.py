"""Grounded QA dataset generation from the existing processed PDF/U​​CKR."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..storage.repository import get_repository
from .config import PaperDistillationConfig

NOT_SPECIFIED = "Not specified in the paper."


@dataclass
class PaperContext:
    project_id: str
    source_id: str
    filename: str
    pages: list[dict[str, Any]]
    uckr: dict[str, Any]

    @property
    def text(self) -> str:
        return "\n\n".join(str(page.get("text", "")) for page in self.pages)


def load_paper_context(project_id: str, source_id: str) -> PaperContext:
    source_repo = get_repository("sources")
    source = source_repo.find_one(
        {"$or": [{"sourceId": source_id}, {"id": source_id}]},
        projection={"_id": 0},
    ) or {}
    normalized = source.get("normalized") or {}
    pages = normalized.get("pages") or []
    if not pages:
        extracted = get_repository("extracted_content").find_one(
            {"sourceId": source_id}, projection={"_id": 0}
        ) or {}
        pages = extracted.get("pages") or []
    uckr = get_repository("uckr").find_one(
        {"projectId": project_id, "sourceId": source_id},
        sort=[("version", -1)], projection={"_id": 0},
    ) or {}
    if not pages:
        raise ValueError(f"No processed pages found for source '{source_id}'.")
    return PaperContext(
        project_id=project_id,
        source_id=source_id,
        filename=source.get("originalFilename") or source.get("file", {}).get("originalName") or "source.pdf",
        pages=pages,
        uckr=uckr,
    )


def _evidence_items(context: PaperContext) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for fact in context.uckr.get("facts", []):
        value = str(fact.get("value") or fact.get("text") or "").strip()
        if value:
            source = fact.get("source") or {}
            items.append({"answer": value, "evidence": str(fact.get("quote") or value), "pages": [source.get("page", 1)], "section": fact.get("section", "")})
    if items:
        return items
    for page in context.pages:
        text = str(page.get("text", ""))
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            sentence = sentence.strip()
            if len(sentence) > 35:
                items.append({"answer": sentence, "evidence": sentence, "pages": [int(page.get("pageNumber", 1))], "section": ""})
    return items


def build_document_chunks(context: PaperContext, max_chars: int = 1800) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for page in context.pages:
        page_number = int(page.get("pageNumber", len(chunks) + 1))
        paragraphs = [p.strip() for p in str(page.get("text", "")).split("\n\n") if p.strip()]
        current = ""
        part = 1
        for paragraph in paragraphs:
            if current and len(current) + len(paragraph) + 2 > max_chars:
                chunks.append({"chunk_id": f"p{page_number:02d}-c{part:02d}", "page": page_number, "section": "", "text": current, "source": context.filename})
                part += 1
                current = ""
            current = f"{current}\n\n{paragraph}".strip()
        if current:
            chunks.append({"chunk_id": f"p{page_number:02d}-c{part:02d}", "page": page_number, "section": "", "text": current, "source": context.filename})
    return chunks


_TEMPLATES = [
    ("basic", "What does the paper state about {topic}?"),
    ("technical", "What technical detail is reported in the paper about {topic}?"),
    ("methodology", "How was {topic} handled in the research?"),
    ("IoT", "What role does {topic} play in the proposed IoT system?"),
    ("sensors", "What does the paper report about the sensor-related item {topic}?"),
    ("machine learning", "What machine-learning information is given for {topic}?"),
    ("CatBoost", "What result or configuration does the paper report for {topic}?"),
    ("results", "What result is explicitly reported for {topic}?"),
    ("numerical", "What exact numerical value is reported for {topic}?"),
    ("architecture", "What architecture detail is associated with {topic}?"),
    ("research", "What research finding is supported by the evidence about {topic}?"),
    ("viva", "How would you answer a viva question about {topic} using this paper?"),
    ("analytical", "What cautious interpretation of {topic} is supported by the paper?"),
]


def _record(question: str, category: str, item: dict[str, Any], difficulty: str) -> dict[str, Any]:
    pages = [int(page) for page in item.get("pages", []) if page]
    return {"instruction": "Answer only from the research paper.", "input": question, "output": item["answer"], "category": category, "difficulty": difficulty, "source_pages": pages or [1], "source_section": item.get("section") or "Not specified in the paper.", "evidence": item["evidence"]}


def generate_qa_records(context: PaperContext, count: int = 200) -> list[dict[str, Any]]:
    items = _evidence_items(context)
    if not items:
        raise ValueError("Cannot generate QA records without extracted evidence.")
    records: list[dict[str, Any]] = []
    index = 0
    for template_index, (category, template) in enumerate(_TEMPLATES):
        for item_index, item in enumerate(items):
            topic = item["answer"][:90]
            question = template.format(topic=topic) + f" (evidence item {template_index + 1}-{item_index + 1})"
            difficulty = "basic" if template_index < 2 else "intermediate" if template_index < 6 else "advanced"
            records.append(_record(question, category, item, difficulty))
            index += 1
            if len(records) >= count:
                return records
    while len(records) < count:
        item = items[len(records) % len(items)]
        records.append(_record(f"What additional fact does the paper provide about evidence item {len(records) + 1}?", "research", item, "intermediate"))
    return records


def generate_evaluation_records(context: PaperContext, count: int = 50) -> list[dict[str, Any]]:
    items = _evidence_items(context)
    records: list[dict[str, Any]] = []
    for index in range(count):
        item = items[index % len(items)]
        question = f"Evaluation question {index + 1}: State the paper-grounded evidence for this finding without changing its numbers: {item['answer'][:110]}"
        records.append(_record(question, "evaluation", item, "advanced"))
    return records


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(record, ensure_ascii=True) + "\n" for record in records), encoding="utf-8")


def create_dataset(project_id: str, source_id: str, config: PaperDistillationConfig | None = None) -> dict[str, Any]:
    cfg = config or PaperDistillationConfig()
    context = load_paper_context(project_id, source_id)
    output = cfg.output_path
    chunks = build_document_chunks(context)
    qa = generate_qa_records(context, cfg.train_records + cfg.validation_records + cfg.test_records)
    evaluation = generate_evaluation_records(context, cfg.evaluation_records)
    train_end = cfg.train_records
    validation_end = train_end + cfg.validation_records
    _write_jsonl(output / "teacher_dataset.jsonl", qa)
    _write_jsonl(output / "teacher_dataset_train.jsonl", qa[:train_end])
    _write_jsonl(output / "teacher_dataset_validation.jsonl", qa[train_end:validation_end])
    _write_jsonl(output / "teacher_dataset_test.jsonl", qa[validation_end:])
    _write_jsonl(output / "evaluation_questions.jsonl", evaluation)
    (output / "document_chunks.json").write_text(json.dumps(chunks, indent=2, ensure_ascii=True), encoding="utf-8")
    return {"status": "completed", "dataset_size": len(qa), "evaluation_questions": len(evaluation), "chunks": len(chunks), "output_dir": str(output), "teacher_model": cfg.teacher_model, "student_model": cfg.student_model}


__all__ = ["PaperContext", "load_paper_context", "build_document_chunks", "generate_qa_records", "generate_evaluation_records", "create_dataset", "NOT_SPECIFIED"]