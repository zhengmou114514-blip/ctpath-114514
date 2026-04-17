---
name: build-model-center
description: Build and separate model-related pages including model insight, model dashboard, model debug console, training center, and dataset import. Use when model features are mixed with business pages or lack clear boundaries.
---

# Goal

Create a proper model center with clearly separated model-facing pages.

This skill covers:
- 模型洞察
- 模型看板
- 模型调试台
- 训练中心
- 数据集 / CSV 导入

# Read first

Before editing:
1. `AGENTS.md`
2. `docs/PROJECT_LOGIC_MANIFEST.md`
3. `README.md`
4. current model-related frontend pages
5. model service files / types if relevant

# Required responsibility boundaries

## 模型洞察
Audience:
- doctor
- current patient workflow

Allowed:
- current patient prediction
- Top-K risks
- evidence summary
- recommendation source
- degradation/fallback state

Forbidden:
- training jobs
- full global metric dashboard
- dataset import UI
- raw JSON debug console

## 模型看板
Audience:
- admin
- governance
- model operator

Allowed:
- model version
- latest training time
- MRR
- Hits@1
- Hits@10
- inference volume
- fallback ratio
- model health

Forbidden:
- patient detail cards
- patient recommendation cards
- data quality issue lists

## 模型调试台
Audience:
- developer / model operator / admin

Allowed:
- sample selector
- raw input payload
- raw output payload
- version selector
- latency
- fallback reason
- error logs
- data source mode

Forbidden:
- doctor-facing production workflow

## 训练中心 / 数据集导入
Audience:
- model operator

Allowed:
- dataset upload
- CSV import for training
- field mapping
- validation issues
- training jobs
- training logs
- metric snapshots

Forbidden:
- direct exposure in doctor home or patient archive workflow

# Rules

1. Model insight, model dashboard, model debug, and training center must be independent pages.
2. CSV / dataset import must only live inside model center.
3. If backend is incomplete, use typed mock adapters and mark TODO clearly.
4. Do not move training or dataset import into doctor-facing pages.
5. Reuse published README metrics when possible.

# Work steps

## Step 1: Identify mixing
State which model responsibilities are currently mixed.

## Step 2: Separate
Define page ownership and route ownership.

## Step 3: Implement
Provide complete code for changed/new pages.

## Step 4: Validate
Provide acceptance checklist.

# Required output format

1. Current Mixing Problem
2. New Responsibility Boundaries
3. Files To Modify
4. Complete Code
5. Acceptance Checklist

# Required acceptance checklist

Must include:
- 模型洞察 only shows current patient model information
- 模型看板 only shows model metrics and status
- 模型调试台 shows raw input/output or debug context
- CSV / dataset import appears only in training/model center pages
- Doctor dashboard does not show full training or model dashboard sections