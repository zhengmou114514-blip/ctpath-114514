# Demo Script

## System Boundary

This project is one chronic disease auxiliary diagnosis business system.

It uses one backend service, one database or demo store, one login/authentication flow, and role-based frontend workbenches.

The doctor, nurse, pharmacist, and admin entries are not separate systems. For demo stability, the same frontend project can be started on different ports so browser storage does not overwrite role sessions.

The demo does not include billing, inpatient management, insurance settlement, pharmacy inventory, procurement, inbound/outbound warehouse flows, or a complete prescription workflow.

## Start Services

Backend:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Doctor entry:

```bash
cd frontend
npm run dev:doctor
```

Nurse entry:

```bash
cd frontend
npm run dev:nurse
```

Pharmacist entry:

```bash
cd frontend
npm run dev:pharmacy
```

Admin entry:

```bash
cd frontend
npm run dev:admin
```

## Demo URLs

- Doctor: `http://localhost:5173`
- Nurse: `http://localhost:5174`
- Pharmacist: `http://localhost:5175`
- Admin: `http://localhost:5176`
- Backend: `http://localhost:8000`

These frontend entries share the same backend and data store.

## Suggested Accounts

- Doctor: `demo_clinic`
- Nurse: `demo_nurse`
- Pharmacist: `demo_pharmacist`
- Admin: `demo_admin`

Use the configured demo password for the local environment.

## Follow-Up Closure Demo

1. Open the doctor entry at `http://localhost:5173`.
2. Log in as the doctor and open a patient detail or model insight page.
3. Create a follow-up task.
4. Open the nurse entry at `http://localhost:5174`.
5. Log in as the nurse and open the nurse follow-up workbench.
6. Confirm the new task appears in the follow-up list.
7. Add a contact log and update the task status to `completed`, `not_reached`, or `need_review`.
8. Return to the doctor entry and refresh or wait for polling.
9. Confirm patient detail shows the latest follow-up status and contact record.

Expected backend records:

- `outpatient_tasks`
- `outpatient_task_logs`
- `patient_contact_logs`
- patient audit logs

## Medication Review Closure Demo

1. Open the doctor entry at `http://localhost:5173`.
2. Log in as the doctor and open patient medications.
3. Create or submit a medication. The review status should be `pending`.
4. Open the pharmacist entry at `http://localhost:5175`.
5. Log in as the pharmacist and open "药师用药复核".
6. Confirm the pending medication appears in the review queue.
7. Approve or reject the medication and enter a review note.
8. Return to the doctor entry and refresh or wait for polling.
9. Confirm patient medications show `approved` or `rejected`.
10. Confirm the patient timeline or audit area records the medication review action.

Expected backend fields:

- `review_status`
- `reviewed_by`
- `reviewed_at`
- `review_note`
- `updated_at`

## Model Insight Demo

1. Open the doctor entry.
2. Select a patient.
3. Trigger or open model insight.
4. Confirm the page shows Top-K risks, evidence summary, and advice source.

DeepSeek is only a text-assistance layer. It is not the core risk scoring model.

## Model Dashboard And Governance Demo

Use the admin entry after logging in as an administrator.

Admin entry:

```text
http://localhost:5176
```

Recommended admin sequence:

1. Log in as `demo_admin`.
2. Open role permissions or drug permission management.
3. Disable pharmacist medication review permission.
4. Refresh the pharmacist entry and confirm medication review is blocked.
5. Re-enable pharmacist medication review permission.
6. Open governance center and process one governance record as resolved, needs supplement, or ignored.
7. Open audit logs and confirm doctor, nurse, pharmacist, and admin actions are visible.
8. Open model dashboard and describe it as model runtime monitoring, not a training center.

Admin closure boundaries:

- Permission closure: permission change -> target role behavior changes -> audit log.
- Governance closure: governance record status changes -> summary changes -> audit log.
- Audit closure: key clinical and admin actions can be traced by operator, role, object, path, and trace id.

Model dashboard is a monitoring view only. Show:

- model version
- metrics
- call volume
- fallback ratio
- health status

Governance center supports a minimal status handling closure for governance records. Other display-only widgets should still be described as governance display or pending-work lists.

## Manual Multi-Role Login Check

1. Open the four frontend ports in one browser.
2. Log in as doctor on port `5173`.
3. Log in as nurse on port `5174`.
4. Log in as pharmacist on port `5175`.
5. Log in as admin on port `5176`.
6. Confirm each tab keeps its own role session.
7. Confirm all tabs still read and write the same backend data.

Different ports are different browser origins, so `localStorage` is isolated per role entry during the demo.

## Validation Commands

Backend:

```bash
pytest
```

Focused closure checks:

```bash
python backend/tests/test_followup_closure_contract.py
python backend/tests/test_medication_review_closure.py
python backend/tests/test_admin_permission_closure.py
python backend/tests/test_governance_audit_closure.py
```

Frontend:

```bash
cd frontend
npm run build
```
