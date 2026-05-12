# Business Closure Plan

## Goal

The system should not only display pages independently. It should form real business closures between roles.

The minimum closures are:

1. Follow-up closure between doctor and nurse.
2. Medication review closure between doctor and pharmacy staff.

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
- `POST /api/patient/{patient_id}/contact-logs`
- `GET /api/patients/{patient_id}`

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

- `GET /api/pharmacy/medication-reviews?status=pending`
- `PATCH /api/pharmacy/medication-reviews/{medication_id}`
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
