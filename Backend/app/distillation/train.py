"""Optional QLoRA training gate for the paper-QA student model."""
from __future__ import annotations

import importlib.util
import json
import platform
import time
from typing import Any

from .config import PaperDistillationConfig


def inspect_runtime() -> dict[str, Any]:
    result: dict[str, Any] = {
        "python": platform.python_version(),
        "cuda_available": False,
        "gpu": None,
        "vram_gb": None,
        "torch": None,
        "transformers": None,
        "peft_available": importlib.util.find_spec("peft") is not None,
        "bitsandbytes_available": importlib.util.find_spec("bitsandbytes") is not None,
        "datasets_available": importlib.util.find_spec("datasets") is not None,
    }
    try:
        import torch

        result["torch"] = getattr(torch, "__version__", "unknown")
        result["cuda_available"] = bool(torch.cuda.is_available())
        if result["cuda_available"]:
            props = torch.cuda.get_device_properties(0)
            result["gpu"] = props.name
            result["vram_gb"] = round(props.total_memory / (1024**3), 2)
    except Exception as exc:
        result["torch_error"] = str(exc)
    try:
        import transformers

        result["transformers"] = getattr(transformers, "__version__", "unknown")
    except Exception as exc:
        result["transformers_error"] = str(exc)
    return result


def training_block_reason(runtime: dict[str, Any]) -> str | None:
    missing: list[str] = []
    if not runtime.get("cuda_available"):
        missing.append("CUDA GPU (PyTorch reports CPU-only runtime)")
    if not runtime.get("peft_available"):
        missing.append("peft")
    if not runtime.get("bitsandbytes_available"):
        missing.append("bitsandbytes")
    if missing:
        return "QLoRA training was not executed: missing " + ", ".join(missing) + "."
    return None


def run_qlora_training(config: PaperDistillationConfig | None = None) -> dict[str, Any]:
    """Run only when the required GPU/QLoRA stack is genuinely available."""
    cfg = config or PaperDistillationConfig()
    runtime = inspect_runtime()
    output = cfg.output_path / "student"
    output.mkdir(parents=True, exist_ok=True)
    training_config = {**cfg.model_dump(), "runtime": runtime, "status": "not_started"}
    (output / "training_config.json").write_text(json.dumps(training_config, indent=2), encoding="utf-8")
    reason = training_block_reason(runtime)
    if reason:
        metrics = {"status": "blocked_training", "actual_fine_tuning": False, "reason": reason, "runtime": runtime}
        (output / "training_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return metrics
    started = time.time()
    try:
        import bitsandbytes  # noqa: F401
        import peft
        import torch
        from datasets import load_dataset
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            DataCollatorForLanguageModeling,
            Trainer,
            TrainingArguments,
        )
    except Exception as exc:
        metrics = {"status": "blocked_training", "actual_fine_tuning": False, "reason": f"QLoRA imports failed: {exc}", "runtime": runtime}
        (output / "training_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return metrics
    try:
        train_file = str(cfg.output_path / "teacher_dataset_train.jsonl")
        validation_file = str(cfg.output_path / "teacher_dataset_validation.jsonl")
        tokenizer = AutoTokenizer.from_pretrained(cfg.student_model, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        quantization = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            cfg.student_model,
            quantization_config=quantization,
            device_map="auto",
            trust_remote_code=True,
        )
        model.config.use_cache = False
        model = prepare_model_for_kbit_training(model)
        lora = LoraConfig(
            r=4,
            lora_alpha=8,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        )
        model = get_peft_model(model, lora)
        model.gradient_checkpointing_enable()

        def format_record(record: dict[str, Any]) -> str:
            return f"### Instruction\n{record.get('instruction', '')}\n### Question\n{record.get('input', '')}\n### Answer\n{record.get('output', '')}"

        def tokenize(batch: dict[str, list[Any]]) -> dict[str, Any]:
            texts = [format_record({key: values[index] for key, values in batch.items()}) for index in range(len(batch["input"]))]
            return tokenizer(texts, truncation=True, max_length=cfg.max_seq_length, padding=False)

        train_raw = load_dataset("json", data_files=train_file, split="train")
        validation_raw = load_dataset("json", data_files=validation_file, split="train")
        train_data = train_raw.map(tokenize, batched=True, remove_columns=train_raw.column_names)
        validation_data = validation_raw.map(tokenize, batched=True, remove_columns=validation_raw.column_names)
        arguments = TrainingArguments(
            output_dir=str(output / "trainer"),
            num_train_epochs=cfg.epochs,
            per_device_train_batch_size=cfg.batch_size,
            per_device_eval_batch_size=cfg.batch_size,
            gradient_accumulation_steps=cfg.gradient_accumulation_steps,
            learning_rate=cfg.learning_rate,
            fp16=True,
            gradient_checkpointing=True,
            logging_steps=1,
            save_strategy="epoch",
            eval_strategy="epoch",
            report_to=[],
            remove_unused_columns=False,
        )
        trainer = Trainer(
            model=model,
            args=arguments,
            train_dataset=train_data,
            eval_dataset=validation_data,
            data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
        )
        train_result = trainer.train()
        model.save_pretrained(output)
        tokenizer.save_pretrained(output)
        metrics = {
            "status": "completed",
            "actual_fine_tuning": True,
            "student_model": cfg.student_model,
            "trainable_parameters": sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad),
            "total_parameters": sum(parameter.numel() for parameter in model.parameters()),
            "training_loss": float(train_result.training_loss),
            "duration_seconds": round(time.time() - started, 2),
            "runtime": runtime,
            "batch_size": cfg.batch_size,
            "gradient_accumulation_steps": cfg.gradient_accumulation_steps,
            "max_seq_length": cfg.max_seq_length,
        }
    except torch.cuda.OutOfMemoryError as exc:
        torch.cuda.empty_cache()
        metrics = {"status": "failed_training", "actual_fine_tuning": False, "reason": f"CUDA out of memory on RTX 3050 4GB: {exc}", "duration_seconds": round(time.time() - started, 2), "runtime": runtime}
    except Exception as exc:
        metrics = {"status": "failed_training", "actual_fine_tuning": False, "reason": str(exc), "duration_seconds": round(time.time() - started, 2), "runtime": runtime}
    (output / "training_metrics.json").write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")
    return metrics


__all__ = ["inspect_runtime", "training_block_reason", "run_qlora_training"]