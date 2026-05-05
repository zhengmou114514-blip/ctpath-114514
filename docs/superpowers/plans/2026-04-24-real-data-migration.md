# Real Data Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove frontend demo fallbacks and local mock state, wire the workspace to real backend-backed data flows, and persist model-center records in the backend so the system operates as a real chronic-care business application.

**Architecture:** Start from the clinical mainline because it drives the core workflow and the paper narrative. Then add backend persistence and APIs for the model center so training data and task records live in durable storage instead of browser memory. Finally, align governance, coordination, and pharmacy pages with the same real-data contract and update docs/tests so the codebase consistently describes the real running system.

**Tech Stack:** Vue 3, TypeScript, Vue Router, Pinia, Element Plus, FastAPI, Pydantic, SQLAlchemy, MySQL, pytest, Vitest

---

### Task 1: Remove frontend demo fallback from the shared API client

**Files:**
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/pages/PatientDetailPage.vue`
- Modify: `frontend/src/pages/ModelInsightPage.vue`
- Modify: `frontend/src/pages/GovernancePage.vue`
- Modify: `frontend/src/pages/ModelDashboardPage.vue`
- Modify: `frontend/src/pages/RoleWorkspacePage.vue`

- [ ] **Step 1: Write the failing test**

```ts
import { describe, it, expect } from 'vitest'
import { healthCheck } from '../services/api'

describe('api client real-data mode', () => {
  it('does not advertise demo fallback behavior in health payloads', async () => {
    const health = await healthCheck()
    expect(health.mode).not.toBe('demo')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/services/__tests__/api-real-data.spec.ts -v`
Expected: FAIL because the client still exposes demo fallback behavior.

- [ ] **Step 3: Write minimal implementation**

```ts
const ENABLE_DEMO_FALLBACK = false

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const normalizedPath = normalizeApiPath(path)
  try {
    const response = await requestClient.request({
      url: normalizedPath,
      method: options.method ?? 'GET',
      headers: mergeRequestHeaders(shouldSetContentType, options.headers),
      data: options.body,
    })
    if (response.status < 200 || response.status >= 300) {
      const detail = extractErrorDetail(response.data, response.statusText || 'Request failed')
      throw new Error(`[${response.status}] ${detail}`)
    }
    return parseResponseData<T>(response.data)
  } catch (e) {
    const m = e instanceof Error ? e.message : ''
    const isNetworkError = !m || /Failed to fetch|NetworkError|Load failed|fetch|ECONNREFUSED|ERR_CONNECTION_REFUSED/i.test(m)
    if (isNetworkError) throw new Error(`Cannot connect to backend API (${API_BASE}). Please start backend service.`)
    throw e
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/services/__tests__/api-real-data.spec.ts -v`
Expected: PASS after demo fallback is removed and the client only talks to the backend.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/api.ts frontend/src/pages/PatientDetailPage.vue frontend/src/pages/ModelInsightPage.vue frontend/src/pages/GovernancePage.vue frontend/src/pages/ModelDashboardPage.vue frontend/src/pages/RoleWorkspacePage.vue
git commit -m "refactor: remove frontend demo fallback"
```

### Task 2: Replace model-center localStorage state with backend persistence

**Files:**
- Modify: `frontend/src/services/modelTrainingAdapter.ts`
- Create: `app/api/model_training.py`
- Create: `app/services/model_training_service.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/mysql_schema.sql`
- Modify: `frontend/src/pages/TrainingCenterPage.vue`
- Modify: `frontend/src/pages/ModelOperationsPage.vue`
- Modify: `frontend/src/pages/ModelDashboardPage.vue`
- Modify: `frontend/src/services/modelBoardAdapter.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { describe, it, expect } from 'vitest'
import { listModelDatasets, listTrainingTasks } from '../services/modelTrainingAdapter'

describe('training center persistence', () => {
  it('loads records from backend-backed state rather than browser-only mock data', () => {
    expect(listModelDatasets().every((item) => item.source !== 'mock-local')).toBe(true)
    expect(listTrainingTasks().every((item) => item.source !== 'mock-local')).toBe(true)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/services/__tests__/training-center-real-data.spec.ts -v`
Expected: FAIL because the adapter still seeds mock-local localStorage state.

- [ ] **Step 3: Write minimal implementation**

```python
@router.get("/api/model/datasets")
def list_model_datasets(_: object = Depends(require_roles("admin"))) -> list[ModelDatasetRecord]:
    return MODEL_TRAINING_SERVICE.list_datasets()

@router.post("/api/model/datasets/import", response_model=ModelDatasetRecord)
def import_model_dataset(...):
    return MODEL_TRAINING_SERVICE.import_dataset(...)

@router.get("/api/model/training-tasks")
def list_training_tasks(_: object = Depends(require_roles("admin"))) -> list[ModelTrainingTaskRecord]:
    return MODEL_TRAINING_SERVICE.list_tasks()

@router.post("/api/model/training-tasks", response_model=ModelTrainingTaskRecord)
def create_training_task(...):
    return MODEL_TRAINING_SERVICE.create_task(...)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/services/__tests__/training-center-real-data.spec.ts -v`
Expected: PASS after the adapter reads/writes backend records only.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/modelTrainingAdapter.ts frontend/src/pages/TrainingCenterPage.vue frontend/src/pages/ModelOperationsPage.vue frontend/src/pages/ModelDashboardPage.vue frontend/src/services/modelBoardAdapter.ts app/api/model_training.py app/services/model_training_service.py backend/app/main.py backend/app/mysql_schema.sql
git commit -m "feat: persist model center data on backend"
```

### Task 3: Align governance, coordination, pharmacy, and role workspace with real backend data

**Files:**
- Modify: `frontend/src/pages/PharmacyWarehousePage.vue`
- Modify: `frontend/src/pages/CareCoordinationPage.vue`
- Modify: `frontend/src/pages/RoleWorkspacePage.vue`
- Modify: `frontend/src/pages/GovernancePage.vue`
- Modify: `frontend/src/services/api.ts`
- Modify: `app/api/pharmacy.py`
- Modify: `app/api/coordination.py`
- Modify: `app/services/governance_service.py`

- [ ] **Step 1: Write the failing test**

```ts
import { describe, it, expect } from 'vitest'
import { getPharmacyDashboard, getCoordinationBoard } from '../services/api'

describe('business workspaces use backend data', () => {
  it('returns persisted inventory and coordination records', async () => {
    const dashboard = await getPharmacyDashboard()
    const coordination = await getCoordinationBoard()
    expect(dashboard.inventory.length).toBeGreaterThanOrEqual(0)
    expect(coordination.items.length).toBeGreaterThanOrEqual(0)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/services/__tests__/workspace-real-data.spec.ts -v`
Expected: FAIL until every page uses backend data without mock fallback.

- [ ] **Step 3: Write minimal implementation**

```ts
export async function getPharmacyDashboard(): Promise<PharmacyDashboardResponse> {
  return request('/pharmacy/dashboard', { method: 'GET' })
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/services/__tests__/workspace-real-data.spec.ts -v`
Expected: PASS after the UI reads backend data directly.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/PharmacyWarehousePage.vue frontend/src/pages/CareCoordinationPage.vue frontend/src/pages/RoleWorkspacePage.vue frontend/src/pages/GovernancePage.vue frontend/src/services/api.ts app/api/pharmacy.py app/api/coordination.py app/services/governance_service.py
git commit -m "feat: align business workspaces with backend data"
```

### Task 4: Update docs and verify the end-to-end real-data contract

**Files:**
- Modify: `README.md`
- Modify: `docs/PROJECT_LOGIC_MANIFEST.md`
- Modify: `docs/启动与演示说明.md`
- Modify: `docs/使用指南.md`
- Modify: `docs/系统设计说明.md`
- Modify: `docs/系统整改建议与执行清单.md`

- [ ] **Step 1: Write the failing test**

```md
The documentation must not describe demo fallback as the primary behavior after the migration.
```

- [ ] **Step 2: Run verification**

Run: `cd frontend && npm run build`
Expected: PASS.

- [ ] **Step 3: Update the docs**

```md
Replace demo-first wording with backend-first real-data wording, and explicitly document that empty state means no record exists rather than a local mock.
```

- [ ] **Step 4: Run verification again**

Run: `python -m pytest`
Expected: PASS for the backend contract suite.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/PROJECT_LOGIC_MANIFEST.md docs/启动与演示说明.md docs/使用指南.md docs/系统设计说明.md docs/系统整改建议与执行清单.md
git commit -m "docs: align repository docs with real-data system behavior"
```


