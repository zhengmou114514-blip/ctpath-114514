# Autoresearch Run Note

## Date

2026-04-22

## Target

Harden the independent `model-api` service so it matches the clinic-side contract discipline and becomes easier to verify for demo use.

## Hypothesis

If `model-api` gets the same minimum service envelope as `clinic-api` — trace id, unified exception payloads, request timing, auth context, and explicit contract tests — then the backend demo path will become verifiable without destabilizing clinic-side pages.

## Files Touched

- `model_api/main.py`
- `model_api/middleware.py`
- `model_api/errors.py`
- `model_api/store.py`
- `model_api/demo_model_seed.py`
- `model_api/schemas.py`
- `test_model_api_contract.py`
- `test_backend_contracts.py`

## Verification

```powershell
cmd /c "set CONDA_NO_PLUGINS=true && conda run --no-capture-output -n ctpath python E:\CTpath-master\test_model_api_contract.py"
cmd /c "set CONDA_NO_PLUGINS=true && conda run --no-capture-output -n ctpath python E:\CTpath-master\test_backend_contracts.py"
cd E:\CTpath-master\frontend
npm run build
npm test -- src/pages/__tests__/AppBootstrap.spec.ts src/pages/__tests__/PatientDetailPage.spec.ts src/pages/__tests__/AppWorkspacePage.spec.ts
```

## Result

- `model-contract-ok`
- `backend-contracts-ok`
- clinic frontend build passed
- clinic key Vitest smoke tests passed

## Decision

Keep.

## Next Bottleneck

The next strongest candidate for another autoresearch run is the model-web presentation and independent demo flow, not the already-stable clinic-side core path.
