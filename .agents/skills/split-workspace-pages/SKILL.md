---
name: split-workspace-pages
description: Split mixed workspace pages into independent route-based pages. Use this when model insight, model dashboard, governance dashboard, or doctor dashboard content is incorrectly mixed in one main content area.
---

# Goal

Fix mixed page rendering and enforce one navigation item = one independent workspace page.

Typical symptoms:
- Clicking “模型洞察” still shows “治理看板”
- Clicking “治理看板” still shows model content
- “模型看板”和“模型洞察”没有分开
- 医生首页承载完整模型页或完整治理页

# Read first

Before changing any code, read:
1. `AGENTS.md`
2. `docs/PROJECT_LOGIC_MANIFEST.md`
3. current router file
4. current main layout file
5. current entry page (`App.vue` or equivalent)

# Scope

Only modify files related to:
- route definitions
- main layout
- main workspace rendering
- doctor dashboard
- model pages
- governance pages

Do not modify backend code in this skill.

# Required module boundaries

## Doctor Dashboard
Only summary/entry content:
- pending patients
- current patient summary
- quick actions
- short risk summary

Must not contain:
- full governance dashboard
- full model dashboard
- model debug console
- long stacked sections

## Model Insight
Only current patient model information:
- current patient prediction
- Top-K risk events
- evidence summary
- recommendation source
- degradation/fallback state

## Model Dashboard
Only global model information:
- model version
- latest training time
- MRR
- Hits@1
- Hits@10
- inference volume
- fallback ratio
- model health

## Governance Dashboard
Only governance information:
- data quality overview
- missing fields
- anomaly timeline count
- incomplete archives
- conflict records
- governance actions

# Hard rules

1. Main content must be mutually exclusive.
2. Use `v-if / v-else-if / v-else` or route-level rendering.
3. Do not keep multiple workspace pages mounted and hide them with CSS.
4. Do not use `display:none` to simulate switching.
5. Do not redesign APIs.
6. Do not rename API fields.
7. Do not add unrelated features.

# Work steps

## Step 1: Diagnose
Explain why pages are mixed:
- router issue
- layout issue
- nested page issue
- shared slot/default panel issue
- active module state issue

## Step 2: Plan
List only the files that need to change.

## Step 3: Implement
Provide complete replacement code for changed files.

## Step 4: Validate
Provide a strict acceptance checklist.

# Required output format

1. Problem Analysis
2. Files To Modify
3. Complete Code
4. Acceptance Checklist

# Required acceptance checklist

Must include all:
- Clicking `模型洞察` does not show `治理看板`
- Clicking `治理看板` does not show `模型洞察`
- Clicking `模型看板` does not show current patient recommendation cards
- Doctor dashboard no longer contains full governance/model pages
- Only one workspace page is mounted at a time