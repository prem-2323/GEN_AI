"""Paper-QA distillation orchestration and report generation."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import PaperDistillationConfig
from .dataset_generator import create_dataset, load_paper_context
from .evaluate import compare_answers
from .inference import run_student_inference
from .teacher import OllamaTeacher
from .train import run_qlora_training


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(record, ensure_ascii=True) + "\n" for record in records), encoding="utf-8")


def run_paper_test(project_id: str, source_id: str, config: PaperDistillationConfig | None = None) -> dict[str, Any]:
    cfg = config or PaperDistillationConfig()
    dataset_result = create_dataset(project_id, source_id, cfg)
    output = Path(dataset_result["output_dir"])
    context = load_paper_context(project_id, source_id)
    evaluation = [json.loads(line) for line in (output / "evaluation_questions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    teacher = OllamaTeacher(cfg.teacher_model)
    teacher_answers: list[dict[str, Any]] = []
    for record in evaluation:
        result = teacher.answer(record["input"], record["evidence"], record["source_pages"])
        teacher_answers.append({"question": record["input"], "answer": result.get("answer", "") if result else "", "source_pages": record["source_pages"], "teacher_status": "completed" if result else "failed"})
    _write_jsonl(output / "teacher_answers.jsonl", teacher_answers)
    training = run_qlora_training(cfg)
    student_answers: list[dict[str, Any]] = []
    if training.get("status") == "completed":
        run_student_inference(output / "evaluation_questions.jsonl", output / "student_answers.jsonl", output / "student", cfg.student_model)
        student_answers = [json.loads(line) for line in (output / "student_answers.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    else:
        _write_jsonl(output / "student_answers.jsonl", student_answers)
    metrics = compare_answers(evaluation, teacher_answers, student_answers, output / "comparison.jsonl")
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "pdf": context.filename, "project_id": project_id, "source_id": source_id, "teacher_model": cfg.teacher_model, "student_model": cfg.student_model, "dataset_size": dataset_result["dataset_size"], "evaluation_questions": dataset_result["evaluation_questions"], "chunks": dataset_result["chunks"], "teacher_answers_completed": sum(item["teacher_status"] == "completed" for item in teacher_answers), "training": training, "metrics": metrics, "actual_fine_tuning": bool(training.get("actual_fine_tuning")), "limitations": ["Student inference and teacher-vs-student scoring are unavailable until QLoRA training completes."] if training.get("status") != "completed" else []}
    (output / "final_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    (output / "final_report.md").write_text("# Document Distillation Test Report\n\n" + f"- PDF: `{context.filename}`\n- Teacher: `{cfg.teacher_model}`\n- Student: `{cfg.student_model}`\n- Dataset records: {dataset_result['dataset_size']}\n- Evaluation questions: {dataset_result['evaluation_questions']}\n- Chunks: {dataset_result['chunks']}\n- Teacher answers completed: {report['teacher_answers_completed']}\n- Training status: `{training.get('status')}`\n- Actual fine-tuning: `{report['actual_fine_tuning']}`\n\nTraining limitation: {training.get('reason', 'none')}\n\nStudent checkpoint: not created unless actual training completes.\n", encoding="utf-8")
    return report


__all__ = ["run_paper_test"]