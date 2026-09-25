"""Student inference and grounded RAG answer helpers."""
from __future__ import annotations

from typing import Any
import json
from pathlib import Path


def student_inference_status(checkpoint_dir: str) -> dict[str, Any]:
    from pathlib import Path

    path = Path(checkpoint_dir)
    adapter = path / "student" / "adapter_model.safetensors"
    pytorch = path / "student" / "adapter_model.bin"
    available = adapter.exists() or pytorch.exists()
    return {"available": available, "status": "ready" if available else "blocked_training", "checkpoint": str(path / "student")}


def answer_with_grounding(question: str, retrieved_chunks: list[dict[str, Any]], student_ready: bool = False) -> dict[str, Any]:
    """Return a grounded answer and page citations without pretending an untrained student exists."""
    if not student_ready:
        return {"status": "blocked_training", "answer": "Student inference unavailable because no trained checkpoint exists.", "source_pages": sorted({int(c.get("page", 1)) for c in retrieved_chunks}), "model": None}
    evidence = " ".join(str(c.get("text", "")) for c in retrieved_chunks)
    return {"status": "ready", "answer": evidence[:1200], "source_pages": sorted({int(c.get("page", 1)) for c in retrieved_chunks}), "model": "distilled-student"}


def run_student_inference(
    evaluation_path: str | Path,
    output_path: str | Path,
    checkpoint_dir: str | Path,
    model_name: str = "Qwen/Qwen2.5-0.5B-Instruct",
    max_new_tokens: int = 96,
) -> dict[str, Any]:
    """Load the saved LoRA adapter and answer every evaluation record."""
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    checkpoint = Path(checkpoint_dir)
    try:
        tokenizer = AutoTokenizer.from_pretrained(checkpoint, trust_remote_code=True)
    except ValueError:
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    base = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=quantization,
        device_map="auto",
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(base, checkpoint)
    model.eval()
    device = next(model.parameters()).device
    answers: list[dict[str, Any]] = []
    records = [json.loads(line) for line in Path(evaluation_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    for record in records:
        prompt = f"### Instruction\n{record.get('instruction', '')}\n### Question\n{record.get('input', '')}\n### Evidence\n{record.get('evidence', '')}\n### Answer\n"
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(device)
        with torch.inference_mode():
            generated = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=tokenizer.pad_token_id)
        answer = tokenizer.decode(generated[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        answers.append({"question": record.get("input"), "answer": answer, "source_pages": record.get("source_pages", []), "model": model_name, "status": "completed"})
    Path(output_path).write_text("".join(json.dumps(item, ensure_ascii=True) + "\n" for item in answers), encoding="utf-8")
    return {"status": "completed", "questions": len(answers), "output_path": str(output_path), "model": model_name}


__all__ = ["student_inference_status", "answer_with_grounding", "run_student_inference"]