#!/usr/bin/env python3
"""Build CTpath-compatible temporal KG files from local chronic disease CSVs.

Outputs three tab-separated files (without suffix):
  data/CHRONIC/train
  data/CHRONIC/valid
  data/CHRONIC/test

Each line format:
  subject\trelation\tobject\ttimestamp
"""

import argparse
import csv
import math
import os
from collections import defaultdict
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

Event = Tuple[str, str, str, str]  # (s, r, o, t)


def _safe_str(v: object) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _norm_token(v: object, default: str = "UNK") -> str:
    s = _safe_str(v)
    if not s:
        return default
    s = s.replace("\t", " ").replace("\n", " ")
    s = "_".join(s.split())
    return s


def _parse_date(s: str) -> Optional[datetime]:
    s = _safe_str(s)
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def _quantile_thresholds(values: List[float], qs: Sequence[float]) -> List[float]:
    if not values:
        return [0.0 for _ in qs]
    xs = sorted(values)
    n = len(xs)
    outs = []
    for q in qs:
        idx = int(round(q * (n - 1)))
        idx = min(max(idx, 0), n - 1)
        outs.append(xs[idx])
    return outs


def _bin_value(x: float, cuts: Sequence[float]) -> str:
    if x <= cuts[0]:
        return "Q1"
    if x <= cuts[1]:
        return "Q2"
    if x <= cuts[2]:
        return "Q3"
    return "Q4"


def _collect_numeric_values(rows: List[Dict[str, str]], fields: Sequence[str]) -> Dict[str, List[float]]:
    store: Dict[str, List[float]] = {f: [] for f in fields}
    for row in rows:
        for f in fields:
            raw = _safe_str(row.get(f, ""))
            if not raw:
                continue
            try:
                store[f].append(float(raw))
            except ValueError:
                continue
    return store


def build_events_from_chronic(rows: List[Dict[str, str]]) -> List[Event]:
    numeric_fields = [
        "BiomarkerScore",
        "MedicationDose",
        "HeartRate",
        "BloodPressure_Systolic",
        "BloodPressure_Diastolic",
        "Cholesterol",
        "BMI",
        "SleepHours",
        "StepsPerDay",
        "StressLevel",
        "CognitiveScore",
        "MoodScore",
    ]

    num_values = _collect_numeric_values(rows, numeric_fields)
    cuts = {
        k: _quantile_thresholds(vs, (0.25, 0.5, 0.75))
        for k, vs in num_values.items()
    }

    cat_map = {
        "Disease": "has_disease",
        "MedicalHistory": "medical_history",
        "Lifestyle": "lifestyle",
        "MedicationAdherence": "med_adherence",
        "Stage": "stage",
        "Smoker": "smoker",
        "AlcoholUse": "alcohol_use",
        "SupportSystem": "support_system",
        "HasCaregiver": "has_caregiver",
        "EmploymentStatus": "employment_status",
        "Gender": "gender",
    }

    num_map = {
        "BiomarkerScore": "biomarker_bin",
        "MedicationDose": "med_dose_bin",
        "HeartRate": "heart_rate_bin",
        "BloodPressure_Systolic": "bp_sys_bin",
        "BloodPressure_Diastolic": "bp_dia_bin",
        "Cholesterol": "cholesterol_bin",
        "BMI": "bmi_bin",
        "SleepHours": "sleep_hours_bin",
        "StepsPerDay": "steps_bin",
        "StressLevel": "stress_bin",
        "CognitiveScore": "cognitive_bin",
        "MoodScore": "mood_bin",
    }

    events: List[Event] = []
    for row in rows:
        pid = _norm_token(row.get("PatientID"), "UNK_PATIENT")
        date_obj = _parse_date(_safe_str(row.get("Date", "")))
        if date_obj is None:
            continue
        t = date_obj.strftime("%Y-%m-%d")
        s = f"p_{pid}"

        age = _safe_str(row.get("Age", ""))
        if age:
            try:
                age_i = int(float(age))
                if age_i < 45:
                    age_bin = "age_lt45"
                elif age_i < 60:
                    age_bin = "age_45_59"
                elif age_i < 75:
                    age_bin = "age_60_74"
                else:
                    age_bin = "age_ge75"
                events.append((s, "age_group", age_bin, t))
            except ValueError:
                pass

        for src, rel in cat_map.items():
            val = _norm_token(row.get(src), "UNK")
            events.append((s, rel, val, t))

        for src, rel in num_map.items():
            raw = _safe_str(row.get(src, ""))
            if not raw:
                continue
            try:
                x = float(raw)
            except ValueError:
                continue
            events.append((s, rel, _bin_value(x, cuts[src]), t))

    return events


def _split_by_time(events: List[Event], train_ratio: float, valid_ratio: float) -> Tuple[List[Event], List[Event], List[Event]]:
    if not events:
        return [], [], []

    dates = sorted({e[3] for e in events})
    n = len(dates)
    train_end = max(1, int(math.floor(n * train_ratio)))
    valid_end = max(train_end + 1, int(math.floor(n * (train_ratio + valid_ratio))))
    valid_end = min(valid_end, n - 1) if n >= 3 else n

    train_dates = set(dates[:train_end])
    valid_dates = set(dates[train_end:valid_end])
    test_dates = set(dates[valid_end:])

    if not valid_dates and test_dates:
        x = min(test_dates)
        valid_dates = {x}
        test_dates.remove(x)
    if not test_dates and valid_dates:
        x = max(valid_dates)
        test_dates = {x}
        valid_dates.remove(x)

    train, valid, test = [], [], []
    for e in events:
        t = e[3]
        if t in train_dates:
            train.append(e)
        elif t in valid_dates:
            valid.append(e)
        else:
            test.append(e)

    return train, valid, test


def _write_events(path: str, events: Iterable[Event]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        for s, r, o, t in events:
            f.write(f"{s}\t{r}\t{o}\t{t}\n")


def _read_csv(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create CTpath TKG files from chronic CSV")
    parser.add_argument("--chronic_csv", type=str, required=True)
    parser.add_argument("--out_dir", type=str, default=os.path.join("data", "CHRONIC"))
    parser.add_argument("--train_ratio", type=float, default=0.7)
    parser.add_argument("--valid_ratio", type=float, default=0.1)
    args = parser.parse_args()

    if args.train_ratio <= 0 or args.valid_ratio <= 0 or args.train_ratio + args.valid_ratio >= 1:
        raise ValueError("train_ratio and valid_ratio must be >0 and sum <1")

    rows = _read_csv(args.chronic_csv)
    events = build_events_from_chronic(rows)
    events.sort(key=lambda x: (x[3], x[0], x[1], x[2]))

    train, valid, test = _split_by_time(events, args.train_ratio, args.valid_ratio)

    os.makedirs(args.out_dir, exist_ok=True)
    _write_events(os.path.join(args.out_dir, "train"), train)
    _write_events(os.path.join(args.out_dir, "valid"), valid)
    _write_events(os.path.join(args.out_dir, "test"), test)

    uniq_patients = len({e[0] for e in events})
    uniq_rels = len({e[1] for e in events})
    uniq_objs = len({e[2] for e in events})
    uniq_dates = len({e[3] for e in events})

    print("Built CHRONIC temporal KG files")
    print(f"out_dir={args.out_dir}")
    print(f"events_total={len(events)} train={len(train)} valid={len(valid)} test={len(test)}")
    print(f"patients={uniq_patients} relations={uniq_rels} objects={uniq_objs} dates={uniq_dates}")


if __name__ == "__main__":
    main()
