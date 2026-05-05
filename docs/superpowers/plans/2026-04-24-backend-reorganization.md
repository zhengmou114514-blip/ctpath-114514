# Backend Reorganization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the repository so all backend-related source, tests, and data live under a single `backend/` directory while keeping the root `start_system.bat` as a compatibility launcher.

**Architecture:** Mirror the openhis-style boundary: keep `frontend/` as the standalone UI app, consolidate all FastAPI and model-service code into `backend/`, and place backend-only tests, seed data, and runtime state underneath that same root. The root workspace should contain only cross-cutting docs, compatibility launchers, and the frontend app.

**Tech Stack:** Python 3, FastAPI, Pydantic, SQL/seed files, PowerShell/batch launch scripts, Vue 3 + TypeScript frontend.

---

### Task 1: Create the backend root and move backend packages

**Files:**
- Create: `backend/`
- Move: `app/` -> `backend/app/`
- Move: `model_api/` -> `backend/model_api/`
- Move: `clinic_api/` -> `backend/clinic_api/`

**Files to keep at root as compatibility-only:**
- `start_system.bat`
- `README.md`
- `docs/`
- `frontend/`

- [ ] **Step 1: Create the new backend root and move the Python packages**

```powershell
New-Item -ItemType Directory -Path backend
Move-Item -LiteralPath app -Destination backend\app
Move-Item -LiteralPath model_api -Destination backend\model_api
Move-Item -LiteralPath clinic_api -Destination backend\clinic_api
```

- [ ] **Step 2: Verify the new package layout**

Run:
```powershell
Get-ChildItem backend -Directory
```
Expected: `backend/app`, `backend/model_api`, and `backend/clinic_api` exist.

- [ ] **Step 3: Keep the root launcher as a compatibility entry**

Update `start_system.bat` so it launches `backend\app` and `frontend\` from their new locations, but leave the script at the repository root.

- [ ] **Step 4: Commit the directory move**

```powershell
git add backend start_system.bat
git commit -m "refactor: consolidate backend packages under backend root"
```

### Task 2: Move backend tests, seed data, and runtime state under backend

**Files:**
- Move: `test_*.py` -> `backend/tests/`
- Move: `verify_*.py` -> `backend/tests/`
- Move: `run_*.py` -> `backend/scripts/`
- Move: `demo_dataset.json` -> `backend/data/datasets/`
- Move: `medical_dataset.json` -> `backend/data/datasets/`
- Move: `backend/app/mysql_schema.sql` -> `backend/data/sql/`
- Move: `backend/app/mysql_seed_demo.sql` -> `backend/data/sql/`
- Move: `app/runtime/` -> `backend/runtime/`

- [ ] **Step 1: Create the backend data and test folders**

```powershell
New-Item -ItemType Directory -Path backend\tests, backend\scripts, backend\data\datasets, backend\data\sql, backend\runtime
```

- [ ] **Step 2: Move the test and data files**

```powershell
Move-Item -LiteralPath test_*.py -Destination backend\tests
Move-Item -LiteralPath verify_*.py -Destination backend\tests
Move-Item -LiteralPath run_*.py -Destination backend\scripts
Move-Item -LiteralPath demo_dataset.json -Destination backend\data\datasets
Move-Item -LiteralPath medical_dataset.json -Destination backend\data\datasets
Move-Item -LiteralPath app\mysql_schema.sql -Destination backend\data\sql
Move-Item -LiteralPath app\mysql_seed_demo.sql -Destination backend\data\sql
Move-Item -LiteralPath app\runtime -Destination backend\runtime
```

- [ ] **Step 3: Verify the files landed in the new structure**

Run:
```powershell
Get-ChildItem backend\tests, backend\scripts, backend\data\datasets, backend\data\sql, backend\runtime
```
Expected: all backend-only test/data/runtime files are under `backend/`.

- [ ] **Step 4: Commit the backend data/test move**

```powershell
git add backend
git commit -m "refactor: move backend tests and seed data under backend root"
```

### Task 3: Rewrite imports, paths, and startup commands for the new backend root

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/dataset_loader.py`
- Modify: `backend/app/store.py`
- Modify: `backend/model_api/main.py`
- Modify: `backend/model_api/store.py`
- Modify: `backend/clinic_api/main.py`
- Modify: `start_system.bat`
- Modify: `README.md`
- Modify: `launch.json`
- Modify: `docs/启动方式.md`
- Modify: `docs/项目启动与维护指南.md`
- Modify: `docs/PROJECT_LOGIC_MANIFEST.md`

- [ ] **Step 1: Update all backend code paths to the new package root**

```python
# Example target shape for root launchers and imports
from backend.app.main import app
from backend.model_api.main import app as model_app
```

- [ ] **Step 2: Update scripts and docs to point to `backend/`**

```powershell
python -m uvicorn backend.app.main:app --reload
python -m uvicorn backend.model_api.main:app --reload
```

- [ ] **Step 3: Verify the compatibility launcher still works from the root**

Run:
```powershell
cmd /c start_system.bat
```
Expected: it still starts the backend and frontend using the relocated backend paths.

- [ ] **Step 4: Commit the path and launcher updates**

```powershell
git add backend start_system.bat README.md launch.json docs
git commit -m "refactor: update launch paths for backend consolidation"
```

### Task 4: Make backend data loading and model seed state backend-local

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/dataset_loader.py`
- Modify: `backend/app/store.py`
- Modify: `backend/model_api/store.py`
- Modify: `backend/model_api/demo_model_seed.py`
- Modify: `backend/app/api/suggestions.py`

- [ ] **Step 1: Move dataset loading to the new backend data folder**

```python
# Target behavior
# - load datasets from backend/data/datasets/
# - write runtime state under backend/runtime/
# - do not inject demo rows into runtime stores during startup
```

- [ ] **Step 2: Make the model API seed explicit and local to backend data**

```python
# Target behavior
# - use backend/runtime/model_api/state.json as the persisted runtime state
# - keep seed data only as initialization input
# - avoid demo-style runtime fallback in the request path
```

- [ ] **Step 3: Keep suggestion generation tied to real predictions**

```python
# Target behavior
# - suggestions endpoint requires real prediction payloads
# - do not synthesize mock predictions inside the endpoint
```

- [ ] **Step 4: Commit the backend data/runtime cleanup**

```powershell
git add backend
git commit -m "refactor: localize backend runtime data and remove demo injection"
```

### Task 5: Final verification and cleanup

**Files:**
- Verify: `backend/app/**`
- Verify: `backend/model_api/**`
- Verify: `frontend/**`
- Verify: `start_system.bat`

- [ ] **Step 1: Run backend import checks**

Run:
```powershell
E:\Anaconda3\envs\ctpath\python.exe -c "import backend.app.main; import backend.model_api.main; print('backend import ok')"
```
Expected: `backend import ok`

- [ ] **Step 2: Run backend test coverage relevant to the moved files**

Run:
```powershell
cd backend
pytest
```
Expected: pass for the moved backend tests.

- [ ] **Step 3: Run frontend verification**

Run:
```powershell
cd frontend
npm test
npm run build
```
Expected: both pass after the backend path changes.

- [ ] **Step 4: Remove stale compatibility references only after verification**

Remove any root-level stale references that still point to `app/` or `model_api/` once the new backend paths are verified.


