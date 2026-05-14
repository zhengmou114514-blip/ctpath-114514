# Business Closure Plan

## Goal

The system should not only display pages independently. It should form real business closures between roles.

The verified demo closures are:

1. Follow-up closure between doctor and nurse.
2. Medication review closure between doctor and pharmacy staff.
3. Admin permission configuration closure.
4. Admin governance handling and audit closure.

All closures remain inside one chronic disease auxiliary diagnosis system with one backend, one data store, and role-based workbenches.

## Closure 1: Follow-up Closure

### Business Flow

```text
Doctor identifies patient risk
        ↓
Doctor creates follow-up task
        ↓
Nurse sees the task
        ↓
Nurse contacts patient
        ↓
Nurse writes contact log
        ↓
Task status changes
        ↓
Patient detail shows latest follow-up result
        ↓
Audit/task log records the operation
```

### Required Backend Capabilities

Required endpoints:

- `POST /api/worklists/followups`
- `PATCH /api/worklists/followups/{task_id}`
- `POST /api/patient/{patient_id}/contact-log`
- `GET /api/patient/{patient_id}`

Required data update:

- `outpatient_tasks`
- `outpatient_task_logs`
- `patient_contact_logs`
- `patient_audit_logs` or `system_audit_logs`

### Required Frontend Behavior

Doctor side:

- patient detail or model insight page can create follow-up task
- patient detail shows latest follow-up status

Nurse side:

- follow-up page shows pending tasks
- nurse can update task status
- nurse can write contact record

### Suggested Status Values

- `pending`
- `contacting`
- `not_reached`
- `need_review`
- `completed`
- `closed`

Do not use inconsistent status names such as `done`, `finished`, and `success`.

### Verification Status

Status: completed and verified for the demo scope.

Verified by:

- `python -m pytest backend/tests/test_followup_closure_contract.py -q`
- four-port browser-context validation using doctor and nurse entries

## Closure 2: Medication Review Closure

### Business Flow

```text
Doctor submits patient medication
        ↓
Medication review status becomes pending
        ↓
Pharmacy staff sees pending review list
        ↓
Pharmacy staff approves or rejects
        ↓
Database records review result
        ↓
Doctor page refreshes and shows approved/rejected status
        ↓
Patient timeline or audit log records the review action
```

### Required Backend Capabilities

Required endpoints:

- `GET /api/pharmacy/review-queue?status=pending`
- `PATCH /api/pharmacy/review-queue/{patient_id}/{medication_id}`
- `GET /api/patient-medication-reviews?status=pending`
- `PATCH /api/patient-medication-reviews/{patient_id}/{medication_id}`
- `GET /api/patient/{patient_id}/medications`

Required fields:

- `review_status`
- `reviewed_by`
- `reviewed_at`
- `review_note`
- `updated_at`

Recommended review status values:

- `pending`
- `approved`
- `rejected`

### Required Frontend Behavior

Doctor side:

- submit or edit patient medication
- see review status in patient detail
- auto-refresh medication status by polling or manual refresh

Pharmacy side:

- see pending medication reviews
- approve or reject
- write review note

### Refresh Strategy

Use polling first. Do not introduce WebSocket unless necessary.

Recommended polling interval:

- 5 seconds

### Verification Status

Status: completed and verified for the demo scope.

Verified by:

- `python -m pytest backend/tests/test_medication_review_closure.py -q`
- four-port browser-context validation using doctor and pharmacist entries

## Closure 3: Admin Permission Configuration Closure

### Business Flow

```text
Admin changes role medication permission
        ↓
Target role refreshes or re-enters the page
        ↓
Menu/button behavior and backend authorization reflect the new permission
        ↓
Unauthorized operation is rejected
        ↓
System audit log records the permission change
```

### Required Backend Capabilities

Required endpoints:

- `GET /api/drug-permissions/{role}`
- `PUT /api/drug-permissions/{role}`
- protected medication review endpoint authorization
- `GET /api/audit/system`

Required audit fields:

- operator
- target role
- changed permission
- operation time
- request path or trace id

### Verification Status

Status: completed and verified for the demo scope.

Verified by:

- `python -m pytest backend/tests/test_admin_permission_closure.py -q`
- four-port browser-context validation using admin and pharmacist entries

## Closure 4: Governance Handling And Audit Closure

### Business Flow

```text
Admin opens governance center
        ↓
Admin handles one governance record
        ↓
Record status changes
        ↓
Governance summary changes
        ↓
System audit log records the action
```

### Required Backend Capabilities

Required endpoints:

- `GET /api/governance/records`
- `PATCH /api/governance/records/{record_id}`
- `GET /api/audit/system`

Supported status values:

- `pending`
- `needs_supplement`
- `resolved`
- `ignored`

### Verification Status

Status: completed and verified for the demo scope.

Verified by:

- `python -m pytest backend/tests/test_governance_audit_closure.py -q`
- four-port browser-context validation using the admin entry

## Boundaries

Do not extend these closures into a full HIS workflow.

Out of scope:

- billing
- inpatient management
- insurance settlement
- pharmacy inventory
- procurement
- inbound/outbound warehouse flows
- complete prescription workflow
- model training center in the clinical workflow

Model dashboard remains a runtime monitoring view. It is not a model training closure.

## Tests Required

### Follow-up Closure Test

A test should verify:

- doctor creates follow-up task
- nurse can see task
- nurse updates status
- nurse writes contact log
- doctor patient detail can see latest follow-up result
- audit/task log exists

### Medication Review Closure Test

A test should verify:

- doctor submits medication
- pharmacy staff sees pending medication
- pharmacy staff approves or rejects
- doctor sees updated review status
- audit/patient event record exists

### Admin Permission Closure Test

A test should verify:

- admin changes pharmacist medication review permission
- pharmacist review is rejected when permission is disabled
- pharmacist review succeeds again after permission is restored
- system audit log contains the permission change

### Governance Audit Closure Test

A test should verify:

- admin queries governance records
- admin updates one governance record status
- summary changes after the update
- system audit log contains the governance action
