import argparse
import csv
import json
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


Quad = Tuple[str, str, str, str]


def read_split(path: Path) -> List[Quad]:
    rows: List[Quad] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for index, parts in enumerate(reader, start=1):
            if len(parts) != 4:
                raise ValueError(f"{path} line {index} does not have 4 columns")
            rows.append((parts[0], parts[1], parts[2], parts[3]))
    return rows


def split_stats(rows: List[Quad]) -> Dict[str, object]:
    rel_counter = Counter(r for _, r, _, _ in rows)
    patients = {s for s, _, _, _ in rows}
    objects = {o for _, _, o, _ in rows}
    dates = {t for _, _, _, t in rows}
    patient_dates = defaultdict(set)
    for s, _, _, t in rows:
        patient_dates[s].add(t)

    multi_visit_patients = sum(1 for ts in patient_dates.values() if len(ts) > 1)

    return {
        "rows": len(rows),
        "patients": len(patients),
        "relations": len(rel_counter),
        "objects": len(objects),
        "dates": len(dates),
        "multi_visit_patients": multi_visit_patients,
        "top_relations": rel_counter.most_common(10),
    }


def detect_wide_table_pattern(all_rows: List[Quad]) -> Dict[str, object]:
    rel_counter = Counter(r for _, r, _, _ in all_rows)
    counts = list(rel_counter.values())
    identical_count_relations = 0
    if counts:
        most_common_count = Counter(counts).most_common(1)[0][1]
        identical_count_relations = most_common_count

    object_vocab = len({o for _, _, o, _ in all_rows})
    patient_vocab = len({s for s, _, _, _ in all_rows})
    dates = len({t for _, _, _, t in all_rows})
    avg_events_per_patient = len(all_rows) / max(patient_vocab, 1)
    avg_events_per_day = len(all_rows) / max(dates, 1)

    flags = []
    if identical_count_relations >= max(8, len(rel_counter) // 2):
        flags.append("many relations have exactly the same frequency, which is typical for wide-table feature expansion")
    if object_vocab <= 50:
        flags.append("object vocabulary is very small for a clinical TKG")
    if avg_events_per_patient >= 100:
        flags.append("event density per patient is high and may come from one-row-to-many-feature expansion")

    verdict = "suitable"
    if flags:
        verdict = "partially_suitable"
    if len(flags) >= 2:
        verdict = "weak_for_clinical_claims"

    return {
        "verdict": verdict,
        "avg_events_per_patient": round(avg_events_per_patient, 2),
        "avg_events_per_day": round(avg_events_per_day, 2),
        "identical_count_relations": identical_count_relations,
        "flags": flags,
    }


def evaluate_dataset(train_rows: List[Quad], valid_rows: List[Quad], test_rows: List[Quad]) -> Dict[str, object]:
    all_rows = train_rows + valid_rows + test_rows
    train_dates = {t for _, _, _, t in train_rows}
    valid_dates = {t for _, _, _, t in valid_rows}
    test_dates = {t for _, _, _, t in test_rows}

    split_leakage = bool(train_dates & valid_dates or train_dates & test_dates or valid_dates & test_dates)
    date_order_ok = True
    if train_dates and valid_dates and test_dates:
        date_order_ok = max(train_dates) <= min(valid_dates) and max(valid_dates) <= min(test_dates)

    structure_fit = {
        "all_rows_have_four_columns": True,
        "time_split_leakage": split_leakage,
        "chronological_split": date_order_ok,
    }

    suitability = detect_wide_table_pattern(all_rows)

    recommendation = []
    if suitability["verdict"] == "suitable":
        recommendation.append("dataset can be used for both system demo and model comparison")
    else:
        recommendation.append("dataset is acceptable for system demo and algorithm migration")
        recommendation.append("do not over-claim clinical effectiveness from this dataset alone")
        recommendation.append("if the paper needs stronger medical evidence, add a real longitudinal clinical dataset")

    return {
        "structure_fit": structure_fit,
        "suitability": suitability,
        "recommendation": recommendation,
    }


def render_markdown(dataset_name: str, stats: Dict[str, Dict[str, object]], evaluation: Dict[str, object]) -> str:
    lines = [
        f"# {dataset_name} Data Audit",
        "",
        "## Split Stats",
        "",
        "| Split | Rows | Patients | Relations | Objects | Dates | Multi-visit Patients |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for split_name in ("train", "valid", "test"):
        split = stats[split_name]
        lines.append(
            f"| {split_name} | {split['rows']} | {split['patients']} | {split['relations']} | "
            f"{split['objects']} | {split['dates']} | {split['multi_visit_patients']} |"
        )

    lines.extend(
        [
            "",
            "## Suitability",
            "",
            f"- Verdict: `{evaluation['suitability']['verdict']}`",
            f"- Chronological split: `{evaluation['structure_fit']['chronological_split']}`",
            f"- Split leakage: `{evaluation['structure_fit']['time_split_leakage']}`",
            f"- Average events per patient: `{evaluation['suitability']['avg_events_per_patient']}`",
            f"- Average events per day: `{evaluation['suitability']['avg_events_per_day']}`",
            "",
            "## Flags",
        ]
    )

    if evaluation["suitability"]["flags"]:
        for flag in evaluation["suitability"]["flags"]:
            lines.append(f"- {flag}")
    else:
        lines.append("- no structural warning triggered")

    lines.extend(["", "## Recommendation"])
    for item in evaluation["recommendation"]:
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit whether a TKG dataset is suitable for CTpath experiments")
    parser.add_argument("--dataset", type=str, default="CHRONIC")
    parser.add_argument("--data_dir", type=str, default="")
    parser.add_argument("--report", type=str, default="")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    data_dir = Path(args.data_dir) if args.data_dir else project_root / "data" / args.dataset

    train_rows = read_split(data_dir / "train")
    valid_rows = read_split(data_dir / "valid")
    test_rows = read_split(data_dir / "test")

    stats = {
        "train": split_stats(train_rows),
        "valid": split_stats(valid_rows),
        "test": split_stats(test_rows),
    }
    evaluation = evaluate_dataset(train_rows, valid_rows, test_rows)

    payload = {
        "dataset": args.dataset,
        "stats": stats,
        "evaluation": evaluation,
    }

    print(json.dumps(payload, indent=2, ensure_ascii=False))

    report_path = Path(args.report) if args.report else project_root / "results" / f"{args.dataset}_data_audit.md"
    content = render_markdown(args.dataset, stats, evaluation)
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(content, encoding="utf-8")
        print(f"Markdown report saved to {report_path}")
    except PermissionError:
        fallback_path = Path(tempfile.gettempdir()) / f"{args.dataset}_data_audit.generated.md"
        fallback_path.write_text(content, encoding="utf-8")
        print(f"Report file is busy, wrote fallback report to {fallback_path}")


if __name__ == "__main__":
    main()
