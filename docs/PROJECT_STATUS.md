# Project Status

## Current Status Summary

This project is a chronic disease auxiliary diagnosis business system. It already has the basic module structure for login, doctor dashboard, patient detail, nurse follow-up, drug management, drug permission management, model insight, model dashboard, governance center, and audit logs.

The minimum demo business closures have now been implemented and verified for the current demo scope.

## Confirmed Implemented or Partially Implemented

### Login and Role Entry

The system has login and role-based entry logic, but logout behavior still needs validation.

Known risks:

- login page may re-enter workspace if old workspace state is not cleared
- browser back navigation after logout needs verification

### Patient Detail

Patient detail is the central page for patient profile, disease timeline, medication, attachments, model advice, and follow-up entry.

### Model Insight

Model insight is for current patient risk result, evidence summary, advice source, and model-related explanation.

DeepSeek is only an optional text-assistance layer. It should not be described as the core prediction engine.

### Nurse Follow-up

The doctor-to-nurse-to-patient-detail follow-up closure is implemented and verified for the demo scope.

Verified behavior:

- doctor creates a follow-up task
- nurse sees the task in the follow-up workbench
- nurse updates task status and writes a contact log
- doctor patient detail returns the latest follow-up/contact summary
- task logs and patient audit logs record the operation

### Drug and Permission Management

Drug catalog and drug permission pages exist.

Medication CRUD and the lightweight pharmacist medication review closure are implemented and verified for the demo scope.

Verified behavior:

- doctor creates a pending patient medication
- pharmacist sees the pending medication in the review queue
- pharmacist approves or rejects the medication
- doctor patient medications return the updated review status
- patient timeline or audit records the review action

### Model Dashboard and Governance Center

Model dashboard and governance center are separate modules.

Model dashboard should show model version, metrics, calls, fallback ratio, and health status.

Governance center shows data quality, abnormal timeline, conflict records, incomplete archives, audit-related information, and a minimal governance record handling closure.

Model dashboard is runtime monitoring only. It should not be described as a training closure or training center.

## Verified Demo Closures

### Follow-up Closure

Required closure:

1. Doctor creates follow-up task.
2. Nurse sees the task.
3. Nurse updates task status.
4. Nurse writes contact log.
5. Patient detail shows latest follow-up/contact status.
6. Audit or task log records the operation.

Current status:

- Completed and verified by focused pytest.
- Completed and verified in the four-port browser-context demo.

### Medication Review Closure

Required closure:

1. Doctor submits medication.
2. Pharmacy staff sees pending review queue.
3. Pharmacy staff approves or rejects.
4. Database records review result.
5. Doctor page refreshes and shows updated review status.
6. Patient event or audit log records the operation.

Current status:

- Completed and verified by focused pytest.
- Completed and verified in the four-port browser-context demo.

### Admin Permission Closure

Verified closure:

1. Admin changes pharmacist medication review permission.
2. Pharmacist review behavior changes after refresh/re-entry.
3. Backend rejects unauthorized review attempts.
4. Permission change writes system audit logs.

Current status:

- Completed and verified by focused pytest.
- Completed and verified in the four-port browser-context demo.

### Governance Handling And Audit Closure

Verified closure:

1. Admin queries governance records.
2. Admin marks a governance record as resolved, needs supplement, or ignored.
3. Governance record status changes.
4. Governance summary changes.
5. System audit logs record the governance action.

Current status:

- Completed and verified by focused pytest.
- Completed and verified in the four-port browser-context demo.

### Display-Only Or Monitoring Modules

The following modules should not be described as complete business closures:

- model dashboard: runtime monitoring display only
- governance widgets without status handling: display or pending-work lists only
- model insight: current-patient risk/advice workflow, not model training

Do not describe the system as a full HIS. It still does not include billing, inpatient management, insurance settlement, pharmacy inventory, procurement, inbound/outbound warehouse flows, or a complete prescription workflow.

## Git Large File Issue

Status: resolved.

The previous push failed because `openhis-main.zip` exceeded the GitHub 100MB file limit. The file has now been removed from Git history, and the cleaned `main` branch has been pushed successfully.

Verified after cleanup:

- `git log --all -- openhis-main.zip` has no output
- `git ls-files openhis-main.zip` has no output
- `git push --force-with-lease origin main` succeeded

`.gitignore` includes:

```gitignore
openhis-main.zip
```

Do not commit `openhis-main.zip` or other large reference archives again. Future reference materials should stay outside the main repository, for example in a local `_references/` directory or external storage.
