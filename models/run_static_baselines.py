import argparse
import json
import random
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.baseline.rotate import RotatE
from models.baseline.trainer import BaselineTrainer, load_data
from models.baseline.transe import TransE


MetricDict = Dict[str, float]


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def add_reciprocal_facts(data: torch.LongTensor, relation_offset: int) -> torch.LongTensor:
    reciprocal = data.clone()
    reciprocal[:, 0], reciprocal[:, 2] = data[:, 2], data[:, 0]
    reciprocal[:, 1] = data[:, 1] + relation_offset
    return reciprocal


def build_bidirectional_filters(
    train_data: torch.LongTensor,
    valid_data: torch.LongTensor,
    test_data: torch.LongTensor,
    relation_offset: int,
) -> Dict[Tuple[int, int, int], List[int]]:
    filters: Dict[Tuple[int, int, int], List[int]] = {}
    all_data = torch.cat([train_data, valid_data, test_data], dim=0)
    all_augmented = torch.cat([all_data, add_reciprocal_facts(all_data, relation_offset)], dim=0)

    for quad in all_augmented:
        h = int(quad[0].item())
        r = int(quad[1].item())
        t = int(quad[2].item())
        ts = int(quad[3].item()) if quad.shape[0] > 3 else 0
        key = (h, r, ts)
        filters.setdefault(key, []).append(t)

    return filters


def average_metrics(lhs: MetricDict, rhs: MetricDict) -> MetricDict:
    metrics: MetricDict = {
        "MRR": float((lhs["MRR"] + rhs["MRR"]) / 2.0),
        "num_samples": float(lhs["num_samples"] + rhs["num_samples"]),
    }
    for key in ("Hits@1", "Hits@3", "Hits@10"):
        metrics[key] = float((lhs[key] + rhs[key]) / 2.0)
    return metrics


def evaluate_bidirectional(
    trainer: BaselineTrainer,
    data: torch.LongTensor,
    filters: Dict[Tuple[int, int, int], List[int]],
    relation_offset: int,
    batch_size: int,
    split_name: str,
) -> MetricDict:
    tail_metrics = trainer.evaluator.evaluate(
        data,
        filters,
        batch_size=batch_size,
        desc=f"{split_name}-tail",
    )
    head_queries = add_reciprocal_facts(data, relation_offset)
    head_metrics = trainer.evaluator.evaluate(
        head_queries,
        filters,
        batch_size=batch_size,
        desc=f"{split_name}-head",
    )
    return average_metrics(tail_metrics, head_metrics)


def build_model(
    model_name: str,
    num_entities: int,
    num_relations: int,
    embedding_dim: int,
    margin: float,
    device: str,
):
    is_cuda = device.startswith("cuda")
    if model_name == "TransE":
        return TransE(
            num_entities=num_entities,
            num_relations=num_relations,
            embedding_dim=embedding_dim,
            margin=margin,
            is_cuda=is_cuda,
        )
    if model_name == "RotatE":
        return RotatE(
            num_entities=num_entities,
            num_relations=num_relations,
            embedding_dim=embedding_dim,
            margin=margin,
            is_cuda=is_cuda,
        )
    raise ValueError(f"Unsupported baseline model: {model_name}")


def run_single_model(
    model_name: str,
    dataset_name: str,
    train_data: torch.LongTensor,
    valid_data: torch.LongTensor,
    test_data: torch.LongTensor,
    num_entities: int,
    num_relations: int,
    args: argparse.Namespace,
    result_dir: Path,
) -> Dict[str, object]:
    relation_offset = num_relations
    model_relations = num_relations * 2

    train_augmented = torch.cat(
        [train_data, add_reciprocal_facts(train_data, relation_offset)],
        dim=0,
    )
    filters = build_bidirectional_filters(train_data, valid_data, test_data, relation_offset)

    model = build_model(
        model_name=model_name,
        num_entities=num_entities,
        num_relations=model_relations,
        embedding_dim=args.embedding_dim,
        margin=args.margin,
        device=args.device,
    )

    trainer = BaselineTrainer(
        model=model,
        model_name=model_name,
        dataset_name=dataset_name,
        num_entities=num_entities,
        num_relations=model_relations,
        device=args.device,
        lr=args.learning_rate,
        margin=args.margin,
        num_neg=args.num_neg,
    )

    model_dir = result_dir / model_name
    model_dir.mkdir(parents=True, exist_ok=True)
    best_model_path = model_dir / "best.pt"

    best_valid_mrr = -1.0
    best_epoch = -1
    best_valid_metrics: MetricDict = {}
    patience_counter = 0

    history: List[Dict[str, float]] = []

    print(f"\nRunning {model_name} on {dataset_name}")
    print("=" * 60)

    for epoch in range(args.max_epochs):
        avg_loss = trainer.train_epoch(
            train_augmented,
            batch_size=args.batch_size,
            epoch=epoch,
        )
        valid_metrics = evaluate_bidirectional(
            trainer,
            valid_data,
            filters,
            relation_offset,
            args.batch_size,
            "valid",
        )

        history.append(
            {
                "epoch": epoch,
                "train_loss": avg_loss,
                "valid_mrr": valid_metrics["MRR"],
                "valid_hits@1": valid_metrics["Hits@1"],
                "valid_hits@3": valid_metrics["Hits@3"],
                "valid_hits@10": valid_metrics["Hits@10"],
            }
        )

        print(
            f"Epoch {epoch}: loss={avg_loss:.4f}, "
            f"MRR={valid_metrics['MRR']:.4f}, "
            f"Hits@10={valid_metrics['Hits@10']:.4f}"
        )

        if valid_metrics["MRR"] > best_valid_mrr:
            best_valid_mrr = valid_metrics["MRR"]
            best_epoch = epoch
            best_valid_metrics = valid_metrics
            patience_counter = 0
            torch.save(trainer.model.state_dict(), best_model_path)
            print(f"  -> best checkpoint saved to {best_model_path}")
        else:
            patience_counter += 1

        if patience_counter >= args.early_stop_patience:
            print(f"Early stopping at epoch {epoch}")
            break

    trainer.model.load_state_dict(torch.load(best_model_path, map_location=args.device))
    test_metrics = evaluate_bidirectional(
        trainer,
        test_data,
        filters,
        relation_offset,
        args.batch_size,
        "test",
    )

    output = {
        "model": model_name,
        "dataset": dataset_name,
        "embedding_dim": args.embedding_dim,
        "learning_rate": args.learning_rate,
        "margin": args.margin,
        "batch_size": args.batch_size,
        "num_neg": args.num_neg,
        "max_epochs": args.max_epochs,
        "best_epoch": best_epoch,
        "reciprocal_training": True,
        "checkpoint": str(best_model_path),
        "valid": best_valid_metrics,
        "test": test_metrics,
        "history": history,
    }

    with open(model_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return output


def write_summary(result_dir: Path, results: List[Dict[str, object]]) -> None:
    comparison = []
    for item in results:
        comparison.append(
            {
                "model": item["model"],
                "valid_mrr": item["valid"]["MRR"],
                "test_mrr": item["test"]["MRR"],
                "test_hits@1": item["test"]["Hits@1"],
                "test_hits@3": item["test"]["Hits@3"],
                "test_hits@10": item["test"]["Hits@10"],
            }
        )

    comparison.sort(key=lambda x: x["test_mrr"], reverse=True)

    with open(result_dir / "comparison.json", "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)

    lines = [
        "# Static KG Baseline Comparison",
        "",
        "| Model | Valid MRR | Test MRR | Hits@1 | Hits@3 | Hits@10 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in comparison:
        lines.append(
            "| {model} | {valid_mrr:.4f} | {test_mrr:.4f} | {test_hits@1:.4f} | "
            "{test_hits@3:.4f} | {test_hits@10:.4f} |".format(**item)
        )

    lines.extend(
        [
            "",
            "Notes:",
            "- Reciprocal triples are added during training.",
            "- Validation and test metrics are averaged over tail prediction and reciprocal head prediction.",
            "- These baselines are static KG models chosen to satisfy the task book comparison requirement.",
        ]
    )

    with open(result_dir / "comparison.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run static KG baselines for CTpath datasets")
    parser.add_argument("--dataset", type=str, default="CHRONIC")
    parser.add_argument("--dataset_path", type=str, default="")
    parser.add_argument("--output_dir", type=str, default="")
    parser.add_argument("--models", type=str, default="TransE,RotatE")
    parser.add_argument("--embedding_dim", type=int, default=200)
    parser.add_argument("--learning_rate", type=float, default=0.001)
    parser.add_argument("--margin", type=float, default=1.0)
    parser.add_argument("--num_neg", type=int, default=4)
    parser.add_argument("--max_epochs", type=int, default=50)
    parser.add_argument("--batch_size", type=int, default=1024)
    parser.add_argument("--early_stop_patience", type=int, default=8)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    set_seed(args.seed)

    project_root = PROJECT_ROOT
    dataset_path = Path(args.dataset_path) if args.dataset_path else project_root / "data" / args.dataset
    dataset_name = args.dataset

    train_data, valid_data, test_data, num_entities, num_relations = load_data(str(dataset_path))

    timestamp = int(time.time())
    output_root = Path(args.output_dir) if args.output_dir else project_root / "results" / "baseline_results"
    result_dir = output_root / f"{dataset_name}_{timestamp}"
    try:
        result_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        temp_root = Path(tempfile.gettempdir()) / "ctpath_baseline_results"
        result_dir = temp_root / f"{dataset_name}_{timestamp}"
        result_dir.mkdir(parents=True, exist_ok=True)
        print(f"Output directory is not writable, falling back to {result_dir}")

    meta = {
        "dataset": dataset_name,
        "dataset_path": str(dataset_path),
        "num_entities": num_entities,
        "num_relations": num_relations,
        "device": args.device,
        "seed": args.seed,
    }
    with open(result_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    results = []
    for model_name in [m.strip() for m in args.models.split(",") if m.strip()]:
        results.append(
            run_single_model(
                model_name=model_name,
                dataset_name=dataset_name,
                train_data=train_data,
                valid_data=valid_data,
                test_data=test_data,
                num_entities=num_entities,
                num_relations=num_relations,
                args=args,
                result_dir=result_dir,
            )
        )

    write_summary(result_dir, results)
    print(f"\nBaseline comparison finished. Results saved to {result_dir}")


if __name__ == "__main__":
    main()
