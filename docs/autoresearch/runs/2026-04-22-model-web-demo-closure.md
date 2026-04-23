# Autoresearch Run Note

## Date

2026-04-22

## Target

Make the independent `model-web` frontend suitable for direct demo use without regressing the stable clinic-side workflow.

## Hypothesis

The route and service boundaries for `model-web` already exist. If the model login page, dashboard, dataset page, training page, version page, operations page, and logout behavior are rewritten around the existing `model-api` contracts, the model-side business loop will become demo-ready.

## Files Touched

- `frontend/model-web/src/composables/useModelWorkspace.ts`
- `frontend/model-web/src/layouts/ModelLayout.vue`
- `frontend/model-web/src/components/ModelSidebar.vue`
- `frontend/model-web/src/components/ModelTopbar.vue`
- `frontend/model-web/src/pages/LoginPage.vue`
- `frontend/model-web/src/pages/ModelDashboardPage.vue`
- `frontend/model-web/src/pages/DatasetManagementPage.vue`
- `frontend/model-web/src/pages/TrainingCenterPage.vue`
- `frontend/model-web/src/pages/ModelVersionPage.vue`
- `frontend/model-web/src/pages/ModelOperationsPage.vue`
- `frontend/model-web/src/style.css`
- `frontend/model.html`
- `frontend/vite.config.mjs`
- `frontend/model-web/src/__tests__/LoginPage.spec.ts`
- `frontend/model-web/src/__tests__/ModelLayout.spec.ts`
- `model_api/store.py`

## Verification

```powershell
cd E:\CTpath-master\frontend
npm run build:model
npm run build
npm test -- model-web/src/__tests__/LoginPage.spec.ts model-web/src/__tests__/ModelLayout.spec.ts src/pages/__tests__/AppBootstrap.spec.ts src/pages/__tests__/PatientDetailPage.spec.ts src/pages/__tests__/AppWorkspacePage.spec.ts
cmd /c "set CONDA_NO_PLUGINS=true && conda run --no-capture-output -n ctpath python E:\CTpath-master\test_backend_contracts.py"
```

## Result

- `build:model` passed and emitted `dist/model.html`
- clinic frontend build still passed
- model-web and clinic smoke tests passed together
- backend contracts still passed

## Decision

Keep.

## Next Bottleneck

The next strongest issue is no longer model-web page closure. It is the startup dataset loader warnings in the clinic backend and the remaining polish gap between model-web visuals and the final defense presentation.
