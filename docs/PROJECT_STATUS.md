# Project Status

## Current Status Summary

This project is a chronic disease auxiliary diagnosis business system. It already has the basic module structure for login, doctor dashboard, patient detail, nurse follow-up, drug management, drug permission management, model insight, model dashboard, governance center, and audit logs.

However, not all business closures are complete.

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

The nurse follow-up page exists, but the complete doctor-to-nurse-to-patient-detail closure needs validation or implementation.

### Drug and Permission Management

Drug catalog and drug permission pages exist.

Medication CRUD exists or is partially implemented, but the pharmacy review closure still needs implementation or validation.

### Model Dashboard and Governance Center

Model dashboard and governance center are separate modules.

Model dashboard should show model version, metrics, calls, fallback ratio, and health status.

Governance center should show data quality, abnormal timeline, conflict records, incomplete archives, and audit-related information.

## Known Not Fully Closed

### Follow-up Closure

Required closure:

1. Doctor creates follow-up task.
2. Nurse sees the task.
3. Nurse updates task status.
4. Nurse writes contact log.
5. Patient detail shows latest follow-up/contact status.
6. Audit or task log records the operation.

Current status:

- Needs code inspection and tests.
- Do not claim this is complete until tested.

### Medication Review Closure

Required closure:

1. Doctor submits medication.
2. Pharmacy staff sees pending review queue.
3. Pharmacy staff approves or rejects.
4. Database records review result.
5. Doctor page refreshes and shows updated review status.
6. Patient event or audit log records the operation.

Current status:

- Needs implementation or verification.
- Do not claim this is complete until tested.

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
