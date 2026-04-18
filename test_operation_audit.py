from __future__ import annotations


def main() -> None:
    from app.audit.operation_audit import record_operation_audit
    from app.audit.system_audit import list_system_audit_logs

    record_operation_audit(
        action="drug_catalog_create",
        result="success",
        path="/api/drugs",
        method="POST",
        detail="drug_id=drug-demo",
        actor=type("Actor", (), {"role": "doctor", "username": "demo_doctor"})(),
    )

    logs = list_system_audit_logs(1)
    assert logs, "system audit log should contain the recorded action"
    assert logs[0]["action"] == "drug_catalog_create"
    assert logs[0]["result"] == "success"
    assert logs[0]["path"] == "/api/drugs"

    print("operation-audit-ok")


if __name__ == "__main__":
    main()
