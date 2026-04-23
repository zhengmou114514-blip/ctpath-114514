# Model Center Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `model-dashboard`, `training-center`, and `model-insight` real, reachable routes with stable back-navigation so the model center behaves like a separate module instead of a dead-end page state.

**Architecture:** Keep the current `AppWorkspacePage` shell and workspace context. Add the missing route records, teach the workspace controller how to map those routes to the existing `AppSection` values, and preserve the current patient-workspace behavior unchanged.

**Tech Stack:** Vue 3, Vue Router, TypeScript, Pinia, Vite

---

### Task 1: Register model-center routes

**Files:**
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: Add the failing route coverage**

The router currently has child routes for `patient-detail`, `nurse-followups`, `governance`, `drug-management`, `drug-permission-management`, `pharmacy`, and `coordination`, but no route records for the model center pages.

- [ ] **Step 2: Add the missing children**

Add child routes under `/` for:
- `model-dashboard` -> `frontend/src/pages/ModelDashboardPage.vue`
- `training-center` -> `frontend/src/pages/TrainingCenterPage.vue`
- `model-operations` -> `frontend/src/pages/ModelOperationsPage.vue`
- `model-insight` -> `frontend/src/pages/ModelInsightPage.vue`

- [ ] **Step 3: Verify route names**

Run:
`E:\Anaconda3\envs\ctpath\python.exe -c "from pathlib import Path; p=Path(r'E:\CTpath-master\frontend\src\router\index.ts'); print(p.read_text(encoding='utf-8'))"`

Expected: the four model-center route names exist in the child route table.

### Task 2: Sync workspace sections to the new routes

**Files:**
- Modify: `frontend/src/pages/AppWorkspacePage.vue`
- Modify: `frontend/src/composables/useWorkspaceController.ts`

- [ ] **Step 1: Add route-to-section and section-to-route mappings**

Map these route names in `AppWorkspacePage`:
- `model-dashboard` -> `model-dashboard`
- `training-center` -> `training-center`
- `model-operations` -> `model-operations`
- `model-insight` -> `insights`

Map these workspace sections back to routes:
- `model-dashboard` -> `model-dashboard`
- `training-center` -> `training-center`
- `model-operations` -> `model-operations`
- `insights` -> `model-insight`

- [ ] **Step 2: Mark the model routes as split workspace routes**

Extend `isSplitWorkspaceRoute` so the shell renders `<RouterView />` for the four model-center routes instead of falling through to the empty placeholder.

- [ ] **Step 3: Verify workspace sync**

Run:
`E:\Anaconda3\envs\ctpath\python.exe -c "from pathlib import Path; p=Path(r'E:\CTpath-master\frontend\src\pages\AppWorkspacePage.vue'); print('model-dashboard' in p.read_text(encoding='utf-8'))"`

Expected: `True` for the new route names in the workspace page.

### Task 3: Verify end-to-end navigation

**Files:**
- No new files

- [ ] **Step 1: Build the frontend**

Run:
`cmd /c npm run build`

Expected: build completes without route resolution errors.

- [ ] **Step 2: Launch the app and exercise the chain**

Open the model dashboard, go to training center, return to model dashboard, and confirm the model insight page still loads as a patient-scoped page under the workspace shell.

- [ ] **Step 3: Confirm no patient workflow regression**

Open doctor dashboard, patient detail, archive, follow-up, and governance pages to confirm they still render through the existing workspace shell and are not affected by the new model routes.
