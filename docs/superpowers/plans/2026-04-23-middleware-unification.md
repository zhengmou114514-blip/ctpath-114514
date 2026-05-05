# Middleware Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unify the business and model API middleware chain so every protected request has consistent trace IDs, timing logs, authentication, RBAC, and error envelopes.

**Architecture:** Keep business and model services separate, but align their middleware contracts. The business API will gain a request-timing middleware and a real RBAC middleware entry in the app startup chain. The model API will keep its timing/auth/error behavior but remain consistent in headers, trace propagation, and protected-route behavior. Route-level permissions stay in place, but the middleware becomes the early enforcement layer.

**Tech Stack:** FastAPI, Starlette middleware, SlowAPI, JWT bearer auth, existing RBAC permission registry, pytest/TestClient.

---

### Task 1: Make the business middleware chain explicit

**Files:**
- Modify: `backend/app/main.py`
- Modify: `app/middleware/__init__.py`
- Create: `app/middleware/timing.py`

- [ ] **Step 1: Write the failing contract expectation**

```python
def test_business_health_contract() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200, response.text
        assert "X-Trace-Id" in response.headers
        assert "X-Process-Time-Ms" in response.headers
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest test_closure_contract.py::test_business_health_contract -v`
Expected: fail because the business app does not yet emit `X-Process-Time-Ms`.

- [ ] **Step 3: Add the request timing middleware and mount it**

```python
from .middleware.timing import RequestTimingMiddleware

app.add_middleware(CORSMiddleware, ...)
app.add_middleware(RBACMiddleware)
app.add_middleware(JWTAuthMiddleware)
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(GlobalExceptionMiddleware)
app.add_middleware(TraceIdMiddleware)
```

```python
from __future__ import annotations

import logging
import time
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .trace_id import get_trace_id

logger = logging.getLogger(__name__)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        trace_id = get_trace_id(request)
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        logger.info(
            "request trace_id=%s method=%s path=%s status=%s elapsed_ms=%.2f",
            trace_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
```

- [ ] **Step 4: Re-run the business contract test**

Run: `pytest test_closure_contract.py::test_business_health_contract -v`
Expected: pass and return both `X-Trace-Id` and `X-Process-Time-Ms`.

### Task 2: Tighten business RBAC and keep the registry consistent

**Files:**
- Modify: `app/api/analytics.py`
- Modify: `app/auth/dependencies.py`
- Modify: `app/auth/rbac_middleware.py`
- Modify: `app/auth/permission_registry.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Update the failing permission expectation**

```python
def test_model_metrics_requires_admin() -> None:
    with TestClient(app) as client:
        doctor_headers = _login_headers(client)
        response = client.get("/api/model/metrics", headers=doctor_headers)
        assert response.status_code == 403, response.text
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest test_closure_contract.py::test_model_metrics_requires_admin -v`
Expected: fail until `/api/model/metrics` is admin-only everywhere.

- [ ] **Step 3: Align the route, dependencies, and registry**

```python
@router.get("/api/model/metrics", response_model=ModelMetricsResponse)
def model_metrics(_: object = Depends(require_roles("admin"))) -> ModelMetricsResponse:
    return get_model_metrics()
```

```python
def require_doctor(request: Request, token: str = Depends(require_token)):
    return get_current_doctor(request, token)
```

```python
def _forbidden_response(...):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": ..., "error_code": "FORBIDDEN", "trace_id": trace_id},
        headers={"X-Trace-Id": trace_id},
    )
```

```python
self.register(APIPermission(
    path="/api/patient/{id}/attachments",
    method="GET",
    required_permissions={Permission.PATIENT_VIEW},
    allowed_roles={Role.ADMIN, Role.DOCTOR, Role.NURSE, Role.PHARMACIST, Role.ARCHIVIST},
    description="获取患者附件列表"
))
```

- [ ] **Step 4: Re-run the permission test**

Run: `pytest test_closure_contract.py::test_model_metrics_requires_admin -v`
Expected: pass and return a 403 for doctor sessions.

### Task 3: Verify the whole middleware contract

**Files:**
- Modify: `test_closure_contract.py`
- Modify: `test_backend_contracts.py`
- Modify: `test_model_api_contract.py`

- [ ] **Step 1: Add the new header and permission assertions**

```python
def test_business_health_contract() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200, response.text
        assert "X-Trace-Id" in response.headers
        assert "X-Process-Time-Ms" in response.headers


def test_model_metrics_requires_admin() -> None:
    with TestClient(app) as client:
        doctor_headers = _login_headers(client)
        response = client.get("/api/model/metrics", headers=doctor_headers)
        assert response.status_code == 403, response.text
```

- [ ] **Step 2: Run the backend contract suite**

Run: `python test_backend_contracts.py`
Expected: `backend-contracts-ok`

- [ ] **Step 3: Commit**

```bash
git add backend/app/main.py app/middleware/timing.py app/middleware/__init__.py app/api/analytics.py app/auth/dependencies.py app/auth/rbac_middleware.py app/auth/permission_registry.py test_closure_contract.py test_backend_contracts.py test_model_api_contract.py
git commit -m "feat: unify middleware contract"
```

