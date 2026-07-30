"""Transparent PyTorch fine-tuning loop for the multilingual Cross-Encoder."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import time
from typing import Any, Iterable

import numpy as np
import torch
from sentence_transformers import CrossEncoder


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def flatten_examples(groups: Iterable[dict[str, Any]]) -> list[tuple[str, str, float]]:
    examples: list[tuple[str, str, float]] = []
    for group in groups:
        question = str(group["question"])
        examples.append((question, str(group["positive"]), 1.0))
        examples.extend(
            (question, str(negative), 0.0)
            for negative in group.get("negatives", [])
        )
    return examples


def mrr_at_k_from_group_scores(
    group_scores: Iterable[tuple[float, list[float]]],
    *,
    k: int = 5,
) -> float:
    reciprocal_ranks: list[float] = []
    for positive_score, negative_scores in group_scores:
        ranked = sorted(
            [(positive_score, True)]
            + [(score, False) for score in negative_scores],
            key=lambda item: item[0],
            reverse=True,
        )
        positive_rank = next(
            rank for rank, (_, is_positive) in enumerate(ranked, start=1) if is_positive
        )
        reciprocal_ranks.append(1.0 / positive_rank if positive_rank <= k else 0.0)
    return sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0


def checkpoint_tree_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(file for file in path.rglob("*") if file.is_file())
    if not files:
        raise ValueError(f"checkpoint directory is empty: {path}")
    for file in files:
        digest.update(file.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        with file.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def _weight_probe(model: torch.nn.Module) -> str:
    parameter = next(parameter for parameter in model.parameters() if parameter.requires_grad)
    value = parameter.detach().float().cpu().numpy().tobytes()
    return hashlib.sha256(value).hexdigest()


def _batch_ranges(total: int, batch_size: int):
    for start in range(0, total, batch_size):
        yield start, min(total, start + batch_size)


def evaluate_groups(
    cross_encoder: CrossEncoder,
    groups: list[dict[str, Any]],
    *,
    batch_size: int = 16,
) -> float:
    score_groups: list[tuple[float, list[float]]] = []
    for group in groups:
        passages = [group["positive"], *group.get("negatives", [])]
        pairs = [[group["question"], passage] for passage in passages]
        scores = cross_encoder.predict(
            pairs,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        values = np.asarray(scores, dtype=np.float32).reshape(-1).tolist()
        score_groups.append((values[0], values[1:]))
    return mrr_at_k_from_group_scores(score_groups, k=5)


def train(
    *,
    model_name: str,
    train_groups: list[dict[str, Any]],
    dev_groups: list[dict[str, Any]],
    output_dir: Path,
    artifact_dir: Path,
    run_name: str,
    epochs: int,
    batch_size: int,
    gradient_accumulation: int,
    learning_rate: float,
    max_length: int,
    seed: int,
    device: str,
    fp16: bool,
) -> dict[str, Any]:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.cuda.reset_peak_memory_stats()

    cross_encoder = CrossEncoder(
        model_name,
        num_labels=1,
        max_length=max_length,
        device=device,
    )
    model = cross_encoder.model
    tokenizer = cross_encoder.tokenizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    loss_function = torch.nn.BCEWithLogitsLoss()
    scaler = torch.amp.GradScaler(
        "cuda",
        enabled=fp16 and device.startswith("cuda"),
    )

    examples = flatten_examples(train_groups)
    before_probe = _weight_probe(model)
    base_validation_mrr = evaluate_groups(cross_encoder, dev_groups)
    global_step = 0
    best_validation_mrr = -1.0
    best_epoch = 0
    history: list[dict[str, Any]] = []
    best_dir = output_dir / "best"
    started_run = time.perf_counter()

    for epoch in range(1, epochs + 1):
        epoch_started = time.perf_counter()
        rng = random.Random(seed + epoch)
        rng.shuffle(examples)
        model.train()
        optimizer.zero_grad(set_to_none=True)
        total_loss = 0.0
        micro_batches = 0

        for batch_number, (start, end) in enumerate(
            _batch_ranges(len(examples), batch_size),
            start=1,
        ):
            batch = examples[start:end]
            questions = [item[0] for item in batch]
            passages = [item[1] for item in batch]
            labels = torch.tensor(
                [item[2] for item in batch],
                dtype=torch.float32,
                device=device,
            )
            encoded = tokenizer(
                questions,
                passages,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt",
            )
            encoded = {key: value.to(device) for key, value in encoded.items()}

            with torch.amp.autocast(
                device_type="cuda",
                dtype=torch.float16,
                enabled=fp16 and device.startswith("cuda"),
            ):
                logits = model(**encoded).logits.reshape(-1)
                raw_loss = loss_function(logits, labels)
                loss = raw_loss / gradient_accumulation

            scaler.scale(loss).backward()
            total_loss += float(raw_loss.detach().cpu())
            micro_batches += 1

            should_step = (
                batch_number % gradient_accumulation == 0
                or end == len(examples)
            )
            if should_step:
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
                global_step += 1

        validation_mrr = evaluate_groups(cross_encoder, dev_groups)
        epoch_dir = output_dir / f"epoch-{epoch}"
        cross_encoder.save_pretrained(
            str(epoch_dir),
            create_model_card=False,
            safe_serialization=True,
        )
        if validation_mrr > best_validation_mrr:
            best_validation_mrr = validation_mrr
            best_epoch = epoch
            cross_encoder.save_pretrained(
                str(best_dir),
                create_model_card=False,
                safe_serialization=True,
            )

        history.append(
            {
                "epoch": epoch,
                "train_loss": total_loss / max(1, micro_batches),
                "validation_mrr@5": validation_mrr,
                "global_step": global_step,
                "epoch_seconds": time.perf_counter() - epoch_started,
            }
        )

    after_probe = _weight_probe(model)
    checkpoint_sha256 = checkpoint_tree_sha256(best_dir)
    reloaded = CrossEncoder(str(best_dir), device=device)
    reload_score = float(
        np.asarray(
            reloaded.predict(
                [[dev_groups[0]["question"], dev_groups[0]["positive"]]],
                show_progress_bar=False,
                convert_to_numpy=True,
            )
        ).reshape(-1)[0]
    )
    peak_vram_bytes = (
        int(torch.cuda.max_memory_allocated())
        if torch.cuda.is_available() and device.startswith("cuda")
        else 0
    )

    artifact_dir.mkdir(parents=True, exist_ok=True)
    history_path = artifact_dir / f"{run_name}_training_history.csv"
    with history_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(history[0]))
        writer.writeheader()
        writer.writerows(history)

    config = {
        "model_name": model_name,
        "run_name": run_name,
        "epochs": epochs,
        "batch_size": batch_size,
        "gradient_accumulation": gradient_accumulation,
        "learning_rate": learning_rate,
        "max_length": max_length,
        "seed": seed,
        "device": device,
        "fp16": fp16,
        "train_groups": len(train_groups),
        "dev_groups": len(dev_groups),
    }
    (artifact_dir / f"{run_name}_config.json").write_text(
        json.dumps(config, indent=2) + "\n",
        encoding="utf-8",
    )
    result = {
        **config,
        "global_step": global_step,
        "base_validation_mrr@5": base_validation_mrr,
        "best_epoch": best_epoch,
        "best_validation_mrr@5": best_validation_mrr,
        "checkpoint_path": best_dir.as_posix(),
        "checkpoint_sha256": checkpoint_sha256,
        "weight_probe_before": before_probe,
        "weight_probe_after": after_probe,
        "weights_changed": before_probe != after_probe,
        "checkpoint_reloaded": True,
        "reload_score": reload_score,
        "peak_vram_bytes": peak_vram_bytes,
        "run_seconds": time.perf_counter() - started_run,
    }
    (artifact_dir / f"{run_name}_result.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    (artifact_dir / f"{run_name}_checkpoint.sha256").write_text(
        f"{checkpoint_sha256}  {best_dir.as_posix()}\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Fine-tune the approved reranker")
    parser.add_argument(
        "--model-name",
        default="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
    )
    parser.add_argument(
        "--train-groups",
        type=Path,
        default=Path(".cache/reranker/groups/train.jsonl"),
    )
    parser.add_argument(
        "--dev-groups",
        type=Path,
        default=Path(".cache/reranker/groups/dev.jsonl"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("checkpoints/reranker"),
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path("artifacts/reranker"),
    )
    parser.add_argument("--run-name", default="smoke")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--gradient-accumulation", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--fp16", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-train-groups", type=int, default=0)
    parser.add_argument("--max-dev-groups", type=int, default=0)
    args = parser.parse_args()

    train_groups = load_jsonl(args.train_groups)
    dev_groups = load_jsonl(args.dev_groups)
    if args.max_train_groups > 0:
        train_groups = train_groups[: args.max_train_groups]
    if args.max_dev_groups > 0:
        dev_groups = dev_groups[: args.max_dev_groups]
    if not train_groups or not dev_groups:
        print(json.dumps({"error": "train/dev groups are empty"}, indent=2))
        return 2

    result = train(
        model_name=args.model_name,
        train_groups=train_groups,
        dev_groups=dev_groups,
        output_dir=args.output_dir / args.run_name,
        artifact_dir=args.artifact_dir,
        run_name=args.run_name,
        epochs=args.epochs,
        batch_size=args.batch_size,
        gradient_accumulation=args.gradient_accumulation,
        learning_rate=args.learning_rate,
        max_length=args.max_length,
        seed=args.seed,
        device=args.device,
        fp16=args.fp16,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["global_step"] > 0 and result["weights_changed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
