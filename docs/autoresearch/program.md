# Program

## Objective

Use the autoresearch loop on CTpath's next high-value bottleneck: make the model-side independent demo path easier to verify and present without regressing the stable clinic-side workflow.

## Success Signal

- `model-api` and `clinic-api` contract scripts both pass
- clinic frontend build passes
- clinic key Vitest smoke tests pass
- no change spills back into stable clinic user flows without verification

## In-Scope Files

- `model_api/**`
- `test_model_api_contract.py`
- `test_backend_contracts.py`
- minimal supporting verification files under the repo root

## Out-of-Scope Files

- clinic page layout rewrites
- unrelated archive/follow-up/drug UI changes
- new model-web visual redesign
- broad backend schema changes

## Verification Commands

```powershell
cmd /c "set CONDA_NO_PLUGINS=true && conda run --no-capture-output -n ctpath python E:\CTpath-master\test_model_api_contract.py"
cmd /c "set CONDA_NO_PLUGINS=true && conda run --no-capture-output -n ctpath python E:\CTpath-master\test_backend_contracts.py"
cd E:\CTpath-master\frontend
npm run build
npm test -- src/pages/__tests__/AppBootstrap.spec.ts src/pages/__tests__/PatientDetailPage.spec.ts src/pages/__tests__/AppWorkspacePage.spec.ts
```

## Revert Rule

Discard any attempt that breaks a passing verification command, broadens scope into unrelated clinic pages, or leaves model-side behavior less predictable than before.

## Stop Condition

Stop when the backend contracts and clinic regression checks all pass and the next bottleneck is primarily model-web presentation rather than service correctness.

## Run Log

- Attempt 1:
  - hypothesis: `model_api` needs the same service-contract discipline as clinic-side APIs
  - files: `model_api/main.py`, `model_api/middleware.py`, `model_api/errors.py`, `model_api/store.py`, `model_api/demo_model_seed.py`, `model_api/schemas.py`, `test_model_api_contract.py`, `test_backend_contracts.py`
  - result: contracts passed after adding middleware and Python-version compatibility fixes
  - keep/discard: keep
- Attempt 2:
  - hypothesis: `model-web` already has a closed route/data chain, so replacing乱码文案、补退出登录收口、强化版本/训练/运营页表达，就能把模型端闭环拉到答辩可展示状态
  - files: `frontend/model-web/src/**`, `frontend/model.html`, `frontend/vite.config.mjs`
  - result: model login, dashboard, dataset, training, version, operations, and logout flows now build and pass smoke tests; `build:model` now emits `dist/model.html`
  - keep/discard: keep
