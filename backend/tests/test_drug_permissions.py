from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    temp_dir = Path(__file__).resolve().parent / "app" / "runtime" / "drug_permission_test_case"
    temp_dir.mkdir(parents=True, exist_ok=True)
    os.environ["CTPATH_DRUG_PERMISSION_DIR"] = str(temp_dir)

    from app.schemas import DrugPermissionUpsertRequest
    from app.services.drug_permission_service import (
        get_drug_permission_item,
        list_drug_permissions,
        update_drug_permission_item,
    )

    records = list_drug_permissions()
    assert {record.role for record in records} == {"doctor", "nurse", "pharmacist", "archivist", "admin"}
    assert len(records) == 5

    doctor = get_drug_permission_item("doctor")
    assert doctor.allow_view is True
    assert doctor.allow_prescribe is True

    updated = update_drug_permission_item(
        "nurse",
        DrugPermissionUpsertRequest(
            role="nurse",
            allow_view=True,
            allow_prescribe=False,
            allow_review=True,
            allow_execute=True,
            allow_controlled_drug=False,
        ),
    )
    assert updated.allow_review is True
    assert updated.allow_execute is True

    filtered = list_drug_permissions(role="nurse")
    assert len(filtered) == 1
    assert filtered[0].role == "nurse"

    print("drug-permission-ok")


if __name__ == "__main__":
    main()
