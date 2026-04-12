# CHRONIC Data Audit

## Summary

- Verdict: `partially_suitable`
- Recommended use: `system demo + model migration + baseline comparison`
- Not recommended: `use it alone to support strong real-clinical-effectiveness claims`

## Measured Stats

| Split | Rows | Patients | Relations | Objects | Dates |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 50808 | 496 | 24 | 37 | 715 |
| valid | 7152 | 222 | 24 | 37 | 102 |
| test | 14040 | 338 | 24 | 37 | 205 |

## What Meets the Requirement

1. The data is already in temporal KG quadruple format `(s, r, o, t)`.
2. The split is chronological, so it can be used for time-aware prediction.
3. The dataset can already run through the full CTpath pipeline.
4. It is enough to support the Web system demo and the task-book experiment workflow.

## Main Risks

1. Many relations have exactly the same frequency, which suggests the dataset comes from wide-table feature expansion rather than native clinical events.
2. The object vocabulary is very small (`37`), which is weak for a richer medical temporal KG.
3. A single patient record is expanded into many relation-object events at the same date, so the temporal signal is partially synthetic.

## Interpretation

This means the current dataset is structurally valid for CTpath, but only partially matches the ideal medical TKG requirement.

It is a good fit for:

1. proving the model can be migrated from general TKGR to chronic-disease scenarios
2. powering the doctor-facing Web system demo
3. completing the comparison experiment required by the task book

It is a weak fit for:

1. claiming real-world medical effectiveness
2. arguing strong clinical generalization without an additional real longitudinal dataset

## Recommended Strategy

1. Keep `CHRONIC` as the main dataset for the system demo and migration experiment.
2. Use `TransE` and `RotatE` as static KG baselines to satisfy the comparison requirement.
3. Keep `ICEWS14` as the reproducibility dataset for the original CTpath model.
4. If the thesis needs stronger medical evidence, add one real longitudinal dataset such as `MIMIC-IV` or `eICU-CRD`.
