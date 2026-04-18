from __future__ import annotations

from types import SimpleNamespace


def main() -> None:
    from app.audit.operation_audit import record_operation_audit
    from app.audit.system_audit import list_system_audit_logs

    request = SimpleNamespace(
        url=SimpleNamespace(path="/api/drugs"),
        method="POST",
        state=SimpleNamespace(trace_id="trace-test-001"),
        client=SimpleNamespace(host="127.0.0.1"),
    )

    record_operation_audit(
        operation="create",
        resource_type="drug_catalog",
        resource_id="drug-demo",
        request=request,
        actor=type("Actor", (), {"role": "doctor", "username": "demo_doctor"})(),
    )

    logs = list_system_audit_logs(1)
    assert logs, "system audit log should contain the recorded action"
    assert logs[0]["action"] == "drug_catalog_create"
    assert logs[0]["result"] == "success"
    assert logs[0]["path"] == "/api/drugs"
    assert "operation=create" in str(logs[0]["detail"])
    assert "resource_type=drug_catalog" in str(logs[0]["detail"])
    assert "resource_id=drug-demo" in str(logs[0]["detail"])
    assert "trace_id=trace-test-001" in str(logs[0]["detail"])

    print("operation-audit-ok")


if __name__ == "__main__":
    main()
